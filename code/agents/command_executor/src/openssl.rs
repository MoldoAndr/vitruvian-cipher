//! OpenSSL command executor
//! Safe subprocess execution with sandboxing

use crate::config::*;
use crate::validators::redact_secret;
use std::env;
use std::path::{Path, PathBuf};
use std::process::Stdio;
use std::time::Duration;
use tempfile::TempDir;
use thiserror::Error;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::process::Command;
use tokio::time::sleep;
use tracing::{debug, error, warn};

#[derive(Error, Debug)]
pub enum OpenSSLError {
    #[error("Command execution timed out after {0}ms")]
    Timeout(u64),
    
    #[error("OpenSSL error: {0}")]
    ExecutionFailed(String),
    
    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),
    
    #[error("Output size exceeded limit of {0} bytes")]
    OutputTooLarge(usize),
    
    #[error("Failed to create temp directory: {0}")]
    TempDirError(String),
    
    #[error("Missing {0} pipe on child process")]
    MissingPipe(&'static str),
}

/// Result of an OpenSSL command execution
#[derive(Debug)]
pub struct ExecutionResult {
    /// stdout output
    pub stdout: Vec<u8>,
    /// stderr output
    pub stderr: String,
    /// Exit code
    pub exit_code: i32,
    /// Command that was executed (for display)
    pub command_display: String,
    /// Command with secrets redacted
    pub command_redacted: String,
}

/// Execution context for a single request
pub struct ExecutionContext {
    /// Temporary directory for this execution
    temp_dir: TempDir,
    /// Timeout for the command
    timeout_ms: u64,
    /// Whether to show secrets in output
    show_secrets: bool,
}

impl ExecutionContext {
    /// Create a new execution context with isolated temp directory
    pub fn new(timeout_ms: u64) -> Result<Self, OpenSSLError> {
        let temp_dir = TempDir::new()
            .map_err(|e| OpenSSLError::TempDirError(e.to_string()))?;
        
        debug!("Created temp directory: {:?}", temp_dir.path());
        
        Ok(Self {
            temp_dir,
            timeout_ms,
            show_secrets: SHOW_SECRETS_IN_COMMAND,
        })
    }
    
    /// Get the temp directory path
    pub fn temp_path(&self) -> &Path {
        self.temp_dir.path()
    }
    
    /// Create a temp file path
    pub fn temp_file(&self, name: &str) -> PathBuf {
        self.temp_dir.path().join(name)
    }
    
    /// Write data to a temp file
    pub async fn write_temp_file(&self, name: &str, data: &[u8]) -> Result<PathBuf, OpenSSLError> {
        let path = self.temp_file(name);
        tokio::fs::write(&path, data).await?;
        Ok(path)
    }
    
    /// Read data from a temp file
    pub async fn read_temp_file(&self, name: &str) -> Result<Vec<u8>, OpenSSLError> {
        let path = self.temp_file(name);
        tokio::fs::read(&path).await.map_err(OpenSSLError::from)
    }
}

/// OpenSSL command builder - prevents shell injection
pub struct OpenSSLCommand {
    /// The binary to execute (openssl or xxd)
    binary: String,
    /// Command arguments
    args: Vec<String>,
    /// Arguments that contain secrets (for redaction)
    secret_indices: Vec<usize>,
    /// Input data (via stdin)
    stdin_data: Option<Vec<u8>>,
}

impl OpenSSLCommand {
    /// Create a new OpenSSL command
    pub fn new() -> Self {
        Self {
            binary: "openssl".to_string(),
            args: Vec::new(),
            secret_indices: Vec::new(),
            stdin_data: None,
        }
    }
    
    /// Create a xxd command
    pub fn xxd() -> Self {
        Self {
            binary: "xxd".to_string(),
            args: Vec::new(),
            secret_indices: Vec::new(),
            stdin_data: None,
        }
    }
    
    /// Add an argument
    pub fn arg<S: Into<String>>(mut self, arg: S) -> Self {
        self.args.push(arg.into());
        self
    }
    
    /// Add a secret argument (will be redacted in display)
    pub fn secret_arg<S: Into<String>>(mut self, arg: S) -> Self {
        self.secret_indices.push(self.args.len());
        self.args.push(arg.into());
        self
    }
    
    /// Set stdin data
    pub fn stdin(mut self, data: Vec<u8>) -> Self {
        self.stdin_data = Some(data);
        self
    }
    
    /// Build display command (with secrets if allowed)
    fn display_command(&self, show_secrets: bool) -> String {
        let mut parts = vec![self.binary.clone()];
        for (i, arg) in self.args.iter().enumerate() {
            if self.secret_indices.contains(&i) && !show_secrets {
                parts.push(redact_secret(arg));
            } else {
                parts.push(arg.clone());
            }
        }
        parts.join(" ")
    }
    
    /// Build redacted command
    fn redacted_command(&self) -> String {
        self.display_command(false)
    }
    
    /// Execute the command
    pub async fn execute(self, ctx: &ExecutionContext) -> Result<ExecutionResult, OpenSSLError> {
        let command_display = self.display_command(ctx.show_secrets);
        let command_redacted = self.redacted_command();
        
        debug!("Executing: {}", command_redacted);
        
        let mut cmd = Command::new(&self.binary);
        cmd.args(&self.args)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .current_dir(ctx.temp_path())
            // Security: don't inherit environment except essentials
            .env_clear()
            .env("PATH", "/usr/bin:/bin:/usr/local/bin")
            .env("HOME", ctx.temp_path());

        if let Ok(modules) = env::var("OPENSSL_MODULES") {
            cmd.env("OPENSSL_MODULES", modules);
        }
        if let Ok(ld_library_path) = env::var("LD_LIBRARY_PATH") {
            cmd.env("LD_LIBRARY_PATH", ld_library_path);
        }
        if let Ok(openssl_conf) = env::var("OPENSSL_CONF") {
            cmd.env("OPENSSL_CONF", openssl_conf);
        }
        
        cmd.kill_on_drop(true);
        let mut child = cmd.spawn()?;
        
        // Write stdin if provided
        if let Some(data) = self.stdin_data {
            if let Some(mut stdin) = child.stdin.take() {
                stdin.write_all(&data).await?;
                drop(stdin);
            }
        }
        
        let mut stdout = child
            .stdout
            .take()
            .ok_or(OpenSSLError::MissingPipe("stdout"))?;
        let mut stderr = child
            .stderr
            .take()
            .ok_or(OpenSSLError::MissingPipe("stderr"))?;

        let stdout_task = tokio::spawn(async move {
            let mut buffer = Vec::new();
            stdout.read_to_end(&mut buffer).await?;
            Ok::<Vec<u8>, std::io::Error>(buffer)
        });

        let stderr_task = tokio::spawn(async move {
            let mut buffer = Vec::new();
            stderr.read_to_end(&mut buffer).await?;
            Ok::<Vec<u8>, std::io::Error>(buffer)
        });

        let status = tokio::select! {
            status = child.wait() => status?,
            _ = sleep(Duration::from_millis(ctx.timeout_ms)) => {
                warn!("Command timed out after {}ms", ctx.timeout_ms);
                let _ = child.kill().await;
                let _ = child.wait().await;
                let _ = stdout_task.await;
                let _ = stderr_task.await;
                return Err(OpenSSLError::Timeout(ctx.timeout_ms));
            }
        };
        
        let stdout = stdout_task
            .await
            .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?
            .map_err(OpenSSLError::from)?;
        let stderr = stderr_task
            .await
            .map_err(|e| OpenSSLError::ExecutionFailed(e.to_string()))?
            .map_err(OpenSSLError::from)?;

        if stdout.len() > MAX_OUTPUT_SIZE || stderr.len() > MAX_OUTPUT_SIZE {
            return Err(OpenSSLError::OutputTooLarge(MAX_OUTPUT_SIZE));
        }

        let stderr = String::from_utf8_lossy(&stderr).to_string();
        let exit_code = status.code().unwrap_or(-1);
        
        if exit_code != 0 {
            error!("OpenSSL command failed: {}", stderr);
        }
        
        Ok(ExecutionResult {
            stdout,
            stderr,
            exit_code,
            command_display,
            command_redacted,
        })
    }
}

impl Default for OpenSSLCommand {
    fn default() -> Self {
        Self::new()
    }
}

/// Get OpenSSL version
pub async fn get_openssl_version() -> Result<String, OpenSSLError> {
    let output = Command::new("openssl")
        .arg("version")
        .output()
        .await?;
    
    let version = String::from_utf8_lossy(&output.stdout).trim().to_string();
    Ok(version)
}

fn with_oqs_providers(cmd: OpenSSLCommand) -> OpenSSLCommand {
    cmd.arg("-provider")
        .arg("oqsprovider")
        .arg("-provider")
        .arg("default")
}

pub async fn list_openssl_providers(ctx: &ExecutionContext) -> Result<Vec<String>, OpenSSLError> {
    let result = with_oqs_providers(OpenSSLCommand::new().arg("list").arg("-providers"))
        .execute(ctx)
        .await?;

    if result.exit_code != 0 {
        return Err(OpenSSLError::ExecutionFailed(result.stderr));
    }

    let output = String::from_utf8_lossy(&result.stdout);
    let mut providers = Vec::new();
    for line in output.lines() {
        if line.starts_with("  ") && !line.starts_with("    ") {
            let name = line.trim();
            if !name.is_empty() && !name.ends_with(':') {
                providers.push(name.to_string());
            }
        }
    }

    Ok(providers)
}

pub async fn list_openssl_signature_algorithms(
    ctx: &ExecutionContext,
) -> Result<Vec<String>, OpenSSLError> {
    let result = with_oqs_providers(
        OpenSSLCommand::new().arg("list").arg("-signature-algorithms"),
    )
    .execute(ctx)
    .await?;

    if result.exit_code != 0 {
        return Err(OpenSSLError::ExecutionFailed(result.stderr));
    }

    let output = String::from_utf8_lossy(&result.stdout);
    let mut algorithms = Vec::new();
    for line in output.lines() {
        if let Some(name) = parse_openssl_list_name(line) {
            algorithms.push(name);
        }
    }

    Ok(algorithms)
}

pub async fn list_openssl_kem_algorithms(
    ctx: &ExecutionContext,
) -> Result<Vec<String>, OpenSSLError> {
    let result =
        with_oqs_providers(OpenSSLCommand::new().arg("list").arg("-kem-algorithms"))
            .execute(ctx)
            .await?;

    if result.exit_code != 0 {
        return Err(OpenSSLError::ExecutionFailed(result.stderr));
    }

    let output = String::from_utf8_lossy(&result.stdout);
    let mut algorithms = Vec::new();
    for line in output.lines() {
        if let Some(name) = parse_openssl_list_name(line) {
            algorithms.push(name);
        }
    }

    Ok(algorithms)
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[tokio::test]
    async fn test_openssl_version() {
        let version = get_openssl_version().await;
        assert!(version.is_ok());
        println!("OpenSSL version: {:?}", version);
    }
    
    #[tokio::test]
    async fn test_command_redaction() {
        let cmd = OpenSSLCommand::new()
            .arg("enc")
            .arg("-aes-256-cbc")
            .arg("-K")
            .secret_arg("0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef");
        
        let redacted = cmd.redacted_command();
        assert!(redacted.contains("0123...cdef"));
        assert!(!redacted.contains("0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"));
    }
}

fn parse_openssl_list_name(line: &str) -> Option<String> {
    let trimmed = line.trim();
    if trimmed.is_empty() || trimmed.ends_with(':') {
        return None;
    }
    let name = trimmed.split('@').next().unwrap_or(trimmed).trim();
    if name.is_empty() || name.starts_with('{') {
        return None;
    }
    Some(name.to_string())
}
