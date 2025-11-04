import time
import numpy as np
import os
import requests
from dotenv import load_dotenv
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
import json
import traceback
from fastapi import UploadFile

from db.chat_DB import save_chat
from .file_embeddings import (
    extract_text_from_file,
    embed_texts,
    save_embedding_to_session,
    get_embedding_from_session,
)

"""
기존 코드에서 수정한 점: 
"""

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROK_API_KEY = os.getenv("GROK_API_KEY")

# 세션별 대화 이력을 임시 저장하는 딕셔너리
session_histories = {}

def chat_handler(req):
    session_id = req.session_id
    prompt = req.prompt
    file = getattr(req, "file", None)
    project_id = getattr(req, "project_id", None)

    if session_id not in session_histories:
        session_histories[session_id] = [{"role": "system", "content": "You are a helpful assistant."}]

    # 파일이 업로드 된 경우 텍스트 추출과 임베딩 수행
    if file:
        file_bytes = file.file.read()
        text = extract_text_from_file(file_bytes, file.filename)
        if text:
            embeddings = embed_texts([text])
            save_embedding_to_session(session_id, embeddings[0])

    embedding = get_embedding_from_session(session_id)
    context_text = "참고 문서 내용 포함" if embedding else ""

    combined_prompt = f"{context_text}\n{prompt}" if context_text else prompt
    session_histories[session_id].append({"role": "user", "content": combined_prompt})

    return combined_prompt, session_id, project_id

def call_openai_model(req):
    session_id = req.session_id
    prompt = req.prompt
    project_id = getattr(req, "project_id", None)

    if session_id not in session_histories:
        session_histories[session_id] = [{"role": "system", "content": "You are a helpful assistant."}]

    # 세션 임베딩 참조
    embedding = get_embedding_from_session(session_id)
    context_text = "참고 문서 내용 포함" if embedding else ""

    combined_prompt = f"{context_text}\n{prompt}" if context_text else prompt

    session_histories[session_id].append({"role": "user", "content": combined_prompt})

    api_url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    payload = {
        "model": "gpt-4o",
        "messages": session_histories[session_id],
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
        session_histories[session_id].append({"role": "assistant", "content": answer, "bot_name": "openai"})

        if project_id is not None:
            save_chat(project_id, prompt, answer, "openai")

    return StreamingResponse(event_generator(), media_type="text/plain")


def call_gemini_model(req):
    session_id = req.session_id
    prompt = req.prompt
    project_id = getattr(req, "project_id", None)

    if session_id not in session_histories:
        session_histories[session_id] = [{"role": "system", "content": "You are a helpful assistant."}]

    # 세션 임베딩 참조
    embedding = get_embedding_from_session(session_id)
    context_text = "참고 문서 내용 포함" if embedding else ""

    combined_prompt = f"{context_text}\n{prompt}" if context_text else prompt

    # 기존 세션 기록 뒤에 추가
    session_histories[session_id].append({"role": "user", "content": combined_prompt})

    gemini_api_url = "https://api.gemini.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GEMINI_API_KEY}"}
    payload = {
        "model": "gemini-2.5-flash",
        "messages": session_histories[session_id],
        "max_tokens": 8192,
        "stream": True
    }

    response = requests.post(gemini_api_url, headers=headers, json=payload, stream=True)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Gemini API 호출 실패")

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
        session_histories[session_id].append({"role": "assistant", "content": answer, "bot_name": "gemini"})

        if project_id is not None:
            save_chat(project_id, prompt, answer, "gemini")

    return StreamingResponse(event_generator(), media_type="text/plain")


def call_grok_model(req):
    session_id = req.session_id
    prompt = req.prompt
    project_id = getattr(req, "project_id", None)

    if session_id not in session_histories:
        session_histories[session_id] = [{"role": "system", "content": "You are a helpful assistant."}]

    # 세션 임베딩 참조
    embedding = get_embedding_from_session(session_id)
    context_text = "참고 문서 내용 포함" if embedding else ""

    # 기존 메시지 + 참고문서 포함
    messages = session_histories[session_id] + [{"role": "user", "content": f"{context_text}\n{prompt}"}]
    # 세션 히스토리에 업데이트
    session_histories[session_id] = [{"role": "system", "content": "You are a helpful assistant."}]
    for msg in messages:
        session_histories[session_id].append(msg)

    api_url = "https://api.grok.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROK_API_KEY}"}
    payload = {
        "model": "grok-1",
        "messages": session_histories[session_id],
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
        session_histories[session_id].append({"role": "assistant", "content": answer, "bot_name": "grok"})
        if project_id is not None:
            save_chat(project_id, prompt, answer, "grok")

    return StreamingResponse(event_generator(), media_type="text/plain")


def call_deep_research_model(req):
    session_id = req.session_id
    prompt = req.prompt
    project_id = getattr(req, "project_id", None)

    if session_id not in session_histories:
        session_histories[session_id] = [
                    {"role": "system",
                    "content": (
                        """
                        You are an expert deep research AI specialized in providing thorough, logical, and well-supported answers.\n
                        For every user query:\n"
                        - Carefully analyze the question and the information provided.\n
                        - If the information is insufficient or ambiguous, YOU MUST NOT answer immediately.\n
                        - Instead, ask clarifying and detailed follow-up questions to gather all necessary data.\n
                        - Only after receiving sufficient information, provide a thorough, step-by-step analysis.\n
                        - Use multiple reliable sources and provide citations when possible.\n
                        - Structure your answer with clear headings, bullet points, and summaries.\n
                        - Use formal, precise, and professional language aimed at decision makers and analysts.\n
                        - If you cannot proceed without more details, explicitly request them from the user.\n\n
                        Now, please analyze the following query comprehensively:\n
                        {user_query}
                        """
                    )}
]
    # 세션 임베딩 참조
    embedding = get_embedding_from_session(session_id)
    context_text = "Included reference document content:" if embedding else ""

    combined_prompt = f"{context_text}\n{prompt}" if context_text else prompt
    session_histories[session_id].append({"role": "user", "content": combined_prompt})

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

            session_histories[session_id].append({"role": "assistant", "content": answer, "bot_name": "gemini-research"})
            if project_id is not None:
                save_chat(project_id, combined_prompt, answer, "gemini-research")

            return {"model": payload["model"], "answer": answer, "history": session_histories[session_id]}
        else:
            api_url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
            payload = {
                "model": "gpt-4o-search-preview",
                "messages": session_histories[session_id],
                "max_tokens": 8192,
                "stream": True,
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
                                json_str = line_str[len("data: "):]
                                json_line = json.loads(json_str)
                                token = json_line['choices'][0].get('delta', {}).get('content', '')
                                answer += token
                                yield token
                        except Exception:
                            continue
                session_histories[session_id].append({"role": "assistant", "content": answer, "bot_name": "openai-research"})
                if project_id is not None:
                    save_chat(project_id, combined_prompt, answer, "openai-research")

            return StreamingResponse(event_generator(), media_type="text/plain")

    except requests.exceptions.Timeout:
        traceback.print_exc()
        raise HTTPException(status_code=504, detail="Deep Research API request timeout")
    except requests.exceptions.ConnectionError:
        traceback.print_exc()
        raise HTTPException(status_code=503, detail="Deep Research API connection failed")
    except requests.exceptions.HTTPError as e:
        traceback.print_exc()
        raise HTTPException(status_code=response.status_code, detail=f"Deep Research API HTTP error: {str(e)}")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Deep Research model call failed: {str(e)}")


