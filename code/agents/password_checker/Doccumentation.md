https://huggingface.co/javirandor/passgpt-10characters
https://github.com/dropbox/zxcvbn
https://haveibeenpwned.com/API/v3
https://www.usenix.org/conference/usenixsecurity16/technical-sessions/presentation/wheeler

## Password Strength Ensemble

This workspace packages three complementary scoring engines behind FastAPI services and fans their outputs into a dedicated aggregator. Running the stack (locally or via Docker Compose) yields a composite password strength verdict that blends neural confidence, heuristic entropy analysis, and breach intelligence. Each component exposes `POST /score` and `GET /health`, so you can deploy them independently, layer them into other systems, or lean on the aggregator to orchestrate cross-checks.

### PassGPT Neural Model

The PassGPT component loads a GPT-2 style language model trained on leaked password distributions and computes the log-probability of each submitted password. That log-probability is mapped to a 1–100 score so that higher surprise (lower likelihood) yields a stronger rating. Requests longer than the configured maximum return HTTP 422, and the aggregator automatically skips PassGPT when passwords exceed the limit (default 10 characters) to avoid extrapolating beyond the model’s training regime. Customize the service with `PASS_GPT_MODEL_NAME` or `PASS_GPT_MODEL_PATH`, along with `PASS_GPT_MAX_PASSWORD_LENGTH`, `PASS_GPT_SCORE_SCALE`, and `PASS_GPT_DEVICE` for inference tuning. For gated Hugging Face models, supply `HUGGINGFACE_HUB_TOKEN`.

### zxcvbn Heuristic Estimator

Dropbox’s zxcvbn library provides pattern-based heuristics and crack-time estimates aligned with empirical password datasets. The wrapper service simply delegates to zxcvbn, enriches the result with the raw score (0–4), logarithmic guess counts, warnings, and improvement suggestions, then smooths scores into a 1–100 range by blending the base zxcvbn score with the entropy term (`guesses_log10`). The normalization prevents overly harsh penalties on marginal passwords while still rewarding high-entropy inputs.

### HaveIBeenPwned Range Checks

This component hashes the candidate password with SHA-1, applies HIBP’s k-anonymity scheme (first five hex characters as the prefix), and looks up breach counts via the official range API. Range responses are cached in-process with an LRU of 8,192 prefixes, cutting roundtrips for repeat queries. The client retries transient failures with exponential backoff, surfaces per-request latency, and normalizes scores by subtracting logarithmic penalties for observed breach counts—clean passwords score 100, while heavily compromised ones collapse toward 1. Configure the HTTP client with `HIBP_API_KEY`, `HIBP_API_ROOT`, timeout, retry, and user-agent parameters to match your deployment requirements.

### Aggregator Orchestration

The aggregator accepts an optional `components` list per request or respects the `ENABLED_COMPONENTS` environment variable to select its fan-out set. It launches concurrent HTTP requests with `httpx.AsyncClient`, collects normalized scores, and averages the successful component values (re-clamping to 1–100). Partial failures are surfaced in the response alongside the individual payloads so callers can decide how to react. If every component fails, the service responds with HTTP 503; if policy filters remove all candidates (e.g., only PassGPT enabled for a long password) it returns HTTP 422. Component endpoints are configurable through `PASS_GPT_URL`, `ZXCVBN_URL`, and `HAVEIBEENPWNED_URL`, enabling cross-host deployments without code changes.

The aggregation step applies reliability safeguards: when zxcvbn reports a very weak score (default ≤1), its weight increases relative to PassGPT, PassGPT is penalized if zxcvbn emits a warning, and short passwords are capped (default max 60 for length <8). These behaviors are configurable via `PASS_SHORT_PASSWORD_LENGTH`, `PASS_SHORT_PASSWORD_MAX_SCORE`, `ZXCVBN_LOW_SCORE_THRESHOLD`, `PASS_GPT_WARNING_PENALTY`, `PASS_GPT_LOW_SCORE_PENALTY`, `PASS_GPT_LOW_WEIGHT`, and `ZXCVBN_LOW_WEIGHT`.

### Deployment Notes

Every service includes a `__main__` guard for quick `uvicorn` launches, but the recommended workflow is to run `docker-compose up` from the workspace root, which binds each component to a predictable port and wires their inter-service URLs automatically. Health endpoints integrate cleanly with container orchestrators, and the aggregator’s single entry point simplifies upstream integration by exposing a unified confidence score plus rich per-component diagnostics for audit trails or UI consumption.
