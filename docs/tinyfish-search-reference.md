> ## Documentation Index
> Fetch the complete documentation index at: https://docs.tinyfish.ai/llms.txt
> Use this file to discover all available pages before exploring further.

# Search API Reference

> Complete reference for the Search API endpoint

## Endpoint

```
GET https://api.search.tinyfish.ai
```

All requests require an `X-API-Key` header. See [Authentication](/authentication).

***

## Request

```
GET https://api.search.tinyfish.ai?query=web+automation+tools&location=US&language=en
```

### Parameters

**query** `string` *required*

The search query string. **Deprecated for domain filtering:** the query string still
accepts `site:`/`-site:` operators (e.g. `python tutorial site:docs.python.org` or
`recipe ideas -site:facebook.com -site:youtube.com`), but prefer the dedicated
`include_domains` / `exclude_domains` params below — they don't collide with other
query syntax.

**purpose** `string`

An optional short statement of **why** you are searching — the underlying goal or task the
results will be used for. A query is often a terse set of keywords; supplying the intent behind
it gives us additional signal to further inform and deliver better-quality results. When omitted,
search behaves exactly as before. Maximum 2000 characters. For example,
`Find an open-source library for parsing PDF invoices in Python`.

**location** `string`

Country code for geo-targeted results (e.g. `US`, `GB`, `FR`, `DE`). When omitted, auto-resolves based on `language` (e.g. `fr` → `FR`). Defaults to `US` if both `location` and `language` are omitted.

**language** `string`

Language code for result language (e.g. `en`, `fr`, `de`). When omitted, auto-resolves based on `location` (e.g. `FR` → `fr`). Defaults to `en` if both `location` and `language` are omitted.

**include\_domains** `string`

Comma-separated list of domains to restrict results to (e.g. `github.com,arxiv.org`).

**exclude\_domains** `string`

Comma-separated list of domains to exclude from results (e.g. `pinterest.com,quora.com`).

**recency\_minutes** `number`

Freshness window in minutes. Must be an integer from `1` to `5256000` (10 years). Use this when you want recent results relative to now, such as `60` for the last hour.

**after\_date** `string`

Lower date bound in `YYYY-MM-DD` format. Use this when you want results after a calendar date cutoff, such as `2026-06-01`.

**before\_date** `string`

Upper date bound in `YYYY-MM-DD` format. Use this when you want results before a calendar date cutoff, such as `2026-06-18`.

**domain\_type** `string`

Type of search to perform. One of `"web"` (default), `"news"`, or `"research_paper"`. Use `"news"` to retrieve recent news articles with publisher and date; use `"research_paper"` to search academic papers with authors, venue, and citation count.

**pub\_year\_min** `number`

Lower publication-year bound, inclusive. Must be an integer from `0` to `9999`, and no greater than `pub_year_max` if both are set. Only supported for `domain_type=research_paper`.

**pub\_year\_max** `number`

Upper publication-year bound, inclusive. Must be an integer from `0` to `9999`, and no less than `pub_year_min` if both are set. Only supported for `domain_type=research_paper`.

**page** `number`

Page number for pagination, starting from `0` (e.g. `2` to retrieve the third page of results). Maximum value is `10`.

> [!NOTE]
>
> **Freshness and date filter rules:** `recency_minutes` cannot be combined with `after_date` or `before_date`. If you send both `after_date` and `before_date`, they must be valid `YYYY-MM-DD` values and `after_date` must be less than or equal to `before_date`.

> [!NOTE]
>
> **Research paper date restrictions:** `after_date`, `before_date`, and `recency_minutes` are not supported for `domain_type=research_paper`. Use `pub_year_min` / `pub_year_max` to scope by publication year instead (e.g. `pub_year_min=2017&pub_year_max=2017`).

> [!NOTE]
>
> **Location & language auto-resolution:** If only one of `location` or `language` is provided, the other is automatically resolved to the most predominant pairing. For example, setting `location=BR` without `language` resolves to `language=pt`. Setting `language=ja` without `location` resolves to `location=JP`. If neither is set, they default to `US` and `en`.

***

## Response

```json theme={null}
{
  "query": "web automation tools",
  "results": [...],
  "total_results": 10,
  "page": 0
}
```

### Top-level fields

**query** `string`

The search query that was executed.

**results** `object[]`

Array of search results.

**total\_results** `number`

Total number of results returned.

**page** `number`

The current page number, starting from `0`.

### `results[]`

**position** `number`

Position in search results (1-indexed).

**site\_name** `string`

Domain name of the result.

**title** `string`

Page title.

**snippet** `string`

Text snippet from the result.

**url** `string`

URL of the result.

**date** `string`

Publication date. Present for news results and some web results.

**publisher** `string`

Publisher name. Present for news results (`domain_type=news`).

**authors** `string[]`

Author list. Present for academic results (`domain_type=research_paper`).

**venue** `string`

Journal or conference name. Present for academic results (`domain_type=research_paper`).

**year** `number`

Publication year. Present for academic results (`domain_type=research_paper`).

**cited\_by\_count** `number`

Citation count. Present for academic results (`domain_type=research_paper`).

**pdf\_url** `string`

PDF URL. Present for academic results when a PDF is available (`domain_type=research_paper`).

## SDK Methods

```python Python theme={null}
from tinyfish import TinyFish

client = TinyFish()
response = client.search.query(query="web automation tools", location="US")
for r in response.results:
    print(r.title, "→", r.url)
```

```typescript TypeScript theme={null}
import { TinyFish } from "@tiny-fish/sdk";

const client = new TinyFish();
const response = await client.search.query({
  query: "web automation tools",
  location: "US",
});
response.results.forEach((r) => console.log(r.title, "→", r.url));
```

***

## Error Codes

| Status | Meaning |
| - | - |
| `400` | Invalid request — missing `query` parameter or bad parameter value |
| `401` | Missing or invalid API key |
| `402` | Daily free allowance used and wallet balance is zero or below (`INSUFFICIENT_CREDITS`) — add funds at the [wallet page](https://agent.tinyfish.ai/wallet) or wait for the daily reset. `FREE_ALLOWANCE_EXHAUSTED` when the allowance is used and the product does not charge the wallet (beta) — wait for the daily reset |
| `403` | Search request forbidden by the upstream service |
| `404` | Search API is not available |
| `429` | Rate limit exceeded |
| `500` | Internal server error |
| `503` | Search service or rate limiting unavailable — retry with backoff |

## Rate Limits

Limits apply per API key, measured in requests per minute across all requests. Accounts default to 30 requests / minute. When the limit is exceeded, the API returns `HTTP 429`.

***

## Billing

Search is free up to 12,000 requests per day; the allowance resets at 00:00 UTC. Beyond it, requests need a positive wallet balance: with a balance of zero or below the API returns `HTTP 402` with code `INSUFFICIENT_CREDITS` until you add funds or the allowance resets. After a top-up, allow a few seconds for the balance to apply. A product that does not charge the wallet (beta) returns `FREE_ALLOWANCE_EXHAUSTED` instead once its allowance is used; only the daily reset lifts it.

***

## Related

> **[Search Overview](/search-api)**
>
> First request, success shape, and product routing

> **[Authentication](/authentication)**
>
> API key setup and troubleshooting

> **[Error Codes](/error-codes)**
>
> Full list of API error codes


This documentation is built and hosted on [Mintlify](https://mintlify.com), a developer documentation platform.