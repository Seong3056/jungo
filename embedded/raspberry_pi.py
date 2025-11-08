import os
import serial
import django
import datetime
from dotenv import load_dotenv

# ===== .env 불러오기 =====
load_dotenv(".env.linux")

PORT = os.getenv("UNO_PORT")  # 예: /dev/ttyACM0
BAUD = int(os.getenv("UNO_BAUD", 9600))  # 기본값 9600

# ===== Django 환경 초기화 =====
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from orders.models import Order


# ===== 로그 함수 =====
def write_log(message):
    """access_log.txt에 시간별 로그 남기기"""
    now = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open("access_log.txt", "a", encoding="utf-8") as f:
        f.write(f"{now} {message}\n")


# ===== 메인 로직 =====
def main():
    try:
        ser = serial.Serial(PORT, BAUD, timeout=1)
        print(f"✅ Serial 연결됨: {PORT} ({BAUD}bps)")
        write_log(f"[INFO] 시리얼 연결 성공 ({PORT})")
    except Exception as e:
        print(f"❌ 시리얼 연결 실패: {e}")
        write_log(f"[ERROR] 시리얼 연결 실패 - {e}")
        return

    while True:
        if ser.in_waiting > 0:
            code = ser.readline().decode().strip()
            if not code:
                continue

            print(f"🔹 입력된 코드: {code}")
            write_log(f"[입력] 코드 수신: {code}")

            # ===== DB에서 최신 주문 코드 가져오기 =====
            try:
                latest_order = Order.objects.last()
                if not latest_order:
                    print("⚠️ DB에 주문 데이터 없음")
                    write_log(f"[WARN] DB 주문 없음 (입력: {code})")
                    continue

                db_code = str(latest_order.confirmation_code)
            except Exception as e:
                print(f"⚠️ DB 접근 실패: {e}")
                write_log(f"[ERROR] DB 접근 실패 - {e}")
                continue

            # ===== 코드 비교 =====
            if code == db_code:
                print("✅ 코드 일치 — 문 열림")
                ser.write(b"MATCH\n")
                write_log(f"[OK] 코드 일치 (입력: {code}, DB: {db_code})")
            else:
                print("❌ 코드 불일치 — 접근 거부")
                ser.write(b"MISMATCH\n")
                write_log(f"[FAIL] 코드 불일치 (입력: {code}, DB: {db_code})")


if __name__ == "__main__":
    main()
