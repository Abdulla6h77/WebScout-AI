# Provider research and configuration

Researched 2026-10-22 using official documentation. Free quotas vary by account/region and can change.

## TinyFish

- [Search reference](https://docs.tinyfish.ai/search-api/reference): `GET https://api.search.tinyfish.ai`,
  query, include_domains, page; `X-API-Key`.
- [Fetch reference](https://docs.tinyfish.ai/fetch-api/reference): `POST https://api.fetch.tinyfish.ai`,
  urls, format=html, links, ttl=0, per_url_timeout_ms; results contain text/final_url.
- [Agent reference](https://docs.tinyfish.ai/agent-api/reference):
  `POST https://agent.tinyfish.ai/v1/automation/run-async`, poll `GET /v1/runs/{id}`;
  cancel with `POST /v1/runs/{id}/cancel`. Result is generated structured data, not raw DOM evidence.
- Agent max_steps and capture_config are account/beta gated; omitted to avoid assuming account capabilities.
- Exact downloaded reference snapshots are included alongside this document. Live authentication was not
  validated because no TinyFish key was present in the process environment or this project's configuration.
  No other project's credentials were searched or read.

## LLM choice

| Provider | Official evidence | Routing decision |
|---|---|---|
| Gemini | [Pricing](https://ai.google.dev/gemini-api/docs/pricing) lists Gemini 3.8 Flash with free input/output; Gemini 4 Argon has no free tier | Suggested model `gemini-3.8-flash`; gated by explicit free-tier confirmation and model catalog check |
| OpenRouter | [Free variants](https://openrouter.ai/docs/guides/routing/model-variants/free) says `openrouter/free` falls back only to free models; paid fallback entries incur charges | Usable default when its key is present; no paid fallback list |
| NVIDIA NIM | [API reference](https://docs.nvidia.com/nim/large-language-models/latest/api-reference.html) documents OpenAI-compatible chat and model discovery | Adapter uses hosted `integrate.api.nvidia.com/v1`; explicit model and confirmation required. Hosted free quota/model eligibility unverified |
| Local | Trusted operator-selected OpenAI-compatible endpoint | Replaceable local inference path; not installed or tested on ROCm |

Gemini Flash is a provisional balance of latency, structured output and context capacity; OpenRouter's
free router avoids binding the project to a disappearing free model. Neither choice guarantees availability
or latency. Model catalogs are checked before first use. The virtual free router may not appear as a model
entry; its documented routing contract is used. Gemini project billing and NVIDIA quota cannot be inferred
from a model name, so operators must confirm their account tier. Do not enable flags blindly.

Structured extraction uses LangChain `with_structured_output(Draft, method='json_schema')`.
Tool-calling support is not required for LLM extraction: graph code controls tools. Unsupported schemas,
rate limits or provider failures yield bounded fallback or abstention. Provider-specific tool-calling
compatibility and context limits are not yet measured in live tests.

The first live OpenRouter attempt did not return a usable structured result. Logs deliberately omit
raw provider exception bodies. A follow-up diagnostic attempt and Chromium installation were not run
after the associated escalation was rejected. Do not call this a validated live LLM integration.
