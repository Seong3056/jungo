import os
import time
import cv2
from datetime import datetime
from config_loader import PROJECT_ROOT
from logger import write_log

camera = None
camera_busy = False


def init_camera():
    global camera

    if camera is not None:
        return camera

    try:
        from picamera2 import Picamera2, Preview
        from libcamera import Transform

        picam2 = Picamera2()

        # ⭐ 안정적이면서 preview와 가장 동일하게 보이는 설정
        config = picam2.create_still_configuration(
            main={
                "size": (1920, 1080),
                "format": "XRGB8888"   # ★ preview-compatible format
            },
            transform=Transform(rotation=180),
            buffer_count=4             # preview 안정성 증가
        )

        picam2.configure(config)

        # Preview 시작
        # picam2.start_preview(Preview.QTGL)
        picam2.start()

        # 자동 노출, 자동 화이트밸런스
        picam2.set_controls({
            "AeEnable": True,
            "AwbEnable": True,
            "Sharpness": 1.0,
            "Contrast": 1.0,
            "Saturation": 1.0,
        })

        camera = picam2
        print("📸 Camera initialized (safe preview-sync mode).")
        write_log("[INFO] Camera initialized successfully (safe preview-sync mode).")

        return camera

    except Exception as e:
        write_log(f"[ERROR] Picamera2 initialization failed: {e}")
        print(f"❌ Picamera2 초기화 실패: {e}")
        camera = None
        return None



def capture_image(filename=None):
    global camera, camera_busy

    if camera_busy:
        return None
    camera_busy = True

    try:
        if camera is None:
            camera = init_camera()

        # 저장 경로
        media_dir = os.path.join(PROJECT_ROOT, "media")
        os.makedirs(media_dir, exist_ok=True)

        if filename is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"photo_{timestamp}.jpg"

        output_path = os.path.join(media_dir, filename)

        # ⭐ preview와 완전 동일한 pipeline에서 캡처함
        frame = camera.capture_array()

        cv2.imwrite(output_path, frame)
        print(f"📁 사진 저장됨: {output_path}")

        return output_path

    except Exception as e:
        write_log(f"[ERROR] Image capture failed: {e}")
        print(f"⚠️ 촬영 실패: {e}")
        return None

    finally:
        camera_busy = False



def release_camera():
    global camera
    try:
        if camera:
            camera.stop()
            camera = None
            print("📷 Camera released.")
    except:
        pass
