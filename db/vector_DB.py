import os, uuid, shutil, traceback

import os
import uuid
import shutil
import traceback

from chromadb import PersistentClient
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from dotenv import load_dotenv
load_dotenv()


## ChromaDB 기본 디렉토리 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Chroma 저장 디렉토리 (project_router와 통일)
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")


## 공통 임베딩 모델
EMBED_MODEL = "text-embedding-ada-002"


## --------------------------- 텍스트를 일정 길이로 분할 ---------------------------
def chunk_text(text: str, chunk_size=800, overlap=100):
    chunks = []
    start = 0
    """
    긴 텍스트를 chunk 단위로 분할
    """

    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunks.append(text[start:end])
        start += (chunk_size - overlap)

    return chunks


## --------------------------- 벡터 저장 (임베딩 생성) ---------------------------

def add_vectors(project_id: int, text: str):
    try:
        persist_dir = f"{CHROMA_DB_PATH}/{project_id}"
        os.makedirs(persist_dir, exist_ok=True)

        chunks = chunk_text(text)
        if not chunks:
            print("⚠️ 저장할 청크 없음")
            return False

        embedding_fn = OpenAIEmbeddings(model=EMBED_MODEL)

        db = Chroma(
            embedding_function=embedding_fn,
            persist_directory=persist_dir
        )

        ids = [str(uuid.uuid4()) for _ in chunks]
        db.add_texts(chunks, ids=ids)

        print(f"✅ 프로젝트 {project_id}: 임베딩 {len(chunks)}개 저장 완료")
        return True

    except Exception as e:
        print(f"❌ 벡터 저장 실패: {e}")
        traceback.print_exc()
        return False


## --------------------------- 벡터 검색 ---------------------------
def search_context(project_id: int, query: str, top_k: int = 3):
    persist_dir = f"{CHROMA_DB_PATH}/{project_id}"

    if not os.path.exists(persist_dir):
        print(f"❌ 프로젝트 {project_id} 벡터 없음")
        return None

    try:
        embedding_fn = OpenAIEmbeddings(model=EMBED_MODEL)

        db = Chroma(
            embedding_function=embedding_fn,
            persist_directory=persist_dir
        )

        try:
            results = db.similarity_search(query, k=top_k)
        except Exception:
            return None

        if not results:
            return None
        
        return "\n\n".join([r.page_content for r in results])

    except Exception as e:
        print(f"❌ 검색 실패: {e}")
        traceback.print_exc()
        return None


## --------------------------- 벡터 삭제 ---------------------------
def delete_project_vectors(project_id: int):
    dir_path = f"{CHROMA_DB_PATH}/{project_id}"

    try:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
            print(f"🗑 프로젝트 {project_id} 벡터 삭제 완료")
        else:
            print("⚠️ 벡터 폴더 없음")

    except Exception as e:
        print("❌ 벡터 삭제 실패:", e)
        traceback.print_exc()

