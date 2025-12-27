//! Asymmetric cryptography provider
//! RSA key generation, encryption, signing via OpenSSL

use crate::models::{
    RsaKeygenResult, RsaPubkeyResult, RsaSignResult, RsaVerifyResult,
    RsaEncryptResult, RsaDecryptResult,
};
use crate::openssl::{ExecutionContext, ExecutionResult, OpenSSLCommand, OpenSSLError};
use crate::validators::{validate_rsa_bits, validate_pem, validate_hash_algo, validate_size};
use crate::config::{MAX_INPUT_SIZE, RSA_KEYGEN_TIMEOUT_MS};
use base64::{Engine, engine::general_purpose::STANDARD as BASE64};
use std::path::Path;

const OAEP_HASH_BYTES: usize = 32; // SHA-256

async fn rsa_key_bits_from_pubkey(
    ctx: &ExecutionContext,
    public_key_path: &Path,
) -> Result<usize, OpenSSLError> {
    let result = OpenSSLCommand::new()
        .arg("pkey")
        .arg("-pubin")
        .arg("-in")
        .arg(public_key_path.to_string_lossy().to_string())
        .arg("-text")
        .arg("-noout")
        .execute(ctx)
        .await?;

    if result.exit_code != 0 {
        return Err(OpenSSLError::ExecutionFailed(result.stderr.clone()));
    }

    let output = String::from_utf8_lossy(&result.stdout);
    for line in output.lines() {
        if let (Some(start), Some(end)) = (line.find('('), line.find(" bit")) {
            let bits_str = line[start + 1..end].trim();
            if let Ok(bits) = bits_str.parse::<usize>() {
                return Ok(bits);
            }
        }
    }

    Err(OpenSSLError::ExecutionFailed(
        "Unable to parse RSA key size from OpenSSL output".to_string(),
    ))
}

/// Generate RSA key pair
/// Command: openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:<bits>
pub async fn rsa_keygen(
    ctx: &ExecutionContext,
    bits: u32,
) -> Result<(RsaKeygenResult, ExecutionResult), OpenSSLError> {
    let validated_bits = validate_rsa_bits(bits)
        .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;
    
    // Generate private key
    let priv_key_path = ctx.temp_file("private.pem");
    
    let keygen_result = OpenSSLCommand::new()
        .arg("genpkey")
        .arg("-algorithm")
        .arg("RSA")
        .arg("-pkeyopt")
        .arg(format!("rsa_keygen_bits:{}", validated_bits))
        .arg("-out")
        .arg(priv_key_path.to_string_lossy().to_string())
        .execute(ctx)
        .await?;
    
    if keygen_result.exit_code != 0 {
        return Err(OpenSSLError::ExecutionFailed(keygen_result.stderr.clone()));
    }
    
    // Read private key
    let private_key_pem = String::from_utf8_lossy(
        &ctx.read_temp_file("private.pem").await?
    ).to_string();
    
    // Extract public key
    let pub_key_result = OpenSSLCommand::new()
        .arg("pkey")
        .arg("-pubout")
        .arg("-in")
        .arg(priv_key_path.to_string_lossy().to_string())
        .execute(ctx)
        .await?;
    
    if pub_key_result.exit_code != 0 {
        return Err(OpenSSLError::ExecutionFailed(pub_key_result.stderr.clone()));
    }
    
    let public_key_pem = String::from_utf8_lossy(&pub_key_result.stdout).to_string();
    
    Ok((
        RsaKeygenResult {
            private_key_pem,
            public_key_pem,
            bits: validated_bits,
        },
        keygen_result,
    ))
}

/// Extract public key from private key
/// Command: openssl pkey -pubout -in private.pem
pub async fn rsa_pubkey(
    ctx: &ExecutionContext,
    private_key_pem: &str,
) -> Result<(RsaPubkeyResult, ExecutionResult), OpenSSLError> {
    validate_pem(private_key_pem)
        .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;
    
    // Write private key to temp file
    ctx.write_temp_file("private.pem", private_key_pem.as_bytes()).await?;
    let priv_key_path = ctx.temp_file("private.pem");
    
    let result = OpenSSLCommand::new()
        .arg("pkey")
        .arg("-pubout")
        .arg("-in")
        .arg(priv_key_path.to_string_lossy().to_string())
        .execute(ctx)
        .await?;
    
    if result.exit_code != 0 {
        return Err(OpenSSLError::ExecutionFailed(result.stderr.clone()));
    }
    
    let public_key_pem = String::from_utf8_lossy(&result.stdout).to_string();
    
    Ok((RsaPubkeyResult { public_key_pem }, result))
}

/// Sign data with RSA private key
/// Command: openssl dgst -sha256 -sign private.pem -out sig.bin data.bin
pub async fn rsa_sign(
    ctx: &ExecutionContext,
    data: &str,
    private_key_pem: &str,
    hash_algo: Option<&str>,
) -> Result<(RsaSignResult, ExecutionResult), OpenSSLError> {
    validate_size(data.as_bytes(), MAX_INPUT_SIZE)
        .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;
    validate_pem(private_key_pem)
        .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;
    
    let algo = hash_algo.unwrap_or("sha256");
    let validated_algo = validate_hash_algo(algo)
        .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;
    
    // Write files
    ctx.write_temp_file("data.bin", data.as_bytes()).await?;
    ctx.write_temp_file("private.pem", private_key_pem.as_bytes()).await?;
    
    let data_path = ctx.temp_file("data.bin");
    let priv_key_path = ctx.temp_file("private.pem");
    let sig_path = ctx.temp_file("signature.bin");
    
    let result = OpenSSLCommand::new()
        .arg("dgst")
        .arg(format!("-{}", validated_algo))
        .arg("-sign")
        .arg(priv_key_path.to_string_lossy().to_string())
        .arg("-out")
        .arg(sig_path.to_string_lossy().to_string())
        .arg(data_path.to_string_lossy().to_string())
        .execute(ctx)
        .await?;
    
    if result.exit_code != 0 {
        return Err(OpenSSLError::ExecutionFailed(result.stderr.clone()));
    }
    
    // Read signature and encode as base64
    let signature_bytes = ctx.read_temp_file("signature.bin").await?;
    let signature_base64 = BASE64.encode(&signature_bytes);
    
    Ok((
        RsaSignResult {
            signature_base64,
            algorithm: format!("RSA-{}", validated_algo.to_uppercase()),
        },
        result,
    ))
}

/// Verify RSA signature
/// Command: openssl dgst -sha256 -verify public.pem -signature sig.bin data.bin
pub async fn rsa_verify(
    ctx: &ExecutionContext,
    data: &str,
    signature_base64: &str,
    public_key_pem: &str,
    hash_algo: Option<&str>,
) -> Result<(RsaVerifyResult, ExecutionResult), OpenSSLError> {
    validate_size(data.as_bytes(), MAX_INPUT_SIZE)
        .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;
    validate_pem(public_key_pem)
        .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;
    
    let algo = hash_algo.unwrap_or("sha256");
    let validated_algo = validate_hash_algo(algo)
        .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;
    
    // Decode signature
    let signature_bytes = BASE64.decode(signature_base64)
        .map_err(|e| OpenSSLError::ExecutionFailed(format!("Invalid base64 signature: {}", e)))?;
    
    // Write files
    ctx.write_temp_file("data.bin", data.as_bytes()).await?;
    ctx.write_temp_file("public.pem", public_key_pem.as_bytes()).await?;
    ctx.write_temp_file("signature.bin", &signature_bytes).await?;
    
    let data_path = ctx.temp_file("data.bin");
    let pub_key_path = ctx.temp_file("public.pem");
    let sig_path = ctx.temp_file("signature.bin");
    
    let result = OpenSSLCommand::new()
        .arg("dgst")
        .arg(format!("-{}", validated_algo))
        .arg("-verify")
        .arg(pub_key_path.to_string_lossy().to_string())
        .arg("-signature")
        .arg(sig_path.to_string_lossy().to_string())
        .arg(data_path.to_string_lossy().to_string())
        .execute(ctx)
        .await?;
    
    // OpenSSL returns "Verified OK" on success
    let valid = result.exit_code == 0 && 
                String::from_utf8_lossy(&result.stdout).contains("Verified OK");
    
    Ok((
        RsaVerifyResult {
            valid,
            algorithm: format!("RSA-{}", validated_algo.to_uppercase()),
        },
        result,
    ))
}

/// Encrypt data with RSA public key (OAEP padding)
/// Command: openssl pkeyutl -encrypt -pubin -inkey public.pem -pkeyopt rsa_padding_mode:oaep
pub async fn rsa_encrypt(
    ctx: &ExecutionContext,
    plaintext: &str,
    public_key_pem: &str,
) -> Result<(RsaEncryptResult, ExecutionResult), OpenSSLError> {
    validate_pem(public_key_pem)
        .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;
    
    // Write files
    ctx.write_temp_file("plaintext.bin", plaintext.as_bytes()).await?;
    ctx.write_temp_file("public.pem", public_key_pem.as_bytes()).await?;
    
    let input_path = ctx.temp_file("plaintext.bin");
    let pub_key_path = ctx.temp_file("public.pem");
    let output_path = ctx.temp_file("ciphertext.bin");

    let key_bits = rsa_key_bits_from_pubkey(ctx, &pub_key_path).await?;
    let key_bytes = key_bits / 8;
    let max_plaintext = key_bytes.saturating_sub(2 * OAEP_HASH_BYTES + 2);
    if max_plaintext == 0 {
        return Err(OpenSSLError::ExecutionFailed(
            "RSA key size too small for OAEP-SHA256".to_string(),
        ));
    }

    validate_size(plaintext.as_bytes(), max_plaintext)
        .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;
    
    let result = OpenSSLCommand::new()
        .arg("pkeyutl")
        .arg("-encrypt")
        .arg("-pubin")
        .arg("-inkey")
        .arg(pub_key_path.to_string_lossy().to_string())
        .arg("-pkeyopt")
        .arg("rsa_padding_mode:oaep")
        .arg("-pkeyopt")
        .arg("rsa_oaep_md:sha256")
        .arg("-in")
        .arg(input_path.to_string_lossy().to_string())
        .arg("-out")
        .arg(output_path.to_string_lossy().to_string())
        .execute(ctx)
        .await?;
    
    if result.exit_code != 0 {
        return Err(OpenSSLError::ExecutionFailed(result.stderr.clone()));
    }
    
    // Read ciphertext
    let ciphertext_bytes = ctx.read_temp_file("ciphertext.bin").await?;
    let ciphertext_base64 = BASE64.encode(&ciphertext_bytes);
    
    Ok((RsaEncryptResult { ciphertext_base64 }, result))
}

/// Decrypt data with RSA private key (OAEP padding)
/// Command: openssl pkeyutl -decrypt -inkey private.pem -pkeyopt rsa_padding_mode:oaep
pub async fn rsa_decrypt(
    ctx: &ExecutionContext,
    ciphertext_base64: &str,
    private_key_pem: &str,
) -> Result<(RsaDecryptResult, ExecutionResult), OpenSSLError> {
    validate_pem(private_key_pem)
        .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;
    
    // Decode ciphertext
    let ciphertext_bytes = BASE64.decode(ciphertext_base64)
        .map_err(|e| OpenSSLError::ExecutionFailed(format!("Invalid base64 ciphertext: {}", e)))?;
    
    // Write files
    ctx.write_temp_file("ciphertext.bin", &ciphertext_bytes).await?;
    ctx.write_temp_file("private.pem", private_key_pem.as_bytes()).await?;
    
    let input_path = ctx.temp_file("ciphertext.bin");
    let priv_key_path = ctx.temp_file("private.pem");
    let output_path = ctx.temp_file("plaintext.bin");
    
    let result = OpenSSLCommand::new()
        .arg("pkeyutl")
        .arg("-decrypt")
        .arg("-inkey")
        .arg(priv_key_path.to_string_lossy().to_string())
        .arg("-pkeyopt")
        .arg("rsa_padding_mode:oaep")
        .arg("-pkeyopt")
        .arg("rsa_oaep_md:sha256")
        .arg("-in")
        .arg(input_path.to_string_lossy().to_string())
        .arg("-out")
        .arg(output_path.to_string_lossy().to_string())
        .execute(ctx)
        .await?;
    
    if result.exit_code != 0 {
        return Err(OpenSSLError::ExecutionFailed(result.stderr.clone()));
    }
    
    // Read plaintext
    let plaintext_bytes = ctx.read_temp_file("plaintext.bin").await?;
    let plaintext = String::from_utf8_lossy(&plaintext_bytes).to_string();
    
    Ok((RsaDecryptResult { plaintext }, result))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::EXECUTION_TIMEOUT_MS;
    
    #[tokio::test]
    async fn test_rsa_keygen() {
        let ctx = ExecutionContext::new(RSA_KEYGEN_TIMEOUT_MS).unwrap();
        let (result, _) = rsa_keygen(&ctx, 2048).await.unwrap();
        
        assert!(result.private_key_pem.contains("BEGIN PRIVATE KEY"));
        assert!(result.public_key_pem.contains("BEGIN PUBLIC KEY"));
        assert_eq!(result.bits, 2048);
    }
    
    #[tokio::test]
    async fn test_rsa_sign_verify() {
        let ctx = ExecutionContext::new(RSA_KEYGEN_TIMEOUT_MS).unwrap();
        
        // Generate keys
        let (keys, _) = rsa_keygen(&ctx, 2048).await.unwrap();
        
        // Sign
        let data = "Hello, RSA signatures!";
        let (sig_result, _) = rsa_sign(&ctx, data, &keys.private_key_pem, None).await.unwrap();
        
        // Verify
        let (verify_result, _) = rsa_verify(
            &ctx,
            data,
            &sig_result.signature_base64,
            &keys.public_key_pem,
            None,
        ).await.unwrap();
        
        assert!(verify_result.valid);
    }
    
    #[tokio::test]
    async fn test_rsa_sign_verify_tampered() {
        let ctx = ExecutionContext::new(RSA_KEYGEN_TIMEOUT_MS).unwrap();
        
        let (keys, _) = rsa_keygen(&ctx, 2048).await.unwrap();
        let (sig_result, _) = rsa_sign(&ctx, "original", &keys.private_key_pem, None).await.unwrap();
        
        // Verify with different data (should fail)
        let (verify_result, _) = rsa_verify(
            &ctx,
            "tampered",
            &sig_result.signature_base64,
            &keys.public_key_pem,
            None,
        ).await.unwrap();
        
        assert!(!verify_result.valid);
    }
    
    #[tokio::test]
    async fn test_rsa_encrypt_decrypt() {
        let ctx = ExecutionContext::new(RSA_KEYGEN_TIMEOUT_MS).unwrap();
        
        let (keys, _) = rsa_keygen(&ctx, 2048).await.unwrap();
        let plaintext = "Secret message for RSA";
        
        // Encrypt
        let (enc_result, _) = rsa_encrypt(&ctx, plaintext, &keys.public_key_pem).await.unwrap();
        
        // Decrypt
        let (dec_result, _) = rsa_decrypt(
            &ctx,
            &enc_result.ciphertext_base64,
            &keys.private_key_pem,
        ).await.unwrap();
        
        assert_eq!(dec_result.plaintext, plaintext);
    }
    
    #[tokio::test]
    async fn test_invalid_key_size() {
        let ctx = ExecutionContext::new(EXECUTION_TIMEOUT_MS).unwrap();
        let result = rsa_keygen(&ctx, 1024).await;
        
        assert!(result.is_err());
    }
}
