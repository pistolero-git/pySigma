# pySigma API

Small HTTP service for **Sigma validation and pySigma conversion**. It intentionally contains no CVE, AI, or research logic.

## API

- `GET /health`
- `GET /api/v1/catalog`
- `GET /api/v1/backends`
- `GET /api/v1/pipelines`
- `GET /api/v1/formats/{backend}`
- `POST /api/v1/validate`
- `POST /api/v1/convert`
- Swagger UI: `/docs`
- ReDoc: `/redoc`

Built-in backend IDs:

| ID | Target | Formats |
|---|---|---|
| `splunk` | Splunk SPL | `default`, `savedsearches` |
| `elasticsearch` | Elasticsearch Lucene | `default` |
| `opensearch` | OpenSearch Lucene | `default`, `monitor_rule`, `dsl_lucene` |
| `opensearch-ppl` | OpenSearch PPL | `default` |

Built-in pipeline IDs: `splunk_windows`, `ecs_windows`, `sysmon`.

## Compatibility note

The dependency set is intentionally pinned to **pySigma 1.5.1** plus compatible backend/plugin releases. pySigma 2.0.0 was released on October 4, 2026, but the current OpenSearch backend release still declares `pysigma >=1.4,<2.0`. This avoids installing an incompatible mixed plugin set.

## Build with Podman or Docker

```bash
podman build -t localhost/pysigma-api:latest .
podman run --rm --name pysigma-api -p 8001:8000 localhost/pysigma-api:latest
```

Then open `http://HOST:8001/docs`.

Docker works with the same Dockerfile by replacing `podman` with `docker`.

## Validate

```bash
curl -sS http://127.0.0.1:8001/api/v1/validate \
  -H 'Content-Type: application/json' \
  --data-binary "$(python3 - <<'PY'
import json

with open("example-rule.yml") as f:
    print(json.dumps({"sigma": f.read()}))
PY
)" | jq
```

## Convert to Splunk

```bash
python - <<'PY' >/tmp/request.json
import json
print(json.dumps({
    'sigma': open('example-rule.yml').read(),
    'backend': 'splunk',
    'pipelines': ['splunk_windows'],
    'format': 'default'
}))
PY

curl -s http://localhost:8001/api/v1/convert \
  -H 'Content-Type: application/json' \
  --data-binary @/tmp/request.json | jq
```

## Convert to OpenSearch PPL

Change the request fields to:

```json
{
  "backend": "opensearch-ppl",
  "pipelines": [],
  "format": "default"
}
```

## Backend options

`backend_options` is passed as keyword arguments to the selected pySigma backend. This is useful for backend-specific settings such as OpenSearch indices:

```json
{
  "backend": "opensearch",
  "pipelines": ["ecs_windows"],
  "format": "monitor_rule",
  "backend_options": {
    "index_names": ["logs-*-*", "beats-*"]
  }
}
```

Only expose this API to trusted applications if you allow arbitrary backend options.

## Optional API key

Set:

```bash
PYSIGMA_API_KEY='a-long-random-secret'
```

Clients must then send:

```text
X-API-Key: a-long-random-secret
```

`/health` remains unauthenticated for container health checks.

## CORS

Default: all origins.

For a production website:

```bash
PYSIGMA_CORS_ORIGINS='https://detections.example.com,https://admin.example.com'
```

## Rootless Podman Quadlet

Build the image first, then copy `pysigma-api.container` to:

```text
~/.config/containers/systemd/pysigma-api.container
```

Run:

```bash
systemctl --user daemon-reload
systemctl --user enable --now pysigma-api.service
```

## Local development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
uvicorn app.main:app --reload
```

## Design boundary

The service does exactly this:

```text
Sigma YAML -> parse/validate -> processing pipeline(s) -> pySigma backend -> output
```

CVE enrichment, LLM generation, proof-of-concept analysis, and frontend logic belong in the calling application.
