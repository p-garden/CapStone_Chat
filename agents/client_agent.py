from pathlib import Path
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI


class ClientAgent:
    def __init__(self, example):
        # Provide default values for persona_type and attitude if not explicitly included in the example
        self.persona_name = example.get("persona_type", "다정한_친구")
        self.attitude = example.get("attitude", "neutral")
        self.prompt_template = self._load_prompt()
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

    def _load_prompt(self):
        prompt_path = Path(__file__).resolve().parents[1] / "prompts" / "client_prompt.txt"
        with open(prompt_path, encoding="utf-8") as f:
            template = f.read()

        return PromptTemplate(
            input_variables=["intake_form", "attitude_instruction", "history"],
            template=template
        )

    def generate(self, intake_form: str, attitude_instruction: str, history: str):
        prompt = self.prompt_template.format(
            intake_form=intake_form,
            attitude_instruction=attitude_instruction,
            history=history
        )
        response = self.llm.invoke(prompt)
        return response.content