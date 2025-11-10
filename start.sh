#!/bin/bash
# 🚀 Jungo All-in-One Server Controller (start / stop / restart) - Python 3.13.5 전용
# ===============================================================================

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

    for PID_LIST in "$DAPHNE_PIDS" "$PI_PIDS" "$NGROK_PIDS" "$RUNSERVER_PIDS"; do
        [ -n "$PID_LIST" ] && echo "$PID_LIST" | xargs kill -9 2>/dev/null
    done

    PORTS=$(sudo lsof -t -i:$PORT -i:4040 2>/dev/null)
    [ -n "$PORTS" ] && echo "$PORTS" | xargs sudo kill -9 2>/dev/null

    echo "✅ Jungo 관련 프로세스 모두 중지 완료"
}

start_services() {
    echo "=============================================="
    echo "🚀 Jungo 서버 통합 실행 시작 (Python 3.13.5)"
    echo "=============================================="

    # ===== 1️⃣ Python 3.13 확인 =====
    if command -v python3.13 &>/dev/null; then
        PYTHON_CMD="python3.13"
    else
        echo "❌ Python 3.13이 설치되어 있지 않습니다."
        echo "👉 설치 명령:"
        echo "   sudo apt update && sudo apt install python3.13 python3.13-venv python3.13-pip -y"
        exit 1
    fi

    echo "✅ Python 3.13 감지됨 ($($PYTHON_CMD --version))"

    # ===== 2️⃣ 가상환경 생성 및 활성화 =====
    if [ ! -d ".venv" ]; then
        echo "🌱 Python 3.13 기반 가상환경 생성 중..."
        $PYTHON_CMD -m venv .venv || { echo "❌ 가상환경 생성 실패."; exit 1; }
    fi
    source .venv/bin/activate
    echo "✅ 가상환경 활성화 완료"

    # pip 복구 및 최신화
    $PYTHON_CMD -m ensurepip --upgrade >/dev/null 2>&1
    $PYTHON_CMD -m pip install --upgrade pip setuptools wheel >/dev/null 2>&1

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
    echo "📦 의존성 설치 중..."
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        pip install \
            "Django==5.2.8" \
            "channels==4.1.0" \
            "daphne==4.1.3" \
            "requests==2.32.3" \
            "pyserial==3.5" \
            "python-dotenv==1.0.1"
    fi
    echo "✅ 패키지 설치 완료"

    # ===== 6️⃣ DB 마이그레이션 =====
    echo "🧱 데이터베이스 마이그레이션 실행..."
    $PYTHON_CMD manage.py makemigrations
    $PYTHON_CMD manage.py migrate
    $PYTHON_CMD manage.py collectstatic --noinput

    # ===== 7️⃣ Daphne 실행 =====
    EXIST_PID=$(lsof -t -i:$PORT)
    [ -n "$EXIST_PID" ] && kill -9 "$EXIST_PID"
    nohup $PYTHON_CMD -m daphne -b 0.0.0.0 -p $PORT core.asgi:application > server.log 2>&1 &
    echo "✅ Daphne 실행 완료 (로그: server.log)"

    # ===== 8️⃣ RaspberryPi + Arduino 통신 =====
    EXIST_PI=$(pgrep -f "raspberry_pi.py")
    [ -n "$EXIST_PI" ] && kill -9 "$EXIST_PI"
    if [ -f "$PI_SCRIPT" ]; then
        echo "🤖 raspberry_pi.py 실행 중..."
        nohup $PYTHON_CMD "$PI_SCRIPT" \
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
        [ -n "$EXIST_NGROK" ] && kill -9 "$EXIST_NGROK"
        nohup ngrok http $PORT --request-header-add='ngrok-skip-browser-warning:true' > ngrok.log 2>&1 &
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
    start) start_services ;;
    stop) stop_services ;;
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
