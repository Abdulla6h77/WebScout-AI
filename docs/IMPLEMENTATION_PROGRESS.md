# Implementation progress

2026-10-22. New standalone project, no copying or accessing Medicine Autopilot during this work.

| Milestone | Implemented | Validation/remaining work |
|---|---|---|
| 1 Foundation | Python project, lockfile, config, Pydantic contract, FastAPI, bounded LangGraph | Fixture graph/API tests passed |
| 2 Retrieval | TinyFish Search/Fetch/async browser adapters, HTTP, Playwright, same-site crawl, fallback | HTTP live passed; TinyFish and browser live incomplete |
| 3 Reliability | Ranking, structured/table evidence, citation mapping, abstention, limited conflicts/freshness/injection checks | Fixture tests passed; semantic verification remains heuristic |
| 4 Models | Gemini/OpenRouter/NVIDIA and local adapter, model availability, free-only gating, retry/fallback | Mock routing passed; real OpenRouter attempt unsuccessful; other live models unvalidated |
| 5 Evaluation | 56 tests passed, 2 opt-in live tests skipped; lint passed; 26-case benchmark and real HTTP probe | Benchmark uses oracle, no live accuracy claim |
| 6 AMD preparation | Linux/CPU instructions, locked Docker config, health/readiness, explicit grader seam | Local image build and CPU container health/readiness passed; GPU and grader integration untested |
| 7 Demo | FastAPI-served HTML question form, citations, status, timing, trace | API/HTML fixture validation passed; no visual browser pass yet |

Definition of done is **not met**: a real TinyFish run and a real LLM-grounded answer are required.
No successful AMD deployment or official eligibility is claimed. A request to install Chromium and
continue live diagnosis was rejected during escalation; no retry of that installation was attempted.

The implementation prioritizes extractive precision over fluent synthesis. Unconfigured providers
produce explicit abstention rather than fake answers. Provider modules are consolidated in one factory
instead of three nearly identical files; graph answer assembly does not need another LLM call.
