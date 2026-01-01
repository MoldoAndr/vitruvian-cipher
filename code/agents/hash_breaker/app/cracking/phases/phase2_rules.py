"""Phase 2: Rule-Based Attack.

Applies intelligent mutations to dictionary words using Hashcat rules.
"""

import logging
from typing import Dict

from app.config import get_settings
from app.cracking.hashcat_runner import run_hashcat_attack

logger = logging.getLogger(__name__)


def rule_based_attack(
    target_hash: str,
    hash_type_id: int,
    timeout: int
) -> Dict:
    """Execute rule-based attack.

    Args:
        target_hash: Target hash to crack
        hash_type_id: Hashcat hash mode
        timeout: Time budget in seconds

    Returns:
        Result dict with cracked status
    """
    settings = get_settings()
    wordlist = settings.wordlists_dir / "rockyou.txt"
    rules_file = settings.rules_dir / "best64.rule"

    logger.info(f"Phase 2: Rule-Based Attack (timeout={timeout}s)")

    try:
        result = run_hashcat_attack(
            target_hash=target_hash,
            hash_type_id=hash_type_id,
            attack_mode=0,
            attack_args=["-r", str(rules_file), str(wordlist)],
            timeout=timeout,
        )

        if result.cracked:
            logger.info(f"Phase 2: Password cracked: {result.password}")
            return {
                "cracked": True,
                "password": result.password,
                "attempts": 5000000,
                "phase": 2,
                "method": "rule_based",
            }

        if result.timeout:
            logger.warning(f"Phase 2: Timeout after {timeout}s")
            return {
                "cracked": False,
                "attempts": 5000000,
                "phase": 2,
                "timeout": True,
            }

        logger.info("Phase 2: No matches found")
        return {
            "cracked": False,
            "attempts": 5000000,  # Approximate with rules
            "phase": 2,
        }

    except Exception as e:
        logger.error(f"Phase 2 error: {e}")
        return {
            "cracked": False,
            "error": str(e),
            "phase": 2,
        }
