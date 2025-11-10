import os
## DB 연결만 담당
from sqlalchemy import create_engine

# DB 접속 정보
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT') or '3306'  # 환경변수 미설정 시 기본값 사용

USER_DB_NAME = os.getenv('USER_DB_NAME', 'user_db')
PROJECT_DB_NAME = os.getenv('PROJECT_DB_NAME', 'project_db')
CHAT_DB_NAME = os.getenv('CHAT_DB_NAME', 'chat_db')

# DB 연결
user_engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{USER_DB_NAME}", echo=True
)
project_engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{PROJECT_DB_NAME}", echo=True
)
chat_engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{CHAT_DB_NAME}", echo=True
)