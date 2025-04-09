"""
 ssh -i "PG.pem" ubuntu@54.180.95.215
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

app = FastAPI()

class ChatRequest(BaseModel):
    user_id: str
    chat_id: str
    first_message: str
    persona_type: str

@app.post("/start_chat")
async def start_chat_endpoint(request: ChatRequest):
    user_info = get_user_info(request.user_id)

    if not user_info:
        # 새로운 사용자일 경우, 사용자 정보를 입력받음
        user_info = {
            "name": input("이름을 입력해주세요: "),
            "age": int(input("나이를 입력해주세요: ")),
            "gender": input("성별을 입력해주세요: ")
        }
        save_user_info(request.user_id, user_info["name"], user_info["age"], user_info["gender"])

    # 채팅 시작
    output_file = f"outputs/{uuid.uuid4().hex}.json"
    run_chat_with_args(output_file, request.persona_type, request.chat_id, request.user_id)

    with open(output_file, "r", encoding="utf-8") as f:
        result = json.load(f)

    return {"user_message": request.first_message, "bot_response": result["history"][-1]["message"]}

@app.get("/get_chat_log/{chat_id}")
async def get_chat_log_endpoint(chat_id: str):
    chat_log = get_chat_log(chat_id)
    if chat_log:
        return {"chat_log": chat_log['messages']}
    else:
        return {"message": "No chat log found for this chat_id."}