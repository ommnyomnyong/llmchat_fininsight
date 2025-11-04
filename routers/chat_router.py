## 채팅 저장 및 불러오기
import traceback
from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from db.chat_DB import save_chat, get_chats
from fastapi import APIRouter, Form, File, UploadFile, HTTPException, status
from fastapi.responses import StreamingResponse
from LLM.services import (
    call_openai_model,
    call_gemini_model,
    call_grok_model,
    call_deep_research_model,
)
from LLM.models import ModelRequest
from typing import Optional, Union

router = APIRouter()

@router.post("/agent-call/{model_name}")
def agent_call(
    model_name: str,
    session_id: str = Form(...),
    prompt: str = Form(...),
    file: Optional[Union[UploadFile, str]] = File(None),
    project_id: Optional[str] = Form(None),
):
    try:
        text_from_file = None
        # 빈 문자열일 경우 None으로 변환
        if isinstance(file, str) and file == "":
            file = None
        if file is not None and getattr(file, "filename", None):
            content = file.file.read()
            file.file.seek(0)  # 파일 포인터 리셋
            from LLM.file_embeddings import extract_text_from_file
            text_from_file = extract_text_from_file(content, file.filename)
            if not text_from_file:
                return "죄송합니다. 파일을 열어서 내용을 확인할 수 없기 때문에 요약해 드릴 수 없습니다."
        else:
            # file이 None이거나 filename이 빈 값일 경우 처리
            text_from_file = None
        # project_id 문자열을 정수로 변환 시도
        if project_id:
            try:
                project_id_int = int(project_id)
            except Exception:
                raise HTTPException(status_code=400, detail="project_id must be an integer")
        else:
            project_id_int = None

        # 요청 객체 생성, 파일 텍스트는 req.prompt에 합치는 등 원하는 로직으로 활용 가능
        full_prompt = f"{text_from_file}\n{prompt}" if text_from_file else prompt
        req = ModelRequest(
            session_id=session_id,
            prompt=full_prompt,
            project_id=project_id_int,
            model_name=model_name,
        )

        # 실제 AI 모델 호출
        if model_name == "openai":
            return call_openai_model(req)
        elif model_name == "gemini":
            return call_gemini_model(req)
        elif model_name == "grok":
            return call_grok_model(req)
        elif model_name in ["openai-research", "gemini-research"]:
            return call_deep_research_model(req)
        else:
            raise HTTPException(status_code=400, detail="지원하지 않는 모델입니다")

    except Exception as e:
        import traceback
        traceback_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
        print(f"[ERROR] Exception in agent_call:\n{traceback_str}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

    
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



