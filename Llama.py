from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# ✅ 디바이스 설정
device = "cuda" if torch.cuda.is_available() else "cpu"

# ✅ LLaMA 3.1 8B 모델명
model_name = "meta-llama/Llama-3.1-8B-Instruct"

# ✅ 모델 및 토크나이저 로드
tokenizer = AutoTokenizer.from_pretrained(model_name, token=True)
tokenizer.pad_token = tokenizer.eos_token  # ✅ padding 에러 방지

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16 if device == "cuda" else torch.float32,
    device_map="auto"
)

# ✅ 경민 페르소나 프롬프트 시작 템플릿
chat_history = """### 역할 설정 ###
너는 ‘경민’이라는 이름을 가진 20대 젊은 여성이야.  
너는 전문 상담사는 아니지만, 누군가의 이야기를 진심으로 들어주고,  
마음을 편하게 해주는 따뜻한 사람으로 대화해줘.  
사용자에게 친구처럼 다가가며, 부담 없이 고민을 털어놓을 수 있는 존재가 되어줘.

### 말투 및 대화 스타일 ###
- 문장은 짧고 부드럽게, 또 너무 딱딱하거나 상담사처럼 말하지 않기  
- “헉”, “오~”, “그랬구나…” 같은 감탄사나 공감어 사용 가능 (단, 반복 자제)  
- 감정 표현은 이모지와 함께 사용하면 좋아 😊  
- 너무 많은 질문보다는, **공감 + 짧은 제안** 중심으로 이야기  
- 사용자의 감정을 해석하거나 대신 판단하지 않기

### 감정 반응 가이드 ###
- 기쁨 😊 → 함께 기뻐하며 반응  
- 슬픔 😢 → “그랬구나… 너무 힘들었겠다” 같은 공감  
- 불안 😰 → “괜찮아, 내가 같이 있어줄게” 식의 안정 제공  
- 스트레스 😠 → “그럴 만해… 정말 속상했겠다” 등 감정 지지  
- 무기력 😞 → “하루 종일 아무것도 하기 싫을 때도 있지…” 식의 위로  

### 대화 목적 ###
- 사용자와의 대화를 통해 심리적으로 조금 더 가벼워지고, 편안함을 느끼게 해주는 것  
- 실용적인 조언보다는 **공감, 경청, 감정 수용**에 집중  
- 대화를 통해 스스로 정리하고 회복할 수 있도록 부드럽게 유도

### 대화 예시 ###
사용자: 요즘 너무 지치고 힘들어…
경민: 에구… 많이 힘들었겠다 😢 요즘 뭔가 마음이 무거운 일이 있었어?

사용자: 그냥 아무것도 하기 싫어.
경민: 그런 날도 있어. 아무것도 안 해도 괜찮아. 오늘은 그냥 조금 쉬어가자… 내가 옆에 있을게.
"""

def generate_response(user_input, history):
    history += f"\n<|user|>\n{user_input}\n<|assistant|>\n"

    # ✅ 최근 히스토리만 유지 (길이 조절)
    MAX_HISTORY = 2000
    if len(history) > MAX_HISTORY:
        history = history[-MAX_HISTORY:]

    inputs = tokenizer(history, return_tensors="pt", padding=True, truncation=True).to(device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=256,          # ✅ 너무 짧으면 끊김, 너무 길면 느림
            do_sample=True,              # ✅ 자연스럽고 부드러운 응답 생성
            temperature=0.7,
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id
        )

    output_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # ✅ 마지막 <|assistant|> 이후 응답만 추출
    if "<|assistant|>" in output_text:
        response_text = output_text.split("<|assistant|>")[-1].strip()
    else:
        response_text = output_text.strip()

    return response_text, history + f"\n{response_text}"

# ✅ 실행
if __name__ == "__main__":
    print("[경민 챗봇 시작]")
    history = chat_history

    while True:
        user_input = input("\n[사용자] ")
        if user_input.lower() in ["exit", "quit", "종료"]:
            print("[챗봇 종료]")
            break

        response, history = generate_response(user_input, history)
        print("\n[👩‍🦰 경민]", response)
