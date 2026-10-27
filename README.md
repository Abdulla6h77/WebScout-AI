# WebScout AI

**2026-10-27 provider repair:** real TinyFish + OpenRouter end-to-end answering and a re-fetched citation
now pass (4.17 seconds in the recorded run). OpenRouter's pinned free model is first; Gemini remains
upstream-unavailable. See [live repair report](docs/LLM_REPAIR_2026-10-27.md). Historical status below
describes the original build before this repair.

A general-purpose, evidence-first web retrieval prototype for AMD AI League Match 4.
Built independently in this folder; no Medicine Autopilot code was accessed or reused.

**Status:** the local workflow and fixture evaluation work. Live HTTP retrieval passed.
Live LLM answering and TinyFish validation remain incomplete. This is not a claim of
official AMD compatibility or competition readiness.

## Run on Windows

Python 3.11+ and [uv](https://docs.astral.sh/uv/) are required.

```powershell
cd 'D:\AMD challenge\4th challenge'
uv sync --frozen
Copy-Item .env.example .env
# Edit .env: set your keys. Do not paste credentials into source code.
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000 for the demo, `/docs` for the API, `/health` for liveness,
and `/ready` for configuration status. Readiness is not an external connectivity test.

The simplest eligible LLM setup is `OPENROUTER_API_KEY` with `OPENROUTER_MODEL=openrouter/free`.
The free router is documented to use only free models; rate limits and model compatibility
still apply. Gemini defaults to `gemini-3.8-flash`, listed with a free tier on Google's pricing
page on 2026-10-22, but is disabled until `GEMINI_FREE_TIER_CONFIRMED=true` because an API key
may belong to a billed project. NVIDIA requires an explicit model and confirmed free access.
See [provider research](docs/PROVIDERS.md). No provider automatically switches to a paid model.

Set `TINYFISH_API_KEY` for open-web search and primary page retrieval. Without it, provide
a starting URL: static HTTP retrieval works without a search credential. Browser navigation
uses `TINYFISH_AGENT_ENABLED=true` and `browser_required=true`; agent summaries are not accepted
as independent evidence. Browser jobs consume TinyFish quota; validate your quota before use.

Optional local browser:

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH="$PWD\.playwright"
.venv\Scripts\python -m playwright install chromium
# Set PLAYWRIGHT_ENABLED=true in .env, retaining the same browser path when starting the server.
```

## API and local evaluator

```powershell
$body = @{ question='What is this domain used for?'; starting_url='https://example.com/' } | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8000/query -Method Post -ContentType application/json -Body $body
.venv\Scripts\python -m app.evaluation.local_adapter --question 'What is this domain used for?' --url https://example.com/
```

The local adapter also accepts one JSON request per stdin line. The AMD adapter intentionally
raises `NotImplementedError` until the organizer's real input/output contract is supplied.

## Test and benchmark

```powershell
.venv\Scripts\python -m pytest -q
.venv\Scripts\python -m ruff check app tests scripts
$env:PYTHONPATH='.'
.venv\Scripts\python scripts/benchmark.py
.venv\Scripts\python scripts/live_probe.py
```

The live probe makes a bounded public HTTP request and at most one routed LLM extraction
(zero retries), plus TinyFish Fetch if a key exists. It never outputs credentials. It writes
`artifacts/live-probe.json`, which is gitignored. The offline benchmark uses fixtures and an
answer oracle; its accuracy and millisecond latencies do not measure live web/LLM performance.

Live browser tests require explicit opt-in: `WEBSCOUT_LIVE_TESTS=1` and
`python -m pytest tests/live -q`. They may consume provider quota. Most tests need no network.

## Design and limits

LangGraph runs analyze → discover → navigate → extract → verify, with bounded replanning.
Defaults: 30-second request budget, 8 attempted pages, 2 link hops, 3 rounds, concurrency 3.
Answers are extractive: every claim must be a literal substring of its cited passage.
LLM relevance assessment is complemented by deterministic evidence-ID, quote, source,
negation, freshness, and limited numeric-conflict checks. This does not prove semantic
entailment for every question. See [architecture](docs/ARCHITECTURE.md) and
[evaluation](docs/EVALUATION.md).

For production exposure, deploy behind authentication, request limits, and outbound network
restrictions. Browser DNS rebinding and remote TinyFish navigation cannot be controlled fully
by application-level URL checks; an egress policy is required. This demo binds to loopback by default.

See [AMD requirements](docs/AMD_REQUIREMENTS.md), [deployment](docs/AMD_DEPLOYMENT.md),
[progress](docs/IMPLEMENTATION_PROGRESS.md), and [submission checklist](docs/SUBMISSION_CHECKLIST.md).
