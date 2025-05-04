from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
from agents.subllm_agent import SubLLMAgent
from prompts.prompt_builder import build_prompt_with_strategies
import os
import re
class CounselorAgent:
    def __init__(self, client_info, persona, model_name="gpt-4o-mini", temperature=0.7):
        self.client_info = client_info
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)
        self.subllm = SubLLMAgent()
        # Load persona prompt based on persona_type
        persona_path = f"prompts/{persona}.txt"
        with open(persona_path, "r", encoding="utf-8") as f:
            self.persona_prompt = f.read()

        self.prompt_template = self.load_prompt_template()

    def load_prompt_template(self):
        with open("prompts/counselor_prompt.txt", "r", encoding="utf-8") as f:
            return f.read()

    # 감정과 인지 왜곡에 맞는 전략 결합
        return f"{emotion_strategy} {distortion_strategy}"
    
    def generate_response(self, history, current_input):
        formatted_history = "\n".join([
            f"{msg['role'].capitalize()}: {msg['message']}" for msg in history
        ])

        # SubLLM 분석
        analysis = self.subllm.analyze(current_input)

        # 전략 프롬프트 조합 (위치 기반 인자 전달!)
        strategy_prompt = build_prompt_with_strategies(
            analysis["반응유형"],
            analysis["상담단계"],
            analysis["상담접근법"]
        )


        # 최종 프롬프트 채우기
        filled_prompt = self.prompt_template.format(
            persona_prompt=self.persona_prompt,
            client_info=self.client_info,
            history=formatted_history,
            current_input=current_input,
            emotion=analysis["감정"],
            distortion=analysis["인지왜곡"],
            strategy_prompt=strategy_prompt
        )

        # LLM 호출
        response = self.llm.invoke(filled_prompt)
        content = response.content if isinstance(response, AIMessage) else str(response)

        # 응답 추출
        reply_match = re.search(r"상담사\s*응답[:：]?\s*(.*?)(?=\n|$)", content, re.DOTALL)
        reply = reply_match.group(1).strip() if reply_match else content.strip()

        return {
            "reply": reply,
            "analysis": analysis
            }

   