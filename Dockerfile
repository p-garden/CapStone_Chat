#docker build --no-cache -t capstone-fastapi .
#docker run -d -p 8000:8000 --name capstone_container capstone-fastapi
#docker start capstone_container

# 1. Python 기반 이미지
FROM python:3.10-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. 패키지 설치
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 4. 소스 코드 복사
COPY . .

# 5. FastAPI 기본 포트 열기
EXPOSE 8000

# 6. 앱 실행 (여기서 app:app 은 app.py 내부의 FastAPI 인스턴스를 의미)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]