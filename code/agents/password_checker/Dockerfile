FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install the combined dependency set once to keep layers small
RUN pip install --no-cache-dir \
    fastapi==0.110.0 \
    uvicorn[standard]==0.29.0 \
    httpx==0.27.0 \
    transformers==4.39.3 \
    torch==2.2.2 \
    zxcvbn==4.4.28

# Pin NumPy to 1.x for torch compatibility.
RUN pip install --no-cache-dir numpy==1.26.4

# Copy application sources
COPY aggregator ./aggregator
COPY zxcvbn ./zxcvbn
COPY haveibeenpwned ./haveibeenpwned
COPY PassGPT ./PassGPT
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Default ports and internal URLs so everything talks over localhost inside the container
ENV PASS_GPT_PORT=8001 \
    ZXCVBN_PORT=8002 \
    HAVEIBEENPWNED_PORT=8003 \
    AGGREGATOR_PORT=8000 \
    PASS_GPT_URL=http://127.0.0.1:8001/score \
    ZXCVBN_URL=http://127.0.0.1:8002/score \
    HAVEIBEENPWNED_URL=http://127.0.0.1:8003/score \
    ENABLED_COMPONENTS=pass_gpt,zxcvbn,haveibeenpwned

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
