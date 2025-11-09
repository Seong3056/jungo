@echo off
chcp 65001 >nul
cd /d "%~dp0"   :: 💡 start.bat이 있는 폴더를 기준으로 경로 고정

title 🚀 Jungo All-in-One Server Starter (v2.3 / Python 3.13)
echo ==============================================
echo  Jungo 서버 실행 (.env + Python 3.13 고정 + Daphne 재시작 지원)
echo ==============================================

:: ===== 0️⃣ Python 3.13 확인 =====
where python >nul 2>&1
if errorlevel 1 (
    echo ⚠️ Python이 설치되어 있지 않습니다.
    echo 👉 https://www.python.org/downloads/release/python-3135/ 에서 설치 후 "Add Python to PATH" 체크!
    pause
    exit /b
)

for /f "tokens=2 delims= " %%a in ('python --version 2^>^&1') do set PY_VER=%%a
echo 현재 Python 버전: %PY_VER%

echo %PY_VER% | find "3.13" >nul
if errorlevel 1 (
    echo ⚠️ Python 3.13이 아닙니다. py -3.13 명령어를 시도합니다...
    py -3.13 --version >nul 2>&1
    if errorlevel 1 (
        echo ❌ Python 3.13이 설치되어 있지 않거나 PATH에 등록되지 않았습니다.
        echo 👉 https://www.python.org/downloads/release/python-3135/ 에서 Python 3.13 설치 후 재시도하세요.
        pause
        exit /b
    )
    set PY_CMD=py -3.13
) else (
    echo ✅ Python 3.13이 감지되었습니다.
    set PY_CMD=python
)

:: ===== 1️⃣ .env 불러오기 =====
setlocal enabledelayedexpansion
if exist ".env.windows" (
    echo 📄 .env 파일 감지됨 → 환경변수 로드 중...
    for /f "usebackq tokens=1,2 delims==" %%A in (".env.windows") do (
        set "%%A=%%B"
    )
) else (
    echo ⚠️ .env 파일이 없습니다. 기본값으로 실행합니다.
)

if not defined DB_PATH set "DB_PATH=./db.sqlite3"
if not defined UNO_PORT set "UNO_PORT=COM3"
if not defined UNO_BAUD set "UNO_BAUD=9600"

echo 🧩 설정 요약:
echo   DB_PATH = %DB_PATH%
echo   UNO_PORT = %UNO_PORT%
echo   UNO_BAUD = %UNO_BAUD%

:: ===== 2️⃣ 가상환경 =====
if not exist ".venv" (
    echo 🌱 Python 3.13 기반 가상환경 생성 중...
    %PY_CMD% -m venv .venv
    if errorlevel 1 (
        echo ❌ 가상환경 생성 실패. Python 3.13 경로를 확인하세요.
        pause
        exit /b
    )
)
call .venv\Scripts\activate
if errorlevel 1 (
    echo ❌ 가상환경 활성화 실패. .venv 폴더 삭제 후 다시 시도하세요.
    pause
    exit /b
)
echo ✅ 가상환경 활성화 완료

:: ===== 3️⃣ 패키지 설치 =====
echo 📦 pip 최신화 중...
%PY_CMD% -m pip install --upgrade pip >nul

if exist "requirements.txt" (
    echo 📦 requirements.txt 기반 의존성 설치 중...
    pip install -r requirements.txt
) else (
    echo ⚠️ requirements.txt 없음 → Python 3.13 호환 기본 패키지 설치
    pip install ^
        "Django==5.2.8" ^
        "channels==4.1.0" ^
        "daphne==4.1.2" ^
        "requests==2.32.3" ^
        "pyserial==3.5" ^
        "python-dotenv==1.0.1"
)
echo ✅ 패키지 설치 완료

:: ===== 4️⃣ DB 마이그레이션 =====
if not exist "manage.py" (
    echo ❌ manage.py 파일이 없습니다. 현재 폴더를 확인하세요.
    pause
    exit /b
)
echo 🧱 DB 마이그레이션 실행...
%PY_CMD% manage.py makemigrations
%PY_CMD% manage.py migrate
%PY_CMD% manage.py collectstatic --noinput

:: ===== 5️⃣ Daphne 재시작 =====
echo 🚦 Daphne 서버 상태 확인 중...

for /f "tokens=5" %%P in ('netstat -ano ^| find ":8000" ^| find "LISTENING"') do (
    echo ⚠️ 포트 8000 점유 중인 프로세스 종료 중 (PID %%P)
    taskkill /PID %%P /F >nul 2>&1
)

for /f "tokens=2 delims=," %%p in ('wmic process where "CommandLine like '%%daphne%%'" get ProcessId /format:csv 2^>nul') do (
    taskkill /PID %%p /F >nul 2>&1
)

echo 🚀 새 Daphne 서버 실행 중...
start "" cmd /k "%PY_CMD% -m daphne -b 0.0.0.0 -p 8000 core.asgi:application"

:: ===== 6️⃣ RaspberryPi + Arduino 통신 =====
set "PI_SCRIPT=embedded\raspberry_pi.py"
echo 🤖 RaspberryPi 통신 프로세스 확인 중...
for /f "tokens=1" %%p in ('tasklist /fi "imagename eq python.exe" /v ^| find "raspberry_pi.py"') do (
    echo ⚠️ 기존 raspberry_pi.py 종료 중 (PID %%p)
    taskkill /pid %%p /f >nul 2>&1
)

if exist "%PI_SCRIPT%" (
    echo 🤖 raspberry_pi.py 실행 중...
    start "" cmd /k "%PY_CMD% "%PI_SCRIPT%" --db-path "%DB_PATH%" --uno-port "%UNO_PORT%" --uno-baudrate "%UNO_BAUD%"
) else (
    echo ⚠️ %PI_SCRIPT% 파일을 찾을 수 없습니다.
)

:: ===== 7️⃣ ngrok 실행 =====
where ngrok >nul 2>&1
if errorlevel 1 (
    echo ⚠️ ngrok이 설치되어 있지 않습니다.
    echo 👉 https://ngrok.com/download 에서 설치 후 PATH에 추가하세요.
) else (
    echo 🌐 ngrok 상태 점검 중...
    for /f "tokens=2 delims=," %%p in ('wmic process where "CommandLine like '%%ngrok http 8000%%'" get ProcessId /format:csv 2^>nul') do (
        echo ⚙️ 기존 ngrok 프로세스 종료 중 (PID %%p)
        taskkill /pid %%p /f >nul 2>&1
    )
    echo 🚀 ngrok 새 터널 실행 중...
    start "" cmd /k "ngrok http 8000 --request-header-add='ngrok-skip-browser-warning:true'"
)

echo ==============================================
echo ✅ Jungo 서버 + Daphne + RaspberryPi 실행 완료!
echo - 관리자 페이지: http://127.0.0.1:8000/admin
echo - ngrok 주소: ngrok 창에서 Forwarding URL 확인
echo ==============================================
pause
