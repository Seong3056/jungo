@echo off
chcp 65001 >nul
title 🚀 Jungo All-in-One Server Starter
echo ==============================================
echo  Jungo 서버 원클릭 실행 스크립트
echo ==============================================

:: ===== 0️⃣ Python 설치 확인 =====
python --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Python이 설치되어 있지 않습니다. https://www.python.org/downloads 에서 설치 후 다시 실행하세요.
    pause
    exit /b
)

:: ===== 1️⃣ 가상환경 생성 및 활성화 =====
if not exist ".venv" (
    echo 🌱 가상환경 생성 중...
    python -m venv .venv
)
call .venv\Scripts\activate
echo ✅ 가상환경 활성화 완료

:: ===== 2️⃣ 의존성 설치 =====
if exist "requirements.txt" (
    echo 📦 requirements.txt 기반으로 의존성 설치 중...
    pip install --upgrade pip
    pip install -r requirements.txt
) else (
    echo ⚠️ requirements.txt가 없습니다. 기본 의존성 세트를 설치합니다.
    pip install django channels daphne whitenoise pillow requests
)

:: ===== 3️⃣ DB 초기화 및 마이그레이션 =====
echo 🧱 데이터베이스 마이그레이션 실행...
if exist "db.sqlite3" (
    echo 기존 DB 삭제 중...
    del /f /q db.sqlite3
)
python manage.py makemigrations
python manage.py migrate

:: ===== 4️⃣ 정적파일 수집 =====
echo 🎨 정적 파일 수집 중 (collectstatic)...
python manage.py collectstatic --noinput

:: ===== 5️⃣ Django 슈퍼유저 생성 여부 =====
echo 👤 관리자 계정을 생성할까요? (y/n)
set /p CREATE_SUPERUSER=
if /i "%CREATE_SUPERUSER%"=="Y" (
    python manage.py createsuperuser
) else (
    echo 관리자 생성 생략
)

:: ===== 6️⃣ Daphne 서버 실행 =====
echo 🚀 Daphne 서버 실행 중... (포트 8000)
start cmd /k "python -m daphne -b 0.0.0.0 -p 8000 core.asgi:application"

:: ===== 7️⃣ ngrok 터널링 (외부 접근용) =====
where ngrok >nul 2>&1
if errorlevel 1 (
    echo ⚠️ ngrok이 설치되어 있지 않습니다.
    echo 👉 https://ngrok.com/download 에서 다운로드 후 환경 변수에 등록하세요.
    echo.
    echo (ngrok을 설치하지 않아도 로컬 서버는 정상 작동합니다.)
) else (
    echo 🌐 ngrok 터널링을 시작합니다...
    start cmd /k "ngrok http 8000 --request-header-add='ngrok-skip-browser-warning:true'"
)

echo ==============================================
echo ✅ Jungo 서버가 실행되었습니다!
echo - Django 관리페이지: http://127.0.0.1:8000/admin
echo - ngrok 외부 URL: ngrok 창에서 Forwarding 주소 확인
echo ==============================================
pause
