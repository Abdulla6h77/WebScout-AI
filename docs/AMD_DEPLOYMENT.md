# AMD deployment preparation

No external deployment was performed. No ROCm was installed on Windows. Official target
hardware/network and interface remain unknown. The Docker image was built locally and its
container `/health` and `/ready` endpoints were smoke-tested on 2026-10-27.

## Linux/CPU prototype

```sh
uv sync --frozen
cp .env.example .env
# Edit configuration and keys.
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Optional Chromium: `.venv/bin/python -m playwright install --with-deps chromium`.
Use a trusted Linux environment; installing system browser dependencies may need privileges.

## Container (when allowed)

From the project root:

```sh
docker build -f deployment/Dockerfile -t webscout-ai .
docker run --rm --env-file .env -p 127.0.0.1:8000:8000 webscout-ai
```

Dependencies are locked in uv.lock. Image runs as non-root, includes Chromium, and exposes /health.
Chromium and base-image builds need network access. Secrets are passed at runtime, never copied into
the image. Local CPU container execution passed; AMD/ROCm execution remains untested. Restrict outbound traffic to public HTTP(S) with
network-layer DNS/redirect enforcement; do not allow cloud metadata or local-network endpoints.

## If local AMD inference is required

Use a separate organizer-compatible Linux ROCm inference server with an OpenAI-compatible API.
Set `LLM_PROVIDER=local`, `LOCAL_BASE_URL`, and `LOCAL_MODEL`. Model discovery and structured output
must match this adapter; verify the actual model/server combination. This is an integration seam,
not a working bundled AMD inference deployment. GPU drivers, models and weights are not in the image.

If all external inference is forbidden, external providers must be disabled and local inference
validated first. If TinyFish is forbidden or unreachable, enable Playwright for website-specific
tasks. Open-web discovery then needs an organizer-approved search provider; this prototype does not
invent a keyless search fallback. Fully offline execution cannot answer current open-web questions
without organizer-provided snapshots or another permitted source.

## Grader integration

The internal JSON schema is documented at /docs; it is not the AMD schema. Replace AMDAdapter.decode/
encode once the official kit specifies files/stdin/HTTP, errors, timeouts, citation requirements and
entrypoint. Validate exact behavior on the supplied examples and record target results.
