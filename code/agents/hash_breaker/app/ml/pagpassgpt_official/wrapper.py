"""
PagPassGPT Official Implementation Wrapper

Integrates the official PagPassGPT implementation from:
https://github.com/Suxyuuu/PagPassGPT

This wrapper provides two modes:
1. With trained model: Uses official PagPassGPT for state-of-the-art performance
2. Without model: Falls back to basic generation for testing
"""

import logging
import os
from pathlib import Path
from typing import List, Optional
import sys

# Add the official PagPassGPT directory to path
official_dir = Path(__file__).parent
sys.path.insert(0, str(official_dir))

logger = logging.getLogger(__name__)


class PagPassGPTGenerator:
    """
    PagPassGPT Password Generator (Official Implementation)
    """

    def __init__(self, model_path: str = "/app/models/pagpassgpt"):
        """
        Initialize generator

        Args:
            model_path: Path to trained PagPassGPT model
        """
        self.model_path = Path(model_path)
        self.use_official = False
        self.tokenizer = None
        self.model = None
        self.device = None

        # Try to load official implementation
        self._load_official()

    def _load_official(self):
        """Try to load official PagPassGPT implementation"""
        try:
            # Check if model exists
            if not self.model_path.exists():
                logger.warning(f"PagPassGPT model not found at {self.model_path}")
                logger.info("Will use fallback generation method")
                return

            # Try to import official tokenizer
            from char_tokenizer import CharTokenizer

            vocab_file = official_dir / "vocab.json"

            if not vocab_file.exists():
                logger.warning(f"vocab.json not found at {vocab_file}")
                return

            # Initialize tokenizer
            self.tokenizer = CharTokenizer(
                vocab_file=str(vocab_file),
                bos_token="<BOS>",
                eos_token="<EOS>",
                sep_token="<SEP>",
                unk_token="<UNK>",
                pad_token="<PAD>"
            )

            # Try to load model
            try:
                from transformers import GPT2LMHeadModel
                import torch

                self.device = "cuda" if torch.cuda.is_available() else "cpu"
                self.model = GPT2LMHeadModel.from_pretrained(str(self.model_path))
                self.model.to(self.device)
                self.model.eval()

                self.use_official = True
                logger.info(f"✅ Official PagPassGPT loaded successfully on {self.device}")

            except Exception as e:
                logger.warning(f"Failed to load model: {e}")
                logger.info("Will use fallback generation method")

        except ImportError as e:
            logger.warning(f"Failed to import official tokenizer: {e}")
            logger.info("Will use fallback generation method")
        except Exception as e:
            logger.warning(f"Failed to initialize official PagPassGPT: {e}")
            logger.info("Will use fallback generation method")

    def generate(
        self,
        pattern: Optional[str] = None,
        prefix: str = "",
        num_passwords: int = 1000000,
        max_length: int = 12
    ) -> List[str]:
        """
        Generate passwords using PagPassGPT

        Args:
            pattern: Optional PCFG pattern (e.g., "L4N2S2")
            prefix: Fixed prefix for all passwords
            num_passwords: Number of passwords to generate
            max_length: Maximum password length

        Returns:
            List of generated passwords
        """
        if self.use_official:
            return self._generate_official(pattern, num_passwords)
        else:
            return self._generate_fallback(num_passwords, max_length)

    def _generate_official(
        self,
        pattern: Optional[str],
        num_passwords: int
    ) -> List[str]:
        """
        Generate passwords using official PagPassGPT

        Args:
            pattern: PCFG pattern
            num_passwords: Number to generate

        Returns:
            List of passwords
        """
        import torch

        passwords = []
        batch_size = 1000
        num_batches = (num_passwords + batch_size - 1) // batch_size

        try:
            # Encode input
            if pattern:
                input_ids = self.tokenizer.encode_forgen(pattern)
            else:
                input_ids = self.tokenizer.encode_forgen("")

            # Add SEP token
            import torch
            sep_token_id = self.tokenizer.sep_token_id
            input_ids = torch.concat([input_ids, torch.tensor([sep_token_id])]).view(1, -1)

            # Generate in batches
            for _ in range(num_batches):
                with torch.no_grad():
                    outputs = self.model.generate(
                        input_ids.to(self.device),
                        max_length=32,
                        do_sample=True,
                        top_k=50,
                        top_p=0.95,
                        temperature=0.8,
                        num_return_sequences=batch_size,
                        pad_token_id=self.tokenizer.pad_token_id
                    )

                # Decode
                batch_passwords = self.tokenizer.batch_decode(outputs)

                # Extract passwords (after separator)
                for pwd in batch_passwords:
                    if '<SEP>' in pwd:
                        password = pwd.split('<SEP>')[1].replace('<EOS>', '').strip()
                        if 4 <= len(password) <= 20:
                            passwords.append(password)

                if len(passwords) >= num_passwords:
                    break

            return passwords[:num_passwords]

        except Exception as e:
            logger.error(f"Error in official generation: {e}")
            return self._generate_fallback(num_passwords, 12)

    def _generate_fallback(
        self,
        num_passwords: int,
        max_length: int
    ) -> List[str]:
        """
        Fallback generation method (rule-based)

        This is used when:
        - No trained model is available
        - Model loading fails

        Args:
            num_passwords: Number to generate
            max_length: Max length

        Returns:
            List of passwords
        """
        logger.info("Using fallback password generation")

        import random
        import string

        passwords = set()

        # Common password patterns
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        special = "!@#$%"

        # RockYou-derived common patterns (simplified)
        patterns = [
            lambda: ''.join(random.choices(lowercase, k=random.randint(6, 10))),
            lambda: ''.join(random.choices(lowercase + digits, k=random.randint(6, 10))),
            lambda: ''.join(random.choices(lowercase, k=1)) + ''.join(random.choices(digits, k=4)),
            lambda: ''.join(random.choices(lowercase, k=6)) + ''.join(random.choices(digits, k=2)),
            lambda: ''.join(random.choices(uppercase + lowercase, k=random.randint(6, 8))) + ''.join(random.choices(digits, k=2)),
            lambda: ''.join(random.choices(lowercase + uppercase + digits, k=random.randint(8, 12))),
        ]

        attempts = 0
        max_attempts = num_passwords * 5

        while len(passwords) < num_passwords and attempts < max_attempts:
            pattern = random.choice(patterns)
            password = pattern()

            if 4 <= len(password) <= max_length:
                passwords.add(password)

            attempts += 1

        return list(passwords)[:num_passwords]


# Global generator instance
_generator = None


def get_generator() -> PagPassGPTGenerator:
    """
    Get or create global generator instance

    Returns:
        PagPassGPTGenerator instance
    """
    global _generator

    if _generator is None:
        _generator = PagPassGPTGenerator()

    return _generator


def check_model_available() -> bool:
    """
    Check if trained PagPassGPT model is available

    Returns:
        True if model exists and can be loaded
    """
    try:
        gen = get_generator()
        return gen.use_official
    except:
        return False
