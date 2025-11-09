#!/bin/bash
# 🚀 Jungo All-in-One Server Controller (start / stop / restart)
# ===============================================================

# 💡 실행 경로 고정
cd "$(dirname "$0")"

ACTION=${1:-start}  # 인자가 없으면 기본값 start
PORT=8000
PI_SCRIPT="embedded/raspberry_pi.py"

# ===== 공통 함수 =====
stop_services() {
    echo "=============================================="
    echo "🛑 Jungo 서버 중지 중..."
    echo "=============================================="

    DAPHNE_PIDS=$(pgrep -f "python.*daphne")
    PI_PIDS=$(pgrep -f "raspberry_pi.py")
    NGROK_PIDS=$(pgrep -f "ngrok http $PORT")
    RUNSERVER_PIDS=$(pgrep -f "manage.py runserver")

    if [ -n "$DAPHNE_PIDS" ]; then
        echo "⚙️ Daphne 종료 중..."
        echo "$DAPHNE_PIDS" | xargs kill -9
    fi
    if [ -n "$PI_PIDS" ]; then
        echo "⚙️ RaspberryPi 프로세스 종료 중..."
        echo "$PI_PIDS" | xargs kill -9
    fi
    if [ -n "$NGROK_PIDS" ]; then
        echo "⚙️ ngrok 종료 중..."
        echo "$NGROK_PIDS" | xargs kill -9
    fi
    if [ -n "$RUNSERVER_PIDS" ]; then
        echo "⚙️ Django runserver 종료 중..."
        echo "$RUNSERVER_PIDS" | xargs kill -9
    fi

    PORTS=$(sudo lsof -t -i:$PORT -i:4040 2>/dev/null)
    if [ -n "$PORTS" ]; then
        echo "⚙️ 포트 점유 프로세스 종료 중..."
        echo "$PORTS" | xargs sudo kill -9
    fi

    echo "✅ Jungo 관련 프로세스 모두 중지 완료"
}

start_services() {
    echo "=============================================="
    echo "🚀 Jungo 서버 통합 실행 시작"
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

    # ===== 3️⃣ .env.linux 불러오기 =====
if [ -f ".env.linux" ]; then
    echo "📄 .env.linux 파일 감지됨 → 환경 변수 로드 중..."
    export $(grep -v '^#' .env.linux | xargs)
else
    echo "⚠️ .env.linux 파일이 없습니다. 기본값으로 실행합니다."
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

    # ===== 7️⃣ Daphne 실행 =====
    EXIST_PID=$(lsof -t -i:$PORT)
    if [ -n "$EXIST_PID" ]; then
        echo "⚠️ 포트 $PORT 점유 중 (PID: $EXIST_PID) → 종료"
        kill -9 "$EXIST_PID"
        sleep 0.5
    fi
    nohup python -m daphne -b 0.0.0.0 -p $PORT core.asgi:application > server.log 2>&1 &
    echo "✅ Daphne 실행 완료"

    # ===== 8️⃣ RaspberryPi + Arduino 통신 =====
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
        EXIST_NGROK=$(pgrep -f "ngrok http $PORT")
        if [ -n "$EXIST_NGROK" ]; then
            echo "⚙️ 기존 ngrok 종료 중 (PID: $EXIST_NGROK)"
            kill -9 "$EXIST_NGROK"
            sleep 1
        fi
        echo "🚀 ngrok 터널 시작 중..."
        nohup ngrok http $PORT --request-header-add='ngrok-skip-browser-warning:true' > ngrok.log 2>&1 &
        sleep 2
        echo "✅ ngrok 실행됨 (로그: ngrok.log)"
    else
        echo "⚠️ ngrok이 설치되어 있지 않습니다. 설치 명령: sudo apt install ngrok -y"
    fi

    echo "=============================================="
    echo "✅ Jungo 서버 + RaspberryPi 자동실행 완료!"
    echo "- 관리자 페이지: http://127.0.0.1:$PORT/admin"
    echo "- ngrok 주소: ngrok.log 확인"
    echo "- 로그: server.log / pi.log / ngrok.log"
    echo "=============================================="
}

# ===== 실행 분기 =====
case "$ACTION" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        stop_services
        sleep 1
        start_services
        ;;
    *)
        echo "⚠️ 사용법: ./start.sh {start|stop|restart}"
        exit 1
        ;;
esac
