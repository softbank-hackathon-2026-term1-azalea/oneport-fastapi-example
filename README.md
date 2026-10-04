# Oneport FastAPI 배포 예제

Oneport 플랫폼의 기본 빌드 경로로 배포할 수 있도록 FastAPI 앱만 분리한 저장소입니다. Python 3.13, FastAPI, SQLAlchemy, Alembic을 사용하며 `Dockerfile`, `pyproject.toml`, `uv.lock`, 앱 소스가 모두 저장소 루트에 있습니다.

## 플랫폼 배포 설정

| 항목 | 값 |
| --- | --- |
| 저장소 | `https://github.com/softbank-hackathon-2026-term1-azalea/oneport-fastapi-example` |
| 브랜치 또는 태그 | `1.1.3` 또는 `1.2.1` (`main`은 `1.2.1`) |
| 빌드 컨텍스트 | `.` |
| Dockerfile 경로 | `Dockerfile` |
| 컨테이너 포트 | `8080` |
| Health 경로 | `/health` |
| Readiness 경로 | `/ready` |
| 마이그레이션 명령 | `sh scripts/start.sh migrate` |

앱에는 PostgreSQL이 필요합니다. 플랫폼에서 DB를 연결해 `DATABASE_URL`을 주입하세요. 캐시 기능은 `1.2.1`에서 `REDIS_URL`을 연결하면 활성화됩니다. 두 이미지 모두 `USER 999:999`로 실행되므로 Kubernetes의 `runAsNonRoot` 검증을 지원합니다.

플랫폼이 저장소 허용 목록을 사용한다면 운영자가 `platform/deployment/build.json`의 `repositories`에 위 저장소 URL을 추가하고 실행 중인 API와 빌드 Worker에 같은 설정을 적용해야 합니다. 저장소 생성만으로 해당 허용 목록이 변경되지는 않습니다.

## 배포 체크포인트

태그에는 `v` 접두사가 없습니다. 앱 코드와 잠금 파일은 원본의 해당 버전에서 그대로 가져왔습니다.

| 태그 | 기능 | 원본 태그 / 커밋 |
| --- | --- | --- |
| `1.1.3` | 노트 생성·조회·삭제, 완료 상태 변경, DB 마이그레이션 | [`v1.1.3`](https://github.com/softbank-hackathon-2026-term1-azalea/oneport-platform-app-example/tree/v1.1.3), `994d736e5e6b85eec6d250e5d9b666e6dcf74680` |
| `1.2.1` | 위 기능 + Redis/Valkey 방문 수 카운터와 캐시 readiness 확인 | [`v1.2.1`](https://github.com/softbank-hackathon-2026-term1-azalea/oneport-platform-app-example/tree/v1.2.1), `111278bf8fb86eaeaaa73e345928808781300b85` |

두 버전은 같은 V2 DB 스키마를 사용합니다. `1.1.3 → 1.2.1 → 1.1.3` 순서로 배포하면서 노트 유지와 캐시 기능의 추가·제거를 확인할 수 있습니다. `1.2.1`로 다시 배포하면 같은 캐시의 방문 수를 이어서 사용합니다. 이 두 체크포인트 사이에는 새 DB 마이그레이션이 없습니다.

## 환경변수

| 변수 | 설명 |
| --- | --- |
| `DATABASE_URL` | PostgreSQL 접속 URL. 지정하면 `DB_*`보다 우선합니다. 비밀번호는 플랫폼 시크릿으로 주입합니다. |
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | `DATABASE_URL` 대신 사용할 개별 DB 접속 정보 |
| `REDIS_URL` | `1.2.1`의 선택적 Redis/Valkey 접속 URL. TLS 연결은 `rediss://`를 사용합니다. |
| `PORT` | 기본 `8080` |
| `LAUNCHPAD_RELEASE_ID` | 모든 응답의 `X-Launchpad-Release` 헤더에 반환하는 플랫폼 릴리즈 ID |
| `APP_COLOR` | 화면 배너 색상 |
| `APP_FORCE_UNHEALTHY` | `true`이면 `/health`가 503을 반환해 롤백을 시연할 수 있습니다. |
| `LOG_FORMAT`, `LOG_LEVEL` | 기본 `json`, `INFO` |
| `DOCS_ENABLED` | `true`이면 API 문서 활성화 |

`GET /version`은 코드의 버전, 빌드 시각, Git SHA, 인스턴스 이름을 반환합니다. `GIT_SHA`는 Docker 빌드 인자로 전달합니다. `/health`는 DB를 조회하지 않으며 `/ready`는 DB와 설정된 캐시를 확인합니다. `1.2.1`에서 캐시를 설정하지 않으면 `/ready`는 `cache: disabled`, `/visits`는 503을 반환합니다.

## 로컬 실행과 검증

Docker가 실행 중이어야 합니다. Compose는 앱과 PostgreSQL을 시작하며 `1.2.1`에서는 Valkey도 시작합니다.

```bash
git clone https://github.com/softbank-hackathon-2026-term1-azalea/oneport-fastapi-example.git
cd oneport-fastapi-example
git checkout 1.2.1
docker compose up --build
```

브라우저에서 `http://localhost:8080`을 엽니다. 테스트는 Testcontainers로 독립적인 DB와 필요한 캐시를 만듭니다.

```bash
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run mypy app tests
uv run pytest -q
docker build --platform linux/amd64 \
  --build-arg GIT_SHA="$(git rev-parse HEAD)" \
  -t oneport-fastapi-example:local .
```

컨테이너 시작 시 DB 연결을 기다린 후 Alembic 마이그레이션을 적용합니다. 마이그레이션은 PostgreSQL advisory lock으로 직렬화됩니다. 플랫폼이 별도 마이그레이션 Job을 실행할 때는 위의 마이그레이션 명령을 사용합니다.

CI는 `main`, 두 체크포인트 태그, PR에서 린트·타입 검사·통합 테스트·루트 Docker 빌드를 실행합니다.
