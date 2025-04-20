from pathlib import Path
from openai import OpenAI
import os
import re
import json

# 'subllm_prompt.txt' 파일 로드하는 함수
def load_prompt(file_name):
    prompt_path = Path(__file__).resolve().parent.parent / "prompts" / file_name
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()

# SubLLMAgent 클래스
class SubLLMAgent:
    def __init__(self, model="gpt-4o-mini"):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model
        self.prompt_template = load_prompt("subllm_prompt.txt")

    def analyze(self, user_input: str) -> dict:
        # 분석용 프롬프트 구성
        prompt = self.prompt_template.format(text=user_input)

        # GPT 호출
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0.4,
            max_tokens=1000,
            messages=[
                {"role": "system", "content": "너는 인지행동치료(CBT) 기반의 전문 심리상담 보조 LLM이야."},
                {"role": "user", "content": prompt}
            ]
        )

        raw_text = response.choices[0].message.content
        parsed = self._parse_llm_response(raw_text)

        # 모든 키와 값의 앞뒤 공백 제거
        cleaned = {k.strip(): v.strip() for k, v in parsed.items()}
        return cleaned

    def _parse_llm_response(self, response: str) -> dict:
        # 초기값 설정
        emotion = "감지되지 않음"
        distortion = "감지되지 않음"
        reaction = "감지되지 않음"
        stage = "감지되지 않음"
        approach = "감지되지 않음"

        # 감정
        emotion_match = re.search(r"감정:\s*(.*)", response)
        if emotion_match:
            emotion = emotion_match.group(1).strip()

        # 인지 왜곡
        distortion_match = re.search(r"인지 왜곡:\s*(.*)", response)
        if distortion_match:
            distortions_raw = distortion_match.group(1).strip()
            if distortions_raw and distortions_raw.lower() != "없음":
                distortions = [d.strip() for d in distortions_raw.split(',')]
                distortion = ", ".join(distortions)
            else:
                distortion = "없음"

        # 반응 유형
        reaction_match = re.search(r"반응 유형:\s*(.*)", response)
        if reaction_match:
            reaction = reaction_match.group(1).strip()

        # 상담 단계
        stage_match = re.search(r"상담 단계:\s*(.*)", response)
        if stage_match:
            stage = stage_match.group(1).strip()

        # 상담 접근법
        approach_match = re.search(r"상담 접근법:\s*(.*)", response)
        if approach_match:
            approach = approach_match.group(1).strip()

        return {
            "감정": emotion,
            "인지왜곡": distortion,
            "반응유형": reaction,
            "상담단계": stage,
            "상담접근법": approach
        }
