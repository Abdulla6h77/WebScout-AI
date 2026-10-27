# Evaluation

## Recorded local results

The first suite run found one failure: a known-site replan could rediscover URLs at depth zero,
bypassing the hop limit. This was fixed by ending known-site exploration when its bounded link
queue is exhausted. The latest recorded run passed **56 tests, with 2 opt-in live tests skipped,
in 1.71 seconds**. Lint also passed. A negation regression test verifies that extracting a name
from a sentence saying it was not that person cannot produce an accepted answer.
Live tests are separate and opt-in; mock provider responses do not establish real API compatibility.

Coverage includes factual answers, policy/company/docs/pricing questions, 2-hop navigation,
dynamic browser routing, table and JSON-LD extraction, multiple sources, model-reported and numeric
conflicts, missing/unanswerable facts, unsafe URLs/private DNS, redirect validation and IP pinning,
duplicate URLs, provider fallback/cache, async TinyFish polling/cancellation, free-provider routing,
rate-limit fallback, paid-model exclusion, timeout, injection, quote integrity, exact output,
domain scope, stale dates, concurrent graph state and FastAPI validation.

## Fixture benchmark

Run `python scripts/benchmark.py` with project root on PYTHONPATH.
Cases: `tests/fixtures/benchmark.json`. Results: `artifacts/benchmark.json` and
`artifacts/benchmark-summary.md`. Expected answers are given to a fixture model oracle, so the benchmark
measures pipeline mechanics, retrieval/citation checks and abstention behavior, not LLM intelligence.

Latest run: 26/26 fixture cases matched expected status and answer. Answered-case citation validity and
passage support were 100%; expected-abstention accuracy was 100%. Fixture retrieval success was 88.46%
and failure-status rate 7.69%, including intentionally broken/no-discovery scenarios.
Measured mean 7.79 ms, median 3.23 ms, p95 7.97 ms in the latest run. These timings exclude real web and model
latency and must not be presented as competition performance. Each rerun records its actual timings.

## Live evidence

`scripts/live_probe.py` recorded successful real HTTPS retrieval from https://example.com/ using
the static fallback. The end-to-end query returned `insufficient_evidence` after 11,925.82 ms because
the configured OpenRouter path did not yield a valid structured result. No answer/citation was fabricated.
No TinyFish key was available; Fetch/Agent live validation remains incomplete. Chromium installation
was requested but the escalation was rejected, so Playwright live validation is incomplete too.

The gitignored `artifacts/live-probe.json` contains the actual result. Provider credentials and raw
provider error text are excluded. A longer-timeout diagnostic probe was prepared but not completed.

## Next evaluation work

1. Add a valid free-tier LLM credential and validate one real cited answer.
2. Supply TinyFish credentials and confirm Search, Fetch, async browser run, cancellation and independent evidence.
3. Install Chromium and run `WEBSCOUT_LIVE_TESTS=1 python -m pytest tests/live -q`.
4. Add held-out live questions and human judgments, independent of model outputs.
5. Measure live latency distributions and evidence relevance, semantic contradictions and freshness.
6. Run the organizer's actual grader after implementing its contract.

Known limits: exact substring inclusion proves provenance, not complete semantic entailment. Negation
and conflict checks are conservative heuristics. Adversarial paraphrases, ambiguous entities, historical
versions and incomplete multi-part answers require stronger assessment and a broader held-out dataset.
