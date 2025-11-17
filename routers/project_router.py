## 프로젝트 생성, 파일 업로드/삭제, 대화 기록 관리 등


from fastapi import APIRouter, Form, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import traceback, os, time
from apscheduler.schedulers.background import BackgroundScheduler

from typing import Optional

## DB 모듈
from db.vector_DB import add_vectors, delete_project_vectors, CHROMA_DB_PATH
from db.project_DB import (
    get_project_info, get_project_info_by_name, get_project_files, 
    get_project_chats, create_project, save_project_file, 
    save_project_chat, delete_project, get_all_projects, update_project_name)

## 파일 처리
from LLM.file_embeddings import extract_text_from_file
## LLM
from LLM.project_llm import call_project_llm


router = APIRouter()

BASE_UPLOAD_DIR = "backend/uploads"
BASE_VECTOR_DIR = CHROMA_DB_PATH    # 임베딩 위치 완전 통일

DELETE_AFTER_DAYS = 7    ## 업로드 된 파일 7일마다 자동 삭제

os.makedirs(BASE_UPLOAD_DIR, exist_ok=True)
os.makedirs(BASE_VECTOR_DIR, exist_ok=True)


## ---------------------- 새로운 프로젝트 생성 ----------------------
@router.post("/create")
def create_new_project(
    email: str = Form(...),     # ✅ 추가
    project_name: str = Form(...), 
    description: str = Form(""),
    project_purpose: str = Form("")   # ✅ 목적 필드 추가
    ):
    
    """
    프로젝트 생성 시:
    - 중복 이름 자동 처리 ("테스트" → "테스트(1)")
    - DB에 저장
    """

    try:
        # 기존 프로젝트에 중복된 이름 확인
        existing = get_project_info_by_name(project_name)
        
        # 중복 이름 처리
        if existing:
            base_name, suffix = project_name, 1

            # 이미 존재하는 이름 중 마지막 숫자를 찾아서 다음 번호 붙이기
            while get_project_info_by_name(f"{base_name}({suffix})"):
                suffix += 1

            project_name = f"{base_name}({suffix})"
        
        # 프로젝트 생성
        new_project_id = create_project(email, project_name, description, project_purpose)

        if not new_project_id:
            raise HTTPException(500, "프로젝트 생성 실패(DB 오류)")
        
        first_prompt = f"""
                        [프로젝트명]
                        {project_name}

                        [프로젝트 설명]
                        {description}

                        [프로젝트 목적]
                        {project_purpose}

                        위 내용을 기반으로 프로젝트 개요를 분석하고, 요약하세요.
                        """

        # gemini 기반 첫 메시지 생성
        first_answer = call_project_llm(
            model="grok",
            project_id=new_project_id,
            prompt=first_prompt
        )

        # 첫 대화 저장
        save_project_chat(
            project_id=new_project_id,
            user_input="",
            bot_output=first_answer,
            model_name="grok"
        )

        return {
            "message": f"프로젝트 '{project_name}' 생성 완료",
            "project_id": new_project_id,
            "project_name": project_name,
            "first_ai_message": first_answer    # 프론트에서 사용하는 필드명
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"❌ 프로젝트 생성 실패: {str(e)} ❌")


## ---------------------- 파일 업로드 및 벡터화 ----------------------
@router.post("/upload-file")
async def upload_project_file(
    project_id: int = Form(...),
    file: UploadFile = File(...)
):
    """
        파일 업로드 → 텍스트 추출 → 벡터화
    """
    try:
        project = get_project_info(project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"❌ 프로젝트 {project_id}가 존재하지 않습니다 ❌")
        
        
       # 이메일별 디렉토리 생성
        upload_dir = os.path.join(BASE_UPLOAD_DIR, str(project_id))
        os.makedirs(upload_dir, exist_ok=True)

        # 파일 저장
        file_bytes = await file.read()
        save_path = os.path.join(upload_dir, f"{project_id}_{file.filename}")
            
        with open(save_path, "wb") as f:
            f.write(file_bytes)

        
        ## 텍스트 추출
        text = extract_text_from_file(file_bytes, file.filename) 
        if not text or not text.strip():
            raise ValueError("❌ 텍스트 추출 실패 ❌")
        
       # 벡터화 (project_id 단위로 분리)
        add_vectors(project_id, text)
        
        # 파일 메타데이터 DB 저장
        save_project_file(
            project_id=project_id,
            file_name=file.filename,
            mime_type=file.content_type,
            file_path=save_path,
            file_size=len(file_bytes)
        )
        
        return {"message": f"파일 '{file.filename}' 업로드 및 임베딩 완료",
                "file_size":len(file_bytes)}
    
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"❌ 파일 업로드 실패: {str(e)} ❌")


## ---------------------- 대화 저장 및 LLM 호출 ----------------------
@router.post("/chat")
async def project_chat(
    project_id: int = Form(...),
    model_name: str = Form(...),
    user_input: str = Form(...),
    file: Optional[UploadFile] = File(None)
):
    
    """
    프로젝트 내부 대화:
    - 이전 대화(context) + 문서 검색 결과 포함
    - OpenAI / Gemini / Grok 중 선택적으로 모델 호출
    """
    
    try:
        project = get_project_info(project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"❌ 프로젝트 {project_id}가 존재하지 않습니다 ❌")
      
        
        # 파일 기반 문맥 추가
        file_text = ""
        if file:
            content = await file.read()
            file_text = extract_text_from_file(content, file.filename)

        context_text = f"[파일 내용]\n{file_text}\n\n" if file_text else ""

        answer = call_project_llm(
            model=model_name,
            project_id=project_id,
            prompt=context_text + user_input
        )
            

        return {"bot_output": answer}

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"❌ 대화 실패: {str(e)} ❌")


## ---------------------- 프로젝트별 대화/파일/정보 불러오기 ----------------------
@router.get("/chat/history")
def get_chat_history(project_id: int):

    """
    사용자가 프로젝트를 다시 열었을 때:
    프로젝트 기본 정보 + 업로드된 파일 + 과거 대화 JSON 반환
    """

    try:
        project = get_project_info(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="❌ 프로젝트를 찾을 수 없습니다 ❌")

        # 파일 목록
        files = get_project_files(project_id)

        # 대화 내용 (JSON)
        chats = get_project_chats(project_id)

        # 임베딩 여부
        vector_path = os.path.join(BASE_VECTOR_DIR, str(project_id))
        has_embedding = os.path.exists(vector_path) and len(os.listdir(vector_path)) > 0

        return {
            "project": project,
            "files": files,
            "chats": chats,  # 프론트에서 챗 내용이 이어서 표시 가능
            "embedding": {
                "exists": has_embedding,
                "path": vector_path
            }
        }
    
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"❌ 프로젝트 내용 불러오기 실패: {str(e)} ❌")


## ---------------------- 프로젝트 이름 수정 ----------------------
@router.put("/rename/{project_id}")
def rename_project(project_id: int, data: dict):
    new_name = data.get("project_name")
    if not new_name:
        raise HTTPException(status_code=400, detail="project_name 필요")

    success = update_project_name(project_id, new_name)
    if not success:
        raise HTTPException(status_code=404, detail="프로젝트 없음")

    # 메시지 대신 변경된 프로젝트 정보 반환
    return {"id": project_id, "project_name": new_name}

## ---------------------- 대화 저장 전용 ----------------------
@router.post("/chat/save")
async def save_chat_only(
    project_id: int = Form(...),
    user_input: str = Form(...),
    bot_output: str = Form(...),
):
    """
    프론트(ChatPage.jsx)에서 실시간 메시지 저장을 위해 사용하는 API
    LLM 호출용이 아니라 '대화 기록만 저장'하는 라우트
    """

    try:
        project = get_project_info(project_id)
        if not project:
            raise HTTPException(404, "프로젝트가 존재하지 않습니다.")

        save_project_chat(
            project_id, user_input, bot_output, "manual-save"
        )


        return {"status": "success"}

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"❌ 대화 저장 실패: {str(e)}")


## ---------------------- 파일 자동 삭제 ----------------------
def auto_delete_old_files():
    """
    일정 기간 지난 파일 자동 삭제
    """
    now = time.time()
    for root, _, files in os.walk(BASE_UPLOAD_DIR):
        for file in files:
            path = os.path.join(root, file)
            if now - os.path.getmtime(path) > DELETE_AFTER_DAYS * 86400:
                os.remove(path)
                print(f"🗑️ 자동 삭제 완료: {path}")

## 백그라운드 스케줄러 실행
scheduler = BackgroundScheduler()
scheduler.add_job(auto_delete_old_files, "interval", days=1) # 매일 1회 실행
scheduler.start()


## ---------------------- 전체 프로젝트 목록 (최신순) ----------------------
@router.get("/list")
def list_projects(email: Optional[str] = None):
    """
    로그인한 사용자의 프로젝트 목록을 최신순으로 반환
    """
    try:
        projects = get_all_projects(email, order_by="created_at DESC")
        return JSONResponse(content=jsonable_encoder(projects))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"❌ 프로젝트 목록 불러오기 실패: {str(e)} ❌")


## --------------------- 프로젝트 삭제(파일 + 대화 기록 등 모두 삭제) ----------------------
@router.delete("/delete/{project_id}")
def remove_project(project_id: int):
    
    """
    프로젝트 삭제 시:
    1. DB에서 프로젝트 + 연결된 파일 + 대화 삭제
    2. backend/uploads/ 로컬 내 파일 삭제
    3. 벡터DB 내 해당 프로젝트 벡터 삭제
    """
    try:
        project = get_project_info(project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"❌ 프로젝트 {project_id}가 존재하지 않습니다 ❌")
        
        # 파일 삭제
        files = get_project_files(project_id)
        for f in files:
            if os.path.exists(f["file_path"]):
                os.remove(f["file_path"])

        # 2. DB에서 프로젝트, 파일, 대화 기록 삭제
        delete_project(project_id)

        # 3. 벡터DB에서 해당 프로젝트 데이터 삭제
        delete_project_vectors(project_id)

        return {"message": f"프로젝트 {project_id} 삭제 완료"}

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"❌ 프로젝트 삭제 실패: {str(e)} ❌")
