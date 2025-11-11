import os
import sys
import django
import asyncio

# ===== Django 루트 경로 등록 =====
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# ===== Django 초기화 =====
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

# ===== 내부 모듈 =====
from embedded.camera_module import init_camera, release_camera
from serial_handler import start_serial
from logger import write_log


async def main():
    write_log("[INFO] === Raspberry Pi module started ===")
    print("🔍 Initializing camera...")

    # ✅ 카메라 한 번만 초기화
    camera_ready = await asyncio.to_thread(init_camera)

    if camera_ready is not None:
        print("✅ Camera initialized and ready.")
        write_log("[INFO] Camera initialized successfully.")
    else:
        print("❌ Camera initialization failed.")
        write_log("[ERROR] Camera initialization failed.")

    # ✅ 시리얼 시작
    await start_serial()

    # 루프 유지
    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 프로그램 종료됨")
        write_log("[INFO] 프로그램 종료됨")
        release_camera()  # ✅ 종료 시 카메라 해제
