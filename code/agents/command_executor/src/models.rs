//! Request and response models for Command Executor API

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// API request to execute an operation
#[derive(Debug, Deserialize)]
pub struct ExecuteRequest {
    /// Operation name (e.g., "base64_encode", "aes_encrypt")
    pub operation: String,
    /// Operation parameters
    pub params: HashMap<String, serde_json::Value>,
}

/// API response for successful execution
#[derive(Debug, Serialize)]
pub struct ExecuteResponse {
    pub success: bool,
    pub operation: String,
    pub result: serde_json::Value,
    pub command: CommandInfo,
    pub metadata: ExecutionMetadata,
}

/// Information about the executed command
#[derive(Debug, Serialize)]
pub struct CommandInfo {
    /// The command that was executed (may be redacted)
    pub executed: String,
    /// Whether secrets were redacted
    pub redacted: bool,
    /// OpenSSL version used
    pub openssl_version: String,
    /// Human-readable explanation
    #[serde(skip_serializing_if = "Option::is_none")]
    pub explanation: Option<String>,
}

/// Execution metadata
#[derive(Debug, Serialize)]
pub struct ExecutionMetadata {
    /// Execution time in milliseconds
    pub execution_time_ms: f64,
    /// Unique request ID
    pub request_id: String,
    /// Timestamp
    pub timestamp: String,
}

/// API error response
#[derive(Debug, Serialize)]
pub struct ErrorResponse {
    pub success: bool,
    pub error: ErrorInfo,
    pub metadata: ExecutionMetadata,
}

/// Error information
#[derive(Debug, Serialize)]
pub struct ErrorInfo {
    /// Error code
    pub code: ErrorCode,
    /// Human-readable message
    pub message: String,
    /// Additional details
    #[serde(skip_serializing_if = "Option::is_none")]
    pub details: Option<String>,
}

/// Error codes
#[derive(Debug, Serialize, Clone, Copy)]
#[serde(rename_all = "snake_case")]
pub enum ErrorCode {
    UnsupportedOperation,
    OpenSSLError,
    Timeout,
    InternalError,
    ValidationFailed,
    SizeLimitExceeded,
}

/// Health check response
#[derive(Debug, Serialize)]
pub struct HealthResponse {
    pub status: String,
    pub service: String,
    pub version: String,
    pub openssl_version: String,
    pub uptime_seconds: u64,
}

/// PQC health check response
#[derive(Debug, Serialize)]
pub struct PqcHealthResponse {
    pub status: String,
    pub provider_loaded: bool,
    pub providers: Vec<String>,
    pub pqc_signatures: Vec<String>,
    pub pqc_kems: Vec<String>,
    pub message: String,
    pub openssl_version: String,
}

/// Operations list response
#[derive(Debug, Serialize)]
pub struct OperationsResponse {
    pub operations: Vec<OperationDetail>,
    pub total: usize,
}

/// Operation detail for documentation
#[derive(Debug, Serialize)]
pub struct OperationDetail {
    pub name: String,
    pub category: String,
    pub description: String,
    pub parameters: Vec<ParameterDetail>,
    pub example_command: String,
}

/// Parameter detail
#[derive(Debug, Serialize)]
pub struct ParameterDetail {
    pub name: String,
    pub r#type: String,
    pub required: bool,
    pub description: String,
}

/// Ciphers/algorithms response
#[derive(Debug, Serialize)]
pub struct CiphersResponse {
    pub symmetric: Vec<CipherInfo>,
    pub hash_algorithms: Vec<String>,
    pub rsa_key_sizes: Vec<u32>,
    pub ec_curves: Vec<String>,
    pub pqc_signatures: Vec<String>,
    pub pqc_kems: Vec<String>,
}

/// Cipher information
#[derive(Debug, Serialize)]
pub struct CipherInfo {
    pub name: String,
    pub key_bits: usize,
    pub iv_bits: usize,
    pub mode: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub warning: Option<String>,
}

// ============================================================================
// Result types for internal operations
// ============================================================================

/// Result of an encoding operation
#[derive(Debug, Serialize)]
pub struct EncodingResult {
    pub output: String,
}

/// Result of a random generation operation
#[derive(Debug, Serialize)]
pub struct RandomResult {
    pub output: String,
    pub bytes_generated: usize,
}

/// Result of a hash operation
#[derive(Debug, Serialize)]
pub struct HashResult {
    pub hash: String,
    pub algorithm: String,
}

/// Result of HMAC operation
#[derive(Debug, Serialize)]
pub struct HmacResult {
    pub mac: String,
    pub algorithm: String,
}

/// Result of AES encryption
#[derive(Debug, Serialize)]
pub struct AesEncryptResult {
    pub ciphertext_base64: String,
    pub iv_hex: String,
    pub hmac_hex: String,
    pub cipher: String,
}

/// Result of AES decryption
#[derive(Debug, Serialize)]
pub struct AesDecryptResult {
    pub plaintext: String,
    pub hmac_verified: bool,
}

/// Result of AES key generation
#[derive(Debug, Serialize)]
pub struct AesKeygenResult {
    pub key_hex: String,
    pub iv_hex: String,
    pub hmac_key_hex: String,
    pub key_bits: usize,
}

/// Result of RSA key generation
#[derive(Debug, Serialize)]
pub struct RsaKeygenResult {
    pub private_key_pem: String,
    pub public_key_pem: String,
    pub bits: u32,
}

/// Result of RSA public key extraction
#[derive(Debug, Serialize)]
pub struct RsaPubkeyResult {
    pub public_key_pem: String,
}

/// Result of RSA signing
#[derive(Debug, Serialize)]
pub struct RsaSignResult {
    pub signature_base64: String,
    pub algorithm: String,
}

/// Result of RSA verification
#[derive(Debug, Serialize)]
pub struct RsaVerifyResult {
    pub valid: bool,
    pub algorithm: String,
}

/// Result of RSA encryption
#[derive(Debug, Serialize)]
pub struct RsaEncryptResult {
    pub ciphertext_base64: String,
}

/// Result of RSA decryption
#[derive(Debug, Serialize)]
pub struct RsaDecryptResult {
    pub plaintext: String,
}

/// Result of PQC signature key generation
#[derive(Debug, Serialize)]
pub struct PqcSigKeygenResult {
    pub private_key_pem: String,
    pub public_key_pem: String,
    pub algorithm: String,
}

/// Result of PQC signature operation
#[derive(Debug, Serialize)]
pub struct PqcSigSignResult {
    pub signature_base64: String,
    pub algorithm: String,
}

/// Result of PQC signature verification
#[derive(Debug, Serialize)]
pub struct PqcSigVerifyResult {
    pub valid: bool,
    pub algorithm: String,
}
