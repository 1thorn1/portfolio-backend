#!/bin/sh
set -e

# Render injects DATABASE_URL as: postgresql://user:password@host:port/dbname
# Spring needs a JDBC URL plus separate credentials, so split it here.
if [ -n "$DATABASE_URL" ]; then
  no_proto="${DATABASE_URL#*://}"
  creds="${no_proto%%@*}"
  hostpath="${no_proto#*@}"
  : "${SPRING_DATASOURCE_USERNAME:=${creds%%:*}}"
  : "${SPRING_DATASOURCE_PASSWORD:=${creds#*:}}"
  export SPRING_DATASOURCE_USERNAME SPRING_DATASOURCE_PASSWORD
  export SPRING_DATASOURCE_URL="jdbc:postgresql://${hostpath}"
fi

# Render expects the app on $PORT (default 10000) bound to 0.0.0.0.
PORT="${PORT:-10000}"
echo "[entrypoint] starting on 0.0.0.0:${PORT}"

exec java \
  -Dserver.port="${PORT}" \
  -Dserver.address=0.0.0.0 \
  -Dadmin.secret-key="${ADMIN_SECRET_KEY}" \
  -jar /app/app.jar
