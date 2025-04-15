from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
import os
import re
class CounselorAgent:
    def __init__(self, client_info, persona_type, model_name="gpt-4o-mini", temperature=0.7):
        self.client_info = client_info
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)

        # Load persona prompt based on persona_type
        persona_path = f"prompts/{persona_type}.txt"
        with open(persona_path, "r", encoding="utf-8") as f:
            self.persona_prompt = f.read()

        self.prompt_template = self.load_prompt_template()

    def load_prompt_template(self):
        with open("prompts/counselor_prompt.txt", "r", encoding="utf-8") as f:
            return f.read()
    

        
    # 감정과 인지 왜곡에 맞는 전략 결합
        return f"{emotion_strategy} {distortion_strategy}"
    
    def generate_response(self, history,latest_client_message):

        # 인사 반복 방지 안내
        extra_instruction = ""
        if len(history) > 0:
            extra_instruction = "\n※ 이전 인사 내용은 이미 언급되었습니다. 이번 응답에서는 인사말을 반복하지 말고 본론에 집중해 주세요."

        # history를 문자열로 변환
        formatted_history = "\n".join([f"{msg['role'].capitalize()}: {msg['message']}" for msg in history])

        filled_prompt = self.prompt_template.format(
            client_info=self.client_info,
            history=formatted_history,  # 변환된 문자열 사용
            persona_prompt=self.persona_prompt,
            latest_client_message=latest_client_message
        ) + extra_instruction

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

        # 상담사 응답 추출
        reply_match = re.search(r"상담사\s*응답:\s*(.*?)(?:\n\[감정\]|$)", text, re.DOTALL)
        if reply_match:
            result["reply"] = reply_match.group(1).strip()

        # 감정, 인지 왜곡, 전략 줄 파싱
        meta_line_match = re.search(r"\[감정\](.*?)\|\s*\[인지 왜곡\](.*?)\|\s*\[전략\](.*)", text)
        if meta_line_match:
            result["emotion"] = meta_line_match.group(1).strip()
            result["distortion"] = meta_line_match.group(2).strip()
            result["cbt_strategy"] = meta_line_match.group(3).strip()

        if not result["reply"]:
            result["reply"] = "[⚠️ 상담사 응답을 생성하지 못했습니다.]"

        print("[🔍 LLM 응답 결과 전체]:\n", text)

        return result
