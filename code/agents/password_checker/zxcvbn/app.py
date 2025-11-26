import os
from typing import Dict, List, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field
from zxcvbn import zxcvbn


class PasswordPayload(BaseModel):
    password: str = Field(..., min_length=1, description="Password to evaluate")


class ScoreResponse(BaseModel):
    component: str
    normalized_score: int = Field(..., ge=1, le=100)
    raw_score: int = Field(..., ge=0, le=4)
    guesses_log10: float
    crack_times_seconds: Dict[str, float]
    warning: Optional[str] = None
    suggestions: List[str] = Field(default_factory=list)


app = FastAPI(
    title="zxcvbn Component",
    description="Password strength scoring using Dropbox's zxcvbn estimator.",
    version="1.0.0",
)


def normalize(score: int, guesses_log10: float) -> int:
    # Blend zxcvbn score with guesses_log10 to smooth the extremes
    base = (score / 4) * 100
    entropy_bonus = min(15.0, max(0.0, guesses_log10 - 10) * 5)
    normalized = base + entropy_bonus
    return max(1, min(100, int(round(normalized))))


@app.get("/health", tags=["internal"])
def health() -> Dict[str, str]:
    return {"status": "ok", "component": "zxcvbn"}


@app.post("/score", response_model=ScoreResponse, tags=["scoring"])
def score(payload: PasswordPayload) -> ScoreResponse:
    result = zxcvbn(payload.password)
    normalized_score = normalize(result["score"], result["guesses_log10"])
    return ScoreResponse(
        component="zxcvbn",
        normalized_score=normalized_score,
        raw_score=result["score"],
        guesses_log10=result["guesses_log10"],
        crack_times_seconds=result["crack_times_seconds"],
        warning=result.get("feedback", {}).get("warning") if result.get("feedback") else None,
        suggestions=result.get("feedback", {}).get("suggestions", []) if result.get("feedback") else [],
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=False)
