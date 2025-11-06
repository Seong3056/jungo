@echo off
chcp 65001 >nul
title 🚀 Jungo All-in-One Server Starter (.env + Local ngrok Token)
echo ==============================================
echo  Jungo 서버 실행 (.env + 로컬 ngrok 토큰)
echo ==============================================

:: ===== 1️⃣ Python 확인 =====
python --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️ Python이 설치되어 있지 않습니다.
    echo 👉 https://www.python.org/downloads 에서 설치 후 "Add Python to PATH"를 꼭 체크하세요.
    pause
    exit /b
)
echo ✅ Python 감지됨

:: ===== 2️⃣ .env 불러오기 =====
setlocal enabledelayedexpansion
if exist ".env.windows" (
    echo 📄 .env.windows 파일 감지됨 → 환경변수 로드 중...
    for /f "usebackq tokens=1,2 delims==" %%A in (".env.windows") do (
        set "%%A=%%B"
    )
) else if exist ".env" (
    echo 📄 기본 .env 파일 감지됨 → 로드 중...
    for /f "usebackq tokens=1,2 delims==" %%A in (".env") do (
        set "%%A=%%B"
    )
) else (
    echo ⚠️ .env 파일이 없습니다. 기본값으로 실행합니다.
)

if not defined DB_PATH set "DB_PATH=%cd%\db.sqlite3"
if not defined UNO_PORT set "UNO_PORT=COM3"
if not defined UNO_BAUD set "UNO_BAUD=9600"

echo 🧩 설정 요약:
echo   DB_PATH = %DB_PATH%
echo   UNO_PORT = %UNO_PORT%
echo   UNO_BAUD = %UNO_BAUD%

:: ===== 3️⃣ 가상환경 =====
if not exist ".venv" (
    echo 🌱 가상환경 생성 중...
    python -m venv .venv
)
call .venv\Scripts\activate
if errorlevel 1 (
    echo ❌ 가상환경 활성화 실패. .venv 폴더를 삭제 후 다시 시도하세요.
    pause
    exit /b
)
echo ✅ 가상환경 활성화 완료

:: ===== 4️⃣ 패키지 설치 =====
echo 📦 pip 최신화 중...
python -m pip install --upgrade pip >nul

if exist "requirements.txt" (
    echo 📦 requirements.txt 기반 의존성 설치 중...
    pip install -r requirements.txt
) else (
    pip install "Django==5.2.8" "channels==4.1.0" "daphne==4.1.2" "requests==2.32.3" "pyserial==3.5" "python-dotenv==1.0.1"
)
echo ✅ 패키지 설치 완료

:: ===== 5️⃣ DB 마이그레이션 =====
if not exist "manage.py" (
    echo ❌ manage.py 파일이 없습니다. 현재 폴더를 확인하세요.
    pause
    exit /b
)
echo 🧱 DB 마이그레이션 실행...
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput

:: ===== 6️⃣ Daphne 서버 재시작 =====
echo 🚦 Daphne 서버 상태 확인 중...
for /f "tokens=1" %%p in ('tasklist /fi "imagename eq python.exe" /v ^| find "daphne"') do (
    echo ⚠️ 기존 Daphne 프로세스 종료 중 (PID %%p)
    taskkill /pid %%p /f >nul 2>&1
)
echo 🚀 새 Daphne 서버 실행 중...
start "" cmd /k "python -m daphne -b 0.0.0.0 -p 8000 core.asgi:application"

:: ===== 7️⃣ RaspberryPi + Arduino 통신 =====
set "PI_SCRIPT=embedded\raspberry_pi.py"
echo 🤖 RaspberryPi 통신 프로세스 확인 중...
for /f "tokens=1" %%p in ('tasklist /fi "imagename eq python.exe" /v ^| find "raspberry_pi.py"') do (
    echo ⚠️ 기존 raspberry_pi.py 종료 중 (PID %%p)
    taskkill /pid %%p /f >nul 2>&1
)

if exist "%PI_SCRIPT%" (
    echo 🤖 raspberry_pi.py 실행 중...
    start "" cmd /k "python %PI_SCRIPT% --db-path \"%DB_PATH%\" --uno-port %UNO_PORT% --uno-baudrate %UNO_BAUD%"
) else (
    echo ⚠️ %PI_SCRIPT% 파일을 찾을 수 없습니다.
)

:: ===== 8️⃣ ngrok 실행 (로컬 저장소 토큰 감지) =====
where ngrok >nul 2>&1
if errorlevel 1 (
    echo ⚠️ ngrok이 설치되어 있지 않습니다.
    echo 👉 https://ngrok.com/download 에서 설치 후 PATH에 추가하세요.
) else (
    echo 🌐 ngrok 터널링 시작 중...
    if exist "%USERPROFILE%\.ngrok2\ngrok.yml" (
        echo ✅ ngrok 로컬 설정 감지됨 → 저장된 토큰으로 실행 중...
    ) else (
        echo ⚠️ ngrok 로컬 설정이 없습니다. 무료 임시 세션으로 실행합니다.
    )
    start "" cmd /k "ngrok http 8000 --request-header-add='ngrok-skip-browser-warning:true'"
)

echo ==============================================
echo ✅ Jungo 서버 + RaspberryPi 실행 완료!
echo - 관리자 페이지: http://127.0.0.1:8000/admin
echo - ngrok 주소: ngrok 창에서 Forwarding URL 확인
echo ==============================================
pause
