from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from langchain_community.llms import HuggingFacePipeline
import torch

# 🔥 1. 불필요한 VRAM 정리 (이전 모델 캐시 제거)
torch.cuda.empty_cache()
torch.cuda.memory_summary(device=None, abbreviated=False)

# 🔥 2. 모델 및 토크나이저 로드
model_name = "DeepSeek-R1-Distill-Qwen-7B"

# ✅ 3. 4-bit 양자화 설정 (메모리 절약 + 최적화)
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,  # 4-bit 양자화 적용
    bnb_4bit_use_double_quant=True,  # 2중 양자화 (RAM 절약)
    bnb_4bit_quant_type="nf4",  # NF4 양자화 방식 (더 나은 성능)
    bnb_4bit_compute_dtype=torch.float16,  # 16-bit 연산 유지
)

# ✅ 4. 토크나이저 로드
tokenizer = AutoTokenizer.from_pretrained(
    model_name,
    token=True  # 최신 방식 적용
)

# ✅ 5. 모델 로드 (Offloading 적용)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    device_map="auto",  # GPU+CPU 자동 할당 (Offloading)
    quantization_config=quantization_config,
    offload_folder="offload"  # 일부 CPU로 로드 (Offloading)
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

# ✅ 7. 테스트 프롬프트 실행
prompt = "심리 상담을 위한 조언을 제공해줘."
response = llm(prompt)

print("\n📝 상담 챗봇 응답:\n", response)