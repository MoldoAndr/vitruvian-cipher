//! Hashing operations provider
//! SHA-256, SHA-512, HMAC via OpenSSL dgst

use crate::models::{HashResult, HmacResult};
use crate::openssl::{ExecutionContext, ExecutionResult, OpenSSLCommand, OpenSSLError};
use crate::validators::{validate_hash_algo, validate_size};
use crate::config::MAX_INPUT_SIZE;

/// Compute hash digest of data
/// Command: echo -n "data" | openssl dgst -sha256
pub async fn hash(
    ctx: &ExecutionContext,
    data: &str,
    algorithm: &str,
) -> Result<(HashResult, ExecutionResult), OpenSSLError> {
    validate_size(data.as_bytes(), MAX_INPUT_SIZE)
        .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;
    
    let algo = validate_hash_algo(algorithm)
        .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;
    
    let result = OpenSSLCommand::new()
        .arg("dgst")
        .arg(format!("-{}", algo))
        .arg("-r")  // Output in format: hash *stdin
        .stdin(data.as_bytes().to_vec())
        .execute(ctx)
        .await?;
    
    if result.exit_code != 0 {
        return Err(OpenSSLError::ExecutionFailed(result.stderr));
    }
    
    // Parse output: "hash_hex *stdin" or "hash_hex(stdin)= hash"
    let output = String::from_utf8_lossy(&result.stdout);
    let hash_hex = output
        .split_whitespace()
        .next()
        .unwrap_or("")
        .trim()
        .to_string();
    
    Ok((
        HashResult {
            hash: hash_hex,
            algorithm: algo.to_string(),
        },
        result,
    ))
}

/// Compute HMAC of data
/// Command: echo -n "data" | openssl dgst -sha256 -hmac "key"
pub async fn hmac(
    ctx: &ExecutionContext,
    data: &str,
    key: &str,
    algorithm: &str,
) -> Result<(HmacResult, ExecutionResult), OpenSSLError> {
    validate_size(data.as_bytes(), MAX_INPUT_SIZE)
        .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;
    
    let algo = validate_hash_algo(algorithm)
        .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;
    
    let result = OpenSSLCommand::new()
        .arg("dgst")
        .arg(format!("-{}", algo))
        .arg("-hmac")
        .secret_arg(key)
        .arg("-r")
        .stdin(data.as_bytes().to_vec())
        .execute(ctx)
        .await?;
    
    if result.exit_code != 0 {
        return Err(OpenSSLError::ExecutionFailed(result.stderr));
    }
    
    let output = String::from_utf8_lossy(&result.stdout);
    let mac_hex = output
        .split_whitespace()
        .next()
        .unwrap_or("")
        .trim()
        .to_string();
    
    Ok((
        HmacResult {
            mac: mac_hex,
            algorithm: algo.to_string(),
        },
        result,
    ))
}

/// Compute HMAC with hex-encoded key (for use with AES HMAC)
/// Command: echo -n "data" | openssl dgst -sha256 -mac hmac -macopt hexkey:key
pub async fn hmac_hex_key(
    ctx: &ExecutionContext,
    data: &[u8],
    key_hex: &str,
    algorithm: &str,
) -> Result<(HmacResult, ExecutionResult), OpenSSLError> {
    validate_size(data, MAX_INPUT_SIZE)
        .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;
    
    let algo = validate_hash_algo(algorithm)
        .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;
    
    let result = OpenSSLCommand::new()
        .arg("dgst")
        .arg(format!("-{}", algo))
        .arg("-mac")
        .arg("hmac")
        .arg("-macopt")
        .secret_arg(format!("hexkey:{}", key_hex))
        .arg("-r")
        .stdin(data.to_vec())
        .execute(ctx)
        .await?;
    
    if result.exit_code != 0 {
        return Err(OpenSSLError::ExecutionFailed(result.stderr));
    }
    
    let output = String::from_utf8_lossy(&result.stdout);
    let mac_hex = output
        .split_whitespace()
        .next()
        .unwrap_or("")
        .trim()
        .to_string();
    
    Ok((
        HmacResult {
            mac: mac_hex,
            algorithm: algo.to_string(),
        },
        result,
    ))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::EXECUTION_TIMEOUT_MS;
    
    #[tokio::test]
    async fn test_sha256_hash() {
        let ctx = ExecutionContext::new(EXECUTION_TIMEOUT_MS).unwrap();
        let (result, _) = hash(&ctx, "hello", "sha256").await.unwrap();
        
        // Known SHA-256 of "hello"
        assert_eq!(
            result.hash,
            "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
        );
    }
    
    #[tokio::test]
    async fn test_sha512_hash() {
        let ctx = ExecutionContext::new(EXECUTION_TIMEOUT_MS).unwrap();
        let (result, _) = hash(&ctx, "hello", "sha512").await.unwrap();
        
        assert_eq!(result.algorithm, "sha512");
        assert_eq!(result.hash.len(), 128); // 512 bits = 128 hex chars
    }
    
    #[tokio::test]
    async fn test_hmac() {
        let ctx = ExecutionContext::new(EXECUTION_TIMEOUT_MS).unwrap();
        let (result, _) = hmac(&ctx, "hello", "secret", "sha256").await.unwrap();
        
        assert!(!result.mac.is_empty());
        assert_eq!(result.algorithm, "sha256");
    }
    
    #[tokio::test]
    async fn test_invalid_algorithm() {
        let ctx = ExecutionContext::new(EXECUTION_TIMEOUT_MS).unwrap();
        let result = hash(&ctx, "hello", "invalid_algo").await;
        
        assert!(result.is_err());
    }
}
