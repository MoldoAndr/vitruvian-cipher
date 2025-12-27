//! API routes for Command Executor
//! RESTful endpoints for cryptographic operations

use axum::{
    extract::State,
    http::StatusCode,
    response::IntoResponse,
    routing::{get, post},
    Json, Router,
};
use std::collections::HashMap;
use std::sync::Arc;
use std::time::Instant;

use crate::config::*;
use crate::models::*;
use crate::openssl::{
    ExecutionContext, OpenSSLError, list_openssl_kem_algorithms, list_openssl_providers,
    list_openssl_signature_algorithms,
};
use crate::providers::{encoding, random, hashing, symmetric, asymmetric, pqc};

/// Application state
pub struct AppState {
    pub start_time: Instant,
    pub openssl_version: String,
}

/// Create the router with all routes
pub fn create_router(state: Arc<AppState>) -> Router {
    Router::new()
        .route("/health", get(health_handler))
        .route("/pqc/health", get(pqc_health_handler))
        .route("/operations", get(operations_handler))
        .route("/ciphers", get(ciphers_handler))
        .route("/execute", post(execute_handler))
        .with_state(state)
}

/// Health check endpoint
async fn health_handler(State(state): State<Arc<AppState>>) -> impl IntoResponse {
    let uptime = state.start_time.elapsed().as_secs();
    
    Json(HealthResponse {
        status: "healthy".to_string(),
        service: "command-executor".to_string(),
        version: env!("CARGO_PKG_VERSION").to_string(),
        openssl_version: state.openssl_version.clone(),
        uptime_seconds: uptime,
    })
}

/// PQC health check endpoint
async fn pqc_health_handler(State(state): State<Arc<AppState>>) -> impl IntoResponse {
    let ctx = match ExecutionContext::new(EXECUTION_TIMEOUT_MS) {
        Ok(ctx) => ctx,
        Err(err) => {
            return Json(PqcHealthResponse {
                status: "unavailable".to_string(),
                provider_loaded: false,
                providers: Vec::new(),
                pqc_signatures: Vec::new(),
                pqc_kems: Vec::new(),
                message: format!("Failed to create execution context: {}", err),
                openssl_version: state.openssl_version.clone(),
            });
        }
    };

    let providers = match list_openssl_providers(&ctx).await {
        Ok(list) => list,
        Err(err) => {
            return Json(PqcHealthResponse {
                status: "unavailable".to_string(),
                provider_loaded: false,
                providers: Vec::new(),
                pqc_signatures: Vec::new(),
                pqc_kems: Vec::new(),
                message: err.to_string(),
                openssl_version: state.openssl_version.clone(),
            });
        }
    };

    let provider_loaded = providers.iter().any(|p| p == "oqsprovider");

    let signature_algos = if provider_loaded {
        list_openssl_signature_algorithms(&ctx)
            .await
            .unwrap_or_default()
    } else {
        Vec::new()
    };

    let pqc_signatures: Vec<String> = signature_algos
        .into_iter()
        .filter(|alg| ALLOWED_PQC_SIG_ALGOS.contains(alg.as_str()))
        .collect();

    let kem_algos = if provider_loaded {
        list_openssl_kem_algorithms(&ctx)
            .await
            .unwrap_or_default()
    } else {
        Vec::new()
    };

    let pqc_kems: Vec<String> = kem_algos
        .into_iter()
        .filter(|alg| ALLOWED_PQC_KEM_ALGOS.contains(alg.as_str()))
        .collect();

    Json(PqcHealthResponse {
        status: if provider_loaded { "available" } else { "unavailable" }.to_string(),
        provider_loaded,
        providers,
        pqc_signatures,
        pqc_kems,
        message: if provider_loaded {
            "oqsprovider loaded successfully".to_string()
        } else {
            "oqsprovider not loaded".to_string()
        },
        openssl_version: state.openssl_version.clone(),
    })
}

/// List all supported operations
async fn operations_handler() -> impl IntoResponse {
    let operations: Vec<OperationDetail> = SUPPORTED_OPERATIONS.iter().map(|op| {
        let parameters = op.params.iter().map(|p| {
            ParameterDetail {
                name: p.to_string(),
                r#type: get_param_type(p),
                required: is_param_required(op.name, p),
                description: get_param_description(p),
            }
        }).collect();
        
        OperationDetail {
            name: op.name.to_string(),
            category: op.category.to_string(),
            description: op.description.to_string(),
            parameters,
            example_command: get_example_command(op.name),
        }
    }).collect();
    
    let total = operations.len();
    
    Json(OperationsResponse { operations, total })
}

/// List available ciphers and algorithms
async fn ciphers_handler() -> impl IntoResponse {
    let symmetric: Vec<CipherInfo> = ALLOWED_SYMMETRIC_CIPHERS.iter().map(|c| {
        let key_bits = get_cipher_key_length(c).unwrap_or(0) * 8;
        let iv_bits = get_cipher_iv_length(c).unwrap_or(0) * 8;
        let mode = if c.contains("cbc") { "CBC" }
                   else if c.contains("gcm") { "GCM" }
                   else if c.contains("ctr") { "CTR" }
                   else { "Stream" };
        
        let warning = if c.contains("des") {
            Some("Legacy cipher - not recommended for new applications".to_string())
        } else {
            None
        };
        
        CipherInfo {
            name: c.to_string(),
            key_bits,
            iv_bits,
            mode: mode.to_string(),
            warning,
        }
    }).collect();
    
    let hash_algorithms: Vec<String> = ALLOWED_HASH_ALGOS.iter().map(|s| s.to_string()).collect();
    let rsa_key_sizes: Vec<u32> = ALLOWED_RSA_BITS.iter().copied().collect();
    let ec_curves: Vec<String> = ALLOWED_EC_CURVES.iter().map(|s| s.to_string()).collect();
    let pqc_signatures: Vec<String> = ALLOWED_PQC_SIG_ALGOS.iter().map(|s| s.to_string()).collect();
    let pqc_kems: Vec<String> = ALLOWED_PQC_KEM_ALGOS.iter().map(|s| s.to_string()).collect();
    
    Json(CiphersResponse {
        symmetric,
        hash_algorithms,
        rsa_key_sizes,
        ec_curves,
        pqc_signatures,
        pqc_kems,
    })
}

/// Execute an operation
async fn execute_handler(
    State(state): State<Arc<AppState>>,
    Json(request): Json<ExecuteRequest>,
) -> Result<Json<ExecuteResponse>, (StatusCode, Json<ErrorResponse>)> {
    let start = Instant::now();
    let request_id = uuid::Uuid::new_v4().to_string();
    
    // Create execution context with appropriate timeout
    let timeout = if request.operation.contains("keygen") {
        RSA_KEYGEN_TIMEOUT_MS
    } else {
        EXECUTION_TIMEOUT_MS
    };
    
    let ctx = ExecutionContext::new(timeout).map_err(|e| {
        make_error_response(ErrorCode::InternalError, e.to_string(), &request_id, start)
    })?;
    
    // Route to appropriate provider
    let result = match request.operation.as_str() {
        // Encoding
        "base64_encode" => execute_base64_encode(&ctx, &request.params).await,
        "base64_decode" => execute_base64_decode(&ctx, &request.params).await,
        "hex_encode" => execute_hex_encode(&ctx, &request.params).await,
        "hex_decode" => execute_hex_decode(&ctx, &request.params).await,
        
        // Random
        "random_bytes" => execute_random_bytes(&ctx, &request.params).await,
        "random_hex" => execute_random_hex(&ctx, &request.params).await,
        "random_base64" => execute_random_base64(&ctx, &request.params).await,
        
        // Hashing
        "hash" => execute_hash(&ctx, &request.params).await,
        "hmac" => execute_hmac(&ctx, &request.params).await,
        
        // Symmetric
        "aes_keygen" => execute_aes_keygen(&ctx, &request.params).await,
        "aes_encrypt" => execute_aes_encrypt(&ctx, &request.params).await,
        "aes_decrypt" => execute_aes_decrypt(&ctx, &request.params).await,
        
        // Asymmetric
        "rsa_keygen" => execute_rsa_keygen(&ctx, &request.params).await,
        "rsa_pubkey" => execute_rsa_pubkey(&ctx, &request.params).await,
        "rsa_sign" => execute_rsa_sign(&ctx, &request.params).await,
        "rsa_verify" => execute_rsa_verify(&ctx, &request.params).await,
        "rsa_encrypt" => execute_rsa_encrypt(&ctx, &request.params).await,
        "rsa_decrypt" => execute_rsa_decrypt(&ctx, &request.params).await,

        // PQC signatures
        "pqc_sig_keygen" => execute_pqc_sig_keygen(&ctx, &request.params).await,
        "pqc_sig_sign" => execute_pqc_sig_sign(&ctx, &request.params).await,
        "pqc_sig_verify" => execute_pqc_sig_verify(&ctx, &request.params).await,
        
        _ => {
            return Err(make_error_response(
                ErrorCode::UnsupportedOperation,
                format!("Unknown operation: {}", request.operation),
                &request_id,
                start,
            ));
        }
    };
    
    match result {
        Ok((result_json, command_display, command_redacted, explanation)) => {
            Ok(Json(ExecuteResponse {
                success: true,
                operation: request.operation,
                result: result_json,
                command: CommandInfo {
                    executed: if SHOW_SECRETS_IN_COMMAND { command_display } else { command_redacted.clone() },
                    redacted: !SHOW_SECRETS_IN_COMMAND,
                    openssl_version: state.openssl_version.clone(),
                    explanation: Some(explanation),
                },
                metadata: ExecutionMetadata {
                    execution_time_ms: start.elapsed().as_secs_f64() * 1000.0,
                    request_id,
                    timestamp: chrono::Utc::now().to_rfc3339(),
                },
            }))
        }
        Err(e) => {
            let (code, message) = match &e {
                OpenSSLError::Timeout(ms) => (ErrorCode::Timeout, format!("Operation timed out after {}ms", ms)),
                OpenSSLError::ExecutionFailed(msg) => {
                    if msg.contains("Invalid") || msg.contains("validation") {
                        (ErrorCode::ValidationFailed, msg.clone())
                    } else {
                        (ErrorCode::OpenSSLError, msg.clone())
                    }
                }
                OpenSSLError::OutputTooLarge(size) => (ErrorCode::SizeLimitExceeded, format!("Output exceeded {} bytes", size)),
                _ => (ErrorCode::InternalError, e.to_string()),
            };
            Err(make_error_response(code, message, &request_id, start))
        }
    }
}

// ============================================================================
// Operation executors
// ============================================================================

type ExecutionOutput = (serde_json::Value, String, String, String);

fn get_param_str<'a>(params: &'a HashMap<String, serde_json::Value>, key: &str) -> Result<&'a str, OpenSSLError> {
    params.get(key)
        .and_then(|v| v.as_str())
        .ok_or_else(|| OpenSSLError::ExecutionFailed(format!("Missing or invalid parameter: {}", key)))
}

fn get_param_str_opt_strict<'a>(
    params: &'a HashMap<String, serde_json::Value>,
    key: &str,
) -> Result<Option<&'a str>, OpenSSLError> {
    match params.get(key) {
        None => Ok(None),
        Some(value) => value
            .as_str()
            .map(Some)
            .ok_or_else(|| OpenSSLError::ExecutionFailed(format!("Invalid parameter type: {}", key))),
    }
}

fn get_param_u64(params: &HashMap<String, serde_json::Value>, key: &str) -> Result<u64, OpenSSLError> {
    params.get(key)
        .and_then(|v| v.as_u64())
        .ok_or_else(|| OpenSSLError::ExecutionFailed(format!("Missing or invalid parameter: {}", key)))
}

fn get_param_u64_opt_strict(
    params: &HashMap<String, serde_json::Value>,
    key: &str,
) -> Result<Option<u64>, OpenSSLError> {
    match params.get(key) {
        None => Ok(None),
        Some(value) => value
            .as_u64()
            .map(Some)
            .ok_or_else(|| OpenSSLError::ExecutionFailed(format!("Invalid parameter type: {}", key))),
    }
}

// Encoding operations
async fn execute_base64_encode(
    ctx: &ExecutionContext,
    params: &HashMap<String, serde_json::Value>,
) -> Result<ExecutionOutput, OpenSSLError> {
    let data = get_param_str(params, "data")?;
    let (result, exec) = encoding::base64_encode(ctx, data).await?;
    Ok((
        serde_json::to_value(result).unwrap(),
        exec.command_display,
        exec.command_redacted,
        "Base64 encoding converts binary data to ASCII text representation".to_string(),
    ))
}

async fn execute_base64_decode(
    ctx: &ExecutionContext,
    params: &HashMap<String, serde_json::Value>,
) -> Result<ExecutionOutput, OpenSSLError> {
    let encoded = get_param_str(params, "encoded")?;
    let (result, exec) = encoding::base64_decode(ctx, encoded).await?;
    Ok((
        serde_json::to_value(result).unwrap(),
        exec.command_display,
        exec.command_redacted,
        "Base64 decoding converts ASCII text back to binary data".to_string(),
    ))
}

async fn execute_hex_encode(
    ctx: &ExecutionContext,
    params: &HashMap<String, serde_json::Value>,
) -> Result<ExecutionOutput, OpenSSLError> {
    let data = get_param_str(params, "data")?;
    let (result, exec) = encoding::hex_encode(ctx, data).await?;
    Ok((
        serde_json::to_value(result).unwrap(),
        exec.command_display,
        exec.command_redacted,
        "Hexadecimal encoding represents each byte as two hex characters".to_string(),
    ))
}

async fn execute_hex_decode(
    ctx: &ExecutionContext,
    params: &HashMap<String, serde_json::Value>,
) -> Result<ExecutionOutput, OpenSSLError> {
    let hex = get_param_str(params, "hex")?;
    let (result, exec) = encoding::hex_decode(ctx, hex).await?;
    Ok((
        serde_json::to_value(result).unwrap(),
        exec.command_display,
        exec.command_redacted,
        "Hexadecimal decoding converts hex string back to binary data".to_string(),
    ))
}

// Random operations
async fn execute_random_bytes(
    ctx: &ExecutionContext,
    params: &HashMap<String, serde_json::Value>,
) -> Result<ExecutionOutput, OpenSSLError> {
    let length = get_param_u64(params, "length")? as usize;
    let (result, exec) = random::random_bytes(ctx, length).await?;
    Ok((
        serde_json::to_value(result).unwrap(),
        exec.command_display,
        exec.command_redacted,
        "Cryptographically secure random bytes from OpenSSL's PRNG".to_string(),
    ))
}

async fn execute_random_hex(
    ctx: &ExecutionContext,
    params: &HashMap<String, serde_json::Value>,
) -> Result<ExecutionOutput, OpenSSLError> {
    let length = get_param_u64(params, "length")? as usize;
    let (result, exec) = random::random_hex(ctx, length).await?;
    Ok((
        serde_json::to_value(result).unwrap(),
        exec.command_display,
        exec.command_redacted,
        "Cryptographically secure random bytes as hexadecimal string".to_string(),
    ))
}

async fn execute_random_base64(
    ctx: &ExecutionContext,
    params: &HashMap<String, serde_json::Value>,
) -> Result<ExecutionOutput, OpenSSLError> {
    let length = get_param_u64(params, "length")? as usize;
    let (result, exec) = random::random_base64(ctx, length).await?;
    Ok((
        serde_json::to_value(result).unwrap(),
        exec.command_display,
        exec.command_redacted,
        "Cryptographically secure random bytes as Base64 string".to_string(),
    ))
}

// Hashing operations
async fn execute_hash(
    ctx: &ExecutionContext,
    params: &HashMap<String, serde_json::Value>,
) -> Result<ExecutionOutput, OpenSSLError> {
    let data = get_param_str(params, "data")?;
    let algorithm = get_param_str_opt_strict(params, "algorithm")?.unwrap_or("sha256");
    let (result, exec) = hashing::hash(ctx, data, algorithm).await?;
    Ok((
        serde_json::to_value(result).unwrap(),
        exec.command_display,
        exec.command_redacted,
        format!("{} produces a fixed-size digest from input data", algorithm.to_uppercase()),
    ))
}

async fn execute_hmac(
    ctx: &ExecutionContext,
    params: &HashMap<String, serde_json::Value>,
) -> Result<ExecutionOutput, OpenSSLError> {
    let data = get_param_str(params, "data")?;
    let key = get_param_str(params, "key")?;
    let algorithm = get_param_str_opt_strict(params, "algorithm")?.unwrap_or("sha256");
    let (result, exec) = hashing::hmac(ctx, data, key, algorithm).await?;
    Ok((
        serde_json::to_value(result).unwrap(),
        exec.command_display,
        exec.command_redacted,
        "HMAC (Hash-based Message Authentication Code) provides data integrity and authenticity".to_string(),
    ))
}

// Symmetric operations
async fn execute_aes_keygen(
    ctx: &ExecutionContext,
    params: &HashMap<String, serde_json::Value>,
) -> Result<ExecutionOutput, OpenSSLError> {
    let bits = get_param_u64_opt_strict(params, "bits")?.map(|b| b as usize);
    let (result, execs) = symmetric::aes_keygen(ctx, bits).await?;
    let cmd = execs.first().map(|e| e.command_display.clone()).unwrap_or_default();
    let cmd_redacted = execs.first().map(|e| e.command_redacted.clone()).unwrap_or_default();
    Ok((
        serde_json::to_value(result).unwrap(),
        cmd,
        cmd_redacted,
        "Generates cryptographically secure random key, IV, and HMAC key".to_string(),
    ))
}

async fn execute_aes_encrypt(
    ctx: &ExecutionContext,
    params: &HashMap<String, serde_json::Value>,
) -> Result<ExecutionOutput, OpenSSLError> {
    let plaintext = get_param_str(params, "plaintext")?;
    let key = get_param_str(params, "key")?;
    let iv = get_param_str_opt_strict(params, "iv")?;
    let hmac_key = get_param_str(params, "hmac_key")?;
    let cipher = get_param_str_opt_strict(params, "cipher")?;
    
    let (result, execs) = symmetric::aes_encrypt(ctx, plaintext, key, iv, hmac_key, cipher).await?;
    let cmd = execs.first().map(|e| e.command_display.clone()).unwrap_or_default();
    let cmd_redacted = execs.first().map(|e| e.command_redacted.clone()).unwrap_or_default();
    Ok((
        serde_json::to_value(result).unwrap(),
        cmd,
        cmd_redacted,
        "AES-CBC encryption with HMAC-SHA256 (Encrypt-then-MAC) for authenticated encryption".to_string(),
    ))
}

async fn execute_aes_decrypt(
    ctx: &ExecutionContext,
    params: &HashMap<String, serde_json::Value>,
) -> Result<ExecutionOutput, OpenSSLError> {
    let ciphertext = get_param_str(params, "ciphertext")?;
    let key = get_param_str(params, "key")?;
    let iv = get_param_str(params, "iv")?;
    let hmac_key = get_param_str(params, "hmac_key")?;
    let hmac = get_param_str(params, "hmac")?;
    let cipher = get_param_str_opt_strict(params, "cipher")?;
    
    let (result, execs) = symmetric::aes_decrypt(ctx, ciphertext, key, iv, hmac_key, hmac, cipher).await?;
    let cmd = execs.last().map(|e| e.command_display.clone()).unwrap_or_default();
    let cmd_redacted = execs.last().map(|e| e.command_redacted.clone()).unwrap_or_default();
    Ok((
        serde_json::to_value(result).unwrap(),
        cmd,
        cmd_redacted,
        "HMAC verified first, then AES-CBC decryption (prevents padding oracle attacks)".to_string(),
    ))
}

// Asymmetric operations
async fn execute_rsa_keygen(
    ctx: &ExecutionContext,
    params: &HashMap<String, serde_json::Value>,
) -> Result<ExecutionOutput, OpenSSLError> {
    let bits = get_param_u64(params, "bits")? as u32;
    let (result, exec) = asymmetric::rsa_keygen(ctx, bits).await?;
    Ok((
        serde_json::to_value(result).unwrap(),
        exec.command_display,
        exec.command_redacted,
        format!("Generates {}-bit RSA key pair using OpenSSL's secure prime generation", bits),
    ))
}

async fn execute_rsa_pubkey(
    ctx: &ExecutionContext,
    params: &HashMap<String, serde_json::Value>,
) -> Result<ExecutionOutput, OpenSSLError> {
    let private_key = get_param_str(params, "private_key")?;
    let (result, exec) = asymmetric::rsa_pubkey(ctx, private_key).await?;
    Ok((
        serde_json::to_value(result).unwrap(),
        exec.command_display,
        exec.command_redacted,
        "Extracts public key from RSA private key".to_string(),
    ))
}

async fn execute_rsa_sign(
    ctx: &ExecutionContext,
    params: &HashMap<String, serde_json::Value>,
) -> Result<ExecutionOutput, OpenSSLError> {
    let data = get_param_str(params, "data")?;
    let private_key = get_param_str(params, "private_key")?;
    let hash_algo = get_param_str_opt_strict(params, "hash_algo")?;
    let (result, exec) = asymmetric::rsa_sign(ctx, data, private_key, hash_algo).await?;
    Ok((
        serde_json::to_value(result).unwrap(),
        exec.command_display,
        exec.command_redacted,
        "RSA signature provides non-repudiation and data integrity".to_string(),
    ))
}

async fn execute_rsa_verify(
    ctx: &ExecutionContext,
    params: &HashMap<String, serde_json::Value>,
) -> Result<ExecutionOutput, OpenSSLError> {
    let data = get_param_str(params, "data")?;
    let signature = get_param_str(params, "signature")?;
    let public_key = get_param_str(params, "public_key")?;
    let hash_algo = get_param_str_opt_strict(params, "hash_algo")?;
    let (result, exec) = asymmetric::rsa_verify(ctx, data, signature, public_key, hash_algo).await?;
    Ok((
        serde_json::to_value(result).unwrap(),
        exec.command_display,
        exec.command_redacted,
        "Verifies RSA signature to confirm data authenticity".to_string(),
    ))
}

async fn execute_rsa_encrypt(
    ctx: &ExecutionContext,
    params: &HashMap<String, serde_json::Value>,
) -> Result<ExecutionOutput, OpenSSLError> {
    let plaintext = get_param_str(params, "plaintext")?;
    let public_key = get_param_str(params, "public_key")?;
    let (result, exec) = asymmetric::rsa_encrypt(ctx, plaintext, public_key).await?;
    Ok((
        serde_json::to_value(result).unwrap(),
        exec.command_display,
        exec.command_redacted,
        "RSA encryption with OAEP padding (SHA-256) for secure key encapsulation".to_string(),
    ))
}

async fn execute_rsa_decrypt(
    ctx: &ExecutionContext,
    params: &HashMap<String, serde_json::Value>,
) -> Result<ExecutionOutput, OpenSSLError> {
    let ciphertext = get_param_str(params, "ciphertext")?;
    let private_key = get_param_str(params, "private_key")?;
    let (result, exec) = asymmetric::rsa_decrypt(ctx, ciphertext, private_key).await?;
    Ok((
        serde_json::to_value(result).unwrap(),
        exec.command_display,
        exec.command_redacted,
        "RSA decryption with OAEP padding (SHA-256)".to_string(),
    ))
}

// PQC signature operations
async fn execute_pqc_sig_keygen(
    ctx: &ExecutionContext,
    params: &HashMap<String, serde_json::Value>,
) -> Result<ExecutionOutput, OpenSSLError> {
    let algorithm = get_param_str_opt_strict(params, "algorithm")?;
    let (result, exec) = pqc::pqc_sig_keygen(ctx, algorithm).await?;
    Ok((
        serde_json::to_value(result).unwrap(),
        exec.command_display,
        exec.command_redacted,
        "Generates PQC signature key pair using oqsprovider (ML-DSA/Falcon)".to_string(),
    ))
}

async fn execute_pqc_sig_sign(
    ctx: &ExecutionContext,
    params: &HashMap<String, serde_json::Value>,
) -> Result<ExecutionOutput, OpenSSLError> {
    let data = get_param_str(params, "data")?;
    let private_key = get_param_str(params, "private_key")?;
    let algorithm = get_param_str_opt_strict(params, "algorithm")?;
    let (result, exec) = pqc::pqc_sig_sign(ctx, data, private_key, algorithm).await?;
    Ok((
        serde_json::to_value(result).unwrap(),
        exec.command_display,
        exec.command_redacted,
        "PQC signature using oqsprovider".to_string(),
    ))
}

async fn execute_pqc_sig_verify(
    ctx: &ExecutionContext,
    params: &HashMap<String, serde_json::Value>,
) -> Result<ExecutionOutput, OpenSSLError> {
    let data = get_param_str(params, "data")?;
    let signature = get_param_str(params, "signature")?;
    let public_key = get_param_str(params, "public_key")?;
    let algorithm = get_param_str_opt_strict(params, "algorithm")?;
    let (result, exec) = pqc::pqc_sig_verify(ctx, data, signature, public_key, algorithm).await?;
    Ok((
        serde_json::to_value(result).unwrap(),
        exec.command_display,
        exec.command_redacted,
        "Verify PQC signature using oqsprovider".to_string(),
    ))
}

// ============================================================================
// Helper functions
// ============================================================================

fn make_error_response(
    code: ErrorCode,
    message: String,
    request_id: &str,
    start: Instant,
) -> (StatusCode, Json<ErrorResponse>) {
    let status = match code {
        ErrorCode::ValidationFailed => StatusCode::BAD_REQUEST,
        ErrorCode::UnsupportedOperation => StatusCode::NOT_FOUND,
        ErrorCode::Timeout => StatusCode::GATEWAY_TIMEOUT,
        ErrorCode::SizeLimitExceeded => StatusCode::PAYLOAD_TOO_LARGE,
        _ => StatusCode::INTERNAL_SERVER_ERROR,
    };
    
    (
        status,
        Json(ErrorResponse {
            success: false,
            error: ErrorInfo {
                code,
                message,
                details: None,
            },
            metadata: ExecutionMetadata {
                execution_time_ms: start.elapsed().as_secs_f64() * 1000.0,
                request_id: request_id.to_string(),
                timestamp: chrono::Utc::now().to_rfc3339(),
            },
        }),
    )
}

fn get_param_type(param: &str) -> String {
    match param {
        "length" | "bits" => "integer",
        "data" | "plaintext" | "ciphertext" | "encoded" | "hex" | "text" => "string",
        "key" | "iv" | "hmac_key" | "hmac" => "string (hex)",
        "signature" => "string (base64)",
        "private_key" | "public_key" => "string (PEM)",
        "algorithm" | "hash_algo" | "cipher" => "string (enum)",
        _ => "string",
    }.to_string()
}

fn is_param_required(operation: &str, param: &str) -> bool {
    match (operation, param) {
        (_, "cipher") => false,
        (_, "hash_algo") => false,
        ("aes_encrypt", "iv") => false,
        ("aes_keygen", "bits") => false,
        ("hash", "algorithm") => false,
        ("pqc_sig_keygen", "algorithm") => false,
        ("pqc_sig_sign", "algorithm") => false,
        ("pqc_sig_verify", "algorithm") => false,
        _ => true,
    }
}

fn get_param_description(param: &str) -> String {
    match param {
        "data" => "Input data to process",
        "plaintext" => "Data to encrypt",
        "ciphertext" => "Encrypted data (Base64)",
        "encoded" => "Base64-encoded string",
        "hex" => "Hexadecimal string",
        "key" => "Encryption key (hex)",
        "iv" => "Initialization vector (hex)",
        "hmac_key" => "HMAC key for authentication (hex)",
        "hmac" => "Expected HMAC value (hex)",
        "private_key" => "RSA private key (PEM format)",
        "public_key" => "RSA public key (PEM format)",
        "signature" => "Digital signature (Base64)",
        "algorithm" => "Algorithm name (hash or PQC, depending on operation)",
        "hash_algo" => "Hash algorithm (sha256, sha512, etc.)",
        "cipher" => "Cipher algorithm (aes-256-cbc, etc.)",
        "bits" => "Key size in bits",
        "length" => "Number of bytes to generate",
        _ => "Parameter value",
    }.to_string()
}

fn get_example_command(operation: &str) -> String {
    match operation {
        "base64_encode" => "echo -n 'hello' | openssl base64 -e -A",
        "base64_decode" => "echo -n 'aGVsbG8=' | openssl base64 -d -A",
        "hex_encode" => "echo -n 'hello' | xxd -p",
        "hex_decode" => "echo -n '68656c6c6f' | xxd -r -p",
        "random_bytes" => "openssl rand -base64 32",
        "random_hex" => "openssl rand -hex 32",
        "random_base64" => "openssl rand -base64 32",
        "hash" => "echo -n 'hello' | openssl dgst -sha256",
        "hmac" => "echo -n 'hello' | openssl dgst -sha256 -hmac 'key'",
        "aes_keygen" => "openssl rand -hex 32 && openssl rand -hex 16",
        "aes_encrypt" => "openssl enc -aes-256-cbc -e -K <key> -iv <iv> -in plain.bin",
        "aes_decrypt" => "openssl enc -aes-256-cbc -d -K <key> -iv <iv> -in cipher.bin",
        "rsa_keygen" => "openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048",
        "rsa_pubkey" => "openssl pkey -pubout -in private.pem",
        "rsa_sign" => "openssl dgst -sha256 -sign private.pem -out sig.bin data.bin",
        "rsa_verify" => "openssl dgst -sha256 -verify public.pem -signature sig.bin data.bin",
        "rsa_encrypt" => "openssl pkeyutl -encrypt -pubin -inkey public.pem -pkeyopt rsa_padding_mode:oaep",
        "rsa_decrypt" => "openssl pkeyutl -decrypt -inkey private.pem -pkeyopt rsa_padding_mode:oaep",
        "pqc_sig_keygen" => "openssl genpkey -provider oqsprovider -provider default -algorithm mldsa44",
        "pqc_sig_sign" => "openssl pkeyutl -provider oqsprovider -provider default -sign -inkey pqc_priv.pem -in data.bin",
        "pqc_sig_verify" => "openssl pkeyutl -provider oqsprovider -provider default -verify -pubin -inkey pqc_pub.pem -sigfile sig.bin -in data.bin",
        _ => "openssl ...",
    }.to_string()
}
