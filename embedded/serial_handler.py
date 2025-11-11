import asyncio
import serial_asyncio
import time
import os
import platform
from orders.models import Order
from camera_module import capture_image
from ai_module import analyze_image
from logger import write_log


class SerialProtocol(asyncio.Protocol):
    def __init__(self):
        self.transport = None
        self.connected = False
        self.last_detection_time = 0
        self.buffer = ""  # ✅ 조각난 데이터를 임시 저장할 버퍼

    def connection_made(self, transport):
        """시리얼 연결이 성립되었을 때"""
        self.transport = transport
        self.connected = True
        port = getattr(transport.serial, "port", "Unknown")
        print(f"✅ 시리얼 연결됨 ({port})")
        write_log(f"[INFO] Serial 연결됨 ({port})")

    def data_received(self, data):
        """데이터가 수신될 때마다 호출"""
        try:
            text = data.decode(errors="ignore")
            self.buffer += text  # ✅ 버퍼에 누적

            # ✅ '\n' 기준으로 완전한 한 줄씩 처리
            while "\n" in self.buffer:
                line, self.buffer = self.buffer.split("\n", 1)
                message = line.strip()

                if not message:
                    continue

                print(f"📡 수신: {message}")
                write_log(f"[RX] {message}")
                asyncio.create_task(self.handle_data(message))

        except Exception as e:
            print(f"⚠️ 수신 처리 중 오류: {e}")
            write_log(f"[ERROR] 수신 처리 오류: {e}")

    async def handle_data(self, message):
        """메시지 내용 분석 및 분기 처리"""
        try:
            # ✅ 초음파 감지
            if message.startswith("ULTRA:"):
                parts = message.split(":")
                if len(parts) < 2:
                    write_log(f"[WARN] 잘못된 ULTRA 데이터: {message}")
                    return

                _, detected = parts
                if detected == "1":
                    now = time.time()
                    if now - self.last_detection_time > 3:
                        self.last_detection_time = now
                        write_log("[INFO] 초음파 감지됨 → AI 분석 실행")

                        image_path = await asyncio.to_thread(capture_image)
                        if image_path:
                            await asyncio.to_thread(analyze_image, image_path)

            # ✅ 주문 코드 확인
            elif message.startswith("CHECK:"):
                parts = message.split(":", maxsplit=2)
                if len(parts) < 3:
                    write_log(f"[WARN] 잘못된 CHECK 데이터: {message}")
                    return

                _, listing_id, code = parts
                await asyncio.to_thread(self.check_order, listing_id, code)

            else:
                write_log(f"[INFO] 알 수 없는 데이터 무시: {message}")

        except Exception as e:
            print(f"⚠️ handle_data 예외: {e}")
            write_log(f"[ERROR] handle_data 예외: {e}")

    def check_order(self, listing_id, code):
        """DB에서 주문 확인 코드 검증"""
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
        """시리얼 연결이 끊겼을 때"""
        print("⚠️ 시리얼 연결 종료됨, 재시도 중...")
        write_log("[WARN] Serial 연결 끊김")
        self.connected = False
        asyncio.create_task(reconnect_serial())


# ====== 재연결 루프 ======
async def reconnect_serial():
    await asyncio.sleep(3)
    await start_serial()


# ====== 시리얼 연결 시작 ======
async def start_serial():
    loop = asyncio.get_running_loop()

    # ✅ start.sh가 이미 .env.linux를 불러왔으므로 바로 환경 변수 사용
    port = os.getenv("UNO_PORT", "/dev/ttyACM0")
    baudrate = int(os.getenv("UNO_BAUD", "9600"))

    try:
        await serial_asyncio.create_serial_connection(
            loop, SerialProtocol, port, baudrate=baudrate
        )
    except Exception as e:
        print(f"❌ Serial 연결 실패: {e}")
        write_log(f"[ERROR] Serial 연결 실패: {e}")
        await asyncio.sleep(3)
        await start_serial()


if __name__ == "__main__":
    try:
        asyncio.run(start_serial())
    except KeyboardInterrupt:
        print("🛑 Serial 모듈 종료됨")
