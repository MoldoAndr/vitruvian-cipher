#!/bin/bash

###############################################################################
# Hash Breaker Microservice - Download Script
#
# Downloads all required models and wordlists for the Hash Breaker service.
#
# Usage:
#   chmod +x download.sh
#   ./download.sh
#
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_DIR="$(pwd)"
MODELS_DIR="${BASE_DIR}/models"
WORDLISTS_DIR="${BASE_DIR}/wordlists"
RULES_DIR="${BASE_DIR}/rules"

# Progress functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Create directories
create_directories() {
    log_info "Creating directories..."
    mkdir -p "${MODELS_DIR}"
    mkdir -p "${WORDLISTS_DIR}"
    mkdir -p "${RULES_DIR}"
    mkdir -p "${BASE_DIR}/data"
    log_success "Directories created"
}

# Download function with retry
download_file() {
    local url="$1"
    local output="$2"
    local description="$3"

    log_info "Downloading ${description}..."

    if [ -f "${output}" ]; then
        log_warning "${description} already exists at ${output}"
        read -p "Overwrite? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Skipping ${description}"
            return 0
        fi
        rm -f "${output}"
    fi

    # Try curl first, fallback to wget
    if command -v curl &> /dev/null; then
        curl -L "${url}" -o "${output}" --progress-bar
    elif command -v wget &> /dev/null; then
        wget -O "${output}" "${url}" --show-progress
    else
        log_error "Neither curl nor wget found. Please install one."
        exit 1
    fi

    if [ -f "${output}" ]; then
        log_success "${description} downloaded to ${output}"
    else
        log_error "Failed to download ${description}"
        return 1
    fi
}

# Download PagPassGPT model
download_pagpassgpt_model() {
    print_step "STEP 1: Downloading PagPassGPT Model (State-of-the-Art)"

    log_info "Checking Python dependencies..."

    # Check if transformers is installed
    if ! python3 -c "import transformers" 2>/dev/null; then
        log_warning "transformers not found. Installing..."
        pip install transformers torch
    fi

    log_info "Downloading PassGPT model from HuggingFace..."

    python3 << 'EOF'
import sys
try:
    from transformers import GPT2LMHeadModel, RobertaTokenizerFast

    model_path = "./models/pagpassgpt"

    print("Downloading tokenizer...")
    tokenizer = RobertaTokenizerFast.from_pretrained(
        "javirandor/passgpt-10characters",
        max_len=12,
        padding="max_length",
        truncation=True,
        do_lower_case=False
    )

    print("Downloading model...")
    model = GPT2LMHeadModel.from_pretrained("javirandor/passgpt-10characters")

    print("Saving model...")
    tokenizer.save_pretrained(model_path)
    model.save_pretrained(model_path)

    print("✅ Model downloaded successfully!")
    print(f"Model saved to: {model_path}")

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
EOF

    if [ $? -eq 0 ]; then
        log_success "PagPassGPT model downloaded successfully"
    else
        log_error "Failed to download PagPassGPT model"
        return 1
    fi
}

# Download wordlists
download_wordlists() {
    print_step "STEP 2: Downloading Wordlists"

    # RockYou wordlist (32M+ passwords)
    log_info "Downloading RockYou wordlist (32M passwords, ~150MB)..."
    download_file \
        "https://github.com/brannondorsey/PassGAN/releases/download/v1.0/rockyou.txt" \
        "${WORDLISTS_DIR}/rockyou.txt" \
        "RockYou wordlist"

    # Create top100k wordlist
    log_info "Creating top 100k wordlist from RockYou..."
    if [ -f "${WORDLISTS_DIR}/rockyou.txt" ]; then
        head -n 100000 "${WORDLISTS_DIR}/rockyou.txt" > "${WORDLISTS_DIR}/top100k.txt"
        log_success "Created top100k wordlist (100,000 passwords)"
    else
        log_error "rockyou.txt not found. Cannot create top100k"
        return 1
    fi

    # CrackStation wordlist (optional, very large)
    log_info "CrackStation wordlist is optional (1.5GB)."
    read -p "Download CrackStation wordlist? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        download_file \
            "https://download.crackstation.net/crackstation.txt" \
            "${WORDLISTS_DIR}/crackstation.txt" \
            "CrackStation wordlist"
    else
        log_info "Skipping CrackStation wordlist"
    fi
}

# Download hashcat rules
download_rules() {
    print_step "STEP 3: Downloading Hashcat Rules"

    # best64.rule
    download_file \
        "https://github.com/hashcat/hashcat/raw/master/rules/best64.rule" \
        "${RULES_DIR}/best64.rule" \
        "best64.rule (64 most effective rules)"

    # OneRuleToRuleThemAll (optional)
    log_info "Additional rules are optional."
    read -p "Download OneRuleToRuleThemAll? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        download_file \
            "https://github.com/hashcat/hashcat/raw/master/rules/OneRuleToRuleThemAll.rule" \
            "${RULES_DIR}/onerule.rule" \
            "OneRuleToRuleThemAll"
    else
        log_info "Skipping OneRuleToRuleThemAll"
    fi
}

# Verify downloads
verify_downloads() {
    print_step "STEP 4: Verifying Downloads"

    local all_good=true

    # Check model
    if [ -d "${MODELS_DIR}/pagpassgpt" ]; then
        log_success "✅ PagPassGPT model found"
    else
        log_error "❌ PagPassGPT model NOT found"
        all_good=false
    fi

    # Check wordlists
    if [ -f "${WORDLISTS_DIR}/rockyou.txt" ]; then
        local size=$(du -h "${WORDLISTS_DIR}/rockyou.txt" | cut -f1)
        log_success "✅ rockyou.txt (${size})"
    else
        log_error "❌ rockyou.txt NOT found"
        all_good=false
    fi

    if [ -f "${WORDLISTS_DIR}/top100k.txt" ]; then
        local count=$(wc -l < "${WORDLISTS_DIR}/top100k.txt")
        log_success "✅ top100k.txt (${count} passwords)"
    else
        log_error "❌ top100k.txt NOT found"
        all_good=false
    fi

    # Check rules
    if [ -f "${RULES_DIR}/best64.rule" ]; then
        local count=$(wc -l < "${RULES_DIR}/best64.rule")
        log_success "✅ best64.rule (${count} rules)"
    else
        log_error "❌ best64.rule NOT found"
        all_good=false
    fi

    if [ "$all_good" = true ]; then
        print_step "✅ ALL DOWNLOADS VERIFIED SUCCESSFULLY"
        return 0
    else
        print_step "❌ SOME DOWNLOADS ARE MISSING"
        return 1
    fi
}

# Print summary
print_summary() {
    print_step "DOWNLOAD SUMMARY"

    echo ""
    echo "Downloaded files:"
    echo ""
    echo "  Models:"
    echo "    - ${MODELS_DIR}/pagpassgpt/ (PassGPT model)"
    echo ""
    echo "  Wordlists:"
    echo "    - ${WORDLISTS_DIR}/rockyou.txt"
    echo "    - ${WORDLISTS_DIR}/top100k.txt"
    if [ -f "${WORDLISTS_DIR}/crackstation.txt" ]; then
        echo "    - ${WORDLISTS_DIR}/crackstation.txt"
    fi
    echo ""
    echo "  Rules:"
    echo "    - ${RULES_DIR}/best64.rule"
    if [ -f "${RULES_DIR}/onerule.rule" ]; then
        echo "    - ${RULES_DIR}/onerule.rule"
    fi
    echo ""
    echo "Total disk usage:"
    du -sh "${MODELS_DIR}" "${WORDLISTS_DIR}" "${RULES_DIR}" 2>/dev/null | head -3
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo -e "${GREEN}✅ Setup complete! You can now run:${NC}"
    echo ""
    echo "  docker-compose up -d"
    echo ""
    echo "To test the API:"
    echo ""
    echo "  curl http://localhost:8000/v1/health"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

# Main execution
main() {
    echo ""
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  Hash Breaker Microservice - Download Script                  ║${NC}"
    echo -e "${BLUE}║  State-of-the-Art Password Hash Auditing                    ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    # Parse command line arguments
    SKIP_MODEL=false
    SKIP_WORDLISTS=false
    SKIP_RULES=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-model)
                SKIP_MODEL=true
                shift
                ;;
            --skip-wordlists)
                SKIP_WORDLISTS=true
                shift
                ;;
            --skip-rules)
                SKIP_RULES=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --skip-model      Skip downloading PagPassGPT model"
                echo "  --skip-wordlists  Skip downloading wordlists"
                echo "  --skip-rules      Skip downloading rules"
                echo "  --help, -h        Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done

    # Execute download steps
    create_directories

    if [ "$SKIP_MODEL" = false ]; then
        download_pagpassgpt_model
    else
        log_warning "Skipping PagPassGPT model download"
    fi

    if [ "$SKIP_WORDLISTS" = false ]; then
        download_wordlists
    else
        log_warning "Skipping wordlist download"
    fi

    if [ "$SKIP_RULES" = false ]; then
        download_rules
    else
        log_warning "Skipping rules download"
    fi

    # Verify and summarize
    if verify_downloads; then
        print_summary
        exit 0
    else
        log_error "Some downloads failed. Please check the errors above."
        exit 1
    fi
}

# Run main function
main "$@"
