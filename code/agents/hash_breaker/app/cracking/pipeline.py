"""Multi-phase cracking pipeline orchestrator."""

import logging
import time
import uuid
from datetime import datetime
from typing import Dict

from app.config import get_settings
from app.cracking.phases import (
    quick_dictionary_attack,
    rule_based_attack,
    ai_generation_attack,
    mask_attack
)
from app.models.enums import JobStatus
from app.models.schemas import JobState
from app.utils.redis_client import get_redis
from app.utils.metrics import MetricsContext, jobs_total, job_duration

logger = logging.getLogger(__name__)


class CrackingPipeline:
    """Multi-phase password cracking pipeline."""

    def __init__(self):
        """Initialize cracking pipeline."""
        self.settings = get_settings()
        self.redis = get_redis()

    def execute(self, job_id: str, target_hash: str, hash_type_id: int, timeout: int) -> Dict:
        """Execute multi-phase cracking pipeline.

        Args:
            job_id: Unique job identifier
            target_hash: Target hash to crack
            hash_type_id: Hashcat hash mode
            timeout: Total timeout in seconds

        Returns:
            Final job state dict
        """
        start_time = time.time()
        total_attempts = 0

        # Initialize job state
        job_state = JobState(
            job_id=job_id,
            status=JobStatus.RUNNING,
            submitted_at=datetime.utcnow()
        )

        self.redis.set(f"job:{job_id}", job_state.model_dump(mode='json'), ex=self.settings.redis_ttl)
        logger.info(f"Job {job_id}: Starting pipeline (timeout={timeout}s)")

        try:
            # Phase 1: Quick Dictionary Attack
            elapsed = time.time() - start_time
            if elapsed < timeout:
                phase_timeout = min(
                    self.settings.get_phase_budget(1, timeout),
                    timeout - elapsed
                )

                with MetricsContext(job_id, phase="Quick Dictionary"):
                    result = quick_dictionary_attack(target_hash, hash_type_id, phase_timeout)
                    total_attempts += result.get("attempts", 0)

                    self._update_progress(job_id, 15, "Phase 1: Quick Dictionary Attack", 1)

                    if result.get("cracked"):
                        return self._success(job_id, result["password"], 1, total_attempts, elapsed)

            # Phase 2: Rule-Based Attack
            elapsed = time.time() - start_time
            if elapsed < timeout:
                phase_timeout = min(
                    self.settings.get_phase_budget(2, timeout),
                    timeout - elapsed
                )

                self._update_progress(job_id, 35, "Phase 2: Rule-Based Attack", 2)

                with MetricsContext(job_id, phase="Rule-Based"):
                    result = rule_based_attack(target_hash, hash_type_id, phase_timeout)
                    total_attempts += result.get("attempts", 0)

                    if result.get("cracked"):
                        return self._success(job_id, result["password"], 2, total_attempts, elapsed)

            # Phase 3: PagPassGPT AI Generation
            elapsed = time.time() - start_time
            if elapsed < timeout:
                phase_timeout = min(
                    self.settings.get_phase_budget(3, timeout),
                    timeout - elapsed
                )

                self._update_progress(job_id, 60, "Phase 3: AI Generation (PagPassGPT)", 3)

                with MetricsContext(job_id, phase="AI Generation"):
                    result = ai_generation_attack(target_hash, hash_type_id, phase_timeout)
                    total_attempts += result.get("attempts", 0)

                    if result.get("cracked"):
                        return self._success(job_id, result["password"], 3, total_attempts, elapsed)

            # Phase 4: Limited Mask Attack
            elapsed = time.time() - start_time
            if elapsed < timeout:
                phase_timeout = timeout - elapsed  # Use remaining time

                self._update_progress(job_id, 80, "Phase 4: Limited Mask Attack", 4)

                with MetricsContext(job_id, phase="Mask Attack"):
                    result = mask_attack(target_hash, hash_type_id, phase_timeout)
                    total_attempts += result.get("attempts", 0)

                    if result.get("cracked"):
                        return self._success(job_id, result["password"], 4, total_attempts, elapsed)

            # All phases failed
            logger.info(f"Job {job_id}: Password not found after all phases")
            return self._failure(job_id, "Password not found after all phases", 4, total_attempts, elapsed)

        except Exception as e:
            logger.error(f"Job {job_id}: Pipeline error - {e}")
            return self._failure(job_id, f"Internal error: {str(e)}", None, total_attempts, time.time() - start_time)

    def _update_progress(self, job_id: str, progress: int, phase: str, phase_num: int) -> None:
        """Update job progress in Redis.

        Args:
            job_id: Job identifier
            progress: Progress percentage (0-100)
            phase: Current phase name
            phase_num: Phase number (1-4)
        """
        elapsed = time.time()
        updates = {
            "progress": progress,
            "current_phase": phase,
            "phase_number": phase_num
        }

        self.redis.update(f"job:{job_id}", updates)
        logger.debug(f"Job {job_id}: Progress {progress}% - {phase}")

    def _success(
        self,
        job_id: str,
        password: str,
        phase: int,
        attempts: int,
        elapsed: float
    ) -> Dict:
        """Handle successful crack.

        Args:
            job_id: Job identifier
            password: Cracked password
            phase: Phase where password was found
            attempts: Total attempts
            elapsed: Elapsed time

        Returns:
            Final job state dict
        """
        # Get current job state and update it
        current_state = self.redis.get(f"job:{job_id}") or {}

        result_state = {
            **current_state,
            "job_id": job_id,
            "status": JobStatus.SUCCESS,
            "result": password,
            "cracked_in_phase": phase,
            "attempts": attempts,
            "time_elapsed": elapsed,
            "progress": 100
        }

        self.redis.set(f"job:{job_id}", result_state, ex=self.settings.redis_ttl)

        jobs_total.labels(status="success").inc()
        job_duration.labels(status="success").observe(elapsed)

        logger.info(f"Job {job_id}: SUCCESS - Password '{password}' cracked in phase {phase} ({elapsed:.2f}s)")

        return result_state

    def _failure(
        self,
        job_id: str,
        reason: str,
        phase: int,
        attempts: int,
        elapsed: float
    ) -> Dict:
        """Handle failed crack.

        Args:
            job_id: Job identifier
            reason: Failure reason
            phase: Last phase attempted
            attempts: Total attempts
            elapsed: Elapsed time

        Returns:
            Final job state dict
        """
        # Get current job state and update it
        current_state = self.redis.get(f"job:{job_id}") or {}

        result_state = {
            **current_state,
            "job_id": job_id,
            "status": JobStatus.FAILED,
            "reason": reason,
            "last_phase": phase,
            "attempts": attempts,
            "time_elapsed": elapsed,
            "progress": 100
        }

        self.redis.set(f"job:{job_id}", result_state, ex=self.settings.redis_ttl)

        jobs_total.labels(status="failed").inc()
        job_duration.labels(status="failed").observe(elapsed)

        logger.info(f"Job {job_id}: FAILED - {reason} after {elapsed:.2f}s")

        return result_state


def run_cracking_pipeline(job_id: str, target_hash: str, hash_type_id: int, timeout: int) -> Dict:
    """Run cracking pipeline (convenience function for Dramatiq).

    Args:
        job_id: Job identifier
        target_hash: Target hash
        hash_type_id: Hash mode
        timeout: Timeout in seconds

    Returns:
        Final job state
    """
    pipeline = CrackingPipeline()
    return pipeline.execute(job_id, target_hash, hash_type_id, timeout)
