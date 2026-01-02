# core_idea.md — “Make Random-Crypto Better” (Benchmark + Agent + RL)

## What this repo is
This folder is a **research-engineering fork/workspace** around **Random-Crypto** (MIT). The goal is not “just run their code”, but to **upgrade it into a thesis-grade benchmark + training stack**: cleaner task generation, stronger evaluation, safer tooling, and more reliable RL fine-tuning.

**North Star:** a third party can clone this repo, run 3 commands (build → eval → train), and reproduce the same scores.

---

## What “BETTER” means (concrete targets)

### 1) Benchmark quality upgrades (Random-Crypto side)
- **Determinism everywhere:** strict seed control for task generation + split generation.
- **Canonical task schema:** every generated task saved as JSON with:
  - `task_id`, `subtype`, `difficulty`, `seed`, `prompt`, `attachments` (if any),
  - `validator` metadata (how to check an answer),
  - `generation_trace` (optional debug info).
- **Difficulty calibration:** each subtype supports multiple difficulty tiers (and we document what changes).
- **Validation reliability:** validators must be:
  - deterministic,
  - strict (no false positives),
  - transparent (return reason for failure).
- **Coverage expansion (optional but ideal):** add subtypes or improve existing ones without breaking backwards compatibility.

### 2) Evaluation quality upgrades (this repo side)
- **Metrics:** Pass@1, Pass@8, Maj@8 per subtype + global, and **seen/unseen** splits.
- **Reproducible sampling:** same prompts + same decoding params → same results.
- **Fast evaluation:** parallel execution, caching of model outputs, structured logs.
- **Failure mode audit:** automatically tag failures into buckets:
  - wrong crypto reasoning,
  - tool misuse,
  - hallucinated tool output,
  - format violations,
  - timeout/OOM.

### 3) Tool-using agent runtime upgrades
- A strict tool protocol: model may only access computation via a tool call (Python sandbox).
- **Tool honesty enforcement:** the runtime must detect and penalize:
  - “fake tool output” (model prints results without a tool call),
  - “fake flag” (flag-looking answers that fail validation).
- **Safe sandbox:** time/memory/cpu limits, no network, isolated FS, full logging.

### 4) RL training upgrades (GRPO-style)
- Provide a clean GRPO loop (or equivalent) that:
  - samples `k` trajectories per task,
  - computes rewards (correctness + honesty + formatting + efficiency),
  - updates via LoRA/QLoRA,
  - logs learning curves and checkpoint evals.
- Goal: **RL model > strong prompted tool baseline** on **unseen** tasks (not just memorization).

---

## What we will modify (MIT license note)
Random-Crypto is MIT, so we can:
- **fork and modify it directly**, and/or
- keep it as a submodule and apply patches.

**Rule:** preserve license headers and keep the MIT license file intact; document major modifications in `CHANGELOG.md` / `docs/`.

---

## Repo philosophy (how we prevent chaos)
1) **Single source of truth = dataset artifacts** (`.jsonl` / `.json` tasks).  
   If a run can’t be reproduced from saved artifacts, it didn’t happen.
2) **No silent magic:** configs are explicit YAML; all runs log config + commit hash + seeds.
3) **Benchmark stability > feature fireworks:** every new subtype/difficulty must ship with tests + validator.
4) **Security mindset:** treat the model as untrusted input (sandbox everything).

---

## Deliverables (thesis-grade)
### A) Engineering deliverables
- CLI commands:
  - `build_dataset` → generates tasks + splits
  - `eval` → runs Pass@k/Maj@k on a model checkpoint
  - `train_grpo` → trains and logs RL runs
- `results/` structure with:
  - per-run configs,
  - per-task outputs,
  - aggregated tables/plots.

### B) Research deliverables
- A clear ablation grid:
  1) no tools
  2) tools (prompt only)
  3) tools + RL (GRPO)
  4) reward variants (honesty on/off, efficiency on/off)
- Plots:
  - learning curve (reward + Pass@1/8 over time),
  - subtype breakdown bars,
  - seen vs unseen comparison.

---

## Minimum viable milestones (do these in order)

### Milestone 1 — “Benchmark is clean”
- Lock deterministic generation.
- Export tasks to a stable JSONL schema.
- Validators are correct, tested, and fast.

**Acceptance:** two runs with same seed produce identical task hashes.

### Milestone 2 — “Evaluation is trustworthy”
- Implement Pass@k + Maj@k.
- Implement seen/unseen splits.
- Add a baseline model run and produce a table.

**Acceptance:** evaluation produces a single `metrics.json` + `report.md` per run.

### Milestone 3 — “Tooling is safe + honest”
- Implement Python sandbox with hard limits and full logs.
- Implement tool call schema + strict parsing.
- Detect hallucinated tool output / fabricated flags.

**Acceptance:** sandbox survives adversarial code and never stalls the runner.

### Milestone 4 — “RL actually improves generalization”
- GRPO loop + LoRA/QLoRA.
- Reward = correctness + honesty (start simple).
- Train on easy/mid tier first, then expand.

**Acceptance:** RL > tool-prompt baseline on unseen tasks (Pass@8).

---

## Non-goals (to keep the thesis sane)
- Not building a general CTF autopwn framework.
- Not using web access or external solvers during evaluation.
- Not chasing maximal SOTA; chasing **clean evidence** and **reproducibility**.

---

## Implementation standards (non-negotiable)
- Every command writes:
  - `config.yaml`, `git_commit.txt`, `seeds.json`, `env.txt`
  - raw generations + tool logs per sample
  - aggregated metrics JSON
- Testing:
  - unit tests for validators and generation determinism,
  - integration test: generate 50 tasks → eval baseline → ensure pipeline completes.
- Code quality:
  - type hints, structured logging, predictable errors.

---

## How to work with Codex / Claude Code (instructions)
When implementing changes:
1) Start with the smallest vertical slice that runs end-to-end (build → eval).
2) Add instrumentation before optimizing.
3) Never change task formats without versioning the schema.
4) Every improvement must come with:
   - a test,
   - a short rationale in `docs/`,
   - and a measurable effect (speed, stability, score, coverage).

---

## Final thesis claim (what I’m proving)
A procedurally generated crypto benchmark can be made **more reliable and more scientific** (deterministic generation + strict validators + robust evaluation), and a tool-using agent trained with GRPO-style RL can **improve generalization** while reducing cheating behaviors (fake tool outputs / fake flags) under a hardened sandboxed runtime.

