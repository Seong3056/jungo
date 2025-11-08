import os
import sys
import serial
import datetime
from dotenv import load_dotenv

# ===== 경로 보정 =====
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# ===== Django 설정 (미래 DB 사용 대비) =====
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# ===== .env 로드 =====
load_dotenv(os.path.join(PROJECT_ROOT, ".env.linux"))

# ===== logging 함수 =====
def write_log(message):
    now = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open(os.path.join(PROJECT_ROOT, "access_log.txt"), "a", encoding="utf-8") as f:
        f.write(f"{now} {message}\n")

# ===== 메인 =====
def main():
    PORT = os.getenv("UNO_PORT", "/dev/ttyACM0")
    BAUD = int(os.getenv("UNO_BAUD", 9600))
    SECRET_CODE = "1234"

    try:
        ser = serial.Serial(PORT, BAUD, timeout=1)
        print(f"✅ Serial 연결됨: {PORT}")
        write_log(f"[INFO] Serial 연결됨: {PORT}")
    except Exception as e:
        print(f"❌ Serial 연결 실패: {e}")
        write_log(f"[ERROR] Serial 연결 실패: {e}")
        return

    while True:
        if ser.in_waiting > 0:
            code = ser.readline().decode().strip()
            if not code:
                continue

            print(f"🔹 입력 코드: {code}")
            write_log(f"[입력] 코드 수신: {code}")

            if code == SECRET_CODE:
                print("✅ 일치 - 문 열기 신호 전송")
                ser.write(b"MATCH\n")
                write_log("[OK] 코드 일치")
            else:
                print("❌ 불일치 - 거부")
                ser.write(b"MISMATCH\n")
                write_log(f"[FAIL] 불일치 입력: {code}")


if __name__ == "__main__":
    main()