from __future__ import annotations

import io
import json
import logging
import math
import os
import re
import uuid
from concurrent.futures import ThreadPoolExecutor
from pypdf import PdfReader
from typing import Any, Optional

from pydantic import TypeAdapter
from .models import Chunk, Deck, Document, Handout, HandoutSection, QuizQuestion, QuizSheet, Slide, Source
from .workflows import build_deck_graph, build_qa_graph, build_quiz_graph


class DiskDict(dict):
    """具備磁碟持久化特性的字典，啟動時自動載入，賦值時自動非同步/同步寫入 JSON 檔案。"""
    def __init__(self, directory: str, model_cls: type, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.directory = directory
        self.adapter = TypeAdapter(model_cls)
        os.makedirs(self.directory, exist_ok=True)
        self._load_all()

    def _load_all(self) -> None:
        try:
            for fname in os.listdir(self.directory):
                if fname.endswith(".json"):
                    fpath = os.path.join(self.directory, fname)
                    try:
                        with open(fpath, "rb") as f:
                            content = f.read()
                        obj = self.adapter.validate_json(content)
                        key = getattr(obj, "id", fname[:-5])
                        super().__setitem__(key, obj)
                    except Exception as err:
                        logging.getLogger(__name__).warning("無法載入持久化檔案 %s: %s", fpath, err)
        except Exception as err:
            logging.getLogger(__name__).warning("掃描持久化目錄 %s 失敗: %s", self.directory, err)

    def __setitem__(self, key: str, value: typing.Any) -> None:
        super().__setitem__(key, value)
        try:
            fpath = os.path.join(self.directory, f"{key}.json")
            json_bytes = self.adapter.dump_json(value, indent=2)
            with open(fpath, "wb") as f:
                f.write(json_bytes)
        except Exception as err:
            logging.getLogger(__name__).warning("寫入持久化檔案 %s 失敗: %s", key, err)

    def __delitem__(self, key: str) -> None:
        super().__delitem__(key)
        try:
            fpath = os.path.join(self.directory, f"{key}.json")
            if os.path.exists(fpath):
                os.remove(fpath)
        except Exception as err:
            logging.getLogger(__name__).warning("刪除持久化檔案 %s 失敗: %s", key, err)


class DocumentStore:
    def __init__(self, base_dir: Optional[str] = None) -> None:
        if base_dir is None:
            base_dir = os.getenv("DOCUMENT_STORE_DIR", os.path.join(os.path.dirname(__file__), "data", "store"))
        self.base_dir = base_dir
        self.documents: dict[str, Document] = DiskDict(os.path.join(base_dir, "documents"), Document)
        self.decks: dict[str, Deck] = DiskDict(os.path.join(base_dir, "decks"), Deck)
        self.quizzes: dict[str, QuizSheet] = DiskDict(os.path.join(base_dir, "quizzes"), QuizSheet)
        self.handouts: dict[str, Handout] = DiskDict(os.path.join(base_dir, "handouts"), Handout)

    def add(self, document: Document) -> None:
        self.documents[document.id] = document

    def get(self, document_id: str) -> Document:
        if document_id not in self.documents:
            raise KeyError(document_id)
        return self.documents[document_id]


def _clean(text: str) -> str:
    text = re.sub(r"[\t\r]+", " ", text)
    text = re.sub(r" +", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _split_page(text: str, page: int, start_index: int) -> list[Chunk]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[Chunk] = []
    buffer = ""
    for paragraph in paragraphs:
        if len(buffer) + len(paragraph) < 900:
            buffer = f"{buffer}\n{paragraph}".strip()
        else:
            if buffer:
                chunks.append(Chunk(buffer, page, start_index + len(chunks)))
            buffer = paragraph
    if buffer:
        chunks.append(Chunk(buffer, page, start_index + len(chunks)))
    if not chunks and text.strip():
        chunks.append(Chunk(text[:1200], page, start_index))
    return chunks


MATH_INDICATORS = {
    "\\int", "\\sum", "\\sqrt", "\\frac", "\\lim", "\\alpha", "\\beta", "\\gamma",
    "\\theta", "\\pi", "\\sigma", "\\infty", "\\partial", "\\matrix", "\\begin",
    "\\over", "\\vec", "\\cdot", "\\times", "\\div", "\\pm", "\\mp", "\\neq",
    "\\leq", "\\geq", "\\approx", "\\equiv", "\\propto", "\\in", "\\notin",
    "\\subset", "\\cup", "\\cap", "\\forall", "\\exists",
    "±", "∓", "≠", "≤", "≥", "≈", "≡", "∞", "∫", "∑", "∏", "√", "∛", "∜", "∂",
    "∇", "∈", "∉", "⊂", "⊆", "∪", "∩", "∧", "∨", "¬", "⇒", "⇔", "→", "↑", "↓",
    "°", "℃", "℉", "Å", "μ", "Ω", "π", "θ", "λ", "Δ", "α", "β", "γ", "δ", "ε",
    "ζ", "η", "κ", "μ", "ν", "ξ", "ρ", "σ", "τ", "φ", "χ", "ψ", "ω"
}


def _page_needs_vision(page: typing.Any, text: str) -> bool:
    """判斷 PDF 頁面是否包含圖片、掃描內容、表格結構或數學公式/符號，從而需要 VLM 多模態 Vision 解析。"""
    try:
        if hasattr(page, "get_images") and callable(page.get_images):
            if len(page.get_images()) > 0:
                return True
    except Exception:
        pass

    clean_text = text.strip()

    # 1. 若文字量極少 (例如圖片/掃描頁面)，需走 Vision 解析
    if len(clean_text) < 40:
        return True

    # 2. 檢查是否包含數學/理化公式符號
    if any(indicator in clean_text for indicator in MATH_INDICATORS):
        return True

    # 3. 檢查是否包含表格結構特徵 (如 Markdown 表格豎線 `|` 或連續 Tab 分離)
    if clean_text.count("|") >= 2 or "\t\t" in clean_text:
        return True

    return False


def parse_pdf(
    content: bytes,
    filename: str,
    ai_service: Optional[AIService] = None,
    enable_multimodal: Optional[bool] = None,
) -> Document:
    chunks: list[Chunk] = []
    total_pages = 0

    # 1. 嘗試使用 PyMuPDF + Vision (方案 A) 進行多模態直解 (含 LaTeX 與圖說)
    if enable_multimodal is None:
        enable_multimodal = os.getenv("ENABLE_MULTIMODAL_PARSING", "false").lower() in ("true", "1", "yes")
    enable_smart_routing = os.getenv("ENABLE_SMART_ROUTING", "true").lower() in ("true", "1", "yes")

    if enable_multimodal and ai_service is not None:
        try:
            import pymupdf  # PyMuPDF
            doc = pymupdf.open(stream=content, filetype="pdf")
            total_pages = len(doc)
            dpi = int(os.getenv("MULTIMODAL_DPI", "200"))
            
            max_workers = int(os.getenv("MULTIMODAL_MAX_WORKERS", "10"))
            pages_list = [(page_idx, page) for page_idx, page in enumerate(doc, 1)]

            def _process_page(item: tuple[int, pymupdf.Page]) -> tuple[int, str]:
                page_idx, page = item
                text = _clean(page.get_text() or "")

                # 頁面級智慧分流：若未開啟或判定需要 Vision，走 Vision 管道；否則直接使用本機擷取之純文字
                if enable_smart_routing and not _page_needs_vision(page, text):
                    logging.getLogger(__name__).info("第 %d 頁判定為純文字頁面，走極速本機解析管道", page_idx)
                    return page_idx, text

                try:
                    pix = page.get_pixmap(dpi=dpi)
                    img_bytes = pix.tobytes("png")
                    page_markdown = ai_service._vision_page_to_markdown(img_bytes)
                    if page_markdown and page_markdown.strip():
                        return page_idx, page_markdown
                except Exception as page_exc:
                    logging.getLogger(__name__).warning("第 %d 頁 Vision 解析失敗：%s", page_idx, page_exc)
                return page_idx, text

            actual_workers = max(1, min(max_workers, len(pages_list)))
            with ThreadPoolExecutor(max_workers=actual_workers) as executor:
                page_results = list(executor.map(_process_page, pages_list))

            page_results.sort(key=lambda x: x[0])
            for page_idx, page_markdown in page_results:
                if page_markdown and page_markdown.strip():
                    chunks.extend(_split_page(page_markdown, page_idx, len(chunks)))
        except Exception as exc:
            logging.getLogger(__name__).warning("PyMuPDF 多模態直解失敗，將自動平滑降級為 pypdf 文字模式：%s", exc)
            chunks = []

    # 2. 若多模態模式未啟動、失敗或傳回空資料，自動降級為 pypdf 文字擷取
    if not chunks:
        reader = PdfReader(io.BytesIO(content))
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception as exc:
                raise ValueError("無法讀取加密的 PDF") from exc

        total_pages = len(reader.pages)
        for page_number, page in enumerate(reader.pages, 1):
            text = _clean(page.extract_text() or "")
            chunks.extend(_split_page(text, page_number, len(chunks)))

    if not chunks:
        raise ValueError("PDF 沒有可擷取的文字與影像內容；請確認檔案正常且未毀損")

    return Document(
        id=uuid.uuid4().hex[:12],
        name=filename,
        pages=total_pages,
        chunks=chunks,
        size_bytes=len(content),
    )


def parse_text(content: str, filename: str = "AI_教案教材.md") -> Document:
    clean_text = _clean(content)
    if not clean_text:
        raise ValueError("教材內容不可為空")

    pages_list = [p.strip() for p in re.split(r"\n(?=# |\n---\n)", clean_text) if p.strip()]
    if not pages_list:
        pages_list = [clean_text]

    chunks: list[Chunk] = []
    for page_idx, page_text in enumerate(pages_list, 1):
        chunks.extend(_split_page(page_text, page_idx, len(chunks)))

    return Document(
        id=uuid.uuid4().hex[:12],
        name=filename,
        pages=len(pages_list),
        chunks=chunks,
        size_bytes=len(content.encode("utf-8")),
    )


def _prepare_openai_strict_schema(schema: dict) -> dict:
    """遞迴轉換 JSON Schema 以符合 OpenAI Strict Structured Output 的語義要求 (如包含 additionalProperties: False 與 required 欄位)。"""
    if not isinstance(schema, dict):
        return schema

    cleaned = {}
    unsupported_keys = {"minItems", "maxItems", "minimum", "maximum", "minLength", "maxLength", "pattern", "format", "default"}

    for key, value in schema.items():
        if key in unsupported_keys:
            continue
        if key == "properties" and isinstance(value, dict):
            cleaned_props = {}
            for prop_name, prop_schema in value.items():
                cleaned_props[prop_name] = _prepare_openai_strict_schema(prop_schema)
            cleaned["properties"] = cleaned_props
        elif key == "items" and isinstance(value, dict):
            cleaned["items"] = _prepare_openai_strict_schema(value)
        else:
            cleaned[key] = value

    if cleaned.get("type") == "object" or "properties" in cleaned:
        cleaned["type"] = "object"
        cleaned["additionalProperties"] = False
        if "properties" in cleaned and isinstance(cleaned["properties"], dict):
            cleaned["required"] = list(cleaned["properties"].keys())

    return cleaned


def _sanitize_obj_latex(obj: Any) -> Any:
    """Recursively repair corrupted LaTeX control characters (e.g. \\x08ar -> \\bar, \\x0crac -> \\frac) in dict/list/str."""
    if isinstance(obj, str):
        s = obj
        s = re.sub(r"[\x08]", lambda m: r"\b", s)
        s = re.sub(r"[\x0c]", lambda m: r"\f", s)
        s = re.sub(r"[\x07]", lambda m: r"\a", s)
        s = re.sub(r"[\x0b]", lambda m: r"\v", s)
        s = re.sub(r"\t(heta|imes|an|au|op|ext|o|ilde|tfrac|quad|qquad)\b", lambda m: r"\t" + m.group(1), s)
        s = re.sub(r"\r(ight|ho|ightarrow|angle|floor|ceil)\b", lambda m: r"\r" + m.group(1), s)
        s = re.sub(r"\n(eq|abla|u|otin|ot|atural|earrow|warrow)\b", lambda m: r"\n" + m.group(1), s)
        return s
    elif isinstance(obj, dict):
        return {k: _sanitize_obj_latex(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_sanitize_obj_latex(elem) for elem in obj]
    return obj


def _clean_and_load_json(json_str: str) -> dict:
    try:
        loaded = json.loads(json_str)
        return _sanitize_obj_latex(loaded)
    except json.JSONDecodeError:
        pass

    # 修復未正確轉義的 LaTeX 反斜線與無效 JSON 轉義字元
    # 1. 將常與 JSON 控制跳脫衝突或遺失雙反斜線的 LaTeX 關鍵字補全雙反斜線
    latex_escapes = r"(?<!\\)\\(frac|beta|mathbf|mathrm|begin|bar|binom|bmod|bullet|boldsymbol|big|Big|bigg|Bigg|bot|box|braket|brace|breve|theta|times|tan|tau|top|text|to|tilde|nabla|neq|nu|notin|not|natural|nearrow|nwarrow|right|rho|rightarrow|rangle|vec|alpha|approx|ast|angle|acute|sim|partial|Delta|delta|gamma|lambda|sigma|mu|omega|pi|phi|psi|chi|epsilon|sum|int|div|prime|left|right)\b"
    s = re.sub(latex_escapes, r"\\\\\1", json_str)
    # 2. 修復所有其餘非合法 JSON 轉義的單反斜線 (如 \', \s, \a, \d 等)
    s = re.sub(r'(?<!\\)\\(?!["\\/bfnrt]|u[0-9a-fA-F]{4})', r"\\\\", s)

    try:
        loaded = json.loads(s)
        return _sanitize_obj_latex(loaded)
    except Exception:
        # 二次積極修復：修復除了雙引號與反斜線外的所有孤立反斜線
        repaired2 = re.sub(r'(?<!\\)\\(?!["\\])', r"\\\\", json_str)
        loaded = json.loads(repaired2)
        return _sanitize_obj_latex(loaded)


def _parse_json_response(content: str) -> dict:
    content_clean = content.strip()
    # 處理 reasoning/thinking 標籤 (包含未閉合的 <think>)
    if "</think>" in content_clean:
        content_clean = content_clean.split("</think>")[-1].strip()

    match = re.search(r"```(?:json)?\s*(\{.*\}|\[.*\])\s*```", content_clean, re.DOTALL)
    if match:
        return _clean_and_load_json(match.group(1).strip())

    start_idx = content_clean.find("{")
    end_idx = content_clean.rfind("}")
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        json_str = content_clean[start_idx : end_idx + 1]
        try:
            return _clean_and_load_json(json_str)
        except Exception:
            pass

def _search_web_for_context(query_str: str) -> str:
    clean_q = re.sub(r"[：:｜|—\-_【】\[\]\(\)（）？?！!，,。.]", " ", query_str)
    clean_q = re.sub(r"\s+", " ", clean_q).strip()[:50] or query_str[:50]
    try:
        from duckduckgo_search import DDGS
        results = list(DDGS(timeout=10).text(clean_q, max_results=3))
        if results:
            formatted = []
            for item in results:
                formatted.append(f"標題：{item.get('title', '')}\n摘要：{item.get('body', '')}")
            return "\n\n".join(formatted)
    except Exception as exc:
        logging.getLogger(__name__).warning("DuckDuckGo 網路搜尋補充失敗：%s", exc)
def _get_tone_and_audience_guidance(tone: str = "清楚易懂", target_audience: str = "一般大眾/初學者") -> str:
    parts = [
        f"【學習對象客製規範（目標：{target_audience}）】",
    ]
    if any(k in target_audience for k in ["國中", "國小", "初學", "入門", "基礎"]):
        parts.append(
            "- 針對初學/國中/基礎對象：必須深入淺出、連結日常生活經驗，嚴禁直接堆砌艱澀冷僻的術語或無解釋的公式。遇到公式時，務必提供生活化的直觀概念與物理意義。"
        )
    elif any(k in target_audience for k in ["高中", "升學"]):
        parts.append(
            "- 針對高中/升學對象：重在概念本質與因果邏輯推導，兼顧考試重點觀念辨析與生活現象應用。"
        )
    elif any(k in target_audience for k in ["大學", "專業", "工程", "研究"]):
        parts.append(
            "- 針對大學/專業對象：強調學術嚴謹度、系統性架構推導、邊界條件與進階原理探討。"
        )
    else:
        parts.append(
            "- 兼顧易讀性與知識深度，邏輯清晰、循序漸進。"
        )

    parts.append(f"\n【教學語氣風格貫徹規範（風格：{tone}）】")
    if "故事" in tone:
        parts.append(
            "- 【故事引導與情境破題】：每個章節的摘要 (summary) 或開場，請務必採用引人入勝的生活情境謎題、科學史探索歷程、科學家發現故事、生活冒險或日常困境破題（例如：牛頓為什麼坐在蘋果樹下？太空人在無重力下推購物車會發生什麼事？切開的蘋果為什麼會變褐色？鐵達尼號為何會沉沒？），激發強烈好奇心與沉浸感。\n"
            "- 【生活化比喻（Metaphor）化解抽象公式】：凡涉及理化公式、定律或抽象概念（如 F=ma、氧化還原、密度、浮力、能量守恆等），嚴禁單純冰冷條列定義，必須搭配鮮活的生活化比喻（例如用推購物車比喻加速度、用男女舞伴配對比喻置換反應、用游泳圈比喻浮力），將公式轉化為生動的情境推演。\n"
            "- 【情境式探究思考題】：思考與討論題 (discussion_questions) 請以「情境偵探/小小科學家探究」視角設計，引導學生融入情境思考。"
        )
    elif "活潑" in tone or "互動" in tone:
        parts.append(
            "- 【活潑互動與探究問答】：語氣熱情親切，多運用啟發式問句（如「你有沒有想過...？」、「如果是你，你會怎麼解開這個謎題？」）。\n"
            "- 穿插生活動手小挑戰、趣味小實驗或日常生活現象觀察，引導學員主動參與。"
        )
    elif "專業" in tone or "嚴謹" in tone:
        parts.append(
            "- 【專業嚴謹與精確演繹】：術語精確、邏輯嚴密，著重定律定義的邊界條件、數理邏輯推導與系統化架構整理。"
        )
    else:  # 清楚易懂
        parts.append(
            "- 【清楚易懂與化繁為簡】：使用平實白話文，步驟拆解分明，將複雜觀念拆解為直觀好吸收的重點清單與複習架構。"
        )

    return "\n".join(parts)


class AIService:
    def __init__(self) -> None:
        self.openai = None
        self.gemini_client = None
        self.ollama = None
        self._embedder = None
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.qa_graph = build_qa_graph()
        self.deck_graph = build_deck_graph()
        self.quiz_graph = build_quiz_graph()

        initial_provider = os.getenv("AI_PROVIDER", "gemini").strip().lower()
        valid_providers = {"openai", "gemini", "ollama", "ollama_cloud", "ollama_local"}
        self.set_provider(initial_provider if initial_provider in valid_providers else "gemini")

    def set_provider(self, provider: str) -> dict[str, str]:
        from dotenv import load_dotenv
        load_dotenv(override=True)
        provider = provider.strip().lower()
        if provider == "ollama":
            base_url = os.getenv("OLLAMA_BASE_URL", "")
            provider = "ollama_local" if "localhost" in base_url or "127.0.0.1" in base_url else "ollama_cloud"

        if provider not in {"openai", "gemini", "ollama_cloud", "ollama_local"}:
            raise ValueError("AI_PROVIDER 必須是 gemini, openai, ollama_cloud 或 ollama_local")

        if provider == "gemini":
            if self.gemini_client is None and self.gemini_api_key:
                try:
                    from google import genai
                    self.gemini_client = genai.Client(api_key=self.gemini_api_key)
                except Exception as exc:
                    logging.getLogger(__name__).warning("Gemini Client 初始化失敗：%s", exc)
            self.model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
            self.embedding_model = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-2")

        elif provider == "openai":
            if not self.api_key:
                raise ValueError("未設定 OPENAI_API_KEY，無法切換至 OpenAI")
            if self.openai is None:
                from openai import OpenAI

                self.openai = OpenAI(api_key=self.api_key)
            self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            self.embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

        elif provider == "ollama_local":
            from ollama import Client
            local_url = os.getenv("OLLAMA_LOCAL_URL", "http://localhost:11434")
            local_client = Client(host=local_url)
            try:
                local_client.list()
            except Exception as exc:
                raise ValueError(f"未偵測到 Ollama 本機服務，請確認已安裝並啟動 Ollama ({local_url})。") from exc

            self.ollama = local_client
            self.model = os.getenv("OLLAMA_LOCAL_MODEL", os.getenv("OLLAMA_MODEL", "qwen2.5:3b"))
            self.embedding_model = os.getenv(
                "HUGGINGFACE_EMBEDDING_MODEL",
                "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            )

        elif provider == "ollama_cloud":
            from ollama import Client
            cloud_url = os.getenv("OLLAMA_BASE_URL", "https://api.ollama.com")
            ollama_key = os.getenv("OLLAMA_API_KEY", "").strip()
            headers = {"Authorization": f"Bearer {ollama_key}"} if ollama_key else {}
            self.ollama = Client(host=cloud_url, headers=headers)
            self.model = os.getenv("OLLAMA_MODEL", "deepseek-v4-flash:0731")
            self.embedding_model = os.getenv("OLLAMA_EMBEDDING_MODEL", "bge-m3")

        self.provider = provider
        return self.info

    @property
    def info(self) -> dict[str, str]:
        labels = {
            "gemini": "Gemini 雲端 API",
            "openai": "OpenAI 雲端 API",
            "ollama_cloud": "Ollama 雲端 API",
            "ollama_local": "Ollama 本機服務",
        }
        label = labels.get(self.provider, "Ollama")
        return {
            "provider": self.provider,
            "provider_label": label,
            "generation_model": self.model,
            "embedding_model": self.embedding_model,
        }

    def _vision_page_to_markdown(self, img_bytes: bytes) -> str:
        """使用 VLM 進行 Vision-Native 多模態頁面直解 (提取表格、LaTeX 公式與觀念圖說)"""
        prompt = (
            "你是一個專業的教材文件 Vision-to-Markdown 解析專家。請分析這張教材頁面圖片，將其轉譯為標準 Markdown 格式：\n"
            "1. 數學公式與理化符號：請將所有單行或獨立公式轉譯為標準 LaTeX 語法（例如 `$E=mc^2$` 或 `$$\\frac{-b \\pm \\sqrt{b^2-4ac}}{2a}$$`）。\n"
            "2. 表格：請轉為標準 Markdown 表格格式。\n"
            "3. 圖片與圖表：請插入 `![圖說描述](fig)` 並詳細說明圖片呈現的觀念、數據與實驗結果。\n"
            "4. 保持原本的章節標題階層 (#, ##, ###) 與排版順序。"
        )

        import base64
        b64_str = base64.b64encode(img_bytes).decode("utf-8")

        if self.provider == "gemini" and self.gemini_client is not None:
            try:
                from google.genai import types
                response = self.gemini_client.models.generate_content(
                    model=self.model,
                    contents=[
                        types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                        prompt,
                    ],
                )
                return (response.text or "").strip()
            except Exception as exc:
                logging.getLogger(__name__).warning("Gemini Vision 解析失敗：%s", exc)

        elif self.provider == "openai" and self.openai is not None:
            try:
                response = self.openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_str}"}},
                            ],
                        }
                    ],
                    max_tokens=2000,
                )
                return (response.choices[0].message.content or "").strip()
            except Exception as exc:
                logging.getLogger(__name__).warning("OpenAI Vision 解析失敗：%s", exc)

        elif self.provider in ("ollama_cloud", "ollama_local") and self.ollama is not None:
            try:
                vision_model = os.getenv("OLLAMA_CLOUD_VISION_MODEL" if self.provider == "ollama_cloud" else "OLLAMA_LOCAL_VISION_MODEL", "qwen2-vl:7b")
                response = self.ollama.chat(
                    model=vision_model,
                    messages=[{"role": "user", "content": prompt, "images": [b64_str]}],
                )
                message = response.message if hasattr(response, "message") else response["message"]
                return (message.content if hasattr(message, "content") else message["content"]).strip()
            except Exception as exc:
                logging.getLogger(__name__).warning("Ollama Vision 解析失敗：%s", exc)

        return ""

    def _embed(self, texts: list[str], *, query: bool = False) -> list[list[float]]:
        if self.provider == "gemini" and self.gemini_client is not None:
            try:
                from google.genai import types
                vectors = []
                batch_size = 50
                for i in range(0, len(texts), batch_size):
                    batch = texts[i : i + batch_size]
                    contents = [types.Content(parts=[types.Part.from_text(text=t)]) for t in batch]
                    res = self.gemini_client.models.embed_content(
                        model=self.embedding_model,
                        contents=contents,
                    )
                    if hasattr(res, "embeddings") and res.embeddings:
                        for emb in res.embeddings:
                            vectors.append(emb.values if hasattr(emb, "values") else list(emb))
                if vectors:
                    return vectors
            except Exception as exc:
                logging.getLogger(__name__).warning("Gemini Embedding 計算失敗：%s", exc)

        if self.provider == "openai" and self.openai is not None:
            response = self.openai.embeddings.create(model=self.embedding_model, input=texts)
            return [item.embedding for item in response.data]

        if self.provider == "ollama_cloud" and self.ollama is not None:
            try:
                # 嘗試呼叫 Ollama 原生 embed API
                if hasattr(self.ollama, "embed"):
                    res = self.ollama.embed(model=self.embedding_model, input=texts)
                    embeddings = res.embeddings if hasattr(res, "embeddings") else res.get("embeddings", [])
                    if embeddings:
                        return embeddings
            except Exception as exc:
                logging.getLogger(__name__).warning("Ollama Cloud embed API 呼叫失敗，將降級為本地模型：%s", exc)

        # 延遲載入 (Lazy Loading) 本地 Hugging Face Embedding 模型 (避免在雲端模式下浪費 GB 級 RAM)
        try:
            if self._embedder is None:
                from sentence_transformers import SentenceTransformer
                hf_model = os.getenv("HUGGINGFACE_EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
                self._embedder = SentenceTransformer(hf_model)
            method_name = "encode_query" if query and hasattr(self._embedder, "encode_query") else "encode_document"
            method = getattr(self._embedder, method_name, self._embedder.encode)
            vectors = method(texts, normalize_embeddings=True, show_progress_bar=False)
            return vectors.tolist() if hasattr(vectors, "tolist") else [list(vector) for vector in vectors]
        except Exception as exc:
            raise RuntimeError(f"Embedding 模型載入或推論失敗：{exc}") from exc

    def index(self, document: Document) -> None:
        document.vectors = self._embed([chunk.text for chunk in document.chunks])

    def retrieve(self, document: Document, query: str, limit: int = 4) -> list[tuple[Chunk, float]]:
        if not document.vectors:
            self.index(document)
        query_vector = self._embed([query], query=True)[0]
        if document.vectors and len(document.vectors[0]) != len(query_vector):
            self.index(document)
        ranked = []
        for chunk, vector in zip(document.chunks, document.vectors):
            dot = sum(a * b for a, b in zip(query_vector, vector))
            denom = math.sqrt(sum(a * a for a in query_vector)) * math.sqrt(sum(b * b for b in vector))
            ranked.append((chunk, dot / denom if denom else 0.0))
        ranked.sort(key=lambda pair: pair[1], reverse=True)
        return ranked[:limit]

    def _text_response(self, system: str, prompt: str) -> str:
        last_exc = None
        if self.provider == "gemini" and self.gemini_client is not None:
            import time
            for attempt in range(2):
                try:
                    from google.genai import types
                    response = self.gemini_client.models.generate_content(
                        model=self.model,
                        contents=prompt,
                        config=types.GenerateContentConfig(system_instruction=system, temperature=0.1),
                    )
                    return (response.text or "").strip()
                except Exception as exc:
                    last_exc = exc
                    if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc):
                        logging.getLogger(__name__).warning("Gemini 遭遇 429 速率限制，等待 1.5 秒後進行重試...")
                        time.sleep(1.5)
                        continue
                    logging.getLogger(__name__).warning("Gemini 文字生成失敗：%s", exc)
                    break

        if self.provider == "openai" and self.openai is not None:
            try:
                response = self.openai.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.1,
                )
                return (response.choices[0].message.content or "").strip()
            except Exception as exc:
                logging.getLogger(__name__).warning("OpenAI 文字生成失敗：%s", exc)
                raise RuntimeError(f"OpenAI 生成失敗：{exc}") from exc

        # 嘗試 Ollama (作為主提供商或備援提供商)
        ollama_client = self.ollama
        ollama_model = self.model
        if ollama_client is None:
            try:
                from ollama import Client
                local_url = os.getenv("OLLAMA_LOCAL_URL", "http://localhost:11434")
                test_client = Client(host=local_url)
                test_client.list()
                ollama_client = test_client
                ollama_model = os.getenv("OLLAMA_LOCAL_MODEL", os.getenv("OLLAMA_MODEL", "qwen2.5:7b"))
            except Exception as ollama_err:
                logging.getLogger(__name__).warning("無法連接本地 Ollama 備援服務：%s", ollama_err)
                ollama_client = None

        if ollama_client is None:
            raise RuntimeError(f"文字生成失敗且無可用備援模型：{last_exc if last_exc else 'Provider 異常'}")

        try:
            response = ollama_client.chat(
                model=ollama_model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                stream=False,
                options={"temperature": 0.1},
            )
            message = response.message if hasattr(response, "message") else response["message"]
            return (message.content if hasattr(message, "content") else message["content"]).strip()
        except Exception as exc:
            raise RuntimeError(
                f"Ollama 回應失敗；請確認服務已啟動且已執行 `ollama pull {ollama_model}`：{exc}"
            ) from exc

    def _structured_response(self, system: str, prompt: str, schema: dict) -> dict:
        last_exc = None
        if self.provider == "gemini" and self.gemini_client is not None:
            import time
            for attempt in range(2):
                try:
                    from google.genai import types
                    response = self.gemini_client.models.generate_content(
                        model=self.model,
                        contents=prompt + f"\n\n請務必輸出符合結構的 JSON。\nSchema: {json.dumps(schema, ensure_ascii=False)}",
                        config=types.GenerateContentConfig(
                            system_instruction=system,
                            response_mime_type="application/json",
                            temperature=0,
                        ),
                    )
                    return _parse_json_response(response.text or "{}")
                except Exception as exc:
                    last_exc = exc
                    if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc):
                        logging.getLogger(__name__).warning("Gemini 遭遇 429 速率限制，等待 1.5 秒後進行重試...")
                        time.sleep(1.5)
                        continue
                    logging.getLogger(__name__).warning("Gemini 結構化輸出失敗 (嘗試 %d)：%s", attempt + 1, exc)
                    break

        if self.provider == "openai" and self.openai is not None:
            try:
                strict_schema = _prepare_openai_strict_schema(schema)
                response = self.openai.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": "structured_output",
                            "strict": True,
                            "schema": strict_schema,
                        },
                    },
                    temperature=0,
                )
                content = response.choices[0].message.content or "{}"
                return _parse_json_response(content)
            except Exception as exc:
                logging.getLogger(__name__).warning("OpenAI 結構化輸出 (strict json_schema) 失敗，將降級為 json_object 模式：%s", exc)
                try:
                    response = self.openai.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system},
                            {"role": "user", "content": prompt + f"\n\n請務必僅輸出合法 JSON，Schema 規定如下：\n{json.dumps(schema, ensure_ascii=False)}"},
                        ],
                        response_format={"type": "json_object"},
                        temperature=0,
                    )
                    content = response.choices[0].message.content or "{}"
                    return _parse_json_response(content)
                except Exception as fallback_exc:
                    raise RuntimeError(f"OpenAI 內容生成失敗：{fallback_exc}") from fallback_exc

        # 嘗試 Ollama (作為主提供商或備援提供商)
        ollama_client = self.ollama
        ollama_model = self.model
        if ollama_client is None:
            try:
                from ollama import Client
                local_url = os.getenv("OLLAMA_LOCAL_URL", "http://localhost:11434")
                test_client = Client(host=local_url)
                test_client.list()
                ollama_client = test_client
                ollama_model = os.getenv("OLLAMA_LOCAL_MODEL", os.getenv("OLLAMA_MODEL", "qwen2.5:7b"))
            except Exception as ollama_err:
                logging.getLogger(__name__).warning("無法連接本地 Ollama 備援服務：%s", ollama_err)
                ollama_client = None

        if ollama_client is None:
            raise RuntimeError(f"結構化輸出失敗且無可用備援模型：{last_exc if last_exc else 'Provider 異常'}")
        
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt + "\n\n請嚴格依照指定 JSON schema 輸出。"},
        ]
        try:
            response = ollama_client.chat(
                model=ollama_model,
                messages=messages,
                format=schema,
                stream=False,
                options={"temperature": 0},
            )
            message = response.message if hasattr(response, "message") else response["message"]
            content = message.content if hasattr(message, "content") else message["content"]
            return _parse_json_response(content)
        except Exception as exc_schema:
            try:
                fallback_prompt = prompt + f"\n\n請務必僅輸出合法 JSON，Schema 規定如下：\n{json.dumps(schema, ensure_ascii=False)}"
                response = ollama_client.chat(
                    model=ollama_model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": fallback_prompt},
                    ],
                    format="json",
                    stream=False,
                    options={"temperature": 0},
                )
                message = response.message if hasattr(response, "message") else response["message"]
                content = message.content if hasattr(message, "content") else message["content"]
                return _parse_json_response(content)
            except Exception as exc_json:
                raise RuntimeError(
                    f"Ollama 結構化輸出失敗；請確認模型 `{ollama_model}` 可用：{exc_schema} | {exc_json}"
                ) from exc_json

    def ask(
        self,
        document: Document,
        question: str,
        enable_web_search: bool = False,
        history: Optional[list[dict]] = None,
    ) -> tuple[str, list[Source], str]:
        initial_state = {
            "question": question,
            "document": document,
            "enable_web_search": enable_web_search,
            "history": history or [],
            "ai_service": self,
        }
        result = self.qa_graph.invoke(initial_state)
        answer = result.get("answer", "")
        sources = result.get("sources", [])
        return answer, sources, self.provider

    def generate_deck(
        self,
        document: Document,
        audience: str,
        tone: str,
        slide_count: int,
        duration: int,
        enable_web_search: bool = False,
        language: str = "zh-TW",
        handout_text: Optional[str] = None,
    ) -> Deck:
        initial_state = {
            "document": document,
            "audience": audience,
            "tone": tone,
            "language": language,
            "slide_count": slide_count,
            "duration": duration,
            "enable_web_search": enable_web_search,
            "handout_text": handout_text,
            "ai_service": self,
        }
        result = self.deck_graph.invoke(initial_state)
        deck = result.get("deck")
        if not deck:
            raise RuntimeError("簡報生成圖未傳回有效 Deck 物件")
        return deck

    def generate_quiz(
        self,
        document: Document,
        question_count: int = 5,
        difficulty: str = "all",
        audience: str = "大學生",
        tone: str = "清楚易懂",
        enable_web_search: bool = False,
        language: str = "zh-TW",
        handout_text: Optional[str] = None,
    ) -> QuizSheet:
        initial_state = {
            "document": document,
            "question_count": question_count,
            "difficulty": difficulty,
            "audience": audience,
            "tone": tone,
            "language": language,
            "enable_web_search": enable_web_search,
            "handout_text": handout_text,
            "ai_service": self,
        }
        result = self.quiz_graph.invoke(initial_state)
        quiz_sheet = result.get("quiz_sheet")
        if not quiz_sheet:
            raise RuntimeError("題目卷生成圖未傳回有效 QuizSheet 物件")
        return quiz_sheet

    def generate_handout(
        self,
        document: Document,
        target_audience: str = "大學生",
        tone: str = "清楚易懂",
        detail_level: str = "standard",
        language: str = "zh-TW",
        enable_web_search: bool = False,
    ) -> Handout:
        total_chunks = len(document.chunks)
        sample_k = min(12, total_chunks)
        step = max(1, total_chunks // sample_k) if total_chunks > 0 else 1
        sampled = [document.chunks[i] for i in range(0, total_chunks, step)][:sample_k]
        context = "\n---\n".join(f"[第 {c.page} 頁段落]\n{c.text[:800]}" for c in sampled)

        web_context = ""
        if enable_web_search:
            search_query = f"{document.name} 核心觀念 重點整理"
            web_results = _search_web_for_context(search_query)
            if web_results:
                web_context = f"\n\n【連網補充題材與資料】\n{web_results}"

        tone_guidance = _get_tone_and_audience_guidance(tone=tone, target_audience=target_audience)

        system = (
            "你是一位頂級資深教育名師與課程講義設計專家。"
            f"請根據所提供的教材內容，為學習對象【{target_audience}】以【{tone}】的教學語氣，設計一份條理分明、重點突出、引人入勝且易於複習的【A4 隨堂講義與學習手冊】。\n\n"
            f"{tone_guidance}\n\n"
            "【排版與數學公式規範】\n"
            "1. 數學與理化公式：教材中凡涉及任何數學公式、物理定律、化學式、變數或計算式，請務必一律使用標準 LaTeX 格式包裹（行內公式與變數使用 $...$ 例如 `$F=ma$` 或 `$\\vec{F}=m\\vec{a}$`；獨立核心公式使用 $$...$$ 例如 `$$F = G\\frac{m_1 m_2}{r^2}$$` 或 `$$E = mc^2$$`）。切勿使用純文字 ASCII 拼湊排版（例如切勿寫成 F=ma 或 m1m2/r^2）。\n"
            "2. 講義內容結構應扎實：摘要應生動扣題，核心要點 (key_points) 請條列分明並標記重點，思考題 (discussion_questions) 具啟發性。\n"
            "3. 講義架構應包含：\n"
            "   - 課程總覽 (overview)\n"
            "   - 3~6 個核心章節 (sections)，每章節包含摘要 (summary)、核心要點 (key_points)、思考與討論題 (discussion_questions)，以及出處頁碼 (source_pages)\n"
            "   - 課後核心總結與心智圖綱要 (key_takeaways)\n"
            "請嚴格依指定 JSON 格式輸出。"
        )

        schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "subtitle": {"type": "string"},
                "overview": {"type": "string"},
                "sections": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "summary": {"type": "string"},
                            "key_points": {"type": "array", "items": {"type": "string"}},
                            "discussion_questions": {"type": "array", "items": {"type": "string"}},
                            "source_pages": {"type": "array", "items": {"type": "integer"}},
                        },
                        "required": ["title", "summary", "key_points", "discussion_questions", "source_pages"],
                    },
                },
                "key_takeaways": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["title", "subtitle", "overview", "sections", "key_takeaways"],
        }

        prompt = (
            f"教材名稱：{document.name}\n"
            f"學習對象：{target_audience}\n"
            f"教學語氣：{tone}\n"
            f"詳細程度：{detail_level}\n"
            f"輸出語言：{language}\n\n"
            f"【教材內容摘要段落】\n{context}"
            f"{web_context}\n\n"
            "請開始生成完整的隨堂講義 JSON。"
        )

        res = self._structured_response(system, prompt, schema)
        sections = []
        for s in res.get("sections", []):
            sections.append(
                HandoutSection(
                    title=s.get("title", ""),
                    summary=s.get("summary", ""),
                    key_points=s.get("key_points", []),
                    discussion_questions=s.get("discussion_questions", []),
                    source_pages=s.get("source_pages", []),
                )
            )

        handout = Handout(
            id=str(uuid.uuid4()),
            document_id=document.id,
            title=res.get("title", document.name.replace(".pdf", "") + " 隨堂學習講義"),
            subtitle=res.get("subtitle", f"適用對象：{target_audience} · 深度備課手冊"),
            overview=res.get("overview", ""),
            sections=sections,
            key_takeaways=res.get("key_takeaways", []),
        )
        return handout

    def refine_slide(
        self,
        slide: Slide,
        instruction: str = "潤飾講稿與要點，使口語表達更自然、生動且具啟發性",
        document: Optional[Document] = None,
    ) -> Slide:
        system = (
            "你是一位頂尖教學演講與簡報口語教練。"
            "請根據使用者的潤飾指示，針對當前單頁投影片的條列重點 (bullets) 與逐頁講稿 (speaker_notes) 進行局部優化與微調。"
            "條列要點請精簡精準 (3~5 點)，講稿請口語自然、生動流暢並點出思考引導。"
        )
        prompt = (
            f"投影片標題：{slide.title}\n"
            f"目前條列重點：{slide.bullets}\n"
            f"目前講稿：{slide.speaker_notes}\n"
            f"潤飾需求指示：{instruction}\n\n"
            "請輸出優化後的條列重點與講稿 JSON。"
        )
        schema = {
            "type": "object",
            "properties": {
                "bullets": {"type": "array", "items": {"type": "string"}},
                "speaker_notes": {"type": "string"},
            },
            "required": ["bullets", "speaker_notes"],
            "additionalProperties": False,
        }
        try:
            res = self._structured_response(system, prompt, schema)
            new_bullets = res.get("bullets") or slide.bullets
            new_notes = res.get("speaker_notes") or slide.speaker_notes
            return Slide(
                title=slide.title,
                bullets=new_bullets,
                speaker_notes=new_notes,
                source_pages=slide.source_pages,
                icon=slide.icon,
                visual_description=slide.visual_description,
                visual_diagram=slide.visual_diagram,
            )
        except Exception as exc:
            logging.getLogger(__name__).warning("投影片 AI 潤飾失敗，保留原講稿: %s", exc)
            return slide

    def regenerate_quiz_question(
        self,
        current_question: QuizQuestion,
        instruction: str = "抽換為同概念但不同情境/題型的新題目",
        difficulty: str = "medium",
        language: str = "zh-TW",
        document: Optional[Document] = None,
    ) -> QuizQuestion:
        context = ""
        if document:
            try:
                retrieved = self.retrieve(document, current_question.question, limit=3)
                context = "\n\n".join(f"[第 {c.page} 頁] {c.text}" for c, _score in retrieved)
            except Exception:
                pass

        system = (
            "你是一位資深命題評量專家。請為教師抽換或重新設計一道高品質評量試題。\n"
            "【規範】：\n"
            "1. 題型 (type)：可為 'single_choice' (單選題, 4 個 options), 'multiple_choice' (多選題), 或 'problem_solving' (計算推導題, options 為空陣列)。\n"
            "2. 公式請使用標準 LaTeX 格式（例如 `$E=mc^2$`）。\n"
            "3. 詳解 (explanation) 須包含完整觀念解析與易錯點分析。"
        )
        prompt = (
            f"原題目：{current_question.question}\n"
            f"原題型：{current_question.type}\n"
            f"難度傾向：{difficulty or current_question.difficulty}\n"
            f"抽換/修改指示：{instruction}\n"
            f"教材背景脈絡：\n{context or '依原題核心知識點衍生新題目'}\n\n"
            "請輸出全新替換題目的 JSON。"
        )
        schema = {
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
        }
        res = self._structured_response(system, prompt, schema)
        return QuizQuestion(
            id=current_question.id,
            type=res.get("type", current_question.type),
            question=res.get("question", current_question.question),
            options=res.get("options", current_question.options),
            answer=res.get("answer", current_question.answer),
            explanation=res.get("explanation", current_question.explanation),
            source_pages=res.get("source_pages", current_question.source_pages),
            difficulty=res.get("difficulty", current_question.difficulty),
        )




SUPERSCRIPTS_MAP = {
    "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
    "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹",
    "+": "⁺", "-": "⁻", "=": "⁼", "(": "⁽", ")": "⁾",
    "n": "ⁿ", "i": "ⁱ", "t": "ᵗ"
}

SUBSCRIPTS_MAP = {
    "0": "₀", "1": "₁", "2": "₂", "3": "₃", "4": "₄",
    "5": "₅", "6": "₆", "7": "₇", "8": "₈", "9": "₉",
    "+": "₊", "-": "₋", "=": "₌", "(": "₍", ")": "₎",
    "a": "ₐ", "e": "ₑ", "h": "ₕ", "i": "ᵢ", "j": "ⱼ",
    "k": "ₖ", "l": "ₗ", "m": "ₘ", "n": "ₙ", "o": "ₒ",
    "p": "ₚ", "r": "ᵣ", "s": "ₛ", "t": "ₜ", "u": "ᵤ", "v": "ᵥ", "x": "ₓ", "y": "ᵧ"
}

GREEK_AND_SYMBOLS_MAP = {
    r"\alpha": "α", r"\beta": "β", r"\gamma": "γ", r"\delta": "δ", r"\Delta": "Δ",
    r"\epsilon": "ε", r"\zeta": "ζ", r"\eta": "η", r"\theta": "θ", r"\Theta": "Θ",
    r"\lambda": "λ", r"\Lambda": "Λ", r"\mu": "μ", r"\nu": "ν", r"\xi": "ξ",
    r"\pi": "π", r"\Pi": "Π", r"\rho": "ρ", r"\sigma": "σ", r"\Sigma": "Σ",
    r"\tau": "τ", r"\phi": "φ", r"\Phi": "Φ", r"\chi": "χ", r"\psi": "ψ",
    r"\omega": "ω", r"\Omega": "Ω",
    r"\times": "×", r"\cdot": "·", r"\approx": "≈", r"\pm": "±",
    r"\mp": "∓", r"\le": "≤", r"\leq": "≤", r"\ge": "≥", r"\geq": "≥",
    r"\neq": "≠", r"\equiv": "≡", r"\infty": "∞", r"\propto": "∝", r"\partial": "∂",
    r"\nabla": "∇", r"\rightarrow": "→", r"\to": "→", r"\leftarrow": "←",
    r"\Rightarrow": "⇒", r"\Leftarrow": "⇐",
    r"\degree": "°", r"\circ": "°", r"\sum": "∑", r"\int": "∫",
    r"\sim": "∼", r"\div": "÷", r"\in": "∈", r"\notin": "∉",
    r"\subset": "⊂", r"\subseteq": "⊆", r"\cap": "∩", r"\cup": "∪",
    r"\,": " ", r"\;": " ", r"\quad": "  ", r"\qquad": "   ",
}


def sanitize_latex_escapes(text: str) -> str:
    """Repair corrupted LaTeX escape sequences caused by JSON / ASCII escape parsing (e.g. \\x08ar -> \\bar, \\x0crac -> \\frac)."""
    if not text:
        return ""
    import re
    s = str(text)
    s = re.sub(r"[\x08]", lambda m: r"\b", s)
    s = re.sub(r"[\x0c]", lambda m: r"\f", s)
    s = re.sub(r"[\x07]", lambda m: r"\a", s)
    s = re.sub(r"[\x0b]", lambda m: r"\v", s)
    s = re.sub(r"\t(heta|imes|an|au|op|ext|o|ilde|tfrac|quad|qquad)\b", lambda m: r"\t" + m.group(1), s)
    s = re.sub(r"\r(ight|ho|ightarrow|angle|floor|ceil)\b", lambda m: r"\r" + m.group(1), s)
    s = re.sub(r"\n(eq|abla|u|otin|ot|atural|earrow|warrow)\b", lambda m: r"\n" + m.group(1), s)
    return s


def auto_repair_math_expressions(text: str) -> str:
    """Comprehensive normalizer and repair engine for LaTeX formulas, control characters, bare math expressions and corrupted tokens."""
    if not text:
        return ""
    import re
    s = str(text)

    # 1. 修復 ASCII 控制字元 (\x0crac -> \frac, \x08eta -> \beta 等)
    s = sanitize_latex_escapes(s)

    # 2. 修復常見畸變之裸 frac 模式 (例如 fracab -> \frac{a}{b}, frac13 -> \frac{1}{3}, frac100100 -> \frac{100}{100})
    s = re.sub(r'\bfrac([a-zA-Z])([a-zA-Z])\b', r'\\frac{\1}{\2}', s)
    s = re.sub(r'\bfrac([0-9])([0-9])\b', r'\\frac{\1}{\2}', s)
    s = re.sub(r'\bfrac([0-9]+)\s+([0-9]+)\b', r'\\frac{\1}{\2}', s)
    s = re.sub(r'\bfrac100100\b', r'\\frac{100}{100}', s)
    s = re.sub(r'\bfrac([a-zA-Z0-9]+)\s*\+\s*([a-zA-Z0-9]+)\s+([a-zA-Z0-9]+)\s*\+\s*([a-zA-Z0-9]+)\b', r'\\frac{\1+\2}{\3+\4}', s)
    s = re.sub(r'\bfracatimescbtimesd\b', r'\\frac{a \\times c}{b \\times d}', s)

    # 3. 修復常見運算子 (neq0 -> \neq 0, times -> \times 等)
    s = re.sub(r'\bneq\s*([0-9a-zA-Z])', r'\\neq \1', s)
    s = re.sub(r"(?<=[0-9a-zA-Z}\^\-\)\'\"\]])(\s*)times(\s*)(?=[0-9a-zA-Z{\\\(\'\"\[])", r"\1\\times\2", s)
    s = re.sub(r'(?<![\\a-zA-Z])\btimes\b(?![a-zA-Z])', r'\\times', s)

    # 4. 修復雙反斜線混用 (\\left, \\frac, \\right, \\times -> \left, \frac, \right, \times)
    s = re.sub(r'\\\\([a-zA-Z]+|[{}[\](),;])', r'\\\1', s)

    # 5. 將所有尚未被 $ 包裹的完整數學表達式與 LaTeX 指令包裹於 $...$
    return _wrap_bare_latex(s)


def _wrap_bare_latex(text: str) -> str:
    """Auto-wrap bare LaTeX expressions and complex mathematical formulas in $...$ if not already wrapped."""
    if not text:
        return ""
    import re
    text = sanitize_latex_escapes(text)

    # 分割出已用 $...$ 或 $$...$$ 或 \[...\] 或 \(...\) 包裹的片段
    parts = re.split(r'(\$\$[\s\S]*?\$\$|\$[^$\n]+?\$|\\\[[\s\S]*?\\\]|\\\([\s\S]*?\\\))', text)
    result = []

    atom = r'(?:\\left[\[(][\s\S]*?\\right[\])]|\\[a-zA-Z]+(?:\[[^\]\n]*\])?(?:\{[^{}\n]*\})*|[0-9a-zA-Z]+(?:\^|\_)(?:\{[^{}\n]*\}|[0-9a-zA-Z+\-]+)|\([^\u4e00-\u9fff\n()]+\)|\[[^\u4e00-\u9fff\n\[\]]+\]|[0-9a-zA-Z\.\']+|[+\-/=<>~×÷≤≥≠≈≡±∓∝∂∇→←⇒⇐∑∫⊕·°])'
    op_or_space = r'(?:\s*[\s+\-/=<>~×÷≤≥≠≈≡±∓∝∂∇→←⇒⇐∑∫⊕·°|^_]\s*|\s*\\(?:times|div|cdot|approx|sim|neq|equiv|pm|mp|le|ge|leq|geq|in|notin|subset|cap|cup|rightarrow|to|oplus|otimes|circ)\s*)'
    full_expr = rf'(?:{atom}(?:{op_or_space}{atom})*)'
    expr_regex = re.compile(full_expr)

    for i, part in enumerate(parts):
        if i % 2 == 1:
            result.append(part)
        else:
            if not part:
                continue
            def _wrap(m):
                val = m.group(0).strip()
                if not val or val.startswith('$'):
                    return m.group(0)
                # Ignore markdown emphasis/backticks
                if val.startswith('*') or val.endswith('*') or val.startswith('`') or val.endswith('`'):
                    return m.group(0)
                if not re.search(r'[\\[\]{}^=+\-/<>~×÷≤≥≠≈≡±∓→←⊕·°]', val) and '\\' not in val and '^' not in val and '_' not in val:
                    return m.group(0)
                return f"${val}$"

            wrapped = expr_regex.sub(_wrap, part)
            result.append(wrapped)

    return "".join(result)


def clean_latex_to_unicode(latex_text: str) -> str:
    """Convert LaTeX formula text into clean Unicode mathematical representation."""
    if not latex_text:
        return ""
    latex_text = sanitize_latex_escapes(latex_text)
    import re

    text = latex_text.strip()
    if text.startswith("$$") and text.endswith("$$"):
        text = text[2:-2].strip()
    elif text.startswith("$") and text.endswith("$"):
        text = text[1:-1].strip()
    elif text.startswith(r"\(") and text.endswith(r"\)"):
        text = text[2:-2].strip()
    elif text.startswith(r"\[") and text.endswith(r"\]"):
        text = text[2:-2].strip()

    # 1. Text wrappers: \text{...}, \mathrm{...}, \mathbf{...}, \mathit{...}
    text = re.sub(r"\\(?:text|mathrm|mathbf|mathit|textbf|textit)\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\(?:left|right)\b", "", text)

    # 2. Vector & Bar: \vec{F} -> F⃗, \vec{a} -> a⃗, \bar{x} -> x̄
    text = re.sub(r"\\vec\{([A-Za-z])\}", r"\1⃗", text)
    text = re.sub(r"\\vec\s*([A-Za-z])", r"\1⃗", text)
    text = re.sub(r"\\bar\{([A-Za-z0-9])\}", lambda m: f"{m.group(1)}\u0304", text)
    text = re.sub(r"\\bar\s*([A-Za-z0-9])", lambda m: f"{m.group(1)}\u0304", text)

    # 3. Fractions: \frac{a}{b} -> a/b
    def _frac_sub(m):
        num = m.group(1).strip()
        den = m.group(2).strip()
        return f"{num}/{den}"
    text = re.sub(r"\\frac\{([^}]+)\}\{([^}]+)\}", _frac_sub, text)

    # 4. Square roots: \sqrt{x} -> √(x), \sqrt[n]{x} -> n√(x)
    text = re.sub(r"\\sqrt\[([^]]+)\]\{([^}]+)\}", r"\1√(\2)", text)
    text = re.sub(r"\\sqrt\{([^}]+)\}", r"√(\1)", text)

    # 5. Times operator repair
    text = re.sub(r"(?<=[0-9a-zA-Z}\^\-\)\'\"\]])(\s*)times(\s*)(?=[0-9a-zA-Z{\\\(\'\"\[])", r"\1\\times\2", text)
    text = re.sub(r'(?<![\\a-zA-Z])\btimes\b(?![a-zA-Z])', r'\\times', text)

    # 6. Greek letters & symbols
    for cmd, sym in GREEK_AND_SYMBOLS_MAP.items():
        text = text.replace(cmd, sym)

    # 7. Superscripts: x^{2} or x^2
    def _sup_sub(m):
        raw = m.group(1) or m.group(2)
        return "".join(SUPERSCRIPTS_MAP.get(c, c) for c in raw)
    text = re.sub(r"\^\{([^}]+)\}|\^([0-9a-zA-Z+\-()])", _sup_sub, text)

    # 8. Subscripts: m_{1} or m_1
    def _sub_sub(m):
        raw = m.group(1) or m.group(2)
        return "".join(SUBSCRIPTS_MAP.get(c, c) for c in raw)
    text = re.sub(r"_\{([^}]+)\}|_([0-9a-zA-Z+\-()])", _sub_sub, text)

    # 9. Clean residual braces or backslashes
    text = text.replace("{", "").replace("}", "")
    text = re.sub(r"\\[a-zA-Z]+", "", text)

    return text.strip()


def add_markdown_and_math_to_pptx_paragraph(
    p,
    text: str,
    font_size=None,
    font_color=None,
    base_bold: bool = False,
    font_name: str = "Noto Sans TC",
):
    """Parse inline markdown (**bold**, *italic*, `code`) and LaTeX math ($...$, $$...$$) and add formatted runs into python-pptx paragraph."""
    if not text:
        return
    import re
    from pptx.dml.color import RGBColor
    from pptx.util import Pt

    text_processed = _wrap_bare_latex(str(text))
    pattern = re.compile(
        r"(\$\$[\s\S]*?\$\$|\$[^$\n]+?\$|\\\[[\s\S]*?\\\]|\\\([\s\S]*?\\\)|(?<!\*)\*\*[^\*\n]+?\*\*(?!\*)|__[^_\n]+?__|(?<!\*)\*[^\*\n]+?\*(?!\*)|`[^`\n]+?`)"
    )
    tokens = pattern.split(text_processed)

    for token in tokens:
        if not token:
            continue

        run = p.add_run()
        run.font.name = font_name
        if font_size is not None:
            run.font.size = font_size
        if font_color is not None:
            run.font.color.rgb = font_color

        if (
            (token.startswith("$$") and token.endswith("$$"))
            or (token.startswith("$") and token.endswith("$"))
            or (token.startswith(r"\[") and token.endswith(r"\]"))
            or (token.startswith(r"\(") and token.endswith(r"\)"))
        ):
            math_clean = clean_latex_to_unicode(token)
            run.text = math_clean
            run.font.italic = True
            run.font.bold = base_bold
        elif (
            (token.startswith("**") and token.endswith("**") and len(token) >= 4)
            or (token.startswith("__") and token.endswith("__") and len(token) >= 4)
        ):
            run.text = token[2:-2]
            run.font.bold = True
        elif token.startswith("*") and token.endswith("*") and len(token) > 2:
            run.text = token[1:-1]
            run.font.italic = True
            run.font.bold = base_bold
        elif token.startswith("`") and token.endswith("`") and len(token) > 2:
            run.text = token[1:-1]
            run.font.bold = base_bold
        else:
            run.text = token
            run.font.bold = base_bold


def make_pptx(deck: Deck) -> bytes:
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.enum.text import PP_ALIGN
    from pptx.util import Inches, Pt

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    for index, item in enumerate(deck.slides):
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        bg = slide.background.fill
        bg.solid()
        bg.fore_color.rgb = RGBColor(247, 247, 242)
        accent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(0.18), Inches(7.5))
        accent.fill.solid(); accent.fill.fore_color.rgb = RGBColor(222, 91, 55); accent.line.fill.background()
        number = slide.shapes.add_textbox(Inches(11.9), Inches(0.45), Inches(0.8), Inches(0.4))
        p = number.text_frame.paragraphs[0]; p.text = f"{index + 1:02d}"; p.font.size = Pt(16); p.font.bold = True; p.font.color.rgb = RGBColor(222, 91, 55); p.alignment = PP_ALIGN.RIGHT

        icon_str = getattr(item, "icon", "💡") or "💡"
        title_box = slide.shapes.add_textbox(Inches(0.85), Inches(0.65), Inches(10.8), Inches(1.1))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        p = tf_title.paragraphs[0]
        add_markdown_and_math_to_pptx_paragraph(p, f"{icon_str}  {item.title}", font_size=Pt(28), font_color=RGBColor(27, 35, 32), base_bold=True)

        # 左側重點內容欄位
        body = slide.shapes.add_textbox(Inches(0.85), Inches(1.95), Inches(6.6), Inches(4.8))
        tf = body.text_frame
        tf.word_wrap = True
        font_size = Pt(15) if len(item.bullets) <= 4 else Pt(14)
        for bullet_index, bullet in enumerate(item.bullets):
            p = tf.paragraphs[0] if bullet_index == 0 else tf.add_paragraph()
            p.space_after = Pt(10)
            add_markdown_and_math_to_pptx_paragraph(p, f"• {bullet}", font_size=font_size, font_color=RGBColor(55, 65, 61))

        # 右側觀念圖解視覺卡片
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(7.8), Inches(1.95), Inches(4.7), Inches(4.8))
        card.fill.solid()
        card.fill.fore_color.rgb = RGBColor(255, 255, 255)
        card.line.color.rgb = RGBColor(222, 91, 55)
        card.line.width = Pt(1.5)

        vis_diagram = getattr(item, "visual_diagram", {}) or {}
        diagram_type = vis_diagram.get("diagram_type", "flowchart")
        type_titles = {
            "flowchart": "🔄 機制流程推導",
            "comparison": "⚖️ 核心概念對比",
            "key_formula": "🧮 關鍵公式解析",
            "concept_map": "📐 觀念架構圖解",
        }
        card_header_text = type_titles.get(diagram_type, "📐 觀念圖解與推導")

        card_title_box = slide.shapes.add_textbox(Inches(7.95), Inches(2.05), Inches(4.4), Inches(0.45))
        p = card_title_box.text_frame.paragraphs[0]
        add_markdown_and_math_to_pptx_paragraph(p, card_header_text, font_size=Pt(15), font_color=RGBColor(222, 91, 55), base_bold=True)

        # 提煉結構化推導步驟 (支援 1~3 個步驟，動態自適應高度與間距)
        raw_steps = vis_diagram.get("steps", [])
        if raw_steps and isinstance(raw_steps, list):
            diagram_steps = []
            for sIdx, s in enumerate(raw_steps[:3]):
                if isinstance(s, dict):
                    diagram_steps.append((s.get("label", f"觀念重點 {sIdx + 1}"), s.get("text", "")))
                else:
                    diagram_steps.append((f"觀念重點 {sIdx + 1}", str(s)))
        else:
            diagram_steps = [
                ("① 核心機制", f"聚焦【{item.title}】之根本原理與邏輯架構"),
                ("② 推導關鍵", item.visual_description[:60] if item.visual_description else "依據教材推導並掌握概念關鍵特徵"),
            ]

        n_steps = len(diagram_steps)
        if n_steps >= 3:
            step_y_starts = [2.52, 3.45, 4.38]
            step_h = 0.85
            vis_y = 5.31
            vis_h = 1.30
            step_txt_size = Pt(11)
            takeaway_txt_size = Pt(11)
        elif n_steps == 2:
            step_y_starts = [2.55, 3.75]
            step_h = 1.05
            vis_y = 4.95
            vis_h = 1.60
            step_txt_size = Pt(12)
            takeaway_txt_size = Pt(11.5)
        else:
            step_y_starts = [2.55]
            step_h = 1.50
            vis_y = 4.25
            vis_h = 2.30
            step_txt_size = Pt(12.5)
            takeaway_txt_size = Pt(12)

        for idx, (lbl, txt) in enumerate(diagram_steps):
            y_pos = step_y_starts[idx]
            step_bg = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.0), Inches(y_pos), Inches(4.3), Inches(step_h))
            step_bg.fill.solid()
            if idx == 0:
                step_bg.fill.fore_color.rgb = RGBColor(255, 245, 242)
                step_bg.line.color.rgb = RGBColor(222, 91, 55)
            elif idx == 1:
                step_bg.fill.fore_color.rgb = RGBColor(237, 242, 247)
                step_bg.line.color.rgb = RGBColor(74, 85, 104)
            else:
                step_bg.fill.fore_color.rgb = RGBColor(247, 250, 252)
                step_bg.line.color.rgb = RGBColor(160, 174, 192)
            step_bg.line.width = Pt(1.0)

            tf_step = step_bg.text_frame
            tf_step.word_wrap = True
            p_lbl = tf_step.paragraphs[0]
            lbl_color = RGBColor(222, 91, 55) if idx == 0 else (RGBColor(74, 85, 104) if idx == 1 else RGBColor(43, 108, 176))
            add_markdown_and_math_to_pptx_paragraph(p_lbl, lbl, font_size=Pt(11), font_color=lbl_color, base_bold=True)

            p_txt = tf_step.add_paragraph()
            str_item = str(txt)
            add_markdown_and_math_to_pptx_paragraph(p_txt, str_item, font_size=step_txt_size, font_color=RGBColor(45, 55, 72))

        # 底部視覺圖解結論方塊
        vis_bg = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.0), Inches(vis_y), Inches(4.3), Inches(vis_h))
        vis_bg.fill.solid()
        vis_bg.fill.fore_color.rgb = RGBColor(240, 249, 255)
        vis_bg.line.color.rgb = RGBColor(43, 108, 176)
        vis_bg.line.width = Pt(1.0)

        tf_vis = vis_bg.text_frame
        tf_vis.word_wrap = True
        p_vis_lbl = tf_vis.paragraphs[0]
        add_markdown_and_math_to_pptx_paragraph(p_vis_lbl, "💡 核心結論與關鍵理解：", font_size=Pt(11), font_color=RGBColor(43, 108, 176), base_bold=True)

        p_vis_txt = tf_vis.add_paragraph()
        takeaway_text = vis_diagram.get("takeaway") or getattr(item, "visual_description", "") or "深入掌握本單元核心機制與概念推導。"
        add_markdown_and_math_to_pptx_paragraph(p_vis_txt, takeaway_text, font_size=takeaway_txt_size, font_color=RGBColor(45, 55, 72))

        notes = slide.notes_slide.notes_text_frame
        notes.text = clean_latex_to_unicode(item.speaker_notes) + (f"\n\n資料來源頁碼：{', '.join(map(str, item.source_pages))}" if item.source_pages else "")
    output = io.BytesIO()
    prs.save(output)
    return output.getvalue()



def make_script(deck: Deck) -> str:
    lines = [f"# {deck.title}", "", deck.subtitle, ""]
    for i, slide in enumerate(deck.slides, 1):
        lines.extend([f"## {i}. {slide.title}", "", slide.speaker_notes, "", f"> 教材頁碼：{', '.join(map(str, slide.source_pages)) or '—'}", ""])
    return "\n".join(lines)


def make_quiz_markdown(sheet: QuizSheet, teacher_mode: bool = False) -> str:
    type_labels = {
        "single_choice": "單選題",
        "multiple_choice": "多選題",
        "problem_solving": "計算與推導論述題",
    }
    lines = [
        f"# {sheet.title}",
        "",
        f"> {sheet.description}",
        f"> 建議測驗時間：{sheet.duration_minutes} 分鐘 | 總題數：{len(sheet.questions)} 題",
        "",
        "---",
        "",
    ]
    for idx, q in enumerate(sheet.questions, 1):
        t_name = type_labels.get(q.type, "評量題")
        diff_badge = {"easy": "基礎", "medium": "中等", "hard": "進階"}.get(q.difficulty, "中等")
        lines.append(f"### 第 {idx} 題【{t_name} · 難度：{diff_badge}】")
        lines.append("")
        lines.append(q.question)
        lines.append("")
        if q.options:
            for opt in q.options:
                lines.append(f"- {opt}")
            lines.append("")
        if teacher_mode:
            lines.append(f"**【標準答案】**：`{q.answer}`")
            lines.append("")
            lines.append(f"**【試題詳解】**：{q.explanation}")
            lines.append("")
            pages_str = ", ".join(map(str, q.source_pages)) if q.source_pages else "—"
            lines.append(f"> 教材出處頁碼：第 {pages_str} 頁")
            lines.append("")
            lines.append("---")
            lines.append("")
        else:
            lines.append("> 作答區 / 演算草稿：")
            lines.append("")
            lines.append("```")
            lines.append("")
            lines.append("")
            lines.append("```")
            lines.append("")
            lines.append("---")
            lines.append("")
    return "\n".join(lines)


def make_handout_markdown(handout: Handout) -> str:
    lines = [
        f"# {handout.title}",
        "",
        f"**{handout.subtitle}**",
        "",
        f"> **課程導讀**：{handout.overview}",
        "",
        "---",
        "",
    ]
    for idx, sec in enumerate(handout.sections, 1):
        lines.append(f"## 第 {idx} 單元：{sec.title}")
        lines.append("")
        lines.append(sec.summary)
        lines.append("")
        if sec.key_points:
            lines.append("### 核心要點與關鍵觀念")
            for kp in sec.key_points:
                lines.append(f"- {kp}")
            lines.append("")
        if sec.discussion_questions:
            lines.append("### 隨堂思考與隨堂練習")
            for q in sec.discussion_questions:
                lines.append(f"1. {q}")
            lines.append("")
        if sec.source_pages:
            pages_str = ", ".join(map(str, sec.source_pages))
            lines.append(f"> 出處頁碼：第 {pages_str} 頁")
            lines.append("")
        lines.append("---")
        lines.append("")

    if handout.key_takeaways:
        lines.append("## 課後總結與核心精華 (Takeaways)")
        lines.append("")
        for kw in handout.key_takeaways:
            lines.append(f"- {kw}")
        lines.append("")

    return "\n".join(lines)




def _format_handout_text(text: str) -> str:
    """Format markdown text in handouts, preserving LaTeX math formulas."""
    if not text:
        return ""
    import re
    import html

    text = auto_repair_math_expressions(str(text))

    # 1. Stash Math tokens ($$...$$, $...$, \[...\], \(...\))
    math_tokens = []
    def _stash_math(m):
        idx = len(math_tokens)
        math_tokens.append(m.group(0))
        return f"%%MATHPLACEHOLDER{idx}%%"

    pattern = re.compile(r"(\$\$[\s\S]*?\$\$|\$[^$\n]+?\$|\\\[[\s\S]*?\\\]|\\\([\s\S]*?\\\))")
    processed = pattern.sub(_stash_math, str(text))

    # 2. Escape non-math text
    processed = html.escape(processed)

    # 3. Inline markdown parsing
    processed = re.sub(r"\*\*([^\*\n]+?)\*\*", r"<strong>\1</strong>", processed)
    processed = re.sub(r"__([^_\n]+?)__", r"<strong>\1</strong>", processed)
    processed = re.sub(r"(?<!\*)\*([^\*\n]+?)\*(?!\*)", r"<em>\1</em>", processed)
    processed = re.sub(r"`([^`\n]+?)`", r"<code>\1</code>", processed)
    processed = processed.replace("\n", "<br>")

    # 4. Restore math tokens
    for idx, math_str in enumerate(math_tokens):
        processed = processed.replace(f"%%MATHPLACEHOLDER{idx}%%", math_str)

    return processed


def make_handout_html(handout: Handout) -> str:
    sections_html = ""
    for idx, sec in enumerate(handout.sections, 1):
        points_html = "".join(f"<li>{_format_handout_text(p)}</li>" for p in sec.key_points)
        questions_html = "".join(f"<li>{_format_handout_text(q)}</li>" for q in sec.discussion_questions)
        pages_html = f"<div class='handout-pages'>教材出處：第 {', '.join(map(str, sec.source_pages))} 頁</div>" if sec.source_pages else ""
        sections_html += f"""
        <section class="handout-section">
            <h2>§ {idx}. {_format_handout_text(sec.title)}</h2>
            <p class="section-summary">{_format_handout_text(sec.summary)}</p>
            {f'<div class="box points-box"><h3>📌 核心要點</h3><ul>{points_html}</ul></div>' if points_html else ''}
            {f'<div class="box questions-box"><h3>💬 隨堂思考與練習</h3><ol>{questions_html}</ol></div>' if questions_html else ''}
            {pages_html}
        </section>
        """

    takeaways_html = "".join(f"<li>{_format_handout_text(t)}</li>" for t in handout.key_takeaways)
    title_esc = _format_handout_text(handout.title or "隨堂講義")
    subtitle_esc = _format_handout_text(handout.subtitle or "")
    overview_esc = _format_handout_text(handout.overview or "")

    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{handout.title or '隨堂講義'} - A4 隨堂講義</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/contrib/auto-render.min.js"></script>
<style>
@page {{
    size: A4 portrait;
    margin: 12mm 15mm;
}}
*, *:before, *:after {{
    box-sizing: border-box;
}}
body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans TC", sans-serif;
    color: #1e293b;
    background: #f8fafc;
    margin: 0;
    padding: 20px;
    line-height: 1.6;
}}
.handout-container {{
    max-width: 820px;
    margin: 0 auto;
    background: #ffffff;
    padding: 32px;
    border-radius: 8px;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.08);
    border: 1px solid #e2e8f0;
}}
.handout-header {{
    border-bottom: 2px solid #2563eb;
    padding-bottom: 12px;
    margin-bottom: 20px;
}}
.handout-title {{
    font-size: 22px;
    font-weight: 800;
    color: #0f172a;
    margin: 0 0 6px 0;
}}
.handout-subtitle {{
    font-size: 13px;
    color: #64748b;
    margin: 0;
}}
.handout-overview {{
    background: #eff6ff;
    border-left: 4px solid #2563eb;
    padding: 12px 16px;
    border-radius: 0 6px 6px 0;
    margin-bottom: 20px;
    font-size: 13.5px;
    line-height: 1.6;
}}
.handout-section {{
    margin-bottom: 24px;
    padding-bottom: 16px;
    border-bottom: 1px dashed #e2e8f0;
}}
.handout-section:last-of-type {{
    border-bottom: none;
}}
.handout-section h2 {{
    font-size: 16px;
    color: #1e3a8a;
    margin-top: 0;
    margin-bottom: 8px;
}}
.section-summary {{
    font-size: 13.5px;
    color: #334155;
    margin: 6px 0 12px 0;
}}
.box {{
    padding: 10px 14px;
    border-radius: 6px;
    margin: 10px 0;
    font-size: 13px;
}}
.box h3 {{
    margin: 0 0 6px 0;
    font-size: 13.5px;
}}
.box ul, .box ol {{
    margin: 0;
    padding-left: 20px;
}}
.box li {{
    margin-bottom: 4px;
}}
.points-box {{
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    color: #166534;
}}
.points-box h3 {{
    color: #166534;
}}
.questions-box {{
    background: #fffbeb;
    border: 1px solid #fef3c7;
    color: #92400e;
}}
.questions-box h3 {{
    color: #92400e;
}}
.handout-pages {{
    font-size: 11.5px;
    color: #94a3b8;
    text-align: right;
    margin-top: 6px;
}}
.takeaways-box {{
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 14px 18px;
    margin-top: 24px;
}}
.takeaways-box h2 {{
    font-size: 15px;
    margin-top: 0;
    color: #0f172a;
    margin-bottom: 8px;
}}
.takeaways-box ul {{
    margin: 0;
    padding-left: 20px;
    font-size: 13px;
}}
.no-print {{
    margin-bottom: 18px;
    display: flex;
    justify-content: flex-end;
    gap: 10px;
}}
.btn-print {{
    background: #2563eb;
    color: #fff;
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 13.5px;
    font-weight: 600;
}}
.btn-print:hover {{
    background: #1d4ed8;
}}
@media print {{
    *, *:before, *:after {{
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
        box-sizing: border-box !important;
    }}
    html, body {{
        background: #ffffff !important;
        color: #0f172a !important;
        margin: 0 !important;
        padding: 0 !important;
        width: 100% !important;
        height: auto !important;
        min-height: 100% !important;
        overflow: visible !important;
        position: static !important;
    }}
    .handout-container {{
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
        width: 100% !important;
        border: none !important;
        display: block !important;
        position: static !important;
        float: none !important;
    }}
    .no-print {{
        display: none !important;
    }}
    .handout-section {{
        break-inside: auto !important;
        page-break-inside: auto !important;
        margin-bottom: 20px !important;
    }}
    .box, .takeaways-box {{
        break-inside: avoid !important;
        page-break-inside: avoid !important;
    }}
    .katex-display {{
        break-inside: avoid !important;
        page-break-inside: avoid !important;
        overflow-x: visible !important;
    }}
}}
</style>
<script>
var katexOptions = {{
    delimiters: [
        {{left: '$$', right: '$$', display: true}},
        {{left: '$', right: '$', display: false}},
        {{left: '\\\\[', right: '\\\\]', display: true}},
        {{left: '\\\\(', right: '\\\\)', display: false}}
    ],
    throwOnError: false
}};

function unescapeMathInElement(element) {{
    if (!element) return;
    var html = element.innerHTML;
    html = html.replace(/(\\$\\$[\\s\\S]*?\\$\\$|\\$[^$\\n]+?\\$|\\\\\\[[\\s\\S]*?\\\\\\]|\\\\\\([\\s\\S]*?\\\\\\))/g, function(match) {{
        return match
            .replace(/&amp;/g, '&')
            .replace(/&lt;/g, '<')
            .replace(/&gt;/g, '>')
            .replace(/&quot;/g, '"')
            .replace(/&#39;/g, "'");
    }});
    element.innerHTML = html;
}}

var mathRendered = false;
function doRenderMath() {{
    if (mathRendered) return;
    if (window.renderMathInElement) {{
        try {{
            var container = document.querySelector('.handout-container');
            if (container) {{
                unescapeMathInElement(container);
                renderMathInElement(container, katexOptions);
            }}
            mathRendered = true;
        }} catch(e) {{
            console.warn('KaTeX error:', e);
        }}
    }}
}}

document.addEventListener('DOMContentLoaded', doRenderMath);
window.addEventListener('load', function() {{
    doRenderMath();
    if (document.fonts && document.fonts.ready) {{
        document.fonts.ready.then(function() {{
            console.log('Fonts ready for print');
        }});
    }}
}});

function triggerPrint() {{
    doRenderMath();
    var btn = document.querySelector('.btn-print');
    if (btn) btn.disabled = true;

    var executePrint = function() {{
        setTimeout(function() {{
            window.print();
            if (btn) btn.disabled = false;
        }}, 150);
    }};

    if (document.fonts && document.fonts.ready) {{
        document.fonts.ready.then(executePrint).catch(executePrint);
    }} else {{
        executePrint();
    }}
}}
</script>
</head>
<body>
<div class="handout-container">
    <div class="no-print">
        <button class="btn-print" onclick="triggerPrint()">🖨️ 列印 / 另存為 A4 PDF</button>
    </div>
    <div class="handout-header">
        <h1 class="handout-title">{title_esc}</h1>
        <p class="handout-subtitle">{subtitle_esc}</p>
    </div>
    {f'<div class="handout-overview"><strong>📖 課程導讀：</strong>{overview_esc}</div>' if overview_esc else ''}
    {sections_html}
    {f'<div class="takeaways-box"><h2>💡 課後總結與精華 (Key Takeaways)</h2><ul>{takeaways_html}</ul></div>' if takeaways_html else ''}
</div>
<script>
// 頁面解析時立即嘗試首次渲染
if (window.renderMathInElement) {{
    doRenderMath();
}}
</script>
</body>
</html>
"""


def make_deck_slides_html(deck: Deck) -> str:
    """Generate high-fidelity standalone printable Slides HTML with customizable layout and orientation controls for PDF saving."""
    slides_html = ""
    for idx, s in enumerate(deck.slides, 1):
        icon_str = getattr(s, "icon", "💡") or "💡"
        title_html = _format_handout_text(s.title)
        bullets_html = "".join(f"<li>{_format_handout_text(b)}</li>" for b in s.bullets)

        vis_diagram = getattr(s, "visual_diagram", {}) or {}
        diagram_type = vis_diagram.get("diagram_type", "flowchart")
        type_titles = {
            "flowchart": "🔄 機制流程推導",
            "comparison": "⚖️ 核心概念對比",
            "key_formula": "🧮 關鍵公式解析",
            "concept_map": "📐 觀念架構圖解",
        }
        card_header_text = type_titles.get(diagram_type, "📐 觀念圖解與推導")

        raw_steps = vis_diagram.get("steps", [])
        if raw_steps and isinstance(raw_steps, list):
            diagram_steps = []
            for sIdx, st in enumerate(raw_steps[:3]):
                if isinstance(st, dict):
                    diagram_steps.append((st.get("label", f"觀念重點 {sIdx + 1}"), st.get("text", "")))
                else:
                    diagram_steps.append((f"觀念重點 {sIdx + 1}", str(st)))
        else:
            diagram_steps = [
                ("① 核心機制", f"聚焦【{s.title}】之根本原理與邏輯架構"),
                ("② 推導關鍵", s.visual_description[:60] if s.visual_description else "依據教材推導並掌握概念關鍵特徵"),
            ]

        steps_html = ""
        for sIdx, (lbl, txt) in enumerate(diagram_steps):
            steps_html += f"""
            <div class="print-step-box step-idx-{sIdx}">
                <div class="print-step-label">{_format_handout_text(lbl)}</div>
                <div class="print-step-text">{_format_handout_text(str(txt))}</div>
            </div>
            """

        takeaway_text = vis_diagram.get("takeaway") or getattr(s, "visual_description", "") or "深入掌握本單元核心機制與概念推導。"
        takeaway_html = f"""
        <div class="print-takeaway-box">
            <div class="print-takeaway-head">💡 核心結論與關鍵理解：</div>
            <div class="print-takeaway-text">{_format_handout_text(takeaway_text)}</div>
        </div>
        """

        notes_html = _format_handout_text(s.speaker_notes)
        pages_str = f"教材第 {', '.join(map(str, s.source_pages))} 頁" if s.source_pages else ""

        slides_html += f"""
        <div class="slide-page-item" data-slide-index="{idx}">
            <div class="slide-inner-card">
                <div class="slide-accent-bar"></div>
                <div class="slide-page-number">{idx:02d}</div>
                <div class="slide-header">
                    <h2><span class="slide-icon">{icon_str}</span> <span class="slide-title">{title_html}</span></h2>
                </div>
                <div class="slide-body-grid">
                    <div class="slide-bullets-col">
                        <ul class="slide-bullets-list">{bullets_html}</ul>
                    </div>
                    <div class="slide-visual-col">
                        <div class="print-visual-card">
                            <div class="print-visual-head">{_format_handout_text(card_header_text)}</div>
                            <div class="print-visual-steps">{steps_html}</div>
                            {takeaway_html}
                        </div>
                    </div>
                </div>
                <div class="slide-notes-drawer hidden">
                    <div class="slide-notes-head">
                        <b>🎙️ 講師演講稿與備課要點</b>
                        <small>{pages_str}</small>
                    </div>
                    <div class="slide-notes-content">{notes_html}</div>
                </div>
            </div>
            <div class="slide-handout-lines hidden">
                <div class="note-lines-header">課堂隨記 / 備忘筆記</div>
                <div class="note-line"></div>
                <div class="note-line"></div>
                <div class="note-line"></div>
                <div class="note-line"></div>
            </div>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{deck.title} - 投影片列印與 PDF 匯出</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/contrib/auto-render.min.js"></script>
<style>
:root {{
    --accent: #de5b37;
    --accent-light: #fff5f2;
    --ink: #1e293b;
    --muted: #64748b;
    --card-bg: #ffffff;
    --stage-bg: #f8fafc;
}}
*, *:before, *:after {{
    box-sizing: border-box;
}}
body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans TC", sans-serif;
    color: var(--ink);
    background: #e2e8f0;
    margin: 0;
    padding: 0;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
}}

/* 頂端列印控制列 (列印時自動隱藏) */
.print-control-bar {{
    position: sticky;
    top: 0;
    z-index: 9999;
    background: #1e293b;
    color: #f8fafc;
    padding: 10px 20px;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}}
.ctrl-left {{
    display: flex;
    align-items: center;
    gap: 15px;
    flex-wrap: wrap;
}}
.ctrl-title {{
    font-size: 15px;
    font-weight: 700;
    color: #fff;
    display: flex;
    align-items: center;
    gap: 6px;
}}
.ctrl-group {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
}}
.ctrl-btn {{
    background: #334155;
    color: #e2e8f0;
    border: 1px solid #475569;
    border-radius: 6px;
    padding: 5px 12px;
    font-size: 12.5px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
}}
.ctrl-btn:hover {{
    background: #475569;
}}
.ctrl-btn.active {{
    background: var(--accent);
    color: #fff;
    border-color: var(--accent);
}}
.ctrl-select {{
    background: #334155;
    color: #fff;
    border: 1px solid #475569;
    border-radius: 6px;
    padding: 5px 10px;
    font-size: 12.5px;
    cursor: pointer;
}}
.ctrl-checkbox {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 12.5px;
    cursor: pointer;
    user-select: none;
}}
.ctrl-checkbox input {{
    cursor: pointer;
}}
.ctrl-right {{
    display: flex;
    align-items: center;
    gap: 10px;
}}
.action-print-btn {{
    background: var(--accent);
    color: #fff;
    border: none;
    border-radius: 6px;
    padding: 7px 18px;
    font-size: 13.5px;
    font-weight: 700;
    cursor: pointer;
    box-shadow: 0 2px 6px rgba(222, 91, 55, 0.4);
    transition: transform 0.1s ease;
}}
.action-print-btn:hover {{
    background: #c54a28;
    transform: translateY(-1px);
}}
.action-close-btn {{
    background: transparent;
    color: #94a3b8;
    border: 1px solid #475569;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 12.5px;
    cursor: pointer;
}}
.action-close-btn:hover {{
    color: #fff;
    border-color: #cbd5e1;
}}

/* 簡報整體容器 */
.slides-doc-wrapper {{
    max-width: 1100px;
    margin: 25px auto 40px auto;
    padding: 0 15px;
}}
.slides-container {{
    display: flex;
    flex-direction: column;
    gap: 25px;
}}

/* 單張投影片樣式 (16:9 卡片外觀，精確重現預覽舞台) */
.slide-page-item {{
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 12px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.06);
    position: relative;
    overflow: hidden;
    break-inside: avoid;
    page-break-inside: avoid;
    padding: 24px 30px;
    display: flex;
    flex-direction: column;
}}
.slide-inner-card {{
    position: relative;
    width: 100%;
    display: flex;
    flex-direction: column;
    height: 100%;
}}
.slide-accent-bar {{
    position: absolute;
    left: -30px;
    top: -24px;
    bottom: -24px;
    width: 8px;
    background: var(--accent);
}}
.slide-page-number {{
    position: absolute;
    top: -6px;
    right: 0;
    font-size: 20px;
    font-weight: 800;
    color: var(--accent);
}}
.slide-header {{
    margin-bottom: 16px;
    padding-right: 45px;
}}
.slide-header h2 {{
    margin: 0;
    font-size: 22px;
    font-weight: 800;
    color: #0f172a;
    display: flex;
    align-items: center;
    gap: 10px;
    line-height: 1.3;
}}
.slide-body-grid {{
    display: grid;
    grid-template-columns: 1.15fr 1fr;
    gap: 20px;
    align-items: start;
    flex: 1;
}}
.slide-bullets-list {{
    margin: 0;
    padding: 0;
    list-style: none;
}}
.slide-bullets-list li {{
    font-size: 14.5px;
    margin-bottom: 14px;
    color: #334155;
    position: relative;
    padding-left: 22px;
    line-height: 1.6;
}}
.slide-bullets-list li:before {{
    content: "";
    position: absolute;
    left: 2px;
    top: 0.55em;
    width: 7px;
    height: 7px;
    background: #c9d765;
    transform: rotate(45deg);
}}

/* 結構化視覺圖解卡片 */
.print-visual-card {{
    background: #ffffff;
    border: 1.5px solid var(--accent);
    border-radius: 10px;
    padding: 12px 14px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.03);
    display: flex;
    flex-direction: column;
    gap: 8px;
}}
.print-visual-head {{
    font-size: 13.5px;
    font-weight: 700;
    color: var(--accent);
    border-bottom: 1px solid #fed7aa;
    padding-bottom: 5px;
}}
.print-visual-steps {{
    display: flex;
    flex-direction: column;
    gap: 6px;
}}
.print-step-box {{
    border-radius: 6px;
    padding: 6px 10px;
    border: 1px solid #cbd5e0;
    background: #f8fafc;
}}
.print-step-box.step-idx-0 {{
    background: #fff5f2;
    border-color: var(--accent);
}}
.print-step-box.step-idx-0 .print-step-label {{
    color: var(--accent);
}}
.print-step-box.step-idx-1 {{
    background: #edf2f7;
    border-color: #4a5568;
}}
.print-step-box.step-idx-1 .print-step-label {{
    color: #4a5568;
}}
.print-step-box.step-idx-2 {{
    background: #f8fafc;
    border-color: #a0aec0;
}}
.print-step-box.step-idx-2 .print-step-label {{
    color: #2b6cb0;
}}
.print-step-label {{
    font-size: 11.5px;
    font-weight: 700;
    margin-bottom: 2px;
}}
.print-step-text {{
    font-size: 12px;
    line-height: 1.45;
    color: #334155;
}}
.print-takeaway-box {{
    background: #f0f9ff;
    border: 1px solid #2b6cb0;
    border-radius: 6px;
    padding: 6px 10px;
    margin-top: 2px;
}}
.print-takeaway-head {{
    font-size: 11px;
    font-weight: 700;
    color: #2b6cb0;
    margin-bottom: 2px;
}}
.print-takeaway-text {{
    font-size: 11.5px;
    color: #334155;
    line-height: 1.4;
}}

/* 演講稿抽屜 */
.slide-notes-drawer {{
    margin-top: 16px;
    background: #f8fafc;
    border-top: 1px dashed #cbd5e1;
    padding-top: 12px;
}}
.slide-notes-head {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 12px;
    color: #475569;
    margin-bottom: 4px;
}}
.slide-notes-content {{
    font-size: 12.5px;
    color: #475569;
    line-height: 1.55;
}}

/* 筆記線 (3 頁講義模式) */
.slide-handout-lines {{
    border-left: 1px dashed #cbd5e1;
    padding-left: 15px;
    display: flex;
    flex-direction: column;
    justify-content: space-around;
}}
.note-lines-header {{
    font-size: 11.5px;
    font-weight: 700;
    color: #94a3b8;
    margin-bottom: 5px;
}}
.note-line {{
    border-bottom: 1px solid #e2e8f0;
    height: 28px;
}}

.hidden {{
    display: none !important;
}}

/* ========== 多版面佈局自適應 ========== */
/* 2 Slides per page */
.layout-2 .slides-container {{
    display: grid;
    grid-template-columns: 1fr;
    gap: 15px;
}}
.layout-2 .slide-page-item {{
    padding: 18px 22px;
}}
.layout-2 .slide-header h2 {{
    font-size: 18px;
}}
.layout-2 .slide-bullets-list li {{
    font-size: 13px;
    margin-bottom: 8px;
}}

/* 3 Slides per page with note lines */
.layout-3 .slide-page-item {{
    display: grid;
    grid-template-columns: 1.4fr 1fr;
    gap: 15px;
    padding: 16px 20px;
}}
.layout-3 .slide-handout-lines {{
    display: flex !important;
}}
.layout-3 .slide-header h2 {{
    font-size: 16px;
}}
.layout-3 .slide-bullets-list li {{
    font-size: 12px;
    margin-bottom: 6px;
}}

/* 4 Slides per page (2x2) */
.layout-4 .slides-container {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
}}
.layout-4 .slide-page-item {{
    padding: 14px 16px;
}}
.layout-4 .slide-header h2 {{
    font-size: 15px;
}}
.layout-4 .slide-bullets-list li {{
    font-size: 11.5px;
    margin-bottom: 6px;
}}
.layout-4 .slide-body-grid {{
    grid-template-columns: 1fr;
    gap: 10px;
}}

/* 6 Slides per page (2x3) */
.layout-6 .slides-container {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
}}
.layout-6 .slide-page-item {{
    padding: 10px 14px;
}}
.layout-6 .slide-header h2 {{
    font-size: 13.5px;
}}
.layout-6 .slide-bullets-list li {{
    font-size: 11px;
    margin-bottom: 4px;
}}
.layout-6 .slide-body-grid {{
    grid-template-columns: 1fr;
    gap: 8px;
}}

/* ========== 列印媒體查詢 (@media print) ========== */
@media print {{
    *, *:before, *:after {{
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
        box-sizing: border-box !important;
    }}
    html, body {{
        background: #ffffff !important;
        color: #0f172a !important;
        margin: 0 !important;
        padding: 0 !important;
        width: 100% !important;
        height: auto !important;
        min-height: auto !important;
        overflow: visible !important;
        position: static !important;
    }}
    .print-control-bar {{
        display: none !important;
    }}
    .slides-doc-wrapper {{
        max-width: 100% !important;
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        display: block !important;
        position: static !important;
        box-shadow: none !important;
    }}
    .slides-container {{
        display: block !important;
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }}
    .slide-page-item {{
        border: 1px solid #cbd5e1 !important;
        box-shadow: none !important;
        border-radius: 8px !important;
        display: block !important;
        overflow: hidden !important;
        page-break-inside: avoid !important;
        break-inside: avoid !important;
        -webkit-column-break-inside: avoid !important;
        margin: 0 0 16px 0 !important;
        padding: 18px 22px !important;
        background: #ffffff !important;
        color: #0f172a !important;
        height: auto !important;
        min-height: auto !important;
        position: relative !important;
    }}
    .slide-accent-bar {{
        position: absolute !important;
        left: 0 !important;
        top: 0 !important;
        bottom: 0 !important;
        width: 6px !important;
    }}
    .slide-inner-card {{
        display: block !important;
        width: 100% !important;
        height: auto !important;
        position: relative !important;
        padding-left: 6px !important;
    }}
    .slide-body-grid {{
        display: flex !important;
        flex-direction: row !important;
        gap: 16px !important;
        width: 100% !important;
        align-items: flex-start !important;
    }}
    .slide-bullets-col {{
        flex: 1.15 !important;
        width: 55% !important;
    }}
    .slide-visual-col {{
        flex: 1 !important;
        width: 45% !important;
    }}
    
    /* 1 Slide per page: 每一張投影片獨立換頁 */
    .layout-1 .slide-page-item {{
        page-break-after: always !important;
        break-after: page !important;
        margin-bottom: 0 !important;
    }}
    .layout-1 .slide-page-item:last-child {{
        page-break-after: auto !important;
        break-after: auto !important;
    }}
    
    /* 2 Slides per page: 每 2 張換一頁 */
    .layout-2 .slides-container {{
        display: block !important;
    }}
    .layout-2 .slide-page-item {{
        margin-bottom: 15px !important;
    }}
    .layout-2 .slide-page-item:nth-child(2n) {{
        page-break-after: always !important;
        break-after: page !important;
        margin-bottom: 0 !important;
    }}
    .layout-2 .slide-page-item:last-child {{
        page-break-after: auto !important;
        break-after: auto !important;
    }}
    
    /* 3 Slides per page: 每 3 張換一頁 */
    .layout-3 .slides-container {{
        display: block !important;
    }}
    .layout-3 .slide-page-item {{
        margin-bottom: 12px !important;
    }}
    .layout-3 .slide-page-item:nth-child(3n) {{
        page-break-after: always !important;
        break-after: page !important;
        margin-bottom: 0 !important;
    }}
    .layout-3 .slide-page-item:last-child {{
        page-break-after: auto !important;
        break-after: auto !important;
    }}
    
    /* 4 Slides per page: 每 4 張換一頁 (2x2) */
    .layout-4 .slides-container {{
        display: flex !important;
        flex-wrap: wrap !important;
        gap: 12px !important;
    }}
    .layout-4 .slide-page-item {{
        width: 48% !important;
        margin-bottom: 12px !important;
    }}
    .layout-4 .slide-page-item:nth-child(4n) {{
        page-break-after: always !important;
        break-after: page !important;
    }}
    .layout-4 .slide-page-item:last-child {{
        page-break-after: auto !important;
        break-after: auto !important;
    }}
    
    /* 6 Slides per page: 每 6 張換一頁 (2x3) */
    .layout-6 .slides-container {{
        display: flex !important;
        flex-wrap: wrap !important;
        gap: 8px !important;
    }}
    .layout-6 .slide-page-item {{
        width: 48% !important;
        margin-bottom: 8px !important;
    }}
    .layout-6 .slide-page-item:nth-child(6n) {{
        page-break-after: always !important;
        break-after: page !important;
    }}
    .layout-6 .slide-page-item:last-child {{
        page-break-after: auto !important;
        break-after: auto !important;
    }}

    .katex-display {{
        break-inside: avoid !important;
        page-break-inside: avoid !important;
        overflow-x: visible !important;
    }}
}}

@page {{
    size: A4 landscape;
    margin: 8mm 10mm;
}}
</style>
</head>
<body class="orientation-landscape layout-1">

<div class="print-control-bar">
    <div class="ctrl-left">
        <div class="ctrl-title">📑 簡報 PDF 與列印模式</div>
        <div class="ctrl-group">
            <button type="button" class="ctrl-btn active" id="btnLandscape" onclick="setOrientation('landscape')">🖥️ 橫向 (16:9)</button>
            <button type="button" class="ctrl-btn" id="btnPortrait" onclick="setOrientation('portrait')">📄 直向 (A4)</button>
        </div>
        <div class="ctrl-group">
            <label for="layoutSelect">每頁配置：</label>
            <select id="layoutSelect" class="ctrl-select" onchange="setLayout(this.value)">
                <option value="1" selected>1 張 / 頁 (全版投影標準)</option>
                <option value="2">2 張 / 頁 (雙投影片講義)</option>
                <option value="3">3 張 / 頁 (附筆記線講義)</option>
                <option value="4">4 張 / 頁 (2×2 縮圖網格)</option>
                <option value="6">6 張 / 頁 (2×3 密集檢索)</option>
            </select>
        </div>
        <div class="ctrl-group">
            <label class="ctrl-checkbox">
                <input type="checkbox" id="notesCheckbox" onchange="toggleNotes(this.checked)"> 包含講師演講稿
            </label>
        </div>
    </div>
    <div class="ctrl-right">
        <button type="button" class="action-print-btn" onclick="triggerPrint()">🖨️ 列印 / 另存為 PDF</button>
        <button type="button" class="action-close-btn" onclick="window.close()">✕ 關閉</button>
    </div>
</div>

<div class="slides-doc-wrapper">
    <div class="slides-container">
        {slides_html}
    </div>
</div>

<script>
var katexOptions = {{
    delimiters: [
        {{ left: '$$', right: '$$', display: true }},
        {{ left: '$', right: '$', display: false }},
        {{ left: '\\\\(', right: '\\\\)', display: false }},
        {{ left: '\\\\[', right: '\\\\]', display: true }}
    ],
    throwOnError: false
}};

function unescapeMathInElement(element) {{
    if (!element) return;
    var html = element.innerHTML;
    html = html.replace(/(\\$\\$[\\s\\S]*?\\$\\$|\\$[^$\\n]+?\\$|\\\\\\[[\\s\\S]*?\\\\\\]|\\\\\\([\\s\\S]*?\\\\\\))/g, function(match) {{
        return match
            .replace(/&amp;/g, '&')
            .replace(/&lt;/g, '<')
            .replace(/&gt;/g, '>')
            .replace(/&quot;/g, '"')
            .replace(/&#39;/g, "'");
    }});
    element.innerHTML = html;
}}

var mathRendered = false;
function doRenderMath() {{
    if (mathRendered) return;
    if (window.renderMathInElement) {{
        try {{
            var container = document.querySelector('.slides-container');
            if (container) {{
                unescapeMathInElement(container);
                renderMathInElement(container, katexOptions);
            }}
            mathRendered = true;
        }} catch(e) {{
            console.warn('KaTeX error:', e);
        }}
    }}
}}

document.addEventListener('DOMContentLoaded', doRenderMath);
window.addEventListener('load', function() {{
    doRenderMath();
    if (document.fonts && document.fonts.ready) {{
        document.fonts.ready.then(function() {{
            console.log('Fonts ready for slide printing');
        }});
    }}
}});

function triggerPrint() {{
    doRenderMath();
    var btn = document.querySelector('.action-print-btn');
    if (btn) btn.disabled = true;

    var executePrint = function() {{
        setTimeout(function() {{
            window.print();
            if (btn) btn.disabled = false;
        }}, 150);
    }};

    if (document.fonts && document.fonts.ready) {{
        document.fonts.ready.then(executePrint).catch(executePrint);
    }} else {{
        executePrint();
    }}
}}

function setOrientation(mode) {{
    document.body.classList.remove('orientation-landscape', 'orientation-portrait');
    document.body.classList.add('orientation-' + mode);
    document.getElementById('btnLandscape').classList.toggle('active', mode === 'landscape');
    document.getElementById('btnPortrait').classList.toggle('active', mode === 'portrait');
    
    var styleEl = document.getElementById('dynamicPageStyle');
    if (!styleEl) {{
        styleEl = document.createElement('style');
        styleEl.id = 'dynamicPageStyle';
        document.head.appendChild(styleEl);
    }}
    styleEl.innerHTML = '@page {{ size: A4 ' + mode + '; margin: 8mm 10mm; }}';
}}

function setLayout(count) {{
    document.body.classList.remove('layout-1', 'layout-2', 'layout-3', 'layout-4', 'layout-6');
    document.body.classList.add('layout-' + count);
    if (count === '3' || count === '2') {{
        setOrientation('portrait');
    }}
}}

function toggleNotes(show) {{
    document.querySelectorAll('.slide-notes-drawer').forEach(function(el) {{
        el.classList.toggle('hidden', !show);
    }});
}}
</script>
</body>
</html>
"""


def make_deck_handout_html(deck: Deck) -> str:
    slides_html = ""
    for idx, s in enumerate(deck.slides, 1):
        bullets_html = "".join(f"<li>{_format_handout_text(b)}</li>" for b in s.bullets)
        icon_str = getattr(s, "icon", "💡") or "💡"
        pages_str = f"<div class='handout-pages'>出處頁碼：第 {', '.join(map(str, s.source_pages))} 頁</div>" if s.source_pages else ""
        notes_html = _format_handout_text(s.speaker_notes)
        slides_html += f"""
        <section class="handout-section">
            <h2>{idx}. {icon_str} {_format_handout_text(s.title)}</h2>
            <div class="box points-box">
                <h3>投影片核心重點</h3>
                <ul>{bullets_html}</ul>
            </div>
            <div class="box notes-box">
                <h3>講師詳細解說詞與延伸備課筆記</h3>
                <p>{notes_html}</p>
            </div>
            {pages_str}
        </section>
        """

    title_esc = _format_handout_text(deck.title)
    subtitle_esc = _format_handout_text(f"{deck.subtitle} · 預估講授時間：{deck.duration} 分鐘" if deck.duration else (deck.subtitle or ""))

    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{deck.title} - A4 教學講義與演講稿</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/contrib/auto-render.min.js"></script>
<style>
@page {{
    size: A4 portrait;
    margin: 12mm 15mm;
}}
*, *:before, *:after {{
    box-sizing: border-box;
}}
body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans TC", sans-serif;
    color: #1e293b;
    background: #f8fafc;
    margin: 0;
    padding: 20px;
    line-height: 1.6;
}}
.handout-container {{
    max-width: 800px;
    margin: 0 auto;
    background: #ffffff;
    padding: 30px;
    border-radius: 8px;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
}}
.handout-header {{
    border-bottom: 2px solid #de5b37;
    padding-bottom: 12px;
    margin-bottom: 20px;
}}
.handout-title {{
    font-size: 22px;
    font-weight: 800;
    color: #0f172a;
    margin: 0 0 4px 0;
}}
.handout-subtitle {{
    font-size: 13px;
    color: #64748b;
    margin: 0;
}}
.handout-section {{
    margin-bottom: 25px;
    page-break-inside: avoid;
}}
.handout-section h2 {{
    font-size: 16px;
    color: #9a3412;
    border-bottom: 1px solid #fed7aa;
    padding-bottom: 5px;
    margin-top: 0;
}}
.box {{
    padding: 10px 14px;
    border-radius: 6px;
    margin: 10px 0;
    font-size: 13px;
}}
.box h3 {{
    margin: 0 0 5px 0;
    font-size: 13.5px;
}}
.points-box {{
    background: #fff7ed;
    border: 1px solid #ffedd5;
}}
.points-box h3 {{
    color: #c2410c;
}}
.notes-box {{
    background: #f8fafc;
    border: 1px solid #e2e8f0;
}}
.notes-box h3 {{
    color: #334155;
}}
.notes-box p {{
    margin: 0;
    font-size: 13px;
    color: #475569;
    line-height: 1.6;
}}
.handout-pages {{
    font-size: 11px;
    color: #94a3b8;
    text-align: right;
    margin-top: 4px;
}}
.no-print {{
    margin-bottom: 15px;
    text-align: right;
}}
.btn-print {{
    background: #de5b37;
    color: #fff;
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 13.5px;
    font-weight: 600;
}}
.btn-print:hover {{
    background: #c2410c;
}}
@media print {{
    *, *:before, *:after {{
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
        box-sizing: border-box !important;
    }}
    html, body {{
        background: #ffffff !important;
        color: #0f172a !important;
        margin: 0 !important;
        padding: 0 !important;
        width: 100% !important;
        height: auto !important;
        min-height: 100% !important;
        overflow: visible !important;
        position: static !important;
    }}
    .handout-container {{
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
        width: 100% !important;
        border: none !important;
        display: block !important;
        position: static !important;
        float: none !important;
    }}
    .no-print {{
        display: none !important;
    }}
    .handout-section {{
        break-inside: auto !important;
        page-break-inside: auto !important;
    }}
    .box {{
        break-inside: avoid !important;
        page-break-inside: avoid !important;
    }}
    .katex-display {{
        break-inside: avoid !important;
        page-break-inside: avoid !important;
        overflow-x: visible !important;
    }}
}}
</style>
<script>
var katexOptions = {{
    delimiters: [
        {{left: '$$', right: '$$', display: true}},
        {{left: '$', right: '$', display: false}},
        {{left: '\\\\[', right: '\\\\]', display: true}},
        {{left: '\\\\(', right: '\\\\)', display: false}}
    ],
    throwOnError: false
}};

function unescapeMathInElement(element) {{
    if (!element) return;
    var html = element.innerHTML;
    html = html.replace(/(\\$\\$[\\s\\S]*?\\$\\$|\\$[^$\\n]+?\\$|\\\\\\[[\\s\\S]*?\\\\\\]|\\\\\\([\\s\\S]*?\\\\\\))/g, function(match) {{
        return match
            .replace(/&amp;/g, '&')
            .replace(/&lt;/g, '<')
            .replace(/&gt;/g, '>')
            .replace(/&quot;/g, '"')
            .replace(/&#39;/g, "'");
    }});
    element.innerHTML = html;
}}

var mathRendered = false;
function doRenderMath() {{
    if (mathRendered) return;
    if (window.renderMathInElement) {{
        try {{
            var container = document.querySelector('.handout-container');
            if (container) {{
                unescapeMathInElement(container);
                renderMathInElement(container, katexOptions);
            }}
            mathRendered = true;
        }} catch(e) {{
            console.warn('KaTeX error:', e);
        }}
    }}
}}

document.addEventListener('DOMContentLoaded', doRenderMath);
window.addEventListener('load', function() {{
    doRenderMath();
    if (document.fonts && document.fonts.ready) {{
        document.fonts.ready.then(function() {{
            console.log('Fonts ready for print');
        }});
    }}
}});

function triggerPrint() {{
    doRenderMath();
    var btn = document.querySelector('.btn-print');
    if (btn) btn.disabled = true;

    var executePrint = function() {{
        setTimeout(function() {{
            window.print();
            if (btn) btn.disabled = false;
        }}, 150);
    }};

    if (document.fonts && document.fonts.ready) {{
        document.fonts.ready.then(executePrint).catch(executePrint);
    }} else {{
        executePrint();
    }}
}}
</script>
</head>
<body>
<div class="handout-container">
    <div class="no-print">
        <button class="btn-print" onclick="triggerPrint()">🖨️ 列印 / 另存為 A4 PDF</button>
    </div>
    <div class="handout-header">
        <h1 class="handout-title">{title_esc}</h1>
        <p class="handout-subtitle">{subtitle_esc}</p>
    </div>
    {slides_html}
</div>
<script>
if (window.renderMathInElement) {{
    doRenderMath();
}}
</script>
</body>
</html>
"""




def add_markdown_and_math_to_paragraph(p, text: str, font_size=None, font_color=None, base_bold=False):
    """Parse inline markdown (bold, italic, code) and LaTeX math ($...$, $$...$$) and add formatted runs."""
    if not text:
        return
    import re
    from docx.shared import Pt, RGBColor

    # Auto wrap bare LaTeX commands if needed
    text_processed = _wrap_bare_latex(str(text))

    pattern = re.compile(r"(\$\$[\s\S]*?\$\$|\$[^$\n]+?\$|\\\[[\s\S]*?\\\]|\\\([\s\S]*?\\\)|(?<!\*)\*\*[^\*\n]+?\*\*(?!\*)|__[^_\n]+?__|(?<!\*)\*[^\*\n]+?\*(?!\*)|`[^`\n]+?`)")
    tokens = pattern.split(text_processed)

    for token in tokens:
        if not token:
            continue

        # Math formula: $$...$$, $...$, \[...\], \(...\)
        if (token.startswith("$$") and token.endswith("$$")) or (token.startswith("$") and token.endswith("$")) or (token.startswith(r"\[") and token.endswith(r"\]")) or (token.startswith(r"\(") and token.endswith(r"\)")):
            math_clean = clean_latex_to_unicode(token)
            run = p.add_run(math_clean)
            run.font.name = "Cambria Math"
            run.font.italic = True
            if base_bold:
                run.font.bold = True
            if font_size:
                run.font.size = font_size
            if font_color:
                run.font.color.rgb = font_color

        # Bold markdown: **...** or __...__
        elif (token.startswith("**") and token.endswith("**") and len(token) >= 4) or (token.startswith("__") and token.endswith("__") and len(token) >= 4):
            content = token[2:-2]
            run = p.add_run(content)
            run.font.bold = True
            if font_size:
                run.font.size = font_size
            if font_color:
                run.font.color.rgb = font_color

        # Italic markdown: *...*
        elif token.startswith("*") and token.endswith("*") and len(token) > 2:
            content = token[1:-1]
            run = p.add_run(content)
            run.font.italic = True
            if base_bold:
                run.font.bold = True
            if font_size:
                run.font.size = font_size
            if font_color:
                run.font.color.rgb = font_color

        # Code markdown: `...`
        elif token.startswith("`") and token.endswith("`") and len(token) > 2:
            content = token[1:-1]
            run = p.add_run(content)
            run.font.name = "Consolas"
            run.font.size = font_size or Pt(9.5)
            run.font.color.rgb = RGBColor(180, 83, 9)

        # Plain text
        else:
            run = p.add_run(token)
            if base_bold:
                run.font.bold = True
            if font_size:
                run.font.size = font_size
            if font_color:
                run.font.color.rgb = font_color


def make_handout_docx(handout: Handout) -> bytes:
    """Generate professional Word (.docx) file for Handout with math and formatting support."""
    import docx
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml import parse_xml
    from docx.oxml.ns import nsdecls

    doc = docx.Document()
    for section in doc.sections:
        section.page_width = Inches(8.27)
        section.page_height = Inches(11.69)
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    style_normal = doc.styles["Normal"]
    font = style_normal.font
    font.name = "Microsoft JhengHei"
    font.size = Pt(10.5)
    font.color.rgb = RGBColor(30, 41, 59)

    # Title
    title_p = doc.add_paragraph()
    add_markdown_and_math_to_paragraph(title_p, handout.title or "隨堂講義", font_size=Pt(20), font_color=RGBColor(15, 23, 42), base_bold=True)
    title_p.paragraph_format.space_after = Pt(2)

    # Subtitle
    if handout.subtitle:
        sub_p = doc.add_paragraph()
        add_markdown_and_math_to_paragraph(sub_p, handout.subtitle, font_size=Pt(11), font_color=RGBColor(100, 116, 139))
        sub_p.paragraph_format.space_after = Pt(8)

    # Overview Table Box
    if handout.overview:
        tbl = doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        tbl.columns[0].width = Inches(6.67)
        cell = tbl.cell(0, 0)
        shading = parse_xml(r'<w:shd {} w:fill="EFF6FF"/>'.format(nsdecls("w")))
        cell._tc.get_or_add_tcPr().append(shading)
        borders = parse_xml(r"""
            <w:tcBorders {} >
                <w:top w:val="none" />
                <w:left w:val="single" w:sz="24" w:space="0" w:color="2563EB" />
                <w:bottom w:val="none" />
                <w:right w:val="none" />
            </w:tcBorders>
        """.format(nsdecls("w")))
        cell._tc.get_or_add_tcPr().append(borders)

        cp = cell.paragraphs[0]
        c_title_run = cp.add_run("【課程導讀】\n")
        c_title_run.font.bold = True
        c_title_run.font.color.rgb = RGBColor(37, 99, 235)
        add_markdown_and_math_to_paragraph(cp, handout.overview, font_size=Pt(10), font_color=RGBColor(30, 41, 59))
        doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # Sections
    for idx, sec in enumerate(handout.sections, 1):
        sec_h = doc.add_paragraph()
        sec_h_title = f"§ {idx}. {sec.title}"
        add_markdown_and_math_to_paragraph(sec_h, sec_h_title, font_size=Pt(13), font_color=RGBColor(30, 58, 138), base_bold=True)
        sec_h.paragraph_format.space_before = Pt(10)
        sec_h.paragraph_format.space_after = Pt(4)

        if sec.summary:
            sum_p = doc.add_paragraph()
            add_markdown_and_math_to_paragraph(sum_p, sec.summary, font_size=Pt(10.5), font_color=RGBColor(51, 65, 85))
            sum_p.paragraph_format.space_after = Pt(6)

        if sec.key_points:
            kp_title = doc.add_paragraph()
            kp_run = kp_title.add_run("📌 核心要點：")
            kp_run.font.bold = True
            kp_run.font.color.rgb = RGBColor(22, 101, 52)
            kp_title.paragraph_format.space_after = Pt(2)
            for kp in sec.key_points:
                p = doc.add_paragraph(style="List Bullet")
                add_markdown_and_math_to_paragraph(p, kp, font_size=Pt(10), font_color=RGBColor(30, 41, 59))
                p.paragraph_format.space_after = Pt(2)

        if sec.discussion_questions:
            dq_title = doc.add_paragraph()
            dq_run = dq_title.add_run("💬 隨堂思考與練習：")
            dq_run.font.bold = True
            dq_run.font.color.rgb = RGBColor(146, 64, 14)
            dq_title.paragraph_format.space_before = Pt(4)
            dq_title.paragraph_format.space_after = Pt(2)
            for q_idx, dq in enumerate(sec.discussion_questions, 1):
                p = doc.add_paragraph()
                p_num = p.add_run(f"{q_idx}. ")
                p_num.font.bold = True
                add_markdown_and_math_to_paragraph(p, dq, font_size=Pt(10), font_color=RGBColor(30, 41, 59))
                p.paragraph_format.space_after = Pt(2)

        if sec.source_pages:
            ref_p = doc.add_paragraph()
            ref_run = ref_p.add_run(f"教材出處：第 {', '.join(map(str, sec.source_pages))} 頁")
            ref_run.font.size = Pt(9)
            ref_run.font.italic = True
            ref_run.font.color.rgb = RGBColor(148, 163, 184)
            ref_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            ref_p.paragraph_format.space_after = Pt(8)

    # Key Takeaways
    if handout.key_takeaways:
        doc.add_paragraph().paragraph_format.space_after = Pt(4)
        takeaway_tbl = doc.add_table(rows=1, cols=1)
        takeaway_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        takeaway_tbl.columns[0].width = Inches(6.67)
        t_cell = takeaway_tbl.cell(0, 0)
        t_shading = parse_xml(r'<w:shd {} w:fill="F8FAFC"/>'.format(nsdecls("w")))
        t_cell._tc.get_or_add_tcPr().append(t_shading)
        t_borders = parse_xml(r"""
            <w:tcBorders {} >
                <w:top w:val="single" w:sz="8" w:space="0" w:color="CBD5E1" />
                <w:left w:val="single" w:sz="8" w:space="0" w:color="CBD5E1" />
                <w:bottom w:val="single" w:sz="8" w:space="0" w:color="CBD5E1" />
                <w:right w:val="single" w:sz="8" w:space="0" w:color="CBD5E1" />
            </w:tcBorders>
        """.format(nsdecls("w")))
        t_cell._tc.get_or_add_tcPr().append(t_borders)

        tcp = t_cell.paragraphs[0]
        t_head = tcp.add_run("🎯 本單元總結與核心精華\n")
        t_head.font.bold = True
        t_head.font.color.rgb = RGBColor(15, 23, 42)
        for t in handout.key_takeaways:
            tp = t_cell.add_paragraph()
            tp.add_run("• ")
            add_markdown_and_math_to_paragraph(tp, t, font_size=Pt(10), font_color=RGBColor(30, 41, 59))
            tp.paragraph_format.space_after = Pt(2)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.getvalue()


def make_quiz_docx(sheet: QuizSheet, teacher_mode: bool = False) -> bytes:
    """Generate professional Word (.docx) file for QuizSheet with math formula and markdown support."""
    import docx
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT

    doc = docx.Document()
    for section in doc.sections:
        section.page_width = Inches(8.27)
        section.page_height = Inches(11.69)
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    style_normal = doc.styles["Normal"]
    font = style_normal.font
    font.name = "Microsoft JhengHei"
    font.size = Pt(10.5)
    font.color.rgb = RGBColor(30, 41, 59)

    # Title
    title_p = doc.add_paragraph()
    add_markdown_and_math_to_paragraph(title_p, sheet.title or "單元評量測驗卷", font_size=Pt(18), font_color=RGBColor(15, 23, 42), base_bold=True)
    title_p.paragraph_format.space_after = Pt(2)
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Subtitle / Mode Indicator
    mode_text = "【教師詳解卷】" if teacher_mode else "【學生練習測驗卷】"
    sub_p = doc.add_paragraph()
    sub_run = sub_p.add_run(f"{mode_text}   建議測驗時間：{sheet.duration_minutes} 分鐘 | 總題數：{len(sheet.questions)} 題")
    sub_run.font.size = Pt(10.5)
    sub_run.font.bold = True
    sub_run.font.color.rgb = RGBColor(37, 99, 235) if teacher_mode else RGBColor(100, 116, 139)
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_p.paragraph_format.space_after = Pt(10)

    # Student info table
    info_tbl = doc.add_table(rows=1, cols=4)
    info_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    info_tbl.columns[0].width = Inches(1.6)
    info_tbl.columns[1].width = Inches(1.2)
    info_tbl.columns[2].width = Inches(2.2)
    info_tbl.columns[3].width = Inches(1.67)

    info_cells = info_tbl.rows[0].cells
    info_cells[0].paragraphs[0].text = "班級：____________"
    info_cells[1].paragraphs[0].text = "座號：______"
    info_cells[2].paragraphs[0].text = "姓名：________________"
    info_cells[3].paragraphs[0].text = "得分：__________"

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    type_labels = {
        "single_choice": "單選題",
        "multiple_choice": "多選題",
        "problem_solving": "計算與推導論述題",
    }
    diff_labels = {"easy": "基礎", "medium": "中等", "hard": "進階"}

    for idx, q in enumerate(sheet.questions, 1):
        t_name = type_labels.get(q.type, "測驗題")
        d_name = diff_labels.get(q.difficulty, "中等")

        qp = doc.add_paragraph()
        q_num = qp.add_run(f"第 {idx} 題. ")
        q_num.font.bold = True
        q_num.font.color.rgb = RGBColor(30, 58, 138)

        q_badge = qp.add_run(f"【{t_name} · 難度：{d_name}】 ")
        q_badge.font.size = Pt(9.5)
        q_badge.font.color.rgb = RGBColor(100, 116, 139)

        add_markdown_and_math_to_paragraph(qp, q.question, font_size=Pt(10.5), font_color=RGBColor(15, 23, 42), base_bold=True)
        qp.paragraph_format.space_before = Pt(8)
        qp.paragraph_format.space_after = Pt(4)

        if q.options:
            for opt in q.options:
                op = doc.add_paragraph()
                add_markdown_and_math_to_paragraph(op, opt, font_size=Pt(10), font_color=RGBColor(51, 65, 85))
                op.paragraph_format.left_indent = Inches(0.3)
                op.paragraph_format.space_after = Pt(2)

        if teacher_mode:
            ans_p = doc.add_paragraph()
            ans_lbl = ans_p.add_run("【標準答案】：")
            ans_lbl.font.bold = True
            ans_lbl.font.color.rgb = RGBColor(22, 101, 52)
            add_markdown_and_math_to_paragraph(ans_p, q.answer, font_size=Pt(10.5), font_color=RGBColor(22, 101, 52), base_bold=True)
            ans_p.paragraph_format.left_indent = Inches(0.2)
            ans_p.paragraph_format.space_after = Pt(2)

            exp_p = doc.add_paragraph()
            exp_lbl = exp_p.add_run("【試題詳解】：")
            exp_lbl.font.bold = True
            exp_lbl.font.color.rgb = RGBColor(30, 41, 59)
            add_markdown_and_math_to_paragraph(exp_p, q.explanation, font_size=Pt(10), font_color=RGBColor(30, 41, 59))
            exp_p.paragraph_format.left_indent = Inches(0.2)
            exp_p.paragraph_format.space_after = Pt(2)

            if q.source_pages:
                src_p = doc.add_paragraph()
                src_run = src_p.add_run(f"【出處頁碼】：第 {', '.join(map(str, q.source_pages))} 頁")
                src_run.font.size = Pt(9)
                src_run.font.italic = True
                src_run.font.color.rgb = RGBColor(148, 163, 184)
                src_p.paragraph_format.left_indent = Inches(0.2)
                src_p.paragraph_format.space_after = Pt(6)
        else:
            ans_space = doc.add_paragraph()
            ans_space.add_run("作答區：(        )")
            ans_space.paragraph_format.left_indent = Inches(0.2)
            ans_space.paragraph_format.space_after = Pt(8)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.getvalue()


def make_deck_docx(deck: Deck) -> bytes:
    """Generate professional Word (.docx) file for Slide Deck & Speaker Notes."""
    import docx
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml import parse_xml
    from docx.oxml.ns import nsdecls

    doc = docx.Document()
    for section in doc.sections:
        section.page_width = Inches(8.27)
        section.page_height = Inches(11.69)
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    style_normal = doc.styles["Normal"]
    font = style_normal.font
    font.name = "Microsoft JhengHei"
    font.size = Pt(10.5)
    font.color.rgb = RGBColor(30, 41, 59)

    # Title
    title_p = doc.add_paragraph()
    add_markdown_and_math_to_paragraph(title_p, deck.title or "教學簡報與逐頁演講稿", font_size=Pt(20), font_color=RGBColor(15, 23, 42), base_bold=True)
    title_p.paragraph_format.space_after = Pt(2)

    # Subtitle
    sub_text = f"{deck.subtitle} · 預估講授時間：{deck.duration} 分鐘 · 共 {len(deck.slides)} 頁" if deck.duration else (deck.subtitle or "")
    if sub_text:
        sub_p = doc.add_paragraph()
        add_markdown_and_math_to_paragraph(sub_p, sub_text, font_size=Pt(10.5), font_color=RGBColor(100, 116, 139))
        sub_p.paragraph_format.space_after = Pt(12)

    for idx, s in enumerate(deck.slides, 1):
        icon_str = getattr(s, "icon", "💡") or "💡"

        # Slide Header
        slide_h = doc.add_paragraph()
        slide_h_title = f"第 {idx} 頁：{icon_str} {s.title}"
        add_markdown_and_math_to_paragraph(slide_h, slide_h_title, font_size=Pt(13.5), font_color=RGBColor(194, 65, 12), base_bold=True)
        slide_h.paragraph_format.space_before = Pt(12)
        slide_h.paragraph_format.space_after = Pt(4)

        # Slide Bullets
        if s.bullets:
            b_head = doc.add_paragraph()
            b_head_run = b_head.add_run("📌 投影片核心要點：")
            b_head_run.font.bold = True
            b_head_run.font.size = Pt(10)
            b_head_run.font.color.rgb = RGBColor(154, 52, 18)
            b_head.paragraph_format.space_after = Pt(2)

            for b in s.bullets:
                bp = doc.add_paragraph(style="List Bullet")
                add_markdown_and_math_to_paragraph(bp, b, font_size=Pt(10), font_color=RGBColor(30, 41, 59))
                bp.paragraph_format.space_after = Pt(2)

        # Speaker Notes Box
        if s.speaker_notes:
            notes_tbl = doc.add_table(rows=1, cols=1)
            notes_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
            notes_tbl.columns[0].width = Inches(6.67)
            n_cell = notes_tbl.cell(0, 0)
            n_shading = parse_xml(r'<w:shd {} w:fill="F8FAFC"/>'.format(nsdecls("w")))
            n_cell._tc.get_or_add_tcPr().append(n_shading)
            n_borders = parse_xml(r"""
                <w:tcBorders {} >
                    <w:top w:val="none" />
                    <w:left w:val="single" w:sz="20" w:space="0" w:color="DE5B37" />
                    <w:bottom w:val="none" />
                    <w:right w:val="none" />
                </w:tcBorders>
            """.format(nsdecls("w")))
            n_cell._tc.get_or_add_tcPr().append(n_borders)

            n_cp = n_cell.paragraphs[0]
            n_head = n_cp.add_run("🎙️ 講師逐頁演講稿與延伸備課筆記：\n")
            n_head.font.bold = True
            n_head.font.size = Pt(10)
            n_head.font.color.rgb = RGBColor(222, 91, 55)

            np_content = n_cell.add_paragraph()
            add_markdown_and_math_to_paragraph(np_content, s.speaker_notes, font_size=Pt(9.5), font_color=RGBColor(51, 65, 85))
            np_content.paragraph_format.space_after = Pt(2)

        # Visual prompt suggestion if any
        if getattr(s, "visual_prompt", None):
            vp_p = doc.add_paragraph()
            vp_lbl = vp_p.add_run("🖼️ 畫面呈現建議：")
            vp_lbl.font.size = Pt(9)
            vp_lbl.font.bold = True
            vp_lbl.font.color.rgb = RGBColor(148, 163, 184)
            add_markdown_and_math_to_paragraph(vp_p, s.visual_prompt, font_size=Pt(9), font_color=RGBColor(100, 116, 139))
            vp_p.paragraph_format.space_before = Pt(2)
            vp_p.paragraph_format.space_after = Pt(2)

        # Source pages
        if s.source_pages:
            ref_p = doc.add_paragraph()
            ref_run = ref_p.add_run(f"教材出處：第 {', '.join(map(str, sec.source_pages) if 'sec' in locals() else map(str, s.source_pages))} 頁")
            ref_run.font.size = Pt(9)
            ref_run.font.italic = True
            ref_run.font.color.rgb = RGBColor(148, 163, 184)
            ref_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            ref_p.paragraph_format.space_after = Pt(6)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.getvalue()


def make_quiz_html(sheet: QuizSheet, teacher_mode: bool = False) -> str:
    """Generate professional printable A4 HTML for QuizSheet."""
    type_labels = {
        "single_choice": "單選題",
        "multiple_choice": "多選題",
        "problem_solving": "計算與推導論述題",
    }
    diff_labels = {"easy": "基礎", "medium": "中等", "hard": "進階"}

    questions_html = ""
    for idx, q in enumerate(sheet.questions, 1):
        t_name = type_labels.get(q.type, "測驗題")
        d_name = diff_labels.get(q.difficulty, "中等")
        q_text_fmt = _format_handout_text(q.question)

        options_html = ""
        if q.options:
            options_items = "".join(f"<div class='quiz-option'>{_format_handout_text(opt)}</div>" for opt in q.options)
            options_html = f"<div class='quiz-options-grid'>{options_items}</div>"

        solution_box_html = ""
        if teacher_mode:
            pages_html = f"<div class='quiz-source'>出處頁碼：第 {', '.join(map(str, q.source_pages))} 頁</div>" if q.source_pages else ""
            solution_box_html = f"""
            <div class="solution-box">
                <div class="solution-answer"><strong>【標準答案】</strong>：<code>{_format_handout_text(q.answer)}</code></div>
                <div class="solution-explanation"><strong>【試題詳解】</strong>：{_format_handout_text(q.explanation)}</div>
                {pages_html}
            </div>
            """
        else:
            solution_box_html = """
            <div class="student-answer-box">
                <span>作答區 / 演算草稿：</span>
                <div class="student-answer-line"></div>
            </div>
            """

        questions_html += f"""
        <div class="quiz-item">
            <div class="quiz-item-header">
                <span class="quiz-number">第 {idx} 題.</span>
                <span class="quiz-badge">{t_name} · 難度：{d_name}</span>
                <div class="quiz-question-body">{q_text_fmt}</div>
            </div>
            {options_html}
            {solution_box_html}
        </div>
        """

    mode_title = "【教師詳解卷】" if teacher_mode else "【學生練習測驗卷】"
    title_esc = _format_handout_text(sheet.title or "單元評量測驗卷")

    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{sheet.title or '單元評量測驗卷'} {mode_title}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/contrib/auto-render.min.js"></script>
<style>
@page {{
    size: A4 portrait;
    margin: 12mm 15mm;
}}
*, *:before, *:after {{
    box-sizing: border-box;
}}
body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans TC", sans-serif;
    color: #1e293b;
    background: #f8fafc;
    margin: 0;
    padding: 20px;
    line-height: 1.6;
}}
.quiz-container {{
    max-width: 820px;
    margin: 0 auto;
    background: #ffffff;
    padding: 32px;
    border-radius: 8px;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.08);
    border: 1px solid #e2e8f0;
}}
.quiz-header {{
    text-align: center;
    border-bottom: 2px solid #334155;
    padding-bottom: 12px;
    margin-bottom: 16px;
}}
.quiz-title {{
    font-size: 20px;
    font-weight: 800;
    color: #0f172a;
    margin: 0 0 4px 0;
}}
.quiz-subtitle {{
    font-size: 13px;
    color: #475569;
    font-weight: 600;
    margin: 0 0 10px 0;
}}
.student-info-bar {{
    display: flex;
    justify-content: space-between;
    background: #f1f5f9;
    padding: 8px 16px;
    border-radius: 6px;
    border: 1px solid #cbd5e1;
    font-size: 13px;
    font-weight: 600;
    color: #334155;
    margin-top: 10px;
}}
.quiz-item {{
    margin-bottom: 20px;
    padding-bottom: 14px;
    border-bottom: 1px dashed #cbd5e1;
}}
.quiz-item:last-child {{
    border-bottom: none;
}}
.quiz-item-header {{
    font-size: 14px;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 8px;
}}
.quiz-number {{
    color: #1e3a8a;
    margin-right: 4px;
}}
.quiz-badge {{
    font-size: 11px;
    padding: 2px 6px;
    background: #e2e8f0;
    color: #475569;
    border-radius: 4px;
    font-weight: 500;
    margin-right: 6px;
}}
.quiz-question-body {{
    display: inline;
    font-weight: 600;
}}
.quiz-options-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px 16px;
    margin: 8px 0 10px 14px;
    font-size: 13px;
}}
@media (max-width: 600px) {{
    .quiz-options-grid {{
        grid-template-columns: 1fr;
    }}
}}
.quiz-option {{
    padding: 4px 0;
    color: #334155;
}}
.solution-box {{
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-left: 4px solid #16a34a;
    padding: 10px 14px;
    border-radius: 0 6px 6px 0;
    margin-top: 8px;
    font-size: 12.5px;
    line-height: 1.55;
}}
.solution-answer {{
    color: #15803d;
    margin-bottom: 4px;
}}
.solution-explanation {{
    color: #166534;
}}
.quiz-source {{
    font-size: 11px;
    color: #86efac;
    text-align: right;
    margin-top: 4px;
}}
.student-answer-box {{
    margin-top: 8px;
    font-size: 12px;
    color: #64748b;
}}
.student-answer-line {{
    border-bottom: 1px dotted #cbd5e1;
    height: 24px;
    margin-top: 2px;
}}
.no-print {{
    margin-bottom: 18px;
    display: flex;
    justify-content: flex-end;
    gap: 10px;
}}
.btn-print {{
    background: #1e293b;
    color: #fff;
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 13.5px;
    font-weight: 600;
}}
.btn-print:hover {{
    background: #0f172a;
}}
@media print {{
    *, *:before, *:after {{
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
        box-sizing: border-box !important;
    }}
    html, body {{
        background: #ffffff !important;
        color: #0f172a !important;
        margin: 0 !important;
        padding: 0 !important;
        width: 100% !important;
        height: auto !important;
        min-height: 100% !important;
        overflow: visible !important;
    }}
    .quiz-container {{
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
        width: 100% !important;
        border: none !important;
    }}
    .no-print {{
        display: none !important;
    }}
    .quiz-item {{
        break-inside: avoid !important;
        page-break-inside: avoid !important;
    }}
    .katex-display {{
        break-inside: avoid !important;
        page-break-inside: avoid !important;
        overflow-x: visible !important;
    }}
}}
</style>
<script>
var katexOptions = {{
    delimiters: [
        {{left: '$$', right: '$$', display: true}},
        {{left: '$', right: '$', display: false}},
        {{left: '\\\\[', right: '\\\\]', display: true}},
        {{left: '\\\\(', right: '\\\\)', display: false}}
    ],
    throwOnError: false
}};

function unescapeMathInElement(element) {{
    if (!element) return;
    var html = element.innerHTML;
    html = html.replace(/(\\$\\$[\\s\\S]*?\\$\\$|\\$[^$\\n]+?\\$|\\\\\\[[\\s\\S]*?\\\\\\]|\\\\\\([\\s\\S]*?\\\\\\))/g, function(match) {{
        return match
            .replace(/&amp;/g, '&')
            .replace(/&lt;/g, '<')
            .replace(/&gt;/g, '>')
            .replace(/&quot;/g, '"')
            .replace(/&#39;/g, "'");
    }});
    element.innerHTML = html;
}}

var mathRendered = false;
function doRenderMath() {{
    if (mathRendered) return;
    if (window.renderMathInElement) {{
        try {{
            var container = document.querySelector('.quiz-container');
            if (container) {{
                unescapeMathInElement(container);
                renderMathInElement(container, katexOptions);
            }}
            mathRendered = true;
        }} catch(e) {{
            console.warn('KaTeX error:', e);
        }}
    }}
}}

document.addEventListener('DOMContentLoaded', doRenderMath);
window.addEventListener('load', function() {{
    doRenderMath();
}});

function triggerPrint() {{
    doRenderMath();
    var btn = document.querySelector('.btn-print');
    if (btn) btn.disabled = true;

    var executePrint = function() {{
        setTimeout(function() {{
            window.print();
            if (btn) btn.disabled = false;
        }}, 150);
    }};

    if (document.fonts && document.fonts.ready) {{
        document.fonts.ready.then(executePrint).catch(executePrint);
    }} else {{
        executePrint();
    }}
}}
</script>
</head>
<body>
<div class="quiz-container">
    <div class="no-print">
        <button class="btn-print" onclick="triggerPrint()">🖨️ 列印 / 另存為 A4 PDF</button>
    </div>
    <div class="quiz-header">
        <h1 class="quiz-title">{title_esc}</h1>
        <div class="quiz-subtitle">{mode_title} &nbsp;|&nbsp; 建議測驗時間：{sheet.duration_minutes} 分鐘 &nbsp;|&nbsp; 總題數：{len(sheet.questions)} 題</div>
        <div class="student-info-bar">
            <span>班級：___________</span>
            <span>座號：_______</span>
            <span>姓名：_______________</span>
            <span>得分：___________</span>
        </div>
    </div>
    {questions_html}
</div>
<script>
if (window.renderMathInElement) {{
    doRenderMath();
}}
</script>
</body>
</html>
"""




