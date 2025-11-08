#!/bin/bash
# 🚀 Jungo All-in-One Server Starter (v2.2 / Python 3.11)
# ======================================================

# 0️⃣ 실행 권한 확인
if [ ! -x "$0" ]; then
    echo "🔧 실행 권한이 없어 자동으로 부여 중..."
    chmod +x "$0"
    echo "✅ 권한 부여 완료"
fi

cd "$(dirname "$0")"

echo "=============================================="
echo " Jungo 서버 실행 (.env + Python 3.11 고정 + Daphne 재시작 지원)"
echo "=============================================="

# ===== 1️⃣ Python 3.11 확인 =====
if ! command -v python3.11 &> /dev/null; then
    echo "⚠️ Python 3.11이 설치되어 있지 않습니다."
    echo "👉 sudo apt update && sudo apt install python3.11 python3.11-venv python3.11-dev -y"
    exit 1
fi
echo "✅ Python 3.11 감지됨"
PY_CMD="python3.11"

# ===== 2️⃣ .env 불러오기 =====
if [ -f ".env.linux" ]; then
    echo "📄 .env 파일 감지됨 → 환경변수 로드 중..."
    export $(grep -v '^#' .env.linux | xargs)
else
    echo "⚠️ .env 파일이 없습니다. 기본값으로 실행합니다."
fi

DB_PATH=${DB_PATH:-./db.sqlite3}
UNO_PORT=${UNO_PORT:-/dev/ttyACM0}
UNO_BAUD=${UNO_BAUD:-9600}

echo "🧩 설정 요약:"
echo "  DB_PATH = ${DB_PATH}"
echo "  UNO_PORT = ${UNO_PORT}"
echo "  UNO_BAUD = ${UNO_BAUD}"

# ===== 3️⃣ 가상환경 설정 =====
if [ ! -d ".venv" ]; then
    echo "🌱 Python 3.11 기반 가상환경 생성 중..."
    ${PY_CMD} -m venv .venv || { echo "❌ 가상환경 생성 실패"; exit 1; }
fi
source .venv/bin/activate || { echo "❌ 가상환경 활성화 실패"; exit 1; }
echo "✅ 가상환경 활성화 완료"

# ===== 4️⃣ 패키지 설치 =====
echo "📦 requirements.txt 설치 중..."
pip install --upgrade pip > /dev/null
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
else
    pip install "Django==5.2.8" "channels==4.1.0" "daphne==4.1.2" "requests==2.32.3" "pyserial==3.5" "python-dotenv==1.0.1"
fi
echo "✅ 패키지 설치 완료"

# ===== 5️⃣ DB 마이그레이션 =====
if [ ! -f manage.py ]; then
    echo "❌ manage.py 파일이 없습니다."
    exit 1
fi
echo "🧱 DB 마이그레이션 중..."
${PY_CMD} manage.py makemigrations
${PY_CMD} manage.py migrate
${PY_CMD} manage.py collectstatic --noinput

# ===== 6️⃣ Daphne 재시작 =====
echo "🚦 Daphne 프로세스 확인 및 재시작 중..."
PIDS=$(lsof -ti:8000)
if [ -n "$PIDS" ]; then
    echo "⚠️ 8000 포트 점유 중 프로세스 종료..."
    kill -9 $PIDS
fi

echo "🚀 새 Daphne 서버 실행 중..."
nohup ${PY_CMD} -m daphne -b 0.0.0.0 -p 8000 core.asgi:application > logs/daphne.log 2>&1 &

# ===== 7️⃣ Raspberry Pi + Arduino 통신 =====
PI_SCRIPT="embedded/raspberry_pi.py"
if pgrep -f "raspberry_pi.py" > /dev/null; then
    echo "⚙️ 기존 raspberry_pi.py 프로세스 종료 중..."
    pkill -f "raspberry_pi.py"
fi

if [ -f "$PI_SCRIPT" ]; then
    echo "🤖 raspberry_pi.py 실행 중..."
    nohup ${PY_CMD} "$PI_SCRIPT" --db-path "${DB_PATH}" --uno-port "${UNO_PORT}" --uno-baudrate "${UNO_BAUD}" > logs/pi.log 2>&1 &
else
    echo "⚠️ ${PI_SCRIPT} 파일을 찾을 수 없습니다."
fi

# ===== 8️⃣ ngrok 터널 =====
if ! command -v ngrok &> /dev/null; then
    echo "⚠️ ngrok이 설치되어 있지 않습니다. https://ngrok.com/download 참조."
else
    echo "🌐 ngrok 재시작 중..."
    pkill -f "ngrok http 8000" > /dev/null 2>&1
    nohup ngrok http 8000 --request-header-add='ngrok-skip-browser-warning:true' > logs/ngrok.log 2>&1 &
fi

echo "=============================================="
echo "✅ Jungo 서버 + Daphne + Raspberry Pi 실행 완료!"
echo " - 관리자 페이지: http://127.0.0.1:8000/admin"
echo " - ngrok 주소는 Forwarding URL 확인"
echo "=============================================="
