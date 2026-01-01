"""
Configuration management for Hash Breaker Microservice.

Uses pydantic-settings for type-safe configuration with environment variable support.
"""

from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LogLevel(str, Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class HashType(int, Enum):
    """Supported hash types (Hashcat hash modes)."""
    MD5 = 0
    SHA1 = 100
    SHA256 = 1400
    SHA512 = 1800
    NTLM = 1000
    BCRYPT = 3200


class Settings(BaseSettings):
    """Application settings.

    Loads from environment variables with fallback to defaults.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    app_name: str = "Hash Breaker Microservice"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: LogLevel = LogLevel.INFO
    environment: Literal["development", "testing", "production"] = "development"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1
    reload: bool = False

    # Message Queue (RabbitMQ)
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    rabbitmq_queue: str = "cracking"
    rabbitmq_prefetch_count: int = 2

    # State Store (Redis)
    redis_url: str = "redis://localhost:6379/0"
    redis_db: int = 0
    redis_ttl: int = 86400  # 24 hours
    redis_max_connections: int = 50

    # Job Configuration
    default_timeout: int = 60
    min_timeout: int = 10
    max_timeout: int = 3600
    max_concurrent_jobs: int = 10

    # Phase Time Allocations (must sum to 1.0)
    phase1_time_ratio: float = 0.10  # Quick Dictionary
    phase2_time_ratio: float = 0.25  # Rule-Based
    phase3_time_ratio: float = 0.35  # PagPassGPT
    phase4_time_ratio: float = 0.30  # Mask Attack

    # Worker Configuration
    worker_concurrency: int = 4
    worker_prefetch_multiplier: int = 2
    worker_timeout: int = 600  # 10 minutes

    # GPU Configuration
    gpu_enable: bool = True
    cuda_visible_devices: str = "all"

    # Paths
    base_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent)
    models_dir: Path = Field(default_factory=lambda: Path("./models"))
    wordlists_dir: Path = Field(default_factory=lambda: Path("./wordlists"))
    rules_dir: Path = Field(default_factory=lambda: Path("./data/rules"))
    logs_dir: Path = Field(default_factory=lambda: Path("./logs"))

    # Hashcat Configuration
    hashcat_path: str = "/usr/bin/hashcat"
    hashcat_workload_profile: Literal["low", "medium", "high", "insane"] = "high"
    hashcat_force: bool = True
    hashcat_potfile_disable: bool = True

    # John the Ripper Configuration
    john_path: str = "/usr/bin/john"
    john_config: str = "/etc/john/john.conf"

    # PagPassGPT Configuration
    pagpassgpt_model_path: Path = Field(
        default_factory=lambda: Path("./models/pagpassgpt")
    )
    pagpassgpt_temperature: float = 0.8
    pagpassgpt_top_k: int = 40
    pagpassgpt_batch_size: int = 100000
    pagpassgpt_threshold: int = 100000  # D&C-GEN threshold

    # Monitoring
    metrics_enabled: bool = True
    metrics_port: int = 9090

    # Rate Limiting (optional)
    rate_limit_enabled: bool = False
    rate_limit_per_hour: int = 100

    @field_validator("phase1_time_ratio", "phase2_time_ratio", "phase3_time_ratio", "phase4_time_ratio")
    @classmethod
    def validate_time_ratios(cls, v):
        """Validate time ratio is between 0 and 1."""
        if not 0 < v < 1:
            raise ValueError("Time ratio must be between 0 and 1")
        return v

    @field_validator("pagpassgpt_model_path", "models_dir", "wordlists_dir")
    @classmethod
    def validate_paths(cls, v):
        """Validate and create directories if needed."""
        if isinstance(v, str):
            v = Path(v)
        if isinstance(v, Path):
            v.mkdir(parents=True, exist_ok=True)
        return v

    def get_phase_budget(self, phase: int, total_timeout: int) -> int:
        """Get time budget for a specific phase.

        Args:
            phase: Phase number (1-4)
            total_timeout: Total timeout in seconds

        Returns:
            Time budget for the phase in seconds
        """
        ratios = {
            1: self.phase1_time_ratio,
            2: self.phase2_time_ratio,
            3: self.phase3_time_ratio,
            4: self.phase4_time_ratio,
        }
        return int(total_timeout * ratios.get(phase, 0))


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings instance.

    Returns:
        Settings: Application settings
    """
    return settings
