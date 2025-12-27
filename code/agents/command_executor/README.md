# Command Executor Agent

**SOTA Cryptographic Command Executor with OpenSSL Backend**

A high-performance, secure cryptographic operations service built in Rust that wraps OpenSSL CLI commands. Provides encoding, hashing, symmetric encryption (AES-CBC + HMAC), and asymmetric operations (RSA) through a clean REST API.

## Features

- 🔐 **Secure by Design**: No shell execution, strict input validation, secret redaction
- ⚡ **High Performance**: Rust + Axum async runtime, minimal overhead
- 📚 **Educational**: Shows exact OpenSSL commands executed
- 🐳 **Containerized**: Multi-stage Docker build, runs as non-root
- 🔒 **Encrypt-then-MAC**: AES-CBC + HMAC-SHA256 for authenticated encryption
- 🛡️ **OAEP Padding**: RSA encryption uses OAEP-SHA256 (not PKCS#1 v1.5)
- 🧪 **PQC Signatures**: ML-DSA/Falcon via oqsprovider (Post-Quantum)

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check with OpenSSL version |
| `/pqc/health` | GET | PQC provider health (oqsprovider) |
| `/operations` | GET | List all supported operations |
| `/ciphers` | GET | List available ciphers/algorithms |
| `/execute` | POST | Execute a cryptographic operation |

## Supported Operations (v1)

### Encoding
| Operation | Description | OpenSSL Command |
|-----------|-------------|-----------------|
| `base64_encode` | Encode to Base64 | `openssl base64 -e -A` |
| `base64_decode` | Decode from Base64 | `openssl base64 -d -A` |
| `hex_encode` | Encode to hexadecimal | `xxd -p` |
| `hex_decode` | Decode from hexadecimal | `xxd -r -p` |

### Random Generation
| Operation | Description | OpenSSL Command |
|-----------|-------------|-----------------|
| `random_bytes` | Generate random bytes (Base64) | `openssl rand -base64 N` |
| `random_hex` | Generate random hex string | `openssl rand -hex N` |
| `random_base64` | Generate random Base64 | `openssl rand -base64 N` |

### Hashing
| Operation | Description | OpenSSL Command |
|-----------|-------------|-----------------|
| `hash` | Compute hash digest | `openssl dgst -<algo>` |
| `hmac` | Compute HMAC | `openssl dgst -<algo> -hmac <key>` |

### Symmetric Encryption (AES-CBC + HMAC)
| Operation | Description | OpenSSL Command |
|-----------|-------------|-----------------|
| `aes_keygen` | Generate AES key + IV + HMAC key | `openssl rand -hex 32` |
| `aes_encrypt` | AES-CBC encrypt + HMAC | `openssl enc -aes-256-cbc -e` + `openssl dgst -sha256 -mac hmac` |
| `aes_decrypt` | Verify HMAC then AES-CBC decrypt | `openssl dgst` verify + `openssl enc -aes-256-cbc -d` |

### Asymmetric (RSA)
| Operation | Description | OpenSSL Command |
|-----------|-------------|-----------------|
| `rsa_keygen` | Generate RSA key pair | `openssl genpkey -algorithm RSA` |
| `rsa_pubkey` | Extract public key | `openssl pkey -pubout` |
| `rsa_sign` | Sign with private key | `openssl dgst -sha256 -sign` |
| `rsa_verify` | Verify signature | `openssl dgst -sha256 -verify` |
| `rsa_encrypt` | Encrypt with public key (OAEP) | `openssl pkeyutl -encrypt -pkeyopt rsa_padding_mode:oaep` |
| `rsa_decrypt` | Decrypt with private key (OAEP) | `openssl pkeyutl -decrypt -pkeyopt rsa_padding_mode:oaep` |

### Post-Quantum Signatures (oqsprovider)
| Operation | Description | OpenSSL Command |
|-----------|-------------|-----------------|
| `pqc_sig_keygen` | Generate PQC signature keypair | `openssl genpkey -provider oqsprovider -algorithm mldsa44` |
| `pqc_sig_sign` | Sign data with PQC private key | `openssl pkeyutl -provider oqsprovider -sign -inkey pqc_priv.pem` |
| `pqc_sig_verify` | Verify PQC signature | `openssl pkeyutl -provider oqsprovider -verify -pubin -inkey pqc_pub.pem` |

## Quick Start

### Docker (Recommended)

```bash
# Build and run
docker compose up --build -d

# Check health
curl http://localhost:8085/health
```

### Local Development

```bash
# Prerequisites: Rust 1.75+, OpenSSL 3.x

# Build
cargo build --release

# Run
cargo run --release

# Test
cargo test
```

### PQC Support Notes
- PQC operations require **liboqs + oqsprovider** installed in the container/runtime.
- The Dockerfile builds and installs oqsprovider automatically.
- To run PQC unit tests locally:
  ```bash
  ENABLE_PQC_TESTS=1 cargo test
  ```

## Usage Examples

### Base64 Encode

```bash
curl -X POST http://localhost:8085/execute \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "base64_encode",
    "params": {"data": "Hello, World!"}
  }'
```

Response:
```json
{
  "success": true,
  "operation": "base64_encode",
  "result": {
    "output": "SGVsbG8sIFdvcmxkIQ=="
  },
  "command": {
    "executed": "openssl base64 -e -A",
    "redacted": false,
    "openssl_version": "OpenSSL 3.0.11",
    "explanation": "Base64 encoding converts binary data to ASCII text representation"
  },
  "metadata": {
    "execution_time_ms": 2.1,
    "request_id": "req_abc123",
    "timestamp": "2025-12-27T10:30:00Z"
  }
}
```

### AES Encryption (Full Flow)

```bash
# 1. Generate keys
curl -X POST http://localhost:8085/execute \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "aes_keygen",
    "params": {"bits": 256}
  }'

# Response contains: key_hex, iv_hex, hmac_key_hex

# 2. Encrypt
curl -X POST http://localhost:8085/execute \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "aes_encrypt",
    "params": {
      "plaintext": "Secret message",
      "key": "<key_hex from step 1>",
      "iv": "<iv_hex from step 1>",
      "hmac_key": "<hmac_key_hex from step 1>"
    }
  }'

# Response contains: ciphertext_base64, iv_hex, hmac_hex

# 3. Decrypt
curl -X POST http://localhost:8085/execute \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "aes_decrypt",
    "params": {
      "ciphertext": "<ciphertext_base64>",
      "key": "<key_hex>",
      "iv": "<iv_hex>",
      "hmac_key": "<hmac_key_hex>",
      "hmac": "<hmac_hex from encrypt>"
    }
  }'
```

### RSA Sign & Verify

```bash
# 1. Generate RSA key pair
curl -X POST http://localhost:8085/execute \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "rsa_keygen",
    "params": {"bits": 2048}
  }'

# 2. Sign data
curl -X POST http://localhost:8085/execute \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "rsa_sign",
    "params": {
      "data": "Document to sign",
      "private_key": "<private_key_pem>"
    }
  }'

# 3. Verify signature
curl -X POST http://localhost:8085/execute \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "rsa_verify",
    "params": {
      "data": "Document to sign",
      "signature": "<signature_base64>",
      "public_key": "<public_key_pem>"
    }
  }'
```

## Security Model

### Input Validation
- **Hex strings**: Must be even length, only `[0-9a-fA-F]`
- **Base64**: Validated before decoding
- **Keys**: Exact length validation for cipher
- **RSA bits**: Only 2048, 3072, 4096 allowed
- **Size limits**: Max 1MB input, 2MB output

### No Shell Injection
Commands are **never** executed via shell:
```rust
// ❌ DANGEROUS - Never done
subprocess.run(f"openssl enc {user_input}", shell=True)

// ✅ SAFE - How we do it
Command::new("openssl")
    .args(["enc", "-aes-256-cbc", ...])
    .spawn()
```

### Secret Redaction
By default, secrets are redacted in command output:
```json
{
  "executed": "openssl enc -aes-256-cbc -K 0123...cdef -iv ..."
}
```

### Encrypt-then-MAC
AES encryption uses **Encrypt-then-MAC** pattern:
1. Encrypt plaintext with AES-CBC
2. Compute HMAC-SHA256 over ciphertext
3. On decrypt: verify HMAC **first**, then decrypt

This prevents padding oracle attacks.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `RUST_LOG` | `info` | Log level |
| `SERVER_HOST` | `0.0.0.0` | Bind address |
| `SERVER_PORT` | `8085` | Listen port |

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                 Command Executor                    │
├─────────────────────────────────────────────────────┤
│  Axum HTTP Server                                   │
│  ├── GET  /health                                   │
│  ├── GET  /operations                               │
│  ├── GET  /ciphers                                  │
│  └── POST /execute                                  │
├─────────────────────────────────────────────────────┤
│  Providers                                          │
│  ├── encoding.rs    (base64, hex)                   │
│  ├── random.rs      (secure random)                 │
│  ├── hashing.rs     (SHA, HMAC)                     │
│  ├── symmetric.rs   (AES-CBC + HMAC)                │
│  └── asymmetric.rs  (RSA)                           │
├─────────────────────────────────────────────────────┤
│  OpenSSL Executor (Sandboxed)                       │
│  ├── Parameterized command building                 │
│  ├── Isolated temp directory per request            │
│  ├── Timeout enforcement                            │
│  └── Secret redaction                               │
├─────────────────────────────────────────────────────┤
│  Validators                                         │
│  ├── Hex/Base64 validation                          │
│  ├── Key length validation                          │
│  ├── Algorithm allowlists                           │
│  └── Injection detection                            │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
              ┌─────────────────┐
              │  OpenSSL 3.x    │
              │  xxd            │
              └─────────────────┘
```

## Roadmap (v2)

- [ ] AES-GCM (when OpenSSL CLI supports tag output)
- [ ] EC key generation and ECDSA
- [ ] X.509 certificate operations
- [ ] PBKDF2 key derivation
- [ ] Ed25519 signatures
- [ ] PQC KEMs (Kyber) via oqsprovider once OpenSSL KEM CLI is available

## License

MIT License - Part of Vitruvian Cipher Bachelor's Thesis
