from __future__ import annotations

import json
import logging
import uuid
from typing import Any, Literal, Optional, TypedDict

# pyrefly: ignore [missing-import]
from duckduckgo_search import DDGS
from langgraph.graph import END, StateGraph

from app.models import Chunk, Document, QuizQuestion, QuizSheet

logger = logging.getLogger(__name__)


class QuizState(TypedDict, total=False):
    document: Document
    question_count: int
    difficulty: str
    audience: str
    tone: str
    language: str
    enable_web_search: bool
    ai_service: Any
    handout_text: Optional[str]
    quiz_outline: dict
    web_results: str
    raw_questions: list[dict]
    quiz_sheet: Optional[QuizSheet]


def _get_lang_instruction(language: str) -> str:
    if language == "en":
        return "Please generate all quiz titles, questions, options, explanations, and rubrics strictly in English."
    elif language == "auto":
        return "請自動識別教材主要語言，並以相同的語言輸出試卷與題目解析。"
    return "無論輸入教材語言為何，請統一以【繁體中文 (Traditional Chinese)】輸出試卷標題、題目內容、選項與詳細解析。"


def _clean_search_query(text: str) -> str:
    import re
    cleaned = re.sub(r"[：:｜|—\-_【】\[\]\(\)（）？?！!，,。.]", " ", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:35]


def _get_quiz_tone_guidance(tone: str = "清楚易懂", audience: str = "一般大眾/初學者") -> str:
    parts = [f"【學習對象命題規範：{audience}】"]
    if any(k in audience for k in ["國中", "國小", "初學", "入門", "基礎"]):
        parts.append("- 題幹文字清晰易懂，避免冗長咬文嚼字，情境題應貼近生活經驗與直觀現象。")
    elif any(k in audience for k in ["高中", "升學"]):
        parts.append("- 著重觀念整合、因果辨析與實驗數據圖表判讀。")
    else:
        parts.append("- 著重學術精準度與深入原理分析。")

    parts.append(f"\n【教學語氣風格貫徹：{tone}】")
    if "故事" in tone:
        parts.append(
            "- 【情境故事化命題】：題幹請盡量設計為「生活情境偵探」、「日常現象解謎」或「生活實驗挑戰」（例如：小明在廚房觀察到...、太空人在月球丟球...），使題目富有趣味與臨場感。\n"
            "- 【解析故事化引導】：explanation 解析時，請用生動的生活比喻與一步步情境推理，引導學生理解為什麼該選項正確或錯誤，而非單純背誦定義。"
        )
    elif "活潑" in tone or "互動" in tone:
        parts.append(
            "- 【活潑互動與引導思考】：題幹生動，詳解中多使用啟發性引導語句與動手思考步驟。"
        )
    elif "專業" in tone or "嚴謹" in tone:
        parts.append(
            "- 【專業嚴謹與標準題型】：標準學術題幹，定義清晰無歧義，解析講求嚴密數理步驟。"
        )
    else:
        parts.append(
            "- 【清楚易懂】：題目問法直觀明確，解析條理清晰、易於自學理解。"
        )
    return "\n".join(parts)


def plan_quiz_node(state: QuizState) -> QuizState:
    ai_service = state["ai_service"]
    document = state["document"]
    question_count = state.get("question_count", 5)
    difficulty = state.get("difficulty", "all")
    audience = state.get("audience", "大學生")
    tone = state.get("tone", "清楚易懂")
    language = state.get("language", "zh-TW")
    handout_text = state.get("handout_text", "")

    total_chunks = len(document.chunks)
    if total_chunks <= 25:
        sampled = document.chunks
    else:
        indices = [int(i * (total_chunks - 1) / 24) for i in range(25)]
        sampled = [document.chunks[i] for i in indices]

    context = "\n\n".join(f"[第 {c.page} 頁] {c.text}" for c in sampled)
    lang_instr = _get_lang_instruction(language)
    tone_guidance = _get_quiz_tone_guidance(tone=tone, audience=audience)

    system_prompt = f"你是資深教務出題與評量專家。請針對學習對象【{audience}】、以【{tone}】的教學語氣，分析教材內容並規劃一份包含核心觀念、易錯陷阱與推導應用的題目卷大綱。\n\n{tone_guidance}\n\n{lang_instr}"
    
    user_prompt_parts = []
    if handout_text:
        user_prompt_parts.append(f"【教學母本講義結構依據】：\n{handout_text[:3000]}\n")
    user_prompt_parts.append(f"【教材全景內容摘要】（共 {document.pages} 頁、{total_chunks} 區塊）：\n{context}\n")
    user_prompt_parts.append(
        f"學習對象：{audience}\n教學語氣：{tone}\n題數：{question_count} 題\n難度傾向：{difficulty}\n目標語言：{language}\n\n"
        f"請規劃測驗卷標題 (title)、測驗指引說明 (description) 以及 {question_count} 個出題考點方向 (focal_topics)。"
    )
    user_prompt = "\n".join(user_prompt_parts)

    schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "description": {"type": "string"},
            "focal_topics": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "required": ["title", "description", "focal_topics"],
        "additionalProperties": False,
    }

    try:
        outline = ai_service._structured_response(system_prompt, user_prompt, schema)
    except Exception as exc:
        logger.warning("出題大綱規劃產生異常，將自動降級：%s", exc)
        outline = {
            "title": f"{document.name} 單元評量測驗卷",
            "description": "本測驗卷旨在檢驗本章節的核心概念掌握度與推導應用能力。",
            "focal_topics": [f"核心考點 {i+1}" for i in range(question_count)],
        }

    return {"quiz_outline": outline}


def enrich_quiz_web_node(state: QuizState) -> QuizState:
    outline = state.get("quiz_outline", {})
    title = outline.get("title", "")
    topics = outline.get("focal_topics", [])
    web_results = ""

    search_keyword = _clean_search_query(title)
    if not search_keyword or search_keyword in ("測驗卷", "題庫", "評量"):
        if topics:
            search_keyword = _clean_search_query(" ".join(str(t) for t in topics[:2]))

    if not search_keyword:
        query_str = "歷屆試題 經典考題"
    else:
        query_str = f"{search_keyword} 考題 題庫 概念題"

    try:
        results = list(DDGS(timeout=10).text(query_str, max_results=3))
        if results:
            import re
            formatted = []
            for item in results:
                title_text = re.sub(r"<[^>]+>", "", item.get("title", "")).strip()
                body_text = re.sub(r"<[^>]+>", "", item.get("body", "")).strip()
                body_text = body_text.replace("{", "(").replace("}", ")")[:180]
                if title_text or body_text:
                    formatted.append(f"題型參考：{title_text}\n內容：{body_text}")
            web_results = "\n\n".join(formatted)
    except Exception as exc:
        logger.warning("題庫補充網路搜尋失敗：%s", exc)
        web_results = ""
    return {"web_results": web_results}


def route_after_quiz_plan(state: QuizState) -> Literal["enrich_quiz_web", "generate_questions"]:
    if state.get("enable_web_search", False):
        return "enrich_quiz_web"
    return "generate_questions"


def generate_questions_node(state: QuizState) -> QuizState:
    """方案 B：以講義考點為骨幹 + 原始教材為例題數據依據，進行單次批次出題 (Single Batch Quiz Generation)"""
    ai_service = state["ai_service"]
    document = state["document"]
    question_count = state.get("question_count", 5)
    difficulty = state.get("difficulty", "all")
    audience = state.get("audience", "大學生")
    tone = state.get("tone", "清楚易懂")
    language = state.get("language", "zh-TW")
    outline = state.get("quiz_outline", {})
    web_results = state.get("web_results", "")
    handout_text = state.get("handout_text", "")

    topics = outline.get("focal_topics", [])
    if not topics:
        topics = [f"核心考點 {i+1}" for i in range(question_count)]
    if len(topics) < question_count:
        topics = list(topics) + [f"綜合應用考點 {i+1}" for i in range(len(topics), question_count)]
    elif len(topics) > question_count:
        topics = list(topics[:question_count])

    # 均勻取樣教材原始片段
    total_chunks = len(document.chunks)
    if total_chunks <= 20:
        sampled = document.chunks
    else:
        indices = [int(i * (total_chunks - 1) / 19) for i in range(20)]
        sampled = [document.chunks[i] for i in indices]
    context = "\n\n".join(f"[第 {c.page} 頁] {c.text}" for c in sampled)

    lang_instr = _get_lang_instruction(language)
    rule = (
        "【出題規範】：\n"
        "1. 題型分配 (type)：綜合包含 'single_choice' (單選題, 4 個 options A/B/C/D), "
        "'multiple_choice' (多選題, 4~5 個 options), 或 'problem_solving' (計算/論述推導題, options 為空陣列 [])。\n"
        "2. 題目與數學公式極致規範：凡涉及任何數學公式、分數、指數、希臘字母、運算符號（如 $a$, $b$, $\\frac{a}{b}$, $\\times$, $\\div$, $\\neq$, $\\pm$, $\\in$, $\\mathbb{Q}$, $\\mathbb{Z}$, $\\sim$, $\\cdot$, $10^{-2}$, $2^{-2} \\times 5^{-2}$ 等），一律 100% 使用 $...$（行內）或 $$...$$（獨立行）完整包裹！嚴禁輸出未包裹 $ 的裸 LaTeX 指令（嚴禁寫 \\frac{a}{b} 或 fracab，必須寫 $\\frac{a}{b}$）！在 JSON 輸出中反斜線必須轉義為 \\\\。\n"
        "3. 正確答案 (answer)：單選題給代號如 'B'，多選題如 'A, C'，計算題給出最終答案數值與單位。\n"
        "4. 詳解 (explanation)：必須包含完整推導邏輯、觀念剖析與常見錯誤陷阱說明（建議 80~150 字）。\n"
        "5. 來源頁碼 (source_pages)：標註教材確切頁碼陣列（例如 [2, 3]）。"
    )

    full_quiz_schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "description": {"type": "string"},
            "questions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["single_choice", "multiple_choice", "problem_solving"]},
                        "question": {"type": "string"},
                        "options": {"type": "array", "items": {"type": "string"}},
                        "answer": {"type": "string"},
                        "explanation": {"type": "string"},
                        "source_pages": {"type": "array", "items": {"type": "integer"}},
                        "difficulty": {"type": "string", "enum": ["easy", "medium", "hard"]},
                    },
                    "required": ["type", "question", "options", "answer", "explanation", "source_pages", "difficulty"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["title", "description", "questions"],
        "additionalProperties": False,
    }

    tone_guidance = _get_quiz_tone_guidance(tone=tone, audience=audience)
    system_prompt = (
        f"你是資深命題與評量專家。請針對學習對象【{audience}】以【{tone}】的教學風格，為本教材一次性批次設計包含 {question_count} 道高品質測驗試題與詳解的完整試卷。\n\n"
        f"{tone_guidance}\n\n"
        f"{rule} {lang_instr}"
    )

    user_prompt_parts = []
    if handout_text:
        user_prompt_parts.append(f"【教學母本講義核心重點依據】：\n{handout_text}\n")
    user_prompt_parts.append(f"【原始教材例題、數據與頁碼索引】：\n{context}\n")
    if web_results:
        user_prompt_parts.append(f"【參考經典題型資料】：\n{web_results}\n")

    topics_str = "\n".join(f"- 第 {i+1} 題考點：{t}" for i, t in enumerate(topics))
    user_prompt_parts.append(
        f"【試卷出題設定】：\n"
        f"- 總題數：{question_count} 題\n"
        f"- 難度傾向：{difficulty}\n"
        f"- 目標語言：{language}\n"
        f"- 預定試卷標題：{outline.get('title', '單元評量測驗卷')}\n\n"
        f"【規劃出題考點列表】：\n{topics_str}\n\n"
        f"請一次性產出包含完整 {question_count} 道題目的合法 JSON 物件。"
    )
    user_prompt = "\n".join(user_prompt_parts)

    try:
        res = ai_service._structured_response(system_prompt, user_prompt, full_quiz_schema)
        questions = res.get("questions", [])
    except Exception as exc:
        logger.warning("批次試卷出題異常，將進行降級建構：%s", exc)
        questions = []
        for idx, topic in enumerate(topics):
            questions.append({
                "type": "single_choice",
                "question": f"下列關於【{topic}】的核心概念，何者敘述最適當？",
                "options": [
                    f"A. {topic} 的定義與推導與教材原理相符",
                    f"B. {topic} 僅在極端特殊條件下成立",
                    f"C. {topic} 的推導忽略了守恆定律",
                    f"D. {topic} 與本章基礎觀念無關",
                ],
                "answer": "A",
                "explanation": f"依據教材內容，{topic} 遵循章節基本定律與核心觀念架構。",
                "source_pages": [1],
                "difficulty": "medium",
            })

    # 若題目數量不足則補齊
    while len(questions) < question_count:
        idx = len(questions)
        t_name = topics[idx] if idx < len(topics) else f"綜合考點 {idx+1}"
        questions.append({
            "type": "single_choice",
            "question": f"針對【{t_name}】的應用實例分析，下列何者正確？",
            "options": [
                f"A. {t_name} 具備廣泛應用與明確之理論支持",
                f"B. {t_name} 不具備實驗可驗證性",
                f"C. {t_name} 僅適用於單一理想模型",
                f"D. 以上皆非",
            ],
            "answer": "A",
            "explanation": f"依據章節核心觀念，{t_name} 具備完整的推導與實務應用依據。",
            "source_pages": [1],
            "difficulty": "medium",
        })

    return {"raw_questions": questions[:question_count]}


def finalize_quiz_node(state: QuizState) -> QuizState:
    document = state["document"]
    outline = state.get("quiz_outline", {})
    raw_questions = state.get("raw_questions", [])

    from app.services import auto_repair_math_expressions

    quiz_questions = []
    for idx, item in enumerate(raw_questions, 1):
        q_id = f"Q{idx:02d}"
        q_type = item.get("type", "single_choice")
        if q_type not in ("single_choice", "multiple_choice", "problem_solving"):
            q_type = "single_choice"

        raw_options = item.get("options", [])
        if not isinstance(raw_options, list):
            raw_options = []
        options = [auto_repair_math_expressions(opt) for opt in raw_options]

        quiz_questions.append(
            QuizQuestion(
                id=q_id,
                type=q_type,
                question=auto_repair_math_expressions(item.get("question", "評量題目")),
                options=options,
                answer=auto_repair_math_expressions(item.get("answer", "A")),
                explanation=auto_repair_math_expressions(item.get("explanation", "詳解說明")),
                source_pages=item.get("source_pages", [1]),
                difficulty=item.get("difficulty", "medium"),
            )
        )

    title = outline.get("title") or f"{document.name} 核心概念評量卷"
    description = outline.get("description") or "本測驗卷旨在檢視教材各章節核心觀念掌握度。"

    quiz_sheet = QuizSheet(
        id=uuid.uuid4().hex[:12],
        document_id=document.id,
        title=title,
        description=description,
        questions=quiz_questions,
        duration_minutes=max(10, len(quiz_questions) * 3),
    )

    return {"quiz_sheet": quiz_sheet}


def build_quiz_graph() -> StateGraph:
    workflow = StateGraph(QuizState)

    workflow.add_node("plan_quiz", plan_quiz_node)
    workflow.add_node("enrich_quiz_web", enrich_quiz_web_node)
    workflow.add_node("generate_questions", generate_questions_node)
    workflow.add_node("finalize_quiz", finalize_quiz_node)

    workflow.set_entry_point("plan_quiz")

    workflow.add_conditional_edges(
        "plan_quiz",
        route_after_quiz_plan,
        {
            "enrich_quiz_web": "enrich_quiz_web",
            "generate_questions": "generate_questions",
        },
    )

    workflow.add_edge("enrich_quiz_web", "generate_questions")
    workflow.add_edge("generate_questions", "finalize_quiz")
    workflow.add_edge("finalize_quiz", END)

    return workflow.compile()
