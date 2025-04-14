from pathlib import Path
from openai import OpenAI
import os
import re
from cbt.cbt_mappings import emotion_strategies, cognitive_distortion_strategies
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
        self.prompt_template = load_prompt("subllm_prompt.txt")  # 'subllm_prompt.txt'를 로드

    def analyze(self, user_input: str) -> dict:
        # 'subllm_prompt.txt'를 기반으로 하는 프롬프트 생성
        prompt = self.prompt_template.format(text=user_input)  # 사용자 입력을 프롬프트에 삽입

        # OpenAI API 호출
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0.4,
            max_tokens=1000,
            messages=[{"role": "system", "content": "너는 인지행동치료 기반의 심리상담 보조 전문가야."},
                      {"role": "user", "content": prompt}]
        )

        raw_text = response.choices[0].message.content
        return self._parse_llm_response(raw_text)

    def _parse_llm_response(self, response: str) -> dict:
        emotion = ""
        distortion = ""

        # 감정 추출 (감정: '슬픔', '기쁨' 등)
        emotion_match = re.search(r"감정:\s*(\S+)", response)
        if emotion_match:
            emotion = emotion_match.group(1).strip()

        # 인지 왜곡 추출 
        distortion_matches = re.findall(r"인지 왜곡:\s*([^,]+(?:,\s*[^,]+)*)", response)

        if distortion_matches:
            # 왜곡 이름 리스트로 정리
            distortions = [d.strip() for d in distortion_matches[0].split(',')]
            distortion = ", ".join(distortions)

        else:
            distortion = "없음"
        # 최종 반환할 JSON 형식으로 결과를 생성
        return {
            "감정": emotion,
            "인지왜곡": distortion,
            "원본문": response
        }
