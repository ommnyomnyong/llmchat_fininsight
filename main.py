from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.chat_router import router as chat_router
from routers.project_router import router as project_router
from routers.user_router import router as user_router
import sys
import asyncio


if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

app = FastAPI()
app.state.session_histories = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/chat")
app.include_router(project_router, prefix="/project")
app.include_router(user_router, prefix="/auth")

# 헬스 체크 등 최소한의 공통 엔드포인트만 main.py에 둠
@app.get("/healthz")
def health_check():
    return {"status": "ok"}

@app.get("/")
def read_root():
    return {"message": "FastAPI 서버 정상"}