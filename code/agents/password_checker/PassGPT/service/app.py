import logging
import math
import os
from pathlib import Path
from typing import Dict

import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from transformers import AutoModelForCausalLM, AutoTokenizer


LOGGER = logging.getLogger("pass_gpt_service")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO))

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

MODEL_ID = (
    os.getenv("PASS_GPT_MODEL_PATH")
    or os.getenv("PASSGPT_MODEL_PATH")
    or os.getenv("PASS_GPT_MODEL_NAME")
    or os.getenv("PASSGPT_MODEL_NAME")
    or "javirandor/passgpt-10characters"
)
MAX_PASSWORD_LENGTH = int(os.getenv("PASS_GPT_MAX_PASSWORD_LENGTH", os.getenv("PASSGPT_MAX_PASSWORD_LENGTH", "10")))
SCORE_SCALE = float(os.getenv("PASS_GPT_SCORE_SCALE", os.getenv("PASSGPT_SCORE_SCALE", "12.0")))

DEVICE_PREFERENCE = os.getenv("PASS_GPT_DEVICE", os.getenv("PASSGPT_DEVICE", "cpu")).lower()

MODEL_PATH = Path(MODEL_ID)
LOCAL_ONLY = MODEL_PATH.exists()
if LOCAL_ONLY:
    LOGGER.info("Loading PassGPT model from local path %s", MODEL_PATH)
if DEVICE_PREFERENCE.startswith("cuda") and not torch.cuda.is_available():
    LOGGER.warning("CUDA requested but not available; falling back to CPU.")
    DEVICE = torch.device("cpu")
else:
    DEVICE = torch.device(DEVICE_PREFERENCE)

TOKENIZER = AutoTokenizer.from_pretrained(MODEL_ID, local_files_only=LOCAL_ONLY)
if TOKENIZER.pad_token is None:
    TOKENIZER.pad_token = TOKENIZER.eos_token

MODEL = AutoModelForCausalLM.from_pretrained(MODEL_ID, local_files_only=LOCAL_ONLY)
MODEL.to(DEVICE)
MODEL.eval()


class PasswordPayload(BaseModel):
    password: str = Field(..., min_length=1, max_length=MAX_PASSWORD_LENGTH, description="Password to evaluate")


class ScoreResponse(BaseModel):
    component: str
    normalized_score: int = Field(..., ge=1, le=100)
    log_probability: float
    average_log_probability: float
    token_count: int
    loss: float
    model_name: str


app = FastAPI(
    title="PassGPT Component",
    description="Password strength scoring using the PassGPT language model.",
    version="1.0.0",
)


def _normalize_score(log_probability: float) -> int:
    if SCORE_SCALE <= 0:
        return 1
    # Convert negative log-probability to a bounded strength score.
    strength = 1.0 - math.exp(log_probability / SCORE_SCALE)
    normalized = int(round(strength * 100))
    return max(1, min(100, normalized))


@app.get("/health", tags=["internal"])
def health() -> Dict[str, str]:
    return {"status": "ok", "component": "pass_gpt", "model": MODEL_ID, "device": str(DEVICE)}


@app.post("/score", response_model=ScoreResponse, tags=["scoring"])
def score_password(payload: PasswordPayload) -> ScoreResponse:
    password = payload.password
    if len(password) > MAX_PASSWORD_LENGTH:
        raise HTTPException(status_code=422, detail=f"Password exceeds maximum length {MAX_PASSWORD_LENGTH}")

    inputs = TOKENIZER(password, return_tensors="pt", add_special_tokens=False)
    input_ids = inputs["input_ids"].to(DEVICE)
    if input_ids.numel() == 0:
        raise HTTPException(status_code=422, detail="Password could not be tokenized.")

    with torch.inference_mode():
        outputs = MODEL(input_ids=input_ids, labels=input_ids)

    loss = float(outputs.loss)
    token_count = max(1, input_ids.shape[1] - 1)
    log_probability = -loss * token_count
    average_log_probability = log_probability / token_count
    normalized_score = _normalize_score(log_probability)

    return ScoreResponse(
        component="pass_gpt",
        normalized_score=normalized_score,
        log_probability=log_probability,
        average_log_probability=average_log_probability,
        token_count=token_count,
        loss=loss,
        model_name=MODEL_ID,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=False)
