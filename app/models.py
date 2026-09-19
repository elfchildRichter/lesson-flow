from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ProviderRequest(BaseModel):
    provider: Literal["openai", "gemini", "ollama", "ollama_cloud", "ollama_local"]



@dataclass
class Chunk:
    text: str
    page: int
    index: int


@dataclass
class Document:
    id: str
    name: str
    pages: int
    chunks: list[Chunk]
    size_bytes: int
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    vectors: Optional[list[list[float]]] = None


class Source(BaseModel):
    page: int
    excerpt: str
    score: float = Field(ge=0, le=1)


class AskRequest(BaseModel):
    document_id: str
    question: str = Field(min_length=2, max_length=1000)
    enable_web_search: bool = Field(default=False)
    history: Optional[list[dict]] = Field(default_factory=list)


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
    mode: str


class GenerateRequest(BaseModel):
    document_id: str
    audience: str = Field(default="大學生", max_length=50)
    tone: str = Field(default="清楚易懂", max_length=50)
    language: Literal["zh-TW", "en", "auto"] = Field(default="zh-TW")
    slide_count: int = Field(default=8, ge=4, le=20)
    duration: int = Field(default=30, ge=10, le=180)
    enable_web_search: bool = Field(default=False)
    handout_text: Optional[str] = Field(default=None, description="可選之講義母本文本，作為生成教學骨幹依據")


class Slide(BaseModel):
    title: str
    bullets: list[str] = Field(min_length=1, max_length=6)
    speaker_notes: str
    source_pages: list[int] = Field(default_factory=list)
    icon: str = Field(default="💡")
    visual_description: str = Field(default="")
    visual_diagram: Optional[dict] = Field(default_factory=dict)


class Deck(BaseModel):
    id: str
    document_id: str
    title: str
    subtitle: str
    slides: list[Slide]
    duration: int
    mode: str


class QuizQuestion(BaseModel):
    id: str
    type: Literal["single_choice", "multiple_choice", "problem_solving"] = "single_choice"
    question: str
    options: list[str] = Field(default_factory=list)
    answer: str
    explanation: str
    source_pages: list[int] = Field(default_factory=list)
    difficulty: Literal["easy", "medium", "hard"] = "medium"


class QuizSheet(BaseModel):
    id: str
    document_id: str
    title: str
    description: str
    questions: list[QuizQuestion]
    duration_minutes: int = 15
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class QuizGenerateRequest(BaseModel):
    document_id: str
    question_count: int = Field(default=5, ge=1, le=20)
    difficulty: Literal["easy", "medium", "hard", "all"] = Field(default="all")
    audience: str = Field(default="大學生", max_length=50)
    tone: str = Field(default="清楚易懂", max_length=50)
    enable_web_search: bool = Field(default=False)
    language: Literal["zh-TW", "en", "auto"] = Field(default="zh-TW")
    handout_text: Optional[str] = Field(default=None, description="可選之講義母本文本，作為出題考點依據")


class HandoutSection(BaseModel):
    title: str
    summary: str
    key_points: list[str] = Field(default_factory=list)
    discussion_questions: list[str] = Field(default_factory=list)
    source_pages: list[int] = Field(default_factory=list)


class Handout(BaseModel):
    id: str
    document_id: str
    title: str
    subtitle: str
    overview: str
    sections: list[HandoutSection]
    key_takeaways: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HandoutGenerateRequest(BaseModel):
    document_id: str
    target_audience: str = Field(default="大學生", max_length=50)
    audience: Optional[str] = Field(default=None, max_length=50)
    tone: str = Field(default="清楚易懂", max_length=50)
    detail_level: Literal["concise", "standard", "detailed"] = Field(default="standard")
    language: Literal["zh-TW", "en", "auto"] = Field(default="zh-TW")
    enable_web_search: bool = Field(default=False)

