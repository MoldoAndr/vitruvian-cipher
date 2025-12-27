//! Input validation module
//! Strict validation to prevent injection and ensure correctness

use crate::config::*;
use lazy_static::lazy_static;
use regex::Regex;
use thiserror::Error;

lazy_static! {
    /// Regex for valid hexadecimal strings
    static ref HEX_REGEX: Regex = Regex::new(r"^[0-9a-fA-F]+$").unwrap();
    
    /// Regex for valid Base64 strings
    static ref BASE64_REGEX: Regex = Regex::new(r"^[A-Za-z0-9+/]*={0,2}$").unwrap();
    
    /// Regex for detecting shell injection attempts
    static ref INJECTION_REGEX: Regex = Regex::new(r"[;&|`$\n\r\\]").unwrap();
    
    /// Regex for valid PEM format
    static ref PEM_REGEX: Regex = Regex::new(r"^-----BEGIN [A-Z ]+-----[\s\S]+-----END [A-Z ]+-----\s*$").unwrap();
}

#[derive(Error, Debug)]
pub enum ValidationError {
    #[error("Input exceeds maximum size of {0} bytes")]
    SizeLimitExceeded(usize),
    
    #[error("Invalid hex string: {0}")]
    InvalidHex(String),
    
    #[error("Invalid Base64 string: {0}")]
    InvalidBase64(String),
    
    #[error("Invalid key length: expected {expected} bytes, got {actual}")]
    InvalidKeyLength { expected: usize, actual: usize },
    
    #[error("Invalid IV length: expected {expected} bytes, got {actual}")]
    InvalidIvLength { expected: usize, actual: usize },
    
    #[error("Unsupported algorithm: {0}")]
    UnsupportedAlgorithm(String),
    
    #[error("Unsupported RSA key size: {0}. Allowed: 2048, 3072, 4096")]
    UnsupportedKeySize(u32),
    
    #[error("Potential injection detected in input")]
    InjectionDetected,
    
    #[error("Invalid PEM format")]
    InvalidPem,
    
    #[error("Length must be positive and <= {0}")]
    InvalidLength(usize),
}

/// Validate that input size is within limits
pub fn validate_size(data: &[u8], max_size: usize) -> Result<(), ValidationError> {
    if data.len() > max_size {
        return Err(ValidationError::SizeLimitExceeded(max_size));
    }
    Ok(())
}

/// Validate that a string is valid hexadecimal
pub fn validate_hex(hex: &str) -> Result<Vec<u8>, ValidationError> {
    // Check for even length
    if hex.len() % 2 != 0 {
        return Err(ValidationError::InvalidHex(
            "Hex string must have even length".to_string(),
        ));
    }
    
    // Check for valid characters
    if !HEX_REGEX.is_match(hex) {
        return Err(ValidationError::InvalidHex(
            "Hex string contains invalid characters".to_string(),
        ));
    }
    
    // Decode to bytes
    hex::decode(hex).map_err(|e| ValidationError::InvalidHex(e.to_string()))
}

/// Validate that a string is valid Base64
pub fn validate_base64(b64: &str) -> Result<Vec<u8>, ValidationError> {
    // Remove whitespace for validation
    let clean: String = b64.chars().filter(|c| !c.is_whitespace()).collect();
    
    if !BASE64_REGEX.is_match(&clean) {
        return Err(ValidationError::InvalidBase64(
            "Invalid Base64 characters".to_string(),
        ));
    }
    
    base64::Engine::decode(&base64::engine::general_purpose::STANDARD, &clean)
        .map_err(|e| ValidationError::InvalidBase64(e.to_string()))
}

/// Validate AES key for a specific cipher
pub fn validate_aes_key(key_hex: &str, cipher: &str) -> Result<Vec<u8>, ValidationError> {
    let expected_len = get_cipher_key_length(cipher)
        .ok_or_else(|| ValidationError::UnsupportedAlgorithm(cipher.to_string()))?;
    
    let key_bytes = validate_hex(key_hex)?;
    
    if key_bytes.len() != expected_len {
        return Err(ValidationError::InvalidKeyLength {
            expected: expected_len,
            actual: key_bytes.len(),
        });
    }
    
    Ok(key_bytes)
}

/// Validate AES IV for a specific cipher
pub fn validate_aes_iv(iv_hex: &str, cipher: &str) -> Result<Vec<u8>, ValidationError> {
    let expected_len = get_cipher_iv_length(cipher)
        .ok_or_else(|| ValidationError::UnsupportedAlgorithm(cipher.to_string()))?;
    
    let iv_bytes = validate_hex(iv_hex)?;
    
    if iv_bytes.len() != expected_len {
        return Err(ValidationError::InvalidIvLength {
            expected: expected_len,
            actual: iv_bytes.len(),
        });
    }
    
    Ok(iv_bytes)
}

/// Validate hash algorithm
pub fn validate_hash_algo(algo: &str) -> Result<&str, ValidationError> {
    let algo_lower = algo.to_lowercase();
    if ALLOWED_HASH_ALGOS.contains(algo_lower.as_str()) {
        // Return the canonical form
        Ok(match algo_lower.as_str() {
            "sha256" => "sha256",
            "sha384" => "sha384",
            "sha512" => "sha512",
            "sha3-256" => "sha3-256",
            "sha3-512" => "sha3-512",
            "md5" => "md5",
            "blake2b512" => "blake2b512",
            "blake2s256" => "blake2s256",
            _ => return Err(ValidationError::UnsupportedAlgorithm(algo.to_string())),
        })
    } else {
        Err(ValidationError::UnsupportedAlgorithm(algo.to_string()))
    }
}

/// Validate symmetric cipher
pub fn validate_cipher(cipher: &str) -> Result<&'static str, ValidationError> {
    let cipher_lower = cipher.to_lowercase();
    if ALLOWED_SYMMETRIC_CIPHERS.contains(cipher_lower.as_str()) {
        Ok(match cipher_lower.as_str() {
            "aes-128-cbc" => "aes-128-cbc",
            "aes-192-cbc" => "aes-192-cbc",
            "aes-256-cbc" => "aes-256-cbc",
            "chacha20" => "chacha20",
            "des-ede3-cbc" => "des-ede3-cbc",
            _ => return Err(ValidationError::UnsupportedAlgorithm(cipher.to_string())),
        })
    } else {
        Err(ValidationError::UnsupportedAlgorithm(cipher.to_string()))
    }
}

/// Validate PQC signature algorithm
pub fn validate_pqc_sig_algo(algo: &str) -> Result<&'static str, ValidationError> {
    let algo_lower = algo.to_lowercase();
    if ALLOWED_PQC_SIG_ALGOS.contains(algo_lower.as_str()) {
        Ok(match algo_lower.as_str() {
            "mldsa44" | "dilithium2" => "mldsa44",
            "mldsa65" | "dilithium3" => "mldsa65",
            "mldsa87" | "dilithium5" => "mldsa87",
            "falcon512" | "falcon-512" => "falcon512",
            "falcon1024" | "falcon-1024" => "falcon1024",
            "falconpadded512" => "falconpadded512",
            "falconpadded1024" => "falconpadded1024",
            _ => return Err(ValidationError::UnsupportedAlgorithm(algo.to_string())),
        })
    } else {
        Err(ValidationError::UnsupportedAlgorithm(algo.to_string()))
    }
}

/// Validate PQC KEM algorithm
#[allow(dead_code)]
pub fn validate_pqc_kem_algo(algo: &str) -> Result<&'static str, ValidationError> {
    let algo_lower = algo.to_lowercase();
    if ALLOWED_PQC_KEM_ALGOS.contains(algo_lower.as_str()) {
        Ok(match algo_lower.as_str() {
            "mlkem512" | "kyber512" => "mlkem512",
            "mlkem768" | "kyber768" => "mlkem768",
            "mlkem1024" | "kyber1024" => "mlkem1024",
            _ => return Err(ValidationError::UnsupportedAlgorithm(algo.to_string())),
        })
    } else {
        Err(ValidationError::UnsupportedAlgorithm(algo.to_string()))
    }
}

/// Validate RSA key size
pub fn validate_rsa_bits(bits: u32) -> Result<u32, ValidationError> {
    if ALLOWED_RSA_BITS.contains(&bits) {
        Ok(bits)
    } else {
        Err(ValidationError::UnsupportedKeySize(bits))
    }
}

/// Validate PEM-encoded key
pub fn validate_pem(pem: &str) -> Result<(), ValidationError> {
    if !PEM_REGEX.is_match(pem) {
        return Err(ValidationError::InvalidPem);
    }
    Ok(())
}

/// Check for potential shell injection in any string input
pub fn check_injection(input: &str) -> Result<(), ValidationError> {
    if INJECTION_REGEX.is_match(input) {
        return Err(ValidationError::InjectionDetected);
    }
    Ok(())
}

/// Validate length parameter for random generation
pub fn validate_length(length: usize, max: usize) -> Result<usize, ValidationError> {
    if length == 0 || length > max {
        return Err(ValidationError::InvalidLength(max));
    }
    Ok(length)
}

/// Sanitize string for display in commands (replace secrets)
pub fn redact_secret(secret: &str) -> String {
    if secret.len() <= 8 {
        "*".repeat(secret.len())
    } else {
        format!("{}...{}", &secret[..4], &secret[secret.len()-4..])
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_valid_hex() {
        assert!(validate_hex("0123456789abcdef").is_ok());
        assert!(validate_hex("ABCDEF").is_ok());
    }
    
    #[test]
    fn test_invalid_hex() {
        assert!(validate_hex("0123456789abcdefg").is_err()); // Invalid char
        assert!(validate_hex("123").is_err()); // Odd length
    }
    
    #[test]
    fn test_injection_detection() {
        assert!(check_injection("normal text").is_ok());
        assert!(check_injection("text; rm -rf /").is_err());
        assert!(check_injection("text | cat").is_err());
        assert!(check_injection("$(whoami)").is_err());
        assert!(check_injection("text`id`").is_err());
    }
    
    #[test]
    fn test_aes_key_validation() {
        // 32 bytes = 64 hex chars for AES-256
        let valid_key = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";
        assert!(validate_aes_key(valid_key, "aes-256-cbc").is_ok());
        
        // Wrong length
        let short_key = "0123456789abcdef";
        assert!(validate_aes_key(short_key, "aes-256-cbc").is_err());
    }

    #[test]
    fn test_pqc_sig_algo_aliases() {
        assert_eq!(validate_pqc_sig_algo("mldsa44").unwrap(), "mldsa44");
        assert_eq!(validate_pqc_sig_algo("dilithium2").unwrap(), "mldsa44");
        assert_eq!(validate_pqc_sig_algo("falcon-512").unwrap(), "falcon512");
        assert!(validate_pqc_sig_algo("unknown").is_err());
    }
}
