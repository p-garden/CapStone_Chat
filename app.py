"""1
ssh -i "PG.pem" ubuntu@43.200.169.229
cd ~/CapStone 
source venv/bin/activate
docker로 넘어가기
uvicorn app:app --host 0.0.0.0 --port 8000
http://0.0.0.0:8000/docs
http://43.200.169.229:8000
{
  "userId": 1,
  "chatId": 1,
  "persona": "26살_한여름",
  "message": "오늘도 기분이 너무 좋아",
  "name": "박정원",
  "age": 26,
  "gender": "남자"
}
rsync -avz \
  --exclude '__pycache__' \
  --exclude 'results' \
  -e "ssh -i ~/Desktop/code/CapStone/PG.pem" \
  ~/Desktop/code/CapStone/ \
  ubuntu@13.125.242.109:~/CapStone

"""
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from chat import generate_response_from_input
from DB import save_user_info, get_user_info, get_chat_log
from typing import Optional
from agents.counselor_agent import CounselorAgent
from datetime import datetime

app = FastAPI()

class ChatRequest(BaseModel):
    userId: int
    chatId: int
    persona: str
    message: str
    name: str
    age: int 
    gender: str 

@app.post("/start_chat")
async def start_chat_endpoint(request: ChatRequest):
    user_info = get_user_info(request.userId)

    if not user_info:
        save_user_info(request.userId, request.name, request.age, request.gender)

    chat_log = get_chat_log(request.chatId) or []
    history = []

    if chat_log and isinstance(chat_log, list) and isinstance(chat_log[0], dict) and 'role' in chat_log[0]:
        history = chat_log

    bot_response = generate_response_from_input(
        persona=request.persona,
        chatId=request.chatId,
        userId=request.userId,
        message=request.message,
        name=request.name,
        age=request.age,
        gender=request.gender,
    )

    return {
        "userId" : request.userId,
        "chatId" : request.chatId,
        "bot_response": bot_response,
        "timestamp" : datetime.now().isoformat()
    }

@app.get("/get_chat_log/{chat_id}")
async def get_chat_log_endpoint(chatId: int):
    chat_log = get_chat_log(chatId)

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