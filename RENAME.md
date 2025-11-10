# Login + Chat Integration App

## 🧩 프로젝트 실행 방법

### 1️⃣ 설치
```bash
# 백엔드 라이브러리
pip install -r requirements.txt

# 프론트엔드 라이브러리
npm install

2️⃣ 환경 변수 설정

.env 파일을 프로젝트 루트(main.py가 있는 곳)에 생성하고 .env.example 참고해서 키 입력

3️⃣ 실행
# 백엔드
uvicorn main:app --reload

# 프론트엔드 (다른 터미널에서)
npm start4️⃣ 접속

브라우저에서 http://localhost:3002
 로 접속


이렇게 하면 백엔드 팀이 그대로 pull 받아서  
> ✅ 가상환경 만들고  
> ✅ requirements 설치하고  
> ✅ npm start 실행하면  
> **로그인 → 채팅화면까지 전부 정상 동작.**
