from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from langchain_community.llms import HuggingFacePipeline
import torch
torch.cuda.empty_cache()

# 🔥 1. 불필요한 VRAM 정리 (이전 모델 캐시 제거)
torch.cuda.empty_cache()
torch.cuda.memory_summary(device=None, abbreviated=False)

# 🔥 2. 모델 및 토크나이저 로드
model_name = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,  # ✅ 변경: bfloat16 사용
)
max_memory = {0: "14GB", "cpu": "10GB"}  # V100 16GB에서 안정적인 메모리 할당

# ✅ 4. 토크나이저 로드
tokenizer = AutoTokenizer.from_pretrained(
    model_name,
    token=True
)


# ✅ 5. 모델 로드 (Offloading 적용)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    device_map = "auto",
    quantization_config=quantization_config,
    offload_state_dict=True  # 모델 일부를 CPU에 오프로드 (VRAM 절약)
)

# ✅ 6. LangChain에서 사용할 래퍼 생성
llm = HuggingFacePipeline.from_model_id(
    model_id=model_name,
    task="text-generation",
    model_kwargs={
        "temperature": 0.7,
        "max_length": 512,
        "do_sample": True,  # 경고 해결 (샘플링 방식 설정)
    },
)


# ✅ 7. 경민 페르소나 적용한 프롬프트
# ✅ DeepSeek에 맞춰 개선된 프롬프트
prompt = """### 역할 & 페르소나 설정 ###
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

### 예시 ###
사용자: "요즘 너무 피곤하고 지치는 느낌이야…"
경민: "헉... 진짜 힘들겠다. 요즘 잠은 잘 자고 있어?😭 조금 쉬면서 리프레시하는 게 필요할 것 같아."

사용자의 입력: "{user_input}"  
경민의 응답:"""

# ✅ 6. 사용자 입력 받아서 응답 생성
def generate_response(user_input):
    final_prompt = prompt.format(user_input=user_input)
    
    # 토큰화
    inputs = tokenizer(final_prompt, return_tensors="pt").to("cuda")
    
    # 모델 실행
    with torch.no_grad():
        outputs = model.generate(**inputs, max_length=512)
    
    # 출력 디코딩
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# ✅ 7. 실행 테스트
if __name__ == "__main__":
    while True:
        user_input = input("\n[사용자] ")
        if user_input.lower() in ["exit", "quit", "종료"]:
            print("[챗봇 종료]")
            break
        
        response = generate_response(user_input)
        print("\n[👩‍🦰 경민]:", response)

