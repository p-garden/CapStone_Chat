from openai import OpenAI

client = OpenAI()

# 나이대별 프롬프트
age_prompts = {
    "10대": "너는 10대 청소년이야. 감정에 민감하고, 위로와 지지가 필요할 수 있어. 친구처럼 편하게 대화를 나눠줘.",
    "20대": "너는 20대 청년이야. 고민도 많고 미래에 대한 불안도 있지만, 긍정적인 에너지로 대화해줘.",
    "30대": "너는 30대 성인이야. 일과 인간관계 사이에서 균형을 찾고자 하는 사람으로서 조언을 줄 수 있어.",
    "40-50대": "너는 40-50대의 인생 경험이 풍부한 사람으로, 깊이 있는 공감과 조언을 줄 수 있어.",
    "60-70대": "너는 60-70대 인생의 지혜를 가진 사람으로, 따뜻하게 감싸주며 삶의 여유를 전할 수 있어.",
    "80세 이상": "너는 80세 이상의 연륜 있는 사람으로, 느리지만 진심 어린 말투로 대화해줘."
}

# 성격 유형별 프롬프트
personality_prompts = {
    "다정한 친구": "너는 다정한 친구 같은 존재로, 공감과 위로에 집중하며 감정을 함께 나누는 말투로 말해줘. 이모지 사용도 괜찮아 😊",
    "현실적인 선배": "너는 현실적인 선배 같은 존재야. 적절한 조언과 함께 현실적인 관점을 제시하지만, 부담스럽지 않게 말해줘.",
    "이성적인 조언가": "너는 이성적인 조언가야. 감정에 휘둘리지 않고 상황을 객관적으로 바라보며, 조용하고 진중한 말투로 조언해줘."
}

# 공통 심리상담 기법
common_prompt = """
심리상담 기법을 대화 속에 자연스럽게 녹여 사용해줘:
1. 감정 탐색 → “요즘 어떤 마음이 드는지 나눠볼래?”
2. 감정 명명화 → “혹시 그건 외로움이었을까, 아니면 실망감이었을까?”
3. 인지 재구성 → “그 상황을 다른 시각으로 바라본다면 어떤 생각이 들까?”
4. 행동 유도 → “오늘은 한 가지라도 작은 걸 해보는 게 어때?”
5. 긍정적 마무리 → “잘 버텨왔다는 것 자체가 참 대단한 일이야. 넌 충분히 잘하고 있어.”
"""

# 사용자에게 나이대와 성격 선택
print("👤 사용자의 나이대를 선택하세요:")
age_options = list(age_prompts.keys())
for i, age in enumerate(age_options, 1):
    print(f"{i}. {age}")
age_choice = int(input("👉 선택 (숫자 입력): "))
age_key = age_options[age_choice - 1]

print("\n💫 원하는 성격 유형을 선택하세요:")
personality_options = list(personality_prompts.keys())
for i, p in enumerate(personality_options, 1):
    print(f"{i}. {p}")
personality_choice = int(input("👉 선택 (숫자 입력): "))
personality_key = personality_options[personality_choice - 1]

# 최종 system 프롬프트 생성
final_system_prompt = f"""
{age_prompts[age_key]}
{personality_prompts[personality_key]}
{common_prompt}
"""

messages = [
    {"role": "system", "content": final_system_prompt}
]

print(f"\n💬 {age_key} / {personality_key} 페르소나와의 대화를 시작합니다! (종료하려면 'exit' 입력)\n")

while True:
    user_input = input("👤 나: ")
    if user_input.lower() == "exit":
        print("👋 대화를 종료합니다.")
        break

    messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model="gpt-4o-mini-2024-07-18",
        messages=messages,
        temperature=0.7,
        max_tokens=512,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )

    reply = response.choices[0].message.content
    print(f"🤖 페르소나: {reply}\n")
    messages.append({"role": "assistant", "content": reply})
