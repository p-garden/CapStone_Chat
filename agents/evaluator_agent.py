from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
from config import load_prompt
import os

class EvaluatorAgent:
    def __init__(self, criteria_list, model_name="gpt-4o-mini", temperature=0.7):
        self.criteria_list = criteria_list  # 평가 기준 리스트
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)

        self.prompt_templates = self.load_prompt_templates()

    def load_prompt_templates(self):
        prompt_templates = {}
        for criteria in self.criteria_list:
            prompt_path = f"prompts/evaluation_{criteria}.txt"
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt_templates[criteria] = f.read()
        return prompt_templates

    def evaluate(self, history, criteria):
        conversation = '\n'.join([
            f"{item['role'].capitalize()}: {item['message']}" for item in history
        ])
        
        filled_prompt = self.prompt_templates[criteria].format(
            conversation=conversation
        )

        response = self.llm.invoke(filled_prompt)

        if isinstance(response, AIMessage):
            return response.content  # 응답 내용 반환
        return str(response)

    def evaluate_all(self, history):
        results = {}
        for criteria in self.criteria_list:
            result = self.evaluate(history, criteria)
            results[criteria] = result  # 평가 결과를 기준별로 저장
        return results

# 사용 예시
if __name__ == "__main__":
    history = [
        {"role": "counselor", "message": "안녕하세요, 로라. 어떻게 지내세요?"},
        {"role": "client", "message": "요즘 너무 벅차게 느껴져요."},
        # 여기에 실제 상담 대화 내용 추가
    ]
    
    evaluator = EvaluatorAgent(criteria_list=["general_1", "general_2", "cbt_1"])
    results = evaluator.evaluate_all(history)
    
    # 결과 출력
    for criteria, result in results.items():
        print(f"{criteria}: {result}")