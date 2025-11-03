## 채팅 저장 및 불러오기

from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from backend.db.chat_DB import save_chat, get_chats


router = APIRouter()
## chat_router.py → save_chat() 호출
## chat_DB.py의 save_chat()에서 MySQL에 저장
@router.post("/save")
def save_chat_message(
    project_id: int = Form(...), 
    user_input: str = Form(...), 
    bot_output: str = Form(...)
    ):
    save_chat(project_id, user_input, bot_output)
    return {"message": "✅ 채팅 저장 완료 ✅"}



@router.get("/list")
def get_chat_history(project_id: int):
    chats = get_chats(project_id)
    return {"chats": chats}

# @router.post("/chat")
# async def chat_with_doc(project_id: int = Form(...), user_input: str = Form(...)):
#     index = load_faiss_index()
#     query_vec = get_embedding(user_input)
#     D, I = index.search(np.array([query_vec]), k=3)

#     # 간단히, 임시로 관련 문서내용을 context로 전달
#     context = f"프로젝트 {project_id} 관련 문서에서 유사한 내용을 기반으로 답변을 작성해주세요."

#     response = genai.GenerativeModel("gemini-pro").generate_content(
#         f"{context}\n\n사용자 질문: {user_input}"
#     )

#     return {"response": response.text}

