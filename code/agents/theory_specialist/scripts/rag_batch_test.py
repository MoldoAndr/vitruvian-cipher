#!/usr/bin/env python3
"""
Batch test runner for the RAG API.

Sends 25 cryptography questions to /generate and stores responses in JSONL.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

import requests


QUESTIONS = [
    "What is RSA?",
    "What is AES and why is it widely used?",
    "Explain the difference between symmetric and asymmetric encryption.",
    "What problem does Diffie-Hellman key exchange solve?",
    "What is a digital signature and how is it verified?",
    "What is a cryptographic hash function?",
    "How does HMAC differ from a plain hash?",
    "What is the purpose of a nonce in cryptographic protocols?",
    "What is the difference between CBC and GCM modes of operation?",
    "What is authenticated encryption and why is it important?",
    "Why is RSA slow compared to symmetric ciphers?",
    "What is a key derivation function (KDF)?",
    "Why are salts used in password hashing?",
    "What is the role of a public key infrastructure (PKI)?",
    "What is the TLS handshake at a high level?",
    "What is perfect forward secrecy?",
    "What is Elliptic Curve Cryptography (ECC)?",
    "What is the RSA padding scheme OAEP used for?",
    "What is a stream cipher and how does it differ from a block cipher?",
    "What are common causes of cryptographic side-channel attacks?",
    "Why are random number generators critical in cryptography?",
    "What are typical key sizes for RSA and AES today?",
    "How does certificate validation work in HTTPS?",
    "What is the difference between a MAC and a digital signature?",
    "What is the purpose of a cryptographic commitment scheme?",
]


def update_provider(session: requests.Session, endpoint: str, model: str, api_key: str) -> None:
    payload = {"provider": "ollama-cloud"}
    if model:
        payload["ollama_model"] = model
    if api_key:
        payload["ollama_api_key"] = api_key
    response = session.post(f"{endpoint}/provider", json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()
    if data.get("provider") != "ollama-cloud":
        raise RuntimeError(f"Provider update failed: {data}")


def run_queries(
    session: requests.Session,
    endpoint: str,
    output_path: str,
    timeout: int,
    sleep_seconds: float,
) -> None:
    output_file = open(output_path, "w", encoding="utf-8")
    failures = 0

    for idx, question in enumerate(QUESTIONS, start=1):
        payload = {"query": question}
        try:
            response = session.post(
                f"{endpoint}/generate",
                json=payload,
                timeout=timeout,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as exc:  # pylint: disable=broad-except
            failures += 1
            data = {
                "error": str(exc),
                "question": question,
            }

        record = {
            "index": idx,
            "question": question,
            "answer": data.get("answer"),
            "sources": data.get("sources"),
            "conversation_id": data.get("conversation_id"),
            "message_id": data.get("message_id"),
            "error": data.get("error"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        output_file.write(json.dumps(record, ensure_ascii=True) + "\n")
        output_file.flush()

        if sleep_seconds > 0:
            time.sleep(sleep_seconds)

    output_file.close()
    print(f"Wrote results to {output_path}")
    if failures:
        print(f"Completed with {failures} failures")
        sys.exit(1)


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch test the RAG API.")
    parser.add_argument(
        "--endpoint",
        default=os.getenv("RAG_ENDPOINT", "http://localhost:8100"),
        help="Base URL for the RAG API.",
    )
    parser.add_argument(
        "--output",
        default=os.getenv("RAG_TEST_OUTPUT", "scripts/rag_test_results.jsonl"),
        help="Path to write JSONL results.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=int(os.getenv("RAG_TEST_TIMEOUT", "60")),
        help="Request timeout in seconds.",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=float(os.getenv("RAG_TEST_SLEEP", "0.0")),
        help="Sleep between requests in seconds.",
    )
    parser.add_argument(
        "--skip-provider",
        action="store_true",
        help="Skip calling /provider before queries.",
    )
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)

    session = requests.Session()
    if not args.skip_provider:
        model = os.getenv("OLLAMA_MODEL", "gpt-oss:120b-cloud")
        api_key = os.getenv("OLLAMA_API_KEY", "")
        update_provider(session, args.endpoint, model=model, api_key=api_key)

    run_queries(
        session=session,
        endpoint=args.endpoint,
        output_path=args.output,
        timeout=args.timeout,
        sleep_seconds=args.sleep,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
