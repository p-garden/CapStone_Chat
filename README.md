# CapStone_Chat
2025-1학기 세종대학교 캡스톤 "심리상담 서비스" AI파트
CapStone_Chat/  
├── chat.py                     # 💬 전체 상담 세션 실행 메인 루프   
│   └── 담당: 상담 진행, 사용자 입력 처리, 에이전트와의 대화 흐름 관리  
│   └── 상담자 및 평가자 역할을 수행하는 에이전트를 호출하여 대화 진행  
│  
├── DB.py                       # 🗄️ 몽고DB 연결 및 데이터베이스 관련 기능   
│   └── 담당: 사용자 정보 저장 및 불러오기, 채팅 로그 관리  
│   └── MongoDB와 연동하여 사용자별 채팅 정보 및 대화 로그 저장  
│   └── `save_chat_log`, `get_chat_log` 함수 등  
│  
├── app.py                      # 🌐 FastAPI 서버   
│   └── 담당: API 서버 구축, 클라이언트 요청 처리  
│   └── 사용자의 입력에 따라 chat.py와 DB.py를 연동하여 상담 세션 시작  
│   └── 백엔드 서버와의 통신을 통해 상담 진행  
│   └── `/start_conversation` 엔드포인트를 통해 상담을 시작하고 결과 반환  
├── config.py                   # ⚙️ 경로, 설정값 등 공통 설정   
│  
├── agents/                     # 🤖 에이전트(모델 역할자) 모듈    
│   ├── counselor_agent.py      # 상담자 역할 에이전트 (서비스용), main LLM   
│   ├── evaluator_agent.py      # 평가자 역할 에이전트 (내부 평가용)  
│   ├── cbt_agent.py            # 에이전트 AI(Assist RAG, 보조 LLM) 감정 소분류, 인지오류, CBT전략등  사용자의 정보를 파악해서 프롬포트 맞춤형 생성 
│  
├── prompts/                    # 📝 모든 에이전트용 프롬프트 텍스트 파일    
│   ├── agent_counselor.txt  
│   └── ...  
│  
├── data/                       # 🗂️ 대화 샘플, 감정 분석 결과 등 저장 위치  
│   ├── example1.json      # 내담자 정보및 시작대화
│   └── ...       
│   
├── results/                    # 📊 평가 결과 저장  
│   ├── emotion_results.json    # 감정 평가 결과 
│   ├── evaluation_scores.json  # 평가자 채점 결과    
│   └── ...  
│
├── logs/                       # 📜 로그 파일 저장
│   ├── chat_log.json           # 1:1 대화 기록 저장  
│
└── README.md                   # 📘 프로젝트 설명서  