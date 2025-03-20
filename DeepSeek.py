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

# ✅ 테스트 실행
inputs = tokenizer("심리 상담을 위한 조언을 제공해줘.", return_tensors="pt").to("cuda")
outputs = model.generate(**inputs, max_length=512)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))