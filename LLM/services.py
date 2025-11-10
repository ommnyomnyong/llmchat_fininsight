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

# 세션별 대화 이력을 임시 저장하는 딕셔너리
session_histories = {}
SESSION_TTL_SECONDS = 86400 # 세션 유지 시간(24h) / 세션 없을 경우 DB에서 최신순으로 채팅 내역 가져옴

# 세션이 없는 경우 DB에서 최신순으로 채팅 기록을 가져오도록
def get_or_create_session(request: Request, session_id):
    session_histories = request.app.state.session_histories
    now = time.time()
    if session_id not in session_histories or (now - session_histories[session_id]["last_access"]) > SESSION_TTL_SECONDS:
        messages = load_chat_history_from_db(session_id) or [{"role": "system", "content": "You are a helpful assistant."}]
        session_histories[session_id] = {"history": messages, "last_access": now}
    else:
        session_histories[session_id]["last_access"] = now
    return session_histories[session_id]["history"]

def append_message(request: Request, session_id, message):
    session_histories = request.app.state.session_histories
    session_histories[session_id]["history"].append(message)
    session_histories[session_id]["last_access"] = time.time()

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
    get_or_create_session(request, session_id)
    embedding = get_embedding_from_session(session_id)
    context_text = "참고 문서 내용 포함" if embedding else ""
    combined_prompt = f"{context_text}\n{prompt}" if context_text else prompt

    chat_id_user = save_chat(session_id, combined_prompt, "", "unknown")
    session_histories[session_id]["history"].append({"id": chat_id_user, "role": "user", "content": combined_prompt})
    api_url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    payload = {
        "model": "gpt-4o",
        "messages": session_histories[session_id]["history"],
        "max_tokens": 8192,
        "stream": True
    }
    response = requests.post(api_url, headers=headers, json=payload, stream=True)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="AI 모델 호출 실패")
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
        chat_id_ai = save_chat(session_id, prompt, answer, "openai")
        session_histories[session_id]["history"].append({
            "id": chat_id_ai, "role": "assistant", "content": answer, "bot_name": "openai"
        })
    return StreamingResponse(event_generator(), media_type="text/plain")

# Gemini 모델 호출 함수
def call_gemini_model(request: Request, req):
    session_histories = request.app.state.session_histories
    session_id = req.session_id
    prompt = req.prompt
    get_or_create_session(request, session_id)
    embedding = get_embedding_from_session(session_id)
    context_text = "참고 문서 내용 포함" if embedding else ""
    combined_prompt = f"{context_text}\n{prompt}" if context_text else prompt
    chat_id_user = save_chat(session_id, combined_prompt, "", "unknown")
    session_histories[session_id]["history"].append({"id": chat_id_user, "role": "user", "content": combined_prompt})

    gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}
    payload = {"contents": [{"parts": [{"text": combined_prompt}]}]}
    response = requests.post(gemini_url, headers=headers, params=params, json=payload)
    print("\n[DEBUG] Gemini status:", response.status_code)
    print("[DEBUG] Gemini raw response type:", type(response.text))
    print("[DEBUG] Gemini raw response:", response.text)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Gemini API 호출 실패")
    try:
        data = response.json()
        print("[DEBUG] data after .json():", type(data), data)
        # dict 타입 체크 및 키 체크
        if not isinstance(data, dict):
            raise Exception(f"Gemini 응답이 dict가 아님: {data}")
        if 'candidates' not in data or not isinstance(data['candidates'], list):
            raise Exception(f"Gemini candidates key 오류: {data}")
        parts = data["candidates"][0]["content"]["parts"]
        answer = "".join(p.get("text", "") for p in parts)
    except Exception as e:
        print("[DEBUG] Gemini 파싱 에러 발생! 원본 응답:", response.text)
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Gemini 응답 파싱 실패: {str(e)}")
    chat_id_ai = save_chat(session_id, prompt, answer, "gemini")
    session_histories[session_id]["history"].append({
        "id": chat_id_ai, "role": "assistant", "content": answer, "bot_name": "gemini"
    })
    return answer


def call_grok_model(request: Request, req):
    session_histories = request.app.state.session_histories
    session_id = req.session_id
    prompt = req.prompt
    get_or_create_session(request, session_id)
    embedding = get_embedding_from_session(session_id)
    context_text = "참고 문서 내용 포함" if embedding else ""
    combined_prompt = f"{context_text}\n{prompt}" if context_text else prompt
    chat_id_user = save_chat(session_id, combined_prompt, "", "unknown")
    session_histories[session_id]["history"].append({"id": chat_id_user, "role": "user", "content": combined_prompt})
    api_url = "https://api.grok.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROK_API_KEY}"}
    payload = {
        "model": "grok-1",
        "messages": session_histories[session_id]["history"],
        "max_tokens": 8192,
        "stream": True
    }
    response = requests.post(api_url, headers=headers, json=payload, stream=True)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Grok API 호출 실패")
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
    get_or_create_session(request, session_id)
    embedding = get_embedding_from_session(session_id)
    context_text = "참고 문서 내용 포함" if embedding else ""
    combined_prompt = f"{context_text}\n{prompt}" if context_text else prompt
    chat_id_user = save_chat(session_id, combined_prompt, "", "unknown")
    session_histories[session_id]["history"].append({"id": chat_id_user, "role": "user", "content": combined_prompt})
    try:
        if getattr(req, "model_name", "") == "gemini-research":
            api_url = "https://api.gemini.ai/v1/responses"
            headers = {"Authorization": f"Bearer {GEMINI_API_KEY}"}
            payload = {
                "input": combined_prompt,
                "model": "gemini-2.5-pro",
                "tools": [{"type": "web_search_preview"}],
                "session_id": session_id
            }
            response = requests.post(api_url, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            result = response.json()
            if "error" in result:
                raise HTTPException(status_code=500, detail=f"Gemini API error: {result['error']}")
            answer = result.get("output_text") or (result.get("output", [{}])[0].get("text") if "output" in result else "No response.")
            chat_id_ai = save_chat(session_id, combined_prompt, answer, "gemini-research")
            session_histories[session_id]["history"].append({
                "id": chat_id_ai, "role": "assistant", "content": answer, "bot_name": "gemini-research"
            })
            return {"model": payload["model"], "answer": answer, "history": session_histories[session_id]["history"]}
        else:
            api_url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
            payload = {
                "model": "gpt-4o-search-preview",
                "messages": session_histories[session_id]["history"],
                "max_tokens": 8192,
                "stream": True
            }
            response = requests.post(api_url, headers=headers, json=payload, stream=True, timeout=30)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="OpenAI API call failed")
            def event_generator():
                answer = ""
                for line in response.iter_lines():
                    if line:
                        try:
                            line_str = line.decode('utf-8').strip()
                            if line_str == "data: [DONE]":
                                break
                            if line_str.startswith("data: "):
                                json_str = line_str[len("data: ") :]
                                json_line = json.loads(json_str)
                                token = json_line['choices'][0].get('delta', {}).get('content', '')
                                answer += token
                                yield token
                        except Exception:
                            continue
                chat_id_ai = save_chat(session_id, combined_prompt, answer, "openai-research")
                session_histories[session_id]["history"].append({
                    "id": chat_id_ai, "role": "assistant", "content": answer, "bot_name": "openai-research"
                })
            return StreamingResponse(event_generator(), media_type="text/plain")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Deep Research model call failed: {str(e)}")


def update_session_history(request: Request, session_id: str, chat_id: int, new_user_input: str, new_bot_output: str):
    session_histories = request.app.state.session_histories
    if session_id not in session_histories:
        raise ValueError("Invalid session_id")

    chat_list = session_histories[session_id]
    updated = False

    for i, chat in enumerate(chat_list):
        if not isinstance(chat, dict):
            print(f"[WARNING] chat_list[{i}] is not dict: {chat}")
            continue  # 타입이 잘못된 경우 skip
        if chat.get("id") == chat_id:
            # 해당 메시지 수정
            if chat.get("role") == "user":
                chat_list[i]["content"] = new_user_input
            # AI 답변 메시지는 같은 chat_id+1 등 별도 메시지라고 가정하여 처리 가능
            if i + 1 < len(chat_list) and isinstance(chat_list[i + 1], dict) and chat_list[i + 1].get("role") == "assistant":
                chat_list[i + 1]["content"] = new_bot_output
            updated = True
            break
    if not updated:
        raise ValueError("Chat message not found in session")
    # 변경 반영
    session_histories[session_id] = chat_list

