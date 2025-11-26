# Stage 1: Builder
FROM ubuntu:24.04 AS builder

# Install build tools and dependencies, including xz-utils, autoconf, automake, and libtool
RUN apt-get update && apt-get install -y --no-install-recommends \
    g++ \
    make \
    m4 \
    zlib1g-dev \
    git \
    wget \
    ca-certificates \
    xz-utils \
    autoconf \
    automake \
    libtool \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /opt/math

# Copy local GMP and ECM tarballs
COPY gmp-6.3.0.tar.xz .
COPY ecm-7.0.4.tar.gz .

# Install GMP
RUN tar -xf gmp-6.3.0.tar.xz \
    && cd gmp-6.3.0 \
    && ./configure --prefix=/opt/math/gmp \
    && make \
    && make install \
    && cd .. \
    && rm -rf gmp-6.3.0 gmp-6.3.0.tar.xz

# Install GMP-ECM
RUN tar -xf ecm-7.0.4.tar.gz \
    && cd ecm-7.0.4 \
    && autoreconf -i \
    && ./configure --prefix=/opt/math/gmp-ecm --with-gmp=/opt/math/gmp \
    && make \
    && make install \
    && cd .. \
    && rm -rf ecm-7.0.4 ecm-7.0.4.tar.gz

# Install ytools
RUN git clone https://github.com/bbuhrow/ytools.git \
    && cd ytools \
    && make \
    && cd ..

# Install ysieve
RUN git clone https://github.com/bbuhrow/ysieve.git \
    && cd ysieve \
    && sed -i '/^CFLAGS/ s|$| -I/opt/math/gmp/include|' Makefile \
    && sed -i '/^LIBS/ s|$| -L/opt/math/gmp/lib -lgmp|' Makefile \
    && make \
    && cd ..

# Install YAFU
RUN git clone https://github.com/bbuhrow/yafu.git \
    && cd yafu \
    && sed -i '/^CFLAGS/ s|$| -I/opt/math/gmp/include -I/opt/math/gmp-ecm/include|' Makefile \
    && sed -i '/^LIBS/ s|$| -L/opt/math/gmp/lib -L/opt/math/gmp-ecm/lib|' Makefile \
    && make yafu USE_SSE41=1 USE_AVX2=1 USE_BMI2=1 SKYLAKEX=1 ICELAKE=1 \
    && cd ..

# Stage 2: Runtime
FROM ubuntu:24.04

# Install Python and dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create and activate a virtual environment
RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Install Flask in the virtual environment
RUN pip install --no-cache-dir flask
RUN pip install --no-cache-dir requests

# Copy YAFU and dependencies from builder
COPY --from=builder /opt/math/yafu/yafu /usr/local/bin/yafu
COPY --from=builder /opt/math/gmp/lib /opt/math/gmp/lib
COPY --from=builder /opt/math/gmp-ecm/lib /opt/math/gmp-ecm/lib
COPY --from=builder /opt/math/ytools/libytools.a /opt/math/ytools/
COPY --from=builder /opt/math/ysieve/libysieve.a /opt/math/ysieve/
COPY --from=builder /opt/math/yafu/yafu.ini /opt/math/yafu/
COPY --from=builder /opt/math/yafu/docfile.txt /opt/math/yafu/

# Set environment variables
ENV LD_LIBRARY_PATH=/opt/math/gmp/lib:/opt/math/gmp-ecm/lib
ENV PYTHONPATH=/app

# Set working directory for Flask app
WORKDIR /app

# Copy Flask application
COPY app.py .

# Expose Flask port
EXPOSE 5000

# Run Flask server using the virtual environment's Python
CMD ["/app/venv/bin/python3", "app.py"]
