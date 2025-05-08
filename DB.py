from pymongo import MongoClient
from datetime import datetime
import os
from config import load_config


# YAML 설정 파일에서 MongoDB URI를 가져오기
config = load_config()
mongo_uri = config["mongodb"]["uri"]
# MongoDB 클라이언트 연결
client = MongoClient(mongo_uri)
db = client['mindAI']  # 'mindAI' 데이터베이스 사용
chat_collection = db['chat_logs']  # 'chat_logs' 컬렉션 사용
user_collection = db['users']  # 사용자 정보 저장을 위한 컬렉션
analysis_collection = db['analysis_reports']  # 분석 리포트 저장용

# 채팅 로그 저장 함수
def save_chat_log(userId, chatId, user_message, bot_response):
    """
    사용자의 메시지와 챗봇의 응답을 채팅 로그에 저장
    """ 
    chat_collection.update_one(
        {"chatId": chatId, "userId": userId},
        {
            "$push": {
                "messages": {
                    "$each": [user_message, bot_response]
                }
            }
        },
        upsert=True
    )
    print(f"Chat log for chatId {chatId} has been saved successfully!")

# 채팅 로그 불러오기 함수
def get_chat_log(chatId):
    """
    특정 chat_id에 대한 채팅 로그를 불러옴
    """
    chat_log = chat_collection.find_one({"chatId": chatId})
    if chat_log:
        return chat_log['messages']  # 메시지 목록 반환
    else:
        return None
"""
사용자 정보는 실제 서비스 시에는 백엔드 서버로부터 전달받을 예정, 현재는 임시로저장하는거
"""

# 사용자 정보 저장 함수
def save_user_info(userId, name, age, gender):
    """
    사용자 정보를 DB에 저장
    """
    userInfo = {
        "userId": userId,
        "name": name,
        "age": age,
        "gender": gender
    }
    user_collection.update_one(
        {"userId": userId},  # user_id가 존재하는지 확인
        {"$set": userInfo},    # 사용자 정보 업데이트
        upsert=True  # user_id가 없다면 새로 추가
    )
    print(f"User info for {userId} has been saved successfully!")

# 사용자 정보 불러오기 함수
def get_user_info(userId):
    """
    특정 user_id에 대한 사용자 정보를 불러옴
    """
    userInfo = user_collection.find_one({"userId": userId})
    if userInfo:
        return userInfo  # 사용자 정보 반환
    else:
        return None
    
   
def save_analysis_report(userId, chatId, topic, emotion, distortion, mainMission, subMission, timestamp):
    """
    분석 리포트를 reports 배열에 누적 저장
    """
    doc = analysis_collection.find_one({"userId": userId, "chatId": chatId})
    existing_reports = doc["reports"] if doc and "reports" in doc else []
    reportId = len(existing_reports) + 1

    new_report = {
        "reportId": reportId,
        "topic": topic,
        "emotion": emotion,
        "distortion": distortion,
        "mainMission": mainMission,
        "subMission": subMission,
        "timestamp": timestamp
    }

    analysis_collection.update_one(
        {"userId": userId, "chatId": chatId},
        {"$push": {"reports": new_report}},
        upsert=True
    )
    print(f"analysis report for chatId {chatId} has been appended successfully!")



# 분석 리포트 불러오기 함수
def get_analysis_report(userId, chatId):
    """
    특정 userId와 chatId에 해당하는 분석 리포트 중 reportId가 가장 큰 것(최신)을 불러옴
    """
    doc = analysis_collection.find_one({"userId": userId, "chatId": chatId})
    if doc and "reports" in doc and isinstance(doc["reports"], list) and doc["reports"]:
        latest_report = max(doc["reports"], key=lambda r: r.get("reportId", 0))
        return latest_report
    return None