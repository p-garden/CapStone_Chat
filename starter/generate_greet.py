#python3 starter/generate_greet.py --persona 26살_한여름
import openai
import sys
import os
import argparse
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import get_config, set_openai_api_key
set_openai_api_key()

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
import re

def load_prompt(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def generate_greet(prompt: str, model_name="gpt-4o-mini", temperature=0.7) -> str:
    llm = ChatOpenAI(model=model_name, temperature=temperature)
    
    # LLM 호출
    response = llm.invoke(prompt)
    content = response.content if isinstance(response, AIMessage) else str(response)

    # 응답 추출 (선택 사항: 포맷이 존재하면 추출)
    reply_match = re.search(r"상담사\s*응답[:：]?\s*(.*?)(?=\n|$)", content, re.DOTALL)
    reply = reply_match.group(1).strip() if reply_match else content.strip()

    return reply

if __name__ == "__main__":
    prompt_path = "starter/first.txt"
    prompt = load_prompt(prompt_path)
    persona_dir = "prompts"
    parser = argparse.ArgumentParser()
    parser.add_argument("--persona", type=str, required=True, help="페르소나 이름 (예: 8살_민지원)")
    args = parser.parse_args()
    persona_prompt_path = os.path.join(persona_dir, f"{args.persona}.txt")
    persona_prompt = load_prompt(persona_prompt_path)

    # 임시 사용자 정보
    emotion = "- 불안: 20%\n- 지침: 60%\n- 기쁨: 20%"
    distortion = "- 과잉 일반화\n- 감정적 추론"
    main_mission = "저녁 먹고 10분 명상하기"
    sub_mission = "마음에 들었던 순간 1가지 기록하기"
    calendar_info = "- 오후 7시 영화 예매\n- 오후 9시 친구와 영상통화"

    # prompt 채우기
    filled_prompt = prompt.format(
        persona_prompt=persona_prompt,
        emotion=emotion,
        distortion=distortion,
        main_mission=main_mission,
        sub_mission=sub_mission,
        calendar_info=calendar_info
    )
    print("\n📤 입력 프롬프트:\n", filled_prompt)
    response = generate_greet(filled_prompt)
    print("\n🤖 GPT 응답:\n", response)
