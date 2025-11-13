from fastapi import APIRouter, Form, File, UploadFile, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import Optional, Union
from db.chat_DB import save_chat, get_chats, update_chat, get_chat_by_id
from LLM.services import (
    call_openai_model, call_gemini_model, call_grok_model,
    call_deep_research_model, update_session_history
)
from LLM.models import ModelRequest

router = APIRouter()

@router.post("/agent-call/{model_name}")
async def agent_call(
    request: Request,
    model_name: str,
    session_id: str = Form(...),
    prompt: str = Form(...),
    chat_id: Optional[int] = Form(None),
    project_id: Optional[int] = Form(None),
    file: Optional[Union[UploadFile, str]] = File(None)
):
    session_histories = request.app.state.session_histories
    try:
        text_from_file = None
        if isinstance(file, str) and file == "":
            file = None
        if file and getattr(file, "filename", None):
            content = file.file.read()
            file.file.seek(0)
            from LLM.file_embeddings import extract_text_from_file
            text_from_file = extract_text_from_file(content, file.filename)
            if not text_from_file:
                return "죄송합니다. 파일을 확인할 수 없습니다."
        new_prompt = f"{text_from_file}\n{prompt}" if text_from_file else prompt

        req = ModelRequest(
            session_id=session_id, prompt=new_prompt,
            project_id=project_id, model_name=model_name
        )

        if model_name == "openai":
            ai_response = call_openai_model(request, req)
        elif model_name == "gemini":
            ai_response = call_gemini_model(request, req)
        elif model_name == "grok":
            ai_response = call_grok_model(request, req)
        elif model_name in ["openai-research", "gemini-research"]:
            ai_response = call_deep_research_model(request, req)
        else:
            raise HTTPException(status_code=400, detail="지원하지 않는 모델입니다")

        # Gemini 계열은 답변이 문자열(str), 나머지는 딕셔너리(dict)
        if model_name == "grok":
            return ai_response         # StreamingResponse 바로 반환

        if model_name.startswith("gemini"):
            answer = ai_response
        else:
            answer = ai_response["answer"] if isinstance(ai_response, dict) else str(ai_response)

        # 채팅 내용 저장/수정
        if chat_id:
            update_session_history(session_id, chat_id, new_prompt, answer)
        print('[DEBUG] session_histories[session_id]:', session_histories.get(session_id))
        print('[DEBUG] chat_id:', chat_id)  # 넘어온 값
        # else:
        #     update_session_history(session_id, None, new_prompt, answer)

        # # 세션 기록 최신화 - 여기서도 answer(str)로 통일해서 넘겨야 오류 없음
        # update_session_history(session_id, chat_id, new_prompt, answer)
        return answer
    except Exception as e:
        import traceback
        traceback_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
        print(f"[ERROR] Exception in agent_call:\n{traceback_str}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.post("/save")
def save_chat_message(
    session_id: str = Form(...),
    user_input: str = Form(...),
    bot_output: str = Form(...),
    bot_name: str = Form(...),
    project_id: Optional[int] = Form(None)
):
    save_chat(session_id, user_input, bot_output, bot_name, project_id)
    return {"message": "✅ 채팅 저장 완료 ✅"}

@router.get("/list")
def get_chat_history(
    session_id: Optional[str] = None,
    project_id: Optional[int] = None
):
    if session_id:
        chats = get_chats(session_id=session_id)
    elif project_id:
        chats = get_chats(project_id=project_id)
    else:
        raise HTTPException(status_code=400, detail="session_id 또는 project_id를 입력하세요.")
    return {"chats": chats}
