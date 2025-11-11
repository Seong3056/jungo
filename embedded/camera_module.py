import os
import time
import cv2
from config_loader import PROJECT_ROOT, config
from logger import write_log


def check_camera():
    """
    카메라 연결 여부 확인 (Picamera2 → OpenCV 순서)
    """
    try:
        # 1️⃣ Picamera2 우선 시도
        from picamera2 import Picamera2
        cam = Picamera2()
        cam.start()
        cam.stop()
        write_log("[INFO] ✅ Camera detected and ready (Picamera2).")
        return True

    except Exception as e:
        write_log(f"[WARN] ⚠️ Picamera2 not available: {e}")

        try:
            # 2️⃣ OpenCV 카메라 확인
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                cap.release()
                write_log("[INFO] ✅ Camera detected and ready (OpenCV).")
                return True
            else:
                write_log("[ERROR] ❌ No camera detected (OpenCV).")
                return False

        except Exception as e2:
            write_log(f"[ERROR] ❌ Camera check failed: {e2}")
            return False


def capture_image():
    """
    카메라로 사진을 촬영하고 저장합니다.
    실행 전 check_camera()를 통해 연결 여부를 먼저 확인합니다.
    """
    output_path = os.path.join(PROJECT_ROOT, config.get("camera", {}).get("output_path", "latest_photo.jpg"))

    # --- 카메라 연결 확인 ---
    if not check_camera():
        print("❌ 카메라 연결 실패. 촬영 불가.")
        write_log("[ERROR] 카메라 연결 실패로 인해 사진 촬영 불가.")
        return None

    try:
        cam = cv2.VideoCapture(0)
        if not cam.isOpened():
            raise Exception("카메라를 열 수 없습니다.")
        time.sleep(0.5)
        ret, frame = cam.read()
        if not ret:
            raise Exception("사진 캡처 실패")
        cv2.imwrite(output_path, frame)
        cam.release()
        print(f"📸 사진 저장 완료: {output_path}")
        write_log(f"[INFO] 사진 촬영 완료: {output_path}")
        return output_path

    except Exception as e:
        print(f"⚠️ 사진 촬영 실패: {e}")
        write_log(f"[ERROR] 사진 촬영 실패: {e}")
        return None
