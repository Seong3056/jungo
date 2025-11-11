import os
import time
import cv2
from config_loader import PROJECT_ROOT, config
from logger import write_log

def capture_image():
    output_path = os.path.join(PROJECT_ROOT, config.get("camera", {}).get("output_path", "latest_photo.jpg"))
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
