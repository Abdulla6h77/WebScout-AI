"""Bounded diagnostics; provider payloads are reduced and credentials redacted."""
import asyncio
import json
import re
from pathlib import Path

import httpx
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import Settings
from app.evaluation.schemas import Draft
from app.llm.factory import LLMRouter, SYSTEM


def safe(value, settings):
    text = str(value)
    for provider in ("gemini", "openrouter", "nvidia", "tinyfish"):
        secret = settings.key(provider)
        if secret:
            text = text.replace(secret, "[REDACTED]")
    text = re.sub(r"AIza[\w-]+|sk-[\w-]+", "[REDACTED]", text)
    text = re.sub(r"(?i)(key|token|authorization)=([^\s&]+)", r"\1=[REDACTED]", text)
    return text[:1600]


async def main():
    s = Settings(llm_retry_limit=0)
    result = {"config": {k: getattr(s, k) for k in ("gemini_model", "openrouter_model", "max_output_tokens", "request_timeout_s")}}
    async with httpx.AsyncClient(trust_env=False, timeout=30) as client:
        for provider, endpoint, headers in (
            ("gemini", "https://generativelanguage.googleapis.com/v1beta/models", {"x-goog-api-key": s.key("gemini")}),
            ("openrouter", "https://openrouter.ai/api/v1/models", {})):
            r = await client.get(endpoint, headers=headers)
            data = r.json()
            if provider == "gemini":
                result["gemini_catalog"] = {"http_status": r.status_code, "models": [x["name"] for x in data.get("models", [])],
                                             "error": safe(data.get("error", ""), s)}
            else:
                result["free_catalog"] = [{"id": x["id"], "parameters": x.get("supported_parameters", []),
                    "context_length": x.get("context_length"), "pricing": x.get("pricing")}
                    for x in data.get("data", []) if x["id"].endswith(":free") and
                    all(float(x.get("pricing", {}).get(k, 1)) == 0 for k in ("prompt", "completion"))]
        router = LLMRouter(s, client)
        for provider, model in router.candidates():
            try:
                llm = router.build(provider, model).with_structured_output(Draft, method="json_schema", include_raw=True)
                async with asyncio.timeout(32):
                    response = await llm.ainvoke([SystemMessage(content=SYSTEM), HumanMessage(content=json.dumps({
                        "question": "What is this domain used for?", "untrusted_evidence": [
                            {"id": "e1", "passage": "This domain is for use in documentation examples without needing permission."}]}))])
                raw = response.get("raw")
                result[provider] = {"status": "returned", "metadata": raw.response_metadata if raw else {},
                    "usage": raw.usage_metadata if raw else {}, "parsed": response["parsed"].model_dump() if response.get("parsed") else None,
                    "parse_error": safe(response.get("parsing_error"), s)}
            except Exception as exc:
                chain, seen = [], set()
                current = exc
                while current and id(current) not in seen:
                    seen.add(id(current))
                    chain.append({"type": type(current).__name__, "status": getattr(current, "status_code", None),
                                  "code": safe(getattr(current, "code", None), s), "message": safe(current, s)})
                    current = current.__cause__ or current.__context__
                completion = getattr(exc, "completion", None)
                result[provider] = {"status": "failed", "chain": chain}
                if completion:
                    result[provider]["completion"] = {"model": completion.model, "usage": completion.usage.model_dump() if completion.usage else {},
                        "finish_reasons": [x.finish_reason for x in completion.choices]}
    output = json.dumps(result, indent=2, default=str)
    # Redact the entire artifact too, including SDK metadata.
    for provider in ("gemini", "openrouter", "nvidia", "tinyfish"):
        if s.key(provider):
            output = output.replace(s.key(provider), "[REDACTED]")
    Path("artifacts/llm-diagnosis.json").write_text(output, encoding="utf-8")
    print(output)


if __name__ == "__main__":
    asyncio.run(main())
