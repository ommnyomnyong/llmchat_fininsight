from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from jose import jwt
import requests
from backend.db.user_DB import save_user

router = APIRouter()

GOOGLE_CLIENT_ID = "ID입력"
GOOGLE_CLIENT_SECRET = "PW입력"
REDIRECT_URI = "http://localhost:8000/auth/google/callback"


## 구글 로그인 URL 요청
@router.get("/google/login")
def google_login():
    google_auth_endpoint = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        "?response_type=code"
        f"&client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        "&scope=openid%20email%20profile"
    )
    return RedirectResponse(url=google_auth_endpoint)


## 구글 로그인 콜백
@router.get("/google/callback")
def google_callback(code: str):
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    ## access token 발급
    token_response = requests.post(token_url, data=data).json()
    access_token = token_response.get("access_token")

    ## 사용자 정보 요청
    userinfo = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()

    ## 사용자 저장
    save_user(userinfo["email"], userinfo["name"], userinfo["picture"])

    ## JWT 발급
    jwt_token = jwt.encode(
        {"email": userinfo["email"], "name": userinfo["name"]},
        "SECRET_KEY",
        algorithm="HS256"
    )

    ## React로 리디렉션
    redirect_url = f"http://localhost:3000/oauth-success?token={jwt_token}"
    return RedirectResponse(url=redirect_url)
