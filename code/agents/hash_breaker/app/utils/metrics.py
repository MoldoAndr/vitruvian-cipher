"""Prometheus metrics collection and exposition."""

import logging
import time
from prometheus_client import Counter, Gauge, Histogram, CollectorRegistry, generate_latest
from prometheus_client.exposition import CONTENT_TYPE_LATEST
from typing import Callable, Optional
from functools import wraps

logger = logging.getLogger(__name__)

# Create custom registry
registry = CollectorRegistry()

# Counters
jobs_total = Counter(
    "hash_breaker_jobs_total",
    "Total number of jobs processed",
    ["status"],
    registry=registry
)

guesses_total = Counter(
    "hash_breaker_guesses_total",
    "Total password guesses made",
    ["phase"],
    registry=registry
)

# Gauges
jobs_current = Gauge(
    "hash_breaker_jobs_current",
    "Current number of jobs by status",
    ["status"],
    registry=registry
)

queue_depth = Gauge(
    "hash_breaker_queue_depth",
    "Current queue depth by priority",
    ["priority"],
    registry=registry
)

gpu_utilization = Gauge(
    "hash_breaker_gpu_utilization",
    "GPU utilization percentage",
    ["worker_id", "gpu_id"],
    registry=registry
)

worker_jobs_active = Gauge(
    "hash_breaker_worker_jobs_current",
    "Current jobs per worker",
    ["worker_id"],
    registry=registry
)

success_rate = Gauge(
    "hash_breaker_success_rate",
    "Success rate by hash type",
    ["hash_type"],
    registry=registry
)

# Histograms
job_duration = Histogram(
    "hash_breaker_jobs_duration_seconds",
    "Job execution duration",
    ["status"],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600, float("inf")),
    registry=registry
)

phase_duration = Histogram(
    "hash_breaker_phase_duration_seconds",
    "Phase execution duration",
    ["phase"],
    buckets=(1, 5, 10, 20, 30, 60, 120, 300, float("inf")),
    registry=registry
)


class MetricsContext:
    """Context manager for tracking metrics."""

    def __init__(self, job_id: str, phase: Optional[str] = None):
        """Initialize metrics context.

        Args:
            job_id: Job identifier
            phase: Cracking phase (optional)
        """
        self.job_id = job_id
        self.phase = phase
        self.start_time: Optional[float] = None

    def __enter__(self):
        """Enter context, start timer."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context, record metrics."""
        if self.start_time is None:
            return

        duration = time.time() - self.start_time

        if self.phase:
            phase_duration.labels(phase=self.phase).observe(duration)

        logger.debug(f"Metrics: job_id={self.job_id}, phase={self.phase}, duration={duration:.2f}s")


def track_job_status(status: str) -> Callable:
    """Decorator to track job completion status.

    Args:
        status: Job status (success/failed/cancelled)

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            jobs_total.labels(status=status).inc()
            return result
        return wrapper
    return decorator


def generate_metrics() -> bytes:
    """Generate Prometheus metrics exposition.

    Returns:
        Metrics in Prometheus text format
    """
    return generate_latest(registry)


def get_content_type() -> str:
    """Get Prometheus content type.

    Returns:
        Content type string
    """
    return CONTENT_TYPE_LATEST
