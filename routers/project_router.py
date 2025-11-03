
## 프로젝트 생성 및 조회
from fastapi import APIRouter, Form, Query
from fastapi.responses import JSONResponse
from backend.db.project_DB import create_project, get_projects

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


## 프로젝트 목록 불러오기
@router.get("/list")
def list_projects(email: str = Query(...)):
    projects = get_projects(email)
    if len(projects) == 0:
        return JSONResponse(content={"new_user": True, "projects": []}) ## 신규 사용자 프로젝트 없음
    return JSONResponse(content={"new_user": False, "projects": projects})  ## 기존 사용자 프로젝트 불러오기