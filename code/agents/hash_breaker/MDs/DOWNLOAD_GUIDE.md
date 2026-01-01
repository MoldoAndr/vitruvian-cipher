# 📥 Download Script Usage Guide

## Quick Start

```bash
# Make executable (if not already)
chmod +x download.sh

# Run download script (downloads everything)
./download.sh
```

## What It Downloads

### 1. PagPassGPT Model (~500MB)
- PassGPT-10character model from HuggingFace
- Saves to `models/pagpassgpt/`
- Used for Phase 3 (AI generation)

### 2. Wordlists
- **RockYou** (150MB) - 32M+ passwords
- **Top 100k** (1MB) - Extracted from RockYou
- **CrackStation** (optional, 1.5GB) - 1.5B passwords

### 3. Hashcat Rules
- **best64.rule** - 64 most effective mutation rules
- **OneRuleToRuleThemAll** (optional) - Comprehensive rule set

## Options

```bash
# Skip model (if you already have it)
./download.sh --skip-model

# Skip wordlists (if you already have them)
./download.sh --skip-wordlists

# Skip rules (if you already have them)
./download.sh --skip-rules

# Show help
./download.sh --help
```

## After Download

Verify everything is downloaded:

```bash
./download.sh  # Will verify existing files
```

Then start the service:

```bash
docker-compose up -d
```

## Troubleshooting

### "transformers not found"
```bash
pip install transformers torch
```

### "Permission denied"
```bash
chmod +x download.sh
```

### "Download failed"
- Check internet connection
- Try again (script supports resuming)
- Some URLs might be rate-limited, wait a few minutes

## File Sizes After Download

```
models/
└── pagpassgpt/     ~500 MB

wordlists/
├── rockyou.txt      ~150 MB
├── top100k.txt      ~1 MB
└── crackstation.txt ~1.5 GB (optional)

rules/
├── best64.rule      ~2 KB
└── onerule.rule     ~100 KB (optional)
```

**Total**: ~650 MB (without CrackStation: ~2 GB)
