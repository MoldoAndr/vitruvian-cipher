#!/usr/bin/env python3
"""Flask server that exposes the SecureBERT inference endpoints."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from flask import Flask, jsonify, request

from api import PayloadError, process_payload  # type: ignore


def _locate_env_file() -> Optional[Path]:
    """Walk up the directory tree to find the project-level .env file."""
    current = Path(__file__).resolve().parent
    for directory in [current, *current.parents]:
        candidate = directory / ".env"
        if candidate.exists():
            return candidate
    return None


ENV_FILE = _locate_env_file()
if ENV_FILE:
    load_dotenv(ENV_FILE)
else:
    load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[1]
ENTITIES_MODEL = Path(os.getenv("ENTITIES_MODEL_DIR", BASE_DIR / "artifacts/entities"))
INTENT_MODEL = Path(os.getenv("INTENT_MODEL_DIR", BASE_DIR / "artifacts/intent"))
HOST = os.getenv("API_HOST", "0.0.0.0")
PORT = int(os.getenv("API_PORT", "8000"))

app = Flask(__name__)


def _add_cors_headers(response):
    """Attach permissive CORS headers for local development."""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@app.after_request
def after_request(response):  # type: ignore[override]
    return _add_cors_headers(response)


@app.get("/health")
def health() -> tuple[dict, int]:
    """Simple liveness endpoint."""
    return {"status": "ok"}, 200


@app.post("/predict")
def predict():
    """Entry point for running entity or intent inference."""
    if not request.is_json:
        return jsonify({"status": "error", "message": "Request body must be JSON"}), 400

    payload = request.get_json()
    if not isinstance(payload, dict):
        return jsonify({"status": "error", "message": "JSON payload must be an object"}), 400

    try:
        response = process_payload(payload, ENTITIES_MODEL, INTENT_MODEL)
    except PayloadError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400
    except Exception as exc:  # pragma: no cover - defensive
        app.logger.exception("Unexpected inference error: %s", exc)
        return jsonify({"status": "error", "message": "Internal server error"}), 500

    return jsonify(response), 200


def main() -> None:
    app.run(host=HOST, port=PORT)


if __name__ == "__main__":
    main()
