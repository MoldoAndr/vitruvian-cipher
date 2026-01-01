# 🚀 One-Command Setup Guide

## ⚡ Super Simple Setup

**No downloads on your host machine! Everything happens inside the Docker container.**

---

## Quick Start (Single Command)

```bash
chmod +x setup.sh
./setup.sh
```

That's it! The script will:
1. ✅ Build Docker image (downloads PagPassGPT model + RockYou wordlist inside container)
2. ✅ Start all services (API, Worker, RabbitMQ, Redis)
3. ✅ Verify everything is working

---

## What Gets Downloaded (Inside Container)

| Component | Size | Source |
|-----------|------|--------|
| **PagPassGPT Model** | ~500 MB | HuggingFace (javirandor/passgpt-10characters) |
| **RockYou Wordlist** | ~150 MB | GitHub (PassGAN releases) |
| **Top 100K** | ~1 MB | Extracted from RockYou |
| **best64.rule** | ~2 KB | GitHub (hashcat) |

**Total**: ~650 MB downloaded **inside container during build**

---

## Architecture

```
Your Host Machine
  └─ No NVIDIA packages!
  └─ No PyTorch!
  └─ No transformers!
  └─ Just Docker 🐳

Docker Container
  ├─ Python 3.10
  ├─ PyTorch + transformers
  ├─ PagPassGPT model (pre-downloaded)
  ├─ RockYou wordlist (pre-downloaded)
  ├─ Hashcat
  └─ Your code
```

---

## How It Works

### Dockerfile Magic

```dockerfile
# Download model during BUILD
RUN python3 << 'EOF'
from transformers import GPT2LMHeadModel, RobertaTokenizerFast

tokenizer = RobertaTokenizerFast.from_pretrained("javirandor/passgpt-10characters")
model = GPT2LMHeadModel.from_pretrained("javirandor/passgpt-10characters")

tokenizer.save_pretrained("/app/models/pagpassgpt")
model.save_pretrained("/app/models/pagpassgpt")
EOF
```

**Benefits**:
- ✅ Downloads happen during `docker build`
- ✅ Cached in Docker image layer
- ✅ No host machine pollution
- ✅ Reproducible builds

---

## Commands

### Initial Setup (First Time)

```bash
./setup.sh
```

### Rebuild (If Code Changed)

```bash
docker compose build
docker compose up -d
```

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f worker
docker compose logs -f api
```

### Stop Services

```bash
docker compose down
```

### Clean Restart

```bash
docker compose down
docker compose up -d --build
```

---

## Troubleshooting

### "Build takes forever"
- Normal first time (downloading 650MB)
- Subsequent builds are instant (Docker cache)

### "Out of space"
```bash
docker system prune -a  # Clean Docker cache
```

### "GPU not detected"
```bash
# Install NVIDIA Container Toolkit
# See: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html
```

---

## What's on My Host Machine?

After setup, your host machine has:

```
hash_breaker/
├── app/              # Your code
├── Dockerfile        # Build instructions
├── docker-compose.yml # Orchestration
└── setup.sh          # Setup script
```

**NOT on your host machine:**
- ❌ No PyTorch
- ❌ No transformers
- ❌ No NVIDIA CUDA packages
- ❌ No models (500 MB)
- ❌ No wordlists (150 MB)

**Everything is inside the container!** 🎉

---

## Verification

### Check What's Inside Container

```bash
# Enter container
docker compose exec worker bash

# Check model
ls -lh /app/models/pagpassgpt/

# Check wordlists
ls -lh /app/wordlists/

# Test Python imports
python3 -c "from transformers import GPT2LMHeadModel; print('✅ OK')"

# Exit container
exit
```

---

## Advantages

1. **Clean Host Machine** - No AI/ML packages needed
2. **Portable** - Same image works everywhere
3. **Reproducible** - Docker layer caching
4. **Isolated** - No dependency conflicts
5. **Easy Cleanup** - `docker compose down`

---

**Bottom Line**: You only need Docker. Nothing else! 🐳
