## 프로젝트 생성, 파일 업로드/삭제, 대화 기록 관리 등


from fastapi import APIRouter, Form, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

## DB 모듈
from backend.db.vector_DB import add_vectors, search_context, delete_project_vectors
from backend.db.project_DB import (
    get_project_info, get_project_info_by_name, get_project_files, get_project_chats,
    create_project, save_project_file, save_project_chat, delete_project, get_all_projects)

import traceback, os

## LLM
from backend.llm.models import extract_text_from_file, call_llm



router = APIRouter()

BASE_UPLOAD_DIR = "backend/uploads"
BASE_VECTOR_DIR = "backend/vector_store"

os.makedirs(BASE_UPLOAD_DIR, exist_ok=True)
os.makedirs(BASE_VECTOR_DIR, exist_ok=True)


## 새로운 프로젝트 생성
@router.post("/create")
def create_new_project(
    email: str = Form(...), 
    project_name: str = Form(...), 
    description: str = Form("")
    ):
    
    """
    프로젝트 생성 시:
    - 중복 이름 자동 처리 ("테스트" → "테스트(1)")
    - DB에 저장
    """

    try:
        # 기존 프로젝트에 중복된 이름 확인
        existing = get_project_info_by_name(project_name, email)
        
        # 중복 이름 처리
        if existing:
            base_name = project_name
            suffix = 1

            # 이미 존재하는 이름 중 마지막 숫자를 찾아서 다음 번호 붙이기
            while get_project_info_by_name(f"{base_name}({suffix})", email):
                suffix += 1

            project_name = f"{base_name}({suffix})"
        
        # 프로젝트 생성
        create_project(email, project_name, description)
        return {"message": f"✅ 프로젝트 '{project_name}' 생성 완료 ✅"}
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"❌ 프로젝트 생성 실패: {str(e)} ❌")


## 파일 업로드 및 벡터화 ------pdf, docx 지원
@router.post("/upload-file")
async def upload_project_file(
    email: str = Form(...),
    project_id: int = Form(...),
    file: UploadFile = File(...)
):
    
    """
        프로젝트 내부에서 파일 업로드 시:
            파일 저장 + 텍스트 추출 + 벡터화
    """
    try:
        project = get_project_info(project_id, email)
        if not project:
            raise HTTPException(status_code=404, detail=f"❌ 프로젝트 {project_id}가 존재하지 않습니다 ❌")
        
        
       # 이메일별 디렉토리 생성
        user_upload_dir = os.path.join(BASE_UPLOAD_DIR, email)
        os.makedirs(user_upload_dir, exist_ok=True)

        # 파일 저장
        file_bytes = await file.read()
        save_path = os.path.join(user_upload_dir, f"{project_id}_{file.filename}")
            
        with open(save_path, "wb") as f:
            f.write(file_bytes)

        ## 텍스트 추출
        text = extract_text_from_file(save_path) 
        if not text.strip():
            raise ValueError("❌ 텍스트 추출 실패 ❌")
        
       # 벡터화 (email + project_id 단위로 분리)
        add_vectors(email, project_id, text)
        
        # 파일 메타데이터 DB 저장
        save_project_file(project_id, email, file.filename, file.content_type, file_bytes, save_path)
        
        return {"message": f"✅ 파일 '{file.filename}' 업로드 및 벡터화 완료 ✅"}
    
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"❌ 파일 업로드 실패: {str(e)} ❌")



@router.post("/chat")
async def project_chat(
    email: str = Form(...),
    project_id: int = Form(...),
    model_name: str = Form(...),
    user_input: str = Form(...),
):
    
    """
    프로젝트 내부 대화:
    - 이전 대화(context) + 문서 검색 결과 포함
    - OpenAI / Gemini / Grok 중 선택적으로 모델 호출
    """
    
    try:
        project = get_project_info(project_id, email)
        if not project:
            raise HTTPException(status_code=404, detail=f"❌ 프로젝트 {project_id}가 존재하지 않습니다 ❌")
      
        
        # 최근 대화 불러오기
        history = get_project_chats(project_id, email, limit=5)  # 최근 5개만 --- limit 수정
        history_text = "\n".join([f"User: {h['user_input']}\nBot: {h['bot_output']}" for h in history])
        
        
        # 벡터 DB에서 문맥 검색 (있으면 참고용으로 추가)
        context = search_context(email, project_id, user_input)
        context_text = f"\n\n[참고 문서 내용]\n{context}" if context else ""


        # LLM에게 과거 대화 내용과 새 입력 함께 전달
        full_prompt = f"{history_text}\nUser: {user_input}\nBot:"
        answer = call_llm(model_name, full_prompt, context_text)


        # 대화 DB에 저장
        save_project_chat(project_id, email, user_input, answer, model_name)


        # 프론트로 반환 (바로 이어붙이기 가능)
        return JSONResponse(content={
            "project_id": project_id,
            "model_name": model_name,
            "user_input": user_input,
            "bot_output": answer
        })
    
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"❌ 대화 실패: {str(e)} ❌")



## 이전 대화 불러오기
@router.get("/chat/history")
def get_chat_history(project_id: int, email: str):

    """
    사용자가 프로젝트를 다시 열었을 때:
    프로젝트 기본 정보 + 업로드된 파일 + 과거 대화 JSON 반환
    """

    try:
        project = get_project_info(project_id, email)
        if not project:
            raise HTTPException(status_code=404, detail="❌ 프로젝트를 찾을 수 없습니다 ❌")

        # 파일 목록
        files = get_project_files(project_id, email)

        # 대화 내용 (JSON)
        chats = get_project_chats(project_id, email, as_text=False)

        # 임베딩 여부
        vector_path = f"{BASE_VECTOR_DIR}/{email}/{project_id}"
        has_embedding = os.path.exists(vector_path) and len(os.listdir(vector_path)) > 0

        response_data = {
            "project": project,
            "files": files,
            "chats": chats,  # 프론트에서 챗 내용이 이어서 표시 가능
            "embedding": {
                "exists": has_embedding,
                "path": vector_path if has_embedding else None
            }
        }

        return JSONResponse(content=jsonable_encoder(response_data))
    
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"❌ 프로젝트 내용 불러오기 실패: {str(e)} ❌")


## 전체 프로젝트 목록 (최신순)
@router.get("/list")
def list_projects(email: str):
    """
    프로젝트 목록을 최신순(created_at DESC)으로 반환
    """
    try:
        projects = get_all_projects(email=email, order_by="created_at DESC")
        return JSONResponse(content=jsonable_encoder(projects))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"❌ 프로젝트 목록 불러오기 실패: {str(e)} ❌")


## 프로젝트 삭제(파일 + 대화 기록 등 모두 삭제)
@router.delete("/delete/{project_id}")
def remove_project(project_id: int, email):
    
    """
    프로젝트 삭제 시:
    1. DB에서 프로젝트 + 연결된 파일 + 대화 삭제
    2. backend/uploads/ 로컬 내 파일 삭제
    3. 벡터DB 내 해당 프로젝트 벡터 삭제
    """
    try:
        project = get_project_info(project_id, email)
        if not project:
            raise HTTPException(status_code=404, detail=f"❌ 프로젝트 {project_id}가 존재하지 않습니다 ❌")
        
        # 파일 삭제
        files = get_project_files(project_id, email)
        for file_info in files:
            file_path = file_info.get("file_path")
            if file_path and os.path.exists(file_path):
                os.remove(file_path)

        # 2. DB에서 프로젝트, 파일, 대화 기록 삭제
        delete_project(project_id, email)

        # 3. 벡터DB에서 해당 프로젝트 데이터 삭제
        delete_project_vectors(project_id, email)

        return {"message": f"✅ 프로젝트 {project_id} 및 관련 데이터 전체 삭제 완료 ✅"}
    
    except HTTPException:
        raise

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"❌ 프로젝트 삭제 실패: {str(e)} ❌")
