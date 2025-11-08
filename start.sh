#!/bin/bash
# 🚀 Jungo All-in-One Server Starter (Django + RaspberryPi + Arduino + Local ngrok Token)
# ========================================================================

# 0️⃣ 실행 권한 자동 부여 (자기 자신)
if [ ! -x "$0" ]; then
    echo "🔧 실행 권한이 없어 자동으로 부여 중..."
    chmod +x "$0"
    echo "✅ 권한 부여 완료"
fi

# 💡 현재 실행 경로를 스크립트 파일 위치로 고정
cd "$(dirname "$0")"

echo "=============================================="
echo " Jungo 서버 통합 실행 (.env + 로컬 ngrok 토큰)"
echo "=============================================="

# ===== 1️⃣ Python 설치 확인 =====
if ! command -v python3 &> /dev/null; then
    echo "⚠️ Python3이 설치되어 있지 않습니다."
    echo "👉 설치 명령: sudo apt install python3 python3-venv python3-pip -y"
    exit 1
fi
echo "✅ Python3 감지됨"

# ===== 2️⃣ 가상환경 생성 및 활성화 =====
if [ ! -d ".venv" ]; then
    echo "🌱 가상환경 생성 중..."
    python3 -m venv .venv || { echo "❌ 가상환경 생성 실패."; exit 1; }
fi

source .venv/bin/activate
echo "✅ 가상환경 활성화 완료"

# ===== 3️⃣ .env 불러오기 =====
if [ -f ".env" ]; then
    echo "📄 .env 파일 감지됨 → 환경 변수 로드 중..."
    export $(grep -v '^#' .env | xargs)
else
    echo "⚠️ .env 파일이 없습니다. 기본값으로 실행합니다."
fi

# ===== 4️⃣ 기본값 설정 =====
SCRIPT_DIR="$(dirname "$(realpath "$0")")"
DB_PATH="${DB_PATH:-$SCRIPT_DIR/db.sqlite3}"
UNO_PORT="${UNO_PORT:-/dev/ttyACM0}"
UNO_BAUD="${UNO_BAUD:-9600}"

echo "🧩 설정 요약:"
echo "  DB_PATH = $DB_PATH"
echo "  UNO_PORT = $UNO_PORT"
echo "  UNO_BAUD = $UNO_BAUD"

# ===== 5️⃣ 의존성 설치 =====
echo "📦 pip 최신화 중..."
python -m pip install --upgrade pip >/dev/null

if [ -f "requirements.txt" ]; then
    echo "📦 requirements.txt 기반 의존성 설치 중..."
    pip install -r requirements.txt
else
    pip install "Django==5.2.8" "channels==4.1.0" "daphne==4.1.2" "requests==2.32.3" "pyserial==3.5" "python-dotenv==1.0.1"
fi
echo "✅ 패키지 설치 완료"

# ===== 6️⃣ DB 마이그레이션 =====
echo "🧱 데이터베이스 마이그레이션 실행..."
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput

# ===== 7️⃣ Daphne 재시작 =====
EXIST_PID=$(lsof -t -i:8000)
if [ -n "$EXIST_PID" ]; then
    echo "⚠️ 포트 8000 점유 중인 프로세스 종료 중 (PID: $EXIST_PID)"
    kill -9 "$EXIST_PID"
    sleep 0.5
fi
nohup python -m daphne -b 0.0.0.0 -p 8000 core.asgi:application > server.log 2>&1 &
echo "✅ Daphne 실행 완료"


# ===== 8️⃣ RaspberryPi + Arduino 통신 =====
PI_SCRIPT="embedded/raspberry_pi.py"
EXIST_PI=$(pgrep -f "raspberry_pi.py")
if [ -n "$EXIST_PI" ]; then
    echo "⚠️ 기존 raspberry_pi.py 종료 중 (PID: $EXIST_PI)"
    kill -9 "$EXIST_PI"
    sleep 0.5
fi

if [ -f "$PI_SCRIPT" ]; then
    echo "🤖 raspberry_pi.py 실행 중..."
    nohup python3 "$PI_SCRIPT" \
        --db-path "$DB_PATH" \
        --uno-port "$UNO_PORT" \
        --uno-baudrate "$UNO_BAUD" \
        > pi.log 2>&1 &
    echo "✅ RaspberryPi 프로세스 시작됨 (로그: pi.log)"
else
    echo "⚠️ $PI_SCRIPT 파일을 찾을 수 없습니다."
fi

# ===== 9️⃣ ngrok 실행 =====
if command -v ngrok &> /dev/null; then
    EXIST_NGROK=$(pgrep -f "ngrok http 8000")
    if [ -n "$EXIST_NGROK" ]; then
        echo "⚙️ 기존 ngrok 프로세스 종료 중 (PID: $EXIST_NGROK)"
        kill -9 "$EXIST_NGROK"
        sleep 1
    fi
    echo "🚀 ngrok 터널 새로 시작 중..."
    nohup ngrok http 8000 --request-header-add='ngrok-skip-browser-warning:true' > ngrok.log 2>&1 &
    sleep 2
    echo "✅ ngrok 실행됨 (로그: ngrok.log)"
else
    echo "⚠️ ngrok이 설치되어 있지 않습니다. 설치 명령: sudo apt install ngrok -y"
fi


echo "=============================================="
echo "✅ Jungo 서버 + RaspberryPi 자동실행 완료!"
echo "- 관리자 페이지: http://127.0.0.1:8000/admin"
echo "- ngrok 주소: ngrok.log 확인"
echo "- 로그: server.log / pi.log / ngrok.log"
echo "=============================================="
