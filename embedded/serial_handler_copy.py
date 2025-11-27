import asyncio
import serial_asyncio
import time
import os
from orders.models import Order
from embedded.camera_module import delete_image, init_camera, capture_image, is_empty_image
from ai_module import analyze_image
from logger import write_log
from listings.models import Listing

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
            match message.split(":", 1):
                # ULTRA 감지
                case ["ULTRA", rest]:
                    if rest != "1":
                        return

                    now = time.time()

                    # 3초 이내 또는 처리 중이면 무시
                    if now - self.last_detection_time <= 3 or self.processing:
                        write_log("[WARN] 감지 무시됨 (중복 감지 또는 처리 중)")
                        return

                    # 감지 시간 등록 + 처리 시작
                    self.last_detection_time = now
                    self.processing = True
                    write_log("[INFO] 물체 감지됨 → 촬영 및 분석 시작")

                    try:
                        # --------------------------------------
                        # 🚨 Listing 테이블에서 최신 레코드 가져오기
                        # --------------------------------------
                        from listings.models import Listing

                        listing = await asyncio.to_thread(
                            lambda: Listing.objects.order_by("-id").first()
                        )

                        # 이미 이미지 존재하면 스킵
                        if listing and listing.capture_image:
                            write_log("[INFO] Listing에 이미 사진 존재 → 촬영/분석 스킵")
                            print("⚠ Listing.capture_image 이미 존재 → 촬영하지 않음")
                            return

                        # 카메라 초기화
                        await asyncio.to_thread(init_camera)

                        # 촬영
                        image_path = await asyncio.to_thread(capture_image)
                        if not image_path:
                            write_log("[ERROR] 촬영 실패(image_path 없음)")
                            return

                        # 촬영된 이미지 저장
                        if listing:
                            def save_image():
                                listing.capture_image = image_path
                                listing.save()

                            await asyncio.to_thread(save_image)

                        # AI 분석
                        await asyncio.to_thread(analyze_image, image_path)

                        write_log("[INFO] 촬영 → 분석 완료")

                    except Exception as e:
                        write_log(f"[ERROR] 촬영/분석 과정 예외: {e}")

                    finally:
                        self.processing = False
                        return
                    
                case ["DETECT", rest]:
                    if rest != "1":
                        return
                    self.transport.write(b"CLOSE\n")
                    try:
                        
                        # 카메라 초기화
                        await asyncio.to_thread(init_camera)
                        from listings.models import Listing

                        listing = await asyncio.to_thread(
                            lambda: Listing.objects.order_by("-id").first()
                        )
                        # ------------------------------------------------------
                        # ① 촬영 먼저 실행
                        # ------------------------------------------------------
                        image_path = await asyncio.to_thread(capture_image)
                        if not image_path:
                            write_log("[ERROR] 촬영 실패(image_path 없음)")
                            return

                        # ------------------------------------------------------
                        # ② empty 이미지 비교 수행
                        # ------------------------------------------------------
                        if is_empty_image(image_path):
                            write_log("[INFO] 내부 물체 없음 → DETECT 분석 스킵")
                            print("🔍 DETECT: empty.jpg와 동일 → 분석하지 않음")
                            delete_image(image_path)
                            return

                        # ------------------------------------------------------
                        # ③ empty가 아니면 이미지 저장 후 AI 분석
                        # ------------------------------------------------------
                        if listing:
                            def save_image():
                                listing.capture_image = image_path
                                listing.save()

                            await asyncio.to_thread(save_image)

                        # AI 분석
                        await asyncio.to_thread(analyze_image, image_path)

                        write_log("[INFO] DETECT 촬영 → 분석 완료")

                    except Exception as e:
                        write_log(f"[ERROR] DETECT 촬영/분석 과정 예외: {e}")

                    finally:
                        self.processing = False
                        return
                    
                case ["OPEN", rest]:
                    write_log("[INFO] OPEN 명령 수신")
                    try:
                        # 카메라 초기화
                        await asyncio.to_thread(init_camera)
                        image_path = await asyncio.to_thread(capture_image)
                        if is_empty_image(image_path):                       
                            
                            write_log("[INFO] 내부 물체 없음 → OPEN")
                            print("🔍 OPEN: empty.jpg와 동일")
                            
                            
                            self.transport.write(b"OPEN\n")
                        else:
                            write_log("[INFO] 물체감지")
                            print("🔍 DEINED 문열기 불가")
                            
                            self.transport.write(b"DENIED\n")
                        #delete_image(image_path)    
                            
                        
                    except Exception as e:
                        write_log(f"[ERROR] OPEN 처리 예외: {e}")
                    


                # CHECK 처리
                case ["CHECK", rest]:
                    parts = message.split(":", maxsplit=2)
                    if len(parts) >= 3:
                        _, listing_id, code = parts
                        await asyncio.to_thread(self.check_order, listing_id, code)
                    else:
                        write_log(f"[WARN] 잘못된 CHECK 데이터: {message}")

                # 그 외
                case _:
                    write_log(f"[INFO] Serial message: {message}")

        except Exception as e:
            write_log(f"[ERROR] handle_data 예외: {e}")

        finally:
            if self.processing:
                self.processing = False



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
