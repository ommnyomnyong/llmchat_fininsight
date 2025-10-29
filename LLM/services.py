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


def call_openai_deep_research_model(req):
    """
    OpenAI Chat Completion API를 사용하되, 'gpt-4o-search-preview' 모델을 호출.
    세션 히스토리에 시스템 메시지로 '정보가 부족하면 궁금한 점을 추가로 물어보세요' 라는 안내 포함.
    해당 모델은 검색 기능이 탑재되어 있어 외부 정보를 참고한 답변 가능.
    
    프론트에서는 이 반환값을 JSON 형태로 받아 
    대화 내용과 AI 답변을 화면에 실시간 출력하거나 저장 및 후처리에 사용.
    """
    import traceback

    session_id = req.session_id
    prompt = req.prompt

    # 세션별 대화 초기화 및 시스템 메시지 설정 (추론 및 재질문 유발 목적)
    if session_id not in session_histories:
        session_histories[session_id] = [
            {"role": "system", "content": "You are a helpful assistant. 정보가 부족하면 궁금한 점을 추가로 물어보세요."}
        ]

    # 유저 질문을 세션 히스토리에 추가
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
        # API 호출
        response = requests.post(api_url, headers=headers, json=payload)
        print(f"[DEBUG] Response status: {response.status_code}")
        text = response.text
        print(f"[DEBUG] Response text: {text}")

        response.raise_for_status()
        result = response.json()

        # 에러 응답 처리
        if "error" in result:
            print(f"[ERROR] OpenAI API error: {result['error']}")
            raise HTTPException(status_code=500, detail="Chat Completion API 에러 발생")

        # 응답에서 텍스트 추출
        answer = result['choices'][0]['message'].get('content', "응답이 없습니다.")

        # AI 답변을 세션 히스토리에 저장
        session_histories[session_id].append({"role": "assistant", "content": answer})

        # 프론트엔드에 전달할 JSON 응답 (대화 히스토리 포함)
        return {"model": "gpt-4o-search-preview", "answer": answer, "history": session_histories[session_id]}

    except requests.exceptions.RequestException as e:
        print(f"[EXCEPTION] requests error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Chat Completion 네트워크 오류")

    except Exception as e:
        print(f"[EXCEPTION] unexpected error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Chat Completion 모델 호출 실패")
