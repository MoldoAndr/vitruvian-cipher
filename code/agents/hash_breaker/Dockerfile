# Lightweight CPU-Only Dockerfile for Hash Breaker Microservice
# Base: ~100MB (vs 4GB for NVIDIA CUDA)
# Final Image: ~500MB (vs 9.5GB)

FROM python:3.10-slim

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install minimal system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Hash cracking tools
    hashcat \
    john \
    # Download tools
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies (CPU-only PyTorch)
RUN pip3 install --no-cache-dir --upgrade pip && \
    # CPU-only torch (much smaller)
    pip3 install --no-cache-dir torch==2.0.0+cpu -f https://download.pytorch.org/whl/torch_stable.html && \
    # Install other dependencies
    pip3 install --no-cache-dir -r requirements.txt

###############################################################################
# Prepare directories (downloads happen at runtime, not build)
###############################################################################

# Create directories
RUN mkdir -p /app/models /app/wordlists /app/rules /app/data /app/logs

###############################################################################
# Copy Application Code
###############################################################################

COPY app/ ./app/
COPY rockyou.txt.gz /tmp/rockyou.txt.gz

# Extract RockYou wordlist at runtime (not build time)
RUN echo "Extracting RockYou wordlist..." && \
    gunzip -c /tmp/rockyou.txt.gz > /app/wordlists/rockyou.txt && \
    echo "Creating top100k wordlist..." && \
    head -n 100000 /app/wordlists/rockyou.txt > /app/wordlists/top100k.txt && \
    echo "✅ Wordlists ready" && \
    rm /tmp/rockyou.txt.gz

# Create non-root user
RUN useradd -m -u 1000 hashbreaker && \
    chown -R hashbreaker:hashbreaker /app

# Switch to non-root user
USER hashbreaker

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/v1/health || exit 1

# Expose port
EXPOSE 8000

# Default command
CMD ["python3", "-m", "app.main"]
