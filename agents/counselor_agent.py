from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
import os

class CounselorAgent:
    def __init__(self, client_info, reason, cbt_technique, cbt_strategy, persona_type, emotion, distortion=None, model_name="gpt-4o-mini", temperature=0.7):
        self.client_info = client_info
        self.reason = reason
        self.cbt_technique = cbt_technique
        self.cbt_strategy = cbt_strategy
        self.emotion = emotion  
        self.distortion = distortion
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)

        # Load persona prompt based on persona_type
        persona_path = f"prompts/{persona_type}.txt"
        with open(persona_path, "r", encoding="utf-8") as f:
            self.persona_prompt = f.read()

        self.prompt_template = self.load_prompt_template()

    def load_prompt_template(self):
        with open("prompts/counselor_prompt.txt", "r", encoding="utf-8") as f:
            return f.read()

    def generate_response(self, history):
        filled_prompt = self.prompt_template.format(
            client_info=self.client_info,
            reason=self.reason,
            history=history,
            cbt_technique=self.cbt_technique,
            cbt_strategy=self.cbt_strategy,
            persona_prompt=self.persona_prompt,
            emotion=self.emotion,
            distortion=self.distortion
        )

        response = self.llm.invoke(filled_prompt)

        if isinstance(response, AIMessage):
            return response.content 
        return str(response)