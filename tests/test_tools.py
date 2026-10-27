import asyncio
import socket

import httpx
import pytest

from app.agents.executor import RetrievalExecutor
from app.core.config import Settings
from app.core.security import canonicalize, in_scope, URLGuard, UnsafeURL
from app.evaluation.schemas import Page, CandidateClaim, Draft
from app.llm.factory import LLMRouter
from app.tools.http_browser import HTTPBrowser
from app.tools.tinyfish import TinyFish
from tests.support import FixtureGuard


def config(**kwargs):
    return Settings(_env_file=None, provider_min_interval_s=0, **kwargs)


class Guard(FixtureGuard):
    async def resolve(self, url):
        return canonicalize(url), "93.184.216.34"


@pytest.mark.parametrize("url", ["http://127.0.0.1", "http://[::1]/", "http://169.254.169.254/",
    "http://10.1.1.1/", "http://localhost/", "ftp://example.org", "https://user:pass@example.org",
    "http://example.org:22", "https://a.internal", "https://example.org\\@127.0.0.1"])
def test_unsafe_url_blocked(url):
    with pytest.raises(UnsafeURL):
        canonicalize(url)


def test_url_canonicalization():
    assert canonicalize("https://EXAMPLE.org:443/path?b=2&utm_source=x&a=1#top") == "https://example.org/path?a=1&b=2"
    assert in_scope("https://docs.example.org/", ["example.org"])
    assert not in_scope("https://evil-example.org/", ["example.org"])


async def test_dns_private_resolution_blocked(monkeypatch):
    async def resolve(*args, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.1", 443))]
    monkeypatch.setattr(asyncio.get_running_loop(), "getaddrinfo", resolve)
    with pytest.raises(UnsafeURL):
        await URLGuard().validate("https://public-looking.org/")


async def test_redirect_validates_every_hop():
    calls = []

    class RedirectGuard(Guard):
        async def resolve(self, url):
            calls.append(url)
            return await super().resolve(url)

    def handler(request):
        if request.url.path == "/":
            return httpx.Response(302, headers={"location": "/policy"})
        return httpx.Response(200, text="<p>Refund policy 30 days.</p>", headers={"content-type": "text/html"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await HTTPBrowser(client, RedirectGuard(), config()).retrieve("https://example.org/")
    assert result.url == "https://example.org/policy"
    assert calls == ["https://example.org/", "https://example.org/policy"]


async def test_redirect_to_private_ip_rejected():
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda req: httpx.Response(302,
        headers={"location": "http://127.0.0.1/secrets"}))) as client:
        with pytest.raises(UnsafeURL):
            await HTTPBrowser(client, Guard(), config()).retrieve("https://example.org/")


async def test_http_pins_ip_and_preserves_host_and_sni():
    def handler(req):
        assert req.url.host == "93.184.216.34"
        assert req.headers["host"] == "example.org"
        assert req.extensions["sni_hostname"] == "example.org"
        return httpx.Response(200, text="<p>Original content.</p>", headers={"content-type": "text/html"})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await HTTPBrowser(client, Guard(), config()).retrieve("https://example.org/")
    assert result.url == "https://example.org/"


async def test_oversized_http_page_rejected():
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda req: httpx.Response(200,
        text="a" * 2000, headers={"content-type": "text/html"}))) as client:
        with pytest.raises(ValueError, match="byte budget"):
            await HTTPBrowser(client, Guard(), config(max_response_bytes=1000)).retrieve("https://example.org/")


class StubBrowser:
    def __init__(self, fail=False, kind="page_text", provider="stub"):
        self.fail, self.kind, self.provider, self.calls = fail, kind, provider, 0

    async def retrieve(self, url, objective=""):
        self.calls += 1
        if self.fail:
            raise ValueError("Failure")
        return Page(url=url, content="Refund policy allows 30 days.", provider=self.provider, evidence_kind=self.kind)


async def test_tinyfish_failure_falls_back_static():
    static, tiny = StubBrowser(provider="httpx"), StubBrowser(fail=True)
    result = await RetrievalExecutor(static, tinyfish=tiny, settings=config()).retrieve("https://example.org/", "Refund")
    assert result.provider == "httpx" and tiny.calls == 1


async def test_browser_required_fallback_uses_playwright():
    static, tiny, browser = StubBrowser(), StubBrowser(fail=True), StubBrowser(provider="playwright")
    result = await RetrievalExecutor(static, tiny, browser, config()).retrieve("https://example.org/", "Refund", True)
    assert result.provider == "playwright" and static.calls == 0


async def test_cache_disabled_by_default_and_bounded_when_enabled():
    static = StubBrowser()
    executor = RetrievalExecutor(static, settings=config(cache_ttl_s=10, cache_entries=1))
    await executor.retrieve("https://example.org/", "Refund")
    await executor.retrieve("https://example.org/", "Refund")
    assert static.calls == 1
    await executor.retrieve("https://example.org/second", "Refund")
    assert len(executor.cache) == 1


async def test_tinyfish_fetch_preserves_actual_final_url():
    def handler(req):
        assert req.headers["X-API-Key"] == "fixture-key"
        return httpx.Response(200, json={"results": [{"url": "https://example.org/", "final_url": "https://example.org/about",
            "title": "About", "text": "<p>Founder Ada.</p>", "links": ["https://example.org/team"]}]})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await TinyFish(client, FixtureGuard(), config(tinyfish_api_key="fixture-key")).retrieve("https://example.org/")
    assert result.url.endswith("/about") and result.links[0].url.endswith("/team")


async def test_tinyfish_async_browser_polling_marks_agent_output():
    def handler(req):
        if req.url.path.endswith("run-async"):
            return httpx.Response(200, json={"run_id": "run-123"})
        return httpx.Response(200, json={"status": "COMPLETED", "result": {"content": "Founder Ada.", "url": "https://example.org/"}})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await TinyFish(client, FixtureGuard(), config(tinyfish_api_key="fixture-key")).browse("https://example.org/", "Find founder")
    assert result.evidence_kind == "agent_output"


async def test_tinyfish_timed_out_run_cancelled():
    calls = []
    def handler(req):
        calls.append(req.url.path)
        return httpx.Response(200, json={"run_id": "run-123", "status": "RUNNING"})
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(TimeoutError):
            await TinyFish(client, FixtureGuard(), config(tinyfish_api_key="fixture-key", request_timeout_s=.05)).browse("https://example.org/", "Find founder")
    assert any(path.endswith("/cancel") for path in calls)


class FakeModel:
    def __init__(self, error=None):
        self.error = error

    def with_structured_output(self, schema, **kwargs):
        return self

    async def ainvoke(self, messages):
        if self.error:
            raise self.error
        return Draft(claims=[CandidateClaim(text="Ada", evidence_id="e1", quote="Founder Ada.")])


class RateLimit(Exception):
    status_code = 429


async def test_llm_rate_limit_falls_back_without_paid_model():
    settings = config(gemini_api_key="fake", gemini_free_tier_confirmed=True,
                      openrouter_api_key="fake", openrouter_model="openrouter/free", llm_retry_limit=0,
                      provider_priority="gemini,openrouter,nvidia")
    async with httpx.AsyncClient() as client:
        router = LLMRouter(settings, client, builders={"gemini": lambda m: FakeModel(RateLimit()),
                                                     "openrouter": lambda m: FakeModel()})
        draft, provider, model, failures = await router.extract("Founder?", [])
    assert provider == "openrouter" and model == "openrouter/free" and failures
    assert draft.claims[0].text == "Ada"


def test_paid_model_and_unconfirmed_tier_disabled():
    router = LLMRouter(config(openrouter_api_key="fake", openrouter_model="paid/model",
                             gemini_api_key="fake", nvidia_api_key="fake", nvidia_model="example/model"), None)
    assert router.candidates() == []


async def test_model_catalog_nonzero_price_rejected():
    model = "vendor/model:free"
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda req: httpx.Response(200,
        json={"data": [{"id": model, "pricing": {"prompt": "1", "completion": "0"}}]}))) as client:
        router = LLMRouter(config(openrouter_api_key="fake", openrouter_model=model), client)
        with pytest.raises(ValueError, match="zero cost"):
            await router.check_available("openrouter", model)


async def test_no_llm_credentials_reports_missing():
    settings = config(llm_provider="none")
    draft, provider, model, failures = await LLMRouter(settings, None).extract("Founder?", [])
    assert not draft.claims and provider is None and "No eligible" in failures[0]
