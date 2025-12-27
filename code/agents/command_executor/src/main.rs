//! Command Executor Agent
//! SOTA Cryptographic operations via OpenSSL backend
//!
//! This service provides secure, sandboxed execution of cryptographic
//! operations using OpenSSL as the backend engine.

mod config;
mod models;
mod validators;
mod openssl;
mod providers;
mod routes;

use std::sync::Arc;
use std::time::Instant;
use tower_http::cors::{Any, CorsLayer};
use tower_http::trace::TraceLayer;
use tracing::{info, Level};
use tracing_subscriber::FmtSubscriber;

use crate::config::{SERVER_HOST, SERVER_PORT};
use crate::openssl::get_openssl_version;
use crate::routes::{create_router, AppState};

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Initialize logging
    FmtSubscriber::builder()
        .with_max_level(Level::INFO)
        .with_target(false)
        .compact()
        .init();
    
    info!("Starting Command Executor Agent v{}", env!("CARGO_PKG_VERSION"));
    
    // Get OpenSSL version
    let openssl_version = get_openssl_version().await.unwrap_or_else(|e| {
        tracing::warn!("Could not get OpenSSL version: {}", e);
        "Unknown".to_string()
    });
    info!("Using {}", openssl_version);
    
    // Create application state
    let state = Arc::new(AppState {
        start_time: Instant::now(),
        openssl_version,
    });
    
    // Create router with middleware
    let app = create_router(state)
        .layer(
            CorsLayer::new()
                .allow_origin(Any)
                .allow_methods(Any)
                .allow_headers(Any),
        )
        .layer(TraceLayer::new_for_http());
    
    // Start server
    let addr = format!("{}:{}", SERVER_HOST, SERVER_PORT);
    let listener = tokio::net::TcpListener::bind(&addr).await?;
    
    info!("🔐 Command Executor listening on http://{}", addr);
    info!("Endpoints:");
    info!("  GET  /health      - Health check");
    info!("  GET  /operations  - List all operations");
    info!("  GET  /ciphers     - List available ciphers/algorithms");
    info!("  POST /execute     - Execute an operation");
    
    axum::serve(listener, app).await?;
    
    Ok(())
}
