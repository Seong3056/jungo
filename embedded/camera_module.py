import os
import time
import cv2
from datetime import datetime
from config_loader import PROJECT_ROOT
from logger import write_log

camera = None
camera_busy = False


def init_camera():
    """고품질 사진 촬영용 Picamera2 초기화 (실제 색감 최적화 스틸 모드)"""
    global camera

    if camera is not None:
        return camera

    try:
        from picamera2 import Picamera2
        from libcamera import Transform

        camera = Picamera2()

        # 📌 스틸 모드 (정확한 색감 + 전체 ISP 파이프라인 사용)
        config = camera.create_still_configuration(
            main={"size": (3280, 2464)},  # 센서 원본 해상도
            transform=Transform(rotation=-90)  # 화면 회전
        )
        camera.configure(config)
        camera.start()

        # 📌 자동 노출 + 자동 화이트밸런스 완전 활성화
        camera.set_controls({
            "AwbEnable": True,
            "AeEnable": True,
        })

        write_log("[INFO] 📸 Picamera2 initialized (still mode, full color accuracy).")
        print("📸 Picamera2 initialized (still mode, full color accuracy).")

        return camera

    except Exception as e:
        write_log(f"[ERROR] ❌ Picamera2 initialization failed: {e}")
        print(f"❌ Picamera2 초기화 실패: {e}")
        camera = None
        return None


def capture_image(filename: str = None):
    """컬러 정확도 최상급 촬영 후 /media 폴더에 저장"""
    global camera, camera_busy

    if camera_busy:
        write_log("[WARN] 카메라 촬영 중 → 요청 무시.")
        return None
    camera_busy = True

    try:
        if camera is None:
            camera = init_camera()
            if camera is None:
                write_log("[ERROR] 😢 카메라 초기화 실패로 촬영 중단")
                camera_busy = False
                return None

        # 저장 경로 생성
        media_dir = os.path.join(PROJECT_ROOT, "media")
        os.makedirs(media_dir, exist_ok=True)

        # 파일명 자동 생성
        if filename is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"photo_{timestamp}.jpg"

        output_path = os.path.join(media_dir, filename)

        # 📸 고품질 컬러 이미지 캡처 (스틸 모드 full ISP 적용됨)
        frame = camera.capture_array()

        cv2.imwrite(output_path, frame)
        print(f"📁 저장 완료: {output_path}")
        write_log(f"[INFO] 사진 저장 완료: {output_path}")

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
            write_log("[INFO] 📷 Camera released.")
            print("📷 Camera released.")
    except Exception as e:
        write_log(f"[WARN] Camera release failed: {e}")
        print(f"⚠️ Camera release failed: {e}")
