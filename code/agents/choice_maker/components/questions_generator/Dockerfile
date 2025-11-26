FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY config ./config
COPY prompts ./prompts
COPY src ./src
COPY README.md ./README.md
COPY data ./data

ENV PYTHONPATH=/app/src

ENTRYPOINT ["python", "-m", "questions_generator.cli"]
