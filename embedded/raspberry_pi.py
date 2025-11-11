import os
import sys
import django

# Django 루트 경로 등록
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# Django 초기화
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()
import asyncio
from serial_handler import start_serial
from logger import write_log

async def main():
    await start_serial()
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 프로그램 종료됨")
        write_log("[INFO] 프로그램 종료됨")
