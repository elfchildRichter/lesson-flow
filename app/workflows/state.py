from __future__ import annotations

from typing import Any, Optional, TypedDict
from app.models import Chunk, Deck, Document, Source


class QAState(TypedDict, total=False):
    question: str
    document: Document
    retrieved_chunks: list[tuple[Chunk, float]]
    web_results: str
    enable_web_search: bool
    is_relevant: bool
    answer: str
    sources: list[Source]
    ai_service: Any
    is_hallucinated: bool
    hallucination_retry: int
    hallucination_feedback: str
    history: list[dict]


class DeckState(TypedDict, total=False):
    document: Document
    audience: str
    tone: str
    language: str
    slide_count: int
    duration: int
    enable_web_search: bool
    ai_service: Any
    outline: dict
    web_results: str
    raw_slides: list[dict]
    is_quality_passed: bool
    retry_count: int
    audit_feedback: str
    handout_text: Optional[str]
    deck: Optional[Deck]


