# WebScout AI

![WebScout AI Banner](https://github.com/Abdulla6h77/WebScout-AI/blob/main/assets/banner.png?raw=width=800&height=200)

> **2026-10-27 provider repair:** real TinyFish + OpenRouter end-to-end answering and a re-fetched citation now pass (4.17 seconds in the recorded run). OpenRouter's pinned free model is first; Gemini remains upstream-unavailable. See [live repair report](docs/LLM_REPAIR_2026-10-27.md). Historical status below describes the original build before this repair.

A general-purpose, evidence-first web retrieval prototype for **AMD AI League Match 4**.
Built independently in this folder; no Medicine Autopilot code was accessed or reused.

[![Status](https://img.shields.io/badge/Status-Local%20workflow-green.svg)](https://img.shields.io/badge/Status-Local%20workflow-green.svg)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://img.shields.io/badge/Python-3.11+-blue.svg)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🚀 Quick Start

Python 3.11+ and [uv](https://docs.astral.sh/uv/) are required.

```powershell
cd 'D:\AMD challenge\4th challenge'
uv sync --frozen
Copy-Item .env.example .env
# Edit .env: set your keys. Do not paste credentials into source code.
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) for the demo, `/docs` for the API, `/health` for liveness, and `/ready` for configuration status.

**Simplest LLM setup:** `OPENROUTER_API_KEY` with `OPENROUTER_MODEL=openrouter/free`.

---

## 📦 Installation

| Step | Command |
|------|---------|
| 1. Install dependencies | `uv sync --frozen` |
| 2. Copy environment template | `Copy-Item .env.example .env` |
| 3. Configure API keys | Edit `.env` with your keys |
| 4. Install Playwright browsers (optional) | ```powershell\n$env:PLAYWRIGHT_BROWSERS_PATH="$PWD\\.playwright"\n.venv\Scripts\python -m playwright install chromium\n``` |
| 5. Start the server | `.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000` |

---

## 🛠️ Usage

### Local Development

```powershell
# Start the server
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Open in browser
# http://127.0.0.1:8000
# http://127.0.0.1:8000/docs  - API documentation
# http://127.0.0.1:8000/health - Liveness check
# http://127.0.0.1:8000/ready   - Configuration status
```

### API Examples

**POST /query**

```json
{
  "question": "What is this domain used for?",
  "starting_url": "https://example.com/"
}
```

**Example cURL:**

```powershell
$body = @{ question='What is this domain used for?'; starting_url='https://example.com/' } | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8000/query -Method Post -ContentType application/json -Body $body
```

**Local adapter evaluation:**

```powershell
.venv\Scripts\python -m app.evaluation.local_adapter --question 'What is this domain used for?' --url https://example.com/
```

---

## 🧪 Test and Benchmark

| Command | Description |
|---------|-------------|
| `.venv\Scripts\python -m pytest -q` | Run test suite |
| `.venv\Scripts\python -m ruff check app tests scripts` | Lint check |
| `PYTHONPATH='.' .venv\Scripts\python scripts/benchmark.py` | Run benchmark |
| `PYTHONPATH='.' .venv\Scripts\python scripts/live_probe.py` | Live probe |

**Live probe:** Makes a bounded public HTTP request and at most one routed LLM extraction (zero retries), plus TinyFish Fetch if a key exists. Results write to `artifacts/live-probe.json` (gitignored).

**Live browser tests:** Require `WEBSCOUT_LIVE_TESTS=1` and `python -m pytest tests/live -q`. May consume provider quota.

---

## 🏗️ Design & Architecture

- **Pipeline:** LangGraph runs analyze → discover → navigate → extract → verify, with bounded replanning.
- **Defaults:** 30-second request budget, 8 attempted pages, 2 link hops, 3 rounds, concurrency 3.
- **Evidence-first:** Every claim must be a literal substring of its cited passage.
- **Checks:** Negation, freshness, limited numeric-conflict checks.
- See [architecture](docs/ARCHITECTURE.md) and [evaluation](docs/EVALUATION.md) for details.

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [AMD Requirements](docs/AMD_REQUIREMENTS.md) | AMD competition requirements |
| [Deployment](docs/AMD_DEPLOYMENT.md) | Deployment guide |
| [Implementation Progress](docs/IMPLEMENTATION_PROGRESS.md) | Progress tracking |
| [Submission Checklist](docs/SUBMISSION_CHECKLIST.md) | Submission checklist |
| [LLM Repair Report](docs/LLM_REPAIR_2026-10-27.md) | Latest LLM repair report |
| [Providers](docs/PROVIDERS.md) | Provider research and configuration |
| [Architecture](docs/ARCHITECTURE.md) | System architecture |
| [Evaluation](docs/EVALUATION.md) | Evaluation methodology |

---

## 🐛 Known Limits

- Browser DNS rebinding and remote TinyFish navigation cannot be fully controlled by application-level URL checks; an egress policy is required.
- This demo binds to loopback by default.
- Production exposure requires authentication, request limits, and outbound network restrictions.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- AMD AI League Match 4 organizers
- TinyFish team
- OpenRouter team
- All contributors and supporters
