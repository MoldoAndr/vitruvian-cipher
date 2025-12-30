# Stage 1: Build YAFU and dependencies
FROM ubuntu:24.04 AS builder

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

WORKDIR /opt/math

COPY junk/gmp-6.3.0.tar.xz .
COPY junk/ecm-7.0.4.tar.gz .

RUN tar -xf gmp-6.3.0.tar.xz \
    && cd gmp-6.3.0 \
    && ./configure --prefix=/opt/math/gmp \
    && make \
    && make install \
    && cd .. \
    && rm -rf gmp-6.3.0 gmp-6.3.0.tar.xz

RUN tar -xf ecm-7.0.4.tar.gz \
    && cd ecm-7.0.4 \
    && autoreconf -i \
    && ./configure --prefix=/opt/math/gmp-ecm --with-gmp=/opt/math/gmp \
    && make \
    && make install \
    && cd .. \
    && rm -rf ecm-7.0.4 ecm-7.0.4.tar.gz

RUN git clone --depth 1 https://github.com/bbuhrow/yafu.git \
    && cd yafu \
    && sed -i 's|../gmp-install/6.2.0-gcc|/opt/math/gmp|g' Makefile.gcc \
    && sed -i 's|../ecm-install/7.0.5-gcc|/opt/math/gmp-ecm|g' Makefile.gcc \
    && make -f Makefile.gcc yafu ECM=1 \
    && cd ..

# Stage 2: Build Go service
FROM golang:1.22-bookworm AS go-builder

WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY main.go ./
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o /out/prime-checker .

# Stage 3: Runtime
FROM ubuntu:24.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -r -u 10001 -g nogroup appuser

WORKDIR /app
RUN mkdir -p /app/data \
    && chown -R appuser:nogroup /app

COPY --from=go-builder /out/prime-checker /app/prime-checker

COPY --from=builder /opt/math/yafu/yafu /usr/local/bin/yafu
COPY --from=builder /opt/math/gmp/lib /opt/math/gmp/lib
COPY --from=builder /opt/math/gmp-ecm/lib /opt/math/gmp-ecm/lib
COPY --from=builder /opt/math/yafu/yafu.ini /opt/math/yafu/
COPY --from=builder /opt/math/yafu/docfile.txt /opt/math/yafu/

ENV LD_LIBRARY_PATH=/opt/math/gmp/lib:/opt/math/gmp-ecm/lib
ENV DB_PATH=/app/data/prime_cache.db

EXPOSE 5000

USER appuser

CMD ["/app/prime-checker"]
