#python3 starter/generate_greet.py --persona 26살_한여름 --userId 1 --chatId 1
import openai
import sys
import os
import argparse

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import get_config, set_openai_api_key
from DB import save_chat_log, get_chat_log
from DB import get_analysis_report
from datetime import datetime
set_openai_api_key()

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
import re

def load_prompt(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def generate_greet(filled_prompt: str, model_name="gpt-4o-mini", temperature=0.7) -> dict:
    llm = ChatOpenAI(model=model_name, temperature=temperature)

    # LLM 호출
    response = llm.invoke(filled_prompt)
    content = response.content if isinstance(response, AIMessage) else str(response)

    # 응답 추출
    reply_match = re.search(r"상담사\s*응답[:：]?\s*(.*?)(?=\n|$)", content, re.DOTALL)
    reply = reply_match.group(1).strip() if reply_match else content.strip()

    return {
        "reply": reply
    }
     
def run_generate_greet(userId: int, chatId: int, name:str, age:int, gender:str):
    prompt_path = "starter/first.txt"
    persona_dir = "prompts"
    prompt = load_prompt(prompt_path)

    chat_log = get_chat_log(chatId)
    recent_persona = None

    for message in reversed(chat_log):
        if message.get("role") == "counselor" and "persona" in message:
            recent_persona = message["persona"]
            break

    if not recent_persona:
        raise ValueError("최근 페르소나 정보를 찾을 수 없습니다.")

    persona_prompt_path = os.path.join(persona_dir, f"{recent_persona}.txt")
    persona = load_prompt(persona_prompt_path)

    report = get_analysis_report(userId, chatId)
    if not report:
        raise ValueError("분석 리포트를 찾을 수 없습니다.")
    
    clientInfo = f"이름: {name}\n나이: {age}\n성별: {gender}"
    topic = report.get("topic", "")
    emotion_data = report.get("emotion", {})
    emotion = "\n".join([f"- {k}: {v}%" for k, v in emotion_data.items()])
    distortion_list = report.get("distortion", [])
    distortion = "\n".join([f"- {item['name']}" for item in distortion_list])
    mainMission = report.get("mainMission", {}).get("title", "")
    subMission_list = report.get("subMission", [])
    subMission = "\n".join([f"- {item['title']}" for item in subMission_list])

    filled_prompt = prompt.format(
        clientInfo=clientInfo,
        persona=persona,
        topic=topic,
        emotion=emotion,
        distortion=distortion,
        mainMission=mainMission,
        subMission=subMission
    )

    response = generate_greet(filled_prompt)

    bot_message = {
        "role": "counselor",
        "message": response["reply"],
        "timestamp": datetime.now().isoformat(),
        "persona": recent_persona
    }

    user_message = {
        "role": "client",
        "message": "",
        "timestamp": datetime.now().isoformat(),
        "analysis": ""
    }

    save_chat_log(userId, chatId, user_message=user_message, bot_response=bot_message)
    return {
        "userId": userId,
        "chatId": chatId,
        "greet": response["reply"],
        "timestamp": datetime.now().isoformat()
    }