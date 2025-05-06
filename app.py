"""1
ssh -i "PG.pem" ubuntu@43.200.169.229
cd ~/CapStone 
source venv/bin/activate
docker로 넘어가기
uvicorn app:app --host 0.0.0.0 --port 8000
http://0.0.0.0:8000/docs
http://43.200.169.229:8000
{
  "userId": 2,
  "chatId": 2,
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

  git push team-repo main:PG
  git checkout PG
  git pull team-repo PG --rebase
  git push team-repo PG
"""
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from chat import generate_response_from_input
from DB import save_user_info, get_user_info, get_chat_log
from starter.generate_greet import generate_greet, load_prompt
from typing import Optional
from agents.counselor_agent import CounselorAgent
from datetime import datetime
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# static 폴더 서빙 추가
app.mount("/static", StaticFiles(directory="static"), name="static")


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

    botResponse = generate_response_from_input(
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
        "botResponse": botResponse,
        "timestamp" : datetime.now().isoformat()
    }

@app.get("/get_chat_log/{chatId}")
async def get_chat_log_endpoint(chatId: int):
    chat_log = get_chat_log(int(chatId))

    if not chat_log:
        # If no chat log found, return an appropriate error message
        raise HTTPException(status_code=404, detail="No chat log found for this chat_id.")
    
    # If chat log is found and is a list with message
    if isinstance(chat_log, list) and len(chat_log) > 0 and 'role' in chat_log[0]:
        return {"chat_log": chat_log}  # ✅ 전체 로그 리스트 반환
    else:
        raise HTTPException(status_code=404, detail="Chat log found, but no message exist.")
    
# 먼저 말걸기 API
class GreetRequest(BaseModel):
    userId: int
    chatId: int
    name: str
    age: int
    gender: str
    topic: str
    emotion: str
    distortion: str
    mainMission: str
    subMission: str
    calendar: str

@app.post("/generate_greet")
async def generate_greet_endpoint(request: GreetRequest):

    chat_log = get_chat_log(request.chatId)
    recent_persona = None
    for message in reversed(chat_log):
        if message.get("role") == "counselor" and "persona" in message:
            recent_persona = message["persona"]
            break

    if not recent_persona:
        raise ValueError("최근 페르소나 정보를 찾을 수 없습니다.")

    persona_path = f"prompts/{recent_persona}.txt"
    persona = load_prompt(persona_path)
    prompt_path = "starter/first.txt"
    prompt_template = load_prompt(prompt_path)

    filled_prompt = prompt_template.format(
        persona=persona,
        topic = request.topic,
        emotion=request.emotion,
        distortion=request.distortion,
        mainMission=request.mainMission,
        subMission=request.subMission,
        calendar=request.calendar
    )

    reply = generate_greet(filled_prompt, request.userId, request.chatId)
    return {
        "userId": request.userId,
        "chatId": request.chatId,
        "greeting": reply,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/docs")
def get_docs():
    return {"message": "Swagger UI will be here!"}

from fastapi import UploadFile, File
from openai import OpenAI
from utils.tts_clova import clova_tts
from datetime import datetime

@app.post("/voice_chat")
async def voice_chat(
    userId: int,
    chatId: int,
    persona: str,
    name: str,
    age: int,
    gender: str,
    file: UploadFile = File(...)
):
    # 1. 음성 파일 저장
    import tempfile, shutil
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        shutil.copyfileobj(file.file, tmp)
        audio_path = tmp.name

    # 2. Whisper로 텍스트 변환 (OpenAI API 사용)

    from utils.tts_clova import get_openai_client

    client = get_openai_client()

    with open(audio_path, "rb") as audio_file:
        input_text = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text"
        )

    # 3. GPT 응답 생성 (공통 로직 재사용)
    from chat import generate_response_from_input
    response_data = generate_response_from_input(
        persona=persona,
        chatId=chatId,
        userId=userId,
        message=input_text,
        name=name,
        age=age,
        gender=gender,
    )
    if isinstance(response_data, dict):
        bot_response = response_data.get("reply", "")
        emotion = response_data.get("analysis", {}).get("감정", "없음")
    else:
        bot_response = response_data
        emotion = "없음"

    # 4. Clova TTS
    from config import AUDIO_DIR
    mp3_filename = f"voice_response_{userId}_{chatId}.mp3"
    mp3_path = AUDIO_DIR / mp3_filename
    clova_tts(bot_response, persona_type=persona, emotion=emotion, output_path=str(mp3_path))

    return {
        "userId": userId,
        "chatId": chatId,
        "message": input_text,
        "botResponse": bot_response,
        "audioResponse": f"http://127.0.0.1:8000/static/{mp3_filename}",
        "timestamp": datetime.now().isoformat()
    }
