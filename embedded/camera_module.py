import os
import time
import cv2
from datetime import datetime
from config_loader import PROJECT_ROOT
from logger import write_log

camera = None
camera_busy = False


def init_camera():
    """프리뷰 화면과 촬영 결과의 색감/밝기를 일치시키는 Picamera2 설정"""
    global camera

    if camera is not None:
        return camera

    try:
        from picamera2 import Picamera2, Preview
        from libcamera import Transform

        picam2 = Picamera2()

        # ---------------------------
        # 핵심: preview와 동일한 ISP 톤을 still 모드에도 강제로 적용
        # ---------------------------
        config = picam2.create_still_configuration(
            main={
                "size": (1920, 1080),      # preview랑 같은 해상도
                "format": "RGB888"         # preview와 동일한 컬러 포맷
            },
            transform=Transform(rotation=-90)
        )

        # preview pipeline의 색감을 최대한 동일화시키기 위한 ISP 조정
        config["controls"] = {
            "AwbEnable": True,
            "AeEnable": True,
            "NoiseReductionMode": 2,   # preview용 NR
            "Sharpness": 1.0,
            "Contrast": 1.0,
            "Saturation": 1.0,
            "TonemapEnable": True,     # preview 스타일 톤매핑 적용
        }

        picam2.configure(config)

        # ---------------------------
        # 프리뷰도 동일한 설정 기반으로 시작
        # ---------------------------
        picam2.start_preview(Preview.QTGL)
        picam2.start()

        # 자동 화이트밸런스 / 노출
        picam2.set_controls({
            "AwbEnable": True,
            "AeEnable": True,
        })

        camera = picam2

        print("📸 Camera initialized (preview == still mode identical).")
        write_log("[INFO] Camera initialized with preview-sync still mode.")

        return camera

    except Exception as e:
        print(f"❌ Picamera2 초기화 실패: {e}")
        write_log(f"[ERROR] Picamera2 initialization failed: {e}")
        camera = None
        return None



def capture_image(filename=None):
    """프리뷰와 동일한 색감/밝기/톤으로 사진 저장"""
    global camera, camera_busy

    if camera_busy:
        return None
    camera_busy = True

    try:
        if camera is None:
            camera = init_camera()

        media_dir = os.path.join(PROJECT_ROOT, "media")
        os.makedirs(media_dir, exist_ok=True)

        if filename is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"photo_{timestamp}.jpg"

        output_path = os.path.join(media_dir, filename)

        # 프리뷰와 동일한 ISP 파이프라인을 그대로 사용
        frame = camera.capture_array()

        cv2.imwrite(output_path, frame)
        print(f"📁 사진 저장됨(프리뷰 동일 색감): {output_path}")
        write_log(f"[INFO] 사진 저장됨: {output_path}")

        return output_path

    except Exception as e:
        print(f"⚠️ 촬영 실패: {e}")
        write_log(f"[ERROR] Image capture failed: {e}")
        return None

    finally:
        camera_busy = False



def release_camera():
    """Picamera2 안전 종료"""
    global camera
    try:
        if camera:
            camera.stop()
            camera = None
            write_log("[INFO] Camera released.")
            print("📷 Camera released.")
    except Exception as e:
        write_log(f"[WARN] Camera release failed: {e}")
        print(f"⚠️ Camera release failed: {e}")
