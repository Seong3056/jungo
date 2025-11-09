import os
import sys
import serial
import datetime
import time
from dotenv import load_dotenv

# ===== 경로 보정 =====
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# ===== Django 설정 =====
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django
try:
    django.setup()
    from orders.models import Order
except Exception as e:
    print(f"⚠️ Django 초기화 실패: {e}")
    time.sleep(2)

# ===== .env 로드 =====
load_dotenv(os.path.join(PROJECT_ROOT, ".env.linux"))

# ===== 로그 함수 =====
def write_log(message):
    now = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    log_path = os.path.join(PROJECT_ROOT, "access_log.txt")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"{now} {message}\n")

# ===== 메인 =====
def main():
    PORT = os.getenv("UNO_PORT", "COM4")   # 윈도우 기본 COM4
    BAUD = int(os.getenv("UNO_BAUD", 9600))
    TIMEOUT = 1

    # 🔁 포트 재시도 루프
    while True:
        try:
            ser = serial.Serial(PORT, BAUD, timeout=TIMEOUT)
            print(f"✅ Serial 연결됨: {PORT}")
            write_log(f"[INFO] Serial 연결됨: {PORT}")
            break
        except Exception as e:
            print(f"❌ Serial 연결 실패: {e}")
            write_log(f"[ERROR] Serial 연결 실패: {e}")
            print("⏳ 3초 후 재시도...")
            time.sleep(3)

    while True:
        try:
            if ser.in_waiting > 0:
                data = ser.readline().decode(errors="ignore").strip()
                if not data:
                    continue

                # 수신 로그 (왼쪽 정렬 + 결과 한 줄)
                print(f"🔹 수신: {data:<25}", end="")

                write_log(f"[RX] {data}")

                # ===== 요청 형식 검증 =====
                if not data.startswith("CHECK:"):
                    print("⚠️ 잘못된 요청 형식")
                    ser.write(b"ERROR\n")
                    write_log("[ERROR] 잘못된 요청 형식")
                    continue

                try:
                    _, listing_id, code = data.split(":")
                except ValueError:
                    print("⚠️ 파싱 오류")
                    ser.write(b"ERROR\n")
                    write_log("[ERROR] 파싱 실패")
                    continue

                # ===== DB 조회 =====
                try:
                    order = Order.objects.get(listing_id=listing_id)
                    db_code = str(order.confirmation_code).strip()

                    if db_code == code:
                        print("✅ 코드 일치")
                        ser.write(b"MATCH\n")
                        write_log(f"[OK] {listing_id} 코드 일치 ({code})")
                    else:
                        print("❌ 코드 불일치")
                        ser.write(b"NO_MATCH\n")
                        write_log(f"[FAIL] {listing_id} 코드 불일치 ({code})")

                except Order.DoesNotExist:
                    print(f"⚠️ DB에 해당 ID({listing_id}) 없음")
                    ser.write(b"NO_LISTING\n")
                    write_log(f"[WARN] {listing_id} 해당 주문 없음")

                except Exception as e:
                    print(f"⚠️ DB 조회 오류: {e}")
                    ser.write(b"ERROR\n")
                    write_log(f"[ERROR] DB 조회 실패: {e}")

        except serial.SerialException as e:
            print(f"\n⚠️ 시리얼 연결 끊김: {e}")
            write_log(f"[ERROR] SerialException: {e}")
            time.sleep(3)
            return main()  # 🔁 자동 재연결

        except KeyboardInterrupt:
            print("\n🛑 사용자에 의해 종료됨")
            write_log("[INFO] 수동 종료")
            ser.close()
            break

        except Exception as e:
            print(f"\n⚠️ 예외 발생: {e}")
            write_log(f"[ERROR] {e}")
            time.sleep(1)
            continue


if __name__ == "__main__":
    main()
