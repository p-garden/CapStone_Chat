"""
실행 코드
python3 chat.py \
  --input_file data/example1.json \
  --output_file results/result1.json \
  --persona_type persona_20s_friend
"""

import json
from pathlib import Path
from agents.client_agent import ClientAgent
from agents.counselor_agent import CounselorAgent
from agents.evaluator_agent import EvaluatorAgent
from agents.cbt_agent import CBTStrategyAgent
from config import get_config
from config import set_openai_api_key
set_openai_api_key()

class TherapySimulation:
    def __init__(self, example: dict, persona_type: str, max_turns: int = 20):
        self.example = example
        self.persona_type = persona_type
        self.max_turns = max_turns
        self.history = []
        self.metadata = get_config()

        self.client_agent = ClientAgent(example["AI_client"])
        self.emotion_state = example["AI_client"].get("emotion_state", "")
        self.cognitive_distortion = example["AI_client"].get("cognitive_distortion", "")

        #CBT 전략 먼저 생성
        self.cbt_strategy_agent = CBTStrategyAgent(example, self.cognitive_distortion)
        self.cbt_technique, self.cbt_strategy = self.cbt_strategy_agent.generate()


        self.counselor_agent = CounselorAgent(
            client_info=example["AI_counselor"]["Response"]["client_information"],
            reason=example["AI_counselor"]["Response"]["reason_counseling"],
            cbt_technique=self.cbt_technique,
            cbt_strategy=self.cbt_strategy,
            persona_type=persona_type,
            emotion=self.emotion_state,
            distortion=self.cognitive_distortion
        )
        self.evaluator_agent = EvaluatorAgent()

        self._init_history()

    def _init_history(self):
        init_counselor = self.example["AI_counselor"]["CBT"]["init_history_counselor"]
        init_client = self.example["AI_counselor"]["CBT"]["init_history_client"]
        self.history = [
            {"role": "counselor", "message": init_counselor},
            {"role": "client", "message": init_client},
        ]

    def _add(self, role, message):
        self.history.append({"role": role, "message": message})

    def run(self):
        for _ in range(self.max_turns):
            counselor_msg = self.counselor_agent.generate_response(self.history)
            self._add("counselor", counselor_msg)

            client_msg = self.client_agent.generate(
                self.example["AI_client"]["intake_form"],
                self.example["AI_client"]["attitude_instruction"],
                "\n".join(f"{m['role'].capitalize()}: {m['message']}" for m in self.history)
            )
            self._add("client", client_msg)

            if "[/END]" in client_msg:
                self.history[-1]["message"] = client_msg.replace("[/END]", "")
                break

        return {
            "persona": self.persona_type,
            "cbt_strategy": self.counselor_agent.cbt_strategy,
            "cbt_technique": self.counselor_agent.cbt_technique,
            "cognitive_distortion": self.cognitive_distortion,
            "history": self.history,
            "evaluation": self.evaluator_agent.evaluate(self.history),
        }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_file", required=True)
    parser.add_argument("--output_file", required=True)
    parser.add_argument("--persona_type", required=True)
    args = parser.parse_args()

    with open(args.input_file, "r", encoding="utf-8") as f:
        example = json.load(f)

    sim = TherapySimulation(example, args.persona_type)
    result = sim.run()

    Path(args.output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)