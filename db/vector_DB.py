import os, chromadb, traceback, uuid, shutil
from chromadb.config import Settings
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings


## ChromaDB 기본 디렉토리 설정
CHROMA_BASE_DIR = "backend/vector_store"
os.makedirs(CHROMA_BASE_DIR, exist_ok=True)

## ChromaDB 클라이언트 초기화
chroma_client = chromadb.Client(Settings(
    persist_directory=CHROMA_BASE_DIR,
    anonymized_telemetry=False
))

## 임베딩 모델 (검색용)
# embed_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


## --------------------------- 텍스트를 일정 길이로 분할 ---------------------------
def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100):
    """
    긴 문서를 일정 길이로 분할 (임베딩 효율성 향상)
    """
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


## --------------------------- 벡터 추가 (임베딩 생성 및 저장) ---------------------------
def add_vectors(project_id: int, text: str, file_name: str = None):
    """
    프로젝트별 문서 텍스트를 임베딩 후 ChromaDB에 저장
    """
    
    try:
        # 프로젝트별 디렉토리
        persist_dir = f"{CHROMA_BASE_DIR}/{project_id}"
        os.makedirs(persist_dir, exist_ok=True)

        # 텍스트 분할
        chunks = chunk_text(text)
        if not chunks:
            print(f"⚠️ 프로젝트 {project_id}: 저장할 텍스트 없음 ⚠️")
            return False

        # OpenAI Embedding 모델 (LangChain용)
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

        # Chroma VectorStore 생성 (프로젝트별 persist_directory)
        db = Chroma(
            persist_directory=persist_dir,
            embedding_function=embeddings
        )

        ## 각 청크를 ID와 함께 추가
        ids = [f"{file_name or 'chunk'}_{uuid.uuid4()}" for _ in chunks]
        db.add_texts(chunks, ids=ids)

        print(f"✅ 프로젝트 {project_id} 벡터 {len(chunks)}개 저장 완료 ✅")
        return True
    
    except Exception as e:
        print(f"❌ 프로젝트 {project_id} 임베딩 생성 실패:❌", e)
        traceback.print_exc()       # --- 에러가 났을 때 원인, 위치를 콘솔에 출력
        return False


## --------------------------- 벡터 검색 ---------------------------
def search_context(project_id: int, query: str, top_k: int = 3):
    """
    프로젝트 내 문맥 검색 (질문 텍스트 반환)
    """
    persist_dir = os.path.join(CHROMA_BASE_DIR, str(project_id))
    
    ## 프로젝트별 벡터 저장소가 존재하지 않으면
    if not os.path.exists(persist_dir):
        print(f"❌ 프로젝트 {project_id} 컬렉션 없음 (임베딩 미생성) ❌")
        return None

    try:
        # 검색용 임베딩
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        db = Chroma(persist_directory=persist_dir, embedding_function=embeddings)

        # 질의 기반 검색
        results = db.similarity_search(query, k=top_k)


        # 검색 결과 로그
        if not results:
            print(f"❌ 프로젝트 {project_id}: 검색 결과 없음 ❌")
            return None

        # 검색된 문서 내용 결합
        context = "\n\n".join([r.page_content for r in results])
        print(f"🔍 프로젝트 {project_id}: {len(results)}개 문맥 반환")
        return context

    except Exception as e:
        print(f"❌ 프로젝트 {project_id} 검색 실패: ❌", e)
        traceback.print_exc()
        return None



## --------------------------- 벡터 삭제 ---------------------------
def delete_project_vectors(project_id: int):
    """
    프로젝트 삭제 시 해당 프로젝트 벡터 데이터 전체 제거
    """
    persist_dir = f"{CHROMA_BASE_DIR}/{project_id}"
   
    try:
        if os.path.exists(persist_dir):
            shutil.rmtree(persist_dir)  # 폴더 + 내부의 모든 하위 파일까지 한 번에 삭제 가능
            print(f"✅ 프로젝트 {project_id} 벡터 삭제 완료 ✅")
            
        else:
            print(f"⚠️ 프로젝트 {project_id} 폴더 없음 — 삭제 생략 ⚠️")
            
    except Exception as e:
        print(f"❌ 프로젝트 {project_id} 벡터 삭제 실패: ❌", e)
        traceback.print_exc()

