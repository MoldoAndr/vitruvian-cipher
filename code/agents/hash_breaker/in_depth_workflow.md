### `Internal_Architecture.md`

# Single-Container Internal Architecture

This architecture describes a monolithic service where all components run within a single Docker container. It is designed for simplicity of deployment, using a process manager to run the necessary services and Python's asynchronous capabilities to handle long-running tasks without blocking the API.

## 1. Core Software Components

The container will run three primary software components, managed by a single process supervisor.



1.  **Process Supervisor (`supervisord`)**
    *   **Purpose:** This is the container's entry point (the main `CMD`). Its job is to start, monitor, and manage all the other processes required by the service. If a process fails, `supervisord` can automatically restart it.
    *   **Processes Managed:**
        *   Redis Server
        *   FastAPI Web Server

2.  **State & Job Store (`redis-server`)**
    *   **Purpose:** Even within a single container, using Redis is superior to a simple in-memory Python dictionary. It provides a structured, persistent (if configured), and robust way to manage the state of each job. It cleanly separates the state data from the application logic.
    *   **Function:** It will run as a background service managed by `supervisord`. The FastAPI application will connect to it on `localhost`.

3.  **API & Task Orchestrator (Python/FastAPI)**
    *   **Purpose:** This is the core application logic. It serves two functions:
        1.  **API Server:** Exposes the `POST /audit-hash` and `GET /status/{job_id}` endpoints to the outside world. It is run by an ASGI server like `Uvicorn`, which is also started by `supervisord`.
        2.  **Task Orchestrator:** It is responsible for executing the multi-phase cracking workflow. It does this using FastAPI's built-in `BackgroundTasks` feature. This allows the API to accept a request, schedule the heavy computation to run in the background, and immediately return a response to the user.

## 2. On-Disk Components

*   **Cracking Tools:** `hashcat`, `john`, and the Python scripts for `PassGAN` are all installed directly into the container's filesystem at build time.
*   **Models & Wordlists:** The PassGAN model and all wordlists (`rockyou.txt`, etc.) are included in the Docker image or, preferably, mounted as a Docker Volume at `/data` to keep the image size manageable and allow for easy updates.

This monolithic design is self-contained. A request comes in, is processed in the background, and the state is updated all within the same operational environment.

***

### `Exact_Workflow.md`

# Exact Step-by-Step Job Workflow

This document provides a precise, unambiguous, step-by-step trace of a single hash auditing job from the moment the request is received to its final completion.

**Scenario:** A user sends a request to audit a hash with a 60-second timeout.

---

### **Phase A: Job Submission & Initiation**

**Step 1: Request Reception**
*   A `POST` request hits the container's exposed port and is routed to the FastAPI application's `/audit-hash` endpoint.
*   **Request Body:** `{ "hash": "a1b2c3d4...", "hash_type_id": 0, "timeout_seconds": 60 }`

**Step 2: Immediate API Handling (Duration: <50ms)**
*   The FastAPI endpoint function begins execution.
*   **Action 2.1: Generate Job ID.** A unique ID is created: `job_id = "f4a5c6b7"`.
*   **Action 2.2: Create Initial State.** The application connects to the local Redis server and creates a new record:
    *   **Key:** `job:f4a5c6b7`
    *   **Value (JSON):** `{ "status": "pending", "progress": "0%", "phase": "Queued", "time_remaining": 60, "submitted_at": "timestamp", "result": null }`
*   **Action 2.3: Schedule Background Task.** The endpoint function uses FastAPI's `BackgroundTasks` to schedule the main cracking function to run *after* the response has been sent.
    *   `background_tasks.add_task(run_cracking_pipeline, job_id="f4a5c6b7", hash="...", timeout=60)`
*   **Action 2.4: Respond to Client.** The API immediately sends a `202 Accepted` response back to the user.
    *   **Response Body:** `{ "job_id": "f4a5c6b7" }`
*   The API's part in the initial request is now **complete**.

---

### **Phase B: Background Execution (`run_cracking_pipeline` function)**

The FastAPI framework now begins executing the `run_cracking_pipeline` function in the background.

**Step 3: Job Initialization**
*   **Action 3.1: Record Start Time.** The function notes the current time: `start_time = time.time()`.
*   **Action 3.2: Update State.** It immediately updates the Redis record to show the job is running.
    *   **Key:** `job:f4a5c6b7`
    *   **Value Update:** `{ "status": "running", "phase": "Phase 1: Quick Dictionary Attack" }`

**Step 4: Execute Cracking Phase 1 - Quick Dictionary Attack**
*   **Action 4.1: Prepare Command.** The function constructs the exact shell command to execute.
    *   `command = "hashcat -m 0 hash_file.txt /data/wordlists/top100k.txt --potfile-disable"`
*   **Action 4.2: Execute Subprocess.** It executes the command using Python's `subprocess.run()`, which **blocks** until `hashcat` finishes this specific task. A timeout is calculated for this phase to ensure it doesn't consume the entire job's time limit.
*   **Action 4.3: Check Result.**
    *   **If Cracked:** The function parses Hashcat's output file, finds the cracked password, updates Redis to `{ "status": "success", "result": "cracked_password" }`, and the entire `run_cracking_pipeline` function **terminates successfully**.
    *   **If Not Cracked:** The function proceeds to the next step.

**Step 5: Execute Cracking Phase 2 - Rule-Based Attack**
*   **Action 5.1: Check Master Timeout.** The function checks if `time.time() - start_time > 60`. If true, it updates Redis to `{ "status": "failed", "reason": "Timeout" }` and terminates.
*   **Action 5.2: Update State.** It updates Redis: `{ "progress": "25%", "phase": "Phase 2: Rule-Based Attack", "time_remaining": ... }`.
*   **Action 5.3: Prepare & Execute Command.** It runs `hashcat` again, but this time with a larger wordlist and a ruleset.
    *   `command = "hashcat -m 0 hash_file.txt /data/wordlists/rockyou.txt -r /data/rules/best64.rule"`
*   **Action 5.4: Check Result.** Same as 4.3. If cracked, update Redis and terminate. If not, continue.

**Step 6: Execute Cracking Phase 3 - AI (PassGAN) Generation**
*   **Action 6.1: Check Master Timeout.**
*   **Action 6.2: Update State.** Update Redis: `{ "progress": "50%", "phase": "Phase 3: AI Candidate Generation" }`.
*   **Action 6.3: Prepare & Execute Piped Command.** This is a special execution that pipes the output of the PassGAN script directly into `hashcat`'s standard input to avoid creating a massive temporary file.
    *   `command = "python /app/passgan_generate.py --num 5000000 | hashcat -m 0 hash_file.txt --stdin"`
*   **Action 6.4: Check Result.** Same as 4.3. If cracked, update Redis and terminate. If not, continue.

**Step 7: Execute Cracking Phase 4 - Limited Brute-Force**
*   **Action 7.1: Check Master Timeout.**
*   **Action 7.2: Update State.** Update Redis: `{ "progress": "75%", "phase": "Phase 4: Limited Brute-Force" }`.
*   **Action 7.3: Prepare & Execute Command.** It runs `hashcat` with a common mask attack. The `subprocess` timeout for this command is set to whatever time is remaining from the original 60-second limit.
    *   `command = "hashcat -m 0 hash_file.txt -a 3 ?a?a?a?a?a?a?a"`
*   **Action 7.4: Check Result.** Same as 4.3. If cracked, update Redis and terminate.

---

### **Phase C: Job Finalization**

**Step 8: Conclude the Job**
*   If the function has completed all phases and the hash was not cracked:
*   **Action 8.1: Update Final State.** It updates the Redis record one last time:
    *   **Key:** `job:f4a5c6b7`
    *   **Value Update:** `{ "status": "failed", "progress": "100%", "reason": "Password not found after all phases." }`
*   The background function `run_cracking_pipeline` finishes its execution.

---

### **Parallel Activity: Status Polling**

*   While **Phase B** is executing, the client can periodically send `GET` requests to `/status/f4a5c6b7`.
*   Each time a request comes in, the API endpoint simply reads the current value of the `job:f4a5c6b7` key from Redis and returns it. This provides the client with a real-time (updated between phases) view of the job's progress.
