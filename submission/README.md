# WebScout AI

WebScout AI is an evidence-first web retrieval agent for AMD AI League Match 4. It accepts a natural-language question and optional starting URL, navigates public web pages within bounded budgets, extracts relevant passages, and returns only claims that can be proven by literal text in cited source evidence.

## Why it is useful

Ordinary web answers often mix search snippets, stale information, and unsupported model knowledge. WebScout keeps the retrieval trail visible: every accepted claim has a source URL and supporting passage, while unanswerable or conflicting questions produce an explicit abstention.

## Architecture

FastAPI exposes `/query`, `/health`, `/ready`, and a small browser demo. LangGraph orchestrates `analyze → discover → navigate → extract → verify`, with bounded retries, pages, link hops, concurrency, and a request deadline. TinyFish Search/Fetch/Agent, direct HTTP, and optional Playwright provide retrieval paths. BeautifulSoup/lxml preserve page text, tables, JSON-LD, dates, and links. BM25-style ranking selects evidence passages. A structured-output LLM proposes claims, and deterministic verification checks evidence IDs, exact quotes, claim inclusion, negation, freshness, suspicious instructions, and selected numeric conflicts.

## Providers

The LLM router supports OpenRouter free routing, Gemini with explicit free-tier confirmation, NVIDIA with explicit free-tier confirmation, and a local OpenAI-compatible endpoint. It never automatically enables a paid model. TinyFish is optional; a starting URL enables static HTTP retrieval without search credentials.

## Run locally

Requirements: Python 3.11+ and `uv`.

```powershell
uv sync --frozen
Copy-Item .env.example .env
# Configure an eligible zero-cost LLM and, if allowed, TinyFish.
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`. API documentation is at `/docs`.

## Test

```powershell
.venv\Scripts\python -m pytest -q
.venv\Scripts\python -m ruff check app tests scripts
$env:PYTHONPATH='.'
.venv\Scripts\python scripts/benchmark.py
```

The fixture benchmark uses an oracle model and is not a live web or model accuracy claim. See `TEST_RESULTS.md` and `FINAL_STATUS.md` for the exact validation record.

## Known limitations

The official Match 4 grader contract, starter kit, network policy, and AMD runtime requirements were not exposed in the public materials retrieved on 2026-10-27. TinyFish and live LLM validation require credentials that were not present in this workspace. AMD GPU/ROCm execution and the final hosted demo are unverified. The internal AMD adapter therefore fails closed rather than inventing a contract.
