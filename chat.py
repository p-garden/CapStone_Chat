import json
from pathlib import Path
from agents.counselor_agent import CounselorAgent
from agents.evaluator_agent import EvaluatorAgent
from config import load_config
from agents.subllm_agent import SubLLMAgent
from config import get_config, set_openai_api_key
from DB import get_chat_log, save_chat_log
from fastapi import FastAPI, HTTPException
import requests
from datetime import datetime
import os
# API 키 설정
set_openai_api_key()

# TherapySimulation 클래스에서 사용자 정보 확인
class TherapySimulation:
    def __init__(self, persona_type: str, chat_id: str, user_id: str, user_name: str, user_age: int, user_gender: str):
        self.persona_type = persona_type
        self.chat_id = chat_id
        self.user_id = user_id
        self.name = user_name
        self.age = user_age
        self.gender = user_gender
        self.history = []

        # Load chat log if it exists
        chat_log = get_chat_log(self.chat_id)
        self.counselor_agent = CounselorAgent(
            client_info = f"이름: {self.name}, 나이: {self.age}세, 성별: {self.gender}",
            persona_type=self.persona_type
        )

        if chat_log and isinstance(chat_log, list) and isinstance(chat_log[0], dict) and 'role' in chat_log[0]:
            self.history = chat_log
        else:
            self.history = []

        # SubLLM analysis
        self.subllm_agent = SubLLMAgent()
        self.evaluator_agent = EvaluatorAgent()

    def run_single_turn(self, client_msg: str):
        self.history.append({
            "role": "client",
            "message": client_msg,
            "timestamp": datetime.now().isoformat()
        })

        result = self.counselor_agent.generate_response(self.history, client_msg)
        reply = result["reply"]

        self.history.append({
            "role": "counselor",
            "message": reply,
            "timestamp": datetime.now().isoformat()
        })

        save_chat_log(self.user_id, self.chat_id, client_msg, reply)

        return reply

def generate_response_from_input(persona_type: str, chat_id: str, user_id: str, user_name: str, user_age: int, 
                                 user_gender: str, client_msg: str):
    sim = TherapySimulation(
        persona_type=persona_type,
        chat_id=chat_id,
        user_id=user_id,
        user_name=user_name,
        user_age=user_age,
        user_gender=user_gender
    )
    return sim.run_single_turn(client_msg)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_file", default=None)
    parser.add_argument("--persona_type", required=True)
    parser.add_argument("--chat_id", required=True)  # chat_id 추가
    parser.add_argument("--user_id", required=True)  # 사용자 이름
    args = parser.parse_args()

#    run_chat_with_args(args.output_file, args.persona_type, args.chat_id, args.user_id)