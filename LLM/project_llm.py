# backend/LLM/project_llm_v2.py

import os, requests, traceback
from fastapi import HTTPException
from dotenv import load_dotenv

# DB
from db.project_DB import get_project_chats, save_project_chat
from db.vector_DB import search_context

# 파일 처리
from LLM.file_embeddings import extract_text_from_file

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
XAI_API_KEY = os.getenv("XAI_API_KEY")


#  LLM API CALL HELPERS
def _openai(messages):
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}

    payload = {
        "model": "gpt-4o",
        "messages": messages,
    }

    res = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=30
    )
    res.raise_for_status()
    return res.json()["choices"][0]["message"]["content"].strip()


def _gemini(prompt):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent"
    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}

    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    res = requests.post(url, headers=headers, params=params, json=payload)
    res.raise_for_status()
    data = res.json()
    parts = data["candidates"][0]["content"]["parts"]
    return "".join(p.get("text", "") for p in parts)


def _grok(messages):
    headers = {"Authorization": f"Bearer {XAI_API_KEY}"}

    payload = {
        "model": "grok",
        "messages": messages,
    }

    res = requests.post("https://api.x.ai/v1/chat/completions", headers=headers, json=payload)
    res.raise_for_status()
    return res.json()["choices"][0]["message"]["content"].strip()


def _deep_research(prompt):
    enhanced = (
        "Deep Research Mode:\n"
        "요청 내용을 단계적으로 분석하고 근거 기반으로 심층 정리하십시오.\n\n"
        f"{prompt}"
    )
    return _gemini(enhanced)


def summarize_old_chats(chats):
    """오래된 대화 자동 요약 (OpenAI 이용)"""
    if not chats:
        return None

    raw = ""
    for c in chats:
        raw += f"User: {c['user_input']}\n"
        raw += f"Assistant: {c['bot_output']}\n"

    prompt = f"""
            다음은 과거 프로젝트 대화 내용입니다.
            핵심 흐름, 논리, 의도만 유지해서 5줄 이내로 요약하세요.

            원문:
            {raw}
            """

    try:
        summary = _openai([
            {"role": "system", "content": "너는 전문적인 요약가다."},
            {"role": "user", "content": prompt}
        ])
        return summary
    except:
        return None


def build_project_context(project_id: int, prompt: str, uploaded_file_bytes=None, filename=None):
    """대화 컨텍스트 품질 향상 버전"""
    
    messages = []

    # 시스템 프롬프트
    system_prompt = (
        "너는 분석가·연구원·기획자·에디터의 역할을 수행하는 전문 AI 어시스턴트입니다.\n"
        "사용자가 입력한 내용을 정확하게 해석하고, 임의로 창작하지 말고, "
        "논리적·간결·명확하게 재구성하세요.\n\n"

        "출력 규칙:\n"
        "1) 한 문단 요약\n"
        "2) 핵심 내용 3~5개\n"
        "3) 중요한 인사이트 도출\n"
        "4) 구조화된 정리 (배경 → 문제 → 분석 → 결론)\n"
        "5) 입력 내용을 보존하면서 문서를 더 명확하게 개선한 버전\n"
        "6) 요청 시 전략·가설·개선방안·실행계획 포함 가능\n\n"

        "규칙:\n"
        "- 내용 왜곡 금지\n"
        "- 임의 창작 금지\n"
        "- 논리적 일관성 유지\n"
        "- 실무 문서 수준으로 작성\n"
    )
    messages.append({"role": "system", "content": system_prompt})

    # 전체 대화 로드
    all_chats = get_project_chats(project_id)

    # 최근 10개 원문 유지
    recent = all_chats[-10:]

    # 오래된 대화는 요약
    older = all_chats[:-10]

    # 오래된 대화 요약본 추가
    if older:
        summary = summarize_old_chats(older)
        if summary:
            messages.append({
                "role": "system",
                "content": f"[이전 대화 요약]\n{summary}"
            })

    # 최근 대화 추가
    for c in recent:
        if c["user_input"]:
            messages.append({"role": "user", "content": c["user_input"]})
        if c["bot_output"]:
            messages.append({"role": "assistant", "content": c["bot_output"]})

    # 벡터 검색 결과
    rag_context = search_context(project_id, prompt)
    if rag_context:
        messages.append({
            "role": "system",
            "content": f"[문서 기반 검색 결과]\n{rag_context}"
        })

    # 업로드 파일 기반 내용
    if uploaded_file_bytes and filename:
        extracted = extract_text_from_file(uploaded_file_bytes, filename)
        if extracted:
            messages.append({
                "role": "system",
                "content": f"[업로드 파일 내용]\n{extracted}"
            })

    # 사용자 입력
    messages.append({"role": "user", "content": prompt})

    return messages


#  PROJECT LLM MASTER FUNCTION (외부에서 호출)
def call_project_llm(model: str, project_id: int, prompt: str, uploaded_file_bytes=None, filename=None):
    """
    프로젝트 기반 LLM 호출 (이전 대화 + 벡터 검색 + 파일 내용 포함)
    """

    # 컨텍스트 자동 조립
    messages = build_project_context(
        project_id=project_id,
        prompt=prompt,
        uploaded_file_bytes=uploaded_file_bytes,
        filename=filename
    )

    # 모델 선택
    model = model.lower()

    if model == "openai":
        answer = _openai(messages)
        
    elif model == "gemini":
        answer = _gemini(messages[-1]["content"])  # gemini는 messages가 아닌 text 기반
        
    elif model in ["grok", "grok-4", "grok-2"]:
        answer = _grok(messages)
        
    elif model in ["deep", "research", "gemini-research"]:
        answer = _deep_research(messages[-1]["content"])
        
    else:
        raise HTTPException(400, f"❌ 지원하지 않는 모델: {model}")

    # 대화 저장
    save_project_chat(project_id, prompt, answer, model)

    return answer

