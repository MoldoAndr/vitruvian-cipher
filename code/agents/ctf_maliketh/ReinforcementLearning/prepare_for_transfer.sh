#!/bin/bash
# Script to prepare RL folder for transfer to powerful machine

echo "=== Preparing RL folder for transfer ==="

# Navigate to RL directory
cd /home/andrei/licenta/code/agents/ctf_maliketh/RL

echo "Current size:"
du -sh .

# Remove unnecessary files
echo ""
echo "Cleaning up unnecessary files..."

# Remove PDFs (not needed for training)
rm -f 2506.02048v2.pdf
rm -f Resume.pdf

# Remove venv from Random-Crypto (will recreate on new machine)
rm -rf Random-Crypto/venv

# Remove .git folders (will clone fresh on new machine if needed)
rm -rf HackSynth-GRPO/.git
rm -rf Random-Crypto/.git

# Remove Claude cache
rm -rf Random-Crypto/.claude

# Remove generated_challenges_llm if empty or not needed
rm -rf Random-Crypto/generated_challenges_llm

echo ""
echo "Removed:"
echo "  - PDF files"
echo "  - venv folders"
echo "  - .git folders"
echo "  - Claude cache"
echo "  - Empty challenge folders"

echo ""
echo "Final size:"
du -sh .
du -sh */*

echo ""
echo "=== Folder ready for transfer ==="
echo ""
echo "Total size to transfer:"
du -sh .

# Create a README with setup instructions
cat > TRANSFER_INSTRUCTIONS.md << 'EOF'
# RL Training Setup Instructions

## What's Included:
- **Random-Crypto**: Challenge generator with 991 filtered challenges
- **HackSynth-GRPO**: GRPO training infrastructure

## Files to Note:
- `Random-Crypto/training_challenges/all_challenges_filtered.csv` - 991 valid challenges
- `Random-Crypto/main.py` - Challenge generator
- `HackSynth-GRPO/train_agent.py` - Main training script
- `HackSynth-GRPO/rl_helpers.py` - RL utilities and reward functions

## Setup on New Machine:

### 1. Create Virtual Environment:
```bash
cd HackSynth-GRPO
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install torch transformers accelerate trl peft bitsandbytes unsloth
```

### 2. Download DeepSeek Model:
```bash
python3 -c "
from transformers import AutoModelForCausalLM, AutoTokenizer
model = AutoModelForCausalLM.from_pretrained(
    'deepseek-ai/DeepSeek-R1-Distill-Qwen-7B',
    device_map='auto'
)
print('Model loaded!')
"
```

### 3. Test Training:
```bash
python train_agent.py \
  --model_id deepseek-ai/DeepSeek-R1-Distill-Qwen-7B \
  --data_path ../Random-Crypto/training_challenges/all_challenges_filtered.csv \
  --output_dir ./test_run \
  --difficulties easy
```

### 4. Full Training:
```bash
python train_agent.py \
  --model_id deepseek-ai/DeepSeek-R1-Distill-Qwen-7B \
  --data_path ../Random-Crypto/training_challenges/all_challenges_filtered.csv \
  --output_dir ./checkpoints/deepseek-r1-crypto \
  --difficulties easy medium
```

## Hardware Requirements:
- GPU with at least 16GB VRAM recommended
- 32GB+ system RAM
- ~50GB disk space for model + checkpoints

## Training Details:
- Challenges: 991 crypto CTF challenges
- Model: DeepSeek-R1-Distill-Qwen-7B (8B parameters)
- Method: GRPO (Group Relative Policy Optimization)
- Estimated training time: 2-4 hours on modern GPU
EOF

echo ""
echo "Created TRANSFER_INSTRUCTIONS.md"
echo ""
echo "=== Ready for rsync! ==="
