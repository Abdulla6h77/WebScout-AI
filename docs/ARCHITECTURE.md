# Architecture

## Flow

`Query` → LangGraph `analyze` → `discover` → `navigate` → `extract` → `verify` → answer or abstention.
Insufficient evidence returns through `replan` when attempts, pages, and hops remain.
A request-wide asyncio deadline wraps the graph and cancels expired work. Each provider also
has its own timeout. A ContextVar carries trace start time independently for concurrent requests.

Planning is deterministic: extract an explicit URL, normalize domain constraints, create three
query variants. Search discovery is a separate TinyFish Search API interface. No unlicensed
scraping of search-engine results is implemented. If discovery has no credential, a starting
URL is required. Same-site links are ranked by BM25-style overlap; pagination links can be
followed within the same crawl budget. Website-specific queries stay within domain scope.

Retrieval is concurrent in batches. TinyFish Fetch is the primary static provider. Explicit
browser requests can use cancellable TinyFish async automation, then Playwright. Static requests
can fall back to httpx, then Playwright if enabled. The browser does not perform arbitrary
LLM-generated clicks or form submissions; TinyFish is the multi-step browser integration.

## Evidence boundary

HTML is parsed with BeautifulSoup/lxml. Script/style/iframe content is removed; JSON-LD is
parsed separately and serialized as document data. Table rows preserve label/value adjacency.
Retrieved links, final URL, retrieval time, publication date when available, and provider are
retained. Content hashes deduplicate identical pages and passages. Passage windows keep nearby context.
BM25-style scores select up to twelve passages, with a boost for identifier tokens containing digits.

TinyFish browser `result` is tagged `agent_output`. It must be re-fetched as page text before it
can enter evidence ranking. Without independent content retrieval, the system abstains. Remote
browser output is allowed to suggest links, which are validated and must remain in domain scope.

LangChain structured output produces `Draft` claims tied to evidence IDs. Deterministic checks
require exact claim/quote inclusion and reject invented IDs, unsupported inference, instruction
injection signals, and substring answers that discard source negation. Citations are constructed
from stored evidence objects, never from model-supplied URLs. Final prose is assembled only from
accepted extracts, so a separate generative synthesis cannot introduce uncited facts.

Contradictions reported by the model trigger abstention. A narrow deterministic guard catches
different prices/day counts in otherwise identical numeric-fact sentences. It does not detect all
semantic disagreements or distinguish every historical version. Current/latest questions reject
explicitly archived evidence or publication dates older than a year. Undated content yields a
freshness warning; fetching now is not proof that a claim is current. These are documented engineering
heuristics, not comprehensive fact verification. Authoritative-source preference is currently
explicit domain constraints and an 'official source' search variant, not a trained authority classifier.

## Resources and security

- Defaults: 30 seconds total, 8 attempted URLs, 2 hops, 3 rounds, 3 retrieval tasks.
- Graph recursion is capped at 40. Search pagination is bounded. Requests are limited to 2 active API jobs.
- Reusable AsyncClient, per-provider serialized LLM throttling, bounded retry and fallback.
- Optional TTL cache with 64-entry default cap; disabled by default for freshness.
- HTTP downloads are streamed with a byte cap. Content and evidence lengths are capped.
- URL schemes, credentials, ports, private/reserved addresses and DNS results are checked.
- Static HTTP pins the checked IP and preserves original Host/TLS SNI. Every redirect is revalidated.
- Playwright validates routed requests and final URLs, blocks POST/downloads/service workers and heavy media.
- Remote browsing and local Chromium still need network-layer egress rules to prevent DNS rebinding or
  private redirects during remote execution. Application checks alone are not a security sandbox.
- Web content has no tool execution authority. Suspicious passages are excluded, but prompt-injection
  detection is heuristic. Do not expose this prototype publicly without defense in depth.
- Provider exception messages and secrets are never returned. Trace records contain stages/timings only.
- Large upstream JSON bodies from remote APIs are bounded by timeout/content validation after decoding;
  a streaming JSON size guard remains a hardening priority.

## Models

The router checks configured model availability and uses LangChain structured extraction.
OpenRouter uses only its free router or a catalog-confirmed free variant. Gemini/NVIDIA are
disabled until the operator confirms free-tier access. Positive estimated-cost settings do not
enable paid models; a priced-model accounting policy is intentionally not implemented.
Actual token usage accounting is not yet exported. A trusted local OpenAI-compatible inference
endpoint is replaceable through `LLM_PROVIDER=local`; it was not validated on AMD hardware.
