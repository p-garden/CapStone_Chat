import json
import os
from pathlib import Path
from openai import OpenAI
from fastapi import HTTPException  # ✅ 추가
from datetime import datetime

from DB import get_chat_log, save_analysis_report
from config import set_openai_api_key

# ✅ OpenAI API 키 설정
set_openai_api_key()

# ✅ 프롬프트 템플릿 로드
def load_prompt_template(filename: str = "report_prompt.txt") -> str:
    prompt_path = Path(__file__).resolve().parent / "prompts" / filename
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()

# ✅ 채팅 로그를 내담자/상담자 형식으로 정리
def format_dialogue(chat_log: list) -> str:
    return "\n".join([
        f"{'내담자' if msg['role'] == 'client' else '상담자'}: {msg['message']}"
        for msg in chat_log
    ])

# ✅ GPT 호출 및 분석 리포트 생성
def generate_analysis_report(chatId: int, userId: int) -> dict:
    chat_log = get_chat_log(chatId)

    if not chat_log:
        print("❌ chat_log 없음!")
        raise HTTPException(status_code=404, detail=f"chatId {chatId}에 대한 대화가 없습니다.")

    # 2. 대화 포맷 구성
    formatted_dialogue = format_dialogue(chat_log)

    # 3. 프롬프트 텍스트 채우기
    prompt_template = load_prompt_template()
    prompt = prompt_template.replace("{dialogue}", formatted_dialogue)\
                            .replace("{chatId}", str(chatId))\
                            .replace("{userId}", str(userId))

    # 4. OpenAI GPT 호출
    from config import get_config
    api_key = get_config()["openai"]["key"]
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.4,
        messages=[
            {"role": "system", "content": "너는 심리상담 데이터를 분석해서 JSON 보고서를 작성하는 전문가야."},
            {"role": "user", "content": prompt}
        ]
    )

    # 5. 결과 파싱
    raw_output = response.choices[0].message.content

    # 마크다운 코드블록 제거 (```json ... ```)
    if raw_output.startswith("```json"):
        raw_output = raw_output.strip("```json").strip("```").strip()
    elif raw_output.startswith("```"):
        raw_output = raw_output.strip("```").strip()

    try:
        result = json.loads(raw_output)
    except json.JSONDecodeError:
        raise ValueError("LLM이 반환한 응답이 JSON 형식이 아닙니다:\n" + raw_output)

    return result
