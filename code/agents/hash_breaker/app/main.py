"""Hash Breaker Microservice API.

FastAPI application exposing REST endpoints for hash auditing.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.models.enums import ErrorCode, JobPriority, JobStatus
from app.models.schemas import (
    HashAuditRequest,
    JobSubmissionResponse,
    JobStatusResponse,
    JobCancelResponse,
    HealthResponse,
    ErrorResponse
)
from app.utils.logging import setup_logging
from app.utils.metrics import generate_metrics, get_content_type
from app.utils.redis_client import get_redis
from app.workers.cracking_worker import process_cracking_job

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize settings
settings = get_settings()

# Initialize FastAPI
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered password hash auditing service using PagPassGPT",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Redis
redis = get_redis()


@app.get("/v1/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    """Health check endpoint for load balancers and monitoring.

    Returns:
        Health status with dependency checks
    """
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.utcnow(),
        dependencies={
            "redis": {
                "status": "healthy" if redis.ping() else "unhealthy"
            }
        },
        workers={
            "total": settings.worker_concurrency,
            "active": 0,
            "idle": settings.worker_concurrency
        },
        queue={
            "depth": redis.get_queue_depth(settings.rabbitmq_queue)
        }
    )


@app.post(
    "/v1/audit-hash",
    response_model=JobSubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Cracking"]
)
async def submit_audit_job(request: HashAuditRequest):
    """Submit a new hash cracking job.

    The job will be processed through a multi-phase pipeline:
    1. Quick Dictionary Attack (10% time)
    2. Rule-Based Attack (25% time)
    3. PagPassGPT AI Generation (35% time)
    4. Limited Mask Attack (30% time)

    Args:
        request: Job submission request

    Returns:
        Job submission response with job_id

    Raises:
        HTTPException: If validation fails
    """
    # Validate hash format (basic check)
    if not request.hash or not request.hash.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": ErrorCode.INVALID_HASH_FORMAT,
                    "message": "Hash cannot be empty"
                }
            }
        )

    # Generate job ID
    job_id = str(uuid.uuid4())

    # Create initial job state
    from app.models.schemas import JobState
    job_state = JobState(
        job_id=job_id,
        status=JobStatus.PENDING,
        submitted_at=datetime.utcnow()
    )

    # Store in Redis (use JSON mode for datetime serialization)
    if not redis.set(f"job:{job_id}", job_state.model_dump(mode='json')):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": ErrorCode.INTERNAL_ERROR,
                    "message": "Failed to create job"
                }
            }
        )

    # Send to Dramatiq queue (select based on priority)
    if request.priority == JobPriority.HIGH:
        process_cracking_job_high.send(job_id, request.hash, request.hash_type_id, request.timeout_seconds)
    elif request.priority == JobPriority.LOW:
        process_cracking_job_low.send(job_id, request.hash, request.hash_type_id, request.timeout_seconds)
    else:
        process_cracking_job.send(job_id, request.hash, request.hash_type_id, request.timeout_seconds)

    logger.info(f"Job {job_id}: Submitted (hash_type={request.hash_type_id}, timeout={request.timeout_seconds}s)")

    return JobSubmissionResponse(
        job_id=job_id,
        status=JobStatus.PENDING
    )


@app.get("/v1/status/{job_id}", response_model=JobStatusResponse, tags=["Cracking"])
async def get_job_status(job_id: str):
    """Query the status of a submitted job.

    Args:
        job_id: Unique job identifier

    Returns:
        Current job status

    Raises:
        HTTPException: If job not found
    """
    job_state = redis.get(f"job:{job_id}")

    if job_state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": ErrorCode.JOB_NOT_FOUND,
                    "message": f"Job {job_id} not found"
                }
            }
        )

    # Convert datetime strings back to datetime objects
    if job_state.get("submitted_at"):
        job_state["submitted_at"] = datetime.fromisoformat(job_state["submitted_at"])
    if job_state.get("started_at"):
        job_state["started_at"] = datetime.fromisoformat(job_state["started_at"])

    # Calculate time remaining if running
    if job_state.get("status") == JobStatus.RUNNING:
        started_at = job_state.get("started_at")
        if started_at:
            # started_at is now a datetime object from the conversion above
            elapsed = (datetime.utcnow() - started_at).total_seconds()
            timeout = 60  # This should come from job state
            job_state["time_remaining"] = max(0, int(timeout - elapsed))

    return JobStatusResponse(**job_state)


@app.post("/v1/jobs/{job_id}/cancel", response_model=JobCancelResponse, tags=["Cracking"])
async def cancel_job(job_id: str):
    """Cancel a running or pending job.

    Args:
        job_id: Unique job identifier

    Returns:
        Cancellation confirmation

    Raises:
        HTTPException: If job not found or already completed
    """
    job_state = redis.get(f"job:{job_id}")

    if job_state is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": ErrorCode.JOB_NOT_FOUND,
                    "message": f"Job {job_id} not found"
                }
            }
        )

    current_status = job_state.get("status")

    if current_status in [JobStatus.SUCCESS, JobStatus.FAILED]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "JOB_ALREADY_COMPLETED",
                    "message": f"Job already {current_status}"
                }
            }
        )

    # Update status to cancelled
    updates = {
        "status": JobStatus.CANCELLED,
        "reason": "User requested cancellation"
    }
    redis.update(f"job:{job_id}", updates)

    logger.info(f"Job {job_id}: Cancelled by user")

    return JobCancelResponse(
        job_id=job_id,
        status=JobStatus.CANCELLED,
        message="Job cancelled successfully",
        cancelled_at=datetime.utcnow()
    )


@app.get("/v1/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus metrics endpoint.

    Returns:
        Metrics in Prometheus text format
    """
    metrics_data = generate_metrics()
    return PlainTextResponse(
        content=metrics_data,
        media_type=get_content_type()
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler.

    Args:
        request: Request object
        exc: Exception

    Returns:
        Error response
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={
            "error": {
                "code": ErrorCode.INTERNAL_ERROR,
                "message": "An internal error occurred"
            }
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers,
        reload=settings.reload,
        log_level=settings.log_level.value.lower()
    )
