from __future__ import annotations

import logging
from typing import Literal

from duckduckgo_search import DDGS
from langgraph.graph import END, StateGraph

from app.models import Source
from app.workflows.handlers.common import _format_history
from .state import QAState

logger = logging.getLogger(__name__)


def retrieve_node(state: QAState) -> QAState:
    ai_service = state["ai_service"]
    document = state["document"]
    question = state["question"]
    history = state.get("history", [])

    # 若為代名詞或短追問，結合上一輪提問主題擴展檢索關鍵字
    query_for_retrieval = question
    if history and len(question.strip()) < 15:
        last_user_turns = [h.get("content", "") for h in history if h.get("role") == "user"]
        if last_user_turns:
            prev_q = last_user_turns[-1][:30]
            query_for_retrieval = f"{prev_q} {question}"

    matches = ai_service.retrieve(document, query_for_retrieval)
    return {"retrieved_chunks": matches}


def grade_documents_node(state: QAState) -> QAState:
    retrieved = state.get("retrieved_chunks", [])
    if not retrieved:
        return {"is_relevant": False}
    
    # 最高相似度得分門檻判斷
    top_score = retrieved[0][1] if len(retrieved) > 0 else 0.0
    is_relevant = top_score >= 0.12 or len(retrieved[0][0].text.strip()) > 30
    return {"is_relevant": is_relevant}


def web_search_node(state: QAState) -> QAState:
    import re
    question = state["question"]
    web_results = ""
    clean_q = re.sub(r"[：:｜|—\-_【】\[\]\(\)（）？?！!，,。.]", " ", question)
    clean_q = re.sub(r"\s+", " ", clean_q).strip()[:50] or question[:50]
    try:
        results = list(DDGS(timeout=10).text(clean_q, max_results=3))
        if results:
            formatted = []
            for item in results:
                formatted.append(f"標題：{item.get('title', '')}\n摘要：{item.get('body', '')}\n網址：{item.get('href', '')}")
            web_results = "\n\n".join(formatted)
    except Exception as exc:
        logger.warning("DuckDuckGo 網路搜尋失敗或超時：%s", exc)
        web_results = ""
    return {"web_results": web_results}


def route_after_grading(state: QAState) -> Literal["generate_answer", "web_search", "fallback_answer"]:
    if state.get("is_relevant", False):
        return "generate_answer"
    if state.get("enable_web_search", False):
        return "web_search"
    return "fallback_answer"


def generate_answer_node(state: QAState) -> QAState:
    ai_service = state["ai_service"]
    question = state["question"]
    history = state.get("history", [])
    retrieved = state.get("retrieved_chunks", [])
    web_results = state.get("web_results", "")
    hallucination_feedback = state.get("hallucination_feedback", "")
    history_text = _format_history(history)

    sources = [
        Source(
            page=c.page,
            excerpt=c.text[:180] + ("…" if len(c.text) > 180 else ""),
            score=max(0.0, min(1.0, round(s, 2))),
        )
        for c, s in retrieved
    ]

    context_parts = []
    if retrieved:
        context_parts.append("\n\n".join(f"[第 {c.page} 頁]\n{c.text}" for c, _ in retrieved))
    
    context_str = "\n---\n".join(context_parts) if context_parts else "無相關教材片段"
    
    system_prompt = (
        "你是嚴謹的繁體中文教學助理。"
        "只能根據提供的教材片段與網路參考資料回答。"
        "若有歷史對話紀錄，請結合上下文脈絡進行精準、連貫的解答或追問補充。"
        "回答必須清楚、精簡，並以（第 X 頁）標示依據。"
        "所有數學公式、理化符號與數學變數，請一律使用標準 LaTeX 語法格式（單行公式使用 $...$，獨立段落公式使用 $$...$$）。"
    )
    user_prompt = ""
    if history_text:
        user_prompt += f"{history_text}\n"
    user_prompt += f"教材片段：\n{context_str}\n\n"
    if web_results:
        user_prompt += f"網路補充資料：\n{web_results}\n\n"
    if hallucination_feedback:
        user_prompt += f"【修正提示】：前次回答經自我審查發現未完全對齊資料（{hallucination_feedback}）。請務必依據參考資料精準回答。\n\n"
    user_prompt += f"學生當前提問：{question}"

    answer = ai_service._text_response(system_prompt, user_prompt)
    return {"answer": answer, "sources": sources}


def check_hallucination_node(state: QAState) -> QAState:
    ai_service = state.get("ai_service")
    answer = state.get("answer", "")
    retrieved = state.get("retrieved_chunks", [])
    web_results = state.get("web_results", "")
    retry_count = state.get("hallucination_retry", 0)

    if not answer or not ai_service or retry_count >= 1:
        return {"is_hallucinated": False}

    context_str = "\n".join(c.text for c, _ in retrieved) if retrieved else ""
    if web_results:
        context_str += "\n" + web_results

    if not context_str.strip():
        return {"is_hallucinated": False}

    system_prompt = (
        "你是嚴謹的 Self-RAG 防幻覺審查員。"
        "請評估 AI 的回答內容是否完全來自給定的參考資料。若回答中包含了參考資料中完全未提及的自創內容，請判定為幻覺。"
    )
    user_prompt = f"參考資料：\n{context_str}\n\nAI回答：\n{answer}"

    schema = {
        "type": "object",
        "properties": {
            "is_grounded": {"type": "boolean"},
            "reason": {"type": "string"},
        },
        "required": ["is_grounded", "reason"],
        "additionalProperties": False,
    }

    try:
        res = ai_service._structured_response(system_prompt, user_prompt, schema)
        is_grounded = res.get("is_grounded", True)
        reason = res.get("reason", "")
        if not is_grounded:
            logger.info("Self-RAG 檢測到幻覺內容，觸發重試修正：%s", reason)
            return {
                "is_hallucinated": True,
                "hallucination_retry": retry_count + 1,
                "hallucination_feedback": reason,
            }
    except Exception as exc:
        logger.warning("防幻覺審查執行失敗，跳過審查：%s", exc)

    return {"is_hallucinated": False}


def route_after_hallucination_check(state: QAState) -> Literal["generate_answer", "end"]:
    if state.get("is_hallucinated", False) and state.get("hallucination_retry", 0) <= 1:
        return "generate_answer"
    return "end"


def fallback_answer_node(state: QAState) -> QAState:
    msg = "教材中未提及此內容。若需搜尋外部資料，建議開啟『網路補充搜尋』功能。"
    return {"answer": msg, "sources": []}


def build_qa_graph() -> StateGraph:
    workflow = StateGraph(QAState)

    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("grade_documents", grade_documents_node)
    workflow.add_node("web_search", web_search_node)
    workflow.add_node("generate_answer", generate_answer_node)
    workflow.add_node("check_hallucination", check_hallucination_node)
    workflow.add_node("fallback_answer", fallback_answer_node)

    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "grade_documents")

    workflow.add_conditional_edges(
        "grade_documents",
        route_after_grading,
        {
            "generate_answer": "generate_answer",
            "web_search": "web_search",
            "fallback_answer": "fallback_answer",
        },
    )

    workflow.add_edge("web_search", "generate_answer")
    workflow.add_edge("generate_answer", "check_hallucination")

    workflow.add_conditional_edges(
        "check_hallucination",
        route_after_hallucination_check,
        {
            "generate_answer": "generate_answer",
            "end": END,
        },
    )

    workflow.add_edge("fallback_answer", END)

    return workflow.compile()

