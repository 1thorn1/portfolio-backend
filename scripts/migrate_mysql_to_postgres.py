#!/usr/bin/env python3
"""
One-off data migration: Railway MySQL  ->  Render PostgreSQL.

Only two tables carry data: `comment` and `visitor_log`. Their schema is
created automatically by Hibernate (`ddl-auto=update`) the first time the
backend boots against the Render database, so this script only copies rows
and then fixes the PostgreSQL identity sequences.

--------------------------------------------------------------------------
Setup
--------------------------------------------------------------------------
    python3 -m venv .venv && source .venv/bin/activate
    pip install "pymysql>=1.1" "psycopg[binary]>=3.1"

    # Source: Railway MySQL public proxy URL
    #   railway variables --service MySQL --kv | grep MYSQL_PUBLIC_URL
    export SOURCE_MYSQL_URL='mysql://root:PASSWORD@sakura.proxy.rlwy.net:43143/railway'

    # Target: Render -> portfolio-db -> "External Database URL"
    export TARGET_PG_URL='postgresql://portfolio:PASSWORD@dpg-xxxx-a.singapore-postgres.render.com/portfolio'

--------------------------------------------------------------------------
Run
--------------------------------------------------------------------------
    python scripts/migrate_mysql_to_postgres.py             # dry run: show row counts on both sides
    python scripts/migrate_mysql_to_postgres.py --run       # copy data (upsert by primary key)
    python scripts/migrate_mysql_to_postgres.py --run --truncate   # wipe target tables first, then copy

The copy is idempotent: rows are upserted on `id`, so re-running is safe.
The Railway MySQL service must be running (Start it in the Railway dashboard
if it shows "Offline") for the source connection to succeed.
"""
from __future__ import annotations

import argparse
import os
import sys
from urllib.parse import unquote, urlparse

try:
    import pymysql
except ImportError:
    sys.exit("Missing dependency: pip install 'pymysql>=1.1'")

try:
    import psycopg
except ImportError:
    sys.exit("Missing dependency: pip install 'psycopg[binary]>=3.1'")

TABLES = {
    # table        -> columns copied, in order
    "comment": ("id", "author", "content", "created_at"),
    "visitor_log": ("id", "ip_address", "visit_date"),
}
BATCH = 500


def parse_mysql(url: str) -> dict:
    p = urlparse(url)
    if p.scheme not in ("mysql", "mysql+pymysql"):
        sys.exit(f"SOURCE_MYSQL_URL must start with mysql:// (got {p.scheme}://)")
    return dict(
        host=p.hostname,
        port=p.port or 3306,
        user=unquote(p.username or ""),
        password=unquote(p.password or ""),
        database=(p.path or "/").lstrip("/") or "railway",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.SSCursor,
    )


def read_source(mysql_cfg: dict):
    """Yield (table, columns, rows) for each table, streamed from MySQL."""
    conn = pymysql.connect(**mysql_cfg)
    try:
        for table, cols in TABLES.items():
            with conn.cursor() as cur:
                cur.execute(f"SELECT {', '.join(cols)} FROM {table} ORDER BY id")
                rows = cur.fetchall()
            yield table, cols, rows
    finally:
        conn.close()


def count_rows_mysql(mysql_cfg: dict) -> dict:
    conn = pymysql.connect(**{**mysql_cfg, "cursorclass": pymysql.cursors.Cursor})
    try:
        out = {}
        with conn.cursor() as cur:
            for table in TABLES:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                out[table] = cur.fetchone()[0]
        return out
    finally:
        conn.close()


def count_rows_pg(pg: "psycopg.Connection") -> dict:
    out = {}
    with pg.cursor() as cur:
        for table in TABLES:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            out[table] = cur.fetchone()[0]
    return out


def upsert(pg: "psycopg.Connection", table: str, cols: tuple, rows: list) -> None:
    if not rows:
        return
    placeholders = ", ".join(["%s"] * len(cols))
    updatable = [c for c in cols if c != "id"]
    set_clause = ", ".join(f"{c} = EXCLUDED.{c}" for c in updatable)
    sql = (
        f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders}) "
        f"ON CONFLICT (id) DO UPDATE SET {set_clause}"
    )
    with pg.cursor() as cur:
        for i in range(0, len(rows), BATCH):
            cur.executemany(sql, rows[i : i + BATCH])


def reset_sequence(pg: "psycopg.Connection", table: str) -> None:
    with pg.cursor() as cur:
        cur.execute(
            "SELECT setval("
            "  pg_get_serial_sequence(%s, 'id'),"
            "  GREATEST(COALESCE((SELECT MAX(id) FROM " + table + "), 0), 1),"
            "  (SELECT COUNT(*) > 0 FROM " + table + ")"
            ")",
            (table,),
        )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", action="store_true", help="actually write to PostgreSQL (default: dry run)")
    ap.add_argument("--truncate", action="store_true", help="TRUNCATE target tables before copying")
    args = ap.parse_args()

    src_url = os.environ.get("SOURCE_MYSQL_URL")
    dst_url = os.environ.get("TARGET_PG_URL")
    if not src_url or not dst_url:
        return "Set SOURCE_MYSQL_URL and TARGET_PG_URL environment variables first."

    mysql_cfg = parse_mysql(src_url)

    print(f"Source MySQL : {mysql_cfg['user']}@{mysql_cfg['host']}:{mysql_cfg['port']}/{mysql_cfg['database']}")
    src_counts = count_rows_mysql(mysql_cfg)
    for t, n in src_counts.items():
        print(f"  {t:<12} {n:>8} rows")

    with psycopg.connect(dst_url, autocommit=False) as pg:
        host = pg.info.host
        print(f"Target Postgres: {pg.info.user}@{host}/{pg.info.dbname}")
        before = count_rows_pg(pg)
        for t, n in before.items():
            print(f"  {t:<12} {n:>8} rows (before)")

        if not args.run:
            print("\nDry run only. Re-run with --run to copy.")
            return 0

        if args.truncate:
            with pg.cursor() as cur:
                cur.execute(f"TRUNCATE {', '.join(TABLES)} RESTART IDENTITY")
            print("\nTruncated target tables.")

        total = 0
        for table, cols, rows in read_source(mysql_cfg):
            upsert(pg, table, cols, rows)
            reset_sequence(pg, table)
            total += len(rows)
            print(f"  copied {len(rows):>8} rows -> {table}")

        pg.commit()

        after = count_rows_pg(pg)
        print("\nDone. Target row counts:")
        ok = True
        for t in TABLES:
            match = "OK" if after[t] >= src_counts[t] else "MISMATCH"
            ok &= after[t] >= src_counts[t]
            print(f"  {t:<12} {after[t]:>8} rows  [{match}]")
        return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
