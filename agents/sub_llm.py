from pathlib import Path
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import os
from openai import OpenAI  # ✅ 이 줄이 꼭 필요해!
from cbt.cbt_mappings import emotion_strategies, cognitive_distortion_strategies
import re

def load_prompt(file_name):
        prompt_path = Path(__file__).resolve().parent.parent / "prompts" / file_name
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()

class SubLLMAgent:
    from pathlib import Path
            
    def __init__(self, model="gpt-4"):
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)
        self.prompt_template = load_prompt("subllm_prompt.txt")
        self.model = model

    def analyze(self, user_input: str) -> dict:
        prompt = self.prompt_template.format(text=user_input)

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0.4,
            max_tokens=1000,
            messages=[
                {"role": "system", "content": "너는 인지행동치료 기반의 심리상담 보조 전문가야."},
                {"role": "user", "content": prompt}
            ]
        )

        raw_text = response.choices[0].message.content
        return self._parse_llm_response(raw_text)

    def _parse_llm_response(self, response: str) -> dict:
        emotion = ""
        emotion_strategy = ""
        distortion = ""
        distortion_strategy = ""

        # 감정 추출
        emotion_match = re.search(r"감정:\s*(\S+)", response)
        if emotion_match:
            emotion = emotion_match.group(1).strip()
            emotion_strategy = emotion_strategies.get(emotion, "")

        # 인지 왜곡 추출
        distortion_match = re.search(r"인지 왜곡:\s*(\S+)", response)
        if distortion_match:
            distortion = distortion_match.group(1).strip()
            distortion_strategy = cognitive_distortion_strategies.get(distortion, "")

        return {
            "감정": emotion,
            "감정_CBT전략": emotion_strategy,
            "인지왜곡": distortion,
            "인지왜곡_CBT전략": distortion_strategy,
            "원본문": response
        }
