## 채팅 저장 및 불러오기

from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from db.chat_DB import save_chat, get_chats
from fastapi import APIRouter, Form, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from LLM.services import (
    call_openai_model,
    call_gemini_model,
    call_grok_model,
    call_deep_research_model,
)
from LLM.models import ModelRequest
from typing import Optional

router = APIRouter()
@router.post("/agent-call/{model_name}")
def agent_call(
    model_name: str,
    session_id: str = Form(...),
    prompt: str = Form(...),
    file: Optional[UploadFile] = File(None),
    project_id: Optional[int] = Form(None),
):
    req = ModelRequest(
        session_id=session_id,
        prompt=prompt,
        project_id=project_id,
        model_name=model_name,
    )
    req.file = file

    # 모델명에 따라 해당 서비스 함수 호출
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

## chat_router.py → save_chat() 호출
## chat_DB.py의 save_chat()에서 MySQL에 저장
@router.post("/save")
def save_chat_message(
    project_id: int = Form(...), 
    user_input: str = Form(...), 
    bot_output: str = Form(...),
    bot_name: str = Form(...)
    ):
    save_chat(project_id, user_input, bot_output, bot_name)
    return {"message": "✅ 채팅 저장 완료 ✅"}


@router.get("/list")
def get_chat_history(project_id: int):
    chats = get_chats(project_id)
    return {"chats": chats}



