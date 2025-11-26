import logging
import os
import string
from pathlib import Path
from typing import Dict

import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from tensorflow import keras


LOGGER = logging.getLogger("pass_strength_ai_service")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO))

DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "2023-05-31_21-52-43_model"
MODEL_PATH = Path(os.getenv("MODEL_PATH", DEFAULT_MODEL_PATH))

if not MODEL_PATH.exists():
    raise RuntimeError(f"Model file not found at {MODEL_PATH}")

MODEL = keras.models.load_model(MODEL_PATH)
INPUT_MAX_LENGTH = MODEL.input_shape[1]
CHARSET = string.ascii_letters + string.digits + string.punctuation


class PasswordPayload(BaseModel):
    password: str = Field(..., max_length=INPUT_MAX_LENGTH, description="Password to evaluate")


class ScoreResponse(BaseModel):
    component: str
    normalized_score: int = Field(..., ge=1, le=100)
    predicted_label: int
    confidence: float
    distribution: Dict[int, float]


app = FastAPI(
    title="PassStrengthAI Component",
    description="Password strength scoring using the PassStrengthAI neural network.",
    version="1.0.0",
)


def _encode_password(password: str) -> np.ndarray:
    encoding = np.zeros((INPUT_MAX_LENGTH, len(CHARSET)), dtype=np.float32)
    for idx, char in enumerate(password):
        try:
            char_index = CHARSET.index(char)
            encoding[idx, char_index] = 1.0
        except ValueError:
            LOGGER.debug("Character %r not present in charset; leaving encoding row as zeros", char)
    return encoding


def _score_from_distribution(probabilities: np.ndarray) -> int:
    labels = np.arange(len(probabilities), dtype=np.float32)
    expected_value = float(np.dot(probabilities, labels))
    # Labels range 0..4 -> normalize to 0..100 and clamp to 1..100
    normalized = max(1, min(100, int(round((expected_value / (len(probabilities) - 1)) * 100))))
    return normalized


@app.get("/health", tags=["internal"])
def health() -> Dict[str, str]:
    return {"status": "ok", "component": "pass_strength_ai"}


@app.post("/score", response_model=ScoreResponse, tags=["scoring"])
def score_password(payload: PasswordPayload) -> ScoreResponse:
    password = payload.password
    if len(password) > INPUT_MAX_LENGTH:
        raise HTTPException(status_code=422, detail=f"Password exceeds maximum length {INPUT_MAX_LENGTH}")

    encoded = _encode_password(password)
    encoded = np.expand_dims(encoded, axis=0)
    probabilities: np.ndarray = MODEL.predict(encoded, verbose=0)[0]

    predicted_label = int(np.argmax(probabilities))
    confidence = float(np.max(probabilities))

    normalized_score = _score_from_distribution(probabilities)
    distribution = {idx: float(prob) for idx, prob in enumerate(probabilities)}

    return ScoreResponse(
        component="pass_strength_ai",
        normalized_score=normalized_score,
        predicted_label=predicted_label,
        confidence=confidence,
        distribution=distribution,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=False)
