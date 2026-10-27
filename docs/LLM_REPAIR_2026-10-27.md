# Urgent provider repair — 2026-10-27

This live report supersedes the older unvalidated-provider status in the initial implementation docs.
No credentials or raw HTTP headers are included. Diagnostic artifacts are gitignored.

## Exact failures observed

**Gemini:** configured `gemini-3.8-flash`, MAX_OUTPUT_TOKENS=1000, request timeout=25 seconds.
Authenticated model discovery returned HTTP 200 and included that model. A direct LangChain request
raised GoogleAPIError -> ServerError, code 503, status UNAVAILABLE, with the message:
“This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.”
This is an upstream capacity error, not an invalid model name or invalid API key.
The router previously inspected only `status_code`; Google's wrapper exposes `code` on itself or
the chained exception. This hid the HTTP status and prevented the intended transient retry classification.

A test of listed `gemini-2.5-flash-lite` returned 404 NOT_FOUND: no longer available to new users;
the API specifically recommends `gemini-3.5-flash-lite`. The latter is in the authenticated model list
and [Google's pricing page](https://ai.google.dev/gemini-api/docs/pricing) lists its input/output free tier.
It still returned upstream 504 in this session. A separate `gemini-3.1-flash-lite` probe returned 503.
Gemini success is therefore NOT claimed. Account free-tier confirmation remains enabled as configured
by the operator; a catalog entry alone does not establish usable account quota.

**OpenRouter:** the old free-router behavior was reproduced with a raw completion request to preserve
metadata even when structured parsing would raise LengthFinishReasonError. The actual selected model
in this reproduction was `recursive/flint-v1.0:free`; HTTP 200, finish_reason=length, zero visible
characters, completion_tokens=1000, cost=0. The provider reported reasoning_tokens=1332, which exceeds
its reported completion count; these inconsistent raw counters are preserved as reported rather than
corrected or fabricated. This supports reasoning/output exhaustion, not an insufficient retrieval result.
The model behind the user's earlier request cannot be recovered from an error type alone; this is a
fresh reproduction, not an assertion about the historical routing choice.

OpenRouter documents that [reasoning usually shares the output-token limit](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens).
Its [free routing documentation](https://openrouter.ai/docs/guides/routing/model-variants/free) distinguishes
free model variants from paid fallbacks. No paid model was used.

## Changes

- Short extraction-only JSON prompt; at most three claims, no reasoning prose.
- Send only evidence IDs and genuine passages rather than unrelated evidence metadata.
- Disable OpenRouter reasoning via `extra_body.reasoning.enabled=false`; require supported parameters.
- Pin `nvidia/nemotron-3.5-super-vl:free`, validated against the live catalog with input/output prices zero.
- Put OpenRouter before Gemini in defaults, .env.example and local .env; preserve keys and other settings.
- Switch Gemini default/local configuration to the API-recommended `gemini-3.5-flash-lite`, minimal thinking,
  omit its unsupported temperature setting. Keep Gemini as fallback while service capacity is unavailable.
- Keep the existing 1000-token output budget: successful JSON needs only 57–69 tokens, so no increase justified.
- Use structured `include_raw=True` to retain selected model, finish reason, usage and cost, without raw text logs.
- Read nested Google `code` values for retry/fallback diagnostics; allowlist diagnostic fields, never log exception bodies.
- Reject length-terminated output even if partial JSON happens to parse. Preserve all existing evidence checks.

## Actual validation

**Direct extraction, outside LangGraph:** TinyFish retrieved https://example.com/ as `page_text`,
not an agent summary. OpenRouter selected `nvidia/nemotron-3.5-super-vl:free`, returned a validated Draft
with the original evidence ID and exact source quote, finish_reason=stop, 68 output tokens, zero reasoning
tokens. Deterministic verifier accepted the claim and constructed the real URL citation.

**Full graph, OpenRouter first:** status answered; 4167.72 ms total. TinyFish retrieval completed at
1568.41 ms; verification completed at 4167.16 ms. No warnings. Model returned 69 output tokens and
zero reasoning tokens. Answer: “for use in documentation examples without needing permission”.
Citation: https://example.com/, title Example Domain. Supporting passage:

> This domain is for use in documentation examples without needing permission.

The citation URL was independently fetched again through TinyFish and both the quotation and answer
were found in the actual webpage. Genuine evidence reached the verifier; no result was fabricated.

Live artifacts: `artifacts/repair-direct.json`, `artifacts/repair-end-to-end.json`,
`artifacts/repair-openrouter-baseline.json`, `artifacts/repair-direct-gemini.json`.
`scripts/verify_llm_repair.py` reproduces direct/full/baseline checks. It invokes real APIs and may
consume free quota; default tests remain offline.

## Regression validation

New tests cover nested Google status extraction/redaction, 503 retry recovery, actual-model metadata,
short evidence payload, disabled reasoning without increasing output tokens, minimal Gemini thinking,
length-exception usage preservation, parse errors and length-terminated partial JSON rejection.
Final pytest: **64 passed, 2 opt-in live tests skipped, 0 failed in 2.83 seconds**.
Ruff: **all checks passed**. Live Gemini availability remains an external limitation.
Restart the running uvicorn process to load the updated code and .env.
