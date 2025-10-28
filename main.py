from fastapi import FastAPI
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv

# .env 파일 불러오기
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI()

class ModelRequest(BaseModel):
    model_name: str
    prompt: str

@app.get("/")
def read_root():
    return {"status": "ok", "message": "AI service backend running"}

@app.post("/agent-call")
def agent_call(req: ModelRequest):
    if req.model_name == "openai":
        api_url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": req.prompt}],
            "max_tokens": 256
        }
        response = requests.post(api_url, headers=headers, json=payload)
        result = response.json()
        return {"response": result}
    elif req.model_name == "gemini":
        return {"response": f"Gemini 모델 API 호출 (프롬프트: {req.prompt})"}
    elif req.model_name == "grok":
        return {"response": f"Grok 모델 API 호출 (프롬프트: {req.prompt})"}
    else:
        return {"error": "지원하지 않는 모델"}
