import os
import time
import cv2
from datetime import datetime
from config_loader import PROJECT_ROOT
from logger import write_log

camera = None
camera_busy = False


def init_camera():
    """Picamera2 카메라를 전역으로 한 번만 초기화 (컬러 원본 모드)"""
    global camera

    if camera is not None:
        return camera

    try:
        from picamera2 import Picamera2

        camera = Picamera2()
        config = camera.create_still_configuration(main={"size": (1280, 720)})
        camera.configure(config)
        camera.start()

        # ✅ 자동 노출 및 화이트밸런스 활성화 (자연스러운 색감)
        controls = {
            "AwbEnable": True,     # 자동 화이트밸런스 켜기
            "AeEnable": True,      # 자동 노출 켜기
        }
        camera.set_controls(controls)

        write_log("[INFO] ✅ Picamera2 initialized successfully (Color original mode).")
        print("✅ Picamera2 initialized successfully (Color original mode).")
        return camera

    except Exception as e:
        write_log(f"[ERROR] ❌ Picamera2 initialization failed: {e}")
        print(f"❌ Picamera2 초기화 실패: {e}")
        camera = None
        return None


def capture_image(filename: str = None):
    """Picamera2 컬러 사진 촬영 후 /media 폴더에 저장"""
    global camera, camera_busy

    if camera_busy:
        write_log("[WARN] 카메라가 이미 촬영 중입니다. 요청 무시.")
        return None
    camera_busy = True

    try:
        if camera is None:
            camera = init_camera()
            if camera is None:
                write_log("[ERROR] Picamera2 unavailable — capture aborted.")
                camera_busy = False
                return None

        # 저장 경로
        media_dir = os.path.join(PROJECT_ROOT, "media")
        os.makedirs(media_dir, exist_ok=True)

        # 파일명 자동 생성
        if filename is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"photo_{timestamp}.jpg"
        output_path = os.path.join(media_dir, filename)

        # 📸 컬러 원본 촬영
        frame = camera.capture_array()

        # ✅ 원본 컬러 그대로 저장
        cv2.imwrite(output_path, frame)
        print(f"📸 컬러 사진 저장 완료: {output_path}")
        write_log(f"[INFO] 컬러 사진 저장 완료: {output_path}")
        return output_path

    except Exception as e:
        write_log(f"[ERROR] 사진 촬영 실패: {e}")
        print(f"⚠️ 사진 촬영 실패: {e}")
        return None

    finally:
        camera_busy = False


def release_camera():
    """프로그램 종료 시 카메라 해제"""
    global camera
    try:
        if camera:
            camera.stop()
            camera = None
            write_log("[INFO] 📷 Camera released successfully.")
            print("📷 Camera released successfully.")
    except Exception as e:
        write_log(f"[WARN] Camera release failed: {e}")
        print(f"⚠️ Camera release failed: {e}")
