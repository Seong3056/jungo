import base64
import json
from openai import OpenAI
from config_loader import config
from logger import write_log   # pi.log 기록
from listings.models import Listing
from django.core.files import File
import os

# API KEY
openai_key = config.get("openai", {}).get("api_key")
client = OpenAI(api_key=openai_key)


def analyze_image(image_path: str):
    # 이미지 Base64 변환
    with open(image_path, "rb") as f:
        image_base64 = base64.b64encode(f.read()).decode("utf-8")

    # ----- 1) OpenAI Vision 요청 -----
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "너는 제품 브랜드·모델·중고 시세를 분석하는 전문가이다. "
                    "중고가는 반드시 '당근마켓 기준 중고 거래가'로 판단한다. "
                    "중고가는 문자열이 아니라 정수 배열 형태로 출력해야 한다."
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "이 사진 속 제품의 브랜드, 모델명, confidence(0~100)를 판별하고 "
                            "당근마켓 기준 중고가를 배열 형태로 제공해줘.\n"
                            "예: {'brand':'Samsung','product':'Galaxy S21','confidence':90,'used_price':[15,18]}\n"
                            "반드시 JSON 딕셔너리 형식만 출력해."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        },
                    },
                ],
            },
        ],
    )

    result_text = response.choices[0].message.content
    print("🧠 AI 분석 원문:", result_text)

    # ----- 2) JSON 파싱 -----
    try:
        clean_text = result_text.replace("'", '"')
        result_dict = json.loads(clean_text)
    except:
        result_dict = {"raw": result_text}

    write_log(f"[AI] 분석 결과: {result_dict}")

    # ----- 3) Listing DB 저장 -----
    try:
        last_listing = Listing.objects.last()
        if last_listing:
            # 3-1. 촬영 이미지 저장
            file_name = os.path.basename(image_path)
            with open(image_path, "rb") as f:
                last_listing.capture_image.save(file_name, File(f), save=False)

            # 3-2. used_price 배열 → 최저가 저장
            if "used_price" in result_dict and isinstance(result_dict["used_price"], list):
                used_low = min(result_dict["used_price"])
                last_listing.used_low_price = used_low

            last_listing.save()
            print(f"📌 Listing({last_listing.id})에 이미지 + 최저가 저장 완료")
            write_log(f"[DB] Listing({last_listing.id}) 저장 완료")
        else:
            print("❌ 저장할 Listing(상품)이 없음")
            write_log("[ERROR] 저장할 Listing이 없음")
    except Exception as e:
        print(f"⚠️ Listing 저장 오류: {e}")
        write_log(f"[ERROR] Listing 저장 오류: {e}")

    # 결과 반환
    return result_dict
