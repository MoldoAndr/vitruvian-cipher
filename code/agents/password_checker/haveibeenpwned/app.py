import hashlib
import logging
import math
import os
import time
from functools import lru_cache
from typing import Dict, Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


LOGGER = logging.getLogger("haveibeenpwned_service")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO))

DEFAULT_API_ROOT = "https://api.pwnedpasswords.com"
HIBP_API_ROOT = os.getenv("HIBP_API_ROOT", DEFAULT_API_ROOT).rstrip("/")
HIBP_API_KEY = os.getenv("HIBP_API_KEY")
HIBP_TIMEOUT = float(os.getenv("HIBP_TIMEOUT_SECONDS", "6.0"))
HIBP_MAX_RETRIES = int(os.getenv("HIBP_MAX_RETRIES", "3"))

USER_AGENT = os.getenv(
    "HIBP_USER_AGENT",
    "PasswordStrengthComponents/2.0 (+https://haveibeenpwned.com/)",
)


class PasswordPayload(BaseModel):
    password: str = Field(..., min_length=1, description="Password to evaluate")


class ScoreResponse(BaseModel):
    component: str
    normalized_score: int = Field(..., ge=1, le=100)
    compromised: bool
    appearances: int
    sha1: str
    data_source_available: bool
    api_latency_ms: Optional[int] = None


class RangeResponse(BaseModel):
    prefix: str
    suffix_count: int
    ttl_seconds: int


app = FastAPI(
    title="Have I Been Pwned Component",
    description="Online breach checks via Have I Been Pwned range API.",
    version="3.0.0",
)


def _score_from_appearances(count: int) -> int:
    if count <= 0:
        return 100
    penalty = min(99, int(math.log10(count + 1) * 20 + 10))
    return max(1, 100 - penalty)


def _hash_password(password: str) -> str:
    return hashlib.sha1(password.encode("utf-8")).hexdigest().upper()


def _request_headers() -> Dict[str, str]:
    headers = {
        "User-Agent": USER_AGENT,
        "Add-Padding": "true",
    }
    if HIBP_API_KEY:
        headers["hibp-api-key"] = HIBP_API_KEY
    return headers


@lru_cache(maxsize=8192)
def _fetch_range(prefix: str) -> Dict[str, int]:
    url = f"{HIBP_API_ROOT}/range/{prefix}"
    last_error: Optional[Exception] = None
    for attempt in range(1, HIBP_MAX_RETRIES + 1):
        try:
            with httpx.Client(timeout=HIBP_TIMEOUT, headers=_request_headers()) as client:
                response = client.get(url)
                response.raise_for_status()
                return _parse_range_response(response.text)
        except (httpx.RequestError, httpx.HTTPStatusError) as exc:
            last_error = exc
            LOGGER.warning(
                "Attempt %s/%s failed fetching prefix %s: %s",
                attempt,
                HIBP_MAX_RETRIES,
                prefix,
                exc,
            )
            sleep_for = min(2 ** attempt, 5)
            time.sleep(sleep_for)
    raise HTTPException(status_code=503, detail=f"Failed to contact HIBP API: {last_error}")


def _parse_range_response(payload: str) -> Dict[str, int]:
    suffix_map: Dict[str, int] = {}
    for line in payload.splitlines():
        if ":" not in line:
            continue
        suffix, count = line.split(":", 1)
        suffix = suffix.strip().upper()
        try:
            suffix_map[suffix] = int(count.strip())
        except ValueError:
            continue
    return suffix_map


@app.get("/health", tags=["internal"])
def health() -> Dict[str, str]:
    status = "ok" if HIBP_API_ROOT else "degraded"
    return {
        "status": status,
        "component": "haveibeenpwned",
        "api_root": HIBP_API_ROOT,
        "api_key_configured": str(bool(HIBP_API_KEY)).lower(),
    }


@app.post("/score", response_model=ScoreResponse, tags=["scoring"])
def score(payload: PasswordPayload) -> ScoreResponse:
    sha1 = _hash_password(payload.password)
    prefix, suffix = sha1[:5], sha1[5:]

    start_time = time.perf_counter()
    suffix_map = _fetch_range(prefix)
    latency_ms = int((time.perf_counter() - start_time) * 1000)

    appearances = suffix_map.get(suffix, 0)
    compromised = appearances > 0
    normalized = _score_from_appearances(appearances)

    return ScoreResponse(
        component="haveibeenpwned",
        normalized_score=normalized,
        compromised=compromised,
        appearances=appearances,
        sha1=sha1,
        data_source_available=True,
        api_latency_ms=latency_ms,
    )


@app.get("/range/{prefix}", response_model=RangeResponse, tags=["internal"])
def get_range(prefix: str) -> RangeResponse:
    prefix = prefix.upper()
    if len(prefix) != 5 or not all(c in "0123456789ABCDEF" for c in prefix):
        raise HTTPException(status_code=400, detail="Prefix must be a 5-character hexadecimal string.")
    suffixes = _fetch_range(prefix)
    return RangeResponse(prefix=prefix, suffix_count=len(suffixes), ttl_seconds=0)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=False)
