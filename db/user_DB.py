from sqlalchemy import text
from backend.db.connection import user_engine


### DB 연결 확인
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
            );"""))
        conn.commit()
        print("✅ users 테이블 초기화 완료! ✅")
    except Exception as e:
        print("❌ user_db 연결 Error! ❌", e)
    

## 사용자 정보 저장
def save_user(email: str, name: str, picture: str):
    query = text("""
                insert into users (email, name, picture)
                values (:email, :name, :picture)
                on duplicate key update 
                    name = values(name),
                    picture = values(picture);
                 """)
    
    try:
        with user_engine.connect() as conn:
            conn.execute(query, {"email" : email, "name" : name, "picture" : picture})
            conn.commit()
        print(f"✅ 사용자 {email} 저장 완료! ✅")
        
    except Exception as e:
        print("❌ 사용자 저장 중 Error! ❌", e)