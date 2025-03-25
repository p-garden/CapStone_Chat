# chat_with_memory.py

import os
import json
from datetime import datetime
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from openai import OpenAI

# === 사용자 설정 ===
USER_ID = "user_001"
VECTOR_DIR = Path("vector_store")
VECTOR_DIR.mkdir(exist_ok=True)

client = OpenAI()
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

# === 파일 경로 ===
faiss_path = VECTOR_DIR / f"{USER_ID}.faiss"
meta_path = VECTOR_DIR / f"{USER_ID}.json"

# === 벡터 저장소 불러오기 ===
if faiss_path.exists() and meta_path.exists():
    index = faiss.read_index(str(faiss_path))
    with open(meta_path, "r") as f:
        metadata = json.load(f)
else:
    index = faiss.IndexFlatL2(384)
    metadata = []

# === 벡터 저장 함수 ===
def save_summary(text):
    vec = embed_model.encode([text])
    index.add(np.array(vec).astype("float32"))
    metadata.append({"summary": text, "timestamp": datetime.now().isoformat()})
    faiss.write_index(index, str(faiss_path))
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

# === 검색 함수 ===
def retrieve_summaries(query, top_k=3):
    if len(metadata) == 0:
        return []
    q_vec = embed_model.encode([query])
    D, I = index.search(np.array(q_vec).astype("float32"), top_k)
    return [metadata[i]["summary"] for i in I[0] if i < len(metadata)]

# === 페르소나 선택 ===
personality_prompts = {
    "다정한 친구": "...",  # 프롬프트 생략 (위 코드 내용 그대로)
    "현실적인 선배": "...",
    "이성적인 조언가": "..."
}

print("👥 상담 스타일을 선택하세요:")
print("1. 다정한 친구")
print("2. 현실적인 선배")
print("3. 이성적인 조언가")
choice = input("👉 선택 (1 ~ 3): ")

types = {"1": "다정한 친구", "2": "현실적인 선배", "3": "이성적인 조언가"}
persona_type = types.get(choice, "다정한 친구")

# === system prompt 구성 ===
recent_context = retrieve_summaries("최근 감정, 수면, 스트레스 등")
context_prompt = "\n".join([f"- {item}" for item in recent_context])
system_content = f"""
이전에 사용자는 다음과 같은 이력이 있습니다:
{context_prompt}

이를 참고하여 대화를 이어가 주세요.

{personality_prompts[persona_type]}
"""

messages = [{"role": "system", "content": system_content}]

print(f"\n💬 {persona_type}와의 대화를 시작해보세요! (종료하려면 'exit' 입력)\n")

while True:
    user_input = input("👤 나: ")
    if user_input.lower() == "exit":
        print("👋 상담을 종료합니다.")
        break

    messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model="gpt-4o-mini-2024-07-18",
        messages=messages,
        temperature=0.7,
        max_tokens=512,
    )
    reply = response.choices[0].message.content
    print(f"🤖 {persona_type}: {reply}")
    messages.append({"role": "assistant", "content": reply})

    # 대화 내용 요약해서 저장 (간단히 input + reply로 저장)
    summary_to_save = f"User: {user_input}\nBot: {reply}"
    save_summary(summary_to_save)