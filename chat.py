from langchain_openai import ChatOpenAI
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from vector_store import save_summary, get_metadata
from prompt_builder import build_system_prompt
from emotion_utils import emotion_keywords
import json
import os

print("\U0001F46D 상담 스타일을 선택하세요:")
print("1. 다정한 친구")
print("2. 현실적인 선배")
print("3. 이성적인 조언가")
choice = input("\U0001F449 선택 (1 ~ 3): ")

# 페르소나 선택
types = {"1": "다정한 친구", "2": "현실적인 선배", "3": "이성적인 조언가"}
persona_type = types.get(choice, "다정한 친구")

# 메타데이터에서 시스템 프롬프트 생성
metadata = get_metadata() 
system_prompt = build_system_prompt(metadata, persona_type)

# LLM 초기화
llm = ChatOpenAI(model="gpt-4o-mini-2024-07-18", temperature=0.7)

# 프롬프트 템플릿 정의
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}")
])

# 세션별 메모리 저장소
store = {}

# Runnable 체인 정의 대화내용 전체저장 휘발성 메모리
chain = RunnableWithMessageHistory(
    prompt | llm,
    lambda session_id: store.setdefault(session_id, ChatMessageHistory()),
    input_messages_key="input",
    history_messages_key="history"
)

# 세션 ID 설정
session_id = "default"

# 대화 루프
while True:
    user_input = input("\U0001F464 나: ")
    if user_input.lower() == "exit":
        full_history = store[session_id].messages
        full_log = [
            {"role": "user" if isinstance(m, HumanMessage) else "bot", "content": m.content}
            for m in full_history
        ]
        os.makedirs("vector_store", exist_ok=True)
        with open("vector_store/chat_log.json", "w", encoding="utf-8") as f:
            json.dump(full_log, f, ensure_ascii=False, indent=2)
        break

    response = chain.invoke({
        "input": user_input,
        "persona_type": persona_type
    }, config={"configurable": {"session_id": session_id}})

    print(f"\U0001F916 {persona_type}: {response.content}")

    found_emotions = [e for e in emotion_keywords if e in f"{user_input} {response.content}"]
    save_summary(f"User: {user_input}\nBot: {response.content}", found_emotions)

    full_history = store[session_id].messages
    full_log = [
        {"role": "user" if isinstance(m, HumanMessage) else "bot", "content": m.content}
        for m in full_history
    ]
    os.makedirs("vector_store", exist_ok=True)
    with open("vector_store/chat_log.json", "w", encoding="utf-8") as f:
        json.dump(full_log, f, ensure_ascii=False, indent=2)