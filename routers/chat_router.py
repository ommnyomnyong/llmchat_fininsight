from fastapi import APIRouter, Form, File, UploadFile, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import Optional, Union
from db.chat_DB import save_chat, get_chats, update_chat, get_chat_by_id
from LLM.services import (
    call_openai_model, call_gemini_model, call_grok_model,
    call_deep_research_model, generate_chat_title #update_session_history
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
    print(f"[DEBUG] session_id: {session_id!r}, prompt: {prompt!r}")

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
        # new_prompt 변수 기본값 먼저 할당
        new_prompt = f"{text_from_file}\n{prompt}" if text_from_file else prompt

        # 디버깅용 로그 – new_prompt 할당 후 출력
        print(f"[DEBUG] session_id: {session_id!r}")
        print(f"[DEBUG] prompt: {new_prompt!r}")

        # 모델명 강제 변환 (심층리서치 요청 시)
        if model_name in ["openai-research", "grok-research", "gemini-research"]:
            model_name = "grok-research"

        # ModelRequest 객체 생성 (반드시 변환된 model_name 으로)
        req = ModelRequest(
            session_id=session_id,
            prompt=new_prompt,
            project_id=project_id,
            model_name=model_name
        )

        if model_name == "openai":
            ai_response = call_openai_model(request, req)
        elif model_name == "gemini":
            ai_response = call_gemini_model(request, req)
        elif model_name == "grok":
            ai_response = call_grok_model(request, req)
        elif model_name in ["gemini-research", "grok-research", "openai-research"]:
            ai_response = call_deep_research_model(request, req)
        else:
            raise HTTPException(status_code=400, detail="지원하지 않는 모델입니다")

        # Gemini 계열은 문자열, 나머지는 dict 형태 처리
        if model_name == "grok":
            return ai_response  # StreamingResponse 바로 반환

        if model_name.startswith("gemini"):
            answer = ai_response
        else:
            answer = ai_response["answer"] if isinstance(ai_response, dict) else str(ai_response)

        # (주석 처리된) 채팅 내용 저장/수정 필요시 로직 활성화 가능
        # if chat_id:
        #     update_session_history(session_id, chat_id, new_prompt, answer)

        return answer

    except Exception as e:
        import traceback
        traceback_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
        print(f"[ERROR] Exception in agent_call:\n{traceback_str}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")



@router.post("/chat/{session_id}/generate-title")
async def generate_title_for_chat(
    session_id: str,
    first_user_message: str = Form(...)
):
    """
    세션 ID와 첫 사용자 메시지를 받아 간단 요약 제목 생성 후 반환
    """
    try:
        title = generate_chat_title(session_id, first_user_message)
        # 필요 시 DB에 제목 저장하는 로직 추가 가능
        return {"title": title}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"제목 생성 실패: {str(e)}")

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
