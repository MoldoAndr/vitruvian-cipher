# vitruvian-cipher

An integrated bachelor-thesis platform that combines specialised AI agents, cryptanalysis utilities, password auditing services, and a locally hosted RAG system tailored for modern cryptography workflows.

![Project logo — rotating](logo/logo-rot.gif)

## Highlights
- Modular microservices for cipher identification, password scoring, prime analysis, and educational RAG assistance
- End-to-end orchestration scripts and Docker Compose stacks for repeatable local deployments
- Extensive documentation set: thesis sources, PlantUML diagrams, architectural writeups, and LaTeX templates
- Mock and React front-ends that demonstrate how the services can be combined into a cohesive user experience

## Repository Tour
| Path | Purpose |
| --- | --- |
| `code/agents` | Source for all backend agents (choice maker, cryptosystem detector, hash breaker, password checker, prime checker, theory specialist) |
| `code/interface` | Static mock UI and Vite-based React starter for wiring the agents together |
| `code/k8s` | Placeholder for future Kubernetes manifests |
| `articole` | Romanian-language project outline, citations, and early architecture notes |
| `doc/Documentatie` | LaTeX templates plus presentation and thesis skeletons used for the written deliverables |
| `doc/agents_doc` | PlantUML diagrams for each agent and a helper script to regenerate them |
| `doc/Licenta_doc` | Working directory for the thesis manuscript, slides, and auxiliary outputs |
| `MoldoAndr.github.io` | Static website that mirrors public-facing diagrams and explanations |

## Agents
### Choice Maker (`code/agents/choice_maker`)
- Two subcomponents: `components/questions_generator` (LLM-powered TOON dataset builder) and `components/make_decision` (SecureBERT-based intent and entity fine-tuning).
- Training scripts live under `components/make_decision/scripts`; they default to datasets exported by the generator.
- Quick start:
  ```bash
  cd code/agents/choice_maker/components/make_decision
  python -m venv .venv && source .venv/bin/activate
  pip install -r requirements.txt
  python scripts/train_intent.py --model-name cisco-ai/SecureBERT2.0-base
  ```
- Docker Compose definitions (both `.yml` and `.yaml`) let you spin up the inference API; `code/run_all.sh` will pick up whichever file is present.

### Cryptosystem God (`code/agents/cryptosystem_god`)
- Bundles three services: a CyberChef Magic wrapper, a dcode.fr-inspired heuristic engine, and an aggregator on port 8090.
- Top-level Compose file builds all three containers and exposes them on 18080/18081/18090.
- Standalone aggregator development flow:
  ```bash
  cd code/agents/cryptosystem_god/aggregator
  npm install
  npm run dev
  curl -s http://127.0.0.1:8090/detect -H 'content-type: application/json' -d '{"input":"U0FMVVQ="}'
  ```

### Hash Breaker (`code/agents/hash_breaker`)
- Architectural notes (`architecture.md`, `workflow.md`, `in_depth_workflow.md`) describe a Celery-based cracking pipeline that layers dictionary, rule-based, GAN-generated, and mask attacks.
- Intended runtime stack: Redis for job state, Hashcat/John workers, and PassGAN for candidate generation piped into the cracking tools.
- Use the workflow document as the blueprint for implementing the orchestrator and status API.

### Password Checker (`code/agents/password_checker`)
- Aggregates three FastAPI services: PassStrengthAI (neural network scoring), zxcvbn (heuristic estimator), and HaveIBeenPwned (range API integration).
- Docker Compose file launches all components plus the aggregator that blends their normalised scores.
- Local launch:
  ```bash
  cd code/agents/password_checker
  docker compose up --build
  curl -s http://localhost:9000/score -H 'content-type: application/json' -d '{"password":"P@ssw0rd"}'
  ```
- Each submodule also ships `requirements.txt` for running the service without containers.

### Prime Checker (`code/agents/prime_checker`)
- Flask API around YAFU (Yet Another Factorization Utility) with FactorDB fallback.
- Endpoint summary:
  - `POST /isprime` accepts `{ "number": "..." }`, validates input, runs YAFU `isprime`/`factor`, and augments results with FactorDB when needed.
  - `GET /health` verifies both YAFU and FactorDB availability.
- The Dockerfile provisions YAFU under `/usr/local/bin/yafu`; make sure the binary stays accessible when packaging the service.

### Theory Specialist (`code/agents/theory_specialist`)
- Fully local cryptography-focused RAG system built with FastAPI, APScheduler, and embedded ChromaDB persistence.
- Key features: background document ingestion, ONNX-based embeddings, reranking, conversation history, and Ollama integration for responses.
- Deploy with Docker Compose:
  ```bash
  cd code/agents/theory_specialist
  mkdir -p data documents models
  docker compose up --build -d
  curl http://localhost:8000/health
  ```
- Detailed architecture, schema, and configuration instructions live in `Software_Details.md`.

### Orchestration Helper
- `code/run_all.sh` brings up the password checker, theory specialist, and choice maker stacks (if their Compose files exist), builds & runs the React interface inside Docker, and reminds you to open the mock interface manually.
- All services are expected to listen on localhost ports 9000, 8100, 8081, and 5173 respectively once the script completes.

## Interfaces (`code/interface`)
- `mock/` is a static HTML/JS dashboard that monitors service health, runs password checks, relays questions to the RAG API, ingests documents, and queries the choice maker.
- `react_interface/` contains the Vite starter that can evolve into a production-grade front-end; install dependencies with `npm install` and run `npm run dev` after pointing the services to the correct base URLs.

## Documentation Assets
- `articole/` hosts Romanian-language planning documents, including `Structura_initiala.md`, which describes the problem statement, objectives, and technology stack rationale.
- `doc/Documentatie/` offers reusable LaTeX templates for the thesis (`thesis/`) and presentation (`presentation/`), along with guidance in `README.md`.
- `doc/agents_doc/` provides PlantUML diagrams per agent; run `./doc/agents_doc/generate_diagram.sh` to regenerate PNGs once PlantUML is installed.
- `doc/Licenta_doc/` contains the actual thesis working files (`Licenta.tex`, auxiliary outputs, and intermediate artifacts).
- `MoldoAndr.github.io/` mirrors architectural snapshots for publishing on GitHub Pages.

## Development and Deployment Notes
- **Prerequisites:** Docker 24+, Docker Compose 2.20+, Python 3.11, Node 18+, and optionally Ollama for the RAG stack.
- **Environment management:** the Python services favour `venv`; the JS services rely on npm. GPU acceleration is optional but recommended for PassGAN or SecureBERT fine-tuning.
- **Configuration:** Most services use `.env` files or environment variables (`OLLAMA_URL`, `HIBP_API_KEY`, `ENABLED_COMPONENTS`, etc.). Review each subproject README before deploying to production.
- **Health checks:** Password checker, theory specialist, and choice maker expose `/health`; the mock UI polls these every 30 seconds.

## Working With The Thesis Materials
- Draft the written paper inside `doc/Licenta_doc/`; `make` or `latexmk` can produce PDFs once the LaTeX dependencies are installed.
- Slides and documentation layouts for the defence live in `doc/Documentatie/presentation`.
- Citations and bibliography sources are tracked in `articole/citations.md` and `doc/Documentatie/thesis/bibliography.bib`.

## Suggested Verify Steps
- Run `code/run_all.sh` to confirm the primary agents start, the React Docker container is serving content, and the mock interface is reachable.
- Hit `http://localhost:9000/score` and `http://localhost:8100/health` to validate the password checker and theory specialist stacks.
- Execute `pytest` or targeted unit tests inside each Python subproject once environments are created (no central test runner is provided).

## Next Steps
- 1. Harden docker-compose files with explicit `.env` examples and volume mappings.
- 2. Automate hash_breaker orchestration by turning the conceptual workflow into runnable Celery tasks.
- 3. Connect the React interface to the live APIs and retire the mock HTML once the service contracts stabilise.
