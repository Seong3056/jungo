import base64
import json
from openai import OpenAI
from config_loader import config
from logger import write_log   # pi.log 기록

# config.yml 에서 API KEY 읽기
openai_key = config.get("openai", {}).get("api_key")
client = OpenAI(api_key=openai_key)


def analyze_image(image_path: str):
    # 이미지 Base64 변환
    with open(image_path, "rb") as f:
        image_base64 = base64.b64encode(f.read()).decode("utf-8")

    # OpenAI Vision 호출 — 중고가 배열 형태 강제
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
                            "★ 반드시 JSON 딕셔너리 형식만 출력하고 used_price는 숫자 배열로 출력해."
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

    # 문자열 → 딕셔너리 변환
    try:
        # 작은따옴표 → 큰따옴표 처리 후 JSON 변환
        clean_text = result_text.replace("'", '"')
        result_dict = json.loads(clean_text)
    except Exception:
        # 파싱 실패 시 raw 반환
        result_dict = {"raw": result_text}

    # pi.log 기록
    write_log(f"[AI] 분석 결과: {result_dict}")

    return result_dict
