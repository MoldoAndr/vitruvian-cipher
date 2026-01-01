#!/bin/bash

###############################################################################
# One-Command Setup for Hash Breaker Microservice
#
# This script builds the Docker image with all models and wordlists
# pre-downloaded inside the container. No need to download anything on host!
#
###############################################################################

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Hash Breaker - One-Command Setup                             ║${NC}"
echo -e "${BLUE}║  Everything downloads INSIDE the container                    ║${NC}"
echo -e "${BLUE}║  No NVIDIA packages on your host machine!                    ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker not found. Please install Docker first.${NC}"
    echo "Get Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker Compose not found. Please install Docker Compose first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker found${NC}"
echo ""

###############################################################################
# Build Docker Image (downloads everything during build)
###############################################################################

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Building Docker Image...${NC}"
echo -e "${BLUE}This will download: PagPassGPT model (~500MB) + RockYou wordlist (~150MB)${NC}"
echo -e "${BLUE}Estimated time: 5-10 minutes (depending on your internet)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Build image
if docker compose version &> /dev/null; then
    docker compose build
else
    docker-compose build
fi

echo ""
echo -e "${GREEN}✅ Build complete!${NC}"
echo ""

###############################################################################
# Start Services
###############################################################################

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Starting Services...${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Start services
if docker compose version &> /dev/null; then
    docker compose up -d
else
    docker-compose up -d
fi

echo ""
echo -e "${GREEN}✅ Services started!${NC}"
echo ""

###############################################################################
# Verify Services
###############################################################################

echo "Waiting for services to be ready..."
sleep 10

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Service Status:${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if docker compose version &> /dev/null; then
    docker compose ps
else
    docker-compose ps
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

###############################################################################
# Access Information
###############################################################################

echo "🌐 Access Points:"
echo ""
echo "  API:           http://localhost:8000"
echo "  API Docs:      http://localhost:8000/docs"
echo "  RabbitMQ:      http://localhost:15672 (guest/guest)"
echo "  Prometheus:    http://localhost:9090"
echo ""

###############################################################################
# Test API
###############################################################################

echo "Testing API..."
sleep 5

if curl -s http://localhost:8000/v1/health > /dev/null; then
    echo -e "${GREEN}✅ API is responding!${NC}"
    echo ""
    echo "Try submitting a cracking job:"
    echo ""
    echo "  curl -X POST http://localhost:8000/v1/audit-hash \\"
    echo "    -H 'Content-Type: application/json' \\"
    echo "    -d '{\"hash\": \"5d41402abc4b2a76b9719d911017c592\", \"hash_type_id\": 0, \"timeout_seconds\": 60}'"
    echo ""
else
    echo -e "${YELLOW}⚠️  API not ready yet. Check logs:${NC}"
    echo ""
    echo "  docker compose logs -f api"
    echo ""
fi

###############################################################################
# Done
###############################################################################

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🎉 All done! Your Hash Breaker Microservice is running!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo "Useful commands:"
echo ""
echo "  View logs:          docker compose logs -f"
echo "  View worker logs:   docker compose logs -f worker"
echo "  Stop services:      docker compose down"
echo "  Restart:            docker compose restart"
echo ""
