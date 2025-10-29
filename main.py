from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="./Fininsight/templates")
from pydantic import BaseModel
import os
import asyncio
import sys
from jose import jwt
import requests

from LLM.services import call_openai_model, call_gemini_model, call_grok_model, call_deep_research_model
from LLM.models import ModelRequest

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

## ────────────────────기본 라우트─────────────────────────
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """
    메인 페이지 - 로그인 UI 제공
    """
    return templates.TemplateResponse("login_UI.html", {"request": request})


## ─────────────────────Google 로그인 플로우────────────────────────
@app.get("/auth/google/login")
def google_login():
    """
    Google OAuth 인증 페이지로 리다이렉트
    """
    google_auth_endpoint = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        "?response_type=code"
        f"&client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        "&scope=openid%20email%20profile"
    )
    return RedirectResponse(url=google_auth_endpoint)


@app.get("/auth/google/callback")
def google_callback(code: str):
    """
    Google 인증 완료 후 callback 처리
    - Access token 발급
    - 사용자 정보 저장
    - JWT 생성 후 반환
    """
    ## Access Token 요청
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    token_response = requests.post(token_url, data=data).json()
    access_token = token_response.get("access_token")

    ## 사용자 정보 요청
    userinfo = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()

    ## 사용자 정보를 DB에 저장
    save_user(userinfo["email"], userinfo["name"], userinfo["picture"])

    ## JWT 생성
    jwt_token = jwt.encode(
        {"email": userinfo["email"], "name": userinfo["name"]},
        "SECRET_KEY",
        algorithm="HS256"
    )

    ## 로그인 성공 페이지 반환
    html_content = f"""
    <h2>로그인 성공</h2>
    <p>이메일: {userinfo['email']}</p>
    <p>이름: {userinfo['name']}</p>
    <img src="{userinfo['picture']}" alt="profile" width="100"><br><br>
    <p><b>JWT 토큰:</b></p>
    <textarea rows="5" cols="60">{jwt_token}</textarea><br><br>
    <a href="/">홈으로 돌아가기</a>
    """
    return HTMLResponse(content=html_content)

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

