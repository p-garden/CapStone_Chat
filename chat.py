from openai import OpenAI
from vector_store import save_summary, get_metadata
from prompt_builder import build_system_prompt
from emotion_utils import emotion_keywords
print("상담 스타일을 선택하세요: ...")
# 선택 입력 받고, persona_type 결정
# === 페르소나 선택 ===
print("\U0001F46D 상담 스타일을 선택하세요:")
print("1. 다정한 친구")
print("2. 현실적인 선배")
print("3. 이성적인 조언가")
choice = input("\U0001F449 선택 (1 ~ 3): ")

types = {"1": "다정한 친구", "2": "현실적인 선배", "3": "이성적인 조언가"}
persona_type = types.get(choice, "다정한 친구")
metadata = get_metadata()
system_prompt = build_system_prompt(metadata, persona_type)
messages = [{"role": "system", "content": system_prompt}]

client = OpenAI()

while True:
    user_input = input("👤 나: ")
    if user_input.lower() == "exit":
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

    found_emotions = [e for e in emotion_keywords if e in f"{user_input} {reply}"]
    save_summary(f"User: {user_input}\nBot: {reply}", found_emotions)