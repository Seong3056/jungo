import os
import sys
import serial
import datetime
import time
import base64
import yaml
import cv2
import platform
from openai import OpenAI
from dotenv import load_dotenv

# ===== 경로 설정 =====
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

# ===== config.yml 로드 =====
def load_config():
    config_path = os.path.join(PROJECT_ROOT, "config.yml")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"⚠️ config.yml 로드 실패: {e}")
        time.sleep(2)
        return {}

config = load_config()

# ===== OpenAI 클라이언트 =====
openai_key = config.get("openai", {}).get("api_key")
openai_model = config.get("openai", {}).get("model", "gpt-4o-mini")

if not openai_key:
    print("❌ config.yml에 openai.api_key가 없습니다!")
    sys.exit(1)

client = OpenAI(api_key=openai_key)

# ===== 카메라 설정 =====
camera_output_path = os.path.join(PROJECT_ROOT, config.get("camera", {}).get("output_path", "latest_photo.jpg"))

# ===== 로그 함수 =====
def write_log(message):
    now = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    log_path = os.path.join(PROJECT_ROOT, "pi.log")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"{now} {message}\n")

# ===== 사진 촬영 =====
import platform
import os
import time
import cv2

def capture_image():
    system_name = platform.system().lower()
    output_path = os.path.join(PROJECT_ROOT, config.get("camera", {}).get("output_path", "latest_photo.jpg"))

    # ✅ Windows 환경: YML에 지정된 이미지 파일 사용
    # if "windows" in system_name:
    #     if os.path.exists(output_path):
    #         print(f"🖼️ Windows 환경 - YML 지정 이미지 사용: {output_path}")
    #         write_log(f"[INFO] Windows 환경 - {output_path} 사용")
    #         return output_path
    #     else:
    #         print(f"⚠️ Windows 환경이지만 지정 이미지({output_path})가 존재하지 않습니다.")
    #         write_log(f"[WARN] Windows 환경 - {output_path} 없음")
    #         return None

    # ✅ 라즈베리파이 등 실제 카메라 사용
    try:
        cam = cv2.VideoCapture(0)
        if not cam.isOpened():
            raise Exception("카메라를 열 수 없습니다.")
        time.sleep(0.5)
        ret, frame = cam.read()
        if not ret:
            raise Exception("사진 캡처 실패")
        cv2.imwrite(output_path, frame)
        cam.release()
        print(f"📸 사진 저장 완료: {output_path}")
        write_log(f"[INFO] 사진 촬영 완료: {output_path}")
        return output_path
    except Exception as e:
        print(f"⚠️ 사진 촬영 실패: {e}")
        write_log(f"[ERROR] 사진 촬영 실패: {e}")
        return None


# ===== AI 분석 =====
def analyze_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            image_base64 = base64.b64encode(img_file.read()).decode("utf-8")

        response = client.chat.completions.create(
            model=openai_model,
            messages=[
                {"role": "system", "content": "너는 물체 인식 전문가야."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "이 사진 속 물건의 브랜드, 제품명을 딕셔너리 형태로 줘."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            },
                        },
                    ],
                },
            ],
        )

        result = response.choices[0].message.content
        print(f"🧠 AI 분석 결과: {result}")
        write_log(f"[AI] 분석 결과: {result}")
        return result
    except Exception as e:
        print(f"⚠️ 이미지 분석 실패: {e}")
        write_log(f"[ERROR] 이미지 분석 실패: {e}")
        return None

# ===== 시리얼 연결 시도 =====
def connect_serial(port, baud, timeout):
    while True:
        try:
            ser = serial.Serial(port, baud, timeout=timeout)
            print(f"✅ Serial 연결됨: {port}")
            write_log(f"[INFO] Serial 연결됨: {port}")
            return ser
        except Exception as e:
            print(f"❌ Serial 연결 실패: {e}")
            write_log(f"[ERROR] Serial 연결 실패: {e}")
            print("⏳ 3초 후 재시도...")
            time.sleep(3)

# ===== 메인 루프 =====
def main():
    PORT = os.getenv("UNO_PORT", "COM4")
    BAUD = int(os.getenv("UNO_BAUD", 9600))
    TIMEOUT = 1

    last_detection_time = 0

    while True:
        ser = connect_serial(PORT, BAUD, TIMEOUT)

        try:
            while True:
                try:
                    if ser.in_waiting > 0:
                        data = ser.readline().decode(errors="ignore").strip()
                        if not data:
                            continue

                        print(f"🔹 수신: {data}")
                        write_log(f"[RX] {data}")

                        # 🔸 무시할 메시지
                        if not (data.startswith("CHECK:") or data.startswith("ULTRA:")):
                            if any(keyword in data for keyword in ["ERROR", "Received", "Unknown", "INIT"]):
                                print(f"ℹ️ 아두이노 상태 메시지 무시: {data}")
                                write_log(f"[INFO] 무시된 메시지: {data}")
                                continue
                            print(f"⚠️ 인식 불가 명령어 수신: {data}")
                            write_log(f"[WARN] 인식 불가 명령어 수신: {data}")
                            continue

                        # 🔍 초음파 감지 처리
                        if data.startswith("ULTRA:"):
                            try:
                                _, detected = data.split(":")
                                if detected == "1":
                                    now = time.time()
                                    if now - last_detection_time < 3:
                                        continue
                                    last_detection_time = now

                                    print("📡 초음파 감지됨 → 사진 촬영 및 AI 분석")
                                    write_log("[INFO] 초음파 감지됨 → AI 분석 실행")

                                    image_path = capture_image()
                                    if image_path:
                                        analyze_image(image_path)
                                else:
                                    print("🔕 초음파 미감지")
                                    write_log("[INFO] 초음파 미감지")
                            except Exception as e:
                                print(f"⚠️ 초음파 데이터 처리 오류: {e}")
                                write_log(f"[ERROR] 초음파 데이터 처리 오류: {e}")
                            continue

                        # 🧾 CHECK 명령 처리
                        if data.startswith("CHECK:"):
                            try:
                                _, listing_id, code = data.split(":")
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

                    else:
                        time.sleep(0.05)  # ✅ CPU 낭비 방지

                except serial.SerialException as e:
                    print(f"⚠️ 시리얼 연결 끊김: {e}")
                    write_log(f"[ERROR] SerialException: {e}")
                    ser.close()
                    time.sleep(3)
                    break  # 🔁 상위 while로 복귀해 재연결

                except KeyboardInterrupt:
                    print("\n🛑 사용자에 의해 종료됨")
                    write_log("[INFO] 수동 종료")
                    ser.close()
                    return

                except Exception as e:
                    print(f"⚠️ 예외 발생: {e}")
                    write_log(f"[ERROR] {e}")
                    time.sleep(1)
                    continue

        except Exception as e:
            print(f"💥 치명적 오류 발생: {e}")
            write_log(f"[FATAL] {e}")
            time.sleep(3)


if __name__ == "__main__":
    main()
