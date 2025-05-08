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

def generate_greet(prompt: str, userId: int, chatId: int, name: str, age: int, gender: str, model_name="gpt-4o-mini", temperature=0.7) -> dict:
    from DB import get_analysis_report
    llm = ChatOpenAI(model=model_name, temperature=temperature)

    # 분석 리포트 로드
    report = get_analysis_report(userId, chatId)
    if not report:
        raise ValueError("분석 리포트를 찾을 수 없습니다.")

    # 분석 정보 추출
    topic = report.get("topic", "")
    emotion_data = report.get("emotion", {})
    emotion = "\n".join([f"- {k}: {v}%" for k, v in emotion_data.items()])
    distortion_list = report.get("distortion", [])
    distortion = "\n".join([f"- {item['name']}" for item in distortion_list])
    mainMission = report.get("mainMission", {}).get("title", "")
    subMission_list = report.get("subMission", [])
    subMission = "\n".join([f"- {item['title']}" for item in subMission_list])

    # 이름, 나이, 성별 포함
    client_info = f"이름: {name}, 나이: {age}세, 성별: {gender}"

    # 프롬프트 채우기
    filled_prompt = prompt.format(
        client_info=client_info,
        topic=topic,
        emotion=emotion,
        distortion=distortion,
        mainMission=mainMission,
        subMission=subMission
    )

    # LLM 호출
    response = llm.invoke(filled_prompt)
    content = response.content if isinstance(response, AIMessage) else str(response)

    # 응답 추출
    reply_match = re.search(r"상담사\s*응답[:：]?\s*(.*?)(?=\n|$)", content, re.DOTALL)
    reply = reply_match.group(1).strip() if reply_match else content.strip()

    return {
        "reply": reply
    }

if __name__ == "__main__":
    prompt_path = "starter/first.txt"
    prompt = load_prompt(prompt_path)
    persona_dir = "prompts"

    parser = argparse.ArgumentParser()
    parser.add_argument("--userId", type=int, required=True, help="사용자 ID")
    parser.add_argument("--chatId", type=int, required=True, help="채팅방 ID")
    args = parser.parse_args()

    chat_log = get_chat_log(args.chatId)
    recent_persona = None

    report = get_analysis_report(args.userId, args.chatId)
    if not report:
        raise ValueError("분석 리포트를 찾을 수 없습니다.")

    topic = report.get("topic", "")
    emotion_data = report.get("emotion", {})
    emotion = "\n".join([f"- {k}: {v}%" for k, v in emotion_data.items()])
    distortion_list = report.get("distortion", [])
    distortion = "\n".join([f"- {item['name']}" for item in distortion_list])
    mainMission = report.get("mainMission", {}).get("title", "")
    subMission_list = report.get("subMission", [])
    subMission = "\n".join([f"- {item['title']}" for item in subMission_list])

    for message in reversed(chat_log):
        if message.get("role") == "counselor" and "persona" in message:
            recent_persona = message["persona"]
            break

    if not recent_persona:
        raise ValueError("최근 페르소나 정보를 찾을 수 없습니다.")

    persona_prompt_path = os.path.join(persona_dir, f"{recent_persona}.txt")
    persona = load_prompt(persona_prompt_path)

    # prompt 채우기
    filled_prompt = prompt.format(
        persona=persona,
        topic=topic,
        emotion=emotion,
        distortion=distortion,
        mainMission=mainMission,
        subMission=subMission 
        )

    response = generate_greet(filled_prompt, args.userId, args.chatId)

    # 챗봇 응답만 저장
    bot_message = {
        "role": "counselor",
        "message": response["reply"],
        "timestamp": datetime.now().isoformat(),
        "persona": recent_persona}

    user_message = {
        "role": "client",
        "message": "",
        "timestamp": datetime.now().isoformat(),
        "analysis": ""
    }

    save_chat_log(args.userId, args.chatId, user_message=user_message, bot_response=bot_message)