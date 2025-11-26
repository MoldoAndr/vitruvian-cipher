#!/usr/bin/env python3
"""Offline seed dataset builder for intent classification + entity extraction."""
from __future__ import annotations

import random
import sys
import uuid
from pathlib import Path
from typing import Dict, Iterable, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.questions_generator.toon import record_to_toon  # noqa: E402

random.seed(1337)
OUTPUT_PATH = Path("data/datasets/intent_entity_seed.jsonl")


def _confidence(low: float = 0.8, high: float = 0.98) -> float:
    return round(random.uniform(low, high), 2)


def _build_record(
    *,
    text: str,
    operation: str,
    entities: List[Dict[str, str | float]],
    metadata: Dict[str, str],
    intent_range: tuple[float, float] = (0.82, 0.97),
) -> Dict[str, object]:
    return {
        "id": str(uuid.uuid4()),
        "text": text.strip(),
        "intent": {"label": operation, "confidence": _confidence(*intent_range)},
        "entities": entities,
        "metadata": metadata,
        "operation": operation,
        "source": {
            "prompt_file": "offline_seed",
            "provider": "template",
            "model": "synthetic",
        },
    }


def _encryption_samples() -> Iterable[Dict[str, object]]:
    scenarios = [
        {
            "payload": "payroll extract for March",
            "algorithm": "AES-256-GCM",
            "context": "storage",
            "compliance": "GDPR",
            "urgency": "low",
        },
        {
            "payload": "staging customer export",
            "algorithm": "ChaCha20-Poly1305",
            "context": "transmission",
            "compliance": "HIPAA",
            "urgency": "medium",
        },
        {
            "payload": "design specs for the HSM",
            "algorithm": "RSA-OAEP",
            "context": "compliance",
            "compliance": "PCI-DSS",
            "urgency": "high",
        },
        {
            "payload": "session token cache",
            "algorithm": "XChaCha20",
            "context": "backup",
            "compliance": None,
            "urgency": "medium",
        },
        {
            "payload": "medical billing batch",
            "algorithm": "AES-128-CBC",
            "context": "storage",
            "compliance": "SOC2",
            "urgency": "high",
        },
        {
            "payload": "HR grievance log",
            "algorithm": "ECC SECP256R1",
            "context": "transmission",
            "compliance": "FedRAMP",
            "urgency": "low",
        },
        {
            "payload": "product roadmap deck",
            "algorithm": "Hybrid RSA+AES envelope",
            "context": "storage",
            "compliance": "ISO 27001",
            "urgency": "medium",
        },
        {
            "payload": "analytics export for the board",
            "algorithm": "AES-256-CTR + HMAC",
            "context": "compliance",
            "compliance": "SOX",
            "urgency": "high",
        },
        {
            "payload": "IoT gateway telemetry snapshot",
            "algorithm": "NTRUEncrypt",
            "context": "backup",
            "compliance": None,
            "urgency": "medium",
        },
        {
            "payload": "PKI admin handbook",
            "algorithm": "Kyber-1024 KEM",
            "context": "compliance",
            "compliance": "FedRAMP High",
            "urgency": "high",
        },
    ]

    for scenario in scenarios:
        text = (
            f"Please encrypt the {scenario['payload']} with {scenario['algorithm']} "
            f"so we stay compliant for {scenario['compliance'] or 'internal controls'}."
        )
        entities = [
            {"type": "plaintext", "value": scenario["payload"], "confidence": _confidence(0.8, 0.95)},
            {"type": "algorithm", "value": scenario["algorithm"], "confidence": _confidence(0.78, 0.92)},
        ]
        if scenario["compliance"]:
            entities.append(
                {
                    "type": "compliance_target",
                    "value": scenario["compliance"],
                    "confidence": _confidence(0.75, 0.9),
                }
            )
        metadata = {"context": scenario["context"], "urgency": scenario["urgency"]}
        yield _build_record(
            text=text,
            operation="encryption",
            entities=entities,
            metadata=metadata,
            intent_range=(0.85, 0.98),
        )


def _decryption_samples() -> Iterable[Dict[str, object]]:
    scenarios = [
        {
            "ciphertext": "p4Q1f8zKU2==",
            "hint": "probably AES-256",
            "reason": "incident response",
            "urgency": "high",
            "evidence": "provided",
        },
        {
            "ciphertext": "74686520756e6b6e6f776e",
            "hint": "hex that might be XOR",
            "reason": "customer dispute",
            "urgency": "medium",
            "evidence": "provided",
        },
        {
            "ciphertext": "wjfbsit",
            "hint": "looks like Caesar",
            "reason": "security audit",
            "urgency": "medium",
            "evidence": "missing",
        },
        {
            "ciphertext": "U2FsdGVkX1+2qpDG8sA9Hg==",
            "hint": "OpenSSL salted block",
            "reason": "restore access",
            "urgency": "high",
            "evidence": "provided",
        },
        {
            "ciphertext": "ENCRYPTED{87ac90cf}",
            "hint": "custom firmware blob",
            "reason": "firmware analysis",
            "urgency": "high",
            "evidence": "provided",
        },
        {
            "ciphertext": "3a4d-5ff1-9988-cc32",
            "hint": "maybe Vigenere",
            "reason": "forensics",
            "urgency": "medium",
            "evidence": "missing",
        },
        {
            "ciphertext": "RXhwZWN0OkZic0FwaTEyMw==",
            "hint": "base64 with prefix",
            "reason": "legacy archive unlock",
            "urgency": "high",
            "evidence": "provided",
        },
        {
            "ciphertext": "9f5c2c61d4b7cf90",
            "hint": "maybe TEA block",
            "reason": "malware triage",
            "urgency": "high",
            "evidence": "provided",
        },
        {
            "ciphertext": "{modexp:77b0}|sig",
            "hint": "suspect RSA message",
            "reason": "legal hold",
            "urgency": "medium",
            "evidence": "provided",
        },
        {
            "ciphertext": "salt$04f1$8a7b9302d1",
            "hint": "bcrypt style",
            "reason": "password recovery for HR",
            "urgency": "high",
            "evidence": "provided",
        },
    ]

    for scenario in scenarios:
        text = f"Need help decrypting {scenario['ciphertext']}; {scenario['hint']}, doing it for {scenario['reason']}."
        entities = [
            {"type": "ciphertext", "value": scenario["ciphertext"], "confidence": _confidence(0.82, 0.95)},
            {"type": "algorithm_hint", "value": scenario["hint"], "confidence": _confidence(0.7, 0.88)},
            {"type": "access_context", "value": scenario["reason"], "confidence": _confidence(0.75, 0.9)},
        ]
        metadata = {"urgency": scenario["urgency"], "evidence": scenario["evidence"]}
        yield _build_record(
            text=text,
            operation="decryption",
            entities=entities,
            metadata=metadata,
            intent_range=(0.83, 0.97),
        )


def _password_strength_samples() -> Iterable[Dict[str, object]]:
    scenarios = [
        {"password": "F1rewall!2024", "policy": "NIST 800-63B", "platform": "vpn", "goal": "reset"},
        {"password": "Graph3ne?Lab", "policy": "12 chars with symbols", "platform": "web", "goal": "new_account"},
        {"password": "Aurora_Sign#77", "policy": "CIS workstation baseline", "platform": "mobile", "goal": "audit"},
        {"password": "m0biusRing$", "policy": "must avoid dictionary words", "platform": "general", "goal": "audit"},
        {"password": "BeaconRed%314", "policy": "FedRAMP moderate", "platform": "web", "goal": "reset"},
        {"password": "IoTCloud^427", "policy": "rotate every 90 days", "platform": "vpn", "goal": "new_account"},
        {"password": "C0pperLeaf@73", "policy": "OWASP 2024 guidance", "platform": "web", "goal": "audit"},
        {"password": "Saffron!Delta92", "policy": "banking MFA rules", "platform": "mobile", "goal": "reset"},
        {"password": "CruxHub#118", "policy": "min 16 chars + entropy score", "platform": "vpn", "goal": "audit"},
        {"password": "LatticeWave$52", "policy": "SOC2 internal control", "platform": "general", "goal": "new_account"},
    ]

    for scenario in scenarios:
        text = f"Can you rate the strength of password '{scenario['password']}' against {scenario['policy']}?"
        entities = [
            {"type": "password_sample", "value": scenario["password"], "confidence": _confidence(0.85, 0.97)},
            {"type": "policy_hint", "value": scenario["policy"], "confidence": _confidence(0.78, 0.93)},
        ]
        metadata = {"platform": scenario["platform"], "assessment_goal": scenario["goal"]}
        yield _build_record(
            text=text,
            operation="password_strength",
            entities=entities,
            metadata=metadata,
            intent_range=(0.86, 0.99),
        )


def _theory_question_samples() -> Iterable[Dict[str, object]]:
    scenarios = [
        {"topic": "zero-knowledge proofs", "format": "explain", "target": None, "difficulty": "intermediate"},
        {"topic": "differential privacy", "format": "compare", "target": "secure multi-party computation", "difficulty": "advanced"},
        {"topic": "lattice-based cryptography", "format": "analyze", "target": "classic RSA", "difficulty": "advanced"},
        {"topic": "homomorphic encryption", "format": "explain", "target": None, "difficulty": "intermediate"},
        {"topic": "forward secrecy", "format": "prove", "target": "static DH", "difficulty": "intro"},
        {"topic": "pairing-based signatures", "format": "compare", "target": "ECDSA", "difficulty": "advanced"},
        {"topic": "post-quantum key exchange", "format": "analyze", "target": "elliptic-curve Diffie-Hellman", "difficulty": "advanced"},
        {"topic": "verifiable delay functions", "format": "explain", "target": None, "difficulty": "intermediate"},
        {"topic": "hash-based signatures", "format": "compare", "target": "SPHINCS+", "difficulty": "advanced"},
        {"topic": "threshold cryptography", "format": "explain", "target": None, "difficulty": "intermediate"},
    ]

    for scenario in scenarios:
        if scenario["target"]:
            text = f"Can you {scenario['format']} {scenario['topic']} versus {scenario['target']}?"
        else:
            text = f"Can you {scenario['format']} how {scenario['topic']} works in modern protocols?"
        entities = [
            {"type": "topic", "value": scenario["topic"], "confidence": _confidence(0.8, 0.95)},
        ]
        if scenario["target"]:
            entities.append(
                {
                    "type": "comparison_target",
                    "value": scenario["target"],
                    "confidence": _confidence(0.75, 0.9),
                }
            )
        metadata = {"difficulty": scenario["difficulty"], "format": scenario["format"]}
        yield _build_record(
            text=text,
            operation="theory_question",
            entities=entities,
            metadata=metadata,
            intent_range=(0.82, 0.96),
        )


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    generators = [
        _encryption_samples,
        _decryption_samples,
        _password_strength_samples,
        _theory_question_samples,
    ]
    records: List[Dict[str, object]] = []
    for fn in generators:
        records.extend(list(fn()))

    with OUTPUT_PATH.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(record_to_toon(record))

    print(f"Wrote {len(records)} samples to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
