import os
import time
import cv2
import numpy as np
from datetime import datetime
from config_loader import PROJECT_ROOT
from logger import write_log

camera = None
camera_busy = False


def init_camera():
    """Picamera2 카메라 초기화 (AI용 노출 및 감마 보정 설정 포함)"""
    global camera

    if camera is not None:
        return camera

    try:
        from picamera2 import Picamera2

        camera = Picamera2()
        config = camera.create_still_configuration(main={"size": (1280, 720)})
        camera.configure(config)
        camera.start()

        # 🔧 AI 분석용 고정 제어값
        controls = {
            "AwbEnable": False,       # 자동 화이트밸런스 끄기
            "AeEnable": False,        # 자동 노출 끄기
            "ExposureTime": 9000,     # 반사 줄이기 위해 살짝 낮춤
            "AnalogueGain": 1.0
        }
        camera.set_controls(controls)

        write_log("[INFO] ✅ Picamera2 initialized successfully (AI optimized mode).")
        print("✅ Picamera2 initialized successfully (AI optimized mode).")
        return camera

    except Exception as e:
        write_log(f"[ERROR] ❌ Picamera2 initialization failed: {e}")
        print(f"❌ Picamera2 초기화 실패: {e}")
        camera = None
        return None


def apply_ai_preprocessing(frame):
    """
    AI 인식률 향상을 위한 전처리:
    - 감마 보정
    - 반사광 억제용 밝기 클리핑
    - 대비 강화(equalizeHist)
    - 약한 블러로 노이즈 제거
    """
    try:
        # 1️⃣ 감마 보정 (밝기 과다 억제)
        gamma = 0.8  # 1보다 작으면 어두워짐 (반사 억제)
        inv_gamma = 1.0 / gamma
        table = np.array([(i / 255.0) ** inv_gamma * 255 for i in np.arange(0, 256)]).astype("uint8")
        frame = cv2.LUT(frame, table)

        # 2️⃣ Grayscale 변환
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 3️⃣ 밝기 클리핑 (하이라이트 억제)
        gray = np.clip(gray, 0, 230).astype(np.uint8)

        # 4️⃣ 대비 강화 (히스토그램 평활화)
        enhanced = cv2.equalizeHist(gray)

        # 5️⃣ 노이즈 완화 (가우시안 블러)
        smoothed = cv2.GaussianBlur(enhanced, (3, 3), 0)

        return smoothed

    except Exception as e:
        write_log(f"[WARN] AI 전처리 중 오류: {e}")
        return frame


def capture_image(filename: str = None):
    """카메라로 사진을 촬영하고 /media 폴더에 저장 (AI 분석용 보정 포함)"""
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

        # 📸 촬영
        frame = camera.capture_array()

        # ✅ AI용 전처리 수행
        processed = apply_ai_preprocessing(frame)

        # 저장
        cv2.imwrite(output_path, processed)
        write_log(f"[INFO] 사진 촬영 및 전처리 완료 (AI용): {output_path}")
        print(f"📸 사진 저장 완료 (AI용): {output_path}")
        return output_path

    except Exception as e:
        write_log(f"[ERROR] 사진 촬영 실패: {e}")
        print(f"⚠️ 사진 촬영 실패: {e}")
        return None

    finally:
        camera_busy = False


def release_camera():
    """프로그램 종료 시 카메라 안전 해제"""
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
