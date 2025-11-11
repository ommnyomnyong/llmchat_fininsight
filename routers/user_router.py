from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from jose import jwt
import requests
from db.user_DB import save_user
import os
from dotenv import load_dotenv
load_dotenv()

router = APIRouter()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8000/auth/google/callback"


# ✅ scope 추가 (중요)
SCOPE = "openid email profile"

## 구글 로그인 URL 요청
@router.get("/google/login")
def google_login():
    google_auth_endpoint = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        "?response_type=code"
        f"&client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope={SCOPE}"
        "&access_type=offline"
        "&prompt=consent"
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
    # -- 로그인 후 사용자를 식별하기 위해, 
    # -- 서버가 아닌 토큰으로 인증 상태를 유지하기 위해
    # -- 프론트엔드가 API 요청할 때, Authorization 헤더에 포함시키기 위해
    # -- 구글 OAuth로 받은 사용자 정보를 바탕으로 JWT 발급 —> 이후엔 자체 인증 체계로 전환
    jwt_token = jwt.encode(
        {"email": userinfo["email"], "name": userinfo["name"]},
        "SECRET_KEY",
        algorithm="HS256"
    )

    ## React로 리디렉션
    redirect_url = f"http://localhost:3000/oauth-success?token={jwt_token}"
    return RedirectResponse(url=redirect_url)
