from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from chat import generate_response_from_input
from DB import save_user_info, get_user_info, get_chat_log, save_analysis_report
from starter.generate_greet import generate_greet, load_prompt
from typing import Optional
from agents.counselor_agent import CounselorAgent
from datetime import datetime
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from report import generate_analysis_report  
from datetime import datetime, timedelta, timezone

kst = timezone(timedelta(hours=9))

app = FastAPI()

# 허용할 origin 목록
origins = [
    "http://43.200.169.229:8000",  # 프론트엔드 주소 (예시)
    "https://todak2-ai.site"
    "https://test-sso.online",  # 실제 서버 도메인
]

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # 허용할 Origin
    allow_credentials=True,
    allow_methods=["*"],              # 허용할 HTTP 메서드 (GET, POST 등)
    allow_headers=["*"],              # 허용할 헤더
)
# static 폴더 서빙 추가
app.mount("/static", StaticFiles(directory="static"), name="static")
kst = timezone(timedelta(hours=9))


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
        "botResponse": botResponse["reply"],
        "timestamp": datetime.now(kst).isoformat()
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
    
from starter.generate_greet import run_generate_greet
@app.post("/generate_greet")
async def generate_greet_endpoint(request: GreetRequest):
    return run_generate_greet(request.userId, request.chatId, request.name, request.age, request.gender)

@app.get("/docs")
def get_docs():
    return {"message": "Swagger UI will be here!"}

from openai import OpenAI
from utils.tts_clova import clova_tts

class VoiceChatRequest(BaseModel):
    userId: int
    chatId: int
    persona: str
    message: str
    name: str
    age: int
    gender: str

@app.post("/voice_chat")
async def voice_chat(request: VoiceChatRequest):

    # 3. GPT 응답 생성 (공통 로직 재사용)
    from chat import generate_response_from_input
    response_data = generate_response_from_input(
        persona=request.persona,
        chatId=request.chatId,
        userId=request.userId,
        message=request.message,
        name=request.name,
        age=request.age,
        gender=request.gender,
    )
    if isinstance(response_data, dict):
        bot_response = response_data.get("reply", "")
        emotion = response_data.get("emotion", "없음")
    else:
        bot_response = response_data
        emotion = "없음"

    # 4. Clova TTS
    from config import AUDIO_DIR
    mp3_filename = f"voice_response_{request.userId}_{request.chatId}.mp3"
    mp3_path = AUDIO_DIR / mp3_filename
    clova_tts(bot_response, persona_type=request.persona, emotion=emotion, output_path=str(mp3_path))

    return {
        "userId": request.userId,
        "chatId": request.chatId,
        "botResponse": bot_response,
        "audioResponse": f"https://todak2-ai.site/static/{mp3_filename}",
        "timestamp": datetime.now(kst).isoformat()
    }

from report import generate_analysis_report
class ReportRequest(BaseModel):
    userId: int
    chatId: int

@app.post("/generate_report")
async def generate_report_post(request: ReportRequest):
    try:
        print("🚀 Report 요청:", request.chatId, request.userId)

        report = generate_analysis_report(chatId=request.chatId, userId=request.userId)

        save_analysis_report(
            chatId=request.chatId,
            userId=request.userId,
            topic=report["missionTopic"],
            emotion=report["missionEmotion"],
            distortion=report["missionDistortion"],
            missions=report["missions"],
            timestamp=datetime.now(kst).isoformat()
        )
        return {
            "userId": request.userId,
            "chatId": request.chatId,
            "timestamp": datetime.now(kst).isoformat(),
            "report": report
        }

    except Exception as e:
        print("❗ 예외 발생:", str(e))  # ✅ 여기에 로그 출력
        raise HTTPException(status_code=500, detail=str(e))