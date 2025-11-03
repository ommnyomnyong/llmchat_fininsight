import os
import requests
from dotenv import load_dotenv
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
import json
import traceback

from ..db.chat_DB import save_chat

"""
기존 코드에서 수정한 점: 아래 3가지 경우의 수를 모두 반영하여 DB에 저장할 수 있도록 메타데이터 변경함.

A. 프로젝트 신규 생성 후 채팅 시작 시
사용자가 명확히 프로젝트 내에서 채팅을 시작하는 경우, 채팅 세션에 project_id를 부여하여 저장

B. 프로젝트 없이 단순 채팅만 하는 경우
project_id가 없으므로, DB에 저장할 때 이 필드를 NULL로 저장

C. 기존에 프로젝트 없이 생성된 채팅을 나중에 특정 프로젝트에 할당하는 경우
DB에 저장된 기존 채팅 기록에는 project_id가 NULL로 저장되어 있음.
프로젝트에 할당하는 시점에 해당 채팅 기록들의 project_id 필드를 갱신(UPDATE)하여 연결합니다.
"""

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROK_API_KEY = os.getenv("GROK_API_KEY")

# 세션별 대화 이력을 임시 저장하는 딕셔너리
session_histories = {}

def call_openai_model(req):
    session_id = req.session_id
    prompt = req.prompt
    project_id = getattr(req, "project_id", None)

    if session_id not in session_histories:
        session_histories[session_id] = [{"role": "system", "content": "You are a helpful assistant."}]

    session_histories[session_id].append({"role": "user", "content": prompt})

    api_url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": session_histories[session_id],
        "max_tokens": 256,
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

    gemini_api_url = "https://api.gemini.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GEMINI_API_KEY}"}
    payload = {
        "model": "gemini-1",
        "messages": session_histories[session_id] + [{"role": "user", "content": prompt}],
        "max_tokens": 256,
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

    grok_api_url = "https://api.grok.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROK_API_KEY}"}
    payload = {
        "model": "grok-1",
        "messages": session_histories[session_id] + [{"role": "user", "content": prompt}],
        "max_tokens": 256,
        "stream": True
    }

    response = requests.post(grok_api_url, headers=headers, json=payload, stream=True)
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
            {"role": "system", "content": "You are a helpful assistant. 정보가 부족하면 궁금한 점을 추가로 물어보세요."}
        ]
    session_histories[session_id].append({"role": "user", "content": prompt})

    try:
        if getattr(req, "model_name", "") == "gemini-2.5-pro":
            api_url = "https://api.gemini.ai/v1/responses"
            headers = {"Authorization": f"Bearer {GEMINI_API_KEY}"}
            payload = {
                "input": prompt,
                "model": "gemini-2.5-pro",
                "tools": [{"type": "web_search_preview"}],
                "session_id": session_id
            }
            response = requests.post(api_url, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            result = response.json()

            if "error" in result:
                raise HTTPException(status_code=500, detail=f"Gemini API error: {result['error']}")

            answer = result.get("output_text") or (result.get("output", [{}])[0].get("text") if "output" in result else "응답이 없습니다.")

            session_histories[session_id].append({"role": "assistant", "content": answer, "bot_name": "gemini"})
            if project_id is not None:
                save_chat(project_id, prompt, answer, "gemini")

            return {"model": payload["model"], "answer": answer, "history": session_histories[session_id]}
        else:
            api_url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
            payload = {
                "model": "gpt-4o-search-preview",
                "messages": session_histories[session_id],
                "max_tokens": 256,
                "stream": True,
            }

            response = requests.post(api_url, headers=headers, json=payload, stream=True, timeout=30)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="OpenAI API 호출 실패")

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
                session_histories[session_id].append({"role": "assistant", "content": answer})
                if project_id is not None:
                    save_chat(project_id, prompt, answer, "openai")

            return StreamingResponse(event_generator(), media_type="text/plain")

    except requests.exceptions.Timeout:
        traceback.print_exc()
        raise HTTPException(status_code=504, detail="Deep Research API 요청 시간 초과")
    except requests.exceptions.ConnectionError:
        traceback.print_exc()
        raise HTTPException(status_code=503, detail="Deep Research API 연결 실패")
    except requests.exceptions.HTTPError as e:
        traceback.print_exc()
        raise HTTPException(status_code=response.status_code, detail=f"Deep Research API HTTP 오류: {str(e)}")
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Deep Research 모델 호출 실패: {str(e)}")
