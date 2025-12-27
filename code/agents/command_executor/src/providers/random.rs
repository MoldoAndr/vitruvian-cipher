//! Random generation provider
//! Cryptographically secure random bytes via OpenSSL

use crate::models::RandomResult;
use crate::openssl::{ExecutionContext, ExecutionResult, OpenSSLCommand, OpenSSLError};
use crate::validators::validate_length;

/// Maximum random bytes to generate
const MAX_RANDOM_BYTES: usize = 1024;

/// Generate random bytes (base64 encoded output)
/// Command: openssl rand -base64 N
pub async fn random_bytes(
    ctx: &ExecutionContext,
    length: usize,
) -> Result<(RandomResult, ExecutionResult), OpenSSLError> {
    validate_length(length, MAX_RANDOM_BYTES)
        .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;
    
    let result = OpenSSLCommand::new()
        .arg("rand")
        .arg("-base64")
        .arg(length.to_string())
        .execute(ctx)
        .await?;
    
    if result.exit_code != 0 {
        return Err(OpenSSLError::ExecutionFailed(result.stderr));
    }
    
    let output = String::from_utf8_lossy(&result.stdout)
        .chars()
        .filter(|c| !c.is_whitespace())
        .collect();
    
    Ok((
        RandomResult {
            output,
            bytes_generated: length,
        },
        result,
    ))
}

/// Generate random hex string
/// Command: openssl rand -hex N
pub async fn random_hex(
    ctx: &ExecutionContext,
    length: usize,
) -> Result<(RandomResult, ExecutionResult), OpenSSLError> {
    validate_length(length, MAX_RANDOM_BYTES)
        .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;
    
    let result = OpenSSLCommand::new()
        .arg("rand")
        .arg("-hex")
        .arg(length.to_string())
        .execute(ctx)
        .await?;
    
    if result.exit_code != 0 {
        return Err(OpenSSLError::ExecutionFailed(result.stderr));
    }
    
    let output = String::from_utf8_lossy(&result.stdout).trim().to_string();
    
    Ok((
        RandomResult {
            output,
            bytes_generated: length,
        },
        result,
    ))
}

/// Generate random base64 string
/// Command: openssl rand -base64 N
pub async fn random_base64(
    ctx: &ExecutionContext,
    length: usize,
) -> Result<(RandomResult, ExecutionResult), OpenSSLError> {
    // Same as random_bytes but with cleaner naming for API
    random_bytes(ctx, length).await
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::EXECUTION_TIMEOUT_MS;
    
    #[tokio::test]
    async fn test_random_hex() {
        let ctx = ExecutionContext::new(EXECUTION_TIMEOUT_MS).unwrap();
        let (result, _) = random_hex(&ctx, 32).await.unwrap();
        
        // 32 bytes = 64 hex chars
        assert_eq!(result.output.len(), 64);
        assert!(result.output.chars().all(|c| c.is_ascii_hexdigit()));
    }
    
    #[tokio::test]
    async fn test_random_base64() {
        let ctx = ExecutionContext::new(EXECUTION_TIMEOUT_MS).unwrap();
        let (result, _) = random_base64(&ctx, 16).await.unwrap();
        
        // Base64 of 16 bytes should be ~22 chars
        assert!(!result.output.is_empty());
        assert_eq!(result.bytes_generated, 16);
    }
    
    #[tokio::test]
    async fn test_random_length_limit() {
        let ctx = ExecutionContext::new(EXECUTION_TIMEOUT_MS).unwrap();
        let result = random_hex(&ctx, 10000).await;
        
        assert!(result.is_err());
    }
}
