import json
from types import SimpleNamespace

import httpx
from langchain_core.messages import AIMessage

from app.core.config import Settings
from app.evaluation.schemas import Draft, CandidateClaim
from app.llm.factory import LLMRouter, failure_details


def settings(**kwargs):
    return Settings(_env_file=None, provider_min_interval_s=0, **kwargs)


def test_google_nested_code_is_retryable_status_without_logging_message():
    class GoogleError(Exception):
        code = 503
    inner = GoogleError("credential=super-secret-key")
    outer = RuntimeError("wrapped secret")
    outer.__cause__ = inner
    details = failure_details(outer)
    assert details["status"] == 503 and details["code"] == "UNAVAILABLE"
    assert "secret" not in json.dumps(details)


def test_length_exception_keeps_actual_model_and_reasoning_usage():
    class LengthFinishReasonError(Exception):
        pass
    exc = LengthFinishReasonError("Don't log me")
    exc.completion = SimpleNamespace(model="reasoning-model:free", choices=[SimpleNamespace(finish_reason="length")],
        usage=SimpleNamespace(model_dump=lambda: {"completion_tokens": 1000, "completion_tokens_details": {"reasoning_tokens": 1000}}))
    details = failure_details(exc)
    assert details["selected_model"] == "reasoning-model:free"
    assert details["finish_reasons"] == ["length"]
    assert details["usage"]["completion_tokens_details"]["reasoning_tokens"] == 1000


def test_openrouter_disables_reasoning_and_keeps_budget():
    router = LLMRouter(settings(openrouter_api_key="fake"), None)
    model = router.build("openrouter", "nvidia/nemotron-3.5-super-vl:free")
    assert model.extra_body["reasoning"]["enabled"] is False
    assert model.max_tokens == 1000
    assert model.extra_body["provider"]["require_parameters"] is True


def test_gemini_replacement_uses_minimal_thinking():
    router = LLMRouter(settings(gemini_api_key="fake"), None)
    model = router.build("gemini", "gemini-3.5-flash-lite")
    assert model.thinking_level == "minimal"
    assert model.max_output_tokens == 1000


async def test_raw_structured_result_exposes_selected_model_and_short_payload():
    captured = {}
    draft = Draft(claims=[CandidateClaim(text="Ada", quote="Founder Ada.", evidence_id="e1")])

    class Fake:
        def with_structured_output(self, schema, **kwargs):
            assert kwargs["include_raw"] is True
            return self

        async def ainvoke(self, messages):
            captured["payload"] = json.loads(messages[-1].content)
            return {"raw": AIMessage(content="{}", response_metadata={"model_name": "actual-model:free", "finish_reason": "stop"}),
                    "parsed": draft, "parsing_error": None}

    evidence = SimpleNamespace(id="e1", passage="Founder Ada.")
    s = settings(llm_provider="openrouter", openrouter_api_key="fake")
    async with httpx.AsyncClient() as client:
        router = LLMRouter(s, client, builders={"openrouter": lambda model: Fake()})
        result, provider, model, failures = await router.extract("Founder?", [evidence])
    assert result == draft and model == "actual-model:free" and provider == "openrouter"
    assert captured["payload"]["untrusted_evidence"] == [{"id": "e1", "passage": "Founder Ada."}]
    assert not failures


async def test_google_code_503_retries_then_recovers():
    class GoogleAPIError(Exception):
        code = 503

    class Fake:
        calls = 0

        def with_structured_output(self, schema, **kwargs):
            return self

        async def ainvoke(self, messages):
            self.calls += 1
            if self.calls == 1:
                raise GoogleAPIError("key=secret")
            return Draft()

    fake = Fake()
    s = settings(llm_provider="gemini", gemini_api_key="fake", gemini_free_tier_confirmed=True, llm_retry_limit=1)
    router = LLMRouter(s, None, builders={"gemini": lambda model: fake})
    _, provider, _, failures = await router.extract("Founder?", [])
    assert provider == "gemini" and fake.calls == 2
    assert "HTTP 503" in failures[0] and "secret" not in str(router.diagnostics)


async def test_structured_parse_error_never_becomes_valid_answer():
    class Fake:
        def with_structured_output(self, schema, **kwargs):
            return self

        async def ainvoke(self, messages):
            return {"raw": AIMessage(content="truncated", response_metadata={"model_name": "actual:free", "finish_reason": "length"}),
                    "parsed": None, "parsing_error": ValueError("truncated")}

    router = LLMRouter(settings(llm_provider="openrouter", openrouter_api_key="fake"), None,
                       builders={"openrouter": lambda model: Fake()})
    draft, provider, _, failures = await router.extract("Founder?", [])
    assert not draft.claims and provider is None and failures
    assert router.diagnostics[0]["finish_reason"] == "length"


async def test_length_finish_rejected_even_when_partial_json_parses():
    class Fake:
        def with_structured_output(self, schema, **kwargs):
            return self

        async def ainvoke(self, messages):
            return {"raw": AIMessage(content="{}", response_metadata={"model_name": "actual:free", "finish_reason": "length"}),
                    "parsed": Draft(), "parsing_error": None}

    router = LLMRouter(settings(llm_provider="openrouter", openrouter_api_key="fake"), None,
                       builders={"openrouter": lambda model: Fake()})
    _, provider, _, failures = await router.extract("Founder?", [])
    assert provider is None and failures
