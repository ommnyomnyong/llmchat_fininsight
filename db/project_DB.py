from sqlalchemy import text
from backend.db.connection import engine


## projects 테이블 생성 
def init_project_db():
    try:
        with engine.connect() as conn:
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
        with engine.connect() as conn:
            conn.execute(query, {
                "user_id": email,
                "project_name": project_name,
                "description": description
            })
            conn.commit()
        print(f"✅ 프로젝트 {project_name} 생성 완료! ✅")
        
    except Exception as e:
        print("❌ 프로젝트 생성 Error! ❌:", e)
        
        
## 기존 사용자의 프로젝트 목록 불러오기
def get_projects(email: str):
    query = text("SELECT id, title FROM projects WHERE email = :email")
    with engine.connect() as conn:
        result = conn.execute(query, {"email": email}).fetchall()
    return [dict(row._mapping) for row in result]


## 프로젝트 목록 조회
def get_projects():
    query = text("""SELECT id, project_name, created_at 
                 FROM projects 
                 ORDER BY created_at DESC""")
    with engine.connect() as conn:
        result = conn.execute(query).fetchall()
    return [dict(row._mapping) for row in result]