//! Encoding operations provider
//! Base64 and hex encoding/decoding via OpenSSL

use crate::models::EncodingResult;
use crate::openssl::{ExecutionContext, ExecutionResult, OpenSSLCommand, OpenSSLError};
use crate::validators::{validate_base64, validate_hex, validate_size};
use crate::config::MAX_INPUT_SIZE;

/// Base64 encode data
/// Command: echo -n "data" | openssl base64 -e -A
pub async fn base64_encode(
    ctx: &ExecutionContext,
    data: &str,
) -> Result<(EncodingResult, ExecutionResult), OpenSSLError> {
    validate_size(data.as_bytes(), MAX_INPUT_SIZE)
        .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;
    
    let result = OpenSSLCommand::new()
        .arg("base64")
        .arg("-e")
        .arg("-A")  // Single line output
        .stdin(data.as_bytes().to_vec())
        .execute(ctx)
        .await?;
    
    if result.exit_code != 0 {
        return Err(OpenSSLError::ExecutionFailed(result.stderr));
    }
    
    let output = String::from_utf8_lossy(&result.stdout).trim().to_string();
    
    Ok((EncodingResult { output }, result))
}

/// Base64 decode data
/// Command: echo -n "encoded" | openssl base64 -d -A
pub async fn base64_decode(
    ctx: &ExecutionContext,
    encoded: &str,
) -> Result<(EncodingResult, ExecutionResult), OpenSSLError> {
    let decoded_bytes = validate_base64(encoded)
        .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;
    validate_size(&decoded_bytes, MAX_INPUT_SIZE)
        .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;
    
    let result = OpenSSLCommand::new()
        .arg("base64")
        .arg("-d")
        .arg("-A")
        .stdin(encoded.as_bytes().to_vec())
        .execute(ctx)
        .await?;
    
    if result.exit_code != 0 {
        return Err(OpenSSLError::ExecutionFailed(result.stderr));
    }
    
    let output = String::from_utf8_lossy(&result.stdout).to_string();
    
    Ok((EncodingResult { output }, result))
}

/// Hex encode data using xxd
/// Command: echo -n "data" | xxd -p
pub async fn hex_encode(
    ctx: &ExecutionContext,
    data: &str,
) -> Result<(EncodingResult, ExecutionResult), OpenSSLError> {
    validate_size(data.as_bytes(), MAX_INPUT_SIZE)
        .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;
    
    let result = OpenSSLCommand::xxd()
        .arg("-p")
        .stdin(data.as_bytes().to_vec())
        .execute(ctx)
        .await?;
    
    if result.exit_code != 0 {
        return Err(OpenSSLError::ExecutionFailed(result.stderr));
    }
    
    // xxd outputs with newlines, remove them
    let output = String::from_utf8_lossy(&result.stdout)
        .chars()
        .filter(|c| !c.is_whitespace())
        .collect();
    
    Ok((EncodingResult { output }, result))
}

/// Hex decode data using xxd
/// Command: echo -n "hex" | xxd -r -p
pub async fn hex_decode(
    ctx: &ExecutionContext,
    hex_data: &str,
) -> Result<(EncodingResult, ExecutionResult), OpenSSLError> {
    let decoded_bytes = validate_hex(hex_data)
        .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;
    validate_size(&decoded_bytes, MAX_INPUT_SIZE)
        .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;
    
    let result = OpenSSLCommand::xxd()
        .arg("-r")
        .arg("-p")
        .stdin(hex_data.as_bytes().to_vec())
        .execute(ctx)
        .await?;
    
    if result.exit_code != 0 {
        return Err(OpenSSLError::ExecutionFailed(result.stderr));
    }
    
    let output = String::from_utf8_lossy(&result.stdout).to_string();
    
    Ok((EncodingResult { output }, result))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::EXECUTION_TIMEOUT_MS;
    
    #[tokio::test]
    async fn test_base64_roundtrip() {
        let ctx = ExecutionContext::new(EXECUTION_TIMEOUT_MS).unwrap();
        let original = "Hello, World!";
        
        let (encoded, _) = base64_encode(&ctx, original).await.unwrap();
        assert_eq!(encoded.output, "SGVsbG8sIFdvcmxkIQ==");
        
        let (decoded, _) = base64_decode(&ctx, &encoded.output).await.unwrap();
        assert_eq!(decoded.output, original);
    }
    
    #[tokio::test]
    async fn test_hex_roundtrip() {
        let ctx = ExecutionContext::new(EXECUTION_TIMEOUT_MS).unwrap();
        let original = "Hello";
        
        let (encoded, _) = hex_encode(&ctx, original).await.unwrap();
        assert_eq!(encoded.output.to_lowercase(), "48656c6c6f");
        
        let (decoded, _) = hex_decode(&ctx, &encoded.output).await.unwrap();
        assert_eq!(decoded.output, original);
    }
}
