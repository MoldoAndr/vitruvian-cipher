# Password Strength Components

This workspace bundles three independent password strength components and an aggregator service that blends their results. Every component exposes a simple FastAPI endpoint so you can run them individually or orchestrate them together with Docker Compose.

## Components

1. **PassStrengthAI** (`PassStrengthAI/service`)
   - Loads the pre-trained neural network model shipped with PassStrengthAI.
   - Endpoint: `POST /score` → `{ "password": "..." }`.
   - Response includes the normalized score (1–100), predicted class (0–4), and probability distribution.
   - Configure with `MODEL_PATH` to point at a different `.keras` model if required.

2. **zxcvbn** (`zxcvbn`)
   - Wraps the Dropbox zxcvbn estimator in a FastAPI service.
   - Endpoint: `POST /score` → `{ "password": "..." }`.
   - Returns the raw zxcvbn score (0–4), crack time estimates, and a normalized score.

3. **HaveIBeenPwned Range API** (`haveibeenpwned`)
   - Hashes the submitted password locally, then queries `https://api.pwnedpasswords.com/range/{prefix}` using the k-anonymity mechanism.
   - Caches range responses in-process for faster repeated lookups and retries transient network errors.
   - Configure with `HIBP_API_KEY` if you have a commercial key (optional), `HIBP_API_ROOT` for alternative endpoints, and timeout/retry knobs.

4. **Aggregator** (`aggregator`)
   - Fans out to the enabled components and combines their normalized scores.
   - Endpoint: `POST /score` → `{ "password": "...", "components": ["pass_strength_ai", "zxcvbn"] }`.
   - If `components` is omitted, the aggregator uses the environment variable `ENABLED_COMPONENTS` (comma-separated, defaults to all three).
   - Combination rule:
     - 3 active components → average of all three (equivalent to ⅓ weight each).
     - 2 active components → average of the two (½ weight each).
     - 1 active component → that component’s result.
   - PassStrengthAI is automatically disabled for passwords longer than 10 characters; the overall score is re-normalized using the remaining components.

All services also expose a `GET /health` endpoint for readiness/liveness checks.

## Running components individually

Each service ships with a `__main__` guard so you can launch it with `uvicorn` directly:

```bash
# PassStrengthAI service
cd PassStrengthAI/service
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000

# zxcvbn service
cd zxcvbn
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8001

# HaveIBeenPwned service
cd haveibeenpwned
pip install -r requirements.txt
export HIBP_API_KEY="<optional-api-key>"
export HIBP_API_ROOT="https://api.pwnedpasswords.com"
uvicorn app:app --host 0.0.0.0 --port 8002

# Aggregator service
cd aggregator
pip install -r requirements.txt
export PASS_STRENGTH_AI_URL="http://localhost:8000/score"
export ZXCVBN_URL="http://localhost:8001/score"
export HAVEIBEENPWNED_URL="http://localhost:8002/score"
uvicorn app:app --host 0.0.0.0 --port 9000
```

Send a password to any component:

```bash
curl -s http://localhost:8000/score -X POST -H "Content-Type: application/json" -d '{"password": "P@ssw0rd"}' | jq
```

For the aggregator, omit the `components` field to use the defaults or set a subset per request:

```bash
curl -s http://localhost:9000/score -X POST -H "Content-Type: application/json" \
  -d '{"password": "P@ssw0rd", "components": ["pass_strength_ai", "zxcvbn"]}' | jq
```

The response includes the blended score (1–100), the list of active components, and individual component payloads or errors for any that failed.

## Next steps

Use Docker (see `docker-compose.yml`) to spin up all services at once, override environment variables to enable/disable components globally, and integrate the aggregator into your broader application.
