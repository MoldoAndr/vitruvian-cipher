# SecureBERT Inference Service Dockerfile - Lightweight CPU-only version
FROM python:3.11-slim

WORKDIR /app

# Install minimal system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy minimal requirements for inference only
COPY requirements-minimal.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-minimal.txt && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copy the application source code
COPY scripts/ ./scripts/
COPY src/ ./src/

# Copy the trained model artifacts
# These should be present after training or provided via volume mount
COPY artifacts/ ./artifacts/

# Set Python path to include current directory and scripts
ENV PYTHONPATH=/app:/app/scripts

# Expose the API port (default 8080 from .env)
EXPOSE 8080

# Health check - lightweight
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# Run the server
CMD ["python", "scripts/server.py"]
