https://github.com/OffRange/PassStrengthAI
https://github.com/dropbox/zxcvbn
https://haveibeenpwned.com/API/v3
https://www.usenix.org/conference/usenixsecurity16/technical-sessions/presentation/wheeler

## Password Strength Ensemble

This workspace packages three complementary scoring engines behind FastAPI services and fans their outputs into a dedicated aggregator. Running the stack (locally or via Docker Compose) yields a composite password strength verdict that blends neural confidence, heuristic entropy analysis, and breach intelligence. Each component exposes `POST /score` and `GET /health`, so you can deploy them independently, layer them into other systems, or lean on the aggregator to orchestrate cross-checks.

### PassStrengthAI Neural Model

Based on the PassStrengthAI project, the service loads the pre-trained TensorFlow model at startup and keeps it resident for low-latency inference. Passwords are one-hot encoded over the printable ASCII alphabet and padded to the model’s fixed input width; characters outside the training charset degrade gracefully by leaving the corresponding row zeroed. The model outputs a five-class distribution (0–4) derived from zxcvbn-labelled training data. The service reports the winning class, its confidence, the full probability histogram, and a 1–100 normalized score computed from the expectation of the distribution. Requests longer than the model’s supported length return HTTP 422, and the aggregator automatically skips PassStrengthAI when passwords exceed 10 characters to avoid misleading scores. Tune behavior with `MODEL_PATH` to swap in a different `.keras` artifact.

### zxcvbn Heuristic Estimator

Dropbox’s zxcvbn library provides pattern-based heuristics and crack-time estimates aligned with empirical password datasets. The wrapper service simply delegates to zxcvbn, enriches the result with the raw score (0–4), logarithmic guess counts, warnings, and improvement suggestions, then smooths scores into a 1–100 range by blending the base zxcvbn score with the entropy term (`guesses_log10`). The normalization prevents overly harsh penalties on marginal passwords while still rewarding high-entropy inputs.

### HaveIBeenPwned Range Checks

This component hashes the candidate password with SHA-1, applies HIBP’s k-anonymity scheme (first five hex characters as the prefix), and looks up breach counts via the official range API. Range responses are cached in-process with an LRU of 8,192 prefixes, cutting roundtrips for repeat queries. The client retries transient failures with exponential backoff, surfaces per-request latency, and normalizes scores by subtracting logarithmic penalties for observed breach counts—clean passwords score 100, while heavily compromised ones collapse toward 1. Configure the HTTP client with `HIBP_API_KEY`, `HIBP_API_ROOT`, timeout, retry, and user-agent parameters to match your deployment requirements.

### Aggregator Orchestration

The aggregator accepts an optional `components` list per request or respects the `ENABLED_COMPONENTS` environment variable to select its fan-out set. It launches concurrent HTTP requests with `httpx.AsyncClient`, collects normalized scores, and averages the successful component values (re-clamping to 1–100). Partial failures are surfaced in the response alongside the individual payloads so callers can decide how to react. If every component fails, the service responds with HTTP 503; if policy filters remove all candidates (e.g., only PassStrengthAI enabled for a long password) it returns HTTP 422. Component endpoints are configurable through `PASS_STRENGTH_AI_URL`, `ZXCVBN_URL`, and `HAVEIBEENPWNED_URL`, enabling cross-host deployments without code changes.

### Deployment Notes

Every service includes a `__main__` guard for quick `uvicorn` launches, but the recommended workflow is to run `docker-compose up` from the workspace root, which binds each component to a predictable port and wires their inter-service URLs automatically. Health endpoints integrate cleanly with container orchestrators, and the aggregator’s single entry point simplifies upstream integration by exposing a unified confidence score plus rich per-component diagnostics for audit trails or UI consumption.
