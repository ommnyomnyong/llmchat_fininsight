import os
## DB 연결만 담당
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
load_dotenv()

# DB 접속 정보
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT') or '3306'  # 환경변수 미설정 시 기본값 사용

# 각각의 DB명 (환경변수에 지정, 미지정 시 기본값)
USER_DB_NAME = os.getenv('USER_DB_NAME', 'user_db')
PROJECT_DB_NAME = os.getenv('PROJECT_DB_NAME', 'project_db')
CHAT_DB_NAME = os.getenv('CHAT_DB_NAME', 'chat_db')

# 임시 엔진으로 DB 3개 생성
base_engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/", echo=True)
for db_name in [USER_DB_NAME, PROJECT_DB_NAME, CHAT_DB_NAME]:
    with base_engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{db_name}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"))
        conn.commit()

# 각각의 엔진으로 개별 DB 연결
user_engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{USER_DB_NAME}", echo=True, pool_recycle=1800,
    pool_pre_ping=True
)
project_engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{PROJECT_DB_NAME}", echo=True, pool_recycle=1800,
    pool_pre_ping=True
)
chat_engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{CHAT_DB_NAME}", echo=True, pool_recycle=1800,
    pool_pre_ping=True
)