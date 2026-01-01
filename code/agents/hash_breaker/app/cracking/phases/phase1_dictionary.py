"""Phase 1: Quick Dictionary Attack.

Uses top password lists for rapid low-hanging fruit recovery.
"""

import logging
import subprocess
from typing import Dict, Optional

from app.config import get_settings

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

    cmd = [
        settings.hashcat_path,
        "-m", str(hash_type_id),
        "-a", "0",  # Straight attack mode
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
        stderr = result.stderr

        # Check if hashcat actually succeeded (exit code 0)
        # Exit code 0 = at least one hash cracked
        # Exit code 1 = no hashes cracked
        # Exit code 255 = error/no device available
        if result.returncode == 0 and output and ":" in output:
            # Hashcat output format: hash:password
            password = output.split(":")[1].strip()
            logger.info(f"Phase 1: Password cracked: {password}")
            return {
                "cracked": True,
                "password": password,
                "phase": 1,
                "method": "quick_dictionary"
            }

        # Check if hashcat failed due to no GPU/OpenCL
        if result.returncode == 255 and ("No OpenCL" in stderr or "No CUDA" in stderr or "No HIP" in stderr):
            logger.warning("Phase 1: Hashcat requires GPU/OpenCL, using CPU-based fallback")
            return _cpu_dictionary_attack(target_hash, wordlist, timeout)

        logger.info(f"Phase 1: No matches found (exit code {result.returncode})")
        return {
            "cracked": False,
            "attempts": 100000,  # Approximate
            "phase": 1
        }

    except subprocess.TimeoutExpired:
        logger.warning(f"Phase 1: Timeout after {timeout}s")
        return {
            "cracked": False,
            "attempts": 100000,
            "phase": 1,
            "timeout": True
        }

    except Exception as e:
        logger.error(f"Phase 1 error: {e}")
        return {
            "cracked": False,
            "error": str(e),
            "phase": 1
        }


def _cpu_dictionary_attack(target_hash: str, wordlist, timeout: int) -> Dict:
    """CPU-based dictionary attack using Python (hashcat fallback).

    Args:
        target_hash: Target hash to crack
        wordlist: Path to wordlist file
        timeout: Time budget in seconds

    Returns:
        Result dict
    """
    import hashlib
    import time

    logger.info(f"Phase 1: Using CPU-based fallback (timeout={timeout}s)")

    start_time = time.time()
    attempts = 0

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

                # Try MD5 (32 chars)
                if len(target_hash) == 32:
                    hash_obj = hashlib.md5(password.encode('utf-8', errors='ignore'))
                    if hash_obj.hexdigest() == target_hash.lower():
                        logger.info(f"Phase 1: Password cracked (CPU-MD5): {password}")
                        return {
                            "cracked": True,
                            "password": password,
                            "attempts": attempts,
                            "phase": 1,
                            "method": "cpu_dictionary"
                        }

                # Try SHA1 (40 chars)
                if len(target_hash) == 40:
                    hash_obj = hashlib.sha1(password.encode('utf-8', errors='ignore'))
                    if hash_obj.hexdigest() == target_hash.lower():
                        logger.info(f"Phase 1: Password cracked (CPU-SHA1): {password}")
                        return {
                            "cracked": True,
                            "password": password,
                            "attempts": attempts,
                            "phase": 1,
                            "method": "cpu_dictionary"
                        }

                # Try SHA256 (64 chars)
                if len(target_hash) == 64:
                    hash_obj = hashlib.sha256(password.encode('utf-8', errors='ignore'))
                    if hash_obj.hexdigest() == target_hash.lower():
                        logger.info(f"Phase 1: Password cracked (CPU-SHA256): {password}")
                        return {
                            "cracked": True,
                            "password": password,
                            "attempts": attempts,
                            "phase": 1,
                            "method": "cpu_dictionary"
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
