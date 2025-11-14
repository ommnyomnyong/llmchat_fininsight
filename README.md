# llmchat_fininsight

## 🚀 프로젝트 소개
- AI 챗봇 기반의 **LLM Chat 서비스** 개발 프로젝트
- FastAPI 백엔드와 React 프론트엔드로 구성
- 사용자 대화 기록, 프로젝트 관리 및 심층 리서치 기능 포함

## ✨ 주요 기능
- 🛠️ FastAPI 기반 고성능 서버 구현
- 💬 대화 세션 및 채팅 기록 관리
- 👥 프로젝트별 사용자 협업 지원
- 🔍 실시간 심층 리서치 및 다중 AI 모델 비교
- 🔐 이메일 및 소셜 로그인(구글) 연동

## 🎯 기술 스택
- Python, FastAPI, SQLAlchemy, MariaDB
- React.js, TypeScript, Chakra UI
- Redis (세션과 캐싱용)
- OpenAI GPT API 등 다중 AI 모델 연동

## 📂 프로젝트 구조
- `/backend` : FastAPI 서버 코드
- `/frontend` : React 기반 프론트엔드
- `/database` : DB 스키마 및 마이그레이션 관리

## ⚙️ 실행 방법
1. `.env` 파일에 API 키 및 DB 정보 입력  
2. 백엔드 서버: `uvicorn main:app --reload`  
3. 프론트엔드: `npm start` 또는 `yarn start`  
4. 브라우저에서 `http://localhost:3000` 접속

## 💡 기여하기
- 이슈 등록 및 PR 환영  
- 코드 스타일 및 커밋 메시지 컨벤션 준수 부탁드립니다

## 📄 라이선스
- MIT License
