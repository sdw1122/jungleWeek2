# 식물 성장형 선물 플랫폼

Flask, PostgreSQL, HTML, CSS, JavaScript 기반의 기본 프로젝트입니다.

## Docker로 실행

Docker Desktop을 실행한 뒤 프로젝트 폴더에서 다음 명령을 실행합니다.

```powershell
docker compose up --build
```

- 웹 화면: `http://localhost:5000`
- DB 상태 확인: `http://localhost:5000/health`
- 컨테이너 상태: `docker compose ps`
- 로그 확인: `docker compose logs -f web db`
- DB 테이블 확인: `docker compose exec db psql -U plant_user -d plant_app -c "\dt"`
- 종료: `docker compose down`

PostgreSQL 데이터는 `postgres_data` 볼륨에 유지됩니다. 최초 볼륨 생성 시
`db/init/001_create_schema.sql`이 자동으로 적용됩니다.

초기 SQL부터 완전히 다시 적용해야 할 때만 아래 명령을 사용합니다. 이 명령은
컨테이너 DB 데이터를 모두 삭제합니다.

```powershell
docker compose down -v
docker compose up --build
```

## 로컬에서 실행

먼저 PostgreSQL을 설치하고 아래 정보로 데이터베이스를 준비합니다.

```text
데이터베이스: plant_app
사용자: plant_user
비밀번호: plant_password
```

PowerShell에서 가상환경과 패키지를 준비합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

애플리케이션을 실행합니다.

```powershell
flask --app run:app run --debug
```

- 웹 화면: `http://localhost:5000`
- DB 상태 확인: `http://localhost:5000/health`

## 주요 폴더

```text
app/
├── models/          # SQLAlchemy 모델
├── routes/          # Flask 라우트
├── services/        # 서비스 로직
├── static/
│   ├── css/         # CSS
│   ├── images/      # 이미지
│   └── js/          # JavaScript
└── templates/       # HTML 템플릿
db/
└── init/            # PostgreSQL 초기화 SQL
```
