import pytest
from app.models import AskRequest, Chunk, Document
from app.services import AIService
from app.workflows.handlers.common import _format_history
from app.workflows.qa_graph import generate_answer_node, retrieve_node
from app.workflows.state import QAState


def test_format_history():
    history = [
        {"role": "user", "content": "什麼是光合作用？"},
        {"role": "assistant", "content": "光合作用是植物利用光能合成有機物的過程。"},
    ]
    formatted = _format_history(history)
    assert "【前情提要 / 歷史對話紀錄】" in formatted
    assert "[使用者 (User)]: 什麼是光合作用？" in formatted
    assert "[AI 助手 (Assistant)]: 光合作用是植物利用光能合成有機物的過程。" in formatted


def test_qa_graph_with_history():
    doc = Document(
        id="doc_history_test",
        name="Biology",
        pages=1,
        chunks=[Chunk(text="光合作用包含光反應與卡爾文循環。", page=1, index=0)],
        size_bytes=100,
    )

    class MockAI:
        provider = "gemini"
        def retrieve(self, document, query):
            return [(doc.chunks[0], 0.95)]

        def _text_response(self, system_prompt, user_prompt):
            assert "光反應" in user_prompt or "第二點" in user_prompt
            assert "【前情提要 / 歷史對話紀錄】" in user_prompt
            return "第二點是指卡爾文循環（第 1 頁）。"

    mock_ai = MockAI()
    history = [
        {"role": "user", "content": "光合作用有哪兩個階段？"},
        {"role": "assistant", "content": "包含光反應與卡爾文循環。"},
    ]

    state = QAState(
        question="第二點詳細說明",
        document=doc,
        history=history,
        ai_service=mock_ai,
        retrieved_chunks=[(doc.chunks[0], 0.95)],
    )

    res = generate_answer_node(state)
    assert "卡爾文循環" in res["answer"]
    assert len(res["sources"]) == 1
    assert res["sources"][0].page == 1
