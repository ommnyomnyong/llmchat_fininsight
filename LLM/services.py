import os
import requests
from dotenv import load_dotenv
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
import json
import traceback

# .env 파일에서 API 키 로드
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROK_API_KEY = os.getenv("GROK_API_KEY")

# 세션별 대화 이력을 임시 저장하는 딕셔너리
# 실제 서비스에서는 Redis 같은 외부 저장소 사용 권장
session_histories = {}

def call_openai_model(req):
    """
    OpenAI gpt-3.5-turbo 모델을 호출하는 함수
    StreamingResponse 형태로 응답을 스트리밍하면서 토큰 단위로 전달함.
    프론트는 이 스트림 데이터를 받아 사용자에게 실시간 타이핑처럼 보여줄 수 있음.
    """
    session_id = req.session_id
    prompt = req.prompt

    # 세션별 대화 히스토리 초기화 또는 가져오기
    if session_id not in session_histories:
        session_histories[session_id] = [{"role": "system", "content": "You are a helpful assistant."}]

    # 유저 발화 추가
    session_histories[session_id].append({"role": "user", "content": prompt})

    api_url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    
    # payload에는 모델, 히스토리, 최대 토큰, 스트리밍 여부 포함
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": session_histories[session_id],
        "max_tokens": 256,
        "stream": True  # 스트리밍 응답 설정 -> AI 답변이 촤라락(?)하고 나오게끔 설정
    }

    # OpenAI API 호출 (스트리밍 모드)
    response = requests.post(api_url, headers=headers, json=payload, stream=True)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="AI 모델 호출 실패")

    # 토큰 단위로 클라이언트에 전달할 generator 함수
    def event_generator():
        answer = ""
        for line in response.iter_lines():
            if line:
                try:
                    # 각 스트림 라인 파싱
                    json_line = json.loads(line.decode('utf-8').replace("data: ", ""))
                    token = json_line['choices'][0].get('delta', {}).get('content', '')
                    answer += token
                    yield token  # 프론트로 한 토큰씩 전송 (타이핑 효과 제공, 마찬가지로 스트리밍 효과를 위해)
                except Exception:
                    continue
        # 전체 응답 완성 후 세션에 저장
        session_histories[session_id].append({"role": "assistant", "content": answer})

    # StreamingResponse 객체로 반환, 프론트 React 등에서 fetch/axios로 받아 처리
    return StreamingResponse(event_generator(), media_type="text/plain")


def call_gemini_model(req):
    """
    Gemini AI 모델 호출 함수, 내부 동작은 call_openai_model과 유사.
    """
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
    """
    Grok AI 모델 호출 함수, 구조 동일.
    """
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


def call_deep_research_model(req):
    """
    이 함수는 OpenAI 또는 Gemini의 Deep Research API를 호출하여 AI 기반 답변을 생성합니다.

    기본적으로는 OpenAI의 'gpt-4o-search-preview' 모델을 사용하지만,
    요청 시 model_name이 'gemini-2.5-pro'로 지정되면 Gemini 2.5 Pro 모델을 사용해 별도의 API 엔드포인트로 호출합니다.

    함수 동작 개요:
    1. 클라이언트가 보내는 세션 ID와 사용자의 질문(prompt)을 기반으로 대화 이력을 관리합니다.
    2. 세션 이력이 없으면, 시스템 역할 메시지로 "도움이 되는 어시스턴트이며, 정보가 부족하면 추가 질문을 하라"는 안내를 포함해 초기화합니다.
    3. 현재 사용자의 질문을 세션 이력에 추가합니다.
    4. model_name에 따라 OpenAI 또는 Gemini Deep Research API를 호출하고, 적절한 페이로드와 헤더를 설정합니다.
    5. API 응답을 받아 오류 여부를 점검하고, 답변 텍스트를 추출합니다.
    6. AI의 답변을 세션 이력에 추가하고, 응답 데이터를 JSON 형식으로 반환합니다.

    프론트엔드 활용 포인트:
    - 프론트엔드는 이 함수를 호출하여 JSON 응답을 받습니다. 응답에는 현재 AI가 생성한 답변("answer")과 대화 이력("history")이 모두 포함됩니다.
    - "answer"는 사용자에게 바로 보여줄 AI의 답변 텍스트입니다.
    - "history"는 대화 상태 유지용으로 사용자가 이전 대화 내용을 기반으로 지속적인 상호작용을 할 수 있게 합니다.
    - 이 기능을 통해 React와 같은 SPA 환경에서도 자연스러운 대화형 UI 구현이 가능합니다.
    - 예를 들어, 사용자가 추가 질문을 하거나, AI가 정보가 부족할 경우 재질문을 요구하는 등의 대화 흐름을 자연스럽게 처리할 수 있습니다.

    네트워크 오류, API 호출 실패 등의 상황에도 적절한 예외 처리를 하여 안정적인 서비스 운영에 기여합니다.
    """
    session_id = req.session_id
    prompt = req.prompt

    if session_id not in session_histories:
        session_histories[session_id] = [
            {"role": "system", "content": "You are a helpful assistant. 정보가 부족하면 궁금한 점을 추가로 물어보세요."}
        ]
    session_histories[session_id].append({"role": "user", "content": prompt})

    try:
        if getattr(req, "model_name", "") == "gemini-2.5-pro":
            # Gemini Deep Research API 호출 (현재 스트리밍 지원 여부 문서 확인 필요)
            api_url = "https://api.gemini.ai/v1/responses"
            headers = {"Authorization": f"Bearer {GEMINI_API_KEY}"}
            payload = {
                "input": prompt,
                "model": "gemini-2.5-pro",
                "tools": [{"type": "web_search_preview"}],
                "session_id": session_id
            }
            # Gemini는 스트리밍 지원이 맞는지 확인 필요, 여기서는 일반 호출
            response = requests.post(api_url, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            result = response.json()

            if "error" in result:
                raise HTTPException(status_code=500, detail=f"Gemini API error: {result['error']}")

            answer = result.get("output_text") or (result.get("output", [{}])[0].get("text") if "output" in result else "응답이 없습니다.")

            session_histories[session_id].append({"role": "assistant", "content": answer})

            # Gemini는 현재 스트리밍 지원 예시 없으므로 일반 JSON 반환
            return {"model": payload["model"], "answer": answer, "history": session_histories[session_id]}

        else:
            # OpenAI API 스트리밍 호출
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
