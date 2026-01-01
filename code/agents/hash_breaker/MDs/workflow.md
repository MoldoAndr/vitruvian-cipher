# Workflow: End-to-End Hash Auditing Process

This document describes the step-by-step data flow and logic for a single hash auditing job, from initial request to final result.

## 1. Job Submission

1.  **Client Request:** A user sends a `POST` request to the `/audit-hash` endpoint of the API Gateway.
    *   **Payload:** `{ "hash": "a1b2c3d4...", "hash_type_id": 0, "timeout_seconds": 60 }`
2.  **API Gateway Handling:**
    *   The API server receives the request.
    *   It generates a unique identifier, e.g., `job_id = "uuid-12345"`.
    *   It creates an initial state record in the Redis State Database:
        `job:uuid-12345 = { "status": "pending", "progress": "0%", ... }`
    *   It publishes a message to the Job Queue containing all necessary job information: `{ "job_id": "uuid-12345", "hash": "...", "hash_type_id": 0, "timeout": 60 }`.
    *   It immediately responds to the client with a `202 Accepted` status and the job ID:
        `{ "job_id": "uuid-12345" }`

## 2. Job Execution (Worker Side)

This is the core, multi-phased process executed by a Cracking Worker.

1.  **Job Consumption:** A free Celery worker consumes the job message from the queue.
2.  **Initialization:**
    *   The worker updates the job status in Redis to `"running"`.
    *   It starts a master timer to enforce the `timeout_seconds` limit.
    *   It launches a background thread responsible for the **10-second status update loop**. This thread will continuously update the `progress` and `time_remaining` fields in Redis for its assigned `job_id`.

3.  **Phase 1: Quick Dictionary Attack**
    *   **Goal:** Find low-hanging fruit using common password lists.
    *   **Action:** The worker runs `hashcat` against the hash using a curated list of the most common passwords (e.g., top 1 million from `rockyou.txt`).
    *   **Check:** If the hash is cracked, the process jumps to **Step 5 (Success)**.

4.  **Phase 2: Rule-Based Attack**
    *   **Goal:** Apply common mutations to dictionary words.
    *   **Action:** The worker uses `John the Ripper` or `hashcat` with a powerful ruleset (e.g., `best64.rule`) against a larger wordlist (e.g., the full `rockyou.txt`). This checks for variations like "Password" -> "P@ssword1".
    *   **Check:** If cracked, jump to **Step 5 (Success)**.

5.  **Phase 3: AI-Generated Candidates (PassGAN)**
    *   **Goal:** Generate novel, human-like passwords that are not in standard wordlists.
    *   **Action:**
        1.  The worker invokes the PassGAN model to generate a large batch of password candidates (e.g., 5 million).
        2.  These candidates are **piped directly** to `hashcat`'s stdin to avoid writing a massive temporary file to disk.
        `python passgan_generator.py | hashcat --stdin ...`
    *   **Check:** If cracked, jump to **Step 5 (Success)**.

6.  **Phase 4: Limited Brute-Force (Mask Attack)**
    *   **Goal:** Attempt to crack simple, pattern-based passwords if time remains.
    *   **Action:** The worker runs `hashcat` with a series of common masks (e.g., 8-character lowercase, `?l?l?l?l?l?l?l?l`; Capital letter + 7 lowercase, `?u?l?l?l?l?l?l?l`). This phase only runs for the time remaining before the master timeout.
    *   **Check:** If cracked, jump to **Step 5 (Success)**.

## 3. Status Polling (Client Side)

1.  **Client Polling:** After submitting the job, the client application begins polling the `GET /status/{job_id}` endpoint every few seconds.
2.  **API Response:** The API Gateway reads the job's current state from Redis and returns it to the client. The client can use this to display a real-time progress bar and estimated time remaining.

## 4. Job Completion

The job can end in one of three states. In all cases, the background status-update thread is terminated.

1.  **Success:**
    *   The cracking tool finds the password.
    *   The worker updates the final state in Redis:
        `job:uuid-12345 = { "status": "success", "result": "cracked_password_123", ... }`
    *   The worker process becomes free to pick up a new job.

2.  **Failure (Timeout):**
    *   The master timer expires.
    *   The worker forcefully terminates the currently running `hashcat` or `john` subprocess.
    *   The worker updates the final state in Redis:
        `job:uuid-12345 = { "status": "failed", "reason": "Execution timed out", ... }`

3.  **Failure (Not Found):**
    *   All four cracking phases complete without finding the password.
    *   The worker updates the final state in Redis:
        `job:uuid-12345 = { "status": "failed", "reason": "Password not found in any phase", ... }`

The client, upon its next poll to the status endpoint, will receive the final "success" or "failed" status and can act accordingly.