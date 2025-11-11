import asyncio
import serial_asyncio
import time
import os
from orders.models import Order
from embedded.camera_module import init_camera, capture_image
from ai_module import analyze_image
from logger import write_log


class SerialProtocol(asyncio.Protocol):
    def __init__(self):
        self.transport = None
        self.connected = False
        self.last_detection_time = 0
        self.buffer = ""
        self.processing = False   # ✅ AI 분석 중인지 표시

    def connection_made(self, transport):
        """시리얼 연결 성립 시"""
        self.transport = transport
        self.connected = True
        port = getattr(transport.serial, "port", "Unknown")
        print(f"✅ 시리얼 연결됨 ({port})")
        write_log(f"[INFO] Serial 연결됨 ({port})")

        # ✅ 카메라 1회 초기화
        asyncio.create_task(asyncio.to_thread(init_camera))

    def data_received(self, data):
        """데이터 수신 시"""
        try:
            text = data.decode(errors="ignore")
            self.buffer += text
            while "\n" in self.buffer:
                line, self.buffer = self.buffer.split("\n", 1)
                message = line.strip()
                if not message:
                    continue
                print(f"📡 수신: {message}")
                write_log(f"[RX] {message}")
                asyncio.create_task(self.handle_data(message))
        except Exception as e:
            write_log(f"[ERROR] 수신 처리 오류: {e}")
            print(f"⚠️ 수신 처리 오류: {e}")

    async def handle_data(self, message):
        """메시지 분석 및 분기 처리"""
        try:
            # ✅ 초음파 감지
            if message.startswith("ULTRA:"):
                _, detected = message.split(":", 1)
                if detected == "1":
                    now = time.time()
                    # 3초 간격 + 처리 중에는 무시
                    if now - self.last_detection_time > 3 and not self.processing:
                        self.last_detection_time = now
                        self.processing = True  # 🔒 전체 프로세스 잠금
                        write_log("[INFO] 초음파 감지됨 → 촬영 및 AI 분석 시작")

                        # ✅ 카메라 보장
                        await asyncio.to_thread(init_camera)

                        # ✅ 사진 촬영
                        image_path = await asyncio.to_thread(capture_image)
                        if image_path:
                            # ✅ AI 분석
                            await asyncio.to_thread(analyze_image, image_path)

                        # ✅ 프로세스 완료 → 다시 감지 가능
                        self.processing = False
                        write_log("[INFO] 촬영 및 분석 완료 → 초음파 감지 재활성화")

                    else:
                        write_log("[WARN] 감지 무시 (분석 중 또는 너무 짧은 간격)")

            # ✅ 주문 코드 검증
            elif message.startswith("CHECK:"):
                parts = message.split(":", maxsplit=2)
                if len(parts) >= 3:
                    _, listing_id, code = parts
                    await asyncio.to_thread(self.check_order, listing_id, code)
                else:
                    write_log(f"[WARN] 잘못된 CHECK 데이터: {message}")

            else:
                write_log(f"[INFO] 알 수 없는 데이터 무시: {message}")

        except Exception as e:
            write_log(f"[ERROR] handle_data 예외: {e}")
            print(f"⚠️ handle_data 예외: {e}")
            self.processing = False  # 🚨 예외 시에도 잠금 해제

    def check_order(self, listing_id, code):
        """DB 주문 코드 검증"""
        try:
            order = Order.objects.get(listing_id=listing_id)
            if str(order.confirmation_code).strip() == code:
                self.transport.write(b"MATCH\n")
                write_log(f"[OK] {listing_id} 코드 일치")
            else:
                self.transport.write(b"NO_MATCH\n")
                write_log(f"[FAIL] {listing_id} 코드 불일치")
        except Order.DoesNotExist:
            self.transport.write(b"NO_LISTING\n")
            write_log(f"[WARN] {listing_id} 주문 없음")
        except Exception as e:
            self.transport.write(b"ERROR\n")
            write_log(f"[ERROR] DB 조회 실패: {e}")

    def connection_lost(self, exc):
        print("⚠️ 시리얼 연결 종료됨, 재시도 중...")
        write_log("[WARN] Serial 연결 끊김")
        self.connected = False
        asyncio.create_task(reconnect_serial())


async def reconnect_serial():
    await asyncio.sleep(3)
    await start_serial()


async def start_serial():
    loop = asyncio.get_running_loop()
    port = os.getenv("UNO_PORT", "/dev/ttyACM0")
    baudrate = int(os.getenv("UNO_BAUD", "9600"))

    try:
        await serial_asyncio.create_serial_connection(loop, SerialProtocol, port, baudrate=baudrate)
    except Exception as e:
        print(f"❌ Serial 연결 실패: {e}")
        write_log(f"[ERROR] Serial 연결 실패: {e}")
        await asyncio.sleep(3)
        await start_serial()
