"""Phase 1: Quick Dictionary Attack.

Uses top password lists for rapid low-hanging fruit recovery.
"""

import logging
from typing import Dict

from app.config import get_settings
from app.cracking.hashcat_runner import run_hashcat_attack
from app.models.enums import HashType

logger = logging.getLogger(__name__)


def quick_dictionary_attack(
    target_hash: str,
    hash_type_id: int,
    timeout: int
) -> Dict:
    """Execute quick dictionary attack.

    Args:
        target_hash: Target hash to crack
        hash_type_id: Hashcat hash mode
        timeout: Time budget in seconds

    Returns:
        Result dict with keys:
            - cracked (bool): Whether password was found
            - password (str, optional): Cracked password
            - attempts (int): Total attempts made
            - duration (float): Execution time
    """
    settings = get_settings()
    wordlist = settings.wordlists_dir / "top100k.txt"

    logger.info(f"Phase 1: Quick Dictionary Attack (timeout={timeout}s)")

    try:
        result = run_hashcat_attack(
            target_hash=target_hash,
            hash_type_id=hash_type_id,
            attack_mode=0,
            attack_args=[str(wordlist)],
            timeout=timeout,
        )

        if result.cracked:
            logger.info(f"Phase 1: Password cracked: {result.password}")
            return {
                "cracked": True,
                "password": result.password,
                "attempts": 100000,
                "phase": 1,
                "method": "quick_dictionary",
            }

        if result.error_type == "no_device":
            logger.warning("Phase 1: Hashcat requires GPU/OpenCL, using CPU-based fallback")
            return _cpu_dictionary_attack(target_hash, hash_type_id, wordlist, timeout)

        if result.timeout:
            logger.warning(f"Phase 1: Timeout after {timeout}s")
            return {
                "cracked": False,
                "attempts": 100000,
                "phase": 1,
                "timeout": True,
            }

        logger.info(f"Phase 1: No matches found (exit code {result.exit_code})")
        return {
            "cracked": False,
            "attempts": 100000,  # Approximate
            "phase": 1,
        }

    except Exception as e:
        logger.error(f"Phase 1 error: {e}")
        return {
            "cracked": False,
            "error": str(e),
            "phase": 1,
        }


def _cpu_dictionary_attack(target_hash: str, hash_type_id: int, wordlist, timeout: int) -> Dict:
    """CPU-based dictionary attack using Python (hashcat fallback).

    Args:
        target_hash: Target hash to crack
        wordlist: Path to wordlist file
        timeout: Time budget in seconds

    Returns:
        Result dict
    """
    import time

    logger.info(f"Phase 1: Using CPU-based fallback (timeout={timeout}s)")

    start_time = time.time()
    attempts = 0

    hash_func = _get_hash_func(hash_type_id)
    if hash_func is None:
        logger.warning(f"Phase 1: CPU fallback unsupported for hash type {hash_type_id}")
        return {
            "cracked": False,
            "error": f"Unsupported hash type for CPU fallback: {hash_type_id}",
            "attempts": 0,
            "phase": 1,
        }

    normalized_hash = target_hash.lower()

    try:
        with open(wordlist, 'r', encoding='latin-1') as f:
            for line in f:
                # Check timeout
                if time.time() - start_time > timeout:
                    logger.warning(f"Phase 1: CPU fallback timeout after {attempts} attempts")
                    return {
                        "cracked": False,
                        "attempts": attempts,
                        "phase": 1,
                        "timeout": True
                    }

                password = line.strip()
                if not password:
                    continue

                attempts += 1

                hash_obj = hash_func(password.encode('utf-8', errors='ignore'))
                if hash_obj.hexdigest() == normalized_hash:
                    logger.info(f"Phase 1: Password cracked (CPU fallback): {password}")
                    return {
                        "cracked": True,
                        "password": password,
                        "attempts": attempts,
                        "phase": 1,
                        "method": "cpu_dictionary",
                    }

        logger.info(f"Phase 1: CPU fallback checked {attempts} passwords, no match")
        return {
            "cracked": False,
            "attempts": attempts,
            "phase": 1
        }

    except Exception as e:
        logger.error(f"Phase 1 CPU fallback error: {e}")
        return {
            "cracked": False,
            "error": str(e),
            "attempts": attempts,
            "phase": 1
        }


def _get_hash_func(hash_type_id: int):
    if hash_type_id == HashType.MD5.value:
        import hashlib
        return hashlib.md5
    if hash_type_id == HashType.SHA1.value:
        import hashlib
        return hashlib.sha1
    if hash_type_id == HashType.SHA256.value:
        import hashlib
        return hashlib.sha256
    if hash_type_id == HashType.SHA512.value:
        import hashlib
        return hashlib.sha512
    return None
