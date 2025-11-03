from sqlalchemy import text
from backend.db.connection import engine

## 채팅 테이블 생성
def init_chat_table():
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS chats (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    project_id INT,
                    user_input TEXT,
                    bot_output TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                );
            """))
            conn.commit()
        print("✅ chats 테이블 생성 완료! ✅")
    
    except Exception as e:
        print("❌ chats 테이블 Error! ❌", e)

## 채팅 저장
def save_chat(project_id: int, user_input: str, bot_output: str):
    query = text("""
        INSERT INTO chats (project_id, user_input, bot_output)
        VALUES (:project_id, :user_input, :bot_output)
    """)
    with engine.connect() as conn:
        conn.execute(query, {
            "project_id": project_id,
            "user_input": user_input,
            "bot_output": bot_output
        })
        conn.commit()

## 채팅 불러오기
def get_chats(project_id: int):
    query = text("""
        SELECT user_input, bot_output, created_at
        FROM chats
        WHERE project_id = :project_id
        ORDER BY created_at ASC;
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"project_id": project_id}).fetchall()
    return [dict(row._mapping) for row in result]
