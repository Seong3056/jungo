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


def _extract_json_text(result_text: str) -> str:
    """
    OpenAI가 ```json ... ``` 형식으로 줄 때도 있고,
    그냥 JSON만 줄 때도 있으니까, 코드블럭을 벗겨서 순수 JSON만 반환.
    """
    text = result_text.strip()

    if "```" in text:
        parts = text.split("```")
        # 예: ['', 'json\n{...}', ''] 이런 식으로 옴
        if len(parts) >= 2:
            inner = parts[1]
            # 맨 앞 줄에 'json' 같은 언어 표시가 있을 수 있음
            lines = inner.splitlines()
            if lines and lines[0].strip().lower().startswith("json"):
                lines = lines[1:]
            text = "\n".join(lines).strip()

    return text


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
                    "반드시 마크다운 코드블럭 없이, 순수 JSON 딕셔너리만 출력해라. "
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
                            "당근마켓 기준 중고가를 실수, 배열 형태로 제공해줘.\n"
                            "예: {'brand':'Samsung','product':'Galaxy S21','confidence':90,'used_price':[15.0,18.0]}\n"
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

    result_text = response.choices[0].message.content or ""
    print("🧠 AI 분석 원문:", result_text)

    # ----- 2) JSON 파싱 -----
    raw_text = result_text
    json_text = _extract_json_text(result_text)
    # 작은따옴표로 줄 수도 있으니까 한 번 정규화
    json_text = json_text.replace("'", '"')

    try:
        parsed = json.loads(json_text)
        if isinstance(parsed, dict):
            result_dict = parsed
        else:
            # 혹시 리스트나 다른 타입으로 오면 raw와 함께 보존
            result_dict = {"parsed": parsed, "raw": raw_text}
    except Exception as e:
        write_log(f"[AI] JSON 파싱 실패: {e} / text={raw_text[:200]}")
        result_dict = {"raw": raw_text}

    write_log(f"[AI] 분석 결과: {result_dict}")

    # ----- 2-1) used_price 안전 처리 -----
    used_low = None
    used_high = None

    price_field = result_dict.get("used_price")

    try:
        if isinstance(price_field, list) and price_field:
            # ['100', 130] 섞여도 int로 캐스팅
            price_values = [int(float(p)) for p in price_field]
            used_low = min(price_values)
            used_high = max(price_values)
        elif isinstance(price_field, (int, float, str)):
            v = int(float(price_field))
            used_low = v
            used_high = v

        if used_low is not None:
            write_log(f"[AI] 중고가 범위: low={used_low}, high={used_high}")
    except Exception as e:
        write_log(f"[AI] used_price 처리 실패: {e} / used_price={price_field}")

    # ----- 3) Listing DB 저장 -----
    try:
        last_listing = Listing.objects.last()
        if last_listing:
            # 3-1. 촬영 이미지 저장
            file_name = os.path.basename(image_path)
            with open(image_path, "rb") as f:
                last_listing.capture_image.save(file_name, File(f), save=False)

            # 3-2. used_price 배열 → 최저가 저장
            if used_low is not None:
                if used_low > 10000:
                    last_listing.used_low_price = used_low
                elif used_low > 100:
                    last_listing.used_low_price = used_low * 1000
                else:
                    last_listing.used_low_price = used_low * 10000
                write_log(f"[DB] Listing({last_listing.id}) used_low_price={used_low}")
            else:
                write_log(f"[DB] Listing({last_listing.id}) used_low_price 업데이트 안 함(값 없음)")

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
