#!/bin/bash
# 🚀 Jungo All-in-One Server Starter (Safe Mode for Raspberry Pi / Linux)
# ===============================================

echo "=============================================="
echo " Jungo 서버 원클릭 실행 (안전 버전 for Linux)"
echo "=============================================="

# ===== 0️⃣ Python 설치 확인 =====
if ! command -v python3 &> /dev/null; then
    echo "⚠️  Python3이 설치되어 있지 않습니다."
    echo "👉 설치 명령: sudo apt install python3 python3-venv python3-pip -y"
    exit 1
fi
echo "✅ Python3 감지됨"

# ===== 1️⃣ 가상환경 생성 및 활성화 =====
if [ ! -d ".venv" ]; then
    echo "🌱 가상환경 생성 중..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "❌ 가상환경 생성 실패. Python이 손상되었을 수 있습니다."
        exit 1
    fi
fi

# 활성화
source .venv/bin/activate
if [ $? -ne 0 ]; then
    echo "❌ 가상환경 활성화 실패. .venv 폴더를 삭제 후 다시 시도하세요."
    exit 1
fi
echo "✅ 가상환경 활성화 완료"

# ===== 2️⃣ pip / 의존성 설치 =====
echo "📦 pip 최신 버전 확인 중..."
python -m pip install --upgrade pip > /dev/null

if [ -f "requirements.txt" ]; then
    echo "📦 requirements.txt 기반 의존성 설치 중..."
    pip install -r requirements.txt
else
    echo "⚠️ requirements.txt가 없습니다. 기본 패키지 설치 중..."
    pip install "django>=5.0.6,<6" "djangorestframework>=3.15,<4" "pillow>=10.0" "python-dotenv>=1.0" "channels>=4.0,<5" "channels-redis>=4.1,<5" "whitenoise>=6.6" "daphne>=4.1"
fi
echo "✅ 패키지 설치 완료"

# ===== 3️⃣ 데이터베이스 마이그레이션 =====
echo "🧱 DB 마이그레이션 실행..."
if [ ! -f "manage.py" ]; then
    echo "❌ manage.py 파일이 없습니다. 현재 폴더를 확인하세요."
    exit 1
fi

if [ -f "db.sqlite3" ]; then
    echo "✅ 기존 DB가 감지되었습니다. 삭제하지 않고 유지합니다."
else
    echo "⚙️ 새 DB를 생성합니다."
fi

python manage.py makemigrations
python manage.py migrate

# ===== 4️⃣ 정적 파일 수집 =====
echo "🎨 정적 파일 수집 (collectstatic)..."
python manage.py collectstatic --noinput

# ===== 5️⃣ Django 슈퍼유저 생성 =====
read -p "👤 관리자 계정을 생성할까요? (y/n): " CREATE_SUPERUSER
if [[ "$CREATE_SUPERUSER" =~ ^[Yy]$ ]]; then
    python manage.py createsuperuser
else
    echo "관리자 생성 생략"
fi

# ===== 6️⃣ Daphne 서버 실행 =====
echo "🚀 Daphne 서버 실행 중 (포트 8000)"
nohup python -m daphne -b 0.0.0.0 -p 8000 core.asgi:application > server.log 2>&1 &
SERVER_PID=$!
echo "✅ Daphne 서버 PID: $SERVER_PID (백그라운드 실행 중)"
echo "👉 로그 파일: server.log"

# ===== 7️⃣ ngrok 설치 및 터널링 =====
if ! command -v ngrok &> /dev/null; then
    echo "⚠️ ngrok이 설치되어 있지 않습니다. 설치 중..."
    curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
      | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \
      && echo "deb https://ngrok-agent.s3.amazonaws.com bookworm main" \
      | sudo tee /etc/apt/sources.list.d/ngrok.list \
      && sudo apt update \
      && sudo apt install ngrok -y
    if [ $? -ne 0 ]; then
        echo "❌ ngrok 설치 실패. 수동 설치 필요."
    else
        echo "✅ ngrok 설치 완료"
    fi
fi

if command -v ngrok &> /dev/null; then
    echo "🌐 ngrok 터널링 시작..."
    nohup ngrok http 8000 --request-header-add='ngrok-skip-browser-warning:true' > ngrok.log 2>&1 &
    echo "✅ ngrok이 백그라운드에서 실행 중 (로그: ngrok.log)"
else
    echo "⚠️ ngrok이 설치되지 않아 터널링을 생략합니다."
fi

echo "=============================================="
echo "✅ Jungo 서버가 실행되었습니다!"
echo "- Django 관리페이지: http://127.0.0.1:8000/admin"
echo "- 외부 접근(ngrok): ngrok 창의 Forwarding 주소 확인"
echo "- 로그 파일: server.log / ngrok.log"
echo "=============================================="
