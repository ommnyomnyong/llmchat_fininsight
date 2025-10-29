from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import asyncio
import sys


from services import call_openai_model, call_gemini_model, call_grok_model, call_openai_deep_research_model
from models import ModelRequest

import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"status": "ok", "message": "AI service backend running"}

@app.post("/agent-call/{model_name}")
def agent_call(model_name: str, req: ModelRequest):
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

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)