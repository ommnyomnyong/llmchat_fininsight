from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from jose import jwt
import requests

app = FastAPI()
templates = Jinja2Templates(directory="templates")

GOOGLE_CLIENT_ID = "client_id"
GOOGLE_CLIENT_SECRET = "cliend_pw"
REDIRECT_URI = "http://localhost:8000/auth/google/callback"


@app.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

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
    token_response = requests.post(token_url, data=data).json()
    access_token = token_response.get("access_token")


    userinfo = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()

    jwt_token = jwt.encode(
        {"email": userinfo["email"], "name": userinfo["name"]},
        "SECRET_KEY",
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
