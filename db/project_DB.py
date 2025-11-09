# project_DB.py
from sqlalchemy import text
from backend.db.connection import project_engine


## projects / project_files / project_chats 테이블 생성
def init_project_db():
    try:
        with project_engine.connect() as conn:
            
            # 프로젝트 테이블 ----- projects 테이블
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS projects (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) NOT NULL,
                project_name VARCHAR(255),
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """))

            # 파일 테이블 ----- project_files 테이블
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS project_files (
                id INT AUTO_INCREMENT PRIMARY KEY,
                project_id INT,
                file_name VARCHAR(255),
                mime_type VARCHAR(255),
                file_data LONGBLOB,
                file_path TEXT,
                file_size BIGINT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id)
                    ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """))

            conn.commit()
        print("✅ projects / files / chats 테이블 생성 완료! ✅")

    except Exception as e:
        print("❌ project_db 테이블 Error ❌:", e)


## ---------------------- 프로젝트 생성 ----------------------
def create_project(email: str, project_name: str, description: str):
    query = text("""
        INSERT INTO projects (email, project_name, description)
        VALUES (:email, :project_name, :description)
    """)
    with project_engine.connect() as conn:
        conn.execute(query, {
            "email": email,
            "project_name": project_name,
            "description": description
        })
        conn.commit()

## ---------------------- 프로젝트명 중복 확인 ----------------------
def get_project_info_by_name(project_name: str, email: str):
    query = text("""
                 SELECT * FROM projects WHERE project_name = :name AND email = :email
                 """)
    with project_engine.connect() as conn:
        result = conn.execute(query, {"name": project_name,  "email": email}).mappings().fetchone()
    return dict(result) if result else None


## ---------------------- 프로젝트 정보 불러오기 ----------------------
def get_project_info(project_id: int, email: str):
    with project_engine.connect() as conn:
        query = text("""
                     SELECT * FROM projects WHERE id = :project_id AND email = :email
                     """)
        result = conn.execute(query, {"project_id": project_id,  "email": email}).fetchone()

        return dict(result._mapping) if result else None


## ---------------------- 프로젝트 목록 ----------------------
def get_all_projects(email: str, order_by: str = "created_at DESC"):
    query = text(f"""
        SELECT * FROM projects WHERE email = :email ORDER BY {order_by}
    """)
    with project_engine.connect() as conn:
        result = conn.execute(query, {"email": email}).fetchall()
    return [dict(row._mapping) for row in result]



## ---------------------- 업로드 파일 목록 ----------------------
def get_project_files(project_id: int):
        query = text("""
            SELECT id, file_name, mime_type, file_path, created_at
            FROM project_files
            WHERE project_id = :project_id
            """)
        with project_engine.connect() as conn:
            result = conn.execute(query, {"project_id": project_id}).fetchall()
        return [dict(row._mapping) for row in result]


## ---------------------- 파일 저장 ----------------------
def save_project_file(project_id, file_name, mime_type, file_data, file_path):
    query = text("""
        INSERT INTO project_files (project_id, file_name, mime_type, file_data, file_path)
        VALUES (:project_id, :file_name, :mime_type, :file_data, :file_path)
    """)
    with project_engine.connect() as conn:
        conn.execute(query, {
            "project_id": project_id,
            "file_name": file_name,
            "mime_type": mime_type,
            "file_data": file_data,
            "file_path": file_path
        })
        conn.commit()



## ---------------------- 프로젝트 삭제(파일 + 대화 삭제) ----------------------
def delete_project(project_id: int, email: str):
    try:
        query = text("""
            DELETE FROM projects WHERE id = :project_id AND email = :email
            """)
        with project_engine.connect() as conn:
            conn.execute(query, {"project_id": project_id, "email": email})
            conn.commit()
            
        print(f"✅ 프로젝트 {project_id} 삭제 완료 (관련 대화 포함) ✅")
    except Exception as e:
        print("❌ 프로젝트 삭제 실패 ❌:", e)


