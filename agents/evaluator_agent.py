from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage

import os

class EvaluatorAgent:
    def __init__(self, model_name="gpt-4o-mini", temperature=0.7):
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)
        # 통합 평가 프롬프트 템플릿 로드
        with open("prompts/evaluation_combined.txt", "r", encoding="utf-8") as f:
            self.prompt_template = f.read()

    def evaluate_all(self, history):
        """
        상담 대화 전체에 대해 6개 항목을 통합하여 평가합니다.
        """
        conversation = '\n'.join([
            f"{item['role'].capitalize()}: {item['message']}" for item in history
        ])
        filled_prompt = self.prompt_template.format(conversation=conversation)

        response = self.llm.invoke(filled_prompt)
        return response.content.strip() if isinstance(response, AIMessage) else str(response).strip()

    def generate_feedback_summary(self, history, evaluation_result):
        """
        통합 평가 결과를 종합 피드백으로 그대로 사용합니다.
        """
        return evaluation_result