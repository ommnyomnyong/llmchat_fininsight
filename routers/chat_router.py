## 채팅 저장 및 불러오기
import traceback
from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from db.chat_DB import save_chat, get_chats, update_chat, get_chat_by_id
from fastapi import APIRouter, Form, File, UploadFile, HTTPException, status
from fastapi.responses import StreamingResponse
from LLM.services import (
    call_openai_model,
    call_gemini_model,
    call_grok_model,
    call_deep_research_model,
    update_session_history
)
from LLM.models import ModelRequest
from typing import Optional, Union

router = APIRouter()

# 1. 채팅 수정 및 AI 재호출 API
@router.post("/agent-call/{model_name}")
def agent_call(
    model_name: str,
    session_id: str = Form(...),
    prompt: str = Form(...),
    chat_id: Optional[int] = Form(None),
    file: Optional[Union[UploadFile, str]] = File(None),
    project_id: Optional[str] = Form(None),
):
    try:
        # 2. 파일 처리 (업로드 파일이 있으면 텍스트 추출)
        text_from_file = None
        if isinstance(file, str) and file == "":
            file = None
        if file is not None and getattr(file, "filename", None):
            content = file.file.read()
            file.file.seek(0)
            from LLM.file_embeddings import extract_text_from_file
            text_from_file = extract_text_from_file(content, file.filename)
            if not text_from_file:
                return "죄송합니다. 파일을 열어서 내용을 확인할 수 없기 때문에 요약해 드릴 수 없습니다."
        else:
            text_from_file = None
        
        # 3. project_id 처리 및 타입 변환
        if project_id:
            try:
                project_id_int = int(project_id)
            except Exception:
                raise HTTPException(status_code=400, detail="project_id must be an integer")
        else:
            project_id_int = None
        

        # 4. 수정 요청 처리: 기존 채팅 내용 조회 후 새 프롬프트 생성
        if chat_id:
            old_chat = get_chat_by_id(chat_id)  # chat_DB.py에 구현 필요
            if old_chat is None:
                raise HTTPException(status_code=404, detail="Chat not found")
            # 기존 프롬프트 혹은 파일 텍스트와 사용자가 수정한 prompt를 적절히 조합
            # 예) 새로운 프롬프트는 수정된 prompt + 파일 내용 등
            new_prompt = f"{text_from_file}\n{prompt}" if text_from_file else prompt
        else:
            new_prompt = f"{text_from_file}\n{prompt}" if text_from_file else prompt

        # 5. ModelRequest 생성
        req = ModelRequest(
            session_id=session_id,
            prompt=new_prompt,
            project_id=project_id_int,
            model_name=model_name,
        )

        # 6. AI 모델 호출
        if model_name == "openai":
            ai_response = call_openai_model(req)
        elif model_name == "gemini":
            ai_response = call_gemini_model(req)
        elif model_name == "grok":
            ai_response = call_grok_model(req)
        elif model_name in ["openai-research", "gemini-research"]:
            ai_response = call_deep_research_model(req)
        else:
            raise HTTPException(status_code=400, detail="지원하지 않는 모델입니다")

        # 7. DB 업데이트 혹은 신규 저장
        if chat_id:
            update_chat(chat_id, prompt, ai_response["answer"])
        else:
            save_chat(project_id_int, prompt, ai_response["answer"], model_name)

        # 8. 세션 기록 동기화 - session_histories 수정
        update_session_history(session_id, chat_id, prompt, ai_response["answer"])

        # 9. 결과 반환
        return ai_response

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



