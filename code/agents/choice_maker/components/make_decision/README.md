# Make Decision (Classifier + Entity Extractor)

This folder hosts the training and inference code for the SecureBERT-based
intent classifier and entity extractor. It expects TOON datasets generated under
`../questions_generator/data/raw`.

## Layout

```
make_decision/
├── artifacts/              # Saved intent/entities checkpoints
├── archives/               # Optional zipped exports
├── requirements.txt        # PyTorch + Transformers stack
├── scripts/
│   ├── train_intent.py     # fine-tune SecureBERT for intent labels
│   ├── train_entities.py   # fine-tune SecureBERT for token tags
│   ├── infer_intent.py     # single-sample classification
│   └── infer_entities.py   # single-sample entity extraction
└── src/
    ├── pipeline/           # data loading + BIO helpers
    └── toon.py             # TOON parser (mirrors generator version)
```

## Installation

```bash
cd make_decision
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Training

Both scripts automatically default to the TOON corpora located at
`../questions_generator/data/raw`.

```bash
# Intent classifier
python3 scripts/train_intent.py \
  --model-name cisco-ai/SecureBERT2.0-base \
  --epochs 3 --batch-size 16

# Entity extractor
python3 scripts/train_entities.py \
  --model-name cisco-ai/SecureBERT2.0-base \
  --epochs 3 --batch-size 8
```

Outputs land in `artifacts/intent` and `artifacts/entities` respectively. Each directory
contains the final Hugging Face checkpoint plus evaluation metrics.

## Inference

Once trained, you can run the lightweight helpers:

```bash
python3 scripts/infer_intent.py \
  --model-dir artifacts/intent \
  --text "Help me decipher this wjfbsit ciphertext"

python3 scripts/infer_entities.py \
  --model-dir artifacts/entities \
  --text "Help me decipher this wjfbsit ciphertext"
```

These scripts load the local checkpoints (no Hugging Face download) and emit the
predicted label/entities with confidence scores.
