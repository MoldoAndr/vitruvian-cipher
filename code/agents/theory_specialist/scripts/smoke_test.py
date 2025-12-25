#!/usr/bin/env python3
import json
import sys
import urllib.error
import urllib.request


BASE_URL = "http://localhost:8100"
QUERIES = [
    "What is RSA?",
    "What is AES?",
    "Compare RSA and AES.",
    "What are the pillars of cryptography?",
    "What is Diffie-Hellman key exchange?",
    "Explain ECDSA vs RSA signatures.",
    "What is a hash function and what are its security properties?",
    "What is a MAC and how does it differ from a digital signature?",
]
QUICK_QUERIES = [
    "What is RSA?",
    "What is AES?",
    "Compare RSA and AES.",
]


def _http_json(method: str, path: str, payload: dict | None = None, timeout: int = 120) -> dict:
    url = f"{BASE_URL}{path}"
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def _check_generate(query: str, timeout: int) -> tuple[bool, str]:
    payload = {"query": query, "conversation_id": None}
    response = _http_json("POST", "/generate", payload, timeout=timeout)
    answer = response.get("answer") or ""
    sources = response.get("sources") or []
    retrieval = response.get("retrieval_strategy")

    problems: list[str] = []
    if len(answer.strip()) < 80:
        problems.append("answer-too-short")
    if not sources:
        problems.append("no-sources")
    if retrieval not in {"hybrid", "vector", "lexical"}:
        problems.append("unexpected-retrieval")
    if "common knowledge" in answer.lower():
        problems.append("mentions-common-knowledge")

    status = "PASS" if not problems else "WARN"
    detail = f"{status} | sources={len(sources)} | retrieval={retrieval or 'n/a'}"
    if problems:
        detail += f" | issues={','.join(problems)}"
    return (not problems), detail


def _parse_args(argv: list[str]) -> tuple[list[str], int]:
    timeout = 120
    queries = QUERIES
    for arg in argv:
        if arg == "--quick":
            queries = QUICK_QUERIES
        elif arg.startswith("--timeout="):
            _, value = arg.split("=", 1)
            timeout = max(10, int(value))
        elif arg.startswith("--limit="):
            _, value = arg.split("=", 1)
            limit = max(1, int(value))
            queries = queries[:limit]
    return queries, timeout


def main() -> int:
    queries, timeout = _parse_args(sys.argv[1:])
    try:
        health = _http_json("GET", "/health")
        status = _http_json("GET", "/status")
    except urllib.error.URLError as exc:
        print(f"FAIL | service-unreachable | {exc}")
        return 2

    health_ok = health.get("status") == "healthy" and health.get("database") == "connected"
    status_ok = (
        status.get("processed_documents", 0) == status.get("total_reference_documents", 0)
        and status.get("pending_documents", 0) == 0
        and status.get("in_progress_documents", 0) == 0
    )

    print(f"{'PASS' if health_ok else 'WARN'} | health | {health}")
    print(f"{'PASS' if status_ok else 'WARN'} | status | {status}")

    failures = 0
    for query in queries:
        ok, detail = _check_generate(query, timeout)
        print(f"{'PASS' if ok else 'WARN'} | generate | {query} | {detail}")
        if not ok:
            failures += 1

    if not health_ok or not status_ok or failures:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
