FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends libgl1 && \
    rm -rf /var/lib/apt/lists/*

COPY service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY service/app.py .
COPY models ./models

ENV MODEL_PATH=/app/models/2023-05-31_21-52-43_model

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
