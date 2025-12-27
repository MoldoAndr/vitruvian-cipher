# syntax=docker/dockerfile:1.7
FROM golang:1.22-alpine AS build

WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .

ENV CGO_ENABLED=0
RUN go build -trimpath -ldflags="-s -w" -o /out/orchestrator ./cmd/orchestrator

FROM gcr.io/distroless/static:nonroot
WORKDIR /app
COPY --from=build /out/orchestrator /app/orchestrator
COPY config.yaml /app/config.yaml
EXPOSE 8200
USER nonroot:nonroot
ENTRYPOINT ["/app/orchestrator"]
CMD ["-config", "/app/config.yaml"]
