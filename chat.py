import json
from pathlib import Path
from agents.counselor_agent import CounselorAgent
from agents.evaluator_agent import EvaluatorAgent
from config import set_openai_api_key
from DB import get_chat_log, save_chat_log, save_user_info, get_user_info
from datetime import datetime
from config import load_config
from pymongo import MongoClient
from fastapi import HTTPException
import requests

# ✅ API 및 DB 초기화
set_openai_api_key()
config = load_config()
client = MongoClient(config["mongo"]["uri"])
db = client['mindAI']

class TherapySimulation:
    def __init__(self, persona_type: str, chat_id: str, user_id: str, max_turns: int = 20):
        self.persona_type = persona_type
        self.chat_id = chat_id
        self.user_id = user_id
        self.max_turns = max_turns
        self.history = []

        # 사용자 정보 로딩 또는 API 요청 제거 (FastAPI에서는 별도로 처리)
        user_info = get_user_info(self.user_id)
        if user_info:
            self.name, self.age, self.gender = user_info["name"], user_info["age"], user_info["gender"]
        else:
            raise ValueError("사용자 정보가 DB에 없습니다. FastAPI에서 미리 저장해야 합니다.")

        # 상담사 에이전트 초기화
        self.counselor_agent = CounselorAgent(
            client_info=f"{self.name}, {self.age}세, {self.gender}",
            persona_type=self.persona_type
        )
        self.evaluator_agent = EvaluatorAgent()

        # 상담 이력 로딩 또는 초기화
        chat_log = get_chat_log(self.chat_id, self.user_id)
        if chat_log:
            self.history = chat_log
        else:
            welcome_input = "상담을 시작하는 간단한 인사말과 상담사의 페르소나를 소개해 주세요. 이름과 나이를 밝혀주세요"
            first_response = self.counselor_agent.generate_response([], welcome_input)
            self.history.append({
                "role": "counselor",
                "message": first_response["reply"],
                "timestamp": datetime.now().isoformat()
            })
            print("Counselor:", first_response["reply"])

    def run(self):
        for turn in range(self.max_turns):
            print(f"--- Turn {turn + 1} ---")
            client_msg = input(f"{self.name}: ").strip()
            if "[/END]" in client_msg:
                break

            self.history.append({
                "role": "client",
                "message": client_msg,
                "timestamp": datetime.now().isoformat()
            })

            result = self.counselor_agent.generate_response(self.history, client_msg)
            reply = result["reply"]
            print("Counselor:", reply)
            self.history.append({
                "role": "counselor",
                "message": reply,
                "timestamp": datetime.now().isoformat()
            })

            save_chat_log(self.user_id, self.chat_id, client_msg, reply)

        evaluation = self.evaluator_agent.evaluate_all(self.history)
        summary = self.evaluator_agent.generate_feedback_summary(self.history, evaluation)

        return {
            "persona": self.persona_type,
            "history": self.history,
            "evaluation": evaluation
        }

def run_chat_with_args(output_file: str | None, persona_type: str, chat_id: str, user_id: str):
    sim = TherapySimulation(
        persona_type=persona_type,
        chat_id=chat_id,
        user_id=user_id, 
    )    
    result = sim.run()

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

def run_chat_fastapi(persona_type: str, chat_id: str, user_id: str) -> dict:
    sim = TherapySimulation(
        persona_type=persona_type,
        chat_id=chat_id,
        user_id=user_id
    )
    welcome_input = "상담을 시작하는 간단한 인사말과 상담사의 페르소나를 소개해 주세요. 이름과 나이를 밝혀주세요"
    result = sim.counselor_agent.generate_response(sim.history, welcome_input)
    reply = result["reply"]
    sim.history.append({
        "role": "counselor",
        "message": reply
    })
    return {
        "persona": persona_type,
        "history": sim.history
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_file", required=True)
    parser.add_argument("--persona_type", required=True)
    parser.add_argument("--chat_id", required=True)
    parser.add_argument("--user_id", required=True)
    args = parser.parse_args()

    sim = TherapySimulation(
        persona_type=args.persona_type,
        chat_id=args.chat_id,
        user_id=args.user_id
    )
    result = sim.run()

    Path(args.output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)