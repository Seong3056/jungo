@echo off
chcp 65001 >nul
title 🚀 Jungo All-in-One Server Starter (Safe Mode)
echo ==============================================
echo  Jungo 서버 원클릭 실행 (안전 버전)
echo ==============================================

:: ===== 0️⃣ Python 설치 확인 =====
python --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Python이 설치되어 있지 않습니다.
    echo 👉 https://www.python.org/downloads 에서 설치 후 "Add Python to PATH"를 꼭 체크하세요.
    pause
    exit /b
)
echo ✅ Python이 감지되었습니다.

:: ===== 1️⃣ 가상환경 생성 및 활성화 =====
if not exist ".venv" (
    echo 🌱 가상환경 생성 중...
    python -m venv .venv
    if errorlevel 1 (
        echo ❌ 가상환경 생성 실패. Python이 손상되었을 수 있습니다.
        pause
        exit /b
    )
)
call .venv\Scripts\activate
if errorlevel 1 (
    echo ❌ 가상환경 활성화 실패. .venv 폴더를 삭제 후 다시 시도하세요.
    pause
    exit /b
)
echo ✅ 가상환경 활성화 완료

:: ===== 2️⃣ pip / 의존성 설치 =====
echo 📦 pip 최신 버전 확인 중...
python -m pip install --upgrade pip >nul

if exist "requirements.txt" (
    echo 📦 requirements.txt 기반 의존성 설치 중...
    pip install -r requirements.txt
) else (
    echo ⚠️ requirements.txt가 없습니다. 기본 패키지 설치 중...
    pip install django>=5.0.6,<6 djangorestframework>=3.15,<4 pillow>=10.0 python-dotenv>=1.0 channels>=4.0,<5 channels-redis>=4.1,<5 whitenoise>=6.6 daphne>=4.1
)
echo ✅ 패키지 설치 완료

:: ===== 3️⃣ 데이터베이스 마이그레이션 =====
echo 🧱 DB 마이그레이션 실행...
if not exist "manage.py" (
    echo ❌ manage.py 파일이 없습니다. 현재 폴더를 확인하세요.
    pause
    exit /b
)

if exist "db.sqlite3" (
    echo ✅ 기존 DB가 감지되었습니다. 삭제하지 않고 그대로 유지합니다.
) else (
    echo ⚙️ 새 DB를 생성합니다.
)

python manage.py makemigrations
python manage.py migrate

:: ===== 4️⃣ 정적 파일 수집 =====
echo 🎨 정적 파일 수집 (collectstatic)...
python manage.py collectstatic --noinput

:: ===== 5️⃣ Django 슈퍼유저 생성 =====
echo 👤 관리자 계정을 생성할까요? (y/n)
set /p CREATE_SUPERUSER=
if /i "%CREATE_SUPERUSER%"=="Y" (
    python manage.py createsuperuser
) else (
    echo 관리자 생성 생략
)

:: ===== 6️⃣ Daphne 서버 실행 =====
echo 🚀 Daphne 서버 실행 중 (포트 8000)
start cmd /k "python -m daphne -b 0.0.0.0 -p 8000 core.asgi:application"

:: ===== 7️⃣ ngrok 터널링 =====
where ngrok >nul 2>&1
if errorlevel 1 (
    echo ⚠️ ngrok이 설치되어 있지 않습니다.
    echo 👉 https://ngrok.com/download 에서 다운로드 후 환경 변수에 등록하세요.
    echo (ngrok 없이도 로컬 서버는 정상 작동합니다.)
) else (
    echo 🌐 ngrok 터널링 시작...
    start cmd /k "ngrok http 8000 --request-header-add='ngrok-skip-browser-warning:true'"
)

echo ==============================================
echo ✅ Jungo 서버가 실행되었습니다!
echo - Django 관리페이지: http://127.0.0.1:8000/admin
echo - ngrok 외부 URL: ngrok 창의 Forwarding 주소 확인
echo ==============================================
pause
