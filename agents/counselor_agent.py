from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
import os
import re


class CounselorAgent:
    def __init__(self, client_info, persona_type, model_name="gpt-4o-mini", temperature=0.7):
        self.client_info = client_info
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)

        # 페르소나 프롬프트 로드
        persona_path = f"prompts/{persona_type}.txt"
        with open(persona_path, "r", encoding="utf-8") as f:
            self.persona_prompt = f.read()

        # 메인 프롬프트 로드
        self.prompt_template = self.load_prompt_template()

    def load_prompt_template(self):
        with open("prompts/counselor_prompt.txt", "r", encoding="utf-8") as f:
            return f.read()

    def generate_response(self, history, current_input):
        formatted_history = "\n".join([
            f"{msg['role'].capitalize()}: {msg['message']}" for msg in history
        ])

        # 인사 반복 방지 안내
        extra_instruction = ""
        if len(history) > 0:
            extra_instruction = "\n※ 이전 인사 내용은 이미 언급되었습니다. 이번 응답에서는 인사말을 반복하지 말고 본론에 집중해 주세요."

        # 최종 프롬프트 작성
        filled_prompt = self.prompt_template.format(
            persona_prompt=self.persona_prompt,
            client_info=self.client_info,
            history=formatted_history,
            current_input=current_input
        ) + extra_instruction

        # LLM 호출
        response = self.llm.invoke(filled_prompt)
        content = response.content if isinstance(response, AIMessage) else str(response)

        return self._parse_response(content)

    def _parse_response(self, text: str) -> dict:
        result = {
            "emotion": "감지되지 않음",
            "distortion": "감지되지 않음",
            "cbt_strategy": "전략 없음",
            "reply": ""
        }

        # 1. 상담사 응답 추출 (이전보다 더 유연하게)
        reply_match = re.search(r"상담사\s*응답[:：]?\s*(.*?)(?=\n\s*\[감정\]|\n\[감정\]|\Z)", text, re.DOTALL)
        if reply_match:
            result["reply"] = reply_match.group(1).strip()

        # 2. 감정/인지/전략 메타데이터 추출
        meta_matches = re.findall(r"\[감정\](.*?)\|\s*\[인지 왜곡\](.*?)\|\s*\[전략\](.*)", text)
        if meta_matches:
            # 가장 마지막에 등장한 메타 정보 사용
            last_meta = meta_matches[-1]
            result["emotion"] = last_meta[0].strip()
            result["distortion"] = last_meta[1].strip()
            result["cbt_strategy"] = last_meta[2].strip()

        # 3. fallback: 상담사 응답이 비었을 경우 텍스트 전체 사용
        if not result["reply"]:
            fallback = text.strip().split("\n")[0]
            if len(fallback) > 10:
                result["reply"] = fallback
            else:
                result["reply"] = "[⚠️ 상담사 응답을 생성하지 못했습니다.]"

        print("[🔍 LLM 응답 결과 전체]:\n", text)
        return result
