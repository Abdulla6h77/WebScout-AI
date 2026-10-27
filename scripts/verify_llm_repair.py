"""Live provider regression probe, with actual retrieved evidence and no raw exception logs."""
import argparse
import asyncio
import json
import time
from pathlib import Path

import httpx

from app.core.config import Settings
from app.evaluation.schemas import Query
from app.agents.verifier import verify
from app.main import build_engine
from app.retrieval.evidence import collect_evidence
from app.llm.factory import SYSTEM, failure_details


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["direct", "end-to-end", "openrouter-baseline"])
    parser.add_argument("--provider", choices=["gemini", "openrouter"])
    parser.add_argument("--model")
    args = parser.parse_args()
    s = Settings(llm_retry_limit=0)
    if args.provider:
        updates = {"llm_provider": args.provider}
        if args.model:
            updates[args.provider + "_model"] = args.model
        s = s.model_copy(update=updates)
    result = {"mode": args.mode}
    async with httpx.AsyncClient(trust_env=False, timeout=35) as client:
        engine = build_engine(s, client)
        if args.mode == "openrouter-baseline":
            # Raw request preserves model/usage even when SDK schema parsing raises a length exception.
            r = await client.post("https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {s.key('openrouter')}"}, json={
                    "model": "openrouter/free", "max_tokens": 1000, "temperature": 0,
                    "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content":
                        'Question: What is this domain used for? Passage ID e1: This domain is for use in documentation examples without needing permission.'}],
                    "response_format": {"type": "json_object"}})
            result["http_status"] = r.status_code
            data = r.json()
            result.update({"selected_model": data.get("model"), "usage": data.get("usage"),
                           "finish_reasons": [c.get("finish_reason") for c in data.get("choices", [])],
                           "visible_characters": [len(c.get("message", {}).get("content") or "") for c in data.get("choices", [])]})
        elif args.mode == "direct":
            page = await engine.executor.retrieve("https://example.com/", "What is this domain used for?")
            evidence = collect_evidence("What is this domain used for?", [page])
            result["retrieved_page"] = page.model_dump(mode="json")
            result["evidence"] = [e.model_dump(mode="json") for e in evidence]
            for provider, _ in engine.llm.candidates():
                engine.llm.settings = s.model_copy(update={"llm_provider": provider})
                start = time.perf_counter()
                draft, name, model, failures = await engine.llm.extract("What is this domain used for?", evidence)
                claims, citations, warnings = verify(draft, evidence, "What is this domain used for?")
                result[provider] = {"provider": name, "model": model, "draft": draft.model_dump(),
                    "verified_claims": claims, "citations": [c.model_dump(mode="json") for c in citations],
                    "failures": failures, "warnings": warnings, "latency_ms": round((time.perf_counter()-start)*1000, 2)}
            result["diagnostics"] = list(engine.llm.diagnostics)
        else:
            answer = await engine.answer(Query(question="What is this domain used for?", starting_url="https://example.com/"))
            result["response"] = answer.model_dump(mode="json")
            result["diagnostics"] = list(engine.llm.diagnostics)
            result["citations_rechecked"] = []
            for citation in answer.citations:
                page = await engine.executor.retrieve(citation.url, "Independently verify quotation")
                # Passages join adjacent lines with spaces, preserving original words.
                result["citations_rechecked"].append({"url": citation.url,
                    "quote_found": " ".join(citation.supporting_text.split()) in " ".join(page.content.split()),
                    "claim_found": citation.claim in citation.supporting_text, "provider": page.provider})
    suffix = "-" + args.provider if args.provider else ""
    Path(f"artifacts/repair-{args.mode}{suffix}.json").write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print(json.dumps(failure_details(exc)))
        raise SystemExit(1)
