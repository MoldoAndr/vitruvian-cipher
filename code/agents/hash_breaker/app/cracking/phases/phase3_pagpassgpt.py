"""Phase 3: AI Generation with PagPassGPT.

State-of-the-art AI-driven password generation using PagPassGPT model.
"""

import logging
from typing import Dict, Iterable, List

from app.ml import get_generator
from app.cracking.hashcat_runner import run_hashcat_attack

logger = logging.getLogger(__name__)


def ai_generation_attack(
    target_hash: str,
    hash_type_id: int,
    timeout: int,
    num_passwords: int = 5000000
) -> Dict:
    """Execute AI-powered generation attack using PagPassGPT.

    Args:
        target_hash: Target hash to crack
        hash_type_id: Hashcat hash mode
        timeout: Time budget in seconds
        num_passwords: Number of passwords to generate

    Returns:
        Result dict with cracked status
    """
    logger.info(f"Phase 3: PagPassGPT AI Generation (timeout={timeout}s, count={num_passwords})")

    try:
        generator = get_generator()
        candidate_iter = _iter_passwords(generator, num_passwords, batch_size=10000)

        result = run_hashcat_attack(
            target_hash=target_hash,
            hash_type_id=hash_type_id,
            attack_mode=0,
            attack_args=[],
            timeout=timeout,
            stdin_iter=candidate_iter,
        )

        attempts = result.attempts if result.attempts is not None else num_passwords

        if result.cracked:
            logger.info(f"Phase 3: Password cracked with AI: {result.password}")
            return {
                "cracked": True,
                "password": result.password,
                "phase": 3,
                "method": "pagpassgpt",
                "attempts": attempts,
            }

        if result.timeout:
            logger.warning(f"Phase 3: Timeout after {timeout}s")
            return {
                "cracked": False,
                "attempts": attempts,
                "phase": 3,
                "timeout": True,
            }

        logger.info("Phase 3: No matches found")
        return {
            "cracked": False,
            "attempts": attempts,
            "phase": 3,
        }

    except Exception as e:
        logger.error(f"Phase 3 error: {e}")
        return {
            "cracked": False,
            "error": str(e),
            "phase": 3,
        }


def _iter_passwords(
    generator,
    total: int,
    batch_size: int = 10000,
) -> Iterable[str]:
    remaining = max(0, int(total))

    while remaining > 0:
        count = min(batch_size, remaining)
        batch: List[str] = generator.generate(num_passwords=count)
        if not batch:
            break
        for pwd in batch:
            if pwd:
                yield pwd
        remaining -= len(batch)
