//! Post-Quantum Cryptography provider (oqsprovider)
//! PQC signatures via OpenSSL provider module

use base64::{engine::general_purpose::STANDARD as BASE64, Engine};

use crate::config::MAX_INPUT_SIZE;
use crate::models::{PqcSigKeygenResult, PqcSigSignResult, PqcSigVerifyResult};
use crate::openssl::{ExecutionContext, ExecutionResult, OpenSSLCommand, OpenSSLError};
use crate::validators::{validate_pem, validate_pqc_sig_algo, validate_size};

const DEFAULT_PQC_SIG_ALGO: &str = "mldsa44";

fn with_pqc_provider(cmd: OpenSSLCommand) -> OpenSSLCommand {
    cmd.arg("-provider")
        .arg("oqsprovider")
        .arg("-provider")
        .arg("default")
}

/// Generate PQC signature key pair (ML-DSA/Falcon)
/// Command: openssl genpkey -provider oqsprovider -provider default -algorithm <algo>
pub async fn pqc_sig_keygen(
    ctx: &ExecutionContext,
    algorithm: Option<&str>,
) -> Result<(PqcSigKeygenResult, ExecutionResult), OpenSSLError> {
    let algo = algorithm.unwrap_or(DEFAULT_PQC_SIG_ALGO);
    let validated_algo =
        validate_pqc_sig_algo(algo).map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;

    let priv_path = ctx.temp_file("pqc_private.pem");

    let keygen_result = with_pqc_provider(
        OpenSSLCommand::new()
            .arg("genpkey")
    )
    .arg("-algorithm")
    .arg(validated_algo)
    .arg("-out")
    .arg(priv_path.to_string_lossy().to_string())
    .execute(ctx)
    .await?;

    if keygen_result.exit_code != 0 {
        return Err(OpenSSLError::ExecutionFailed(keygen_result.stderr.clone()));
    }

    let private_key_pem = String::from_utf8_lossy(&ctx.read_temp_file("pqc_private.pem").await?)
        .to_string();

    let pubkey_result = with_pqc_provider(
        OpenSSLCommand::new()
            .arg("pkey")
    )
    .arg("-pubout")
    .arg("-in")
    .arg(priv_path.to_string_lossy().to_string())
    .execute(ctx)
    .await?;

    if pubkey_result.exit_code != 0 {
        return Err(OpenSSLError::ExecutionFailed(pubkey_result.stderr.clone()));
    }

    let public_key_pem = String::from_utf8_lossy(&pubkey_result.stdout).to_string();

    Ok((
        PqcSigKeygenResult {
            private_key_pem,
            public_key_pem,
            algorithm: validated_algo.to_string(),
        },
        keygen_result,
    ))
}

/// Sign data with PQC private key
/// Command: openssl pkeyutl -provider oqsprovider -provider default -sign -inkey priv.pem -in data.bin
pub async fn pqc_sig_sign(
    ctx: &ExecutionContext,
    data: &str,
    private_key_pem: &str,
    algorithm: Option<&str>,
) -> Result<(PqcSigSignResult, ExecutionResult), OpenSSLError> {
    validate_size(data.as_bytes(), MAX_INPUT_SIZE)
        .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;
    validate_pem(private_key_pem)
        .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;

    let algo = if let Some(algo) = algorithm {
        validate_pqc_sig_algo(algo).map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?
    } else {
        "unknown"
    };

    ctx.write_temp_file("data.bin", data.as_bytes()).await?;
    ctx.write_temp_file("pqc_private.pem", private_key_pem.as_bytes()).await?;

    let data_path = ctx.temp_file("data.bin");
    let priv_path = ctx.temp_file("pqc_private.pem");
    let sig_path = ctx.temp_file("pqc_signature.bin");

    let result = with_pqc_provider(
        OpenSSLCommand::new()
            .arg("pkeyutl")
    )
    .arg("-sign")
    .arg("-inkey")
    .arg(priv_path.to_string_lossy().to_string())
    .arg("-rawin")
    .arg("-in")
    .arg(data_path.to_string_lossy().to_string())
    .arg("-out")
    .arg(sig_path.to_string_lossy().to_string())
    .execute(ctx)
    .await?;

    if result.exit_code != 0 {
        return Err(OpenSSLError::ExecutionFailed(result.stderr.clone()));
    }

    let signature_bytes = ctx.read_temp_file("pqc_signature.bin").await?;
    let signature_base64 = BASE64.encode(&signature_bytes);

    Ok((
        PqcSigSignResult {
            signature_base64,
            algorithm: algo.to_string(),
        },
        result,
    ))
}

/// Verify PQC signature with public key
/// Command: openssl pkeyutl -provider oqsprovider -provider default -verify -pubin -inkey pub.pem -sigfile sig.bin -in data.bin
pub async fn pqc_sig_verify(
    ctx: &ExecutionContext,
    data: &str,
    signature_base64: &str,
    public_key_pem: &str,
    algorithm: Option<&str>,
) -> Result<(PqcSigVerifyResult, ExecutionResult), OpenSSLError> {
    validate_size(data.as_bytes(), MAX_INPUT_SIZE)
        .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;
    validate_pem(public_key_pem)
        .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?;

    let algo = if let Some(algo) = algorithm {
        validate_pqc_sig_algo(algo).map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?
    } else {
        "unknown"
    };

    let signature_bytes = BASE64
        .decode(signature_base64)
        .map_err(|e| OpenSSLError::ExecutionFailed(format!("Invalid base64 signature: {}", e)))?;

    ctx.write_temp_file("data.bin", data.as_bytes()).await?;
    ctx.write_temp_file("pqc_public.pem", public_key_pem.as_bytes()).await?;
    ctx.write_temp_file("pqc_signature.bin", &signature_bytes).await?;

    let data_path = ctx.temp_file("data.bin");
    let pub_path = ctx.temp_file("pqc_public.pem");
    let sig_path = ctx.temp_file("pqc_signature.bin");

    let result = with_pqc_provider(
        OpenSSLCommand::new()
            .arg("pkeyutl")
    )
    .arg("-verify")
    .arg("-pubin")
    .arg("-inkey")
    .arg(pub_path.to_string_lossy().to_string())
    .arg("-sigfile")
    .arg(sig_path.to_string_lossy().to_string())
    .arg("-rawin")
    .arg("-in")
    .arg(data_path.to_string_lossy().to_string())
    .execute(ctx)
    .await?;

    let valid = result.exit_code == 0;

    Ok((
        PqcSigVerifyResult {
            valid,
            algorithm: algo.to_string(),
        },
        result,
    ))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::EXECUTION_TIMEOUT_MS;

    fn pqc_tests_enabled() -> bool {
        std::env::var("ENABLE_PQC_TESTS")
            .map(|v| v == "1" || v == "true")
            .unwrap_or(false)
    }

    #[tokio::test]
    async fn test_pqc_keygen_sign_verify() {
        if !pqc_tests_enabled() {
            return;
        }

        let ctx = ExecutionContext::new(EXECUTION_TIMEOUT_MS).unwrap();
        let (keys, _) = pqc_sig_keygen(&ctx, Some("mldsa44")).await.unwrap();

        let data = "Post-quantum signatures";
        let (sig, _) = pqc_sig_sign(&ctx, data, &keys.private_key_pem, Some("mldsa44"))
            .await
            .unwrap();
        let (verify, _) = pqc_sig_verify(
            &ctx,
            data,
            &sig.signature_base64,
            &keys.public_key_pem,
            Some("mldsa44"),
        )
        .await
        .unwrap();

        assert!(verify.valid);
    }
}
