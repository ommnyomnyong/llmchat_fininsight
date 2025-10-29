from fastapi.requests import Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from jose import jwt
import requests

templates = Jinja2Templates(directory="templates")  # 템플릿 폴더 경로 설정

GOOGLE_CLIENT_ID = "client_id"
GOOGLE_CLIENT_SECRET = "client_secret"
REDIRECT_URI = "http://localhost:8000/auth/google/callback"

def render_login_page(request: Request) -> HTMLResponse:
    """
    로그인 페이지 렌더링
    """
    return templates.TemplateResponse("login.html", {"request": request})

def get_google_login_redirect() -> RedirectResponse:
    """
    구글 OAuth 인증 페이지로 리다이렉트 URL 생성 및 반환
    """
    google_auth_endpoint = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        "?response_type=code"
        f"&client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        "&scope=openid%20email%20profile"
    )
    return RedirectResponse(url=google_auth_endpoint)

def handle_google_callback(code: str) -> HTMLResponse:
    """
    OAuth 콜백 처리: 토큰 요청, 사용자 정보 조회, JWT 생성, 로그인 완료 HTML 반환
    """
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

    userinfo = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()

    jwt_token = jwt.encode(
        {"email": userinfo["email"], "name": userinfo["name"]},
        "SECRET_KEY",  # 실제 서비스에서는 환경변수 관리 필요
        algorithm="HS256"
    )

    html_content = f"""
    <h2>로그인 성공</h2>
    <p>이메일: {userinfo['email']}</p>
    <p>이름: {userinfo['name']}</p>
    <img src="{userinfo['picture']}" alt="profile" width="100">
    <p>JWT 토큰:</p>
    <textarea rows="5" cols="60">{jwt_token}</textarea>
    """
    return HTMLResponse(content=html_content)
