from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import asyncio
import sys

from LLM.services import call_openai_model, call_gemini_model, call_grok_model, call_openai_deep_research_model
from LLM.models import ModelRequest

# Windows 환경에서 uvicorn 실행 시 asyncio 이벤트 루프 정책 설정
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

app = FastAPI()

# CORS 설정: React 개발 서버(기본 3000 포트) 등에서 API 호출 가능하도록 모든 도메인 허용(테스트용)
# 운영 환경에서는 allow_origins를 프론트 도메인으로 제한 권장
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    """
    헬스 체크용 기본 엔드포인트.
    React 앱이나 다른 클라이언트에서 백엔드 서버 상태 확인 가능.
    """
    return {"status": "ok", "message": "AI service backend running"}

@app.post("/agent-call/{model_name}")
def agent_call(model_name: str, req: ModelRequest):
    """
    AI 모델 호출 단일 엔드포인트.

    - model_name: 호출할 AI 모델명 (예: openai, gemini, grok, gpt-4o-search-preview)
    - req: 요청 바디로 session_id, prompt 포함
    - 지정된 모델의 서비스 함수 호출 후 JSON 응답 반환

    React 프론트에서 다음과 같이 호출:

    ```
    fetch("http://127.0.0.1:8000/agent-call/gpt-4o-search-preview", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        session_id: "user-session-id",
        prompt: "오늘 삼성전자 주가 알려줘"
      })
    })
    .then(res => res.json())
    .then(data => {
      // data.answer 포함된 AI 답변을 UI에 출력
      // data.history 전체 대화 기록 관리
      console.log(data.answer);
    });
    ```

    - React 개발 시 동일 컴퓨터 로컬에서 FastAPI 서버 8000 포트와 React 개발서버 3000 포트가 다른 도메인이므로,
    - CORS 미들웨어로 API 요청이 차단되지 않도록 허용 설정되어 있음.
    """
    if model_name == "openai":
        return call_openai_model(req)
    elif model_name == "gemini":
        return call_gemini_model(req)
    elif model_name == "grok":
        return call_grok_model(req)
    elif model_name == "gpt-4o-search-preview":
        return call_openai_deep_research_model(req)
    else:
        raise HTTPException(status_code=400, detail="지원하지 않는 모델입니다")

if __name__ == "__main__":
    import uvicorn
    import sys
    import asyncio

    # Windows 호환을 위한 이벤트 루프 정책 설정
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    # FastAPI + uvicorn 서버 실행 (로컬 8000 포트)
    # 터미널에서 아래 명령으로 실행 가능
    # python main.py
    # React 개발서는 보통 터미널에서 별도 `npm start`로 localhost:3000 실행
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
