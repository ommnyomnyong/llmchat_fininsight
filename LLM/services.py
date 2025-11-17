import time
import numpy as np
import os
import requests
from dotenv import load_dotenv
from fastapi import HTTPException, Request
from fastapi.responses import StreamingResponse
import json
import traceback
from fastapi import UploadFile
import tiktoken

from db.chat_DB import save_chat, load_chat_history_from_db
from .file_embeddings import (
    extract_text_from_file,
    embed_texts,
    save_embedding_to_session,
    get_embedding_from_session,
)


load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROK_API_KEY = os.getenv("GROK_API_KEY")

SESSION_TTL_SECONDS = 86400 # 세션 유지 시간(24h) / 세션 없을 경우 DB에서 최신순으로 채팅 내역 가져옴

### 세션 관리 및 토큰 제한 처리
MODEL_MAX_TOKENS = {
    "openai-gpt4o": 8192,
    "gemini-2.5-pro": 4096,
    "grok-4": 2048,
    "deep-research": 4096,
}

# 토크나이저 캐시
tokenizer_cache = {}
# 모델명에 따른 토크나이저 반환
def get_tokenizer(model_name: str):
    model_key = None
    for key in MODEL_MAX_TOKENS.keys():
        if key in model_name.lower():
            model_key = key
            break
    if model_key is None:
        model_key = "openai-gpt4o"

    if model_key not in tokenizer_cache:
        # tiktoken encoding 인스턴스 생성 (모델명에 맞는 인코딩 불러오기)
        # OpenAI에서는 GPT-4o, GPT-4 등 모두 'cl100k_base' 인코딩 사용
        # 필요시 모델명에 따라 분기 처리가능
        tokenizer_cache[model_key] = tiktoken.encoding_for_model("gpt-4o")
    return tokenizer_cache[model_key]

def count_tokens(text: str, tokenizer) -> int:
    tokens = tokenizer.encode(text)
    return len(tokens)

# 대화 이력을 최대 토큰 수에 맞게 제한
def limit_history_by_tokens(history, max_tokens, tokenizer):
    limited_history = []
    token_count = 0

    for msg in reversed(history):
        content = msg.get("content", "")
        tokens = count_tokens(content, tokenizer)
        if token_count + tokens > max_tokens:
            break
        limited_history.append(msg)
        token_count += tokens

    return list(reversed(limited_history))

def get_max_tokens_for_model(model_name: str) -> int:
    for key in MODEL_MAX_TOKENS.keys():
        if key in model_name.lower():
            return MODEL_MAX_TOKENS[key]
    return 1000

# 세션이 없는 경우 DB에서 최신순으로 채팅 기록을 가져오도록
def get_or_create_session(request: Request, session_id: str):
    session_histories = request.app.state.session_histories
    now = time.time()
    if session_id not in session_histories or (now - session_histories[session_id]["last_access"]) > SESSION_TTL_SECONDS:
        messages = load_chat_history_from_db(session_id) or [{"role": "system", "content": "You are a helpful assistant."}]
        session_histories[session_id] = {"history": messages, "last_access": now}
    else:
        session_histories[session_id]["last_access"] = now
    return session_histories[session_id]["history"]

def prepare_messages_for_model(request: Request, session_id: str, model_name: str):
    history = get_or_create_session(request, session_id)
    max_tokens = get_max_tokens_for_model(model_name)
    tokenizer = get_tokenizer(model_name)
    limited_history = limit_history_by_tokens(history, max_tokens, tokenizer)
    return limited_history

def chat_handler(request: Request, req):
    session_histories = request.app.state.session_histories
    session_id = req.session_id
    prompt = req.prompt
    file = getattr(req, "file", None)
    if session_id not in session_histories:
        session_histories[session_id] = {"history": [{"role": "system", "content": "You are a helpful assistant."}], "last_access": time.time()}
    if file:
        file_bytes = file.file.read()
        text = extract_text_from_file(file_bytes, file.filename)
        if text:
            embeddings = embed_texts([text])
            save_embedding_to_session(session_id, embeddings[0])
    embedding = get_embedding_from_session(session_id)
    context_text = "참고 문서 내용 포함" if embedding else ""
    combined_prompt = f"{context_text}\n{prompt}" if context_text else prompt
    session_histories[session_id]["history"].append({"role": "user", "content": combined_prompt})
    return combined_prompt, session_id

def call_openai_model(request: Request, req):
    session_histories = request.app.state.session_histories
    session_id = req.session_id
    prompt = req.prompt
    model_name = "openai-gpt4o"  

    # 세션 이력 토큰 제한 적용하여 메시지 준비
    messages = prepare_messages_for_model(request, session_id, model_name)

    # 새 사용자 메시지 추가
    messages.append({"role": "user", "content": prompt})
    # 첫 메시지이면 제목 생성 로직 실행
    if len(messages) == 1:
        chat_title = generate_chat_title(session_id, prompt)
        # 제목 저장: DB 저장 함수나 세션 내 별도 필드에 저장 가능
        print(f"[INFO] 세션 {session_id} 제목 생성: {chat_title}")
    # 세션 이력 업데이트 및 타임스탬프 갱신
    session_histories[session_id]["history"] = messages
    session_histories[session_id]["last_access"] = time.time()

    # 사용자 메시지 DB 저장
    chat_id_user = save_chat(session_id, prompt, "", "unknown")

    api_url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    payload = {
        "model": "gpt-4o",
        "messages": messages,
        "max_tokens": 8192,
        "stream": True
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload, stream=True, timeout=30)
        if response.status_code != 200:
            try:
                err_msg = response.json().get('error', {}).get('message', response.text)
            except Exception:
                err_msg = response.text
            raise HTTPException(status_code=response.status_code, detail=f"OpenAI 호출 실패: {err_msg}")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"OpenAI 네트워크 오류: {str(e)}")

    def event_generator():
        answer = ""
        for line in response.iter_lines():
            if line:
                try:
                    json_line = json.loads(line.decode('utf-8').replace("data: ", ""))
                    token = json_line['choices'][0].get('delta', {}).get('content', '')
                    answer += token
                    yield token
                except Exception:
                    continue
        # AI 응답 DB 저장
        chat_id_ai = save_chat(session_id, prompt, answer, "openai")
        session_histories[session_id]["history"].append({
            "id": chat_id_ai,
            "role": "assistant",
            "content": answer,
            "bot_name": "openai"
        })

    return StreamingResponse(event_generator(), media_type="text/plain")

# Gemini 모델 호출 함수
def call_gemini_model(request: Request, req):
    session_histories = request.app.state.session_histories
    session_id = req.session_id
    prompt = req.prompt
    model_name = "gemini-2.5-pro"

    # 세션 이력 토큰 제한 적용, 토크나이저 사용
    messages = prepare_messages_for_model(request, session_id, model_name)
    # 첫 메시지이면 제목 생성 로직 실행
    if len(messages) == 1:
        chat_title = generate_chat_title(session_id, prompt)
        # 제목 저장: DB 저장 함수나 세션 내 별도 필드에 저장 가능
        print(f"[INFO] 세션 {session_id} 제목 생성: {chat_title}")
    # 새 사용자 메시지 추가
    messages.append({"role": "user", "content": prompt})

    # 세션 상태 갱신
    session_histories[session_id]["history"] = messages
    session_histories[session_id]["last_access"] = time.time()

    # 사용자 메시지 DB 저장
    chat_id_user = save_chat(project_id=None, session_id=session_id, user_input=prompt, bot_output="", bot_name="unknown")

    gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent"
    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(gemini_url, headers=headers, params=params, json=payload, timeout=120)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Gemini API 호출 실패")
        data = response.json()
        if not isinstance(data, dict) or 'candidates' not in data or not isinstance(data['candidates'], list):
            raise Exception(f"Gemini 응답 형식 오류: {data}")
        parts = data["candidates"][0]["content"]["parts"]
        answer = "".join(p.get("text", "") for p in parts)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Gemini 응답 파싱 실패: {str(e)}")

    # AI 답변 DB 저장 및 세션에 추가
    chat_id_ai = save_chat(session_id, prompt, answer, "gemini")
    session_histories[session_id]["history"].append({
        "id": chat_id_ai, "role": "assistant", "content": answer, "bot_name": "gemini"
    })
    return answer

# def call_gemini_model(request: Request, req):
#     session_histories = request.app.state.session_histories
#     session_id = req.session_id
#     prompt = req.prompt
#     get_or_create_session(request, session_id)
#     embedding = get_embedding_from_session(session_id)
#     context_text = "참고 문서 내용 포함" if embedding else ""
#     combined_prompt = f"{context_text}\n{prompt}" if context_text else prompt
#     chat_id_user = chat_id_user = save_chat(
#                                     project_id=None,
#                                     session_id=session_id,
#                                     user_input=combined_prompt,
#                                     bot_output="",
#                                     bot_name="unknown"
#                                 )
#     session_histories[session_id]["history"].append({"id": chat_id_user, "role": "user", "content": combined_prompt})

#     gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent"
#     headers = {"Content-Type": "application/json"}
#     params = {"key": GEMINI_API_KEY}
#     payload = {"contents": [{"parts": [{"text": combined_prompt}]}]}
#     response = requests.post(gemini_url, headers=headers, params=params, json=payload)
#     print("\n[DEBUG] Gemini status:", response.status_code)
#     print("[DEBUG] Gemini raw response type:", type(response.text))
#     print("[DEBUG] Gemini raw response:", response.text)
#     if response.status_code != 200:
#         raise HTTPException(status_code=response.status_code, detail="Gemini API 호출 실패")
#     try:
#         data = response.json()
#         print("[DEBUG] data after .json():", type(data), data)
#         # dict 타입 체크 및 키 체크
#         if not isinstance(data, dict):
#             raise Exception(f"Gemini 응답이 dict가 아님: {data}")
#         if 'candidates' not in data or not isinstance(data['candidates'], list):
#             raise Exception(f"Gemini candidates key 오류: {data}")
#         parts = data["candidates"][0]["content"]["parts"]
#         answer = "".join(p.get("text", "") for p in parts)
#     except Exception as e:
#         print("[DEBUG] Gemini 파싱 에러 발생! 원본 응답:", response.text)
#         import traceback
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail=f"Gemini 응답 파싱 실패: {str(e)}")
#     chat_id_ai = save_chat(session_id, prompt, answer, "gemini")
#     session_histories[session_id]["history"].append({
#         "id": chat_id_ai, "role": "assistant", "content": answer, "bot_name": "gemini"
#     })
#     return answer

def call_grok_model(request: Request, req):
    session_histories = request.app.state.session_histories
    session_id = req.session_id
    prompt = req.prompt
    model_name = "grok-4"

    # 세션 이력 제한 + 토크나이저
    messages = prepare_messages_for_model(request, session_id, model_name)
    messages.append({"role": "user", "content": prompt})
    # 첫 메시지이면 제목 생성 로직 실행
    if len(messages) == 1:
        chat_title = generate_chat_title(session_id, prompt)
        # 제목 저장: DB 저장 함수나 세션 내 별도 필드에 저장 가능
        print(f"[INFO] 세션 {session_id} 제목 생성: {chat_title}")
    session_histories[session_id]["history"] = messages
    session_histories[session_id]["last_access"] = time.time()

    chat_id_user = save_chat(session_id, prompt, "", "unknown")

    api_url = "https://api.x.ai/v1/chat/completions"
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Grok(xAI) API Key 미설정")

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "grok-4",
        "messages": messages,
        "max_tokens": 2048,
        "stream": True
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload, stream=True, timeout=120)
        if response.status_code != 200:
            try:
                err_json = response.json()
            except Exception:
                err_json = response.text
            raise HTTPException(status_code=response.status_code,
                detail=f"Grok(xAI) API 호출 실패 (status {response.status_code}): {err_json}")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Grok(xAI) 네트워크 예외: {str(e)}")

    def event_generator():
        answer = ""
        for line in response.iter_lines():
            if line:
                try:
                    json_line = json.loads(line.decode('utf-8').replace("data: ", ""))
                    token = json_line['choices'][0].get('delta', {}).get('content', '')
                    answer += token
                    yield token
                except Exception:
                    continue
        chat_id_ai = save_chat(session_id, prompt, answer, "grok")
        session_histories[session_id]["history"].append({
            "id": chat_id_ai, "role": "assistant", "content": answer, "bot_name": "grok"
        })

    return StreamingResponse(event_generator(), media_type="text/plain")


# def call_grok_model(request: Request, req):
#     session_histories = request.app.state.session_histories
#     session_id = req.session_id
#     prompt = req.prompt
#     get_or_create_session(request, session_id)
#     embedding = get_embedding_from_session(session_id)
#     context_text = "참고 문서 내용 포함" if embedding else ""
#     combined_prompt = f"{context_text}\n{prompt}" if context_text else prompt
#     chat_id_user = save_chat(session_id, combined_prompt, "", "unknown")
#     session_histories[session_id]["history"].append({"id": chat_id_user, "role": "user", "content": combined_prompt})

#     # 공식 API 엔드포인트와 모델명
#     api_url = "https://api.x.ai/v1/chat/completions"
#     api_key = os.getenv("XAI_API_KEY")
#     if not api_key:
#         print("[DEBUG] XAI_API_KEY 환경변수가 설정되지 않았습니다!")
#         raise HTTPException(status_code=500, detail="Grok(xAI) API Key 미설정")
#     headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
#     # 메시지 배열에서 불필요한 필드는 제외
#     messages = [
#         {"role": m["role"], "content": m["content"]}
#         for m in session_histories[session_id]["history"]
#     ]
#     payload = {
#         "model": "grok-4",           # 최신 최상위 모델
#         "messages": messages,
#         "max_tokens": 2048,           # 필요시 조정
#         "stream": True
#     }
#     print("[DEBUG] 요청 URL:", api_url)
#     print("[DEBUG] 헤더:", headers)
#     print("[DEBUG] Payload:", json.dumps(payload, ensure_ascii=False)[:800])

#     try:
#         response = requests.post(api_url, headers=headers, json=payload, stream=True, timeout=120)
#         print("[DEBUG] 응답 Status:", response.status_code)
#         print("[DEBUG] 응답 Body:", response.text[:500])
#         if response.status_code != 200:
#             try:
#                 err_json = response.json()
#             except Exception:
#                 err_json = response.text
#             print("[ERROR] 상세 에러:", err_json)
#             raise HTTPException(status_code=response.status_code,
#                 detail=f"Grok(xAI) API 호출 실패 (status {response.status_code}): {err_json}")
#     except requests.exceptions.RequestException as e:
#         print("[EXCEPTION] 네트워크 오류:", str(e))
#         raise HTTPException(status_code=500, detail=f"Grok(xAI) 네트워크 예외: {str(e)}")

#     def event_generator():
#         answer = ""
#         for line in response.iter_lines():
#             if line:
#                 try:
#                     json_line = json.loads(line.decode('utf-8').replace("data: ", ""))
#                     # Grok의 스트리밍 포맷은 OpenAI와 동일함
#                     token = json_line['choices'][0].get('delta', {}).get('content', '')
#                     answer += token
#                     yield token
#                 except Exception as e:
#                     print("[STREAM ERROR]", str(e))
#                     continue
#         chat_id_ai = save_chat(session_id, prompt, answer, "grok")
#         session_histories[session_id]["history"].append({
#             "id": chat_id_ai, "role": "assistant", "content": answer, "bot_name": "grok"
#         })
#     return StreamingResponse(event_generator(), media_type="text/plain")


def call_grok_model(request: Request, req):
    session_histories = request.app.state.session_histories
    session_id = req.session_id
    prompt = req.prompt
    model_name = "grok-4"

    # 세션 이력 제한 + 토크나이저
    messages = prepare_messages_for_model(request, session_id, model_name)
    messages.append({"role": "user", "content": prompt})

    session_histories[session_id]["history"] = messages
    session_histories[session_id]["last_access"] = time.time()

    chat_id_user = save_chat(session_id, prompt, "", "unknown")

    api_url = "https://api.x.ai/v1/chat/completions"
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Grok(xAI) API Key 미설정")

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "grok-4",
        "messages": messages,
        "max_tokens": 2048,
        "stream": True
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload, stream=True, timeout=120)
        if response.status_code != 200:
            try:
                err_json = response.json()
            except Exception:
                err_json = response.text
            raise HTTPException(status_code=response.status_code,
                detail=f"Grok(xAI) API 호출 실패 (status {response.status_code}): {err_json}")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Grok(xAI) 네트워크 예외: {str(e)}")

    def event_generator():
        answer = ""
        for line in response.iter_lines():
            if line:
                try:
                    json_line = json.loads(line.decode('utf-8').replace("data: ", ""))
                    token = json_line['choices'][0].get('delta', {}).get('content', '')
                    answer += token
                    yield token
                except Exception:
                    continue
        chat_id_ai = save_chat(session_id, prompt, answer, "grok")
        session_histories[session_id]["history"].append({
            "id": chat_id_ai, "role": "assistant", "content": answer, "bot_name": "grok"
        })

    return StreamingResponse(event_generator(), media_type="text/plain")


def call_deep_research_model(request: Request, req):
    session_histories = request.app.state.session_histories
    session_id = req.session_id
    prompt = req.prompt
    model_name = "gemini-research"  # 예시

    # 세션 이력 제한 + 토크나이저
    messages = prepare_messages_for_model(request, session_id, model_name)

    base_deep_research_prompt = (
        "You are an AI research assistant. Use the document search results "
        "to provide accurate and relevant answers. If the user's input lacks "
        "necessary information, ask clarifying questions to gather more details "
        "before answering. Base your responses strictly on available evidence "
        "and reasoning."
    )

    context_text = None
    embedding = get_embedding_from_session(session_id)
    if embedding:
        context_text = "참고 문서 내용 포함"

    combined_prompt = f"{base_deep_research_prompt}\n{context_text}\n{prompt}" if context_text else f"{base_deep_research_prompt}\n{prompt}"

    # 사용자 요청 DB 저장
    chat_id_user = save_chat(project_id=None, session_id=session_id, user_input=prompt, bot_output="", bot_name="unknown")

    # 메시지 배열에 요청 추가
    messages.append({"role": "user", "content": combined_prompt})

    # 세션 이력 갱신
    session_histories[session_id]["history"] = messages
    session_histories[session_id]["last_access"] = time.time()

    try:
        if getattr(req, "model_name", "") == "gemini-research":
            api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent"
            headers = {"Content-Type": "application/json"}
            params = {"key": GEMINI_API_KEY}
            payload = {"contents": [{"parts": [{"text": combined_prompt}]}]}
            response = requests.post(api_url, headers=headers, params=params, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()


            print(f"[DEBUG] HTTP 상태코드: {response.status_code}")
            print(f"[DEBUG] 응답 헤더: {response.headers}")

            try:
                response.raise_for_status()
            except Exception as http_err:
                print("[ERROR] HTTP 오류 발생!")
                print(f"[ERROR] HTTP 오류 메시지: {http_err}")
                print(f"[ERROR] 응답 본문: {response.text}")
                raise

            result = response.json()
            print(f"[DEBUG] API 응답 JSON: {result}")

            if not isinstance(result, dict):
                print("[ERROR] 응답이 dict 타입이 아님!")
                print(f"[ERROR] 원본 응답: {result}")
                raise Exception(f"Gemini 응답이 dict가 아님: {result}")

            if "quotaExceeded" in result:
                print("[ERROR] 쿼터 초과 감지됨!")
                raise HTTPException(status_code=429, detail="API 사용량(비용/쿼터) 초과입니다.")

            if "error" in result:
                print(f"[ERROR] API 에러 메시지: {result['error']}")
                raise HTTPException(status_code=500, detail=f"Gemini 오류: {result['error']}")

            if "output_text" in result:
                answer = result["output_text"]
            elif "candidates" in result and result["candidates"]:
                parts = result["candidates"][0].get("content", {}).get("parts", [])
                answer = "".join(part.get("text", "") for part in parts)
            else:
                answer = "No response."
                print("[WARN] 예상치 못한 응답 포맷, 답변 없음")

        else:
            print("[ERROR] 지원하지 않는 모델 호출 시도")
            raise HTTPException(status_code=400, detail="지원하지 않는 모델입니다.")
    except Exception as e:
        print("\n[EXCEPTION] Deep Research 모델 호출 중 예외 발생!")
        print(f"[EXCEPTION] 예외 타입: {type(e)}")
        print(f"[EXCEPTION] 예외 메시지: {str(e)}")
        print("[EXCEPTION] 전체 트레이스백:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Deep Research model call failed: {str(e)}")

    # AI 응답 DB 저장 및 세션 업데이트
    chat_id_ai = save_chat(project_id=None, session_id=session_id, user_input=combined_prompt, bot_output=answer, bot_name="gemini-research")
    session_histories[session_id]["history"].append({
        "id": chat_id_ai, "role": "assistant", "content": answer, "bot_name": "gemini-research"
    })

    return answer

# def call_deep_research_model(request: Request, req):
#     session_histories = request.app.state.session_histories
#     session_id = req.session_id
#     prompt = req.prompt
#     get_or_create_session(request, session_id)
#     embedding = get_embedding_from_session(session_id)
#     context_text = "참고 문서 내용 포함" if embedding else ""

#     base_deep_research_prompt = (
#         "You are an AI research assistant. Use the document search results "
#         "to provide accurate and relevant answers. If the user's input lacks "
#         "necessary information, ask clarifying questions to gather more details "
#         "before answering. Base your responses strictly on available evidence "
#         "and reasoning."
#     )
#     combined_prompt = f"{base_deep_research_prompt}\n{context_text}\n{prompt}" if context_text else f"{base_deep_research_prompt}\n{prompt}"

#     # DB 저장: 사용자 요청
#     chat_id_user = save_chat(project_id=None, session_id=session_id, user_input=prompt, bot_output="", bot_name="unknown")
#     session_histories[session_id]["history"].append({"id": chat_id_user, "role": "user", "content": combined_prompt})

#     try:
#         if getattr(req, "model_name", "") == "gemini-research":
#             api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent"
#             headers = {"Content-Type": "application/json"}
#             params = {"key": GEMINI_API_KEY}
#             payload = {
#                 "contents": [{"parts": [{"text": combined_prompt}]}]
#             }
#             response = requests.post(api_url, headers=headers, params=params, json=payload, timeout=120)
#             try:
#                 response.raise_for_status()
#                 result = response.json()
#                 print("[DEBUG] Gemini API RESPONSE:", result)  # 전체 body 출력
#                 error_msg = None
#                 # 비용/쿼터 관련 디버깅
#                 if "usageInfo" in result:
#                     print("[DEBUG] Usage info:", result["usageInfo"])
#                 if "quotaExceeded" in result:
#                     print("[DEBUG] Quota exceeded:", result["quotaExceeded"])
#                     error_msg = "API 사용량(비용/쿼터) 초과입니다. 구글 콘솔에서 확인 요망."
#                 # 일반 에러 메시지
#                 if "error" in result:
#                     print("[DEBUG] Gemini ERROR MESSAGE:", result["error"])
#                     if isinstance(result["error"], dict):
#                         error_msg = result["error"].get("message", str(result["error"]))
#                     else:
#                         error_msg = str(result["error"])
#                 # 안전 정책 필터 디버깅
#                 if "safetyStatus" in result:
#                     print("[DEBUG] Safety status:", result["safetyStatus"])
#                     error_msg = "응답이 정책(안전) 필터에 의해 제한됨: " + str(result["safetyStatus"])
#                 # Gemini 응답 추출
#                 if "output_text" in result:
#                     answer = result["output_text"]
#                 elif "candidates" in result and result["candidates"]:
#                     # Gemini 2.5 응답 예시 (REST 구조)
#                     candidate = result["candidates"][0]
#                     # 구조 맞춰 'content'/'parts'/'text' 추출
#                     candidates_content = candidate.get("content", {})
#                     parts = candidates_content.get("parts", [])
#                     answer_candidates = [part.get("text","") for part in parts if "text" in part]
#                     answer = "\n".join(answer_candidates) if answer_candidates else "No response."
#                 elif "output" in result and len(result["output"]) > 0 and "text" in result["output"][0]:
#                     answer = result["output"][0]["text"]
#                 else:
#                     answer = "No response."
#                     if error_msg:
#                         print("[DEBUG] 정확한 원인:", error_msg)
#                         answer = f"No response. 원인: {error_msg}"
#             except Exception as e:
#                 print("[DEBUG] Gemini API Exception:", e)
#                 print("[DEBUG] Response text:", getattr(response, "text", "<no response>"))
#                 raise HTTPException(status_code=500, detail=f"Deep Research model call failed: {str(e)}")
#             # DB 저장: Gemini 답변
#             chat_id_ai = save_chat(project_id=None, session_id=session_id, user_input=combined_prompt, bot_output=answer, bot_name="gemini-research")
#             session_histories[session_id]["history"].append({
#                 "id": chat_id_ai, "role": "assistant", "content": answer, "bot_name": "gemini-research"
#             })
#             return answer  # 답변 텍스트만 반환
#         else:
#             raise HTTPException(status_code=400, detail="지원하지 않는 모델입니다.")
#     except Exception as e:
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail=f"Deep Research model call failed: {str(e)}")



# def update_session_history(request: Request, session_id: str, chat_id: int, new_user_input: str, new_bot_output: str):
#     session_histories = request.app.state.session_histories
#     if session_id not in session_histories:
#         raise ValueError("Invalid session_id")

#     chat_list = session_histories[session_id]
#     updated = False

#     for i, chat in enumerate(chat_list):
#         if not isinstance(chat, dict):
#             print(f"[WARNING] chat_list[{i}] is not dict: {chat}")
#             continue  # 타입이 잘못된 경우 skip
#         if chat.get("id") == chat_id:
#             # 해당 메시지 수정
#             if chat.get("role") == "user":
#                 chat_list[i]["content"] = new_user_input
#             # AI 답변 메시지는 같은 chat_id+1 등 별도 메시지라고 가정하여 처리 가능
#             if i + 1 < len(chat_list) and isinstance(chat_list[i + 1], dict) and chat_list[i + 1].get("role") == "assistant":
#                 chat_list[i + 1]["content"] = new_bot_output
#             updated = True
#             break
#     if not updated:
#         raise ValueError("Chat message not found in session")
#     # 변경 반영
#     session_histories[session_id] = chat_list




# # ----------------------------------------------
# #  통합 LLM 호출 래퍼 (project_router.py와 호환)
# # ---------------- OpenAI ----------------------
# def _call_openai_chat(model_name: str, prompt: str):
#     """OpenAI 모델 호출 (단순 응답 텍스트 반환)"""
#     try:
#         headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
#         payload = {
#             "model": model_name,
#             "messages": [
#                 {"role": "system", "content": "You are a helpful assistant."},
#                 {"role": "user", "content": prompt},
#             ],
#             "temperature": 0.7,
#         }

#         response = requests.post(
#             "https://api.openai.com/v1/chat/completions",
#             headers=headers,
#             json=payload,
#             timeout=30
#         )

#         if response.status_code != 200:
#             raise HTTPException(status_code=500, detail=f"OpenAI Error: {response.text}")

#         data = response.json()
#         return data["choices"][0]["message"]["content"].strip()

#     except Exception as e:
#         traceback.print_exc()
#         return f"❌ OpenAI 호출 실패: {str(e)}"


# # ---------------- Gemini ----------------
# def _call_gemini(prompt: str):
#     """Gemini Flash 호출"""
#     try:
#         if not GEMINI_API_KEY:
#             raise HTTPException(status_code=500, detail="Gemini API 키가 설정되지 않았습니다.")

#         gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
#         headers = {"Content-Type": "application/json"}
#         params = {"key": GEMINI_API_KEY}
#         payload = {"contents": [{"parts": [{"text": prompt}]}]}

#         response = requests.post(gemini_url, headers=headers, params=params, json=payload)
#         data = response.json()
#         parts = data["candidates"][0]["content"]["parts"]
#         return "".join(p.get("text", "") for p in parts)  # <-- 텍스트만 반환
#     except Exception as e:
#         traceback.print_exc()
#         return f"❌ Gemini 호출 실패: {str(e)}"


# # ---------------- Grok ----------------
# def _call_grok(prompt: str):
#     """Grok 모델 호출"""
#     try:
#         headers = {"Authorization": f"Bearer {GROK_API_KEY}"}
#         payload = {
#             "model": "grok-1",
#             "messages": [
#                 {"role": "system", "content": "You are a helpful assistant."},
#                 {"role": "user", "content": prompt},
#             ],
#         }

#         response = requests.post("https://api.grok.ai/v1/chat/completions", headers=headers, json=payload)
#         if response.status_code != 200:
#             raise HTTPException(status_code=500, detail=f"Grok API 오류: {response.text}")

#         data = response.json()
#         return data["choices"][0]["message"]["content"].strip()

#     except Exception as e:
#         traceback.print_exc()
#         return f"❌ Grok 호출 실패: {str(e)}"


# 채팅 내용 요약
def generate_chat_title(session_id: str, first_user_message: str) -> str:
    # OpenAI에 간단한 요약 요청하여 제목 생성 (동기 호출 예시)
    prompt = f"아래 대화를 한 문장으로 요약하여 제목으로 만들어줘:\n{first_user_message}"
    api_url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 20,
        "temperature": 0.5,
        "n": 1
    }
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()
        title = data["choices"][0]["message"]["content"].strip()
        # TODO: DB나 세션에 제목 저장하는 로직 추가 가능
        return title
    except Exception as e:
        print(f"[WARN] 제목 생성 실패: {str(e)}")
        return "제목 없음"


# ---------------- 통합 LLM 래퍼 ----------------
def call_llm(model_name: str, prompt: str, context_text: str = ""):
    """
    project_router.py에서 통합적으로 호출되는 LLM 래퍼
    model_name: 'openai', 'gemini', 'grok', 'deep' 중 하나
    prompt: 사용자 입력 텍스트
    context_text: 문서 검색 결과
    """
    full_prompt = f"{context_text}\n\n{prompt}" if context_text else prompt
    model_name_lower = model_name.lower()

    if "openai" in model_name_lower or "gpt" in model_name_lower:
        return _call_openai_chat("gpt-4o", full_prompt)

    elif "gemini" in model_name_lower:
        return _call_gemini(full_prompt)

    elif "grok" in model_name_lower:
        return _call_grok(full_prompt)

    elif "deep" in model_name_lower:
        return _call_openai_chat("gpt-4o-search-preview", full_prompt)

    else:
        raise ValueError(f"❌ 지원하지 않는 모델명입니다: {model_name}")

# 서버 초기화 시
def startup_event(app):
    app.state.session_histories = {}

# 주기적 오래된 세션 클린업 (별도 스케줄러 또는 백그라운드 태스크 권장)
def cleanup_sessions(app):
    now = time.time()
    to_delete = []
    for sid, val in app.state.session_histories.items():
        if (now - val["last_access"]) > SESSION_TTL_SECONDS:
            to_delete.append(sid)
    for sid in to_delete:
        del app.state.session_histories[sid]