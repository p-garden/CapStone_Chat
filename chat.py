"""
실행 코드
python3 chat.py --output_file results/result1.json --persona_type persona_20s_friend --chat_id PGchat1 --user_id PG1
"""

import json
from pathlib import Path
from agents.client_agent import ClientAgent
from agents.counselor_agent import CounselorAgent
from agents.evaluator_agent import EvaluatorAgent
from agents.sub_llm import SubLLMAgent
from config import get_config, set_openai_api_key
from cbt.cbt_mappings import emotion_strategies, cognitive_distortion_strategies
from DB import get_chat_log, save_chat_log, save_user_info, get_user_info  # DB.py에서 import
from fastapi import FastAPI, HTTPException
import requests

# API 키 설정
set_openai_api_key()
#from pymongo import MongoClient

# 연결 문자열 사용
#client = MongoClient("mongodb+srv://j2982477:EZ6t7LEsGEYmCiJK"
#"@mindAI.zgcb4ae.mongodb.net/?retryWrites=true&w=majority&appName=mindAI")

# 'mindAI' 데이터베이스에 연결
#db = client['mindAI']
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
        else:
            self.history = [{"role": "client", "message": f"{self.name}님, 안녕하세요. 어떤 문제가 있으신가요?"}]

        # SubLLM analysis
        self.subllm_agent = SubLLMAgent()
        self.evaluator_agent = EvaluatorAgent(criteria_list=["general_1", "general_2", "general_3", "cbt_1", "cbt_2", "cbt_3"])

         # 상담자 에이전트와 평가자 에이전트 초기화
        self.counselor_agent = CounselorAgent(
            client_info=f"{self.name}, {self.age}세, {self.gender}",
            total_strategy="",  # 초기에는 전략을 공란으로 두고 사용자의 메시지에 따라 업데이트
            persona_type=persona_type,
            emotion="",
            distortion=""
        )
    """
        self._init_history()
    def _init_history(self):
        
        채팅을 위한 초기화 작업을 처리하는 메서드입니다.
        현재로서는 간단하게 'client' 역할로 기본 메시지를 설정합니다.
        
        if not self.history:  # history가 비어 있으면 초기 메시지를 추가
            self.history.append({
                "role": "client",
                "message": f"{self.name}님, 안녕하세요. 어떤 문제가 있으신가요?"
            })
    """
    def run(self):
        for turn in range(self.max_turns):
            print(f"--- Turn {turn + 1} ---")

            # 1. 상담자 응답 생성
            counselor_msg = self.counselor_agent.generate_response(self.history)
            self.history.append({"role": "counselor", "message": counselor_msg})
            print("Counselor:", counselor_msg)

            # 직접 내담자 역할을 할 수 있는 부분 (현재는 사용자가 직접 입력)
            client_msg = input(f"{self.name}: ")
            self.history.append({"role": "client", "message": client_msg})
            print(f"{self.name}: {client_msg}")

            # 3. SubLLM 분석 (감정 및 인지 왜곡 탐지)
            analysis_result = self.subllm_agent.analyze(client_msg)
            emotion = analysis_result.get("감정", "")
            distortion = analysis_result.get("인지왜곡", "")
            total_strategy = analysis_result.get("총합_CBT전략", "")  # 여기서 total_strategy 사용
            
            print(f"Emotion detected: {emotion}")
            print(f"Cognitive Distortion detected: {distortion}")
            print(f"CBT Strategy: {total_strategy}")
            print()

            # 4. 최신 분석 결과로 상담자 에이전트 재정의
            self.counselor_agent = CounselorAgent(
                client_info=f"{self.name}, {self.age}세, {self.gender}성",
                total_strategy=total_strategy,
                persona_type=self.persona_type,
                emotion=emotion,
                distortion=distortion
            )
            # 5. 채팅 로그 저장
            save_chat_log(self.user_id, self.chat_id, client_msg, counselor_msg)  # 채팅 로그를 MongoDB에 저장
            # 6. 종료 조건 체크
            if "[/END]" in client_msg or client_msg.strip().lower() == "exit":
                self.history[-1]["message"] = client_msg.replace("[/END]", "exit")
                break

        # 7. 평가 수행
        evaluation_result = self.evaluator_agent.evaluate_all(self.history)

        # 7. 결과 반환
        return {
            "persona": self.persona_type,
            "cbt_strategy": total_strategy,
            "cognitive_distortion": distortion,
            "emotion": emotion,
            "history": self.history,
            "evaluation": evaluation_result
        }

    def start_chat_api(self):
        # Call the /start_chat API to collect user information
        api_url = "http://15.164.216.174:8000/start_chat"  # 실제 서버 IP를 넣어야 해
        data = {
            "user_id": self.user_id,
            "chat_id": self.chat_id,
            "first_message": "Hello",
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

def run_chat_with_args(output_file: str, persona_type: str, chat_id: str, user_id: str):
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
    parser.add_argument("--output_file", required=True)
    parser.add_argument("--persona_type", required=True)
    parser.add_argument("--chat_id", required=True)  # chat_id 추가
    parser.add_argument("--user_id", required=True)  # 사용자 이름

    args = parser.parse_args()

    run_chat_with_args(args.output_file, args.persona_type, args.chat_id, args.user_id)
