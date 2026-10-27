"""Explicit, bounded live probe. Never prints keys or raw provider exceptions."""
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

import httpx

from app.core.config import Settings
from app.evaluation.schemas import Query
from app.main import build_engine


async def main():
    settings = Settings(llm_retry_limit=0, max_attempts=1, time_budget_s=30, request_timeout_s=15)
    results = {"timestamp": datetime.now(timezone.utc).isoformat(), "kind": "live", "checks": {}}
    async with httpx.AsyncClient(trust_env=False) as client:
        engine = build_engine(settings, client)
        try:
            page = await engine.executor.http.retrieve("https://example.com/")
            results["checks"]["httpx"] = {"status": "passed", "url": page.url, "chars": len(page.content)}
        except Exception as exc:
            results["checks"]["httpx"] = {"status": "failed", "error_type": type(exc).__name__}
        # One actual zero-cost routed LLM answer; no paid fallback is eligible.
        if engine.llm.candidates():
            try:
                answer = await engine.answer(Query(question="What is this domain used for?", starting_url="https://example.com/"))
                results["checks"]["end_to_end"] = answer.model_dump(mode="json")
            except Exception as exc:
                results["checks"]["end_to_end"] = {"status": "failed", "error_type": type(exc).__name__}
        else:
            results["checks"]["end_to_end"] = {"status": "skipped", "reason": "No eligible LLM credentials"}
        if engine.executor.tinyfish:
            try:
                page = await engine.executor.tinyfish.retrieve("https://example.com/")
                results["checks"]["tinyfish_fetch"] = {"status": "passed", "url": page.url, "chars": len(page.content)}
            except Exception as exc:
                results["checks"]["tinyfish_fetch"] = {"status": "failed", "error_type": type(exc).__name__}
        else:
            results["checks"]["tinyfish_fetch"] = {"status": "skipped", "reason": "TINYFISH_API_KEY missing"}
        results["checks"]["tinyfish_agent"] = {"status": "skipped", "reason": "Remote browser run needs credential and quota validation"}
        results["checks"]["playwright"] = {"status": "skipped", "reason": "Run separate local browser integration test"}
    path = Path("artifacts/live-probe.json")
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
