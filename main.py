from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import os
import asyncio
import sys
from jose import jwt
import requests

from LLM.services import call_openai_model, call_gemini_model, call_grok_model, call_deep_research_model
from LLM.models import ModelRequest
from Login.login import render_login_page, get_google_login_redirect, handle_google_callback


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


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """
    메인 로그인 페이지 렌더링 엔드포인트

    - 역할: 로그인 UI (예: 이메일+비밀번호 입력, Google 로그인 버튼 등)를 사용자에게 보여줌
    - 프론트에서 활용법:
      • 사용자가 웹사이트 접속 시 이 URL(`"/"`)을 호출하여 로그인 화면을 받음
      • 로그인 UI에서 사용자는 로그인 정보 입력 혹은 OAuth 로그인 버튼 클릭 가능
      • React 같은 SPA 환경이라면 초기 페이지 로딩용으로 사용 가능
    """
    return render_login_page(request)


@app.get("/auth/google/login")
def google_login():
    """
    Google OAuth 인증 시작을 위해 Google 로그인 페이지로 리다이렉트하는 엔드포인트

    - 역할: Google 로그인을 위해 OAuth 인증 URL로 리다이렉션 처리
    - 프론트에서 활용법:
      • 로그인 UI에서 사용자가 'Google로 로그인' 버튼 클릭 시 이 엔드포인트를 호출
      • 호출 즉시 Google OAuth 인증 페이지로 이동함 (사용자 인증/권한 요청)
      • OAuth 인증 끝나면 Google이 미리 지정한 콜백 URL로 리다이렉트(예: `/auth/google/callback`)
    """
    return get_google_login_redirect()


@app.get("/auth/google/callback")
def google_callback(code: str):
    """
    Google OAuth 인증 콜백 엔드포인트

    - 역할:
      • Google 로그인 완료 후 Google OAuth 서버가 리다이렉트하면서 전달하는 인증 코드(`code`)를 받음
      • 이 `code`를 이용해 Google OAuth 서버에 액세스 토큰 발급 요청을 수행
      • 액세스 토큰을 바탕으로 Google 사용자 정보를 API로 요청
      • 사용자 정보를 내부 DB에 저장 (회원 관리 목적)
      • JWT 토큰을 생성해, 로그인 성공 정보를 사용자에게 보여줌
    - 프론트에서 활용법:
      • 사용자가 Google 로그인 과정 완료 후 자동으로 이 엔드포인트가 호출됨
      • 종료 화면에서 이메일, 이름, 프로필 사진, JWT 토큰 등을 확인 가능
      • 별도 UI가 아닌 API 호출 이후 리턴되는 HTML 페이지를 바로 보여주는 구조
      • 추후 JWT 토큰을 이용해 클라이언트 세션 관리 및 API 인증에 활용 가능
    """
    return handle_google_callback(code)


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

    - model_name: 호출할 AI 모델명 (예: openai, gemini, grok, gpt-4o-search-preview, gemini-2.5-pro)
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
    elif model_name in ["gpt-4o-search-preview", "gemini-2.5-pro"]:
        return call_deep_research_model(req)
    else:
        raise HTTPException(status_code=400, detail="지원하지 않는 모델입니다")

if __name__ == "__main__":
    import uvicorn
    import sys
    import asyncio

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
    else:
        loop = None

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True, loop=loop)

    # FastAPI + uvicorn 서버 실행 (로컬 8000 포트)
    # 터미널에서 아래 명령으로 실행 가능
    # python main.py
    # React 개발서는 별도 터미널에서 `npm start`로 localhost:3000 실행

