from sqlalchemy import text
from db.connection import user_engine

def init_db():
    try:
        with user_engine.connect() as conn:
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) UNIQUE,
                name VARCHAR(100),
                picture VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """))
            conn.commit()
        print("✅ users 테이블 초기화 완료!")
    except Exception as e:
        print("❌ user_db 연결 Error:", e)

def save_user(email: str, name: str, picture: str):
    query = text("""
        INSERT INTO users (email, name, picture)
        VALUES (:email, :name, :picture)
        ON DUPLICATE KEY UPDATE 
            name = VALUES(name),
            picture = VALUES(picture);
    """)
    try:
        with user_engine.connect() as conn:
            with conn.begin():  # ✅ 트랜잭션 시작
                conn.execute(query, {"email": email, "name": name, "picture": picture})
        print(f"✅ 사용자 {email} 저장 완료!")
    except Exception as e:
        print("❌ 사용자 저장 중 Error:", e)
    