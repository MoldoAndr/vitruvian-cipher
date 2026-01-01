# Architecture: Distributed Hash Auditing Service

This document outlines the architecture for a single-endpoint, containerized service designed for auditing password hash strength. The system is built to be robust, scalable, and modular, integrating multiple cracking tools to maximize effectiveness.

## 1. Guiding Principles

*   **Decoupling:** The API for submitting jobs is decoupled from the long-running, computationally-intensive cracking tasks.
*   **Scalability:** The architecture allows for multiple cracking "worker" nodes to run in parallel to process a high volume of jobs.
*   **Modularity:** Each component (API, queue, worker, tools) is a distinct part of the system, allowing for easier maintenance and upgrades.
*   **Portability:** The entire system is containerized with Docker, ensuring it can run consistently across different environments.

## 2. Core Components

The system is composed of four main components: an API Gateway, a Job Queue, Cracking Workers, and a State Database.

### 2.1. API Gateway

*   **Technology:** Python (FastAPI)
*   **Purpose:** Provides the single public-facing endpoint for the service. It is lightweight and designed only for handling web requests, not for computation.
*   **Endpoints:**
    *   `POST /audit-hash`: The primary endpoint to submit a new job.
        *   **Request Body:** `{ "hash": "string", "hash_type_id": int, "timeout_seconds": int }`
        *   **Actions:**
            1.  Validates the input.
            2.  Generates a unique `job_id`.
            3.  Pushes a new job message onto the Job Queue.
            4.  Immediately returns the `job_id` to the client.
    *   `GET /status/{job_id}`: The endpoint for health checks and status updates.
        *   **Actions:**
            1.  Queries the State Database (Redis) using the `job_id`.
            2.  Returns the current status of the job, including progress and time remaining.

### 2.2. Job Queue

*   **Technology:** RabbitMQ or Redis
*   **Purpose:** Acts as a message broker that decouples the API Gateway from the Cracking Workers. This prevents the API from getting blocked by long-running tasks and allows jobs to be distributed among multiple workers.
*   **Flow:** The API Gateway publishes a "job" message. A worker consumes the message to start processing.

### 2.3. State Database

*   **Technology:** Redis
*   **Purpose:** A fast, in-memory key-value store used to maintain the real-time state of each job.
*   **Data Structure:** A simple hash map for each job.
    *   `Key`: `job:<job_id>`
    *   `Value`: `{ "status": "pending|running|success|failed", "progress": "15%", "time_remaining": 45, "current_phase": "Dictionary Attack", "result": "null|cracked_password" }`
*   **Interaction:** The Cracking Worker continuously updates this record every 10 seconds. The API Gateway reads from it for status checks.

### 2.4. Cracking Workers

*   **Technology:** Python (Celery for task management) running in a Docker container.
*   **Purpose:** The computational core of the system. These are long-running processes that listen for jobs on the queue, execute them, and update the state.
*   **Internal Tools:**
    *   **Hashcat:** GPU-accelerated tool for brute-force, mask, and dictionary attacks. The primary workhorse.
    *   **John the Ripper (JtR):** CPU-based tool, excellent for rule-based attacks on wordlists.
    *   **PassGAN:** A pre-trained Generative Adversarial Network (GAN) model used to generate highly probable, human-like password candidates. This acts as an intelligent, dynamic wordlist generator.
*   **Data/Models:**
    *   **PassGAN Model:** The pre-trained model files will be downloaded and included in the Docker image during the build process (e.g., from a source like Hugging Face).
    *   **Wordlists:** Large wordlists (RockYou, Pwned Passwords, etc.) will be mounted into the container as a Docker volume. This prevents bloating the image and allows for easy updates to the wordlists without rebuilding the entire image.

## 3. Dockerization (Multi-Stage Build)

A multi-stage `Dockerfile` will be used to create an optimized and clean final image.

*   **Stage 1: `builder`**
    *   Starts from a full Python base image.
    *   Installs all build-time dependencies (e.g., `gcc`, `python-dev`).
    *   Downloads and installs the required Python packages (FastAPI, Celery, Redis client) into a virtual environment.
    *   Downloads the PassGAN model files from a remote source.

*   **Stage 2: `final`**
    *   Starts from a slim base image (e.g., `python:3.10-slim`).
    *   Installs runtime dependencies like `hashcat`, `john`, and any required libraries (`libcuda` for GPU access).
    *   Copies the Python virtual environment and the PassGAN model from the `builder` stage.
    *   Sets the final `CMD` or `ENTRYPOINT` to launch the API server or the Celery worker process. This allows the same image to be used for both services, configured via environment variables.
