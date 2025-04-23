"""
실행 코드
python3 chat.py --output_file results/result1.json --persona_type persona_5살_민지원 --chat_id PG123 --user_id userPG
"""

import json
from pathlib import Path
from agents.counselor_agent import CounselorAgent
from agents.evaluator_agent import EvaluatorAgent
from config import load_config
from agents.subllm_agent import SubLLMAgent
from config import get_config, set_openai_api_key
from cbt.cbt_mappings import emotion_strategies, cognitive_distortion_strategies
from DB import get_chat_log, save_chat_log, save_user_info, get_user_info  # DB.py에서 import
from fastapi import FastAPI, HTTPException
import requests
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# .env 파일을 로드
load_dotenv()

# 환경 변수에서 MongoDB URI를 가져오기
mongo_uri = os.getenv("MONGO_URI")

# MongoDB 클라이언트 연결
client = MongoClient(mongo_uri)
db = client['mindAI']  # 'mindAI' 데이터베이스 사용
chat_collection = db['chat_logs']  # 'chat_logs' 컬렉션 사용
user_collection = db['users']  # 사용자 정보 저장을 위한 컬렉션
# API 키 설정
set_openai_api_key()

# TherapySimulation 클래스에서 사용자 정보 확인
class TherapySimulation:
    def __init__(self, persona_type: str, chat_id: str, user_id: str, max_turns: int = 20):
        self.persona_type = persona_type
        self.chat_id = chat_id
        self.user_id = user_id
        self.max_turns = max_turns
        self.history = []

        # Check if the user exists in the database
        user_info = get_user_info(self.user_id)
        if user_info:
            # If the user exists, load their information
            self.name = user_info["name"]
            self.age = user_info["age"]
            self.gender = user_info["gender"]
        else:
            # If the user doesn't exist, receive the information via API
            # Call the /start_chat API to collect user info
            user_info = self.start_chat_api()
            self.name = user_info["name"]
            self.age = user_info["age"]
            self.gender = user_info["gender"]
            save_user_info(self.user_id, self.name, self.age, self.gender)

        # Load chat log if it exists
        chat_log = get_chat_log(self.chat_id)
        if chat_log and isinstance(chat_log, list) and isinstance(chat_log[0], dict) and 'role' in chat_log[0]:
            self.history = chat_log
            if not hasattr(self, 'counselor_agent'):
                self.counselor_agent = CounselorAgent(
                    client_info=f"{self.name}, {self.age}세, {self.gender}",
                    persona_type=self.persona_type
                )
        else:
            self.counselor_agent = CounselorAgent(
                client_info=f"{self.name}, {self.age}세, {self.gender}",
                persona_type=self.persona_type
            )
            welcome_input = "상담을 시작하는 간단한 인사말과 상담사의 페르소나를 소개해 주세요. 이름과 나이를 밝혀주세요"
            result = self.counselor_agent.generate_response([], welcome_input)
            welcome_message = result.get("reply", "상담사가 인사말을 준비 중이에요.")
            self.history = [{"role": "counselor", "message": welcome_message}]

        # SubLLM analysis
        self.subllm_agent = SubLLMAgent()
        self.evaluator_agent = EvaluatorAgent()

    def run(self):
        for turn in range(self.max_turns):
            print(f"--- Turn {turn + 1} ---")

            # 직접 내담자 역할을 할 수 있는 부분 (현재는 사용자가 직접 입력)
            client_msg = input(f"{self.name}: ").strip()
            if "[/END]" in client_msg or client_msg.strip().lower() == "exit":
                self.history[-1]["message"] = client_msg.replace("[/END]", "exit")
                break
           
        # 사용자 메시지 + 타임스탬프 포함
            self.history.append({
                "role": "client",
                "message": client_msg,
                "timestamp": datetime.now().isoformat()
            })

            # 상담사 응답 생성
            result = self.counselor_agent.generate_response(self.history, client_msg)
            reply = result["reply"]
            print("Counselor:", reply)


            # 상담사 응답도 타임스탬프 포함
            self.history.append({
                "role": "counselor",
                "message": reply,
                "timestamp": datetime.now().isoformat()
            })

            # 저장
            save_chat_log(self.user_id, self.chat_id, client_msg, reply)
        evaluation = self.evaluator_agent.evaluate_all(self.history)
        summary = self.evaluator_agent.generate_feedback_summary(self.history, evaluation)

        # 7. 결과 반환
        return {
            "persona": self.persona_type,
            "history": self.history,
            "evaluation": evaluation
        }

    def start_chat_api(self):
        # Call the /start_chat API to collect user information
        api_url = "http://13.125.242.109:8000/start_chat"  # 실제 서버 IP를 넣어야 해
        data = {
            "user_id": self.user_id,
            "chat_id": self.chat_id,
            "persona_type": self.persona_type,
            "name": None,  # These will be filled in the API
            "age": None,
            "gender": None
        }

        response = requests.post(api_url, json=data)
        
        if response.status_code == 200:
            user_info = response.json()
            return user_info  # The response contains user data
        else:
            raise HTTPException(status_code=500, detail="Error retrieving user information.")

def run_chat_with_args(output_file: str | None, persona_type: str, chat_id: str, user_id: str):
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"results/result_{timestamp}.json"

    sim = TherapySimulation(
        persona_type=persona_type,
        chat_id=chat_id,
        user_id=user_id, 
    )    
    result = sim.run()

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_file", default=None)
    parser.add_argument("--persona_type", required=True)
    parser.add_argument("--chat_id", required=True)  # chat_id 추가
    parser.add_argument("--user_id", required=True)  # 사용자 이름
    args = parser.parse_args()

    run_chat_with_args(args.output_file, args.persona_type, args.chat_id, args.user_id)
