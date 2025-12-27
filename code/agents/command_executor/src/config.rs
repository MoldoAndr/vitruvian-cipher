//! Configuration module for Command Executor
//! Defines limits, allowlists, and runtime settings

use std::collections::HashSet;
use lazy_static::lazy_static;

/// Maximum input size in bytes (1 MB)
pub const MAX_INPUT_SIZE: usize = 1_048_576;

/// Maximum output size in bytes (2 MB)
pub const MAX_OUTPUT_SIZE: usize = 2_097_152;

/// Command execution timeout in milliseconds
pub const EXECUTION_TIMEOUT_MS: u64 = 30_000;

/// RSA key generation timeout (longer due to prime generation)
pub const RSA_KEYGEN_TIMEOUT_MS: u64 = 60_000;

/// Whether to show secrets in command output (default: false for security)
pub const SHOW_SECRETS_IN_COMMAND: bool = false;

/// Server configuration
pub const SERVER_HOST: &str = "0.0.0.0";
pub const SERVER_PORT: u16 = 8085;

lazy_static! {
    /// Allowed hash algorithms
    pub static ref ALLOWED_HASH_ALGOS: HashSet<&'static str> = {
        let mut set = HashSet::new();
        set.insert("sha256");
        set.insert("sha384");
        set.insert("sha512");
        set.insert("sha3-256");
        set.insert("sha3-512");
        set.insert("md5");  // Legacy, with warning
        set.insert("blake2b512");
        set.insert("blake2s256");
        set
    };
    
    /// Allowed symmetric ciphers (v1: CBC mode with HMAC)
    pub static ref ALLOWED_SYMMETRIC_CIPHERS: HashSet<&'static str> = {
        let mut set = HashSet::new();
        // AES-CBC (primary for v1)
        set.insert("aes-128-cbc");
        set.insert("aes-192-cbc");
        set.insert("aes-256-cbc");
        // ChaCha20 (if available)
        set.insert("chacha20");
        // Legacy (with warnings)
        set.insert("des-ede3-cbc");
        set
    };
    
    /// Allowed RSA key sizes
    pub static ref ALLOWED_RSA_BITS: HashSet<u32> = {
        let mut set = HashSet::new();
        set.insert(2048);
        set.insert(3072);
        set.insert(4096);
        set
    };
    
    /// Allowed EC curves
    pub static ref ALLOWED_EC_CURVES: HashSet<&'static str> = {
        let mut set = HashSet::new();
        set.insert("prime256v1");
        set.insert("secp384r1");
        set.insert("secp521r1");
        set
    };

    /// Allowed PQC signature algorithms (oqsprovider)
    pub static ref ALLOWED_PQC_SIG_ALGOS: HashSet<&'static str> = {
        let mut set = HashSet::new();
        // NIST-standardized ML-DSA names (oqsprovider 0.11+)
        set.insert("mldsa44");
        set.insert("mldsa65");
        set.insert("mldsa87");
        // Falcon (optional PQC)
        set.insert("falcon512");
        set.insert("falcon1024");
        set.insert("falconpadded512");
        set.insert("falconpadded1024");
        // Legacy aliases (mapped to ML-DSA/Falcon)
        set.insert("dilithium2");
        set.insert("dilithium3");
        set.insert("dilithium5");
        set.insert("falcon-512");
        set.insert("falcon-1024");
        set
    };

    /// Allowed PQC KEM algorithms (oqsprovider)
    pub static ref ALLOWED_PQC_KEM_ALGOS: HashSet<&'static str> = {
        let mut set = HashSet::new();
        // NIST-standardized ML-KEM names (oqsprovider 0.11+)
        set.insert("mlkem512");
        set.insert("mlkem768");
        set.insert("mlkem1024");
        // Legacy Kyber aliases (mapped to ML-KEM)
        set.insert("kyber512");
        set.insert("kyber768");
        set.insert("kyber1024");
        set
    };
    
    /// All supported operations
    pub static ref SUPPORTED_OPERATIONS: Vec<OperationInfo> = vec![
        // Encoding
        OperationInfo {
            name: "base64_encode",
            category: "encoding",
            description: "Encode data to Base64",
            params: vec!["data"],
        },
        OperationInfo {
            name: "base64_decode",
            category: "encoding",
            description: "Decode Base64 to data",
            params: vec!["encoded"],
        },
        OperationInfo {
            name: "hex_encode",
            category: "encoding",
            description: "Encode data to hexadecimal",
            params: vec!["data"],
        },
        OperationInfo {
            name: "hex_decode",
            category: "encoding",
            description: "Decode hexadecimal to data",
            params: vec!["hex"],
        },
        // Random
        OperationInfo {
            name: "random_bytes",
            category: "random",
            description: "Generate cryptographically secure random bytes",
            params: vec!["length"],
        },
        OperationInfo {
            name: "random_hex",
            category: "random",
            description: "Generate random bytes as hex string",
            params: vec!["length"],
        },
        OperationInfo {
            name: "random_base64",
            category: "random",
            description: "Generate random bytes as Base64",
            params: vec!["length"],
        },
        // Hashing
        OperationInfo {
            name: "hash",
            category: "hashing",
            description: "Compute hash digest of data",
            params: vec!["data", "algorithm"],
        },
        OperationInfo {
            name: "hmac",
            category: "hashing",
            description: "Compute HMAC of data",
            params: vec!["data", "key", "algorithm"],
        },
        // Symmetric encryption
        OperationInfo {
            name: "aes_encrypt",
            category: "symmetric",
            description: "Encrypt data with AES-CBC + HMAC",
            params: vec!["plaintext", "key", "iv", "hmac_key"],
        },
        OperationInfo {
            name: "aes_decrypt",
            category: "symmetric",
            description: "Decrypt AES-CBC data (verifies HMAC first)",
            params: vec!["ciphertext", "key", "iv", "hmac_key", "hmac"],
        },
        OperationInfo {
            name: "aes_keygen",
            category: "symmetric",
            description: "Generate AES key and IV",
            params: vec!["bits"],
        },
        // Asymmetric
        OperationInfo {
            name: "rsa_keygen",
            category: "asymmetric",
            description: "Generate RSA key pair",
            params: vec!["bits"],
        },
        OperationInfo {
            name: "rsa_pubkey",
            category: "asymmetric",
            description: "Extract public key from private key",
            params: vec!["private_key"],
        },
        OperationInfo {
            name: "rsa_sign",
            category: "asymmetric",
            description: "Sign data with RSA private key",
            params: vec!["data", "private_key", "hash_algo"],
        },
        OperationInfo {
            name: "rsa_verify",
            category: "asymmetric",
            description: "Verify RSA signature",
            params: vec!["data", "signature", "public_key", "hash_algo"],
        },
        OperationInfo {
            name: "rsa_encrypt",
            category: "asymmetric",
            description: "Encrypt data with RSA public key (OAEP)",
            params: vec!["plaintext", "public_key"],
        },
        OperationInfo {
            name: "rsa_decrypt",
            category: "asymmetric",
            description: "Decrypt data with RSA private key (OAEP)",
            params: vec!["ciphertext", "private_key"],
        },
        // PQC signatures (oqsprovider)
        OperationInfo {
            name: "pqc_sig_keygen",
            category: "pqc",
            description: "Generate PQC signature key pair (ML-DSA/Falcon)",
            params: vec!["algorithm"],
        },
        OperationInfo {
            name: "pqc_sig_sign",
            category: "pqc",
            description: "Sign data with PQC private key",
            params: vec!["data", "private_key", "algorithm"],
        },
        OperationInfo {
            name: "pqc_sig_verify",
            category: "pqc",
            description: "Verify PQC signature with public key",
            params: vec!["data", "signature", "public_key", "algorithm"],
        },
    ];
}

/// Information about a supported operation
#[derive(Debug, Clone)]
pub struct OperationInfo {
    pub name: &'static str,
    pub category: &'static str,
    pub description: &'static str,
    pub params: Vec<&'static str>,
}

/// Get cipher key length in bytes
pub fn get_cipher_key_length(cipher: &str) -> Option<usize> {
    match cipher {
        "aes-128-cbc" => Some(16),
        "aes-192-cbc" => Some(24),
        "aes-256-cbc" => Some(32),
        "chacha20" => Some(32),
        "des-ede3-cbc" => Some(24),
        _ => None,
    }
}

/// Get cipher IV length in bytes
pub fn get_cipher_iv_length(cipher: &str) -> Option<usize> {
    match cipher {
        "aes-128-cbc" | "aes-192-cbc" | "aes-256-cbc" => Some(16),
        "chacha20" => Some(16),
        "des-ede3-cbc" => Some(8),
        _ => None,
    }
}
