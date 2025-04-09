
"""1
 ssh -i "PG.pem" ubuntu@15.164.26.174
cd ~/CapStone 
source venv/bin/activate
uvicorn app:app --host 0.0.0.0 --port 8000
"""
import json
import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from chat import run_chat_with_args
from DB import save_user_info, get_user_info, get_chat_log, save_chat_log
from typing import Optional

app = FastAPI()

class ChatRequest(BaseModel):
    user_id: str
    chat_id: str
    first_message: str
    persona_type: str
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None

@app.post("/start_chat")
async def start_chat_endpoint(request: ChatRequest):
    # 기존 사용자 정보를 가져옴
    user_info = get_user_info(request.user_id)

    if user_info:
        # 기존 사용자라면 사용자 정보를 사용
        name = user_info.get("name")
        age = user_info.get("age")
        gender = user_info.get("gender")
    else:
        # 새로운 사용자라면 정보 입력 받음
        if request.name is None or request.age is None or request.gender is None:
            raise HTTPException(status_code=400, detail="New user information must be provided.")
        
        # 새 사용자 정보 저장
        save_user_info(request.user_id, request.name, request.age, request.gender)
        name = request.name
        age = request.age
        gender = request.gender

    # 기존 채팅 로그 가져오기
    chat_log = get_chat_log(request.chat_id)

    if chat_log and isinstance(chat_log, list) and isinstance(chat_log[0], dict) and 'role' in chat_log[0]:
        history = chat_log
    else:
        history = [{"role": "client", "message": f"{name}님, 안녕하세요. 어떤 문제가 있으신가요?"}]
    


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
