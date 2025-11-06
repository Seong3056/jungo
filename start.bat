@echo off
chcp 65001 >nul
title 🚀 Jungo All-in-One Server Starter (Safe Mode)
echo ==============================================
echo  Jungo 서버 원클릭 실행 (안전 버전)
echo ==============================================

:: ===== 0️⃣ Python 설치 확인 =====
python --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️ Python이 설치되어 있지 않습니다.
    echo 👉 https://www.python.org/downloads 에서 설치 후 "Add Python to PATH" 옵션을 꼭 체크하세요.
    pause
    exit /b
)
echo ✅ Python 감지 완료

:: ===== 1️⃣ 가상환경 생성 및 활성화 =====
if not exist ".venv" (
    echo 🌱 가상환경 생성 중...
    python -m venv .venv
    if errorlevel 1 (
        echo ❌ 가상환경 생성 실패. Python 환경을 확인하세요.
        pause
        exit /b
    )
)
call .venv\Scripts\activate
if errorlevel 1 (
    echo ❌ 가상환경 활성화 실패. ".venv" 폴더를 삭제 후 재시도하세요.
    pause
    exit /b
)
echo ✅ 가상환경 활성화 완료

:: ===== 2️⃣ pip / 의존성 설치 =====
echo 📦 pip 최신화 중...
python -m pip install --upgrade pip >nul

if exist "requirements.txt" (
    echo 📦 requirements.txt 기반 의존성 설치 중...
    pip install -r requirements.txt
) else (
    echo ⚠️ requirements.txt가 없습니다. 기본 패키지를 설치합니다.
    pip install "Django==5.2.8" "djangorestframework==3.15.2" "channels==4.1.0" "daphne==4.1.2" ^
    "twisted==24.3.0" "asgiref==3.8.1" "requests==2.32.3" "pyserial==3.5" ^
    "opencv-python==4.10.0.84" "Pillow==10.4.0" "tzdata==2025.1" "whitenoise==6.7.0" "python-dotenv==1.0.1"
)
echo ✅ 패키지 설치 완료

:: ===== 3️⃣ 데이터베이스 마이그레이션 =====
echo 🧱 데이터베이스 마이그레이션 실행 중...
if not exist "manage.py" (
    echo ❌ manage.py 파일을 찾을 수 없습니다. 프로젝트 루트를 확인하세요.
    pause
    exit /b
)

if exist "db.sqlite3" (
    echo ✅ 기존 DB 유지: db.sqlite3
) else (
    echo ⚙️ 새 SQLite DB 생성...
)
python manage.py makemigrations
python manage.py migrate

:: ===== 4️⃣ 정적 파일 수집 =====
echo 🎨 정적 파일 수집 (collectstatic)...
python manage.py collectstatic --noinput

:: ===== 6️⃣ Daphne 서버 실행 =====
echo 🚀 Daphne 서버 실행 중 (포트 8000)
start cmd /k "python -m daphne -b 0.0.0.0 -p 8000 core.asgi:application"

:: ===== 7️⃣ Ngrok 터널링 (선택적) =====
where ngrok >nul 2>&1
if errorlevel 1 (
    echo ⚠️ ngrok이 설치되어 있지 않습니다.
    echo 👉 https://ngrok.com/download 에서 다운로드 후 환경변수 등록하세요.
) else (
    echo 🌐 ngrok 터널링 시작...
    start cmd /k "ngrok http 8000 --request-header-add='ngrok-skip-browser-warning:true'"
)

echo ==============================================
echo ✅ Jungo 서버가 정상적으로 실행되었습니다!
echo - 관리자 페이지: http://127.0.0.1:8000/admin
echo - ngrok 외부 URL: ngrok 창의 Forwarding 주소 확인
echo ==============================================
pause