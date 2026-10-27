# Test results

Checked 2026-10-27 in `D:\AMD challenge\4th challenge`.

## Automated checks

| Check | Result |
|---|---|
| `.venv/Scripts/python.exe -m pytest -q` | **56 passed, 2 skipped** in 1.66 seconds |
| `.venv/Scripts/python.exe -m ruff check app tests scripts` | **Passed** |
| `PYTHONPATH=. .venv/Scripts/python.exe scripts/benchmark.py` | **26/26 fixture cases passed** |

Fixture benchmark details: answer correctness 100%, answered-case citation validity 100%, evidence support 100%, expected-abstention accuracy 100%, retrieval success 88.46%, mean latency 7.79 ms, median 3.23 ms, p95 7.97 ms. These are offline fixture/oracle measurements and exclude live web and model latency.

## Live checks

`scripts/live_probe.py` successfully retrieved `https://example.com/` through the direct HTTP provider and extracted 172 characters. End-to-end LLM answering, TinyFish Fetch/Agent, and Playwright were skipped because no `.env` or provider credentials were available in this workspace. No live answer or live citation is claimed.

## Local and Docker startup

The local Uvicorn smoke test returned HTTP 200 from `/health`, `/ready`, and `/`. The Docker image build completed with `docker build -f deployment/Dockerfile -t webscout-ai:submission .`. A container smoke test also returned HTTP 200 from `/health` and `/ready`; readiness correctly reported `missing_llm_configuration` because no credentials were supplied. AMD GPU/ROCm execution was not tested.
