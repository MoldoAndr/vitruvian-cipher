"""Phase 2: Rule-Based Attack.

Applies intelligent mutations to dictionary words using Hashcat rules.
"""

import logging
import subprocess
from typing import Dict

from app.config import get_settings

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

    cmd = [
        settings.hashcat_path,
        "-m", str(hash_type_id),
        "-a", "0",  # Straight attack with rules
        "-r", str(rules_file),
        str(target_hash),
        str(wordlist),
        "--potfile-disable",
        "--quiet",
        "--force",
        "--runtime", str(timeout)
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        output = result.stdout

        if output and ":" in output:
            password = output.split(":")[1].strip()
            logger.info(f"Phase 2: Password cracked: {password}")
            return {
                "cracked": True,
                "password": password,
                "phase": 2,
                "method": "rule_based"
            }

        logger.info("Phase 2: No matches found")
        return {
            "cracked": False,
            "attempts": 5000000,  # Approximate with rules
            "phase": 2
        }

    except subprocess.TimeoutExpired:
        logger.warning(f"Phase 2: Timeout after {timeout}s")
        return {
            "cracked": False,
            "attempts": 5000000,
            "phase": 2,
            "timeout": True
        }

    except Exception as e:
        logger.error(f"Phase 2 error: {e}")
        return {
            "cracked": False,
            "error": str(e),
            "phase": 2
        }
