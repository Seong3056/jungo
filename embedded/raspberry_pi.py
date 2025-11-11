# embedded/raspberry_pi.py
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
from embedded.camera_module import check_camera   # ✅ 경로 변경됨
from serial_handler import start_serial
from logger import write_log


async def main():
    write_log("[INFO] === Raspberry Pi module started ===")
    print("🔍 Checking camera availability...")

    camera_ready = check_camera()

    if camera_ready:
        print("✅ Camera is ready.")
        write_log("[INFO] Camera ready: True")
    else:
        print("❌ Camera not detected.")
        write_log("[ERROR] Camera ready: False")
        # 실패 시 중단하려면 ↓
        # import sys; sys.exit(1)

    await start_serial()

    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 프로그램 종료됨")
        write_log("[INFO] 프로그램 종료됨")
