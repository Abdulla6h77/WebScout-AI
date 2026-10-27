import asyncio

from app.agents.graph import WebScout
from app.core.config import Settings
from app.core.security import canonicalize
from app.evaluation.schemas import CandidateClaim, Draft, Link, Page
from app.tools.extractor import extract_html


class FixtureGuard:
    async def validate(self, url):
        return canonicalize(url)


class FixtureExecutor:
    def __init__(self, pages, delay=0):
        self.pages, self.delay, self.calls = pages, delay, []

    async def retrieve(self, url, objective, browser_required=False, domains=None):
        self.calls.append((url, browser_required))
        await asyncio.sleep(self.delay)
        if url not in self.pages:
            raise ValueError("Fixture missing")
        value = self.pages[url]
        if isinstance(value, Page):
            return value
        return extract_html(value, url, "fixture")


class FixtureSearch:
    def __init__(self, urls):
        self.urls = urls

    async def discover(self, query, domains, page=0):
        return [Link(url=u) for u in self.urls]


class FixtureLLM:
    """Oracle for plumbing tests only. This is not an actual language model."""
    def __init__(self, answer=None, contradiction=False, hallucinate=False):
        self.answer, self.contradiction, self.hallucinate = answer, contradiction, hallucinate

    async def extract(self, question, evidence, exact=False):
        if self.contradiction:
            return Draft(contradictions=["Sources disagree"]), "fixture", "oracle", []
        for e in evidence:
            if self.answer and self.answer in e.passage:
                return Draft(claims=[CandidateClaim(text=self.answer,
                    evidence_id=e.id, quote="Invented quote" if self.hallucinate else e.passage)]), "fixture", "oracle", []
        return Draft(), "fixture", "oracle", []


def engine(pages, answer=None, urls=None, delay=0, **kwargs):
    settings = Settings(_env_file=None, llm_provider="none", provider_min_interval_s=0, **kwargs)
    executor = FixtureExecutor(pages, delay)
    scout = WebScout(settings, executor, FixtureSearch(urls if urls is not None else list(pages)),
                     FixtureLLM(answer), FixtureGuard())
    return scout
