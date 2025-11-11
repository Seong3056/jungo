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
    """Picamera2 카메라 초기화 (AI용 색상 유지 + 반사 억제 설정)"""
    global camera

    if camera is not None:
        return camera

    try:
        from picamera2 import Picamera2

        camera = Picamera2()
        config = camera.create_still_configuration(main={"size": (1280, 720)})
        camera.configure(config)
        camera.start()

        # 🔧 AI 분석용 고정 설정: 자동 노출 / 화이트밸런스 비활성화
        controls = {
            "AwbEnable": False,
            "AeEnable": False,
            "ExposureTime": 9000,  # 적정 노출로 반사 억제
            "AnalogueGain": 1.0
        }
        camera.set_controls(controls)

        write_log("[INFO] ✅ Picamera2 initialized successfully (Color AI mode).")
        print("✅ Picamera2 initialized successfully (Color AI mode).")
        return camera

    except Exception as e:
        write_log(f"[ERROR] ❌ Picamera2 initialization failed: {e}")
        print(f"❌ Picamera2 초기화 실패: {e}")
        camera = None
        return None


def apply_color_ai_preprocessing(frame):
    """
    AI 인식률 향상을 위한 전처리:
    - 감마 보정 (밝은 반사 억제)
    - LAB 색공간에서 L 채널 대비 강화
    - 색 정보 유지 (a,b 채널 그대로)
    """
    try:
        # 1️⃣ 감마 보정 (밝은 반사 억제)
        gamma = 0.8  # 1보다 작으면 어두워짐 → 반사 줄이기 효과
        inv_gamma = 1.0 / gamma
        table = np.array([(i / 255.0) ** inv_gamma * 255 for i in np.arange(0, 256)]).astype("uint8")
        frame = cv2.LUT(frame, table)

        # 2️⃣ LAB 변환 (밝기/색 분리)
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        # 3️⃣ L 채널 대비 강화 (equalizeHist)
        l = cv2.equalizeHist(l)

        # 4️⃣ 다시 합치기 (색 정보 유지)
        merged = cv2.merge((l, a, b))
        processed = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)

        # 5️⃣ 약한 블러로 노이즈 완화
        processed = cv2.GaussianBlur(processed, (3, 3), 0)

        return processed

    except Exception as e:
        write_log(f"[WARN] AI 전처리 중 오류: {e}")
        return frame


def capture_image(filename: str = None):
    """카메라로 사진 촬영 후 AI 분석용으로 전처리 + 저장"""
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

        # ✅ 전처리 적용 (색상 유지 + 대비 향상 + 반사 억제)
        processed = apply_color_ai_preprocessing(frame)

        # 저장
        cv2.imwrite(output_path, processed)
        print(f"📸 사진 저장 완료 (AI 컬러용): {output_path}")
        write_log(f"[INFO] 사진 촬영 완료 (AI 컬러용): {output_path}")
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
