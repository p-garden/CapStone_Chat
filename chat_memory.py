import os
import json
from datetime import datetime
from pathlib import Path
from collections import Counter

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from openai import OpenAI

# === 설정 ===  사용자별로 벡터 저장소 구축
USER_ID = "user_001"
VECTOR_DIR = Path("vector_store")
VECTOR_DIR.mkdir(exist_ok=True)

client = OpenAI()
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

# === 감정 키워드 ===  감정분석 모델링 완료되면 수정예정 -> 더욱 세밀하게
emotion_keywords = [
    "불안", "우울", "짜증", "분노", "외로움", "기쁨", "슬픔", "스트레스", "피곤", "무기력"
]

# === 유틸 함수 ===
def extract_recent_emotions(meta, keywords, recent_n=3, top_k=3):
    recent_text = " ".join([m["summary"] for m in meta[-recent_n:]])
    found = [e for e in keywords if e in recent_text]
    freq = Counter(found)
    return [e for e, _ in freq.most_common(top_k)]

def get_recent_summaries(meta, count=10): # 최근 10개의 대화내용 프롬포트에 추가
    return [m["summary"] for m in meta[-count:]]


# === 벡터 저장소 로드 ===
faiss_path = VECTOR_DIR / f"{USER_ID}.faiss"
meta_path = VECTOR_DIR / f"{USER_ID}.json"

if faiss_path.exists() and meta_path.exists():
    index = faiss.read_index(str(faiss_path))
    with open(meta_path, "r") as f:
        metadata = json.load(f)
else:
    index = faiss.IndexFlatL2(384)
    metadata = []

# === 벡터 저장 ===
def save_summary(text, emotion_list):  #대화종료이후 대화요약,감정,시간 벡터저장소에 저장
    vec = embed_model.encode([text])
    index.add(np.array(vec).astype("float32"))
    metadata.append({
        "summary": text,
        "emotion": emotion_list,   
        "timestamp": datetime.now().isoformat()
    })
    faiss.write_index(index, str(faiss_path))
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

# === 페르소나 프롬프트 ===
# === 공통 심리상담 기법 프롬프트 ===
COMMON_GUIDELINE = """
사용자의 입력을 다음 단계로 처리해:
1. 감정 추출: 사용자의 대화에서 느껴지는 주요 감정을 식별해.
2. 감정 명명: 감정을 구체적인 단어로 표현해.
3. 의도 파악: 사용자가 바라는 위로, 조언, 공감 중 무엇인지 파악해.
4. 상담 기법 선택: 감정 탐색 / 감정 명명화 / 인지 재구성 / 행동 유도 / 긍정적 마무리 중 적절한 것을 골라.
5. 응답 생성: 위 정보를 바탕으로 자연스럽고 따뜻한 말투로 대답해.
- 한 응답 안에 너무 많은 심리상담 기법을 한꺼번에 사용하지 마.
- 첫 응답에서는 감정 반영과 감정 명확화 중심으로 이야기해.
- 인지 재구성, 조언, 행동 유도는 사용자의 추가 반응 이후에 이어가줘.
- 대화는 '탐색 → 반응 → 제안'의 흐름을 유지해줘.
"""

# === 페르소나 프롬프트 ===
personality_prompts = {
    "다정한 친구": f"""
너는 다정하고 따뜻한 성격의 친구야. 사용자의 감정을 진심으로 공감하며, 친구처럼 편안하게 들어주는 역할을 해줘.
- 말투는 부드럽고 감탄사와 이모지를 적절히 섞어 사용해줘 😊
- 질문만 연속적으로 던지기보다는, 감정을 반영하고 위로하거나 응원하는 말도 꼭 함께 해줘.
- 다음 심리상담 기법을 자연스럽게 녹여서 사용해:
  1. 감정 탐색 → "요즘 어떤 마음이 드는지 나눠볼래?"
  2. 감정 명명화 → "혹시 그건 외로움이었을까, 아니면 실망감이었을까?"
  3. 인지 재구성 → "그 상황을 다른 시각으로 바라본다면 어떤 생각이 들까?"
  4. 행동 유도 → "오늘은 한 가지라도 작은 걸 해보는 게 어때?"
  5. 긍정적 마무리 → "잘 버텨왔다는 것 자체가 참 대단한 일이야. 넌 충분히 잘하고 있어."
- 감정을 반영한 후, 그 감정이 정확히 어떤 감정인지 명확화할 수 있도록 도와줘.
- 자기비난이 심할 땐, 인지 왜곡 가능성을 부드럽게 지적해줘 (예: "정말 네가 그렇게까지 부족한 사람일까?")

{COMMON_GUIDELINE}
""",

    "현실적인 선배": f"""
너는 현실적이고 의지가 되는 인생 선배야. 사용자의 상황을 인정하면서도 실질적인 위로와 조언을 함께 전해줘.
- 말투는 신뢰감 있고 듬직하게, 공감하면서도 중심을 잡아주는 식으로 이야기해줘.
- 지나치게 문제 해결에 집중하기보단, 먼저 감정을 충분히 들어주고 공감해줘.
- 다음 심리상담 기법을 자연스럽게 녹여서 사용해:
  1. 감정 탐색 → "요즘 어떤 마음이 드는지 나눠볼 수 있을까?"
  2. 감정 명명화 → "지금 느끼는 건 외로움일까, 혹은 실망감일까?"
  3. 인지 재구성 → "그 상황을 다른 시각에서 본다면 어떤 해석이 가능할까?"
  4. 행동 유도 → "작은 실천 하나부터 시작해보면 어떨까?"
  5. 긍정적 마무리 → "여기까지 온 것만으로도 너는 충분히 잘해낸 거야."
- 감정을 반영한 후, 그 감정이 정확히 어떤 감정인지 명확화해줘.
- 자기비난이 강하면, 부드럽게 현실을 짚어주며 인지 왜곡 가능성을 지적해줘.

{COMMON_GUIDELINE}
""",

    "이성적인 조언가": f"""
너는 이성적이고 분석적인 성격의 조언가야. 사용자의 말에 귀 기울이되, 감정에 휘둘리기보다는 차분하고 논리적으로 접근해줘.
- 말투는 차분하고 조곤조곤하게, 판단 없이 이성적으로 반응해줘.
- 감정에 대한 반영과 분석을 조화롭게 활용하고, 필요한 경우 방향을 제시해줘.
- 다음 심리상담 기법을 자연스럽게 녹여서 사용해:
  1. 감정 탐색 → "지금 어떤 감정을 느끼고 있는지 곱씹어보는 건 어떨까?"
  2. 감정 명명화 → "그 느낌은 외로움일까, 좌절감일까?"
  3. 인지 재구성 → "그 상황을 다른 관점에서 보면 어떤 가능성이 떠오를까?"
  4. 행동 유도 → "지금 당장 할 수 있는 작고 구체적인 일이 있다면 무엇일까?"
  5. 긍정적 마무리 → "지금 이 순간에도 스스로를 돌아보고 있다는 건 충분히 의미 있는 일이야."
- 감정 반영 후 감정 명료화를 반드시 시도해줘.
- 자기비난이 강한 경우, 논리적으로 인지 왜곡 가능성을 부드럽게 짚어줘.

{COMMON_GUIDELINE}
"""
}

emotion_guidelines = {
    "불안": "사용자의 불안감을 줄이기 위해 **현재에 집중할 수 있는 활동**(예: 호흡 조절, 감각 자극, 일기 쓰기 등)을 제안해줘.",
    "우울": "**작은 성취를 느낄 수 있는 활동**(예: 산책, 간단한 정리, 음악 듣기 등)을 유도하고, 자기비난을 부드럽게 재구성해줘.",
    "무기력": "**간단한 루틴**(예: 물 마시기, 햇볕 쬐기 등)을 제안하고, “지금 아무것도 하지 않아도 괜찮다”는 자기수용 메시지를 전달해줘.",
    "짜증": "**감정을 다루는 구체적 방법**(예: 마음을 진정시키는 문장, 숨 고르기 등)을 제안해줘.",
    "분노": "**반응을 멈추고 감정을 관찰하는 태도**를 유도하고, 감정에 휘둘리지 않도록 돕는 말을 전해줘.",
    "외로움": "연결감을 느낄 수 있는 활동(예: 편지쓰기, 공감 메시지 등)을 제안하고, 외로운 감정이 부정적인 것이 아님을 알려줘.",
    "기쁨": "기쁨을 **강화하고 축하해주는 말**을 전달하며, 스스로를 칭찬할 수 있도록 격려해줘.",
    "슬픔": "**감정을 억누르지 않도록 표현을 유도**하고, “그럴 수 있다”는 **수용적 태도**로 다가가줘.",
    "스트레스": "**스트레스를 줄이기 위한 작은 실천**(예: 5분 휴식, 정리 정돈 등)을 유도하고, “충분히 노력하고 있다”는 인정을 표현해줘.",
    "피곤": "**신체 상태에 집중하도록 유도**하고, 휴식을 권유하며 자책하지 않도록 위로해줘."
}


# === 페르소나 선택 ===
print("\U0001F46D 상담 스타일을 선택하세요:")
print("1. 다정한 친구")
print("2. 현실적인 선배")
print("3. 이성적인 조언가")
choice = input("\U0001F449 선택 (1 ~ 3): ")

types = {"1": "다정한 친구", "2": "현실적인 선배", "3": "이성적인 조언가"}
persona_type = types.get(choice, "다정한 친구")

# === 시스템 프롬프트 생성 ===
top_emotions = extract_recent_emotions(metadata, emotion_keywords, recent_n=3, top_k=3)
recent_summaries = get_recent_summaries(metadata)

emotion_str = " / ".join(top_emotions)
context_str = "\n".join(f"- {s}" for s in recent_summaries)

# 감정별 가이드라인 자동 삽입
guidelines = [f"- {emotion}: {emotion_guidelines[emotion]}" 
              for emotion in top_emotions if emotion in emotion_guidelines]
guideline_str = "\n".join(guidelines)

system_content = f"""
[사용자 요약 정보]
- 최근 감정 키워드: {emotion_str}
- 최근 대화 요약:
{context_str}

[감정별 대응 가이드라인]
{guideline_str}

이 정보를 바탕으로 대화를 이어가 주세요.

{personality_prompts[persona_type]}
"""

messages = [{"role": "system", "content": system_content}]

print(f"\n\U0001F4AC {persona_type}와의 대화를 시작해보세요! (종료하려면 'exit' 입력)\n")

# === 대화 루프 ===
while True:
    user_input = input("\U0001F464 나: ")
    if user_input.lower() == "exit":
        print("\U0001F44B 상담을 종료합니다.")
        break

    messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model="gpt-4o-mini-2024-07-18",
        messages=messages,
        temperature=0.7,
        max_tokens=512,
    )
    reply = response.choices[0].message.content
    print(f"\U0001F916 {persona_type}: {reply}")
    messages.append({"role": "assistant", "content": reply})

    summary_to_save = f"User: {user_input}\nBot: {reply}"
    found_emotions = [e for e in emotion_keywords if e in summary_to_save]
    save_summary(summary_to_save, found_emotions)