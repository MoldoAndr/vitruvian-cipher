# Password Strength Components

This workspace bundles three independent password strength components and an aggregator service that blends their results. Every component exposes a simple FastAPI endpoint so you can run them individually or orchestrate them together with Docker Compose.

## Components

1. **PassGPT** (`PassGPT/service`)
   - Loads the PassGPT language model and scores passwords by their log-probability under the model.
   - Endpoint: `POST /score` → `{ "password": "..." }`.
   - Response includes the normalized score (1–100), log-probability details, and model metadata.
   - Configure with `PASS_GPT_MODEL_NAME` or `PASS_GPT_MODEL_PATH`, plus `PASS_GPT_MAX_PASSWORD_LENGTH`, `PASS_GPT_SCORE_SCALE`, and `PASS_GPT_DEVICE`. Gated Hugging Face models require `HUGGINGFACE_HUB_TOKEN`.

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
   - Endpoint: `POST /score` → `{ "password": "...", "components": ["pass_gpt", "zxcvbn"] }`.
   - If `components` is omitted, the aggregator uses the environment variable `ENABLED_COMPONENTS` (comma-separated, defaults to all three).
   - Combination rule:
     - 3 active components → average of all three (equivalent to ⅓ weight each).
     - 2 active components → average of the two (½ weight each).
     - 1 active component → that component’s result.
   - PassGPT is automatically disabled for passwords longer than 10 characters (configurable via `PASS_GPT_MAX_PASSWORD_LENGTH`); the overall score is re-normalized using the remaining components.
   - Aggregation tweaks improve reliability: when zxcvbn flags a very weak password, it is weighted more heavily, PassGPT is penalized if zxcvbn emits warnings, and short passwords (<8 chars) are capped at 60 by default. Tune with `PASS_SHORT_PASSWORD_LENGTH`, `PASS_SHORT_PASSWORD_MAX_SCORE`, `ZXCVBN_LOW_SCORE_THRESHOLD`, `PASS_GPT_WARNING_PENALTY`, `PASS_GPT_LOW_SCORE_PENALTY`, `PASS_GPT_LOW_WEIGHT`, and `ZXCVBN_LOW_WEIGHT`.

All services also expose a `GET /health` endpoint for readiness/liveness checks.

## Running components individually

Each service ships with a `__main__` guard so you can launch it with `uvicorn` directly:

```bash
# PassGPT service
cd PassGPT/service
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
export PASS_GPT_URL="http://localhost:8000/score"
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
  -d '{"password": "P@ssw0rd", "components": ["pass_gpt", "zxcvbn"]}' | jq
```

The response includes the blended score (1–100), the list of active components, and individual component payloads or errors for any that failed.

## Reliability checks

Run the built-in reliability script against a running aggregator:

```bash
python3 scripts/reliability_check.py --components pass_gpt,zxcvbn
```

Add `--with-hibp` to include a small HIBP sample, or `--components all` to use the aggregator defaults.

## Next steps

Use Docker (see `docker-compose.yml`) to spin up all services at once, override environment variables to enable/disable components globally, and integrate the aggregator into your broader application.
