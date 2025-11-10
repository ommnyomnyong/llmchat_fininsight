from sqlalchemy import text
from db.connection import chat_engine


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

## 채팅 저장 후 chat_id를 반한 >> session에도 chat_id를 동일하게 저장하기 위함
def save_chat(project_id: int | None, user_input: str, bot_output: str, bot_name: str = 'unknown'):
    query = text("""
        INSERT INTO chats (project_id, user_input, bot_output, bot_name) 
        VALUES (:project_id, :user_input, :bot_output, :bot_name)
    """)
    with chat_engine.connect() as conn:
        result = conn.execute(query, {
            "project_id": project_id,
            "user_input": user_input,
            "bot_output": bot_output,
            "bot_name": bot_name
        })
        conn.commit()
        # chat_id 반환
        try:
            chat_id = result.lastrowid
        except AttributeError:
            chat_id = result.inserted_primary_key[0]
        return chat_id

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
def get_chats(project_id: int | None = None):
    if project_id is None:
        # 프로젝트 할당 안 된 채팅만 조회
        query = text("""
            SELECT user_input, bot_output, created_at
            FROM chats
            WHERE project_id IS NULL
            ORDER BY created_at ASC;
        """)
        params = {}
    else:
        # 특정 프로젝트 채팅만 조회
        query = text("""
            SELECT user_input, bot_output, created_at
            FROM chats
            WHERE project_id = :project_id
            ORDER BY created_at ASC;
        """)
        params = {"project_id": project_id}
    with chat_engine.connect() as conn:
        result = conn.execute(query, params).fetchall()
    return [dict(row._mapping) for row in result]

## 채팅 수정하기
# 지정한 chat_id에 해당하는 채팅 기록(입력 및 출력, 프로젝트 ID 포함)을 DB에서 조회
def get_chat_by_id(chat_id: int):
    query = text("""
        SELECT id, user_input, bot_output, project_id
        FROM chats
        WHERE id = :chat_id
    """)
    with chat_engine.connect() as conn:
        result = conn.execute(query, {"chat_id": chat_id}).fetchone()
        if result:
            return dict(result._mapping)
        else:
            return None
        
# 지정한 chat_id에 해당하는 채팅 기록의 사용자 입력과 AI 출력 메시지를 수정
# 수정 시점(created_at)도 현재 시각으로 갱신
def update_chat(chat_id: int, new_user_input: str, new_bot_output: str):
    query = text("""
        UPDATE chats
        SET user_input = :new_user_input,
            bot_output = :new_bot_output,
            created_at = CURRENT_TIMESTAMP
        WHERE id = :chat_id
    """)
    with chat_engine.connect() as conn:
        conn.execute(query, {
            "new_user_input": new_user_input,
            "new_bot_output": new_bot_output,
            "chat_id": chat_id
        })
        conn.commit()
