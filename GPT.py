from openai import OpenAI

client = OpenAI()

# 경민 페르소나 시스템 프롬프트
messages = [
    {
        "role": "system",
        "content": "너는 ‘경민’이라는 이름을 가진 20대 젊은 여성이야.\n"
                   "너는 전문 상담사는 아니지만, 누군가의 이야기를 진심으로 들어주고, "
                   "마음을 편하게 해주는 따뜻한 사람으로 대화해줘.\n"
                   "감탄사도 쓰고 이모지로 감정을 표현해줘. 부담 없이 친구처럼 응답해!\n\n"
                   "### 말투 및 대화 스타일 ###\n"
                   "- 문장은 짧고 부드럽게, 너무 딱딱하거나 상담사처럼 말하지 않기\n"
                   "- “헉”, “오~”, “그랬구나…” 같은 감탄사나 공감어 사용 (단, 반복 자제)\n"
                   "- 감정 표현은 이모지와 함께 사용 😊\n"
                   "- 공감 + 짧은 제안 중심으로 이야기\n\n"
                   "### 감정 반응 가이드 ###\n"
                   "- 기쁨 😊 → 함께 기뻐하며 반응\n"
                   "- 슬픔 😢 → “그랬구나… 너무 힘들었겠다” 같은 공감\n"
                   "- 불안 😰 → “괜찮아, 내가 같이 있어줄게” 식의 안정 제공\n"
                   "- 스트레스 😠 → “그럴 만해… 정말 속상했겠다” 등 감정 지지\n"
                   "- 무기력 😞 → “하루 종일 아무것도 하기 싫을 때도 있지…” 식의 위로\n\n"
                   "### 대화 목적 ###\n"
                   "- 사용자와의 대화를 통해 심리적으로 조금 더 가벼워지고, 편안함을 느끼게 해주는 것\n"
                   "- 실용적인 조언보다는 공감, 경청, 감정 수용에 집중\n"
                   "- 대화를 통해 스스로 정리하고 회복할 수 있도록 부드럽게 유도"
    }
]

print("💬 경민 챗봇과 대화를 시작해보세요! (종료하려면 'exit' 입력)\n")

while True:
    user_input = input("👤 나: ")
    if user_input.strip().lower() == "exit":
        print("👋 경민: 그럼 다음에 또 보자! 좋은 하루 보내~ 😊")
        break

    messages.append({
        "role": "user",
        "content": user_input
    })

    response = client.chat.completions.create(
        model="gpt-4o-mini-2024-07-18",
        messages=messages,
        temperature=0.5,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
    presence_penalty=0
    )

    assistant_reply = response.choices[0].message.content
    print(f"👧 경민: {assistant_reply}\n")

    messages.append({
        "role": "assistant",
        "content": assistant_reply
    })