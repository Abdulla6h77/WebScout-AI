# WebScout AI architecture

## Request path

FastAPI receives a validated `Query` and passes it to a bounded LangGraph workflow:

`analyze → discover → navigate → extract → verify → answer or abstention`

The planner extracts an explicit URL, normalizes allowed domains, and creates query variants. Discovery uses TinyFish Search when configured. Navigation retrieves a bounded batch of pages concurrently, follows only in-scope links, deduplicates content by hash, and supports TinyFish Fetch, direct HTTP, and optional Playwright/browser paths.

## Evidence boundary

HTML is parsed into text, tables, JSON-LD, links, titles, providers, timestamps, and publication dates. Relevant passage windows are ranked with a BM25-style scorer. A structured-output LLM may propose claims, but final claims must use a known evidence ID, an exact quote from the passage, and claim text contained in that quote. Citations are built from stored evidence rather than model-supplied URLs. Conflicts, negation loss, stale current-answer evidence, and prompt-injection signals can cause rejection or abstention.

## Limits and security

Defaults are a 30-second request budget, 8 attempted pages, 2 link hops, 3 attempts, and 3 retrieval tasks per batch. URLs are canonicalized, restricted to HTTP(S), checked for credentials/private addresses/unsafe ports, DNS-validated, and revalidated across redirects. HTTP retrieval pins the validated IP while preserving Host/TLS SNI. Content, response, cache, and graph recursion limits prevent unbounded work.

## Deployment

The Dockerfile uses Python 3.11, locked uv dependencies, Chromium, a non-root runtime user, and a `/health` healthcheck. ROCm and AMD GPU inference are not bundled; the local-model configuration is an integration seam requiring an organizer-compatible Linux ROCm service.
