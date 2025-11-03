## 채팅 저장 및 불러오기

from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from backend.db.chat_DB import save_chat, get_chats

router = APIRouter()
## chat_router.py → save_chat() 호출
## chat_DB.py의 save_chat()에서 MySQL에 저장
@router.post("/save")
def save_chat_message(
    project_id: int = Form(...), 
    user_input: str = Form(...), 
    bot_output: str = Form(...)
    ):
    save_chat(project_id, user_input, bot_output)
    return {"message": "✅ 채팅 저장 완료 ✅"}

## chat_router.py → get_chats(project_id) 실행
## chat_DB.py에서 해당 프로젝트의 모든 대화 불러옴
@router.get("/list")
def get_chat_history(project_id: int):
    chats = get_chats(project_id)
    return {"chats": chats}
