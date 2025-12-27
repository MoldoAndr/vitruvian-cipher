"""
Configuration module for Agent CLI.
Contains all API endpoints and settings.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
import os
from pathlib import Path


@dataclass
class EndpointConfig:
    """Configuration for a single service endpoint."""
    base_url: str
    endpoints: Dict[str, str]
    
    def get_url(self, endpoint: str) -> str:
        """Get full URL for an endpoint."""
        return f"{self.base_url}{self.endpoints.get(endpoint, '')}"


@dataclass
class Config:
    """Main configuration class for all agent services."""
    
    password_checker: EndpointConfig = field(default_factory=lambda: EndpointConfig(
        base_url=os.getenv("PASSWORD_CHECKER_URL", "http://localhost:9000"),
        endpoints={
            "health": "/health",
            "score": "/score"
        }
    ))
    
    theory_specialist: EndpointConfig = field(default_factory=lambda: EndpointConfig(
        base_url=os.getenv("THEORY_SPECIALIST_URL", "http://localhost:8100"),
        endpoints={
            "health": "/health",
            "generate": "/generate",
            "ingest": "/ingest",
            "conversations": "/conversations"
        }
    ))
    
    choice_maker: EndpointConfig = field(default_factory=lambda: EndpointConfig(
        base_url=os.getenv("CHOICE_MAKER_URL", "http://localhost:8081"),
        endpoints={
            "health": "/health",
            "extract": "/predict"
        }
    ))
    
    command_executor: EndpointConfig = field(default_factory=lambda: EndpointConfig(
        base_url=os.getenv("COMMAND_EXECUTOR_URL", "http://localhost:8085"),
        endpoints={
            "health": "/health",
            "pqc_health": "/pqc/health",
            "execute": "/execute",
            "operations": "/operations",
            "ciphers": "/ciphers"
        }
    ))


# Global config instance
config = Config()


# Service names for display
SERVICE_NAMES = {
    "password_checker": "Password Checker",
    "theory_specialist": "Theory Specialist",
    "choice_maker": "Choice Maker",
    "command_executor": "Command Executor"
}

# Agent modes
AGENT_MODES = {
    "password": {
        "name": "Password Analysis",
        "description": "Analyze password strength using AI, zxcvbn, and breach detection",
        "icon": "🔐"
    },
    "crypto": {
        "name": "Cryptography Expert",
        "description": "Ask questions about cryptographic algorithms and security",
        "icon": "🧠"
    },
    "choice": {
        "name": "Choice Maker",
        "description": "Extract intents and entities from text",
        "icon": "🎯"
    },
    "document": {
        "name": "Document Ingestion",
        "description": "Add documents to the knowledge base",
        "icon": "📄"
    },
    "executor": {
        "name": "Command Executor",
        "description": "Execute cryptographic operations via OpenSSL",
        "icon": "⚡"
    }
}

# Password checker components
PASSWORD_COMPONENTS = {
    "pass_strength_ai": {
        "name": "AI Engine",
        "description": "Neural network-based password strength analysis"
    },
    "zxcvbn": {
        "name": "zxcvbn",
        "description": "Dropbox's entropy-based password strength estimator"
    },
    "haveibeenpwned": {
        "name": "Breach Check",
        "description": "Check if password appears in known data breaches"
    }
}

# Choice maker modes
CHOICE_MODES = {
    "both": "Extract both intent and entities",
    "intent_extraction": "Extract intent only",
    "entity_extraction": "Extract entities only"
}

# Document types
DOCUMENT_TYPES = {
    "pdf": "PDF Document",
    "markdown": "Markdown File",
    "text": "Plain Text"
}

# Command executor operations (grouped)
EXECUTOR_OPERATIONS = {
    "encoding": {
        "base64_encode": "Encode data to Base64",
        "base64_decode": "Decode Base64 data",
        "hex_encode": "Encode data to hexadecimal",
        "hex_decode": "Decode hexadecimal data",
    },
    "random": {
        "random_bytes": "Generate random bytes (Base64)",
        "random_hex": "Generate random hex string",
        "random_base64": "Generate random Base64 string",
    },
    "hashing": {
        "hash": "Compute hash digest (sha256, sha512)",
        "hmac": "Compute HMAC",
    },
    "symmetric": {
        "aes_keygen": "Generate AES key + IV + HMAC key",
        "aes_encrypt": "AES-CBC encrypt with HMAC",
        "aes_decrypt": "AES-CBC decrypt (verifies HMAC)",
    },
    "asymmetric": {
        "rsa_keygen": "Generate RSA key pair",
        "rsa_pubkey": "Extract RSA public key from private key",
        "rsa_sign": "Sign data with RSA",
        "rsa_verify": "Verify RSA signature",
        "rsa_encrypt": "Encrypt with RSA (OAEP)",
        "rsa_decrypt": "Decrypt with RSA (OAEP)",
    },
    "pqc": {
        "pqc_sig_keygen": "Generate PQC signature key pair (ML-DSA/Falcon)",
        "pqc_sig_sign": "Sign data with PQC private key",
        "pqc_sig_verify": "Verify PQC signature with public key",
    }
}
