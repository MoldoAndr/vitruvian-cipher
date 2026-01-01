"""Phase 4: Limited Mask Attack.

Brute-force simple password patterns with remaining time budget.
"""

import logging
import subprocess
from typing import Dict

from app.config import get_settings

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
    settings = get_settings()

    logger.info(f"Phase 4: Limited Mask Attack (timeout={timeout}s)")

    for i, mask in enumerate(COMMON_MASKS):
        # Calculate time for this mask
        time_per_mask = timeout // len(COMMON_MASKS)

        logger.debug(f"Phase 4: Trying mask {i+1}/{len(COMMON_MASKS)}: {mask}")

        cmd = [
            settings.hashcat_path,
            "-m", str(hash_type_id),
            "-a", "3",  # Mask attack mode
            str(target_hash),
            mask,
            "--potfile-disable",
            "--quiet",
            "--force",
            "--runtime", str(time_per_mask),
            "--increment",  # Increment mask length
            "--increment-min", "1",
            "--increment-max", "8"
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=time_per_mask
            )

            output = result.stdout

            if output and ":" in output:
                password = output.split(":")[1].strip()
                logger.info(f"Phase 4: Password cracked with mask '{mask}': {password}")
                return {
                    "cracked": True,
                    "password": password,
                    "phase": 4,
                    "method": "mask_attack",
                    "mask": mask
                }

        except subprocess.TimeoutExpired:
            logger.debug(f"Phase 4: Mask '{mask}' timed out")
            continue

        except Exception as e:
            logger.error(f"Phase 4 error with mask '{mask}': {e}")
            continue

    logger.info("Phase 4: No matches found with any mask")
    return {
        "cracked": False,
        "attempts": 10000000,  # Approximate
        "phase": 4
    }
