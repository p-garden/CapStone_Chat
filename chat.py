import json
from pathlib import Path
from agents.counselor_agent import CounselorAgent
from agents.evaluator_agent import EvaluatorAgent
from config import set_openai_api_key
from DB import get_chat_log, save_chat_log, save_user_info, get_user_info
from datetime import datetime

# OpenAI API 키 설정
set_openai_api_key()

from pymongo import MongoClient
client = MongoClient("mongodb+srv://j2982477:EZ6t7LEsGEYmCiJK@mindai.zgcb4ae.mongodb.net/?retryWrites=true&w=majority&appName=mindAI")
db = client['mindAI']

class TherapySimulation:
    def __init__(self, persona_type: str, chat_id: str, user_id: str, max_turns: int = 20):
        self.persona_type = persona_type
        self.chat_id = chat_id
        self.user_id = user_id
        self.max_turns = max_turns
        self.history = []

        # 사용자 정보 로딩
        user_info = get_user_info(self.user_id)
        if user_info:
            self.name = user_info["name"]
            self.age = user_info["age"]
            self.gender = user_info["gender"]
        else:
            print(f"{self.user_id}는 새로운 사용자입니다. 사용자 정보를 입력해주세요.")
            self.name = input("이름을 입력해주세요: ")
            self.age = int(input("나이를 입력해주세요: "))
            self.gender = input("성별을 입력해주세요: ")
            save_user_info(self.user_id, self.name, self.age, self.gender)

        # 에이전트 초기화
        self.counselor_agent = CounselorAgent(
            client_info=f"{self.name}, {self.age}세, {self.gender}",
            persona_type=self.persona_type
        )

        # 수정
        self.evaluator_agent = EvaluatorAgent()

        # 기존 상담 기록 불러오기
        chat_log = get_chat_log(self.chat_id, self.user_id)
        if chat_log:
            self.history = chat_log
        else:
            # 초기 상담사 인사는 generate_response 대신 LLM 직접 호출로 처리
            welcome_input = "상담을 시작하는 간단한 인사말과 상담사의 페르소나를 소개해 주세요. 이름과 나이를 밝혀주세요"
            counselor_result = self.counselor_agent.generate_response([], welcome_input)

            initial_message = {
                "role": "counselor",
                "message": counselor_result["reply"],
                "timestamp": datetime.now().isoformat()
            }
            self.history.append(initial_message)

            print("Counselor:", initial_message["message"])

    
    

    def run(self):
        for turn in range(self.max_turns):
            print(f"--- Turn {turn + 1} ---")
            client_msg = input(f"{self.name}: ").strip()

            if "[/END]" in client_msg:
                break

            # 사용자 메시지 + 타임스탬프 포함
            self.history.append({
                "role": "client",
                "message": client_msg,
                "timestamp": datetime.now().isoformat()
            })

            # 상담사 응답 생성
            result = self.counselor_agent.generate_response(self.history, client_msg)
            counselor_msg = result.get("reply", "[⚠️ 상담사 응답을 생성하지 못했습니다.]")
            emotion = result.get("emotion", "감지되지 않음")
            distortion = result.get("distortion", "감지되지 않음")
            strategy = result.get("cbt_strategy", "전략 없음")

            # 출력
            print("Counselor:", counselor_msg)
            print(f"[감정] {emotion} | [인지 왜곡] {distortion} | [전략] {strategy}\n")

            # 상담사 응답도 타임스탬프 포함
            self.history.append({
                "role": "counselor",
                "message": counselor_msg,
                "timestamp": datetime.now().isoformat()
            })

            # 저장
            save_chat_log(self.user_id, self.chat_id, client_msg, counselor_msg)

        # 통합 평가
        full_conversation = "\n".join([
            f"{msg['role'].capitalize()}: {msg['message']}" for msg in self.history
        ])
        evaluation_result = self.evaluator_agent.evaluate_all(self.history)
        feedback_summary = self.evaluator_agent.generate_feedback_summary(self.history, evaluation_result)

        # 최종 결과 저장
        return {
            "persona": self.persona_type,
            "history": self.history,
            "evaluation": evaluation_result
        }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_file", required=True)
    parser.add_argument("--persona_type", required=True)
    parser.add_argument("--chat_id", required=True)
    parser.add_argument("--user_id", required=True)

    args = parser.parse_args()

    sim = TherapySimulation(
        persona_type=args.persona_type,
        chat_id=args.chat_id,
        user_id=args.user_id
    )
    result = sim.run()

    Path(args.output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)