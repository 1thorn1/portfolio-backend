# portfolio-backend

포트폴리오 사이트(방문자 카운트 · 방명록)용 Spring Boot API 서버.

- **Stack**: Java 17, Spring Boot 4.1, Spring Data JPA, PostgreSQL
- **배포**: [Render](https://render.com) (Docker) — `master` push 시 자동 배포
- **프론트엔드**: [1thorn1/portfolio-frontend](https://github.com/1thorn1/portfolio-frontend) (Vercel)

## API

| Method | Path | 설명 |
|---|---|---|
| `GET` | `/api/visitors/count` | 누적 방문자 수 |
| `GET` | `/api/comments` | 방명록 목록 |
| `POST` | `/api/comments` | 방명록 작성 — body `{ "author": "...", "content": "..." }` |
| `DELETE` | `/api/comments/{id}` | 방명록 삭제 — header `X-Admin-Key: <ADMIN_SECRET_KEY>` |

CORS 허용 오리진은 `src/main/java/com/juhee/portfolio_backend/config/WebConfig.java` 에서 관리.

## 로컬 실행

PostgreSQL 17이 필요합니다 (Docker 예시):

```bash
docker run -d --name portfolio-pg \
  -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=portfolio \
  -p 5432:5432 postgres:17-alpine

cp src/main/resources/application.properties.example src/main/resources/application.properties
export ADMIN_SECRET_KEY=local-dev-key

./gradlew bootRun
```

기본값은 `application.properties.example` 참고. 아래 환경변수로 덮어쓸 수 있습니다.

| 변수 | 기본값 | 용도 |
|---|---|---|
| `SPRING_DATASOURCE_URL` | `jdbc:postgresql://localhost:5432/portfolio` | DB 접속 URL |
| `SPRING_DATASOURCE_USERNAME` | `postgres` | DB 사용자 |
| `SPRING_DATASOURCE_PASSWORD` | `postgres` | DB 비밀번호 |
| `JPA_DDL_AUTO` | `update` | Hibernate 스키마 관리 모드 |
| `ADMIN_SECRET_KEY` | *(없음, 필수)* | 방명록 삭제 인증 키 |
| `PORT` | `8080` | 서버 포트 |

## Render 배포

배포는 저장소 루트의 [`render.yaml`](./render.yaml) 블루프린트로 관리합니다.

### 1. 최초 배포 (Blueprint)

1. https://dashboard.render.com/select-repo?type=blueprint 접속
2. GitHub 계정 연결 후 `1thorn1/portfolio-backend` 선택
3. `render.yaml`이 아래 두 리소스를 자동 생성:
   - **portfolio-db** — PostgreSQL (free, Singapore)
   - **portfolio-backend** — Docker 웹 서비스 (free, Singapore)
4. `ADMIN_SECRET_KEY` 값 입력 (`sync: false` 로 표시된 항목) → **Apply**
5. 첫 빌드 완료 후 서비스 URL 확인 — `onrender.com` 서브도메인은 전역 고유라
   이름이 겹치면 접미사가 붙습니다. 현재 배포 주소: `https://portfolio-backend-p51a.onrender.com`
   (이 값이 바뀌면 프론트엔드 `Portfolio.dc.html`의 `apiBase`도 함께 수정)

`DATABASE_URL`, DB 계정 등 나머지 환경변수는 `render.yaml`이 `portfolio-db`에서 자동 주입합니다.
컨테이너 시작 시 `docker-entrypoint.sh`가 Render의 `DATABASE_URL`(`postgresql://...`)을
Spring이 요구하는 JDBC URL + 계정으로 변환합니다.

### 2. 이후 배포 (자동)

`master` 브랜치에 push하면 Render가 Docker 이미지를 다시 빌드해 재배포합니다
(`render.yaml`의 `autoDeploy: true`). 수동 배포는 대시보드의
**Manual Deploy → Deploy latest commit**.

### 3. 헬스 체크

`healthCheckPath: /api/comments` — 200 응답이 없으면 배포가 롤백됩니다.
free 플랜은 15분 무활동 시 슬립하며, 첫 요청 시 콜드스타트에 ~30초 걸립니다.

### 4. 환경변수 요약 (Render)

| 변수 | 출처 |
|---|---|
| `DATABASE_URL` | `portfolio-db` (자동) |
| `SPRING_JPA_HIBERNATE_DDLAUTO` | `render.yaml` (`update`) |
| `ADMIN_SECRET_KEY` | 대시보드에서 수동 입력 |
| `PORT` | Render 자동 주입 → `docker-entrypoint.sh`가 `server.port`로 전달 |

## 데이터 마이그레이션 (Railway MySQL → Render PostgreSQL)

기존 Railway MySQL 데이터를 옮기려면 [`scripts/migrate_mysql_to_postgres.py`](./scripts/migrate_mysql_to_postgres.py) 사용:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install "pymysql>=1.1" "psycopg[binary]>=3.1"

export SOURCE_MYSQL_URL='mysql://root:PASSWORD@sakura.proxy.rlwy.net:43143/railway'
export TARGET_PG_URL='postgresql://portfolio:PASSWORD@dpg-xxxx-a.singapore-postgres.render.com/portfolio'

python scripts/migrate_mysql_to_postgres.py          # 드라이런 (행 수만 출력)
python scripts/migrate_mysql_to_postgres.py --run    # 실제 복사 (PK 기준 upsert)
```

- Render 백엔드가 한 번 부팅되어 테이블(`comment`, `visitor_log`)이 생성된 뒤 실행
- Railway MySQL 서비스가 실행 중이어야 함
- 완전히 새로 넣으려면 `--run --truncate`
