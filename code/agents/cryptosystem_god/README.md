## Cryptosystem God Stack

This workspace bundles multiple ciphertext-detection agents and exposes them through a unified gateway so a single HTTP request fans out to specialised backends (CyberChef wrapper, dcode.fr heuristics, etc.).

### Components

- `cyberchef/` – wraps CyberChef's Magic detector in an HTTP API (`POST /detect` on port 8080).
- `dcode_fr/` – heuristics inspired by dcode.fr's cipher identifier (`POST /detect` on port 8081).
- `aggregator/` – gateway that calls every agent and merges their responses (`POST /detect` on port 8090).

### Running with Docker Compose

```bash
docker compose up --build
```

This starts three containers. Host port mappings:

- CyberChef API → `http://127.0.0.1:18080/detect`
- dcode.fr heuristics → `http://127.0.0.1:18081/detect`
- Gateway (fan-out endpoint) → `http://127.0.0.1:18090/detect`

Example gateway request:

```bash
curl -s http://127.0.0.1:18090/detect \
  -H 'content-type: application/json' \
  -d '{"input":"U0FMVVQ="}' | jq
```

Sample response (trimmed):

```json
{
  "input": "U0FMVVQ=",
  "operation": "detect",
  "agents": [
    { "name": "cyberchef", "ok": true, "status": 200, "data": { "...": "..." } },
    { "name": "dcode_fr", "ok": true, "status": 200, "data": { "...": "..." } }
  ],
  "meta": { "totalAgents": 2, "successfulAgents": 2 }
}
```

### Configuration Notes

- Override per-agent endpoints via environment variables (`CYBERCHEF_URL`, `DCODE_URL`, …) on the gateway container.
- Adjust fan-out timeout with `REQUEST_TIMEOUT_MS` (defaults to 3.5 s).
- Each agent directory contains its own README with standalone usage instructions.
