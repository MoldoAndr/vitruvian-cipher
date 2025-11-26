#!/usr/bin/env python3
"""Single entry-point for running intent or entity inference via JSON payloads."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, MutableMapping, Optional

from transformers import (
    AutoModelForSequenceClassification,
    AutoModelForTokenClassification,
    AutoTokenizer,
    pipeline,
)


# Lazy initialized transformers pipelines so repeated invocations in the same
# process do not reload large checkpoints.
_ENTITY_PIPE = None
_INTENT_PIPE = None


def _json_error(message: str, code: int = 1) -> None:
    """Emit a JSON error payload and exit."""
    print(json.dumps({"status": "error", "message": message}, ensure_ascii=False))
    raise SystemExit(code)


def _load_payload(payload_arg: Optional[str], payload_file: Optional[Path]) -> Dict[str, Any]:
    """Load the JSON payload from CLI argument, file, or stdin."""
    raw: Optional[str] = None
    if payload_arg:
        raw = payload_arg
    elif payload_file:
        try:
            raw = payload_file.read_text(encoding="utf-8")
        except OSError as exc:
            _json_error(f"Failed to read payload file: {exc}")
    else:
        raw = sys.stdin.read()

    if not raw.strip():
        _json_error("Empty payload provided")

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        _json_error(f"Payload is not valid JSON: {exc}")


def _normalize_operation(op_field: Any) -> str:
    """Normalize the 'ops' / 'operation' field to a single operation string."""
    if op_field is None:
        _json_error("Payload must include 'operation' or 'ops' key")

    if isinstance(op_field, str):
        ops: List[str] = [op_field]
    elif isinstance(op_field, Iterable):
        ops = [str(item) for item in op_field]
    else:
        _json_error("Operation must be a string or list of strings")

    # Remove empty entries.
    ops = [op.strip() for op in ops if op and str(op).strip()]
    if not ops:
        _json_error("Operation list is empty")

    if len(ops) != 1:
        _json_error("Provide exactly one operation per request")

    op_value = ops[0].lower()
    if op_value not in {"entity_extraction", "intent_extraction"}:
        _json_error(f"Unsupported operation '{op_value}'")
    return op_value


def _get_text(payload: MutableMapping[str, Any]) -> str:
    """Extract the text value supporting multiple key aliases."""
    text_value = payload.get("input_text") or payload.get("text")
    if not isinstance(text_value, str) or not text_value.strip():
        _json_error("Payload must include non-empty 'input_text' or 'text'")
    return text_value


def _ensure_entity_pipe(model_dir: Path):
    global _ENTITY_PIPE
    if _ENTITY_PIPE is None:
        tokenizer = AutoTokenizer.from_pretrained(model_dir)
        model = AutoModelForTokenClassification.from_pretrained(model_dir)
        _ENTITY_PIPE = pipeline(
            "token-classification",
            model=model,
            tokenizer=tokenizer,
            aggregation_strategy="simple",
        )
    return _ENTITY_PIPE


def _ensure_intent_pipe(model_dir: Path):
    global _INTENT_PIPE
    if _INTENT_PIPE is None:
        tokenizer = AutoTokenizer.from_pretrained(model_dir)
        model = AutoModelForSequenceClassification.from_pretrained(model_dir)
        _INTENT_PIPE = pipeline("text-classification", model=model, tokenizer=tokenizer)
    return _INTENT_PIPE


def handle_entity_extraction(text: str, model_dir: Path) -> Dict[str, Any]:
    pipeline_ = _ensure_entity_pipe(model_dir)
    raw_predictions = pipeline_(text)
    entities = [
        {
            "entity": pred.get("entity_group"),
            "score": float(pred.get("score", 0.0)),
            "text": text[pred.get("start", 0) : pred.get("end", 0)],
            "start": int(pred.get("start", 0)),
            "end": int(pred.get("end", 0)),
        }
        for pred in raw_predictions
    ]
    return {"entities": entities, "count": len(entities)}


def handle_intent_extraction(text: str, model_dir: Path) -> Dict[str, Any]:
    pipeline_ = _ensure_intent_pipe(model_dir)
    predictions = pipeline_(text, truncation=True)
    top_pred = predictions[0] if predictions else {}
    return {
        "label": top_pred.get("label"),
        "score": float(top_pred.get("score", 0.0)) if top_pred else 0.0,
        "all_predictions": predictions,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Unified inference entry point for SecureBERT models.")
    parser.add_argument(
        "--entities-model",
        type=Path,
        default=Path("artifacts/entities"),
        help="Path to the trained entity extraction model directory.",
    )
    parser.add_argument(
        "--intent-model",
        type=Path,
        default=Path("artifacts/intent"),
        help="Path to the trained intent classification model directory.",
    )
    parser.add_argument(
        "--payload",
        help="JSON payload string. If omitted, provide --payload-file or pipe JSON via stdin.",
    )
    parser.add_argument(
        "--payload-file",
        type=Path,
        help="Path to a JSON file describing the operation request.",
    )
    args = parser.parse_args()

    payload = _load_payload(args.payload, args.payload_file)
    operation = _normalize_operation(payload.get("operation") or payload.get("ops"))
    text = _get_text(payload)

    if operation == "entity_extraction":
        result = handle_entity_extraction(text, args.entities_model)
    else:  # intent_extraction
        result = handle_intent_extraction(text, args.intent_model)

    response = {
        "status": "ok",
        "operation": operation,
        "input_text": text,
        "result": result,
    }
    print(json.dumps(response, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
