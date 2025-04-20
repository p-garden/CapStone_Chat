"""1
 ssh -i "PG.pem" ubuntu@13.125.242.109
cd ~/CapStone 
source venv/bin/activate
uvicorn app:app --host 0.0.0.0 --port 8000
http://0.0.0.0:8000/docs
http://13.125.242.109:8000/docs
{
    "user_id": "userPG",
    "chat_id": "PG123",
    "persona_type": "persona_8살_민지원"

    "user_id": "new1234",
    "chat_id": "new1234",
    "persona_type": "persona_8살_민지원",
    "name": "새로운",
    "age": 1,
    "gender": "남"
}
}

"""
import json
import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from chat import run_chat_with_args
from DB import save_user_info, get_user_info, get_chat_log
from typing import Optional
from agents.counselor_agent import CounselorAgent


app = FastAPI()

class ChatRequest(BaseModel):
    user_id: str
    chat_id: str
    persona_type: str
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None

@app.post("/start_chat")
async def start_chat_endpoint(request: ChatRequest):
    user_info = get_user_info(request.user_id)

    if user_info:
        # 기존 사용자라면 DB에 저장된 정보를 활용
        name = user_info.get("name")
        age = user_info.get("age")
        gender = user_info.get("gender")
    else:
        # 새로운 사용자라면 이름, 나이, 성별이 꼭 포함되어야 함
        if request.name is None or request.age is None or request.gender is None:
            raise HTTPException(status_code=400, detail="New user must provide name, age, and gender.")
        name = request.name
        age = request.age
        gender = request.gender
        save_user_info(request.user_id, name, age, gender)

    chat_log = get_chat_log(request.chat_id)
    history = []

    if chat_log and isinstance(chat_log, list) and isinstance(chat_log[0], dict) and 'role' in chat_log[0]:
        history = chat_log
    else:
        counselor_agent = CounselorAgent(
            client_info=f"{name}, {age}세, {gender}",
            persona_type=request.persona_type
        )
        welcome_input = "상담을 시작하는 간단한 인사말과 상담사의 페르소나를 소개해 주세요. 이름과 나이를 밝혀주세요"
        result = counselor_agent.generate_response([], welcome_input)
        welcome_message = result.get("reply", "상담사가 인사말을 준비 중이에요.")
        history = [{"role": "counselor", "message": welcome_message}]

    output_file = f"results/{uuid.uuid4().hex}.json"
    run_chat_with_args(output_file, request.persona_type, request.chat_id, request.user_id)

    with open(output_file, "r", encoding="utf-8") as f:
        result = json.load(f)

    return {
        "bot_response": result["history"][-1]["message"],
        "history": history
    }

@app.get("/get_chat_log/{chat_id}")
async def get_chat_log_endpoint(chat_id: str):
    chat_log = get_chat_log(chat_id)

    if not chat_log:
        # If no chat log found, return an appropriate error message
        raise HTTPException(status_code=404, detail="No chat log found for this chat_id.")
    
    # If chat log is found and is a list with message
    if isinstance(chat_log, list) and len(chat_log) > 0 and 'role' in chat_log[0]:
        return {"chat_log": chat_log}  # ✅ 전체 로그 리스트 반환
    else:
        raise HTTPException(status_code=404, detail="Chat log found, but no message exist.")
@app.get("/docs")
def get_docs():
    return {"message": "Swagger UI will be here!"}