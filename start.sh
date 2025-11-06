#!/bin/bash
# 🚀 Jungo All-in-One Server Starter (Auto Restart + Safe Mode)
# ============================================================

# 0️⃣ 실행 권한 자동 부여
if [ ! -x "$0" ]; then
    echo "🔧 실행 권한이 없어 자동으로 부여 중..."
    chmod +x "$0"
    echo "✅ 권한 부여 완료"
fi

echo "=============================================="
echo " Jungo 서버 원클릭 실행 (자동 재시작 버전)"
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
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "❌ 가상환경 생성 실패. Python 환경을 확인하세요."
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

# ===== 4️⃣ DB 자동 생성 =====
if [ ! -f "manage.py" ]; then
    echo "❌ manage.py 파일이 없습니다. 현재 폴더를 확인하세요."
    exit 1
fi

echo "🧱 데이터베이스 초기화 확인 중..."
if [ -f "db.sqlite3" ]; then
    echo "✅ 기존 DB 감지됨 — 유지합니다."
else
    echo "⚙️ DB가 없습니다. 자동으로 새로 생성합니다..."
    python manage.py makemigrations
    python manage.py migrate
fi

# ===== 5️⃣ 정적 파일 수집 =====
echo "🎨 정적 파일 수집 (collectstatic)..."
python manage.py collectstatic --noinput

# ===== 6️⃣ Daphne 서버 자동 재시작 =====
echo "🚦 Daphne 서버 상태 확인 중..."
EXIST_PID=$(pgrep -f "daphne -b 0.0.0.0 -p 8000")

if [ -n "$EXIST_PID" ]; then
    echo "⚠️ 기존 Daphne 서버가 실행 중 (PID: $EXIST_PID)"
    echo "🧹 기존 서버 종료 중..."
    kill -9 "$EXIST_PID"
    sleep 1
    echo "✅ 이전 Daphne 서버 종료 완료"
fi

echo "🚀 새 Daphne 서버 실행 중 (포트 8000)"
nohup python -m daphne -b 0.0.0.0 -p 8000 core.asgi:application > server.log 2>&1 &
SERVER_PID=$!
sleep 2
echo "✅ 새 Daphne 서버 PID: $SERVER_PID (백그라운드 실행)"
echo "👉 로그 파일: server.log"

# ===== 7️⃣ ngrok 자동 재시작 =====
if command -v ngrok &> /dev/null; then
    EXIST_NGROK=$(pgrep -f "ngrok http 8000")
    if [ -n "$EXIST_NGROK" ]; then
        echo "⚠️ 기존 ngrok 터널 종료 중..."
        kill -9 "$EXIST_NGROK"
        sleep 1
        echo "✅ 이전 ngrok 종료 완료"
    fi

    if [ -f ".ngrok_token" ]; then
        NGROK_TOKEN=$(cat .ngrok_token)
        ngrok config add-authtoken "$NGROK_TOKEN"
        echo "🔑 ngrok 인증 토큰 등록 완료"
    fi

    echo "🌐 새 ngrok 터널링 시작..."
    nohup ngrok http 8000 --request-header-add='ngrok-skip-browser-warning:true' > ngrok.log 2>&1 &
    echo "✅ ngrok 실행됨 (로그: ngrok.log)"
else
    echo "⚠️ ngrok이 설치되어 있지 않습니다. 설치 명령:"
    echo "👉 sudo apt install ngrok -y"
fi

echo "=============================================="
echo "✅ Jungo 서버 재시작 완료!"
echo "- 관리자 페이지: http://127.0.0.1:8000/admin"
echo "- 외부 접근(ngrok): ngrok Forwarding 주소 확인"
echo "- 로그: server.log / ngrok.log"
echo "=============================================="
