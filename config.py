from pathlib import Path
import os
import yaml

# 사용자 ID는 환경 변수에서 가져오고, 없을 경우 기본값 사용
USER_ID = os.getenv("USER_ID", "user_001")

# 기본 디렉토리 설정
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PROMPT_DIR = BASE_DIR / "prompts"
LOG_DIR = BASE_DIR / "logs"

# 디렉토리 생성
for path in [DATA_DIR, PROMPT_DIR, LOG_DIR]:
    path.mkdir(parents=True, exist_ok=True)

def load_prompt(file_name):
    prompt_path = PROMPT_DIR / file_name
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()

def get_config():
    return {
        "openai": {
            "key": os.getenv("OPENAI_API_KEY", "")
        }
    }
def load_config():
    config_path = Path(__file__).parent / "conf.d" / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def set_openai_api_key():
    config = load_config()
    os.environ["OPENAI_API_KEY"] = config["openai"]["key"]