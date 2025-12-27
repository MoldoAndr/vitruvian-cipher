# ============================================================================
# Command Executor - Multi-stage Dockerfile
# SOTA Cryptographic operations via OpenSSL backend
# ============================================================================

# Stage 1: Build liboqs + oqsprovider (PQC)
FROM debian:bookworm-slim AS oqs-builder

ARG LIBOQS_VERSION=0.15.0
ARG OQSPROVIDER_VERSION=0.11.0

RUN apt-get update && apt-get install -y \
    git \
    cmake \
    ninja-build \
    build-essential \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt

RUN git clone --depth 1 --branch ${LIBOQS_VERSION} https://github.com/open-quantum-safe/liboqs.git
RUN cmake -S liboqs -B liboqs/build -GNinja \
      -DCMAKE_INSTALL_PREFIX=/opt/oqs \
      -DBUILD_SHARED_LIBS=ON \
      -DOQS_USE_OPENSSL=ON \
      -DOQS_BUILD_ONLY_LIB=ON \
    && cmake --build liboqs/build \
    && cmake --install liboqs/build

RUN git clone --depth 1 --branch ${OQSPROVIDER_VERSION} https://github.com/open-quantum-safe/oqs-provider.git
RUN cmake -S oqs-provider -B oqs-provider/build -GNinja \
      -DCMAKE_INSTALL_PREFIX=/opt/oqs \
      -DCMAKE_PREFIX_PATH=/opt/oqs \
      -DOPENSSL_ROOT_DIR=/usr \
      -DOQS_PROVIDER_BUILD_TESTS=OFF \
    && cmake --build oqs-provider/build \
    && cmake --install oqs-provider/build \
    && install -d /opt/oqs/lib/ossl-modules \
    && find oqs-provider/build -name "oqsprovider.so" -exec cp {} /opt/oqs/lib/ossl-modules/ \;

# Stage 2: Builder
FROM rust:1.80-slim-bookworm AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy manifests first for dependency caching
COPY Cargo.toml Cargo.lock* ./

# Create dummy source for dependency compilation
RUN mkdir -p src && \
    echo 'fn main() { println!("dummy"); }' > src/main.rs

# Build dependencies only (cached layer)
RUN cargo build --release && rm -rf src target/release/deps/command*

# Copy actual source code
COPY src ./src

# Build the actual application
RUN cargo build --release

# ============================================================================
# Stage 3: Runtime
# ============================================================================
FROM debian:bookworm-slim AS runtime

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    # OpenSSL 3.x
    openssl \
    libssl3 \
    # xxd for hex encoding (part of vim-common)
    xxd \
    # curl for healthcheck
    curl \
    # CA certificates for any HTTPS operations
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN useradd -r -s /bin/false -u 1000 executor

# Create necessary directories
RUN mkdir -p /app /tmp/executor && \
    chown -R executor:executor /app /tmp/executor

WORKDIR /app

# Copy oqsprovider + liboqs
COPY --from=oqs-builder /opt/oqs /opt/oqs

# Ensure provider is also visible in the default OpenSSL module path
RUN mkdir -p /usr/lib/x86_64-linux-gnu/ossl-modules && \
    if [ -f /opt/oqs/lib/ossl-modules/oqsprovider.so ]; then \
      cp /opt/oqs/lib/ossl-modules/oqsprovider.so /usr/lib/x86_64-linux-gnu/ossl-modules/; \
    fi

# Copy the binary from builder
COPY --from=builder /app/target/release/command-executor /app/command-executor

# Set ownership
RUN chown executor:executor /app/command-executor

# Switch to non-root user
USER executor

# Environment variables
ENV RUST_LOG=info
ENV TMPDIR=/tmp/executor
ENV OPENSSL_MODULES=/opt/oqs/lib/ossl-modules
ENV LD_LIBRARY_PATH=/opt/oqs/lib

# Expose port
EXPOSE 8085

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8085/health || exit 1

# Run the application
CMD ["/app/command-executor"]
