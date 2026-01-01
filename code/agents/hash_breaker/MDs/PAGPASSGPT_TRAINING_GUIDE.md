# 🎓 PagPassGPT Training Guide

## Overview

This guide explains how to train the **official PagPassGPT model** for your bachelor thesis.

**Important:** The microservice can run WITHOUT a trained model (using fallback generation), but for SOTA performance you should train PagPassGPT.

---

## Quick Decision Tree

```
Need PagPassGPT Model?
├─ YES: Want SOTA performance (12% better than PassGPT)
│  ├─ Have GPU? → Follow Training Guide below
│  └─ No GPU? → Use cloud (Colab, AWS, etc.)
└─ NO: Just testing → Microservice uses fallback generation
```

---

## Option 1: Use Pre-trained Model (Fastest)

**Status:** No official pre-trained models available yet.

**Workaround:** Use fallback generation (already implemented).

---

## Option 2: Train from Scratch (SOTA Performance)

### Prerequisites

1. **GPU:** NVIDIA GPU with 12GB+ VRAM recommended
2. **Dataset:** RockYou password dataset (~150MB)
3. **Time:** 6-24 hours depending on GPU

### Step 1: Prepare Environment

```bash
# Clone official PagPassGPT repo (already in temp_pagpassgpt/)
cd temp_pagpassgpt

# Create conda environment
conda create -n pagpassgpt python=3.8.10
conda activate pagpassgpt

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Prepare Dataset

```bash
# Make sure rockyou.txt is available
# (Already downloaded in hash_breaker root directory)

cd temp_pagpassgpt

# Run preprocessing
sh ./scripts/preprocess.sh
```

This will:
1. Clean RockYou dataset
2. Create pattern files
3. Split train/val/test sets

### Step 3: Train Model

```bash
# Run training script
sh ./scripts/train.sh
```

**Training parameters** (in `scripts/train.sh`):
- Epochs: 10
- Batch size: 256
- Learning rate: 5e-5
- Max sequence length: 32

**Expected time:**
- RTX 3090: ~6 hours
- RTX 4090: ~4 hours
- Colab (K80): ~24 hours

### Step 4: Export Model for Microservice

After training completes:

```bash
# The trained model will be in: temp_pagpassgpt/output/checkpoint-*/

# Copy to microservice models directory
mkdir -p ../models/pagpassgpt
cp -r output/checkpoint-*/* ../models/pagpassgpt/

# Verify
ls ../models/pagpassgpt/
# Should see: config.json, pytorch_model.bin, tokenizer_config.json, etc.
```

---

## Option 3: Use Cloud Training (No Local GPU)

### Google Colab (Free)

1. Upload `temp_pagpassgpt/` to Google Drive
2. Create Colab notebook with GPU
3. Run training commands
4. Download trained model
5. Copy to `models/pagpassgpt/`

### AWS/GCP/Azure

1. Launch GPU instance (p3.2xlarge or similar)
2. Clone PagPassGPT repo
3. Follow training steps
4. Download model when done

---

## Integration with Microservice

### With Trained Model

```bash
# Place trained model in models/pagpassgpt/
docker compose build
docker compose up -d
```

The microservice will automatically:
✅ Detect the model
✅ Load official PagPassGPT
✅ Use SOTA generation
✅ Apply D&C-GEN algorithm

### Without Model (Fallback)

```bash
# Just start the microservice
docker compose up -d
```

The microservice will:
✅ Use rule-based fallback generation
✅ Still function correctly
✅ Just lower hit rate

---

## Verification

### Check if Model is Loaded

```bash
# Check API logs
docker compose logs -f api | grep "PagPassGPT"

# With model: "✅ Official PagPassGPT loaded successfully"
# Without model: "Will use fallback generation method"
```

### Test Generation

```bash
# Submit test job
curl -X POST http://localhost:8000/v1/audit-hash \
  -H 'Content-Type: application/json' \
  -d '{
    "hash": "5d41402abc4b2a76b9719d911017c592",
    "hash_type_id": 0,
    "timeout_seconds": 60
  }'
```

---

## Performance Comparison

| Method | Hit Rate | Duplicate Rate | Speed |
|--------|----------|----------------|-------|
| **PagPassGPT (Trained)** | **23.5%** | **9.28%** | Fast |
| PassGPT | 21% | 34% | Fast |
| Fallback (No Model) | ~5% | Low | Fast |

---

## Troubleshooting

### "Model not found"

```bash
# Check if model files exist
ls -lh models/pagpassgpt/

# Should see:
# config.json
# pytorch_model.bin (or model.safetensors)
# tokenizer_config.json
# vocab.json
```

### "CUDA out of memory"

**Solutions:**
- Use smaller batch size in training
- Use gradient accumulation
- Use smaller model variant

### "Tokenizer import error"

```bash
# Verify vocab.json exists
ls app/ml/pagpassgpt_official/vocab.json

# Should exist (copied from official repo)
```

---

## Resources

- **Paper:** https://www.computer.org/csdl/proceedings-article/dsn/2024/410500a429/1ZPxTMt2ao8
- **Official Repo:** https://github.com/Suxyuuu/PagPassGPT
- **RockYou Dataset:** https://github.com/brannondorsey/naive-hashcat/releases/download/data/rockyou.txt

---

## Thesis Documentation

When writing your thesis, cite:

```bibtex
@inproceedings{pagpassgpt2024,
  title={PagPassGPT: Pattern Guided Password Guessing via Generative Pretrained Transformer},
  booktitle={2024 IEEE/IFIP International Conference on Dependable Systems and Networks (DSN)},
  year={2024},
  organization={IEEE}
}
```

Key points for thesis:
- **State-of-the-art:** PagPassGPT achieves 23.5% hit rate (DSN 2024)
- **D&C-GEN Algorithm:** Reduces duplicates from 34% to 9.28%
- **Pattern-Guided:** Uses PCFG patterns for better generalization
