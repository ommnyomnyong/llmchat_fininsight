
## 프로젝트 생성 및 조회
from fastapi import APIRouter, Form, Query
from fastapi.responses import JSONResponse
from backend.db.project_DB import create_project, get_projects_by_email, save_project_file, get_projects
# from backend.llm.LLM import embed_and_store
# import os

router = APIRouter()


## 새로운 프로젝트 생성
@router.post("/create")
def create_new_project(
    email: str = Form(...), 
    project_name: str = Form(...), 
    description: str = Form("")
    ):
    
    create_project(email, project_name, description)
    return {"message": f"✅ 프로젝트 '{project_name}' 생성 완료 ✅"}


# ## 파일 업로드
# @router.post("/upload")
# async def upload_project_file(
#     project_id: int = Form(...),
#     file: UploadFile = None
# ):
#     try:
#         # 1️⃣ 파일 저장
#         file_path = os.path.join(UPLOAD_DIR, file.filename)
#         with open(file_path, "wb") as f:
#             content = await file.read()
#             f.write(content)

#         # 2️⃣ 벡터화 및 FAISS 저장
#         embedding_id = embed_and_store(file_path)

#         # 3️⃣ DB에 파일 정보 저장
#         save_project_file(
#             project_id=project_id,
#             file_name=file.filename,
#             mime_type=file.content_type,
#             file_data=content,
#             file_path=file_path,
#             embedding_id=embedding_id
#         )

#         return {"message": f"✅ 파일 '{file.filename}' 업로드 및 벡터화 완료!"}

#     except Exception as e:
#         return JSONResponse(content={"error": str(e)}, status_code=500)

## 프로젝트 목록 불러오기
@router.get("/list")
def list_projects(email: str = Query(...)):
    projects = get_projects_by_email(email)
    if len(projects) == 0:
        return JSONResponse(content={"new_user": True, "projects": []}) ## 신규 사용자 프로젝트 없음
    return JSONResponse(content={"new_user": False, "projects": projects})  ## 기존 사용자 프로젝트 불러오기


## 삭제 API
@router.delete("/delete")
def delete_existing_project(project_id: int = Query(...)):
    delete_project(project_id)
    return {"message": f"🗑 프로젝트 {project_id} 삭제 완료! (관련 채팅 자동 삭제됨)"}
