from sqlalchemy import text
from db.connection import project_engine


## projects 테이블 생성 
def init_project_db():
    try:
        with project_engine.connect() as conn:
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS projects (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255),
                project_name VARCHAR(255),
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );"""))
            conn.commit()
        print("✅ projects 테이블 생성 완료! ✅")
        
    except Exception as e:
        print("❌ project_db 테이블 Error! ❌", e)
        

## 프로젝트 생성
def create_project(email : str, project_name : str, description : str):
    query = text("""
        INSERT INTO projects (email, project_name, description)
        VALUES (:user_id, :project_name, :description);
    """)
    try:
        with project_engine.connect() as conn:
            conn.execute(query, {
                "user_id": email,
                "project_name": project_name,
                "description": description
            })
            conn.commit()
        print(f"✅ 프로젝트 {project_name} 생성 완료! ✅")
        
    except Exception as e:
        print("❌ 프로젝트 생성 Error! ❌:", e)
        
        
# 기존 사용자 프로젝트 목록 조회용
def get_projects_by_email(email: str):
    query = text("""
        SELECT id, project_name, created_at
        FROM projects
        WHERE email = :email
        ORDER BY created_at DESC
    """)
    with project_engine.connect() as conn:
        result = conn.execute(query, {"email": email}).fetchall()
    return [dict(row._mapping) for row in result]


## 프로젝트 목록 조회
def get_projects():
    query = text("""SELECT id, project_name, created_at 
                 FROM projects 
                 ORDER BY created_at DESC""")
    with project_engine.connect() as conn:
        result = conn.execute(query).fetchall()
    return [dict(row._mapping) for row in result]


## 파일 저장
def save_project_file(project_id, file_name, mime_type, file_data, file_path, embedding_id):
    query = text("""
        INSERT INTO project_files (project_id, file_name, mime_type, file_data, file_path, embedding_id)
        VALUES (:project_id, :file_name, :mime_type, :file_data, :file_path, :embedding_id)
    """)
    with project_engine.connect() as conn:
        conn.execute(query, {
            "project_id": project_id,
            "file_name": file_name,
            "mime_type": mime_type,
            "file_data": file_data,
            "file_path": file_path,
            "embedding_id": embedding_id
        })
        conn.commit()

## 프로젝트 삭제 (연쇄 삭제 유도)
def delete_project(project_id: int):
    query = text("DELETE FROM projects WHERE id = :project_id")
    try:
        with project_engine.connect() as conn:
            conn.execute(query, {"project_id": project_id})
            conn.commit()
        print(f"✅ 프로젝트 {project_id} 삭제 완료 (관련 채팅 자동 삭제) ✅")
    except Exception as e:
        print("❌ 프로젝트 삭제 실패 ❌:", e)