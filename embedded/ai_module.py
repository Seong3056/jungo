import base64
import cv2
import numpy as np
from openai import OpenAI
from config_loader import config
from logger import write_log

openai_key = config.get("openai", {}).get("api_key")
openai_model = config.get("openai", {}).get("model", "gpt-4o-mini")

client = OpenAI(api_key=openai_key)

def analyze_image(image_path):
    try:
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        brightness = np.mean(gray)
        sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()

        brightness_score = min(max((brightness / 128) * 100, 0), 100)
        sharpness_score = min(max((sharpness / 150) * 100, 0), 100)
        quality_score = round((brightness_score * 0.4 + sharpness_score * 0.6), 2)

        with open(image_path, "rb") as img_file:
            image_base64 = base64.b64encode(img_file.read()).decode("utf-8")

        response = client.chat.completions.create(
            model=openai_model,
            messages=[
                {"role": "system", "content": "너는 제품 인식 및 품질 분석 전문가야."},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "이 사진 속 물건의 브랜드, 제품명을 식별하고 "
                                "제품 일치도(confidence, 0~100)를 포함한 딕셔너리로 출력해줘. "
                                "형식 예시: {'brand': 'Nike', 'product': 'Air Max 90', 'confidence': 92}"
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                        },
                    ],
                },
            ],
        )

        ai_result_text = response.choices[0].message.content
        print(f"🧠 AI 분석 원문: {ai_result_text}")

        import json
        try:
            ai_result = json.loads(ai_result_text)
        except:
            ai_result = {"raw": ai_result_text}

        result = {
            "brand": ai_result.get("brand", "Unknown"),
            "product": ai_result.get("product", "Unknown"),
            "confidence": ai_result.get("confidence", 0),
            "brightness": round(brightness, 2),
            "sharpness": round(sharpness, 2),
            "quality_score": quality_score,
            "status": "Good" if quality_score > 70 else "Poor",
        }

        print(f"✅ 종합 분석 결과: {result}")
        write_log(f"[AI] 종합 분석 결과: {result}")
        return result

    except Exception as e:
        print(f"⚠️ 이미지 분석 실패: {e}")
        write_log(f"[ERROR] 이미지 분석 실패: {e}")
        return None
