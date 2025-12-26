#!/bin/sh
set -eu

PASS_GPT_PORT=${PASS_GPT_PORT:-8001}
ZXCVBN_PORT=${ZXCVBN_PORT:-8002}
HAVEIBEENPWNED_PORT=${HAVEIBEENPWNED_PORT:-8003}
AGGREGATOR_PORT=${AGGREGATOR_PORT:-8000}

# Keep aggregator defaults in sync with the internal component ports
export PASS_GPT_URL="${PASS_GPT_URL:-http://127.0.0.1:${PASS_GPT_PORT}/score}"
export ZXCVBN_URL="${ZXCVBN_URL:-http://127.0.0.1:${ZXCVBN_PORT}/score}"
export HAVEIBEENPWNED_URL="${HAVEIBEENPWNED_URL:-http://127.0.0.1:${HAVEIBEENPWNED_PORT}/score}"
export ENABLED_COMPONENTS="${ENABLED_COMPONENTS:-pass_gpt,zxcvbn,haveibeenpwned}"

echo "Starting PassGPT on port ${PASS_GPT_PORT}"
uvicorn app:app \
  --app-dir /app/PassGPT/service \
  --host 0.0.0.0 \
  --port "${PASS_GPT_PORT}" &
PASS_GPT_PID=$!

echo "Starting zxcvbn on port ${ZXCVBN_PORT}"
uvicorn app:app \
  --app-dir /app/zxcvbn \
  --host 0.0.0.0 \
  --port "${ZXCVBN_PORT}" &
ZXCVBN_PID=$!

echo "Starting HaveIBeenPwned on port ${HAVEIBEENPWNED_PORT}"
uvicorn app:app \
  --app-dir /app/haveibeenpwned \
  --host 0.0.0.0 \
  --port "${HAVEIBEENPWNED_PORT}" &
HIBP_PID=$!

echo "Starting aggregator on port ${AGGREGATOR_PORT}"
uvicorn app:app \
  --app-dir /app/aggregator \
  --host 0.0.0.0 \
  --port "${AGGREGATOR_PORT}" &
AGGREGATOR_PID=$!

trap 'kill ${PASS_GPT_PID} ${ZXCVBN_PID} ${HIBP_PID} ${AGGREGATOR_PID} 2>/dev/null || true' INT TERM

# Keep the container alive as long as the aggregator stays up
wait "${AGGREGATOR_PID}"
EXIT_CODE=$?

kill "${PASS_GPT_PID}" "${ZXCVBN_PID}" "${HIBP_PID}" 2>/dev/null || true
wait "${PASS_GPT_PID}" "${ZXCVBN_PID}" "${HIBP_PID}" 2>/dev/null || true

exit "${EXIT_CODE}"
