FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# TensorFlow requires libgl1; keep base image slim otherwise
RUN apt-get update && \
    apt-get install -y --no-install-recommends libgl1 && \
    rm -rf /var/lib/apt/lists/*

# Install the combined dependency set once to keep layers small
RUN pip install --no-cache-dir \
    fastapi==0.110.0 \
    uvicorn[standard]==0.29.0 \
    httpx==0.27.0 \
    tensorflow==2.15.0 \
    numpy==1.26.4 \
    zxcvbn==4.4.28

# Copy application sources
COPY aggregator ./aggregator
COPY zxcvbn ./zxcvbn
COPY haveibeenpwned ./haveibeenpwned
COPY PassStrengthAI ./PassStrengthAI
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Default ports and internal URLs so everything talks over localhost inside the container
ENV PASS_STRENGTH_AI_PORT=8001 \
    ZXCVBN_PORT=8002 \
    HAVEIBEENPWNED_PORT=8003 \
    AGGREGATOR_PORT=8000 \
    PASS_STRENGTH_AI_URL=http://127.0.0.1:8001/score \
    ZXCVBN_URL=http://127.0.0.1:8002/score \
    HAVEIBEENPWNED_URL=http://127.0.0.1:8003/score \
    ENABLED_COMPONENTS=pass_strength_ai,zxcvbn,haveibeenpwned

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
