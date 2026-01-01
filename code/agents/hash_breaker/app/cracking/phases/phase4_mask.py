"""Phase 4: Limited Mask Attack.

Brute-force simple password patterns with remaining time budget.
"""

import logging
import time
from typing import Dict

from app.cracking.hashcat_runner import run_hashcat_attack

logger = logging.getLogger(__name__)


# Common password masks for brute-force
COMMON_MASKS = [
    "?l?l?l?l?l?l?l?l",      # 8 lowercase
    "?u?l?l?l?l?l?l",        # 1 uppercase + 7 lowercase
    "?l?l?l?l?l?l?d",        # 7 lowercase + 1 digit
    "?l?l?l?l?l?l?l?d",      # 7 lowercase + 1 digit (8 total)
    "?a?a?a?a?a?a?a",        # 8 printable ASCII
]


def mask_attack(
    target_hash: str,
    hash_type_id: int,
    timeout: int
) -> Dict:
    """Execute limited mask attack.

    Args:
        target_hash: Target hash to crack
        hash_type_id: Hashcat hash mode
        timeout: Time budget in seconds

    Returns:
        Result dict with cracked status
    """
    logger.info(f"Phase 4: Limited Mask Attack (timeout={timeout}s)")

    if timeout <= 0:
        logger.warning("Phase 4: No time budget available")
        return {
            "cracked": False,
            "attempts": 0,
            "phase": 4,
            "timeout": True,
        }

    start_time = time.time()

    for i, mask in enumerate(COMMON_MASKS):
        remaining = timeout - (time.time() - start_time)
        if remaining <= 0:
            logger.debug("Phase 4: Time budget exhausted")
            break

        masks_left = len(COMMON_MASKS) - i
        time_per_mask = max(1, int(remaining / masks_left))

        logger.debug(f"Phase 4: Trying mask {i+1}/{len(COMMON_MASKS)}: {mask}")

        try:
            result = run_hashcat_attack(
                target_hash=target_hash,
                hash_type_id=hash_type_id,
                attack_mode=3,
                attack_args=[
                    mask,
                    "--increment",
                    "--increment-min",
                    "1",
                    "--increment-max",
                    "8",
                ],
                timeout=time_per_mask,
            )

            if result.cracked:
                logger.info(f"Phase 4: Password cracked with mask '{mask}': {result.password}")
                return {
                    "cracked": True,
                    "password": result.password,
                    "attempts": 10000000,
                    "phase": 4,
                    "method": "mask_attack",
                    "mask": mask,
                }

        except Exception as e:
            logger.error(f"Phase 4 error with mask '{mask}': {e}")
            continue

    logger.info("Phase 4: No matches found with any mask")
    return {
        "cracked": False,
        "attempts": 10000000,  # Approximate
        "phase": 4
    }
