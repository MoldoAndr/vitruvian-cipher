#!/usr/bin/env bash
# Quick verification that all configurations are valid

echo "========================================="
echo "Vitruvian Platform - Configuration Check"
echo "========================================="
echo ""

# 1. Check docker-compose.yml
echo "1. Validating docker-compose.yml..."
if docker compose -f docker-compose.yml config > /dev/null 2>&1; then
    echo "   ✓ docker-compose.yml is valid"
else
    echo "   ✗ docker-compose.yml has errors"
    docker compose -f docker-compose.yml config 2>&1 | head -5
    exit 1
fi

# 2. List active services
echo ""
echo "2. Active services:"
docker compose -f docker-compose.yml config --services 2>/dev/null | sed 's/^/   - /'

# 3. Check scripts are executable
echo ""
echo "3. Checking script permissions..."
for script in scripts/*.sh run_all.sh; do
    if [ -x "$script" ]; then
        echo "   ✓ $script"
    else
        echo "   ⚠ $script (not executable)"
    fi
done

# 4. Verify Makefile
echo ""
echo "4. Checking Makefile..."
if [ -f Makefile ]; then
    echo "   ✓ Makefile exists"
    echo "   Available targets:"
    make help 2>&1 | grep -E "^\s+\w+:" | head -10 | sed 's/^/     /'
else
    echo "   ✗ Makefile not found"
fi

# 5. Check .env
echo ""
echo "5. Environment configuration:"
if [ -f .env ]; then
    echo "   ✓ .env exists"
else
    if [ -f .env.example ]; then
        echo "   ⚠ .env not found (but .env.example exists)"
        echo "     Run: cp .env.example .env"
    else
        echo "   ⚠ Neither .env nor .env.example found"
    fi
fi

echo ""
echo "========================================="
echo "Configuration check complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Run: ./run_all.sh build"
echo "  2. Run: ./run_all.sh start"
echo "  3. Run: ./run_all.sh health"
