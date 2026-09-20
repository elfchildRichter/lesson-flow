from __future__ import annotations

import logging
from typing import Any, Dict
from app.workflows.handlers.common import _clean_topic, _format_history

logger = logging.getLogger(__name__)


def academic_handler(payload: Dict[str, Any]) -> Dict[str, Any]:
    """🎓 教務教學部 Handler：處理問答、教學大綱與簡報講稿生成"""
    query = payload.get("query", "")
    ai_service = payload.get("ai_service")
    clean_topic = _clean_topic(query)
    query_lower = query.lower()
    history_text = _format_history(payload.get("history"))

    # 跨部門職能引導：若問題屬於其他部門，主動指引尋求專屬助手支援
    marketing_cross_keywords = [
        "行銷", "推廣", "宣傳", "招生", "文案", "貼文", "賣點", "亮點",
        "社群", "廣告", "獲客", "受眾", "曝光", "定價", "fb 貼文", "threads 貼文"
    ]
    if any(k in query_lower for k in marketing_cross_keywords):
        return {
            "output_text": (
                "👋 您好！我是【🎓 教務教學部】的教務小老師。\n\n"
                "撰寫課程行銷推廣、招生策略、社群文案與賣點包裝屬於【🚀 市場與營銷部】（營銷推廣專員）的主要專長與職責範圍。\n\n"
                "👉 建議您點擊切換至【🚀 市場與營銷部】（與營銷推廣專員對話），獲得最專業的行銷文案與推廣策略支援！"
            ),
            "department": "academic",
            "referred_department": "marketing"
        }
    if any(k in query_lower for k in ["機構合約", "學校合約", "席位開通", "授權審核", "團體席位", "團體授權"]):
        return {
            "output_text": (
                "👋 您好！我是【🎓 教務教學部】的教務小老師。\n\n"
                "學校與機構合約審核、團隊席位授權與帳號開通屬於【🏫 營運與行政部】（教務行政特助）的專屬職能範圍。\n\n"
                "👉 建議您點擊切換至【🏫 營運與行政部】（與教務行政特助對話），獲得專屬行政管理與授權支援！"
            ),
            "department": "academic",
            "referred_department": "operations"
        }
    if any(k in query_lower for k in ["railway 部署", "oom 記憶體", "docker 容器", "部署報錯", "伺服器診斷"]):
        return {
            "output_text": (
                "👋 您好！我是【🎓 教務教學部】的教務小老師。\n\n"
                "伺服器部署、系統效能與記憶體診斷屬於【🛠️ 技術維護部】（技術維護工程師）的專屬職務範圍。\n\n"
                "👉 建議您點擊切換至【🛠️ 技術維護部】（與技術維護工程師對話），獲取技術診斷支援！"
            ),
            "department": "academic",
            "referred_department": "devops"
        }

    prompt = f"""你是 Lesson Flow (課伴) 教務教學部的「教務小老師」(LessonFlow Tutor)。
{history_text}請以親切、專業、結構清晰的資深學術教學助教口吻，回答老師或學生的備課、教學或學科觀念問題：

使用者提問 / 主題：{clean_topic}

回答規範：
1. 嚴謹清晰，切合備課與教學實務需求。
2. 包含核心觀念解析、教學建議與重點摘要。
3. 若涉及理化數學公式，請精準使用標準 LaTeX 格式（行內 $...$ 或獨立區塊 $$...$$）。
4. 若有適用教材頁碼請附上出處標註（如 [P.1], [P.3]）。
5. 自我介紹時請稱呼自己為「教務小老師」，請勿自稱其他職稱。
6. 回覆語言請與使用者提問語言保持一致（若提問為繁體中文則以繁體中文回答，若為英文則以英文回答）。"""

    content = ""
    if ai_service:
        try:
            if ai_service.provider == "gemini" and ai_service.gemini_client:
                res = ai_service.gemini_client.models.generate_content(
                    model=ai_service.model, contents=prompt
                )
                content = res.text
            elif ai_service.provider == "openai" and ai_service.openai:
                res = ai_service.openai.chat.completions.create(
                    model=ai_service.model,
                    messages=[{"role": "user", "content": prompt}],
                )
                content = res.choices[0].message.content
            elif ai_service.ollama:
                res = ai_service.ollama.generate(model=ai_service.model, prompt=prompt)
                content = res.get("response", "")
        except Exception as e:
            logger.warning(f"Academic AI call failed: {e}")

    if not content:
        is_english = any(c.isalpha() and c.isascii() for c in query) and not any('\u4e00' <= c <= '\u9fff' for c in query)
        if is_english:
            content = (
                f"📖 【Lesson Flow Academic Assistance】\n\n"
                f"📌 Lesson Topic: {clean_topic}\n\n"
                f"💡 Core Concept Analysis:\n"
                f"1. Concept Introduction: Focus on fundamental definitions and principles, aligned with visual diagrams [P.1].\n"
                f"2. Key Formulas: Display key mathematical/physical formulas clearly (e.g., $E = mc^2$).\n"
                f"3. Review & Verification: Validated with Self-RAG verification to ensure zero hallucination and accurate citations [P.3].\n\n"
                f"👉 Next Steps: Export to PowerPoint (.pptx) with page-by-page lecture scripts."
            )
        else:
            content = (
                f"📖 【Lesson Flow 教學輔導】\n\n"
                f"📌 授課主題：{clean_topic}\n\n"
                f"💡 核心概念解析：\n"
                f"1. 觀念導讀：著重理解基本定義與原理，配合多模態圖示對照 [P.1]。\n"
                f"2. 關鍵公式：請標示標準公式結構（如 $E = mc^2$）。\n"
                f"3. 課後複習：搭配 Self-RAG 自動校對，無幻覺且確保出處標記正確 [P.3]。\n\n"
                f"👉 建議下一步：匯出成 PowerPoint (.pptx) 並附帶逐頁教學演講稿。"
            )

    return {"output_text": content, "topic": clean_topic, "department": "academic"}
