from pymongo import MongoClient
from datetime import datetime

# MongoDB 연결 설정
client = MongoClient("mongodb+srv://j2982477:EZ6t7LEsGEYmCiJK@mindai.zgcb4ae.mongodb.net/?retryWrites=true&w=majority&appName=mindAI")
db = client['mindAI']  # 'mindAI' 데이터베이스 사용
chat_collection = db['chat_logs']  # 'chat_logs' 컬렉션 사용
user_collection = db['users']       # 사용자 정보 저장을 위한 컬렉션

# 채팅 로그 저장 함수
def save_chat_log(user_id, chat_id, user_message, bot_response):
    """
    사용자의 메시지와 챗봇의 응답을 채팅 로그에 저장합니다.
    동일한 user_id와 chat_id를 가진 세션이 있으면 해당 세션에 메시지를 추가하고,
    없으면 새 세션을 생성합니다.
    """ 
    # 현재 시간
    timestamp = datetime.now().isoformat()

    # 새로 추가할 메시지 목록
    messages_to_push = [
        {
            "role": "user",
            "message": user_message,
            "timestamp": timestamp
        },
        {
            "role": "bot",
            "message": bot_response,
            "timestamp": timestamp
        }
    ]

    # 채팅 로그 저장 (user_id와 chat_id를 함께 필터로 사용)
    chat_collection.update_one(
        {"chat_id": chat_id, "user_id": user_id},  # user_id와 chat_id 모두 사용
        {
            "$push": {"messages": {"$each": messages_to_push}},
            "$set": {"updated_at": timestamp}
        },
        upsert=True
    )

    print(f"Chat log for chat_id {chat_id} has been saved successfully!")

# 채팅 로그 불러오기 함수
def get_chat_log(chat_id, user_id):
    """
    특정 chat_id와 user_id에 대한 채팅 로그를 불러옵니다.
    """
    chat_log = chat_collection.find_one({"chat_id": chat_id, "user_id": user_id})
    if chat_log and "messages" in chat_log:
        return chat_log['messages']  # 메시지 목록 반환
    else:
        return None

"""
사용자 정보는 실제 서비스 시에는 백엔드 서버로부터 전달받을 예정입니다.
현재는 임시로 저장하는 방식입니다.
"""

# 사용자 정보 저장 함수
def save_user_info(user_id, name, age, gender):
    """
    사용자 정보를 DB에 저장합니다.
    """
    user_info = {
        "user_id": user_id,
        "name": name,
        "age": age,
        "gender": gender
    }
    user_collection.update_one(
        {"user_id": user_id},
        {"$set": user_info},
        upsert=True
    )
    print(f"User info for {user_id} has been saved successfully!")

# 사용자 정보 불러오기 함수
def get_user_info(user_id):
    """
    특정 user_id에 대한 사용자 정보를 불러옵니다.
    """
    user_info = user_collection.find_one({"user_id": user_id})
    if user_info:
        return user_info
    else:
        return None
