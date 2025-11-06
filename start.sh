#!/bin/bash
# 🚀 Jungo All-in-One Server Starter (Final Safe Mode)
# ===============================================

# 0️⃣ 실행 권한 자동 부여
if [ ! -x "$0" ]; then
    echo "🔧 실행 권한이 없어 자동으로 부여 중..."
    chmod +x "$0"
    echo "✅ 권한 부여 완료"
fi

echo "=============================================="
echo " Jungo 서버 원클릭 실행 (최종 안정 버전)"
echo "=============================================="

# ===== 1️⃣ Python 설치 확인 =====
if ! command -v python3 &> /dev/null; then
    echo "⚠️  Python3이 설치되어 있지 않습니다."
    echo "👉 설치 명령: sudo apt install python3 python3-venv python3-pip -y"
    exit 1
fi
echo "✅ Python3 감지됨"

# ===== 2️⃣ 가상환경 생성 및 활성화 =====
if [ ! -d ".venv" ]; then
    echo "🌱 가상환경 생성 중..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "❌ 가상환경 생성 실패. Python이 손상되었을 수 있습니다."
        exit 1
    fi
fi

source .venv/bin/activate
if [ $? -ne 0 ]; then
    echo "❌ 가상환경 활성화 실패. .venv 폴더를 삭제 후 다시 시도하세요."
    exit 1
fi
echo "✅ 가상환경 활성화 완료"

# ===== 3️⃣ pip / 의존성 설치 =====
echo "📦 pip 최신화 중..."
python -m pip install --upgrade pip >/dev/null

if [ -f "requirements.txt" ]; then
    echo "📦 requirements.txt 기반 의존성 설치 중..."
    pip install -r requirements.txt
else
    echo "⚠️ requirements.txt가 없습니다. 기본 패키지 설치 중..."
    pip install "Django==5.2.8" "djangorestframework==3.15.2" "channels==4.1.0" "daphne==4.1.2" \
                "twisted==24.3.0" "asgiref==3.8.1" "requests==2.32.3" "pyserial==3.5" \
                "opencv-python==4.10.0.84" "Pillow==10.4.0" "tzdata==2025.1" "whitenoise==6.7.0" "python-dotenv==1.0.1"
fi
echo "✅ 패키지 설치 완료"

# ===== 4️⃣ DB 마이그레이션 =====
if [ ! -f "manage.py" ]; then
    echo "❌ manage.py 파일이 없습니다. 현재 폴더를 확인하세요."
    exit 1
fi

echo "🧱 DB 마이그레이션 실행..."
if [ -f "db.sqlite3" ]; then
    echo "✅ 기존 DB 유지 (db.sqlite3)"
else
    echo "⚙️ 새 DB 생성..."
fi
python manage.py makemigrations
python manage.py migrate

# ===== 5️⃣ 정적 파일 수집 =====
echo "🎨 정적 파일 수집 (collectstatic)..."
python manage.py collectstatic --noinput

# ===== 7️⃣ 로그 관리 (1MB 이상시 초기화) =====
for LOG_FILE in server.log ngrok.log; do
    if [ -f "$LOG_FILE" ]; then
        FILE_SIZE=$(stat -c%s "$LOG_FILE")
        if [ $FILE_SIZE -gt 1048576 ]; then
            echo "🧹 $LOG_FILE 용량이 1MB를 초과하여 초기화합니다."
            echo "" > "$LOG_FILE"
        fi
    fi
done

# ===== 8️⃣ Daphne 서버 중복 실행 방지 및 실행 =====
if pgrep -f "daphne -b 0.0.0.0 -p 8000" > /dev/null; then
    echo "⚠️ 이미 Daphne 서버가 실행 중입니다. (중복 실행 방지)"
else
    echo "🚀 Daphne 서버 실행 중 (포트 8000)"
    nohup python -m daphne -b 0.0.0.0 -p 8000 core.asgi:application > server.log 2>&1 &
    SERVER_PID=$!
    echo "✅ Daphne 서버 PID: $SERVER_PID (백그라운드 실행)"
fi

# ===== 9️⃣ ngrok 설치 및 자동 토큰 등록 =====
if ! command -v ngrok &> /dev/null; then
    echo "⚠️ ngrok이 설치되어 있지 않습니다. 자동 설치 시도..."
    curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
        | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \
        && echo "deb https://ngrok-agent.s3.amazonaws.com bookworm main" \
        | sudo tee /etc/apt/sources.list.d/ngrok.list >/dev/null \
        && sudo apt update \
        && sudo apt install ngrok -y
    if [ $? -ne 0 ]; then
        echo "❌ ngrok 설치 실패. 수동 설치 필요."
    else
        echo "✅ ngrok 설치 완료"
    fi
fi

# ngrok 토큰 자동 등록
if [ -f ".ngrok_token" ]; then
    NGROK_TOKEN=$(cat .ngrok_token)
    ngrok config add-authtoken "$NGROK_TOKEN"
    echo "🔑 ngrok 인증 토큰 등록 완료"
else
    echo "⚠️ .ngrok_token 파일이 없습니다. ngrok auth 토큰을 등록하려면 이 파일에 저장하세요."
fi

# ===== 🔟 ngrok 중복 실행 방지 및 실행 =====
if pgrep -f "ngrok http 8000" > /dev/null; then
    echo "⚠️ ngrok이 이미 실행 중입니다. (중복 실행 방지)"
else
    echo "🌐 ngrok 터널링 시작..."
    nohup ngrok http 8000 --request-header-add='ngrok-skip-browser-warning:true' > ngrok.log 2>&1 &
    echo "✅ ngrok이 백그라운드에서 실행 중 (로그: ngrok.log)"
fi

echo "=============================================="
echo "✅ Jungo 서버가 완전히 실행되었습니다!"
echo "- 관리자 페이지: http://127.0.0.1:8000/admin"
echo "- 외부 접근(ngrok): ngrok Forwarding 주소 확인"
echo "- 로그: server.log / ngrok.log"
echo "=============================================="
