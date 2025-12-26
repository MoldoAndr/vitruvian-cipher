import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator


LOGGER = logging.getLogger("password_strength_aggregator")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO))


@dataclass
class ComponentConfig:
    name: str
    label: str
    score_endpoint: str


COMPONENT_ALIASES = {"pass_strength_ai": "pass_gpt"}


def _normalize_component_name(component: str) -> str:
    return COMPONENT_ALIASES.get(component, component)


COMPONENTS: Dict[str, ComponentConfig] = {
    "pass_gpt": ComponentConfig(
        name="pass_gpt",
        label="PassGPT",
        score_endpoint=os.getenv(
            "PASS_GPT_URL",
            os.getenv("PASS_STRENGTH_AI_URL", "http://pass_gpt:8000/score"),
        ),
    ),
    "zxcvbn": ComponentConfig(
        name="zxcvbn",
        label="zxcvbn",
        score_endpoint=os.getenv("ZXCVBN_URL", "http://zxcvbn:8000/score"),
    ),
    "haveibeenpwned": ComponentConfig(
        name="haveibeenpwned",
        label="HaveIBeenPwned",
        score_endpoint=os.getenv("HAVEIBEENPWNED_URL", "http://haveibeenpwned:8000/score"),
    ),
}

DEFAULT_ENABLED = [
    _normalize_component_name(component.strip())
    for component in os.getenv("ENABLED_COMPONENTS", ",".join(COMPONENTS.keys())).split(",")
    if component.strip()
]
DEFAULT_ENABLED = [component for component in DEFAULT_ENABLED if component in COMPONENTS]

PASS_GPT_MAX_PASSWORD_LENGTH = int(os.getenv("PASS_GPT_MAX_PASSWORD_LENGTH", "10"))
PASS_SHORT_PASSWORD_LENGTH = int(os.getenv("PASS_SHORT_PASSWORD_LENGTH", "8"))
PASS_SHORT_PASSWORD_MAX_SCORE = int(os.getenv("PASS_SHORT_PASSWORD_MAX_SCORE", "60"))
ZXCVBN_LOW_SCORE_THRESHOLD = int(os.getenv("ZXCVBN_LOW_SCORE_THRESHOLD", "1"))
PASS_GPT_WARNING_PENALTY = int(os.getenv("PASS_GPT_WARNING_PENALTY", "15"))
PASS_GPT_LOW_SCORE_PENALTY = int(os.getenv("PASS_GPT_LOW_SCORE_PENALTY", "10"))
PASS_GPT_LOW_WEIGHT = float(os.getenv("PASS_GPT_LOW_WEIGHT", "0.6"))
ZXCVBN_LOW_WEIGHT = float(os.getenv("ZXCVBN_LOW_WEIGHT", "1.4"))


class AggregationRequest(BaseModel):
    password: str = Field(..., min_length=1, description="Password to score")
    components: Optional[List[str]] = Field(
        None, description="Optional list of component identifiers to enable for this request."
    )

    @validator("components", each_item=True)
    def _validate_component(cls, value: str) -> str:
        normalized = _normalize_component_name(value)
        if normalized not in COMPONENTS:
            raise ValueError(f"Unknown component '{value}'. Valid options: {', '.join(COMPONENTS.keys())}")
        return normalized


class ComponentResult(BaseModel):
    name: str
    label: str
    normalized_score: Optional[int] = Field(None, ge=1, le=100)
    success: bool
    detail: Optional[Dict] = None
    error: Optional[str] = None


class AggregationResponse(BaseModel):
    active_components: List[str]
    normalized_score: int = Field(..., ge=1, le=100)
    components: List[ComponentResult]


app = FastAPI(
    title="Password Strength Aggregator",
    description="Combines results from PassGPT, zxcvbn, and HaveIBeenPwned components.",
    version="1.0.0",
)

# Add CORS middleware to allow browser requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def _call_component(client: httpx.AsyncClient, component: ComponentConfig, password: str) -> ComponentResult:
    try:
        response = await client.post(component.score_endpoint, json={"password": password}, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        normalized = data.get("normalized_score")
        if normalized is None:
            raise ValueError("Component response missing 'normalized_score'.")
        return ComponentResult(
            name=component.name,
            label=component.label,
            normalized_score=int(normalized),
            success=True,
            detail=data,
        )
    except Exception as exc:
        LOGGER.error("Component %s failed: %s", component.name, exc)
        return ComponentResult(
            name=component.name,
            label=component.label,
            success=False,
            error=str(exc),
        )


def _clamp_score(score: float) -> int:
    return max(1, min(100, int(round(score))))


def _normalize_weighted(weighted_scores: List[float], weights: List[float]) -> int:
    if not weighted_scores or not weights:
        raise HTTPException(status_code=503, detail="No component scores available to produce a result.")
    total_weight = sum(weights)
    if total_weight <= 0:
        raise HTTPException(status_code=503, detail="No component weights available to produce a result.")
    average = sum(weighted_scores) / total_weight
    return _clamp_score(average)


@app.get("/health", tags=["internal"])
def health() -> Dict[str, str]:
    return {"status": "ok", "component": "aggregator", "available_components": ",".join(COMPONENTS.keys())}


@app.post("/score", response_model=AggregationResponse, tags=["scoring"])
async def aggregate_scores(payload: AggregationRequest) -> AggregationResponse:
    enabled = list(payload.components or DEFAULT_ENABLED)
    enabled = [component for component in enabled if component in COMPONENTS]

    disabled_results: List[ComponentResult] = []

    if len(payload.password) > PASS_GPT_MAX_PASSWORD_LENGTH and "pass_gpt" in enabled:
        enabled.remove("pass_gpt")
        LOGGER.info(
            "Disabling PassGPT for password length %s > %s",
            len(payload.password),
            PASS_GPT_MAX_PASSWORD_LENGTH,
        )
        disabled_results.append(
            ComponentResult(
                name="pass_gpt",
                label=COMPONENTS["pass_gpt"].label,
                normalized_score=None,
                success=False,
                detail=None,
                error=f"Disabled automatically for passwords longer than {PASS_GPT_MAX_PASSWORD_LENGTH} characters.",
            )
        )

    if not enabled:
        if disabled_results:
            raise HTTPException(
                status_code=422,
                detail="No components available after applying password length policies.",
            )
        raise HTTPException(status_code=400, detail="No valid components selected.")

    async with httpx.AsyncClient() as client:
        tasks = [
            _call_component(client, COMPONENTS[component_name], payload.password) for component_name in enabled
        ]
        results = await asyncio.gather(*tasks)

    combined_results = disabled_results + list(results)

    results_by_name = {result.name: result for result in combined_results}
    zxcvbn_result = results_by_name.get("zxcvbn")
    zxcvbn_detail = zxcvbn_result.detail if zxcvbn_result and zxcvbn_result.success else {}
    zxcvbn_raw_score = None
    zxcvbn_warning = False
    if isinstance(zxcvbn_detail, dict):
        raw_score = zxcvbn_detail.get("raw_score")
        if isinstance(raw_score, int):
            zxcvbn_raw_score = raw_score
        warning = zxcvbn_detail.get("warning")
        zxcvbn_warning = bool(warning)

    zxcvbn_low = zxcvbn_raw_score is not None and zxcvbn_raw_score <= ZXCVBN_LOW_SCORE_THRESHOLD

    weighted_scores: List[float] = []
    weights: List[float] = []
    for result in combined_results:
        if not (result.success and result.normalized_score is not None):
            continue
        adjusted = float(result.normalized_score)
        weight = 1.0
        if result.name == "pass_gpt" and zxcvbn_result and zxcvbn_result.success:
            if zxcvbn_warning:
                adjusted -= PASS_GPT_WARNING_PENALTY
            if zxcvbn_low:
                adjusted -= PASS_GPT_LOW_SCORE_PENALTY
                weight = PASS_GPT_LOW_WEIGHT
        if result.name == "zxcvbn" and zxcvbn_low:
            weight = ZXCVBN_LOW_WEIGHT
        adjusted = _clamp_score(adjusted)
        weighted_scores.append(adjusted * weight)
        weights.append(weight)

    combined = _normalize_weighted(weighted_scores, weights)
    if len(payload.password) < PASS_SHORT_PASSWORD_LENGTH:
        combined = min(combined, PASS_SHORT_PASSWORD_MAX_SCORE)

    return AggregationResponse(
        active_components=[result.name for result in combined_results if result.success],
        normalized_score=combined,
        components=combined_results,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=False)
