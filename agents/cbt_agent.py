from pathlib import Path
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

class CBTStrategyAgent:
    def __init__(self, example: dict, cognitive_distortion: str):
        self.client_info = example["AI_counselor"]["Response"]["client_information"]
        self.reason = example["AI_counselor"]["Response"]["reason_counseling"]
        self.history = example["AI_counselor"]["CBT"].get("init_history_client", "")
        self.distortion = cognitive_distortion
        self.prompt_template = self._load_template()
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

    def _load_template(self):
        prompt_path = Path("prompts/cbt_strategy_prompt.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            template_text = f.read()
        return PromptTemplate(
            input_variables=[
                "client_information",
                "reason_counseling",
                "history",
                "cognitive_distortion",
            ],
            template=template_text,
        )

    def generate(self):
        prompt = self.prompt_template.format(
            client_information=self.client_info,
            reason_counseling=self.reason,
            history=self.history,
            cognitive_distortion=self.distortion
        )

        result = self.llm.invoke(prompt).content
        try:
            technique = result.split("CBT Strategy:")[0].replace("CBT Technique:", "").strip()
            strategy = result.split("CBT Strategy:")[1].strip()
        except:
            technique = ""
            strategy = result.strip()

        return technique, strategy