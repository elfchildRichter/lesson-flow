from __future__ import annotations

import os
from pathlib import Path
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Depends, Request
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from typing import Optional
from pydantic import BaseModel, Field

from fastapi_auth_lite import (
    init_db,
    auth_router,
    admin_router,
    get_current_user,
    require_quota,
    decode_access_token,
    get_user_quota_info,
    hash_password,
)

from .models import (
    AskRequest,
    AskResponse,
    GenerateRequest,
    Handout,
    HandoutGenerateRequest,
    ProviderRequest,
    QuizGenerateRequest,
    QuizSheet,
)
from .services import (
    AIService,
    DocumentStore,
    make_deck_docx,
    make_deck_handout_html,
    make_deck_slides_html,
    make_handout_docx,
    make_handout_html,
    make_handout_markdown,
    make_pptx,
    make_quiz_docx,
    make_quiz_html,
    make_quiz_markdown,
    make_script,
    parse_pdf,
)
from .tiers import get_tier_config

load_dotenv(override=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv(override=True)
    db_path = os.getenv("AUTH_DB_PATH", "./data/users.db")
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    init_db()
    yield

app = FastAPI(
    title="課伴 LessonFlow",
    version="1.0.0",
    lifespan=lifespan
)

# 掛載認證與管理員介面 (/api/auth/*, /api/admin/*)
auth_router.routes = [r for r in auth_router.routes if getattr(r, "path", "") != "/api/user/me"]
app.include_router(auth_router)
app.include_router(admin_router)

store = DocumentStore()
ai = AIService()
STATIC_DIR = Path(__file__).parent / "static"


from .workflows import company_router, skill_registry


@app.get("/api/agent/skills")
def get_agent_skills() -> dict:
    skills = skill_registry.list_skills()
    return {"skills": [s.to_dict() for s in skills]}


def get_user_tier_and_role(current_user: dict) -> tuple[str, str]:
    user_id = current_user.get("user_id") or current_user.get("id")
    username = current_user.get("sub") or current_user.get("username")
    role = current_user.get("role", "user")
    tier_key = current_user.get("tier", "teacher_trial")

    db_path = os.getenv("AUTH_DB_PATH", "./data/users.db")
    if os.path.exists(db_path):
        import sqlite3
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT tier, role FROM users WHERE id = ? OR username = ?", (user_id, username))
            row = cursor.fetchone()
            if row:
                if row[0]:
                    tier_key = row[0]
                if row[1]:
                    role = row[1]
    if role == "admin":
        tier_key = "admin"
    return tier_key, role


from app.tiers import get_tier_config, ACTION_CREDIT_COSTS


def get_optional_current_user(request: Request) -> dict | None:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ", 1)[1]
    try:
        return decode_access_token(token)
    except Exception:
        return None


def get_user_credits_info(user_id: int | str, username: str, role: str, tier_config: dict) -> dict:
    daily_limit = tier_config.get("daily_credits", 100)
    if role == "admin" or daily_limit == -1:
        return {
            "used": 0,
            "daily_limit": -1,
            "remaining": -1,
            "is_unlimited": True,
            "costs": ACTION_CREDIT_COSTS
        }
    db_path = os.getenv("AUTH_DB_PATH", "./data/users.db")
    used_credits = 0
    if os.path.exists(db_path) and user_id:
        import sqlite3
        from datetime import date
        today_str = date.today().isoformat()
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT used_count FROM daily_quotas WHERE user_id = ? AND action = 'credits' AND usage_date = ?",
                    (user_id, today_str)
                )
                row = cursor.fetchone()
                if row:
                    used_credits = row[0]
                else:
                    cursor.execute(
                        "INSERT OR IGNORE INTO daily_quotas (user_id, action, usage_date, used_count, daily_limit) VALUES (?, 'credits', ?, 0, ?)",
                        (user_id, today_str, daily_limit)
                    )
                    conn.commit()
        except Exception:
            pass
    remaining = max(0, daily_limit - used_credits)
    return {
        "used": used_credits,
        "daily_limit": daily_limit,
        "remaining": remaining,
        "is_unlimited": False,
        "costs": ACTION_CREDIT_COSTS
    }


def deduct_user_credits(user_id: int | str, cost: int, daily_limit: int, role: str, action_label: str = "本操作") -> None:
    """檢查並扣除使用者備課點數，若點數不足則拋出 HTTPException(429)"""
    if role == "admin" or daily_limit == -1 or cost <= 0:
        return
    db_path = os.getenv("AUTH_DB_PATH", "./data/users.db")
    if os.path.exists(db_path) and user_id:
        import sqlite3
        from datetime import date
        today_str = date.today().isoformat()
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT used_count FROM daily_quotas WHERE user_id = ? AND action = 'credits' AND usage_date = ?",
                (user_id, today_str)
            )
            row = cursor.fetchone()
            used_credits = row[0] if row else 0
            if used_credits + cost > daily_limit:
                remaining = max(0, daily_limit - used_credits)
                raise HTTPException(
                    status_code=429,
                    detail=f"今日備課點數不足 ({action_label}需要 {cost} 點，目前剩餘 {remaining} 點，每日額度 {daily_limit} 點)。請升級帳號或明日重置。"
                )
            if row:
                cursor.execute(
                    "UPDATE daily_quotas SET used_count = used_count + ?, daily_limit = ? WHERE user_id = ? AND action = 'credits' AND usage_date = ?",
                    (cost, daily_limit, user_id, today_str)
                )
            else:
                cursor.execute(
                    "INSERT INTO daily_quotas (user_id, action, usage_date, used_count, daily_limit) VALUES (?, 'credits', ?, ?, ?)",
                    (user_id, today_str, cost, daily_limit)
                )
            conn.commit()


def require_dynamic_quota(action: str = "ask"):
    def dependency(current_user: dict = Depends(get_current_user)) -> dict:
        tier_key, role = get_user_tier_and_role(current_user)
        tier_config = get_tier_config(tier_key, role)
        cost = ACTION_CREDIT_COSTS.get(action, 1)

        user_id = current_user.get("user_id") or current_user.get("id")
        username = current_user.get("sub") or current_user.get("username")
        daily_limit = tier_config.get("daily_credits", 100)

        action_labels = {
            "deck": "生成教學簡報",
            "handout": "生成隨堂講義",
            "quiz": "生成單元試卷",
            "refine": "AI 局部微調",
            "ask": "文件提問",
            "parse": "標準教材解析",
            "vlm_parse": "VLM 視覺多模態解析",
        }
        deduct_user_credits(user_id, cost, daily_limit, role, action_labels.get(action, "本操作"))

        credits_info = get_user_credits_info(user_id, username, role, tier_config)
        current_user["credits"] = credits_info
        current_user["tier_config"] = tier_config
        current_user["tier"] = tier_key
        current_user["role"] = role
        # Backwards compatible mapping
        current_user["quota"] = {
            "credits": {
                "used_count": credits_info["used"],
                "daily_limit": credits_info["daily_limit"],
                "remaining": credits_info["remaining"]
            }
        }
        return current_user

    return dependency


def rollback_user_quota(user_id: int | str, action: str) -> None:
    """當生成或處理失敗時，自動將已扣除的點數回退。"""
    cost = ACTION_CREDIT_COSTS.get(action, 0)
    if cost <= 0:
        return
    db_path = os.getenv("AUTH_DB_PATH", "./data/users.db")
    if os.path.exists(db_path) and user_id:
        import sqlite3
        from datetime import date
        today_str = date.today().isoformat()
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE daily_quotas SET used_count = MAX(0, used_count - ?) WHERE user_id = ? AND action = 'credits' AND usage_date = ?",
                    (cost, user_id, today_str)
                )
                conn.commit()
        except Exception as exc:
            logging.getLogger(__name__).warning("回退點數失敗: %s", exc)


@app.post("/api/agent/dispatch")
def dispatch_agent_task(
    payload: dict,
    request: Request,
    current_user: dict = Depends(require_dynamic_quota("ask"))
) -> dict:
    query = payload.get("query", "").strip()
    platform = payload.get("platform", "FB / 社群媒體")
    if not query:
        raise HTTPException(400, "請提供有效的任務指令說明")

    user_id = current_user.get("id") or current_user.get("user_id", 0)
    username = current_user.get("username") or current_user.get("sub", "使用者")
    role = current_user.get("role", "user")
    tier_key = current_user.get("tier", "teacher_trial")
    tier_config = current_user.get("tier_config") or get_tier_config(tier_key, role)
    credits_info = current_user.get("credits") or get_user_credits_info(user_id, username, role, tier_config)

    user_info = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "tier": tier_config,
        "credits": credits_info,
        "quota": current_user.get("quota", {}),
    }

    full_payload = {
        "query": query,
        "platform": platform,
        "target_department": payload.get("target_department"),
        "history": payload.get("history", []),
        "ai_service": ai,
        "user_info": user_info,
    }
    try:
        state = company_router.invoke({"input_query": query, "payload": full_payload})
        return state.get("result", {})
    except Exception as exc:
        raise HTTPException(500, f"Agent 任務派發失敗：{exc}") from exc


@app.get("/api/user/me")
def get_current_user_profile(current_user: dict = Depends(get_current_user)) -> dict:
    user_id = current_user.get("user_id") or current_user.get("id")
    username = current_user.get("sub") or current_user.get("username")
    tier_key, role = get_user_tier_and_role(current_user)

    db_path = os.getenv("AUTH_DB_PATH", "./data/users.db")
    if os.path.exists(db_path):
        import sqlite3
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id = ? OR username = ?", (user_id, username))
            conn.commit()

    tier_config = get_tier_config(tier_key, role)
    credits_info = get_user_credits_info(user_id, username, role, tier_config)

    return {
        "id": user_id,
        "username": username,
        "role": role,
        "tier": tier_key,
        "tier_info": dict(tier_config),
        "credits": credits_info,
        "quota": {
            "credits": {
                "used_count": credits_info["used"],
                "daily_limit": credits_info["daily_limit"],
                "remaining": credits_info["remaining"]
            }
        }
    }


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", **ai.info}


@app.get("/api/provider")
def get_provider() -> dict:
    return ai.info


@app.post("/api/provider")
def set_provider(request: ProviderRequest) -> dict:
    try:
        info = ai.set_provider(request.provider)
        return {"status": "ok", **info}

    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc



def document_payload(document) -> dict:
    return {
        "id": document.id,
        "name": document.name,
        "pages": document.pages,
        "chunks": len(document.chunks),
        "size_bytes": document.size_bytes,
        **ai.info,
    }


@app.post("/api/documents")
async def upload_document(
    file: UploadFile = File(...),
    enable_multimodal: bool = Form(False),
    current_user: dict = Depends(require_dynamic_quota("upload"))
) -> dict:
    if file.content_type != "application/pdf" and not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(415, "只支援 PDF 檔案")
    tier_key, role = get_user_tier_and_role(current_user)
    tier_config = get_tier_config(tier_key, role)

    content = await file.read()
    max_mb = tier_config.get("max_upload_mb", 30)
    max_bytes = max_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(413, f"您的會員層級 [{tier_config['name_zh']}] 上傳檔案上限為 {max_mb} MB，請升級帳號或縮小檔案")

    if enable_multimodal and not tier_config.get("enable_vlm", False):
        enable_multimodal = False

    action = "vlm_parse" if enable_multimodal else "parse"
    cost = ACTION_CREDIT_COSTS.get(action, 5)
    user_id = current_user.get("user_id") or current_user.get("id")
    daily_limit = tier_config.get("daily_credits", 100)

    action_label = "VLM 視覺多模態解析" if enable_multimodal else "標準教材解析"
    deduct_user_credits(user_id, cost, daily_limit, role, action_label)

    try:
        document = parse_pdf(content, file.filename or "教材.pdf", ai_service=ai, enable_multimodal=enable_multimodal)
        ai.index(document)
    except ValueError as exc:
        rollback_user_quota(user_id, action)
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:
        rollback_user_quota(user_id, action)
        raise HTTPException(500, f"處理 PDF 時發生錯誤：{exc}") from exc
    store.add(document)
    return document_payload(document)


from pydantic import BaseModel


class ImportTextRequest(BaseModel):
    title: str
    content: str


@app.post("/api/documents/import_text")
def import_text_document(
    request: ImportTextRequest,
    current_user: dict = Depends(get_current_user)
) -> dict:
    from app.services import parse_text
    safe_title = (request.title or "AI_備課教案").strip()
    if not safe_title.endswith(".md") and not safe_title.endswith(".txt"):
        safe_title = f"{safe_title}.md"
    try:
        document = parse_text(request.content, filename=safe_title)
        ai.index(document)
        store.add(document)
        return document_payload(document)
    except Exception as exc:
        raise HTTPException(500, f"導入教案時發生錯誤：{exc}") from exc


@app.post("/api/ask", response_model=AskResponse)
def ask(
    request: AskRequest,
    current_user: dict = Depends(require_dynamic_quota("ask"))
) -> AskResponse:
    user_id = current_user.get("user_id") or current_user.get("id")
    try:
        document = store.get(request.document_id)
    except KeyError as exc:
        rollback_user_quota(user_id, "ask")
        raise HTTPException(404, "找不到文件，請重新上傳") from exc

    tier_config = current_user.get("tier_config") or get_tier_config(current_user.get("tier"), current_user.get("role"))
    enable_web_search = request.enable_web_search
    if enable_web_search and not tier_config.get("enable_web_search", False):
        enable_web_search = False

    try:
        import inspect
        sig = inspect.signature(ai.ask)
        if "history" in sig.parameters or any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
            answer, sources, mode = ai.ask(
                document,
                request.question,
                enable_web_search,
                history=request.history,
            )
        else:
            answer, sources, mode = ai.ask(document, request.question, enable_web_search)
    except Exception as exc:
        rollback_user_quota(user_id, "ask")
        raise HTTPException(502, f"AI 暫時無法回答：{exc}") from exc
    return AskResponse(answer=answer, sources=sources, mode=mode)


@app.post("/api/decks")
def generate_deck(
    request: GenerateRequest,
    current_user: dict = Depends(require_dynamic_quota("deck"))
) -> dict:
    user_id = current_user.get("user_id") or current_user.get("id")
    try:
        document = store.get(request.document_id)
    except KeyError as exc:
        rollback_user_quota(user_id, "deck")
        raise HTTPException(404, "找不到文件，請重新上傳") from exc

    tier_config = current_user.get("tier_config") or get_tier_config(current_user.get("tier"), current_user.get("role"))
    enable_web_search = request.enable_web_search
    if enable_web_search and not tier_config.get("enable_web_search", False):
        enable_web_search = False

    try:
        deck = ai.generate_deck(
            document,
            request.audience,
            request.tone,
            request.slide_count,
            request.duration,
            enable_web_search,
            language=request.language,
            handout_text=request.handout_text,
        )
    except Exception as exc:
        rollback_user_quota(user_id, "deck")
        raise HTTPException(502, f"產生教材時發生錯誤：{exc}") from exc
    store.decks[deck.id] = deck
    return deck.model_dump()


@app.get("/api/decks/{deck_id}/pptx")
def download_pptx(deck_id: str) -> Response:
    deck = store.decks.get(deck_id)
    if not deck:
        raise HTTPException(404, "找不到簡報")
    content = make_pptx(deck)
    return Response(content, media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation", headers={"Content-Disposition": f'attachment; filename="lesson-{deck.id}.pptx"'})


@app.get("/api/decks/{deck_id}/script")
def download_script(deck_id: str) -> Response:
    deck = store.decks.get(deck_id)
    if not deck:
        raise HTTPException(404, "找不到講稿")
    return Response(
        make_script(deck),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="script-{deck.id}.md"'},
    )


@app.get("/api/decks/{deck_id}/docx")
def download_deck_docx(deck_id: str) -> Response:
    deck = store.decks.get(deck_id)
    if not deck:
        raise HTTPException(404, "找不到簡報")
    docx_bytes = make_deck_docx(deck)
    return Response(
        docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="deck-notes-{deck.id}.docx"'},
    )


class RefineSlideRequest(BaseModel):
    instruction: str = Field(default="潤飾講稿與要點，使口語表達更自然、生動且具啟發性", max_length=500)


@app.post("/api/decks/{deck_id}/slides/{slide_index}/refine")
def refine_deck_slide(
    deck_id: str,
    slide_index: int,
    request: RefineSlideRequest = RefineSlideRequest(),
    current_user: dict = Depends(require_dynamic_quota("refine")),
) -> dict:
    user_id = current_user.get("user_id") or current_user.get("id")
    deck = store.decks.get(deck_id)
    if not deck:
        rollback_user_quota(user_id, "refine")
        raise HTTPException(404, "找不到簡報")
    if slide_index < 0 or slide_index >= len(deck.slides):
        rollback_user_quota(user_id, "refine")
        raise HTTPException(400, f"無效的投影片索引：{slide_index} (總頁數：{len(deck.slides)})")

    doc = None
    try:
        doc = store.get(deck.document_id)
    except Exception:
        pass

    try:
        refined_slide = ai.refine_slide(deck.slides[slide_index], instruction=request.instruction, document=doc)
        deck.slides[slide_index] = refined_slide
        store.decks[deck.id] = deck
        return {
            "status": "ok",
            "slide_index": slide_index,
            "slide": refined_slide.model_dump(),
            "deck": deck.model_dump(),
        }
    except Exception as exc:
        rollback_user_quota(user_id, "refine")
        raise HTTPException(502, f"AI 潤飾講稿失敗：{exc}") from exc


@app.patch("/api/decks/{deck_id}")
def update_deck_content(
    deck_id: str,
    payload: dict,
    current_user: Optional[dict] = Depends(get_optional_current_user),
) -> dict:
    deck = store.decks.get(deck_id)
    if not deck:
        raise HTTPException(404, "找不到簡報")

    try:
        if "title" in payload:
            deck.title = str(payload["title"])
        if "subtitle" in payload:
            deck.subtitle = str(payload["subtitle"])
        if "slides" in payload and isinstance(payload["slides"], list):
            from app.models import Slide
            new_slides = []
            for s in payload["slides"]:
                if isinstance(s, dict):
                    new_slides.append(Slide(**s))
                elif isinstance(s, Slide):
                    new_slides.append(s)
            deck.slides = new_slides
        store.decks[deck.id] = deck
        return {"status": "ok", "deck": deck.model_dump()}
    except Exception as exc:
        raise HTTPException(400, f"更新簡報資料格式錯誤：{exc}") from exc


from pydantic import BaseModel
import sqlite3


class TextDeckRequest(BaseModel):
    topic: str
    content: str


@app.post("/api/deck/generate_from_text")
def generate_deck_from_text(
    request: TextDeckRequest,
    current_user: dict = Depends(require_dynamic_quota("deck"))
) -> dict:
    from app.services import parse_text
    try:
        temp_doc = parse_text(request.content, filename=request.topic or "教學主題.md")
        store.add(temp_doc)
        deck = ai.generate_deck(
            temp_doc,
            audience="學生",
            tone="專業生動",
            slide_count=8,
            duration=30,
            enable_web_search=False,
            language="zh-TW"
        )
        store.decks[deck.id] = deck
        return {
            "status": "success",
            "deck_id": deck.id,
            "slide_count": len(deck.slides),
            "download_url": f"/api/decks/{deck.id}/pptx"
        }
    except Exception as exc:
        raise HTTPException(500, f"生成簡報失敗：{exc}") from exc


@app.post("/api/quiz/generate")
def generate_quiz(
    request: QuizGenerateRequest,
    current_user: dict = Depends(require_dynamic_quota("quiz")),
) -> dict:
    user_id = current_user.get("user_id") or current_user.get("id")
    try:
        document = store.get(request.document_id)
    except KeyError as exc:
        rollback_user_quota(user_id, "quiz")
        raise HTTPException(404, "找不到文件，請重新上傳") from exc

    tier_config = current_user.get("tier_config") or get_tier_config(current_user.get("tier"), current_user.get("role"))
    enable_web_search = request.enable_web_search
    if enable_web_search and not tier_config.get("enable_web_search", False):
        enable_web_search = False

    try:
        sheet = ai.generate_quiz(
            document,
            question_count=request.question_count,
            difficulty=request.difficulty,
            audience=request.audience,
            tone=request.tone,
            enable_web_search=enable_web_search,
            language=request.language,
            handout_text=request.handout_text,
        )
    except Exception as exc:
        rollback_user_quota(user_id, "quiz")
        raise HTTPException(502, f"出題失敗：{exc}") from exc

    store.quizzes[sheet.id] = sheet
    return sheet.model_dump()


class RegenerateQuestionRequest(BaseModel):
    instruction: str = Field(default="抽換為同概念但不同情境/題型的新題目", max_length=500)
    difficulty: str = Field(default="medium")
    language: str = Field(default="zh-TW")
    current_question: Optional[dict] = None
    quiz: Optional[dict] = None


@app.post("/api/quiz/{quiz_id}/questions/{question_index}/regenerate")
def regenerate_quiz_single_question(
    quiz_id: str,
    question_index: int,
    request: RegenerateQuestionRequest = RegenerateQuestionRequest(),
    current_user: dict = Depends(require_dynamic_quota("refine")),
) -> dict:
    user_id = current_user.get("user_id") or current_user.get("id")
    sheet = store.quizzes.get(quiz_id)
    if not sheet and request.quiz:
        try:
            from app.models import QuizSheet
            sheet = QuizSheet(**request.quiz)
            store.quizzes[sheet.id] = sheet
        except Exception:
            pass

    target_question = None
    if sheet and 0 <= question_index < len(sheet.questions):
        target_question = sheet.questions[question_index]
    elif request.current_question:
        try:
            from app.models import QuizQuestion
            target_question = QuizQuestion(**request.current_question)
        except Exception:
            pass

    if not target_question:
        rollback_user_quota(user_id, "refine")
        raise HTTPException(404, "找不到欲抽換的題目資料")

    doc = None
    if sheet:
        try:
            doc = store.get(sheet.document_id)
        except Exception:
            pass

    try:
        new_question = ai.regenerate_quiz_question(
            target_question,
            instruction=request.instruction,
            difficulty=request.difficulty,
            language=request.language,
            document=doc,
        )
        if sheet and 0 <= question_index < len(sheet.questions):
            sheet.questions[question_index] = new_question
            store.quizzes[sheet.id] = sheet
        return {
            "status": "ok",
            "question_index": question_index,
            "question": new_question.model_dump(),
            "quiz": sheet.model_dump() if sheet else None,
        }
    except Exception as exc:
        rollback_user_quota(user_id, "refine")
        raise HTTPException(502, f"AI 抽換題目失敗：{exc}") from exc


@app.patch("/api/quiz/{quiz_id}")
def update_quiz_content(
    quiz_id: str,
    payload: dict,
    current_user: Optional[dict] = Depends(get_optional_current_user),
) -> dict:
    sheet = store.quizzes.get(quiz_id)
    if not sheet:
        raise HTTPException(404, "找不到題目卷")

    try:
        if "title" in payload:
            sheet.title = str(payload["title"])
        if "description" in payload:
            sheet.description = str(payload["description"])
        if "questions" in payload and isinstance(payload["questions"], list):
            from app.models import QuizQuestion
            new_questions = []
            for q in payload["questions"]:
                if isinstance(q, dict):
                    new_questions.append(QuizQuestion(**q))
                elif isinstance(q, QuizQuestion):
                    new_questions.append(q)
            sheet.questions = new_questions
        store.quizzes[sheet.id] = sheet
        return {"status": "ok", "quiz": sheet.model_dump()}
    except Exception as exc:
        raise HTTPException(400, f"更新題目卷資料格式錯誤：{exc}") from exc


@app.get("/api/quiz/{quiz_id}")
def get_quiz(quiz_id: str) -> dict:
    sheet = store.quizzes.get(quiz_id)
    if not sheet:
        raise HTTPException(404, "找不到題目卷")
    return sheet.model_dump()


@app.get("/api/quiz/{quiz_id}/markdown")
def download_quiz_markdown(quiz_id: str, teacher: bool = False) -> Response:
    sheet = store.quizzes.get(quiz_id)
    if not sheet:
        raise HTTPException(404, "找不到題目卷")
    md_content = make_quiz_markdown(sheet, teacher_mode=teacher)
    prefix = "teacher" if teacher else "student"
    return Response(
        md_content,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="quiz-{prefix}-{sheet.id}.md"'},
    )


@app.get("/api/quiz/{quiz_id}/docx")
def download_quiz_docx(quiz_id: str, teacher: bool = False) -> Response:
    sheet = store.quizzes.get(quiz_id)
    if not sheet:
        raise HTTPException(404, "找不到題目卷")
    docx_bytes = make_quiz_docx(sheet, teacher_mode=teacher)
    prefix = "teacher" if teacher else "student"
    return Response(
        docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="quiz-{prefix}-{sheet.id}.docx"'},
    )


@app.get("/api/quiz/{quiz_id}/html")
@app.get("/api/quiz/{quiz_id}/print")
def view_quiz_html(quiz_id: str, teacher: bool = False) -> Response:
    sheet = store.quizzes.get(quiz_id)
    if not sheet:
        raise HTTPException(404, "找不到題目卷")
    html_content = make_quiz_html(sheet, teacher_mode=teacher)
    return Response(html_content, media_type="text/html; charset=utf-8")



@app.post("/api/handouts/generate")
def generate_handout_endpoint(
    request: HandoutGenerateRequest,
    current_user: dict = Depends(require_dynamic_quota("handout")),
) -> dict:
    user_id = current_user.get("user_id") or current_user.get("id")
    try:
        document = store.get(request.document_id)
    except KeyError as exc:
        rollback_user_quota(user_id, "handout")
        raise HTTPException(404, "找不到文件，請重新上傳") from exc

    tier_config = current_user.get("tier_config") or get_tier_config(current_user.get("tier"), current_user.get("role"))
    enable_web_search = request.enable_web_search
    if enable_web_search and not tier_config.get("enable_web_search", False):
        enable_web_search = False

    try:
        aud = request.audience or request.target_audience or "大學生"
        handout = ai.generate_handout(
            document,
            target_audience=aud,
            tone=request.tone,
            detail_level=request.detail_level,
            language=request.language,
            enable_web_search=enable_web_search,
        )
    except Exception as exc:
        rollback_user_quota(user_id, "handout")
        raise HTTPException(502, f"生成隨堂講義失敗：{exc}") from exc

    store.handouts[handout.id] = handout
    return handout.model_dump()


@app.get("/api/handouts/{handout_id}")
def get_handout(handout_id: str) -> dict:
    handout = store.handouts.get(handout_id)
    if not handout:
        raise HTTPException(404, "找不到講義資料")
    return handout.model_dump()


@app.patch("/api/handouts/{handout_id}")
def update_handout_content(
    handout_id: str,
    payload: dict,
    current_user: Optional[dict] = Depends(get_optional_current_user),
) -> dict:
    handout = store.handouts.get(handout_id)
    if not handout:
        raise HTTPException(404, "找不到講義資料")

    try:
        if "title" in payload:
            handout.title = str(payload["title"])
        if "subtitle" in payload:
            handout.subtitle = str(payload["subtitle"])
        if "overview" in payload:
            handout.overview = str(payload["overview"])
        if "key_takeaways" in payload and isinstance(payload["key_takeaways"], list):
            handout.key_takeaways = [str(k) for k in payload["key_takeaways"]]
        if "sections" in payload and isinstance(payload["sections"], list):
            from app.models import HandoutSection
            new_sections = []
            for s in payload["sections"]:
                if isinstance(s, dict):
                    new_sections.append(HandoutSection(**s))
                elif isinstance(s, HandoutSection):
                    new_sections.append(s)
            handout.sections = new_sections
        store.handouts[handout.id] = handout
        return {"status": "ok", "handout": handout.model_dump()}
    except Exception as exc:
        raise HTTPException(400, f"更新講義資料格式錯誤：{exc}") from exc


@app.get("/api/handouts/{handout_id}/markdown")
def download_handout_markdown(handout_id: str) -> Response:
    handout = store.handouts.get(handout_id)
    if not handout:
        raise HTTPException(404, "找不到講義資料")
    md_content = make_handout_markdown(handout)
    return Response(
        md_content,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="handout-{handout.id}.md"'},
    )


@app.get("/api/handouts/{handout_id}/html")
@app.get("/api/handouts/{handout_id}/print")
def view_handout_html(handout_id: str) -> Response:
    handout = store.handouts.get(handout_id)
    if not handout:
        raise HTTPException(404, "找不到講義資料")
    html_content = make_handout_html(handout)
    return Response(html_content, media_type="text/html; charset=utf-8")


@app.get("/api/handouts/{handout_id}/docx")
def download_handout_docx(handout_id: str) -> Response:
    handout = store.handouts.get(handout_id)
    if not handout:
        raise HTTPException(404, "找不到講義資料")
    docx_bytes = make_handout_docx(handout)
    return Response(
        docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="handout-{handout.id}.docx"'},
    )



@app.get("/api/decks/{deck_id}/handout/print")
def print_deck_handout(deck_id: str) -> Response:
    deck = store.decks.get(deck_id)
    if not deck:
        raise HTTPException(404, "找不到簡報資料")
    html_content = make_deck_handout_html(deck)
    return Response(html_content, media_type="text/html; charset=utf-8")


@app.get("/api/decks/{deck_id}/pdf")
@app.get("/api/decks/{deck_id}/slides/print")
def print_deck_slides(deck_id: str) -> Response:
    deck = store.decks.get(deck_id)
    if not deck:
        raise HTTPException(404, "找不到簡報資料")
    html_content = make_deck_slides_html(deck)
    return Response(html_content, media_type="text/html; charset=utf-8")


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

