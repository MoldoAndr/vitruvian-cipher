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


# Global config instance
config = Config()


# Service names for display
SERVICE_NAMES = {
    "password_checker": "Password Checker",
    "theory_specialist": "Theory Specialist",
    "choice_maker": "Choice Maker"
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
