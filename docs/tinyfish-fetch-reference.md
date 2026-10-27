> ## Documentation Index
> Fetch the complete documentation index at: https://docs.tinyfish.ai/llms.txt
> Use this file to discover all available pages before exploring further.

# Fetch API Reference

> Complete reference for the Fetch API endpoint

## Endpoint

```
POST https://api.fetch.tinyfish.ai
```

All requests require an `X-API-Key` header. See [Authentication](/authentication).

***

## Request

```json theme={null}
{
  "urls": ["https://example.com"],
  "format": "html",
  "links": false,
  "image_links": false,
  "ttl": 3600,
  "per_url_timeout_ms": 45000
}
```

### Parameters

**urls** `string[]` *required*

URLs to fetch and extract. Maximum 10 URLs per request.

All URLs must use `http` or `https`. Private IP addresses, localhost, and cloud metadata endpoints are rejected.

**purpose** `string`

An optional short statement of **why** you are fetching these URLs — the underlying goal or task
the content will be used for. Supplying the intent behind a fetch gives us additional signal to
further inform and deliver better-quality results. When omitted, fetch behaves exactly as before.
When supplied, the value must be non-empty (whitespace-only values are rejected). Maximum 2000
characters. For example, `Compare pricing tiers across vendors for a procurement report`.

**format** `string` (default: markdown)

Output format for the `text` field in each result. One of:

* `html` — semantic HTML
* `markdown` — clean Markdown, recommended for LLMs (default)
* `json` — structured document tree

**links** `boolean` (default: false)

When `true`, include all `<a href>` URLs found on the page in the `links` field.

**image\_links** `boolean` (default: false)

When `true`, include all `<img src>` URLs found on the page in the `image_links` field.

**iframe\_links** `boolean` (default: false)

When `true`, include the `src` URLs of `<iframe>` elements found on the page in the `iframe_links` field.

Use this when a page embeds its main content in a frame (job boards, booking widgets, document viewers): fetch the returned URL to read the embedded content. Iframes that a page injects with JavaScript are only present when the page was rendered in a browser.

**ttl** `integer` (default: omitted)

Cache freshness tolerance in seconds.

* Omit `ttl` to accept any cached entry.
* Set `ttl` to `0` when you want a live fetch.
* Set `ttl` to a positive integer to accept cached entries younger than that many seconds.

**per\_url\_timeout\_ms** `integer` (default: omitted)

Per-URL wall-clock timeout budget in milliseconds. Must be between `1` and `110000`.

If a URL exceeds this budget, that URL returns a `timeout` error in `errors[]` while other URLs in the same request can still complete.

**if\_none\_match** `string`

An ETag you saved from a prior fetch of this URL, forwarded verbatim as the `If-None-Match` header on the origin request. Single URL only — combining with a batch of URLs returns a `400`.

**if\_modified\_since** `string`

A `Last-Modified` value you saved from a prior fetch of this URL, forwarded verbatim as the `If-Modified-Since` header on the origin request. Single URL only — combining with a batch of URLs returns a `400`.

**include\_etag\_and\_last\_modified** `boolean` (default: false)

When `true`, include `etag` and `last_modified` on each result so you can store them and replay them on your next fetch of the same URL. Works with a single URL or a batch.

> [!NOTE]
>
> Conditional requests are a stateless pass-through — Fetch does not store `etag` or `last_modified` for you. Save the values returned by `include_etag_and_last_modified` and replay them as `if_none_match` / `if_modified_since` on your next request to detect whether the page changed.

**include\_selectors** `string[]`

An array of CSS selectors (1–20 entries, each 1–1000 characters) that scopes extracted content (`text`, `links`, `image_links`) to elements matching **any** entry, concatenated in document order. Tag selectors cover semantic sections (`main`, `article`, `nav`); entries may themselves use CSS comma-grouping (`"main, footer"`). Standard CSS only — not XPath, Playwright `text=` locators, or glob patterns such as `*specificat*` (attribute matching like `[class*="price"]` is fine). Ids that start with a digit or contain dots are not valid `#id` selectors; use the attribute form instead (`[id="48599"]`).

Selected content is returned verbatim, converted to the requested `format` (scripts and styles stripped) — automatic boilerplate removal is bypassed. Page-level metadata (`title`, `description`, `language`, `author`, `published_date`) still comes from the full document.

If **some** entries match and others don't, the URL still succeeds with the matched content and the misses are listed in the result's `unmatched_selectors`. If **no** entry matches anything, that URL fails with the per-URL error code `selector_not_matched` — there is no silent full-page fallback — and the error carries `unmatched_selectors` plus `candidate_selectors` retry hints. Invalid CSS selector syntax is rejected with a `422`.

**exclude\_selectors** `string[]`

An array of CSS selectors (1–20 entries, each 1–1000 characters) for elements to remove before extraction. Applied **before** `include_selectors` scopes what remains, so it also prunes inside selected regions. Entries that match nothing are a no-op, never an error. Same syntax rules as `include_selectors`: standard CSS only, attribute form for digit-leading or dotted ids. Invalid CSS selector syntax is rejected with a `422`.

> [!NOTE]
>
> Selectors are applied after the page is fetched — caching and routing are unchanged. URLs that resolve to direct PDF or CSV downloads have no HTML to scope, so sending `include_selectors` or `exclude_selectors` for them fails that URL with `selector_unsupported`.

**highlights** `object`

Ask a question and get back the passages from each page that best answer it — ranked, and quoted word-for-word from the page. Requires `format: "markdown"`. Sub-fields below.

**highlights.query** `string` *required*

The question to answer from each page. Include the entity or topic in the query (e.g. "who founded Acme Corp", not "who founded this company") — retrieval works on vocabulary overlap with the page, and keyword-poor queries return empty results far more often.

**highlights.max\_snippets** `integer` (default: 5)

Maximum ranked passages per URL. Between `1` and `20`.

**highlights.max\_characters** `integer`

Soft total-character budget across a URL's passages, between `100` and `20000`. Passages are added until the budget is reached, but the top-ranked passage is always returned even if it alone exceeds the budget.

**highlights.include\_full\_page\_text** `boolean` (default: false)

By default a highlights request returns just the passages — the result's `text` field is `null`. Set `true` to also receive the full page markdown in `text`.

> [!NOTE]
>
> **Beta:** Highlights is in beta and is enabled per-account — [join our Beta program](https://agent.tinyfish.ai/beta) to enable it for your account. Requests that include `highlights` from an account that isn't enabled return `403 FORBIDDEN`; requests without the field are unaffected.

> [!NOTE]
>
> Highlights are computed for standard web pages. PDFs and other non-HTML documents are still fetched and their text returned, but `highlights` is not computed for them — the field is absent on those results.

***

## Response

```json theme={null}
{
  "results": [...],
  "errors": [...]
}
```

### `results[]`

One entry per successfully fetched URL.

**url** `string`

The original requested URL.

**final\_url** `string`

The URL after any redirects. May differ from `url`.

**title** `string | null`

Page title, preferring `og:title` over `<title>`. `null` if not found.

**description** `string | null`

Meta description, preferring `og:description` over `<meta name="description">`. `null` if not found.

**language** `string | null`

Detected page language (e.g. `"en"`). `null` if undetectable.

**author** `string | null`

Author from meta tags. `null` if not found.

**published\_date** `string | null`

Publication date, if detectable. `null` if not found.

**text** `string | object | null`

Extracted page content. Format depends on the `format` request parameter:

* `string` when `format` is `"html"` or `"markdown"`
* `object` (document tree) when `format` is `"json"`
* `null` on a highlights request, unless `highlights.include_full_page_text: true`

**links** `string[]`

All `<a href>` URLs on the page, resolved to absolute URLs. Only present when `links: true` was requested.

**image\_links** `string[]`

All `<img src>` URLs on the page, resolved to absolute URLs. Only present when `image_links: true` was requested.

**iframe\_links** `string[]`

`<iframe src>` URLs on the page, resolved to absolute URLs and deduplicated, in document order. Only present when `iframe_links: true` was requested.

**not\_modified** `boolean (optional)`

Present and `true` only when the origin returned `304 Not Modified` for your `if_none_match` or `if_modified_since` header — the content is unchanged and you can skip re-processing. Omitted otherwise.

**etag** `string (optional)`

The origin's current ETag validator. Save it and replay it as `if_none_match` on your next fetch of this URL. Present only when the origin sent one and you set `include_etag_and_last_modified`; omitted otherwise.

**last\_modified** `string (optional)`

The origin's current Last-Modified validator. Save it and replay it as `if_modified_since` on your next fetch of this URL. Present only when the origin sent one and you set `include_etag_and_last_modified`; omitted otherwise.

**unmatched\_selectors** `string[] (optional)`

Partial-miss report for `include_selectors`: the entries that matched no elements on this page. Present only when some (but not all) entries matched — the result still carries the matched content. Omitted when every entry matched. A total miss is reported as a `selector_not_matched` entry in `errors[]` instead.

**highlights** `object[] (optional)`

Ranked verbatim passages answering the request's `highlights.query`, best first. Each entry is `{ "text": string, "rank": integer }`, with `rank` starting at `1`. Present only on highlights requests.

An **empty array** means the page was fetched and analyzed and does not answer the query — a deliberate, calibrated signal, not a failure. A **missing field** on a highlights request means highlights could not be computed for this URL (rare and transient); the fetch itself still succeeded, and a retry is safe.

**latency\_ms** `number | null`

Time to fetch and extract this URL, in milliseconds. `null` if unavailable.

**format** `string`

Output format used for the `text` field. Echoes the request `format` parameter (`"markdown"`, `"html"`, or `"json"`).

> [!NOTE]
>
> Fields that could not be extracted (`title`, `description`, `language`, `author`, `published_date`) are returned as `null`.

### `errors[]`

One entry per URL that could not be fetched. Always present, may be empty. Per-URL failures do not affect the rest of the batch.

**url** `string`

The URL that failed.

**error** `string`

Structured error code identifying the failure type. One of: `target_http_error`, `page_not_found`, `target_unreachable`, `timeout`, `bot_blocked`, `empty_content`, `login_required`, `content_too_large`, `invalid_url`, `invalid_redirect_url`, `proxy_error`, `conditional_unsupported`, `selector_not_matched`, `selector_unsupported`.

**status** `number (optional)`

Upstream HTTP status code. Present when `error` is `target_http_error` or `page_not_found`.

**unmatched\_selectors** `string[] (optional)`

The `include_selectors` entries that matched no elements on the fetched page. Present only when `error` is `selector_not_matched`.

**candidate\_selectors** `string[] (optional)`

Cheap retry hints (max 10), present only when `error` is `selector_not_matched`: landmark tags found on the page (e.g. `main`, `article`, `nav`) plus `#id` selectors of content-heavy elements. Agents can retry the fetch with `include_selectors` drawn from this list.

## SDK Methods

```python Python theme={null}
from tinyfish import TinyFish

client = TinyFish()
result = client.fetch.get_contents(
    urls=["https://www.tinyfish.ai/"],
    format="markdown",
)
for page in result.results:
    print(page.title, "→", page.text[:100])
```

```typescript TypeScript theme={null}
import { TinyFish } from "@tiny-fish/sdk";

const client = new TinyFish();
const result = await client.fetch.getContents({
  urls: ["https://www.tinyfish.ai/"],
  format: "markdown",
});
result.results.forEach((page) => console.log(page.title, "→", page.text.slice(0, 100)));
```

***

## Error Codes

HTTP-level errors apply to the entire request.

| Status | Meaning |
| - | - |
| `400` | Invalid request — missing `urls`, too many URLs (max 10), bad parameter value, `if_none_match`/`if_modified_since` combined with a batch of URLs, or `highlights` combined with a non-markdown `format` |
| `401` | Missing or invalid API key |
| `402` | Daily free allowance used and wallet balance is zero or below (`INSUFFICIENT_CREDITS`) — add funds at the [wallet page](https://agent.tinyfish.ai/wallet) or wait for the daily reset. `FREE_ALLOWANCE_EXHAUSTED` when the allowance is used and the product does not charge the wallet (beta) — wait for the daily reset |
| `403` | `highlights` sent from an account that isn't beta-enabled — contact support for access |
| `422` | Invalid CSS selector syntax in `include_selectors` / `exclude_selectors` |
| `429` | Rate limit exceeded |
| `500` | Internal server error |
| `503` | Fetch service or rate limiting unavailable — retry with backoff |

Per-URL errors appear in `errors[]` alongside a `200` response. The `error` field is one of these codes:

| Error code | `status` field | Meaning |
| - | - | - |
| `target_http_error` | HTTP status code (e.g. `403`, `500`) | Target server returned a non-2xx HTTP response other than 404/410 |
| `page_not_found` | `404` or `410` | Target URL does not exist (HTTP 404 Not Found or 410 Gone) |
| `target_unreachable` | — | Connection refused, TLS failure, DNS failure, or other network error |
| `timeout` | — | Page did not finish loading within the request deadline |
| `bot_blocked` | — | Site returned a bot-protection challenge (Cloudflare, Incapsula) |
| `empty_content` | — | Browser returned HTML but no extractable text found |
| `login_required` | — | Target redirected to a login or account wall — the page is not served to anonymous sessions, so retrying without credentials won't help |
| `content_too_large` | — | Document exceeds the 20MB size limit for generic documents (PDF and CSV have their own 50MB budgets); not retried in the browser |
| `invalid_url` | — | URL rejected before fetch (private IP, invalid scheme, disallowed host) |
| `invalid_redirect_url` | — | Redirect target rejected before fetch (private IP or disallowed host) |
| `proxy_error` | — | Proxy tunnel failed — site may be reachable directly |
| `conditional_unsupported` | — | URL requires browser rendering — conditional requests (`if_none_match` / `if_modified_since`) are supported on the fast path only |
| `selector_not_matched` | — | No elements matching any `include_selectors` entry remained after `exclude_selectors` was applied (total miss); the error carries `unmatched_selectors` + `candidate_selectors` retry hints. A partial miss is not an error — it's reported on the result's `unmatched_selectors` |
| `selector_unsupported` | — | `include_selectors` / `exclude_selectors` sent for a URL that resolves to a direct PDF/CSV download — no HTML to scope |

> [!NOTE]
>
> Per-URL fetch failures are **not** HTTP errors. They appear as entries in `errors[]` alongside a `200` response.

> [!NOTE]
>
> Each URL has a **110-second backend timeout**. If the page doesn't respond within 110 seconds, that URL returns a `timeout` error in `errors[]` while the rest of the batch continues. Requests are also subject to a **120-second CDN ceiling** for the full batch. Set your client-side timeout to at least **150 seconds** to receive CDN timeout errors cleanly.

***

## Supported Content Types

| Content Type | Behavior |
| - | - |
| HTML | Full text extraction with formatting |
| PDF | Text content extracted |
| JSON | Raw JSON returned as text |
| Plain text | Full text returned |
| Images (PNG, JPG) | Not supported — returns an error indicating no extractable content |

***

## Usage Endpoint

Retrieve a paginated history of your fetch operations.

```
GET https://api.fetch.tinyfish.ai/usage
```

All requests require an `X-API-Key` header. See [Authentication](/authentication).

### Query Parameters

**start\_after** `string (ISO 8601)`

Filter results created after this timestamp. Example: `2026-01-01T00:00:00Z`

**end\_before** `string (ISO 8601)`

Filter results created before this timestamp. Example: `2026-02-01T00:00:00Z`

**status** `string`

Filter by result status. One of: `completed`, `failed`.

**limit** `integer` (default: 100)

Maximum number of items per page. Range: 1-1000.

**page** `integer` (default: 1)

Page number for pagination.

### Response

```json theme={null}
{
  "items": [...],
  "total": 42,
  "limit": 100,
  "page": 1,
  "total_pages": 1,
  "has_more": false
}
```

### `items[]`

**id** `string`

Unique identifier for the fetch result.

**url** `string`

The original requested URL.

**final\_url** `string`

The URL after any redirects.

**title** `string | null`

Page title, if detected.

**description** `string | null`

Meta description, if detected.

**language** `string | null`

Detected page language (e.g. `"en"`).

**author** `string | null`

Page author, if detected.

**published\_date** `string | null`

Published date, if detected.

**format** `string`

The format used for extraction: `markdown`, `html`, or `json`.

**status** `string`

Result status: `completed` or `failed`.

**request\_origin** `string`

Where the request originated: `api`, `cli`, `python-sdk`, `js-sdk`, `mcp`, etc.

**request\_id** `string | null`

The request ID that grouped this URL with others in a batch.

**text\_length** `integer | null`

Length of the extracted text content in characters. The full text is not included in usage responses.

**links\_count** `integer`

Number of links found on the page.

**image\_links\_count** `integer`

Number of image links found on the page.

**latency\_ms** `number | null`

Time taken to fetch and extract the page, in milliseconds.

**not\_modified** `boolean (optional)`

Present and `true` only when that fetch was a conditional request that returned `304 Not Modified`. Omitted otherwise.

**etag** `string (optional)`

The origin's ETag validator captured at fetch time. Present only when `include_etag_and_last_modified` was set on that request and the origin returned one; omitted otherwise.

**last\_modified** `string (optional)`

The origin's Last-Modified validator captured at fetch time. Present only when `include_etag_and_last_modified` was set on that request and the origin returned one; omitted otherwise.

**created\_at** `string (ISO 8601)`

Timestamp when the fetch was executed.

**error** `string | null`

Error message if the fetch failed. `null` for successful fetches.

### Error Codes

| Status | Meaning |
| - | - |
| `400` | Invalid query parameters |
| `401` | Missing or invalid API key |
| `500` | Internal server error |

***

## Rate Limits

Limits apply per API key, measured in URLs per minute across all requests. Accounts default to 150 URLs / minute. When the limit is exceeded, the API returns `HTTP 429`.

***

## Billing

Fetch is free up to 1,000 URLs per day, counted per successfully fetched URL; the allowance resets at 00:00 UTC. Beyond it, requests need a positive wallet balance: with a balance of zero or below the API returns `HTTP 402` with code `INSUFFICIENT_CREDITS` until you add funds or the allowance resets. After a top-up, allow a few seconds for the balance to apply. A product that does not charge the wallet (beta) returns `FREE_ALLOWANCE_EXHAUSTED` instead once its allowance is used; only the daily reset lifts it.

***

## Related

> **[Fetch Overview](/fetch-api)**
>
> First request, response shape, and product routing

> **[Authentication](/authentication)**
>
> API key setup and troubleshooting

> **[Error Codes](/error-codes)**
>
> Full list of API error codes


This documentation is built and hosted on [Mintlify](https://mintlify.com), a developer documentation platform.