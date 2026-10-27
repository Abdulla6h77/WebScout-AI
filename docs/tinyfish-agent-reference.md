> ## Documentation Index
> Fetch the complete documentation index at: https://docs.tinyfish.ai/llms.txt
> Use this file to discover all available pages before exploring further.

# Agent API Reference

> Technical reference for goal-based TinyFish automation

## Endpoints

| Endpoint | Method | Returns | Cancel support |
| - | - | - | - |
| `https://agent.tinyfish.ai/v1/automation/run` | `POST` | Final run result | No |
| `https://agent.tinyfish.ai/v1/automation/run-async` | `POST` | `run_id` immediately | Yes |
| `https://agent.tinyfish.ai/v1/automation/run-sse` | `POST` | SSE event stream | Yes |

All requests require the `X-API-Key` header. See [Authentication](/authentication).

## Common Request Body

All three automation endpoints accept the same JSON body.

```json theme={null}
{
  "url": "https://example.com",
  "goal": "Find the pricing page and extract all plan details",
  "output_schema": {
    "type": "object",
    "properties": {
      "title": { "type": "string" },
      "price": { "type": "number" }
    },
    "required": ["title", "price"]
  },
  "browser_profile": "lite",
  "proxy_config": {
    "enabled": true,
    "type": "tinyfish",
    "country_code": "US"
  },
  "agent_config": {
    "mode": "strict",
    "max_steps": 50,
    "max_duration_seconds": 300
  },
  "webhook_url": "https://example.com/webhooks/tinyfish",
  "use_profile": true,
  "profile_id": "prof_abc123def4567890",
  "use_vault": true,
  "credential_item_ids": ["cred:a1b2c3d4:Work:item-xyz"]
}
```

| Field | Type | Required | Notes |
| - | - | - | - |
| `url` | `string` | Yes | Target website URL to automate |
| `goal` | `string` | Yes | Natural-language instruction for the automation |
| `output_schema` | `object` | No | Structured-output schema subset for the run result. Unsupported fields are rejected before execution. See [Structured Output](/key-concepts/structured-output) |
| `browser_profile` | `lite \| stealth` | No | Defaults to `lite` |
| `proxy_config.enabled` | `boolean` | No | Enables proxying for the run |
| `proxy_config.type` | `tinyfish \| custom` | No | `tinyfish` (default) uses the built-in TinyFish proxy; `custom` requires your own proxy URL |
| `proxy_config.country_code` | `string` | No | Any ISO 3166-1 alpha-2 code (e.g. `US`, `IN`). Used with `type: "tinyfish"`. Defaults to `US` |
| `proxy_config.url` | `string` | No | Required when `type: "custom"` |
| `proxy_config.username` | `string` | No | Custom proxy username |
| `proxy_config.password` | `string` | No | Custom proxy password |
| `agent_config.mode` | `default \| strict` | No | Beta-gated. Use `strict` for fail-fast automation where the agent should stop instead of exploring workarounds |
| `agent_config.max_steps` | `integer` | No | Beta-gated. Optional run step limit from 1 to 500. Omit the field to use EVA's default of 150 |
| `agent_config.max_duration_seconds` | `integer` | No | Maximum wall-clock seconds before the agent stops. Defaults to no limit |
| `webhook_url` | `string` | No | HTTPS URL to receive run lifecycle notifications. Must use `https://`. See [Webhooks](/webhooks) |
| `capture_config` | `object` | No | Opt into extra run artifacts (`screenshots`, `recording`, `html`, `snapshots`, `elements`). Account-gated — returns `403` if your account is not enabled for a requested capability |
| `use_profile` | `boolean` | No | Use the default saved [Browser Context Profile](/key-concepts/browser-context-profiles) for this run |
| `profile_id` | `string` | No | Select a specific Browser Context Profile. Requires `use_profile: true` |
| `use_vault` | `boolean` | No | Enable [vault credentials](/key-concepts/credentials) for this run. When `true`, TinyFish can log into sites using your connected password manager |
| `credential_item_ids` | `string[]` | No | Scope the run to specific credential URIs from `GET /v1/vault/items`. Requires `use_vault: true`. If omitted, all synced items are available |

> [!NOTE]
>
> **Beta:** `agent_config.mode: "strict"` is in beta — you must join the beta to use it (contact support to
> enable it for your account). Strict mode is best for
> precise tests and automations where unexpected page state should stop the run quickly instead of
> trying alternate paths.

> [!NOTE]
>
> **Beta:** `agent_config.max_steps` is available only to beta-enabled users. Use it when a run
> needs a shorter or longer step budget than EVA's default. Non-beta API requests that include
> `max_steps` return `403 FORBIDDEN`; requests without the field are unaffected.

> [!NOTE]
>
> Use `use_profile: true` for your default Browser Context Profile. Add `profile_id` when the run must use a
> specific saved profile. Create and set up profiles from the dashboard or the
> [Browser Context Profiles API](/agent-api/browser-context-profiles).

See [Structured Output](/key-concepts/structured-output) for the supported keyword allowlist, size and depth limits, and common rewrites for invalid schemas.

See [Browser Context Profiles](/key-concepts/browser-context-profiles), [Browser Context Profiles API](/agent-api/browser-context-profiles), [Browser Profiles](/key-concepts/browser-profiles), [Proxies](/key-concepts/proxies), and [Vault Credentials](/key-concepts/credentials) for operational guidance.

## `POST /v1/automation/run`

Use this endpoint when you want the final result in one blocking response.

```json theme={null}
{
  "run_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "COMPLETED",
  "started_at": "2024-01-01T00:00:00Z",
  "finished_at": "2024-01-01T00:00:30Z",
  "num_of_steps": 5,
  "result": {
    "product": "iPhone 15",
    "price": "$799"
  },
  "error": null
}
```

| Field | Type | Notes |
| - | - | - |
| `run_id` | `string \| null` | Unique identifier for the run |
| `status` | `COMPLETED \| FAILED` | Final run state |
| `started_at` | `string \| null` | ISO 8601 timestamp |
| `finished_at` | `string \| null` | ISO 8601 timestamp |
| `num_of_steps` | `number \| null` | Number of steps taken |
| `result` | `object \| null` | Extracted JSON result |
| `error` | `object \| null` | Present only when the run failed |

Runs created via `/run` cannot be cancelled.

## `POST /v1/automation/run-async`

Use this endpoint when you want a `run_id` immediately and will fetch the full run later.

```json theme={null}
{
  "run_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "error": null
}
```

| Field | Type | Notes |
| - | - | - |
| `run_id` | `string \| null` | Created run ID |
| `error` | `object \| null` | Present only when run creation failed |

Fetch the full run state later with `GET /v1/runs/{id}`.

## `POST /v1/automation/run-sse`

Use this endpoint when you want a streaming event feed while the automation runs.

Possible SSE event types:

| Event type | Fields |
| - | - |
| `STARTED` | `type`, `run_id`, `timestamp` |
| `STREAMING_URL` | `type`, `run_id`, `streaming_url`, `timestamp` |
| `PROGRESS` | `type`, `run_id`, `purpose`, `timestamp` |
| `HEARTBEAT` | `type`, `timestamp` |
| `COMPLETE` | `type`, `run_id`, `status`, `result?`, `error?`, `timestamp` (on failure, `error` carries `help_url` / `help_message`) |

Example stream:

```text theme={null}
data: {"type":"STARTED","run_id":"run_123","timestamp":"2025-01-01T00:00:00Z"}

data: {"type":"STREAMING_URL","run_id":"run_123","streaming_url":"https://...","timestamp":"..."}

data: {"type":"PROGRESS","run_id":"run_123","purpose":"Clicking submit button","timestamp":"..."}

data: {"type":"COMPLETE","run_id":"run_123","status":"COMPLETED","result":{...},"timestamp":"..."}
```

> [!NOTE]
>
> **Reconnection:** SSE streams do not support `Last-Event-ID` reconnection. If your client disconnects mid-stream, recover by polling `GET /v1/runs/{run_id}` until the run reaches a terminal status (`COMPLETED`, `FAILED`, or `CANCELLED`).

### Raw HTTP (no SDK)

Parse SSE events directly without the TinyFish SDK:

```python theme={null}
import os
import httpx
import json

url = "https://agent.tinyfish.ai/v1/automation/run-sse"
headers = {"X-API-Key": os.environ["TINYFISH_API_KEY"]}
payload = {"url": "https://example.com", "goal": "Extract the page title"}

with httpx.stream("POST", url, headers=headers, json=payload, timeout=120) as response:
    for line in response.iter_lines():
        if line.startswith("data: "):
            event = json.loads(line[6:])
            print(f"Event: {event['type']}")
            if event["type"] == "COMPLETE":
                print(f"Result: {event.get('result', {})}")
```

## `GET /v1/runs/{id}`

Use this endpoint to retrieve the current or final state of an async or streaming run.

| Field | Type | Notes |
| - | - | - |
| `run_id` | `string` | Unique run identifier |
| `status` | `PENDING \| RUNNING \| COMPLETED \| FAILED \| CANCELLED` | Current run state |
| `goal` | `string` | Original goal text |
| `created_at` | `string` | ISO 8601 timestamp |
| `started_at` | `string \| null` | ISO 8601 timestamp |
| `finished_at` | `string \| null` | ISO 8601 timestamp |
| `num_of_steps` | `integer \| null` | Number of steps taken |
| `result` | `object \| null` | Extracted JSON result |
| `error` | `object \| null` | Error details if failed |
| `profile_attached` | `boolean` | Whether a Browser Context Profile was attached to the run |
| `profile_id` | `string \| null` | ID of the attached Browser Context Profile, if any. Both profile fields are omitted when an organization workflow key reads a run that used a profile |
| `streaming_url` | `string \| null` | Live browser stream URL while running |
| `browser_config` | `object \| null` | Proxy settings used for the run |
| `video_url` | `string \| null` | Presigned run recording URL, if available |
| `output_schema` | `object \| null` | Structured-output schema originally requested for the run |
| `steps` | `array` | Recorded step events for the run |

`error` may include:

| Field | Type | Notes |
| - | - | - |
| `code` | `string` | Machine-readable error code |
| `message` | `string` | Human-readable failure description |
| `category` | `SYSTEM_FAILURE \| AGENT_FAILURE \| BILLING_FAILURE \| UNKNOWN` | Error class |
| `retry_after` | `number \| null` | Suggested retry delay in seconds |
| `help_url` | `string` | Troubleshooting link |
| `help_message` | `string` | Human-readable guidance |

## `POST /v1/runs/{id}/cancel`

Only runs created via `/run-async` or `/run-sse` can be cancelled.

```json theme={null}
{
  "run_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "CANCELLED",
  "cancelled_at": "2026-01-14T10:30:55Z",
  "message": null
}
```

| Field | Type | Notes |
| - | - | - |
| `run_id` | `string` | Run identifier |
| `status` | `CANCELLED \| COMPLETED \| FAILED` | Actual status after the cancel attempt |
| `cancelled_at` | `string \| null` | ISO 8601 timestamp |
| `message` | `string \| null` | Idempotency or terminal-state message |

## Error Codes

Common HTTP-level errors across automation endpoints:

| Status | Code | Meaning |
| - | - | - |
| `400` | `INVALID_INPUT` | Invalid request body or missing required fields |
| `401` | `MISSING_API_KEY`, `INVALID_API_KEY` | Missing or invalid API key |
| `401` | `VAULT_RECONNECT_REQUIRED` | Reconnect the affected vault provider, then retry; see [error recovery](/error-codes) |
| `403` | `FORBIDDEN` | Access denied |
| `429` | `RATE_LIMIT_EXCEEDED` | Rate limit exceeded |
| `500` | `INTERNAL_ERROR` | Internal server error |

The `COMPLETE` SSE event or `GET /v1/runs/{id}` may also include run-level failures such as `TASK_FAILED`, `SITE_BLOCKED`, `MAX_STEPS_EXCEEDED`, `TIMEOUT`, or `BILLING_REJECTED`.

## Related

> **[Agent overview](/agent-api)**
>
> First request, endpoint selection, and goal-writing basics

> **[Structured Output](/key-concepts/structured-output)**
>
> Schema support, limits, and common rewrites

> **[Runs](/key-concepts/runs)**
>
> Statuses, polling, and lifecycle behavior

> **[Goal prompting guide](/prompting-guide)**
>
> Improve automation reliability

> **[Authentication](/authentication)**
>
> API key setup and troubleshooting

> **[Vault Credentials](/key-concepts/credentials)**
>
> Use password manager credentials in runs

> **[Browser Context Profiles](/key-concepts/browser-context-profiles)**
>
> Reuse saved logged-in browser state


This documentation is built and hosted on [Mintlify](https://mintlify.com), a developer documentation platform.