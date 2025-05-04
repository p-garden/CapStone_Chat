#python3 starter/generate_greet.py --persona 26살_한여름 --userId 1 --chatId 1
import openai
import sys
import os
import argparse

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import get_config, set_openai_api_key
from DB import save_chat_log, get_chat_log
from datetime import datetime
set_openai_api_key()

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
import re

def load_prompt(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def generate_greet(prompt: str, userId: str, chatId: str, model_name="gpt-4o-mini", temperature=0.7) -> dict:
    llm = ChatOpenAI(model=model_name, temperature=temperature)
    
    # LLM 호출
    response = llm.invoke(prompt)
    content = response.content if isinstance(response, AIMessage) else str(response)

    # 응답 추출 (선택 사항: 포맷이 존재하면 추출)
    reply_match = re.search(r"상담사\s*응답[:：]?\s*(.*?)(?=\n|$)", content, re.DOTALL)
    reply = reply_match.group(1).strip() if reply_match else content.strip()

    return {  
        "userId": userId,
        "chatId": chatId,
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
    for message in reversed(chat_log):
        if message.get("role") == "counselor" and "persona" in message:
            recent_persona = message["persona"]
            break

    if not recent_persona:
        raise ValueError("최근 페르소나 정보를 찾을 수 없습니다.")

    persona_prompt_path = os.path.join(persona_dir, f"{recent_persona}.txt")
    persona = load_prompt(persona_prompt_path)

    # 임시 사용자 정보
    topic = "사용자는 행복을 느끼지 못하고, 자신의 존재 가치를 낮게 평가하는 감정을 표현하고 있습니다. 이러한 감정은 불확실한 미래에 대한 두려움과 함께, 자신의 소중함을 잃었다고 느끼는 것에서 비롯된 것으로 보입니다. 이는 자아 존중감의 결여와 직결되며, 자아 이미지가 부정적으로 형성될 가능성을 내포하고 있습니다." 
    emotion = "- 불안: 20%\n- 지침: 60%\n- 기쁨: 20%"
    distortion = "- 과잉 일반화\n- 감정적 추론"
    mainMission = "저녁 먹고 10분 명상하기"
    subMission = "마음에 들었던 순간 1가지 기록하기"
    calendar = "- 오후 7시 영화 예매\n- 오후 9시 친구와 영상통화"

    # prompt 채우기
    filled_prompt = prompt.format(
        persona=persona,
        topic=topic,
        emotion=emotion,
        distortion=distortion,
        mainMission=mainMission,
        subMission=subMission,
        calendar=calendar 
        )
    print("\n📤 입력 프롬프트:\n", filled_prompt)

    response = generate_greet(filled_prompt, args.userId, args.chatId)
    print("\n🤖 GPT 응답:\n", response)

    # 챗봇 응답만 저장
    bot_message = {
        "role": "counselor",
        "message": response["reply"],
        "timestamp": datetime.now().isoformat()
    }
    save_chat_log(args.userId, args.chatId, user_message={}, bot_response=bot_message)
