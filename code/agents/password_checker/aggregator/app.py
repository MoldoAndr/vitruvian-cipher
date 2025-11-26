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


COMPONENTS: Dict[str, ComponentConfig] = {
    "pass_strength_ai": ComponentConfig(
        name="pass_strength_ai",
        label="PassStrengthAI",
        score_endpoint=os.getenv("PASS_STRENGTH_AI_URL", "http://pass_strength_ai:8000/score"),
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
    component.strip()
    for component in os.getenv("ENABLED_COMPONENTS", ",".join(COMPONENTS.keys())).split(",")
    if component.strip()
]

PASS_STRENGTH_MAX_PASSWORD_LENGTH = 10


class AggregationRequest(BaseModel):
    password: str = Field(..., min_length=1, description="Password to score")
    components: Optional[List[str]] = Field(
        None, description="Optional list of component identifiers to enable for this request."
    )

    @validator("components", each_item=True)
    def _validate_component(cls, value: str) -> str:
        if value not in COMPONENTS:
            raise ValueError(f"Unknown component '{value}'. Valid options: {', '.join(COMPONENTS.keys())}")
        return value


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
    description="Combines results from PassStrengthAI, zxcvbn, and HaveIBeenPwned components.",
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


def _normalize(scores: List[int]) -> int:
    if not scores:
        raise HTTPException(status_code=503, detail="No component scores available to produce a result.")
    average = sum(scores) / len(scores)
    return max(1, min(100, int(round(average))))


@app.get("/health", tags=["internal"])
def health() -> Dict[str, str]:
    return {"status": "ok", "component": "aggregator", "available_components": ",".join(COMPONENTS.keys())}


@app.post("/score", response_model=AggregationResponse, tags=["scoring"])
async def aggregate_scores(payload: AggregationRequest) -> AggregationResponse:
    enabled = payload.components or DEFAULT_ENABLED
    enabled = [component for component in enabled if component in COMPONENTS]

    disabled_results: List[ComponentResult] = []

    if len(payload.password) > PASS_STRENGTH_MAX_PASSWORD_LENGTH and "pass_strength_ai" in enabled:
        enabled.remove("pass_strength_ai")
        LOGGER.info(
            "Disabling PassStrengthAI for password length %s > %s",
            len(payload.password),
            PASS_STRENGTH_MAX_PASSWORD_LENGTH,
        )
        disabled_results.append(
            ComponentResult(
                name="pass_strength_ai",
                label=COMPONENTS["pass_strength_ai"].label,
                normalized_score=None,
                success=False,
                detail=None,
                error=f"Disabled automatically for passwords longer than {PASS_STRENGTH_MAX_PASSWORD_LENGTH} characters.",
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

    scores = [
        result.normalized_score
        for result in combined_results
        if result.success and result.normalized_score is not None
    ]
    combined = _normalize(scores)

    return AggregationResponse(
        active_components=[result.name for result in combined_results if result.success],
        normalized_score=combined,
        components=combined_results,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=False)
