# Prime Checker Service

Fast prime checking service with multiple backends:
- Local fast-path for small/64-bit numbers (deterministic Miller-Rabin).
- YAFU for primality and factorization when available.
- FactorDB fallback for large or unknown cases.
- In-memory LRU cache plus persistent BoltDB store for repeat lookups.

## Run (Docker)
Build and start:

```bash
docker build -t prime_checker:local .
docker run --rm -p 5000:5000 --name prime_checker prime_checker:local
```

## Request format
POST JSON payload with a `number` string:

```json
{"number":"123456789"}
```

## Endpoints

### `POST /isprime`
Checks primality, returns factors if composite and available.

```bash
curl -s -X POST -H 'Content-Type: application/json' \
  -d '{"number":"100"}' http://localhost:5000/isprime
```

Example response:
```json
{"number":"100","is_prime":false,"factors":["2","2","5","5"],"source":"local"}
```

### `GET /health`
Reports service health and backend availability.

```bash
curl -s http://localhost:5000/health
```

Example response:
```json
{"factordb_accessible":true,"status":"healthy","timestamp":1710000000,"yafu_available":true}
```

### `GET /stats`
Cache and storage stats.

```bash
curl -s http://localhost:5000/stats
```

Example response:
```json
{"cache_entries":12,"db_entries":120,"uptime_sec":3600}
```

### `GET /history`
Most recent stored results (default limit 50, max 500).

```bash
curl -s http://localhost:5000/history
curl -s http://localhost:5000/history?limit=10
```

Example response:
```json
{
  "items": [
    {
      "number": "100",
      "is_prime": false,
      "factors": ["2","2","5","5"],
      "source": "local",
      "updated_at": 1710000000,
      "hit_count": 3
    }
  ]
}
```

## Configuration (env vars)
- `PORT` (default `5000`)
- `DB_PATH` (default `/app/data/prime_cache.db`)
- `CACHE_SIZE` (default `10000`)
- `MAX_DIGITS` (default `1000`)
- `MAX_BODY_BYTES` (default `1048576`)
- `YAFU_PATH` (default `/usr/local/bin/yafu`)
- `YAFU_WORKDIR` (default `/opt/math/yafu`)
- `YAFU_PRIME_TIMEOUT_MS` (default `5000`)
- `YAFU_FACTOR_TIMEOUT_MS` (default `8000`)
- `YAFU_CONCURRENCY` (default `2`)
- `YAFU_FACTOR_MAX_DIGITS` (default `60`)
- `FACTORDB_TIMEOUT_MS` (default `10000`)
- `FACTORDB_RETRIES` (default `2`)
- `FACTORDB_BACKOFF_MS` (default `500`)
- `SMALL_FACTOR_LIMIT` (default `1000000000000`)
- `HEALTH_CACHE_TTL_MS` (default `30000`)
- `ENABLE_FACTORDB` (default `true`)

## Notes
- If YAFU is missing or times out, the service falls back to FactorDB (if enabled).
- Composite results can be returned even if factors are unavailable; check the `note` field.
