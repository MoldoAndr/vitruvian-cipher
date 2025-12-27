//! Symmetric encryption provider
//! AES-256-CBC + HMAC-SHA256 (Encrypt-then-MAC)

use crate::models::{AesEncryptResult, AesDecryptResult, AesKeygenResult};
use crate::openssl::{ExecutionContext, ExecutionResult, OpenSSLCommand, OpenSSLError};
use crate::validators::{validate_aes_key, validate_aes_iv, validate_hex, validate_size, validate_cipher};
use crate::config::{MAX_INPUT_SIZE, get_cipher_iv_length};
use crate::providers::hashing::hmac_hex_key;
use base64::{Engine, engine::general_purpose::STANDARD as BASE64};
use subtle::ConstantTimeEq;

/// Default cipher for v1
const DEFAULT_CIPHER: &str = "aes-256-cbc";

/// Generate AES key, IV, and HMAC key
/// Command: openssl rand -hex 32 (key) + openssl rand -hex 16 (iv) + openssl rand -hex 32 (hmac)
pub async fn aes_keygen(
    ctx: &ExecutionContext,
    bits: Option<usize>,
) -> Result<(AesKeygenResult, Vec<ExecutionResult>), OpenSSLError> {
    let key_bits = bits.unwrap_or(256);
    if ![128, 192, 256].contains(&key_bits) {
        return Err(OpenSSLError::ExecutionFailed(
            "Invalid key size. Use 128, 192, or 256 bits".to_string()
        ));
    }

    let key_bytes = key_bits / 8;
    
    let iv_bytes = 16; // AES block size
    let hmac_key_bytes = 32; // HMAC-SHA256 key
    
    // Generate key
    let key_result = OpenSSLCommand::new()
        .arg("rand")
        .arg("-hex")
        .arg(key_bytes.to_string())
        .execute(ctx)
        .await?;
    
    if key_result.exit_code != 0 {
        return Err(OpenSSLError::ExecutionFailed(key_result.stderr.clone()));
    }
    
    let key_hex = String::from_utf8_lossy(&key_result.stdout).trim().to_string();
    
    // Generate IV
    let iv_result = OpenSSLCommand::new()
        .arg("rand")
        .arg("-hex")
        .arg(iv_bytes.to_string())
        .execute(ctx)
        .await?;
    
    if iv_result.exit_code != 0 {
        return Err(OpenSSLError::ExecutionFailed(iv_result.stderr.clone()));
    }
    
    let iv_hex = String::from_utf8_lossy(&iv_result.stdout).trim().to_string();
    
    // Generate HMAC key
    let hmac_result = OpenSSLCommand::new()
        .arg("rand")
        .arg("-hex")
        .arg(hmac_key_bytes.to_string())
        .execute(ctx)
        .await?;
    
    if hmac_result.exit_code != 0 {
        return Err(OpenSSLError::ExecutionFailed(hmac_result.stderr.clone()));
    }
    
    let hmac_key_hex = String::from_utf8_lossy(&hmac_result.stdout).trim().to_string();
    
    Ok((
        AesKeygenResult {
            key_hex,
            iv_hex,
            hmac_key_hex,
            key_bits,
        },
        vec![key_result, iv_result, hmac_result],
    ))
}

/// Encrypt data with AES-CBC + HMAC (Encrypt-then-MAC)
/// Commands:
///   1. openssl enc -aes-256-cbc -e -K <key> -iv <iv> -in plain.bin -out cipher.bin
///   2. openssl dgst -sha256 -mac hmac -macopt hexkey:<hmac_key> cipher.bin
pub async fn aes_encrypt(
    ctx: &ExecutionContext,
    plaintext: &str,
    key_hex: &str,
    iv_hex: Option<&str>,
    hmac_key_hex: &str,
    cipher: Option<&str>,
) -> Result<(AesEncryptResult, Vec<ExecutionResult>), OpenSSLError> {
    let cipher_name = cipher.unwrap_or(DEFAULT_CIPHER);
    let cipher_validated = validate_cipher(cipher_name)
        .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;
    
    // Validate inputs
    validate_size(plaintext.as_bytes(), MAX_INPUT_SIZE)
        .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;
    
    validate_aes_key(key_hex, cipher_validated)
        .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;
    
    // Generate IV if not provided
    let iv_hex_final = if let Some(iv) = iv_hex {
        validate_aes_iv(iv, cipher_validated)
            .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;
        iv.to_string()
    } else {
        let iv_len = get_cipher_iv_length(cipher_validated).unwrap_or(16);
        let iv_result = OpenSSLCommand::new()
            .arg("rand")
            .arg("-hex")
            .arg(iv_len.to_string())
            .execute(ctx)
            .await?;
        if iv_result.exit_code != 0 {
            return Err(OpenSSLError::ExecutionFailed(iv_result.stderr.clone()));
        }
        String::from_utf8_lossy(&iv_result.stdout).trim().to_string()
    };
    
    // Validate HMAC key
    validate_hex(hmac_key_hex)
        .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;
    
    // Write plaintext to temp file
    let input_path = ctx.write_temp_file("plaintext.bin", plaintext.as_bytes()).await?;
    let output_path = ctx.temp_file("ciphertext.bin");
    
    // Encrypt
    let encrypt_result = OpenSSLCommand::new()
        .arg("enc")
        .arg(format!("-{}", cipher_validated))
        .arg("-e")
        .arg("-K")
        .secret_arg(key_hex)
        .arg("-iv")
        .arg(&iv_hex_final)
        .arg("-in")
        .arg(input_path.to_string_lossy().to_string())
        .arg("-out")
        .arg(output_path.to_string_lossy().to_string())
        .execute(ctx)
        .await?;
    
    if encrypt_result.exit_code != 0 {
        return Err(OpenSSLError::ExecutionFailed(encrypt_result.stderr.clone()));
    }
    
    // Read ciphertext
    let ciphertext = ctx.read_temp_file("ciphertext.bin").await?;
    let ciphertext_base64 = BASE64.encode(&ciphertext);
    
    // Compute HMAC over ciphertext (Encrypt-then-MAC)
    let (hmac_result, hmac_exec) = hmac_hex_key(ctx, &ciphertext, hmac_key_hex, "sha256").await?;
    
    Ok((
        AesEncryptResult {
            ciphertext_base64,
            iv_hex: iv_hex_final,
            hmac_hex: hmac_result.mac,
            cipher: cipher_validated.to_string(),
        },
        vec![encrypt_result, hmac_exec],
    ))
}

/// Decrypt data with AES-CBC (verifies HMAC first)
/// Commands:
///   1. openssl dgst -sha256 -mac hmac -macopt hexkey:<hmac_key> cipher.bin (verify)
///   2. openssl enc -aes-256-cbc -d -K <key> -iv <iv> -in cipher.bin -out plain.bin
pub async fn aes_decrypt(
    ctx: &ExecutionContext,
    ciphertext_base64: &str,
    key_hex: &str,
    iv_hex: &str,
    hmac_key_hex: &str,
    expected_hmac: &str,
    cipher: Option<&str>,
) -> Result<(AesDecryptResult, Vec<ExecutionResult>), OpenSSLError> {
    let cipher_name = cipher.unwrap_or(DEFAULT_CIPHER);
    let cipher_validated = validate_cipher(cipher_name)
        .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;
    
    // Validate inputs
    validate_aes_key(key_hex, cipher_validated)
        .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;
    validate_aes_iv(iv_hex, cipher_validated)
        .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;
    validate_hex(hmac_key_hex)
        .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;
    validate_hex(expected_hmac)
        .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;
    
    // Decode ciphertext
    let ciphertext = BASE64.decode(ciphertext_base64)
        .map_err(|e| OpenSSLError::ExecutionFailed(format!("Invalid base64: {}", e)))?;
    
    validate_size(&ciphertext, MAX_INPUT_SIZE)
        .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;
    
    // STEP 1: Verify HMAC FIRST (critical for security!)
    let (computed_hmac, hmac_exec) = hmac_hex_key(ctx, &ciphertext, hmac_key_hex, "sha256").await?;
    
    let expected_bytes = hex::decode(expected_hmac)
        .map_err(|e| OpenSSLError::ExecutionFailed(format!("Invalid HMAC hex: {}", e)))?;
    let computed_bytes = hex::decode(&computed_hmac.mac)
        .map_err(|e| OpenSSLError::ExecutionFailed(format!("Invalid HMAC hex: {}", e)))?;

    if expected_bytes.len() != computed_bytes.len()
        || !bool::from(expected_bytes.ct_eq(&computed_bytes))
    {
        return Err(OpenSSLError::ExecutionFailed(
            "HMAC verification failed! Ciphertext may have been tampered with.".to_string()
        ));
    }
    
    // STEP 2: Decrypt (only after HMAC verification)
    let input_path = ctx.write_temp_file("ciphertext.bin", &ciphertext).await?;
    let output_path = ctx.temp_file("plaintext.bin");
    
    let decrypt_result = OpenSSLCommand::new()
        .arg("enc")
        .arg(format!("-{}", cipher_validated))
        .arg("-d")
        .arg("-K")
        .secret_arg(key_hex)
        .arg("-iv")
        .arg(iv_hex)
        .arg("-in")
        .arg(input_path.to_string_lossy().to_string())
        .arg("-out")
        .arg(output_path.to_string_lossy().to_string())
        .execute(ctx)
        .await?;
    
    if decrypt_result.exit_code != 0 {
        return Err(OpenSSLError::ExecutionFailed(decrypt_result.stderr.clone()));
    }
    
    // Read plaintext
    let plaintext_bytes = ctx.read_temp_file("plaintext.bin").await?;
    let plaintext = String::from_utf8_lossy(&plaintext_bytes).to_string();
    
    Ok((
        AesDecryptResult {
            plaintext,
            hmac_verified: true,
        },
        vec![hmac_exec, decrypt_result],
    ))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::EXECUTION_TIMEOUT_MS;
    
    #[tokio::test]
    async fn test_aes_keygen() {
        let ctx = ExecutionContext::new(EXECUTION_TIMEOUT_MS).unwrap();
        let (result, _) = aes_keygen(&ctx, Some(256)).await.unwrap();
        
        assert_eq!(result.key_hex.len(), 64); // 256 bits = 64 hex chars
        assert_eq!(result.iv_hex.len(), 32);  // 128 bits = 32 hex chars
        assert_eq!(result.hmac_key_hex.len(), 64);
    }
    
    #[tokio::test]
    async fn test_aes_roundtrip() {
        let ctx = ExecutionContext::new(EXECUTION_TIMEOUT_MS).unwrap();
        
        // Generate keys
        let (keys, _) = aes_keygen(&ctx, Some(256)).await.unwrap();
        
        // Encrypt
        let plaintext = "Hello, AES encryption!";
        let (encrypted, _) = aes_encrypt(
            &ctx,
            plaintext,
            &keys.key_hex,
            Some(&keys.iv_hex),
            &keys.hmac_key_hex,
            None,
        ).await.unwrap();
        
        // Decrypt
        let (decrypted, _) = aes_decrypt(
            &ctx,
            &encrypted.ciphertext_base64,
            &keys.key_hex,
            &encrypted.iv_hex,
            &keys.hmac_key_hex,
            &encrypted.hmac_hex,
            None,
        ).await.unwrap();
        
        assert_eq!(decrypted.plaintext, plaintext);
        assert!(decrypted.hmac_verified);
    }
    
    #[tokio::test]
    async fn test_aes_tampered_hmac() {
        let ctx = ExecutionContext::new(EXECUTION_TIMEOUT_MS).unwrap();
        
        let (keys, _) = aes_keygen(&ctx, Some(256)).await.unwrap();
        
        let (encrypted, _) = aes_encrypt(
            &ctx,
            "secret",
            &keys.key_hex,
            Some(&keys.iv_hex),
            &keys.hmac_key_hex,
            None,
        ).await.unwrap();
        
        // Try to decrypt with wrong HMAC
        let result = aes_decrypt(
            &ctx,
            &encrypted.ciphertext_base64,
            &keys.key_hex,
            &encrypted.iv_hex,
            &keys.hmac_key_hex,
            "0000000000000000000000000000000000000000000000000000000000000000", // Wrong HMAC
            None,
        ).await;
        
        assert!(result.is_err());
        assert!(result.unwrap_err().to_string().contains("HMAC verification failed"));
    }
}
