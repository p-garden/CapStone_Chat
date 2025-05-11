from pathlib import Path
from openai import OpenAI
import os
import re
import json
from config import get_config

# 'subllm_prompt.txt' 파일 로드하는 함수
def load_prompt(file_name):
    prompt_path = Path(__file__).resolve().parent.parent / "prompts" / file_name
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()

# SubLLMAgent 클래스
class SubLLMAgent:
    def __init__(self, model="gpt-4o-mini"):
        api_key = get_config()["openai"]["key"]
        self.client = OpenAI(api_key=api_key)
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

    def classify_topic(self, user_input: str) -> str:
        """
        사용자의 발화를 11가지 주제 중 하나로 분류하여 반환
        """
        topic_prompt = f"""
        다음 사용자 발화를 읽고 아래 11개 주제 중 가장 관련 있는 하나를 골라 반환해줘.
        오직 주제 이름만 한 단어로 출력해줘. 설명하지 마.

        [주제 목록]
        1. 우울/무기력
        2. 불안/긴장
        3. 대인관계/소통 어려움
        4. 진로/미래 불안
        5. 학업/성적 스트레스
        6. 직장/업무 스트레스
        7. 가족 문제
        8. 연애/이별
        9. 자기이해/성격 혼란
        10. 생활습관/신체 문제
        11. 기타

        [사용자 발화]
        {user_input}
        """

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0.2,
            max_tokens=30,
            messages=[
                {"role": "system", "content": "너는 전문 심리상담 분석가야. 주제만 정확히 선택해서 한 단어로 알려줘."},
                {"role": "user", "content": topic_prompt}
            ]
        )
        return response.choices[0].message.content.strip()

def classify_topic(user_input: str, model="gpt-4o-mini") -> str:
    from openai import OpenAI
    import os
    api_key = get_config()["openai"]["key"]
    client = OpenAI(api_key=api_key)
    topic_prompt = f"""
    다음 사용자 발화를 읽고 아래 11개 주제 중 가장 관련 있는 하나를 골라 반환해줘.
    오직 주제 이름만 한 단어로 출력해줘. 설명하지 마.

    [주제 목록]
	1.	학업/성적 스트레스
	2.	직장/업무 스트레스
	3.	진로/미래 불안
	4.	대인관계/소통 어려움
	5.	가족 문제
	6.	연애/이별
	7.	자기이해/성격 혼란
	8.	생활습관/신체 문제
	9.	기타

    [사용자 발화]
    {user_input}
    """

    response = client.chat.completions.create(
        model=model,
        temperature=0.2,
        max_tokens=30,
        messages=[
            {"role": "system", "content": "너는 전문 심리상담 분석가야. 주제만 정확히 선택해서 한 단어로 알려줘."},
            {"role": "user", "content": topic_prompt}
        ]
    )
    return response.choices[0].message.content.strip()
