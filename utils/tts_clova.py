# utils/tts_clova.py
from pathlib import Path
import requests
import yaml
from openai import OpenAI

_client = None

def get_openai_client():
    global _client
    if _client is None:
        _client = OpenAI()
    return _client

CLOVA_API_URL = "https://naveropenapi.apigw.ntruss.com/tts-premium/v1/tts"

PERSONA_SPEAKER_MAP = {
    "8살_민지원": "ndain",
    "26살_한여름": "vyuna",
    "55살_김서연": "vgoeun"
}

def get_emotion_settings(emotion):
    if emotion in ["기쁨", "기대", "신뢰"]:
        return {"emotion": "2", "emotion_strength": "2"}
    elif emotion in ["슬픔", "공포", "분노", "혐오"]:
        return {"emotion": "1", "emotion_strength": "2"}
    elif emotion == "놀람":
        return {"emotion": "0", "emotion_strength": "1"}
    else:
        return {"pitch": "0"}

def load_clova_config():
    config_path = Path(__file__).parent.parent / "conf.d" / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["clova"]

def clova_tts(text, persona_type, emotion, output_path):
    config = load_clova_config()
    speaker = PERSONA_SPEAKER_MAP.get(persona_type, "vgoeun")
    emotion_settings = get_emotion_settings(emotion)

    headers = {
        "X-NCP-APIGW-API-KEY-ID": config["api_id"],
        "X-NCP-APIGW-API-KEY": config["api_secret"]
    }

    data = {
        "speaker": speaker,
        "text": text,
        "volume": "0",
        "speed": "0",
        "pitch": emotion_settings.get("pitch", "0"),
        "format": "mp3"
    }

    if "emotion" in emotion_settings:
        data["emotion"] = emotion_settings["emotion"]
        data["emotion_strength"] = emotion_settings["emotion_strength"]

    # 민지원 전용 설정 추가
    if persona_type == "8살_민지원":
        data["alpha"] = "3"

    response = requests.post(CLOVA_API_URL, headers=headers, data=data)
    if response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(response.content)
        return True
    else:
        print("❌ Clova TTS 실패:", response.status_code, response.text)
        return False
