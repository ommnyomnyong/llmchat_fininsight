# project_DB.py
from sqlalchemy import text
from db.connection import project_engine


# ---------------------- DB 초기화 ----------------------
def init_project_db():
    try:
        with project_engine.connect() as conn:
            
            # 프로젝트 테이블
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS projects (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) NOT NULL,
                project_name VARCHAR(255),
                description TEXT,
                project_purpose TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """))

            # 파일 테이블
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS project_files (
                id INT AUTO_INCREMENT PRIMARY KEY,
                project_id INT,
                file_name VARCHAR(255),
                mime_type VARCHAR(255),
                file_path TEXT,
                file_size BIGINT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id)
                    ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """))

            # 프로젝트 챗 로그 테이블
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS project_chats (
                id INT AUTO_INCREMENT PRIMARY KEY,
                project_id INT,
                file_id INT NULL,
                user_input TEXT,
                bot_output TEXT,
                bot_name VARCHAR(100) DEFAULT 'unknown',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id)
                    ON DELETE CASCADE,
                FOREIGN KEY (file_id) REFERENCES project_files(id)
                    ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """))
            
            conn.commit()
        print("✅ projects / project_files / project_chats 테이블 생성 완료!")

    except Exception as e:
        print("❌ project_db 테이블 생성 오류:", e)


# ---------------------- 프로젝트 생성 ----------------------
def create_project(email: str, project_name: str, description: str, project_purpose: str):
    query = text("""
        INSERT INTO projects (email, project_name, description, project_purpose)
        VALUES (:email, :project_name, :description, :project_purpose)
    """)
    with project_engine.connect() as conn:
        result = conn.execute(query, {
            "email": email,
            "project_name": project_name,
            "description": description,
            "project_purpose": project_purpose
        })
        conn.commit()
        return result.lastrowid


# ---------------------- 프로젝트명 중복 확인 ----------------------
def get_project_info_by_name(project_name: str):
    query = text("""
        SELECT * FROM projects WHERE project_name = :name
    """)
    with project_engine.connect() as conn:
        result = conn.execute(query, {"name": project_name}).mappings().fetchone()
    return dict(result) if result else None


# ---------------------- 프로젝트 정보 불러오기 ----------------------
def get_project_info(project_id: int):
    query = text("SELECT * FROM projects WHERE id = :project_id")
    with project_engine.connect() as conn:
        result = conn.execute(query, {"project_id": project_id}).fetchone()
    return dict(result._mapping) if result else None


# ---------------------- 프로젝트 목록 ----------------------
def get_all_projects(email=None, order_by: str = "created_at DESC"):
    with project_engine.connect() as conn:
        if email:
            query = text(f"SELECT * FROM projects WHERE email = :email ORDER BY {order_by}")
            rows = conn.execute(query, {"email": email}).mappings().all()
        else:
            query = text(f"SELECT * FROM projects ORDER BY {order_by}")
            rows = conn.execute(query).mappings().all()

        return [dict(row) for row in rows]


# ---------------------- 프로젝트 이름 수정 ----------------------
def update_project_name(project_id: int, new_name: str):
    query = text("""
        UPDATE projects 
        SET project_name = :new_name
        WHERE id = :project_id
    """)
    with project_engine.begin() as conn:
        result = conn.execute(query, {
            "new_name": new_name,
            "project_id": project_id
        })
        return result.rowcount > 0


# ---------------------- 업로드 파일 목록 ----------------------
def get_project_files(project_id: int):
    query = text("""
        SELECT id, file_name, mime_type, file_path, file_size, created_at
        FROM project_files
        WHERE project_id = :project_id
    """)
    with project_engine.connect() as conn:
        result = conn.execute(query, {"project_id": project_id}).fetchall()

    return [dict(row._mapping) for row in result]


# ---------------------- 파일 저장 ----------------------
def save_project_file(project_id, file_name, mime_type, file_path, file_size):
    query = text("""
        INSERT INTO project_files (project_id, file_name, mime_type, file_path, file_size)
        VALUES (:project_id, :file_name, :mime_type, :file_path, :file_size)
    """)
    with project_engine.connect() as conn:
        conn.execute(query, {
            "project_id": project_id,
            "file_name": file_name,
            "mime_type": mime_type,
            "file_path": file_path,
            "file_size": file_size
        })
        conn.commit()


# ---------------------- 파일 레코드 삭제 (자동 삭제용) ----------------------
def delete_file_record(file_path: str):
    query = text("""
        DELETE FROM project_files 
        WHERE file_path = :file_path
    """)
    with project_engine.connect() as conn:
        conn.execute(query, {"file_path": file_path})
        conn.commit()


# ---------------------- 프로젝트 대화 저장 ----------------------
def save_project_chat(project_id, user_input, bot_output, model_name):
    query = text("""
        INSERT INTO project_chats (project_id, user_input, bot_output, bot_name)
        VALUES (:project_id, :user_input, :bot_output, :bot_name)
    """)
    with project_engine.connect() as conn:
        conn.execute(query, {
            "project_id": project_id,
            "user_input": user_input,
            "bot_output": bot_output,
            "bot_name": model_name
        })
        conn.commit()


# ---------------------- 프로젝트 대화 불러오기 ----------------------
def get_project_chats(project_id: int, limit: int = None):
    limit_clause = f"LIMIT {limit}" if limit else ""
    query = text(f"""
        SELECT id, project_id, user_input, bot_output, bot_name, created_at
        FROM project_chats
        WHERE project_id = :project_id
        ORDER BY id ASC
        {limit_clause}
    """)
    with project_engine.connect() as conn:
        result = conn.execute(query, {"project_id": project_id}).fetchall()

    return [dict(row._mapping) for row in result]


# ---------------------- 프로젝트 삭제 ----------------------
def delete_project(project_id: int):
    try:
        with project_engine.connect() as conn:
            conn.execute(text("""
                DELETE FROM projects
                WHERE id = :project_id
            """), {"project_id": project_id})
            conn.commit()

        return {"message": f"프로젝트(ID={project_id}) 삭제 완료"}

    except Exception as e:
        return {"error": f"❌ 삭제 중 오류 발생: {str(e)}"}
