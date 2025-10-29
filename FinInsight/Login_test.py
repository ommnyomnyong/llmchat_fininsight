from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from jose import jwt
import requests

## FastAPI 앱 기본 설정
app = FastAPI()
templates = Jinja2Templates(directory="templates")      ## HTML 렌더링용 템플릿 폴더(templates)

## Google OAuth 클라이언트 설정
GOOGLE_CLIENT_ID = "client_id"
GOOGLE_CLIENT_SECRET = "cliend_pw"
REDIRECT_URI = "http://localhost:8000/auth/google/callback"    ## OAuth 인증 완료 후 이동 경로


## 기본 페이지 ----- 로그인 버튼
@app.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    """
    Front에서 접근 시 기본으로 보여주는 로그인 페이지
    (템플릿: templates/login_UI.html)
    """
    return templates.TemplateResponse("login.html", {"request": request})


## Google OAuth 로그인 요청
@app.get("/auth/google/login")
def google_login():
    google_auth_endpoint = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        "?response_type=code"
        f"&client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        "&scope=openid%20email%20profile"
    )
    return RedirectResponse(url=google_auth_endpoint)

## Google 로그인 callback 처리
@app.get("/auth/google/callback")
def google_callback(code: str):
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    ## Google OAuth 서버로 토큰 요청
    token_response = requests.post(token_url, data=data).json()
    access_token = token_response.get("access_token")


    ## 사용자 프로필 정보 가져오기
    userinfo = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()

    ## JWT 토큰 생성
    jwt_token = jwt.encode(
        {"email": userinfo["email"], "name": userinfo["name"]},
        "SECRET_KEY",        ## 실제 서비스에서는 .env로 분리 필요
        algorithm="HS256"
    )

    ## 로그인 완료 후 화면
    html_content = f"""
    <h2>로그인 성공</h2>
    <p>이메일: {userinfo['email']}</p>
    <p>이름: {userinfo['name']}</p>
    <img src="{userinfo['picture']}" alt="profile" width="100">
    <p>JWT 토큰:</p>
    <textarea rows="5" cols="60">{jwt_token}</textarea>
    """
    return HTMLResponse(content=html_content)

