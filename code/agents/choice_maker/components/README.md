# Choice Maker Toolkit

This repo is now split into two self-contained components:

- `questions_generator/` – prompt specs, CLI, and scripts for producing TOON
  datasets (intent + entities) using LLMs.
- `make_decision/` – SecureBERT-based training + inference pipeline that consumes
  those TOON files to build the final classifier and entity extractor.

See each folder's README for detailed instructions.
