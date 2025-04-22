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
import traceback
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from chat import run_chat_fastapi
from DB import save_user_info, get_user_info, get_chat_log

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
    try:
        print("\u2705 /start_chat 진입")
        print("\ud83d\udcc5 입력 데이터:", request.dict())

        user_info = get_user_info(request.user_id)
        if not user_info:
            if request.name is None or request.age is None or request.gender is None:
                raise HTTPException(status_code=400, detail="New user must provide name, age, and gender.")
            save_user_info(request.user_id, request.name, request.age, request.gender)

        result = run_chat_fastapi(request.persona_type, request.chat_id, request.user_id)

        return {
            "bot_response": result["history"][-1]["message"],
            "history": result["history"]
        }

    except Exception as e:
        print("\u274c 오류 발생!")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_chat_log/{chat_id}")
async def get_chat_log_endpoint(chat_id: str):
    chat_log = get_chat_log(chat_id)

    if not chat_log or not isinstance(chat_log, list) or 'role' not in chat_log[0]:
        raise HTTPException(status_code=404, detail="No valid chat log found.")

    return {"chat_log": chat_log}

@app.get("/docs")
def get_docs():
    return {"message": "Swagger UI will be here!"}
