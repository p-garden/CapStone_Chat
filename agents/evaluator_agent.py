# agents/evaluator_agent.py
from config import load_prompt
from langchain.prompts import PromptTemplate

class EvaluatorAgent:
    def __init__(self, criteria_name="general_1"):
        self.criteria_name = criteria_name
        self.prompt_text = load_prompt(f"evaluation_{criteria_name}.txt")
        self.template = PromptTemplate(
            input_variables=["conversation"],
            template=self.prompt_text,
        )

    def evaluate(self, history):
        conversation = '\n'.join([
            f"{item['role'].capitalize()}: {item['message']}" for item in history
        ])
        prompt = self.template.format(conversation=conversation)
        return prompt  # 실제 GPT 평가 요청으로 이어질 수 있음

    def evaluate_all(self, history, criteria_list):
        results = {}
        for criteria in criteria_list:
            self.criteria_name = criteria
            self.prompt_text = load_prompt(f"evaluation_{criteria}.txt")
            self.template = PromptTemplate(
                input_variables=["conversation"],
                template=self.prompt_text,
            )
            prompt = self.evaluate(history)
            results[criteria] = prompt  # 실제 GPT 호출로 대체 가능
        return results
