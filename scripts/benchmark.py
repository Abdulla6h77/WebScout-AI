"""Reproducible FIXTURE benchmark, not an external model accuracy evaluation."""
import asyncio
import json
import math
import statistics
from datetime import datetime, timezone
from pathlib import Path

from app.evaluation.schemas import Query
from tests.support import engine, FixtureLLM


async def main():
    cases = json.loads(Path("tests/fixtures/benchmark.json").read_text(encoding="utf-8"))
    records = []
    for case in cases:
        pages = {url: html for url, html in case["pages"].items()}
        scout = engine(pages, case.get("oracle_answer"), urls=case.get("urls"))
        if case.get("contradiction"):
            scout.llm = FixtureLLM(contradiction=True)
        query = Query(question=case["question"], starting_url=case.get("starting_url"))
        result = await scout.answer(query)
        answer_match = result.answer == case.get("expected_answer", "")
        status_match = result.status == case["expected_status"]
        valid = all(c.url in pages and c.claim in c.supporting_text for c in result.citations)
        from app.retrieval.evidence import collect_evidence
        from app.tools.extractor import extract_html
        evidence = collect_evidence(query.question, [extract_html(html, url, "fixture") for url, html in pages.items()])
        support = all(any(c.url == e.url and c.supporting_text == e.passage for e in evidence) for c in result.citations)
        records.append({"id": case["id"], "correct": answer_match and status_match,
            "citation_valid": valid, "evidence_support": support,
            "expected_abstention": case["expected_status"] != "answered", "abstained": result.status != "answered",
            "retrieved": bool(scout.executor.calls and result.retrieval_provider),
            "provider_failed": result.status == "retrieval_failed", "result": result.model_dump(mode="json")})
    times = sorted(r["result"]["execution_time_ms"] for r in records)
    answered = [r for r in records if r["result"]["status"] == "answered"]
    abstentions = [r for r in records if r["expected_abstention"]]
    summary = {"kind": "fixture_pipeline_with_oracle_model", "timestamp": datetime.now(timezone.utc).isoformat(),
        "warning": "Offline fixtures and an answer oracle measure pipeline behavior only; not live model or web accuracy.",
        "cases": len(records), "correct_cases": sum(r["correct"] for r in records),
        "answer_correctness": sum(r["correct"] for r in records) / len(records),
        "citation_validity_on_answered": sum(r["citation_valid"] for r in answered) / max(1, len(answered)),
        "evidence_support_on_answered": sum(r["evidence_support"] for r in answered) / max(1, len(answered)),
        "retrieval_success_rate": sum(r["retrieved"] for r in records) / len(records),
        "abstention_accuracy": sum(r["abstained"] for r in abstentions) / max(1, len(abstentions)),
        "provider_failure_rate": sum(r["provider_failed"] for r in records) / len(records),
        "average_latency_ms": statistics.mean(times), "median_latency_ms": statistics.median(times),
        "p95_latency_ms": times[math.ceil(.95 * len(times)) - 1]}
    folder = Path("artifacts")
    folder.mkdir(exist_ok=True)
    (folder / "benchmark.json").write_text(json.dumps({"summary": summary, "records": records}, indent=2), encoding="utf-8")
    (folder / "benchmark-summary.md").write_text("# Fixture benchmark\n\n" + summary["warning"] + "\n\n```json\n" + json.dumps(summary, indent=2) + "\n```\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if not all(r["correct"] and r["citation_valid"] and r["evidence_support"] for r in records):
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
