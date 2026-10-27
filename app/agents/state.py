from typing import TypedDict

from app.evaluation.schemas import Query, Page, Evidence, Draft, Citation


class AgentState(TypedDict, total=False):
    query: Query
    domains: list[str]
    search_queries: list[str]
    queue: list[tuple[str, int]]
    visited: list[str]
    pages: list[Page]
    evidence: list[Evidence]
    draft: Draft
    claims: list[str]
    citations: list[Citation]
    attempt: int
    warnings: list[str]
    trace: list[dict]
    model_provider: str | None
    model: str | None
    retrieval_failures: int
