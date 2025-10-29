import os
import requests
from dotenv import load_dotenv
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
import json
import traceback


load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROK_API_KEY = os.getenv("GROK_API_KEY")


# 세션 이력 임시 저장 (프로덕션 전 Redis 등으로 확장 필요)
session_histories = {}


def call_openai_model(req):
    session_id = req.session_id
    prompt = req.prompt

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
        session_histories[session_id].append({"role": "assistant", "content": answer})

    return StreamingResponse(event_generator(), media_type="text/plain")


def call_gemini_model(req):
    session_id = req.session_id
    prompt = req.prompt

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
        session_histories[session_id].append({"role": "assistant", "content": answer})

    return StreamingResponse(event_generator(), media_type="text/plain")


def call_grok_model(req):
    session_id = req.session_id
    prompt = req.prompt

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
        session_histories[session_id].append({"role": "assistant", "content": answer})

    return StreamingResponse(event_generator(), media_type="text/plain")


def call_openai_deep_research_model(req):
    import traceback

    session_id = req.session_id
    prompt = req.prompt

    if session_id not in session_histories:
        session_histories[session_id] = [
            {"role": "system", "content": "You are a helpful assistant. 정보가 부족하면 궁금한 점을 추가로 물어보세요."}
        ]

    session_histories[session_id].append({"role": "user", "content": prompt})

    api_url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    payload = {
        "model": "gpt-4o-search-preview",
        "messages": session_histories[session_id],
        "max_tokens": 256,
        "stream": True
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload)
        print(f"[DEBUG] Response status: {response.status_code}")
        text = response.text
        print(f"[DEBUG] Response text: {text}")

        response.raise_for_status()
        result = response.json()

        if "error" in result:
            print(f"[ERROR] OpenAI API error: {result['error']}")
            raise HTTPException(status_code=500, detail="Chat Completion API 에러 발생")

        answer = result['choices'][0]['message'].get('content', "응답이 없습니다.")

        session_histories[session_id].append({"role": "assistant", "content": answer})

        return {"model": "gpt-4o-search-preview", "answer": answer, "history": session_histories[session_id]}

    except requests.exceptions.RequestException as e:
        print(f"[EXCEPTION] requests error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Chat Completion 네트워크 오류")

    except Exception as e:
        print(f"[EXCEPTION] unexpected error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Chat Completion 모델 호출 실패")