from fastapi.testclient import TestClient

from app.main import app


def test_health_exposes_configured_models():
    response = TestClient(app).get("/api/health")

    assert response.status_code == 200
    assert response.json()["provider"] in {"gemini", "ollama", "openai", "ollama_cloud", "ollama_local"}
    assert response.json()["generation_model"]
    assert response.json()["embedding_model"]


def test_demo_endpoint_is_removed():
    paths = TestClient(app).get("/openapi.json").json()["paths"]

    assert "/api/demo" not in paths


def test_provider_get_and_post():
    client = TestClient(app)
    get_res = client.get("/api/provider")
    assert get_res.status_code == 200
    assert "provider" in get_res.json()

    post_res = client.post("/api/provider", json={"provider": "ollama_cloud"})
    assert post_res.status_code == 200
    assert post_res.json()["status"] == "ok"
    assert post_res.json()["provider"] == "ollama_cloud"

    # 測試切換至未啟動的本機服務應回傳 400 與安裝/啟動提示
    local_res = client.post("/api/provider", json={"provider": "ollama_local"})
    if local_res.status_code == 400:
        assert "未偵測到 Ollama 本機服務" in local_res.json()["detail"]


def test_upload_invalid_file_type():
    client = TestClient(app)
    from fastapi_auth_lite import get_current_user
    app.dependency_overrides[get_current_user] = lambda: {"id": "test_upload_admin", "username": "admin", "role": "admin", "tier": "teacher_pro"}
    try:
        response = client.post(
            "/api/documents",
            files={"file": ("test.txt", b"hello world", "text/plain")}
        )
        assert response.status_code == 415
        assert "只支援 PDF 檔案" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_ask_non_existent_document():
    client = TestClient(app)
    from app.main import store
    store.documents.clear()
    response = client.post(
        "/api/ask",
        json={"document_id": "non_existent", "question": "Hi?"}
    )
    # 不論認證通過與否，找不到文件時應處理 401/403 或 404
    assert response.status_code in {401, 403, 404}


def test_deck_non_existent_document_and_download():
    client = TestClient(app)
    response = client.get("/api/decks/non_existent/pptx")
    assert response.status_code == 404

    script_res = client.get("/api/decks/non_existent/script")
    assert script_res.status_code == 404


def test_quiz_endpoints():
    client = TestClient(app)
    from fastapi_auth_lite import get_current_user
    from app.main import store
    from app.models import Chunk, Document

    doc = Document(id="doc-quiz-test", name="測試教材.pdf", pages=1, chunks=[Chunk("量子力學基礎", 1, 0)], size_bytes=100)
    store.add(doc)

    app.dependency_overrides[get_current_user] = lambda: {"id": "quiz_tester_999", "username": "tester", "role": "admin", "tier": "teacher_pro"}
    try:
        # 測試找不到文件
        res_404 = client.post("/api/quiz/generate", json={"document_id": "not-found", "question_count": 3})
        assert res_404.status_code == 404

        # 測試成功產生與下載
        from app.main import ai
        ai._structured_response = lambda sys, prompt, schema: {
            "title": "量子力學小考",
            "description": "單元測驗",
            "focal_topics": ["波粒二象性"],
            "type": "single_choice",
            "question": "光子能量為何？",
            "options": ["A. E=hf", "B. E=mc", "C. E=1/2mv^2", "D. E=0"],
            "answer": "A",
            "explanation": "依據普朗克-愛因斯坦關係式，E=hf。",
            "source_pages": [1],
            "difficulty": "easy",
        }
        res_gen = client.post(
            "/api/quiz/generate",
            json={
                "document_id": "doc-quiz-test",
                "question_count": 1,
                "audience": "高中生",
                "tone": "活潑互動",
                "language": "zh-TW",
            },
        )
        assert res_gen.status_code == 200
        quiz_id = res_gen.json()["id"]
        assert len(res_gen.json()["questions"]) >= 1

        # 測試取得題目卷
        res_get = client.get(f"/api/quiz/{quiz_id}")
        assert res_get.status_code == 200
        assert res_get.json()["title"] == "量子力學小考"

        # 測試下載學生版與教師版 Markdown
        res_std = client.get(f"/api/quiz/{quiz_id}/markdown?teacher=false")
        assert res_std.status_code == 200
        assert "作答區" in res_std.text

        res_tch = client.get(f"/api/quiz/{quiz_id}/markdown?teacher=true")
        assert res_tch.status_code == 200
        assert "【標準答案】" in res_tch.text
    finally:
        app.dependency_overrides.clear()


def test_handout_endpoints():
    client = TestClient(app)
    from fastapi_auth_lite import get_current_user
    from app.main import store, ai
    from app.models import Chunk, Document

    doc = Document(id="doc-handout-test", name="物理手冊.pdf", pages=2, chunks=[Chunk("牛頓第一運動定律", 1, 0), Chunk("牛頓第二運動定律", 2, 1)], size_bytes=200)
    store.add(doc)

    app.dependency_overrides[get_current_user] = lambda: {"id": "handout_tester_999", "username": "tester", "role": "admin", "tier": "teacher_pro"}
    try:
        # Mock handout structured response
        ai._structured_response = lambda sys, prompt, schema: {
            "title": "力學基礎隨堂講義",
            "subtitle": "高中物理核心概念導讀",
            "target_audience": "高中生",
            "sections": [
                {
                    "title": "慣性與力學基礎",
                    "core_concept": "物體在不受外力時保持靜止或等速直線運動。",
                    "detailed_explanation": "牛頓第一定律又稱為慣性定律。",
                    "key_takeaways": ["慣性是物體抗拒運動狀態改變的性質"],
                    "source_pages": [1],
                }
            ],
            "overall_summary": "力學是物理學的基石。",
            "study_tips": ["理解公式物理意義而非死記"],
        }

        res_gen = client.post(
            "/api/handouts/generate",
            json={
                "document_id": "doc-handout-test",
                "audience": "高中生",
                "tone": "活潑互動",
                "language": "zh-TW",
                "detail_level": "standard",
            },
        )
        assert res_gen.status_code == 200
        handout_id = res_gen.json()["id"]
        assert handout_id in store.handouts

        # 測試取得講義
        res_get = client.get(f"/api/handouts/{handout_id}")
        assert res_get.status_code == 200
        assert res_get.json()["title"] == "力學基礎隨堂講義"

        # 測試 Markdown 匯出
        res_md = client.get(f"/api/handouts/{handout_id}/markdown")
        assert res_md.status_code == 200
        assert "力學基礎隨堂講義" in res_md.text

        # 測試 HTML A4 列印視圖
        res_html = client.get(f"/api/handouts/{handout_id}/html")
        assert res_html.status_code == 200
        assert "@page" in res_html.text
    finally:
        app.dependency_overrides.clear()


def test_admin_users_list_schema_migration():
    client = TestClient(app)
    from fastapi_auth_lite import get_current_user, init_db
    init_db()
    app.dependency_overrides[get_current_user] = lambda: {"id": 1, "username": "admin", "role": "admin"}
    try:
        response = client.get("/api/admin/users/list")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert "users" in response.json()
    finally:
        app.dependency_overrides.clear()


def test_deck_refine_and_patch():
    client = TestClient(app)
    from fastapi_auth_lite import get_current_user
    from app.main import store, ai
    from app.models import Deck, Slide

    deck = Deck(
        id="deck-refine-test",
        document_id="doc-refine-test",
        title="原始投影片標題",
        subtitle="副標題",
        slides=[
            Slide(
                title="第一頁",
                bullets=["重點一", "重點二"],
                speaker_notes="原始逐頁講稿",
                source_pages=[1],
            )
        ],
        duration=15,
        mode="test",
    )
    store.decks[deck.id] = deck

    app.dependency_overrides[get_current_user] = lambda: {"id": "refine_tester_1", "username": "tester", "role": "admin", "tier": "teacher_pro"}
    try:
        # Mock structured response for refine
        ai._structured_response = lambda sys, prompt, schema: {
            "bullets": ["優化要點一", "優化要點二"],
            "speaker_notes": "優化後的口語講稿",
        }

        # 1. Refine slide
        res_refine = client.post(
            f"/api/decks/{deck.id}/slides/0/refine",
            json={"instruction": "更生動"},
        )
        assert res_refine.status_code == 200
        assert res_refine.json()["slide"]["speaker_notes"] == "優化後的口語講稿"
        assert store.decks[deck.id].slides[0].speaker_notes == "優化後的口語講稿"

        # 2. PATCH manual edits (free 0 credits)
        res_patch = client.patch(
            f"/api/decks/{deck.id}",
            json={"title": "教師手動修改後的標題"},
        )
        assert res_patch.status_code == 200
        assert store.decks[deck.id].title == "教師手動修改後的標題"
    finally:
        app.dependency_overrides.clear()


def test_quiz_regenerate_and_patch():
    client = TestClient(app)
    from fastapi_auth_lite import get_current_user
    from app.main import store, ai
    from app.models import QuizQuestion, QuizSheet

    sheet = QuizSheet(
        id="quiz-regen-test",
        document_id="doc-regen-test",
        title="原始試卷",
        description="說明",
        questions=[
            QuizQuestion(
                id="q1",
                type="single_choice",
                question="1+1=?",
                options=["A. 1", "B. 2"],
                answer="B",
                explanation="1+1=2",
                source_pages=[1],
                difficulty="easy",
            )
        ],
    )
    store.quizzes[sheet.id] = sheet

    app.dependency_overrides[get_current_user] = lambda: {"id": "regen_tester_1", "username": "tester", "role": "admin", "tier": "teacher_pro"}
    try:
        ai._structured_response = lambda sys, prompt, schema: {
            "type": "single_choice",
            "question": "2+2=?",
            "options": ["A. 3", "B. 4"],
            "answer": "B",
            "explanation": "2+2=4",
            "source_pages": [1],
            "difficulty": "medium",
        }

        # 1. Regenerate single question
        res_regen = client.post(
            f"/api/quiz/{sheet.id}/questions/0/regenerate",
            json={"instruction": "換更難的題目"},
        )
        assert res_regen.status_code == 200
        assert res_regen.json()["question"]["question"] == "2+2=?"
        assert store.quizzes[sheet.id].questions[0].question == "2+2=?"

        # 2. PATCH manual edits
        res_patch = client.patch(
            f"/api/quiz/{sheet.id}",
            json={"title": "手動修改試卷標題"},
        )
        assert res_patch.status_code == 200
        assert store.quizzes[sheet.id].title == "手動修改試卷標題"
    finally:
        app.dependency_overrides.clear()


def test_handout_patch():
    client = TestClient(app)
    from fastapi_auth_lite import get_current_user
    from app.main import store
    from app.models import Handout, HandoutSection

    handout = Handout(
        id="handout-patch-test",
        document_id="doc-patch-test",
        title="原始講義",
        subtitle="副標題",
        overview="總覽",
        sections=[
            HandoutSection(
                title="第一章",
                summary="摘要",
                key_points=["要點1"],
                discussion_questions=["問題1"],
                source_pages=[1],
            )
        ],
        key_takeaways=["重點"],
    )
    store.handouts[handout.id] = handout

    app.dependency_overrides[get_current_user] = lambda: {"id": "handout_patch_tester", "username": "tester", "role": "admin", "tier": "teacher_pro"}
    try:
        res_patch = client.patch(
            f"/api/handouts/{handout.id}",
            json={"title": "手動修改後的講義標題", "overview": "手動修改總覽"},
        )
        assert res_patch.status_code == 200
        assert store.handouts[handout.id].title == "手動修改後的講義標題"
        assert store.handouts[handout.id].overview == "手動修改總覽"
    finally:
        app.dependency_overrides.clear()


def test_docx_and_print_endpoints():
    client = TestClient(app)
    from fastapi_auth_lite import get_current_user
    from app.main import store
    from app.models import Handout, HandoutSection, QuizSheet, QuizQuestion, Deck, Slide

    # 1. Handout setup
    handout = Handout(
        id="h_api_docx",
        document_id="doc_api",
        title="API測試講義",
        subtitle="副標題",
        overview="總覽",
        sections=[HandoutSection(title="章節1", summary="摘要1", key_points=["點1"], discussion_questions=["問1"])],
        key_takeaways=["總結1"],
    )
    store.handouts[handout.id] = handout

    # 2. Quiz setup
    quiz = QuizSheet(
        id="q_api_docx",
        document_id="doc_api",
        title="API測試試卷",
        description="描述",
        questions=[
            QuizQuestion(
                id="q1",
                type="single_choice",
                question="測試問題？",
                options=["A", "B"],
                answer="A",
                explanation="詳解",
            )
        ],
    )
    store.quizzes[quiz.id] = quiz

    app.dependency_overrides[get_current_user] = lambda: {"id": "docx_tester", "username": "tester", "role": "admin", "tier": "teacher_pro"}
    try:
        # Test Handout DOCX
        res_h_docx = client.get(f"/api/handouts/{handout.id}/docx")
        assert res_h_docx.status_code == 200
        assert "officedocument.wordprocessingml.document" in res_h_docx.headers["Content-Type"]
        assert len(res_h_docx.content) > 1000

        # Test Quiz DOCX (student & teacher)
        res_q_docx_student = client.get(f"/api/quiz/{quiz.id}/docx?teacher=false")
        assert res_q_docx_student.status_code == 200
        assert "quiz-student" in res_q_docx_student.headers["Content-Disposition"]

        res_q_docx_teacher = client.get(f"/api/quiz/{quiz.id}/docx?teacher=true")
        assert res_q_docx_teacher.status_code == 200
        assert "quiz-teacher" in res_q_docx_teacher.headers["Content-Disposition"]

        # Test Quiz Print/HTML
        res_q_html = client.get(f"/api/quiz/{quiz.id}/print?teacher=true")
        assert res_q_html.status_code == 200
        assert "text/html" in res_q_html.headers["Content-Type"]
        assert "教師詳解卷" in res_q_html.text

        # Test Deck DOCX
        deck = Deck(
            id="deck_api_docx_1",
            document_id="doc_1",
            title="簡報測試",
            subtitle="高中生｜20分鐘",
            duration=20,
            mode="gemini",
            slides=[Slide(title="第一頁", bullets=["重點一"], speaker_notes="講稿內容", source_pages=[1])],
        )
        store.decks[deck.id] = deck
        res_deck_docx = client.get(f"/api/decks/{deck.id}/docx")
        assert res_deck_docx.status_code == 200
        assert "officedocument.wordprocessingml.document" in res_deck_docx.headers["Content-Type"]
        assert f"deck-notes-{deck.id}.docx" in res_deck_docx.headers["Content-Disposition"]
        assert len(res_deck_docx.content) > 1000
    finally:
        app.dependency_overrides.clear()


def test_patch_sync_endpoints():
    client = TestClient(app)
    from app.main import store
    from app.models import Deck, Slide, Handout, HandoutSection, QuizSheet, QuizQuestion

    # 1. Test Deck PATCH and Export sync
    deck = Deck(
        id="deck_patch_sync_1",
        document_id="doc_sync_1",
        title="原始簡報標題",
        subtitle="原始副標題",
        duration=30,
        mode="gemini",
        slides=[
            Slide(title="原始第一頁", bullets=["原始重點 A"], speaker_notes="原始講稿", visual_diagram={"steps": [{"label": "① 原始", "text": "原始說明"}]})
        ],
    )
    store.decks[deck.id] = deck

    res_patch_deck = client.patch(
        f"/api/decks/{deck.id}",
        json={
            "title": "修改後簡報標題",
            "slides": [
                {
                    "title": "修改後第一頁",
                    "bullets": ["修改後重點 1", "新增重點 2"],
                    "speaker_notes": "修改後的逐頁講稿",
                    "visual_diagram": {"steps": [{"label": "① 核心機制", "text": "更新後的推導"}], "takeaway": "核心結論"},
                }
            ],
        },
    )
    assert res_patch_deck.status_code == 200
    updated_deck = store.decks[deck.id]
    assert updated_deck.title == "修改後簡報標題"
    assert updated_deck.slides[0].title == "修改後第一頁"
    assert updated_deck.slides[0].bullets == ["修改後重點 1", "新增重點 2"]
    assert updated_deck.slides[0].speaker_notes == "修改後的逐頁講稿"

    # Test PPTX and PDF export with updated content
    res_pptx = client.get(f"/api/decks/{deck.id}/pptx")
    assert res_pptx.status_code == 200
    assert len(res_pptx.content) > 0

    res_pdf = client.get(f"/api/decks/{deck.id}/pdf")
    assert res_pdf.status_code == 200
    assert "修改後第一頁" in res_pdf.text

    # 2. Test Handout PATCH
    handout = Handout(
        id="handout_patch_sync_1",
        document_id="doc_sync_1",
        title="原始講義標題",
        subtitle="原始副標題",
        overview="原始課程總覽",
        sections=[HandoutSection(title="原始章節", summary="原始導讀", key_points=["原始要點"])],
    )
    store.handouts[handout.id] = handout

    res_patch_handout = client.patch(
        f"/api/handouts/{handout.id}",
        json={
            "title": "修改後講義標題",
            "sections": [{"title": "修改後章節", "summary": "修改後導讀", "key_points": ["最新要點 100"]}],
        },
    )
    assert res_patch_handout.status_code == 200
    assert store.handouts[handout.id].title == "修改後講義標題"
    assert store.handouts[handout.id].sections[0].title == "修改後章節"

    # 3. Test Quiz PATCH
    quiz = QuizSheet(
        id="quiz_patch_sync_1",
        document_id="doc_sync_1",
        title="原始試卷標題",
        description="原始試卷說明",
        questions=[QuizQuestion(id="q1", type="single_choice", question="原始題目？", options=["A", "B"], answer="A", explanation="原始解析")],
    )
    store.quizzes[quiz.id] = quiz

    res_patch_quiz = client.patch(
        f"/api/quiz/{quiz.id}",
        json={
            "title": "修改後試卷標題",
            "questions": [{"id": "q1", "type": "single_choice", "question": "修改後題目？", "options": ["A", "B", "C"], "answer": "B", "explanation": "修改後解析"}],
        },
    )
    assert res_patch_quiz.status_code == 200
    assert store.quizzes[quiz.id].title == "修改後試卷標題"
    assert store.quizzes[quiz.id].questions[0].question == "修改後題目？"
    assert store.quizzes[quiz.id].questions[0].answer == "B"








