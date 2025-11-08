"""
채팅에 파일 업로드 시 해당 내용을 텍스트 추출 >> 임베딩 하여 임시 세션에 저장(1h)
DB에 영구 저장하지 않고 세션으로 임시적으로만 저장
"""
import io
import os
from typing import Optional, List
import openai
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# PDF 텍스트 추출
from pdfminer.high_level import extract_text as extract_pdf_text

# 워드(.docx) 텍스트 추출
import docx2txt

# 이미지 OCR
from PIL import Image
import pytesseract

# 임시 세션 임베딩 저장소, {session_id: (embedding, timestamp)} 구조
session_embeddings = {}

# TTL 1시간(3600초)
EMBEDDING_TTL_SECONDS = 3600

# ----------------------- 텍스트 추출 -----------------------
def extract_text_from_file(file_bytes: bytes, file_name: str) -> Optional[str]:
    """
    PDF, DOCX, 이미지(png/jpg/jpeg/bmp)에서 텍스트 추출
    :param file_bytes: 업로드된 파일의 바이트 데이터
    :param file_name: 파일명 (확장자 구분용)
    :return: 추출된 텍스트 문자열 (없으면 None)
    """
    ext = file_name.split('.')[-1].lower()
    text = None

    try:
        if ext == "pdf":
            text = extract_pdf_text(io.BytesIO(file_bytes))
        elif ext in ["doc", "docx"]:
            text = docx2txt.process(io.BytesIO(file_bytes))
        elif ext in ["png", "jpg", "jpeg", "bmp"]:
            image = Image.open(io.BytesIO(file_bytes))
            text = pytesseract.image_to_string(image)
        else:
            # 지원하지 않는 확장자 예외처리
            text = None
    except Exception as e:
        print(f"Error extracting text from {file_name}: {e}")
        text = None

    if text and text.strip():
        return text.strip()
    return None

def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    OpenAI 임베딩 API를 통해 텍스트 리스트를 임베딩 벡터 리스트로 변환.

    :param texts: 임베딩할 텍스트 문자열 리스트
    :return: 각 텍스트별 임베딩 벡터 리스트
    """
    try:
        response = openai.Embedding.create(
            input=texts,
            model="text-embedding-ada-002"
        )
        embeddings = [item['embedding'] for item in response['data']]
        return embeddings
    except Exception as e:
        print(f"❌ 임베딩 생성 실패: {e} ❌")
        return []

# ----------------------- 세션 저장 / 로드 -----------------------
def save_embedding_to_session(session_id: str, embedding: List[float]):
     """세션 임시 저장"""
    session_embeddings[session_id] = (embedding, time.time())

def get_embedding_from_session(session_id: str) -> Optional[List[float]]:
    """세션에서 임베딩 불러오기 (1시간 TTL)"""
    data = session_embeddings.get(session_id)
    if not data:
        return None
    embedding, timestamp = data
    if time.time() - timestamp > EMBEDDING_TTL_SECONDS:
        # TTL 만료시 삭제
        del session_embeddings[session_id]
        return None
    return embedding
