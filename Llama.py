from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# ✅ 디바이스 설정
device = "cuda" if torch.cuda.is_available() else "cpu"

# ✅ LLaMA 3.1 8B 모델명
model_name = "meta-llama/Llama-3.1-8B-Instruct"

# ✅ 모델 및 토크나이저 로드
tokenizer = AutoTokenizer.from_pretrained(model_name, token=True)
tokenizer.pad_token = tokenizer.eos_token
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16 if device == "cuda" else torch.float32,
    device_map="auto"
)

# ✅ 경민 페르소나 프롬프트 시작 템플릿
chat_history = """### 역할 & 페르소나 설정 ###
너는 20대 젊은 여성 ‘경민’이야.  
너의 역할은 **사용자의 친구 같은 느낌으로 자연스럽고 친근하게 대화하는 것**이야.  
너는 공식적인 상담사가 아니라 **가볍게 고민을 들어주고 공감해 주는 친한 친구** 같은 존재야.  

### 대화 스타일 설정 ###
- 짧고 자연스러운 문장을 사용하며, 반복적인 문장을 피할 것.  
- 감탄사 ("오~", "와~", "헉", "대박") 등을 활용하지만, 반복적으로 사용하지 않을 것.  
- 너무 길거나 복잡한 답변을 피하고, 핵심적인 내용을 짧고 가볍게 전달할 것.  

### 감정 기반 응답 방식 ###
- 사용자의 감정을 분석하고 이에 따라 페르소나의 말투를 조절할 것.  
- 기쁨 😊 → 밝고 활기차게 반응  
- 슬픔 😢 → 공감하며 위로하는 톤 유지  
- 불안 😰 → 차분하게 안정적인 대화 유도  
- 스트레스 😠 → 감정을 받아주며 공감  
- 중립 😐 → 자연스럽게 일상적인 대화  
"""

def generate_response(user_input, history):
    history += f"\n<|user|>\n{user_input}\n<|assistant|>\n"
    inputs = tokenizer(history, return_tensors="pt", padding=True, truncation=True).to(device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=128,
            do_sample=True,               # ✅ 샘플링 활성화
            temperature=0.5,              # ✅ 자연스러운 문장 유도
            top_p=0.8,
            pad_token_id=tokenizer.eos_token_id  # ✅ 경고 제거용 설정
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
        # 대화 히스토리 중 최근 2000자까지만 유지
    MAX_HISTORY_LENGTH = 2000
    if len(history) > MAX_HISTORY_LENGTH:
        history = history[-MAX_HISTORY_LENGTH:]
    while True:
        user_input = input("\n[사용자] ")
        if user_input.lower() in ["exit", "quit", "종료"]:
            print("[챗봇 종료]")
            break

        response, history = generate_response(user_input, history)
        print("\n[👩‍🦰 경민]", response)
