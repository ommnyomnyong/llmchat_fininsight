from sqlalchemy import text
from db.connection import chat_engine

"""
기존 코드에서 수정한 내용 (인용 수정)
1. 채팅 기록 저장 시 사용한 AI 모델명도 함께 저장하도록 bot_name열 추가함
2. 프로젝트에 할당되어 있지 않은 채팅 기록을 프로젝트에 할당할 수 있도록 assign_chats_to_project 함수 추가함
"""

## 채팅 테이블 생성
def init_chat_table():
    try:
        with chat_engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS chats (
                id INT AUTO_INCREMENT PRIMARY KEY,
                project_id INT,
                user_input TEXT,
                bot_output TEXT,
                bot_name VARCHAR(100) NOT NULL DEFAULT 'unknown',  -- AI 모델명 저장용
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            );
            """))
            conn.commit()
        print("✅ chats 테이블 생성 완료! ✅")
    
    except Exception as e:
        print("❌ chats 테이블 Error! ❌", e)

## 채팅 저장
def save_chat(project_id: int | None, user_input: str, bot_output: str, bot_name: str = 'unknown'):
    query = text("""
        INSERT INTO chats (project_id, user_input, bot_output, bot_name)
        VALUES (:project_id, :user_input, :bot_output, :bot_name)
    """)
    with chat_engine.connect() as conn:
        conn.execute(query, {
            "project_id": project_id,
            "user_input": user_input,
            "bot_output": bot_output,
            "bot_name": bot_name
        })
        conn.commit()

# 채팅 기록을 프로젝트에 할당
def assign_chats_to_project(chat_ids: list[int], project_id: int):
    query = text("""
        UPDATE chats SET project_id = :project_id
        WHERE id IN :chat_ids
    """)
    with chat_engine.connect() as conn:
        conn.execute(query, {"project_id": project_id, "chat_ids": tuple(chat_ids)})
        conn.commit()

## 채팅 불러오기
def get_chats(project_id: int):
    query = text("""
        SELECT user_input, bot_output, created_at
        FROM chats
        WHERE project_id = :project_id
        ORDER BY created_at ASC;
    """)
    with chat_engine.connect() as conn:
        result = conn.execute(query, {"project_id": project_id}).fetchall()
    return [dict(row._mapping) for row in result]
