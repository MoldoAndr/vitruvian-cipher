## Cryptosystem Gateway

This service provides a single `/detect` endpoint that forwards ciphertexts to every configured detection agent (CyberChef wrapper, dcode.fr heuristics, etc.) and returns their responses in a unified payload.

### Local development

```bash
npm install
npm run dev
# Gateway listens on http://127.0.0.1:8090 by default
```

Sample request:

```bash
curl -s http://127.0.0.1:8090/detect \
  -H 'content-type: application/json' \
  -d '{"input":"U0FMVVQ="}' | jq
```

Response structure:

```json
{
  "input": "U0FMVVQ=",
  "agents": [
    {
      "name": "cyberchef",
      "ok": true,
      "status": 200,
      "data": { "... trimmed ..." }
    },
    {
      "name": "dcode_fr",
      "ok": true,
      "status": 200,
      "data": { "... trimmed ..." }
    }
  ]
}
```

### Configuration

- Environment variables `CYBERCHEF_URL`, `DCODE_URL`, etc. can override default agent endpoints. See `src/agents.mjs` for the full list.
- Set `REQUEST_TIMEOUT_MS` to adjust per-agent timeout (defaults to 3500 ms).

### Docker usage

```bash
docker build -t cryptosystem-gateway .
docker run --rm -p 8090:8090 \
  -e CYBERCHEF_URL=http://host.docker.internal:8080/detect \
  -e DCODE_URL=http://host.docker.internal:8081/detect \
  cryptosystem-gateway
```

In compose setups the service expects the agent containers to share the same network so it can reach them via their service names.
