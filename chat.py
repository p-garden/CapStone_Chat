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
from datetime import datetime, timedelta, timezone
import os
from agents.subllm_agent import classify_topic # 새로 만든 함수가 있는 파일에서 import

# API 키 설정
set_openai_api_key()
kst = timezone(timedelta(hours=9))

# TherapySimulation 클래스에서 사용자 정보 확인
class TherapySimulation:
    def __init__(self, persona: str, chatId: int, userId: int, name: str, age: int, gender: str):
        self.persona = persona
        self.chatId = chatId
        self.userId = userId
        self.name = name
        self.age = age
        self.gender = gender
        self.history = []

        # Load chat log if it exists
        chat_log = get_chat_log(self.chatId)
        self.counselor_agent = CounselorAgent(
            client_info = f"이름: {self.name}, 나이: {self.age}세, 성별: {self.gender}",
            persona=self.persona
        )

        if chat_log and isinstance(chat_log, list) and isinstance(chat_log[0], dict) and 'role' in chat_log[0]:
            self.history = chat_log
        else:
            self.history = []

        # SubLLM analysis
        self.subllm_agent = SubLLMAgent()
        self.evaluator_agent = EvaluatorAgent()

    def run_single_turn(self, message: str):
        timestamp = datetime.now(kst).isoformat()
        result = self.counselor_agent.generate_response(self.history, message)
        reply = result["reply"]
        analysis = result.get("analysis", {})

        topic_result = classify_topic(message)

        user_entry = {
            "role": "client",
            "message": message,
            "timestamp": timestamp,
            "analysis": analysis,
            "topic": topic_result
        }

        bot_entry = {
            "role": "counselor",
            "message": reply,
            "timestamp":datetime.now(kst).isoformat(),
            "persona": self.persona  # 현재 사용된 페르소나 저장
        }

        self.history.extend([user_entry, bot_entry])
        save_chat_log(self.userId, self.chatId, user_entry, bot_entry)

        return reply

def generate_response_from_input(persona: str, chatId: int, userId: int, name: str, age: int, 
                                 gender: str, message: str):
    sim = TherapySimulation(
        persona=persona,
        chatId=chatId,
        userId=userId,
        name=name,
        age=age,
        gender=gender
    )
    return sim.run_single_turn(message)