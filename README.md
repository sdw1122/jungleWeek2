# 식물 성장형 선물 플랫폼

Flask, PostgreSQL, HTML, CSS, JavaScript 기반의 기본 프로젝트입니다.

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
