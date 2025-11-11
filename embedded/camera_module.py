import os
import time
import cv2
from datetime import datetime
from config_loader import PROJECT_ROOT
from logger import write_log

# 전역 Picamera2 인스턴스 및 상태
camera = None
camera_busy = False


def init_camera():
    """
    Picamera2 카메라를 전역으로 한 번만 초기화합니다.
    AI 분석용으로 자동 노출, 자동 화이트밸런스를 끄고 일정한 설정으로 고정합니다.
    """
    global camera

    if camera is not None:
        return camera

    try:
        from picamera2 import Picamera2

        camera = Picamera2()
        config = camera.create_still_configuration(main={"size": (1280, 720)})
        camera.configure(config)
        camera.start()

        # ✅ AI 분석용: 자동 기능 비활성화 + 일정한 노출값 유지
        controls = {
            "AwbEnable": False,       # 자동 화이트밸런스 비활성화
            "AeEnable": False,        # 자동 노출 비활성화
            "ExposureTime": 10000,    # 노출 시간(μs 단위, 환경에 따라 조정)
            "AnalogueGain": 1.0       # 감도 고정
        }
        camera.set_controls(controls)

        write_log("[INFO] ✅ Picamera2 initialized successfully (AI mode).")
        print("✅ Picamera2 initialized successfully (AI mode).")
        return camera

    except Exception as e:
        write_log(f"[ERROR] ❌ Picamera2 initialization failed: {e}")
        print(f"❌ Picamera2 초기화 실패: {e}")
        camera = None
        return None


def capture_image(filename: str = None):
    """
    이미 초기화된 Picamera2 카메라로 사진을 촬영하고 /media 폴더에 저장합니다.
    AI 분석용으로 대비가 향상된 흑백 이미지로 저장합니다.
    """
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

        # 저장 폴더 생성
        media_dir = os.path.join(PROJECT_ROOT, "media")
        os.makedirs(media_dir, exist_ok=True)

        # 파일명 자동 생성
        if filename is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"photo_{timestamp}.jpg"
        output_path = os.path.join(media_dir, filename)

        # 📸 촬영
        frame = camera.capture_array()

        # ✅ AI 분석용 전처리 (밝기/대비 개선)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        enhanced = cv2.equalizeHist(gray)  # 히스토그램 평활화 (대비 향상)
        cv2.imwrite(output_path, enhanced)

        print(f"📸 사진 저장 완료 (AI용): {output_path}")
        write_log(f"[INFO] 사진 촬영 완료 (AI용): {output_path}")
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
