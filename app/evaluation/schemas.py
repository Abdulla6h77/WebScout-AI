from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Query(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    starting_url: str | None = Field(None, max_length=2048)
    allowed_domains: list[str] = Field(default_factory=list, max_length=10)
    browser_required: bool = False
    exact_answer: bool = False

    @field_validator("question")
    @classmethod
    def not_blank(cls, value):
        if len(value.strip()) < 3:
            raise ValueError("Question must contain at least three non-space characters")
        return value.strip()


class Link(BaseModel):
    url: str
    text: str = ""


class Page(BaseModel):
    url: str
    title: str = ""
    content: str = ""
    provider: str
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    published_at: str | None = None
    links: list[Link] = Field(default_factory=list)
    tables: list[list[list[str]]] = Field(default_factory=list)
    structured: list[dict] = Field(default_factory=list)
    evidence_kind: Literal["page_text", "agent_output"] = "page_text"
    status: Literal["success", "failed"] = "success"


class Evidence(BaseModel):
    id: str
    url: str
    title: str
    passage: str
    provider: str
    score: float
    retrieved_at: datetime
    published_at: str | None = None


class CandidateClaim(BaseModel):
    text: str = Field(min_length=1, max_length=1200)
    evidence_id: str
    quote: str = Field(min_length=1, max_length=2000)
    relation: Literal["direct", "inference"] = "direct"


class Draft(BaseModel):
    claims: list[CandidateClaim] = Field(default_factory=list, max_length=6)
    contradictions: list[str] = Field(default_factory=list, max_length=6)


class Citation(BaseModel):
    url: str
    title: str
    supporting_text: str
    claim: str
    evidence_id: str
    retrieved_at: datetime
    published_at: str | None = None


class Answer(BaseModel):
    question: str
    answer: str = ""
    status: Literal["answered", "insufficient_evidence", "retrieval_failed", "timeout", "invalid_request"]
    citations: list[Citation] = Field(default_factory=list)
    execution_time_ms: float = 0
    retrieval_provider: str | None = None
    model_provider: str | None = None
    model: str | None = None
    warnings: list[str] = Field(default_factory=list)
    trace: list[dict] = Field(default_factory=list)
