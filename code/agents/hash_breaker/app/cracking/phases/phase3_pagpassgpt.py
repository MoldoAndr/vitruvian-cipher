"""Phase 3: AI Generation with PagPassGPT.

State-of-the-art AI-driven password generation using PagPassGPT model.
"""

import logging
import subprocess
from typing import Dict

from app.config import get_settings
from app.ml import get_generator

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
    settings = get_settings()

    logger.info(f"Phase 3: PagPassGPT AI Generation (timeout={timeout}s, count={num_passwords})")

    # Create generator script as subprocess
    generator_script = f"""
import sys
sys.path.insert(0, '/app')
from app.ml.pagpassgpt import get_generator

gen = get_generator()
for pwd in gen.generate(num_passwords={num_passwords}):
    print(pwd)
"""

    # Pipe to hashcat via stdin
    hashcat_cmd = [
        settings.hashcat_path,
        "-m", str(hash_type_id),
        "-",  # Read from stdin
        "--stdin",
        "--potfile-disable",
        "--quiet",
        "--force",
        "--runtime", str(timeout)
    ]

    try:
        # Run generator and pipe to hashcat
        generator_proc = subprocess.Popen(
            ["python3", "-c", generator_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        result = subprocess.run(
            hashcat_cmd,
            input=generator_proc.stdout,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        output = result.stdout

        if output and ":" in output:
            password = output.split(":")[1].strip()
            logger.info(f"Phase 3: Password cracked with AI: {password}")
            return {
                "cracked": True,
                "password": password,
                "phase": 3,
                "method": "pagpassgpt",
                "attempts": num_passwords
            }

        logger.info("Phase 3: No matches found")
        return {
            "cracked": False,
            "attempts": num_passwords,
            "phase": 3
        }

    except subprocess.TimeoutExpired:
        logger.warning(f"Phase 3: Timeout after {timeout}s")
        return {
            "cracked": False,
            "attempts": num_passwords,
            "phase": 3,
            "timeout": True
        }

    except Exception as e:
        logger.error(f"Phase 3 error: {e}")
        return {
            "cracked": False,
            "error": str(e),
            "phase": 3
        }
