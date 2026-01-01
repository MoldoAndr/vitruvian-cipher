"""Dramatiq worker for hash cracking tasks."""

import logging
import os

import dramatiq
from dramatiq.brokers.rabbitmq import RabbitmqBroker

from app.config import get_settings
from app.cracking.pipeline import run_cracking_pipeline

# Configure logging
from app.utils.logging import setup_logging
setup_logging()

logger = logging.getLogger(__name__)

# Initialize settings
settings = get_settings()

# Configure RabbitMQ broker
broker = RabbitmqBroker(
    url=settings.rabbitmq_url,
    max_priority=3
)
dramatiq.set_broker(broker)


def _execute_cracking_job(job_id: str, target_hash: str, hash_type_id: int, timeout: int) -> dict:
    logger.info(f"Worker {os.getpid()}: Processing job {job_id}")

    try:
        result = run_cracking_pipeline(job_id, target_hash, hash_type_id, timeout)
        logger.info(f"Worker {os.getpid()}: Job {job_id} completed with status {result.get('status')}")
        return result
    except Exception as e:
        logger.error(f"Worker {os.getpid()}: Job {job_id} failed with error: {e}")
        raise


@dramatiq.actor(
    queue_name=settings.rabbitmq_queue,
    max_retries=3,
    time_limit=settings.worker_timeout * 1000,  # Convert to ms
    priority=1  # Normal priority
)
def process_cracking_job(job_id: str, target_hash: str, hash_type_id: int, timeout: int) -> dict:
    """Process hash cracking job.

    Args:
        job_id: Unique job identifier
        target_hash: Target hash to crack
        hash_type_id: Hashcat hash mode
        timeout: Maximum execution time

    Returns:
        Final job state dict
    """
    return _execute_cracking_job(job_id, target_hash, hash_type_id, timeout)


# High priority actor
@dramatiq.actor(
    queue_name=f"{settings.rabbitmq_queue}_high",
    max_retries=3,
    time_limit=settings.worker_timeout * 1000,
    priority=3  # High priority
)
def process_cracking_job_high(job_id: str, target_hash: str, hash_type_id: int, timeout: int) -> dict:
    """Process high-priority cracking job.

    Args:
        job_id: Unique job identifier
        target_hash: Target hash to crack
        hash_type_id: Hashcat hash mode
        timeout: Maximum execution time

    Returns:
        Final job state dict
    """
    return _execute_cracking_job(job_id, target_hash, hash_type_id, timeout)


# Low priority actor
@dramatiq.actor(
    queue_name=f"{settings.rabbitmq_queue}_low",
    max_retries=3,
    time_limit=settings.worker_timeout * 1000,
    priority=0  # Low priority
)
def process_cracking_job_low(job_id: str, target_hash: str, hash_type_id: int, timeout: int) -> dict:
    """Process low-priority cracking job.

    Args:
        job_id: Unique job identifier
        target_hash: Target hash to crack
        hash_type_id: Hashcat hash mode
        timeout: Maximum execution time

    Returns:
        Final job state dict
    """
    return _execute_cracking_job(job_id, target_hash, hash_type_id, timeout)


if __name__ == "__main__":
    # Run worker
    logger.info(f"Starting Dramatiq worker (concurrency={settings.worker_concurrency})")
    # Note: This worker is typically started via: dramatiq app.workers.cracking_worker
    pass
