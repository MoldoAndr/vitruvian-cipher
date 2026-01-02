
Cuprins

Glosar
1. Introducere
   1.1 Scopul documentului
   1.2 Domeniul de aplicare
   1.3 Definiții, acronime și abrevieri
   1.4 Referințe
   1.5 Prezentare generală a documentului
2. Descrierea generală
   2.1 Perspectiva produsului
   2.2 Funcționalități ale produsului
   2.3 Caracteristici ale utilizatorului
   2.4 Constrângeri generale
   2.5 Mediul de operare
3. Caracteristici de Sistem si Cerinte Functionale
   3.1 Managementul Agenților AI
   3.2 Password Intelligence Suite
   3.3 Prime Factorization Engine
   3.4 Theory Specialist RAG System
   3.5 Command Executor (Rust)
   3.6 Choice Maker (NLP Engine)
   3.7 Orchestrator
   3.8 Authentication & Authorization
   3.9 Hash Breaking Agent (Planificat)
   3.10 Cryptosystem Detection (Planificat)
4. Cerințe Non-Funcționale
   4.1 Performanță
   4.2 Securitate
   4.3 Disponibilitate & Fiabilitate
   4.4 Scalabilitate
   4.5 Observabilitate
   4.6 Mentenanabilitate
5. Quality of Service (QoS)
6. Cerințe AI/ML Specifice
   6.1 Model Specification
   6.2 Data Management
   6.3 Guardrails
   6.4 Ethics
   6.5 Model Lifecycle
7. Compliance
   7.1 GDPR
   7.2 NIST SP 800-53
   7.3 FIPS 140-2
   7.4 NATO STANAG (dacă aplicabil)
8. Design & Implementation Constraints
   8.1 Installation
   8.2 Build & Delivery (CI/CD)
   8.3 Distribution (Kubernetes)
   8.4 Maintainability
   8.5 Portability
   8.6 Cost
9. Verification & Validation
10. Anexe
    10.1 Architecture Diagrams
    10.2 API Contracts (OpenAPI)
    10.3 Data Model
    10.4 K8s Manifests
    10.5 CI/CD Pipelines

---

# 📋 DETALII CERINȚE

## CERINȚE FUNCȚIONALE DETALIATE (FR-XXX)

### 1. Managementul Agenților AI
- **FR-001**: Sistemul TREBUIE să suporte execuția a minimum 5 agenți AI specializați (Password, Theory, Prime, Command, Choice)
- **FR-002**: Sistemul TREBUIE să permită adăugarea de noi agenți fără modificarea codului orchestratorului (plugin architecture)
- **FR-003**: Sistemul TREBUIE să execute agenți în paralel pentru operațiuni independente (concurrency support)
- **FR-004**: Sistemul TREBUIE să detecteze și redeștepte agenții căzuți (auto-healing)
- **FR-005**: Sistemul TREBUIE să implementeze health-check pentru fiecare agent la interval de 30 secunde
- **FR-006**: Sistemul TREBUIE să mențină un pool de agenți cu dimensiune configurabilă (scaling)
- **FR-007**: Sistemul TREBUIE să logheze toate interacțiunile inter-agent pentru debugging

### 2. Password Intelligence Suite
- **FR-008**: Sistemul TREBUIE să analizeze parolele folosind minimum 3 modele ML: PassGPT (neural LM), PassStrengthAI (CNN), zxcvbn (heuristic)
- **FR-009**: Sistemul TREBUIE să verifice parolele în baza de date HaveIBeenPwned (12B+ credențiale compromise)
- **FR-010**: Sistemul TREBUIE să genereze un scor unic de securitate (0-100) din agregarea modelelor (weighted ensemble)
- **FR-011**: Sistemul TREBUIE să ofere recomandări contextuale de îmbunătățire bazate pe ML-driven pattern analysis
- **FR-012**: Sistemul TREBUIE să returneze toate scorurile individuale pentru transparență
- **FR-013**: Sistemul TREBUIE să suporte verificare în batch pentru până la 1000 parole
- **FR-014**: Sistemul AR TREBUI să includă istoricul verificărilor per utilizator

### 3. Prime Factorization Engine
- **FR-015**: Sistemul TREBUIE să determine primalitatea numerelor mari până la 512 biți folosind YAFU
- **FR-016**: Sistemul TREBUIE să factorizeze numere compuse folosind algoritmi optimizați (Pollard Rho, ECM, SIQS)
- **FR-017**: Sistemul TREBUIE să folosească FactorDB API ca fallback pentru numere foarte mari
- **FR-018**: Sistemul TREBUIE să cache-uie rezultatele factorizării în SQLite local
- **FR-019**: Sistemul TREBUIE să permită configurarea timeout-urilor per operație (default: 8s factorization, 5s primality)
- **FR-020**: Sistemul TREBUIE să extragă numere din text natural (semantic number recognition)
- **FR-021**: Sistemul TREBUIE să execute factorizarea concurentă cu semaphore-based resource management

### 4. Theory Specialist RAG System
- **FR-022**: Sistemul TREBUIE să indexeze documente PDF și text în ChromaDB cu chunking inteligent
- **FR-023**: Sistemul TREBUIE să genereze embeddings local folosind ONNX models (BAAI/bge-small-en-v1.5)
- **FR-024**: Sistemul TREBUIE să răspundă la întrebări criptografice cu citări din documente sursă
- **FR-025**: Sistemul TREBUIE să mențină context conversațional pe bază de conversation_id
- **FR-026**: Sistemul TREBUIE să implementeze reranking cu cross-encoder (BAAI/bge-reranker-base)
- **FR-027**: Sistemul TREBUIE să suporte retrieval hybrid: vector + lexical search
- **FR-028**: Sistemul TREBUIE să permită ingestia de documente noi fără restart (hot reload)
- **FR-029**: Sistemul AR TREBUI să suporte multiple knowledge bases (document collections)

### 5. Command Executor (Rust)
- **FR-030**: Sistemul TREBUIE să execute operații criptografice simetrice: AES-128/256 (CBC, GCM, CTR)
- **FR-031**: Sistemul TREBUIE să execute operații criptografice asimetrice: RSA (2048, 4096 biți), Ed25519
- **FR-032**: Sistemul TREBUIE să execute funcții hash: SHA-256, SHA-512, SHA-3, BLAKE2
- **FR-033**: Sistemul TREBUIE să execute HMAC cu algoritmi configurabili
- **FR-034**: Sistemul TREBUIE să suporte post-quantum cryptography: Kyber (KEM), Dilithium (signatures)
- **FR-035**: Sistemul TREBUIE să impună timeout-uri per operație pentru prevenirea DoS
- **FR-036**: Sistemul TREBUIE să valideze input-urile pe 3 nivele: length, charset, algorithm allowlist
- **FR-037**: Sistemul TREBUIE să ruleze cu cap_drop pentru securitate maximă (non-root, minimal capabilities)
- **FR-038**: Sistemul TREBUIE să folosească OpenSSL 3.0 pentru primitivele criptografice

### 6. Choice Maker (NLP Engine)
- **FR-039**: Sistemul TREBUIE să clasifice intent-ul utilizatorului folosind SecureBERT fine-tuned
- **FR-040**: Sistemul TREBUIE să suporte minimum 10 clase de intent-uri (password_strength, primality, encryption, decryption, theory, hash_break, etc.)
- **FR-041**: Sistemul TREBUIE să extragă entități: numere, algoritmi criptografici, parametri
- **FR-042**: Sistemul TREBUIE să routeze cererile către agentul adecvat bazat pe intent + entities
- **FR-043**: Sistemul TREBUIE să returneze confidence scores pentru clasificare
- **FR-044**: Sistemul AR TREBUI să suporte multi-language (EN, RO, FR)
- **FR-045**: Sistemul AR TREBUI să învețe din feedback (active learning)

### 7. Orchestrator
- **FR-046**: Sistemul TREBUIE să coordoneze toți agenții cu health-check real-time
- **FR-047**: Sistemul TREBUIE să suporte provideri multipli LLM: Ollama, OpenAI, Gemini, Anthropic
- **FR-048**: Sistemul TREBUIE să agregheze răspunsurile paralele în timp real
- **FR-049**: Sistemul TREBUIE să gestioneze lifecycle-ul agenților: start, stop, restart, scale
- **FR-050**: Sistemul TREBUIE să implementeze request multiplexing pentru throughput maxim
- **FR-051**: Sistemul TREBUIE să ofere API HTTP REST pentru toate operațiile
- **FR-052**: Sistemul TREBUIE să stocheze configurația în BoltDB local
- **FR-053**: Sistemul AR TREBUI să suporte WebSocket pentru streaming responses

### 8. Authentication & Authorization (Backend Go - Planificat)
- **FR-054**: Sistemul TREBUIE să suporte autentificare JWT cu access tokens (15min) și refresh tokens (7 zile)
- **FR-055**: Sistemul TREBUIE să implementeze RBAC cu 3 roluri: Admin (full access), User (limitat), Auditor (read-only)
- **FR-056**: Sistemul TREBUIE să suporte refresh token rotation pentru securitate
- **FR-057**: Sistemul TREBUIE să ofere endpoint-uri: /register, /login, /refresh, /logout, /me
- **FR-058**: Sistemul AR TREBUI să suporte OAuth2 / SSO (Google, GitHub, Microsoft)
- **FR-059**: Sistemul AR TREBUI să suporte API key authentication pentru automatizare
- **FR-060**: Sistemul AR TREBUI să ofere 2FA (TOTP) pentru conturi Admin
- **FR-061**: Sistemul TREBUIE să logheze toate încercările de autentificare (success/failure)

### 9. Hash Breaking Agent (Planificat)
- **FR-062**: Sistemul TREBUIE să spargă hash-uri folosind Hashcat (GPU acceleration)
- **FR-063**: Sistemul TREBUIE să folosească PassGAN pentru generare inteligentă de parole candidat
- **FR-064**: Sistemul TREBUIE să distribuie sarcinile pe un cluster Celery (distributed task queue)
- **FR-065**: Sistemul TREBUIE să suporte multiple hash types: MD5, SHA1, SHA256, bcrypt, scrypt, Argon2
- **FR-066**: Sistemul TREBUIE să raporteze progresul spargerii în timp real (percentage, ETA)
- **FR-067**: Sistemul TREBUIE să permită oprirea și reluarea sarcinilor
- **FR-068**: Sistemul TREBUIE să stocheze rezultatele în PostgreSQL pentru audit

### 10. Cryptosystem Detection (Planificat)
- **FR-069**: Sistemul TREBUIE să detecteze automat criptosisteme din input (ciphertext, metadata)
- **FR-070**: Sistemul TREBUIE să integreze CyberChef pentru operațiuni complexe de conversie
- **FR-071**: Sistemul TREBUIE să identifice algoritmi: AES, RSA, DES, 3DES, Blowfish, Twofish
- **FR-072**: Sistemul TREBUIE să detecteze mode-uri de operare: ECB, CBC, GCM, CTR
- **FR-073**: Sistemul AR TREBUI să ofere sugestii de atac automate (padding oracle, brute force)

---

## CERINȚE NEFUNCȚIONALE DETALIATE (NFR-XXX)

### 1. Performanță
- **NFR-001**: Timp de răspuns < 2 secunde pentru operațiuni standard de criptare/decryptare
- **NFR-002**: Throughput minimum 100 request-uri/oră per agent în condiții normale
- **NFR-003**: Factorizare numere < 1024 biți în < 10 secunde (YAFU local)
- **NFR-004**: Generare embeddings pentru 100 pagini document în < 5 minute
- **NFR-005**: Analiză parolă (incluzând HIBP check) în < 3 secunde
- **NFR-006**: Intent classification în < 500ms (SecureBERT inference)
- **NFR-007**: Scalare orizontală la minimum 10 instanțe per agent în Kubernetes
- **NFR-008**: Cold start time < 30 secunde pentru orice agent
- **NFR-009**: Memory limit per agent: maximum 4GB (configurabil)
- **NFR-010**: CPU limit per agent: maximum 2 vCPU (configurabil)

### 2. Securitate (SR-XXX)
#### Autentificare & Sesiuni
- **SR-001**: Toate comunicațiile TREBUIE să fie criptate cu TLS 1.3
- **SR-002**: Parolele TREBUIE să fie hashed cu Argon2id (memory: 64MB, iterations: 3, parallelism: 2)
- **SR-003**: JWT tokens TREBUIE să fie semnate cu RS256 (asymmetric) și să expire în 15 minute
- **SR-004**: Refresh tokens TREBUIE să fie rotite la fiecare utilizare
- **SR-005**: Sesiunile TREBUIE să fie invalidate la logout (blacklist în Redis)
- **SR-006**: Sistemul TREBUIE să blocheze conturile după 5 încercări eșuate de autentificare pentru 30 minute

#### Controlul Accesului
- **SR-007**: Sistemul TREBUIE să implementeze RBAC cu principle of least privilege
- **SR-008**: API-urile TREBUIE să verifice permisiunile la fiecare request (authorization middleware)
- **SR-009**: Resursele sensibile TREBUIE să fie accesibile doar cu rol Admin

#### Protecția Datelor
- **SR-010**: Datele sensibile (parole, API keys) TREBUIE să fie criptate at-rest (AES-256-GCM)
- **SR-011**: Secrets management TREBUIE să folosească HashiCorp Vault sau K8s Secrets
- **SR-012**: Logs TREBUIE să nu conțină date sensibile (sanitizare automată)
- **SR-013**: Backup-urile TREBUIE să fie criptate

#### Network Security
- **SR-014**: Network segmentation: agenții în rețea izolată (vitruvian-agents)
- **SR-015**: Firewall rules: doar porturile necesare deschise (80, 443, 8200)
- **SR-016**: Rate limiting: 10 req/min pentru autentificare, 100 req/min pentru alte endpoint-uri

#### Application Security
- **SR-017**: Validare input la toate endpoint-urile (whitelist approach)
- **SR-018**: Prevenire SQL Injection: doar parametrized queries
- **SR-019**: Prevenire XSS: output encoding pentru toate datele user
- **SR-020**: Prevenire CSRF: token-based protection pentru state-changing operations
- **SR-021**: Security headers: CSP, X-Frame-Options, HSTS, X-Content-Type-Options

#### Container Security
- **SR-022**: Containerele TREBUIE să ruleze cu non-root user
- **SR-023**: Capabilities drop: ALL cu excepția NET_BIND_SERVICE
- **SR-024**: Security opt: no-new-privileges:true
- **SR-025**: Image signing: Docker Content Trust sau cosign
- **SR-026**: Vulnerability scanning: Trivy scan în CI/CD pipeline
- **SR-027**: Base images: Alpine sau distroless minimal

#### Audit & Logging
- **SR-028**: Toate operațiile critice TREBUIE loghate: auth, agent operations, crypto operations
- **SR-029**: Log format: JSON structurat cu câmpuri: timestamp, user_id, operation, resource, result
- **SR-030**: Log retention: minimum 5 ani pentru audit trail
- **SR-031**: Logs TREBUIE să fie trimise către centralized logging (ELK / Loki)
- **SR-032**: Imuabilitate log-uri: write-only storage pentru archivare

### 3. Disponibilitate & Fiabilitate
- **NFR-011**: Uptime SLA: 99.5% (lunar) = maximum 3.6 ore downtime/lună
- **NFR-012**: MTTR (Mean Time To Recovery): < 15 minute pentru incidente critice
- **NFR-013**: Redundanță: minimum 2 replica per agent în Kubernetes
- **NFR-014**: Auto-healing: restart automat la crash cu backoff exponențial (1s, 2s, 4s, 8s, max 60s)
- **NFR-015**: Health checks: liveness și readiness probes în K8s
- **NFR-016**: Graceful shutdown: trece requests-in-flight înainte de stop
- **NFR-017**: Circuit breaker: fail-fast pentru downstream services căzute
- **NFR-018**: Database: PostgreSQL cu replicație (master-slave) pentru high availability

### 4. Scalabilitate
- **NFR-019**: Suport pentru 1000+ utilizatori concurenți
- **NFR-020**: Auto-scaling orizontală în Kubernetes (HPA) bazat pe CPU/memory
- **NFR-021**: Database sharding pentru > 1TB date (dacă e necesar)
- **NFR-022**: Connection pooling pentru PostgreSQL (max 100 conexiuni)
- **NFR-023**: Redis cluster pentru scalare cache (sentinel mode)
- **NFR-024**: Load balancing: Kubernetes Service (ClusterIP) pentru intern, Ingress pentru extern

### 5. Observabilitate
#### Metrics
- **NFR-025**: Export metrici în format Prometheus (endpoint /metrics)
- **NFR-026**: Metrici business: passwords_checked, primes_factored, docs_ingested, crypto_ops
- **NFR-027**: Metrici tehnice: request_duration, request_count, error_rate, memory_usage, cpu_usage
- **NFR-028**: Labels: agent_type, operation, status, user_id (optional)

#### Logging
- **NFR-029**: Structured logging (JSON) cu trace IDs
- **NFR-030**: Log levels: ERROR, WARN, INFO, DEBUG (configurabil)
- **NFR-031**: Correlation IDs pentru request tracing peste microservicii
- **NFR-032**: Sampling: 100% pentru ERROR, 10% pentru INFO în producție

#### Tracing
- **NFR-033**: Distributed tracing cu OpenTelemetry
- **NFR-034**: Trace collection: Jaeger sau Tempo
- **NFR-035**: Span attribution: ingress → orchestrator → agent → egress

#### Dashboards & Alerting
- **NFR-036**: Dashboards Grafana pentru vizualizare metrici real-time
- **NFR-037**: Alerte Prometheus: agent down > 5 min, error_rate > 5%, memory > 90%
- **NFR-038**: Alert channels: email, Slack (webhook), PagerDuty (critical)

### 6. Mentenanabilitate
- **NFR-039**: Code coverage > 80% pentru teste unitare
- **NFR-040**: API documentation auto-generată (OpenAPI 3.0 / Swagger)
- **NFR-041**: Zero-downtime deployment în Kubernetes (rolling updates, maxSurge: 1, maxUnavailable: 0)
- **NFR-042**: Database migrations: versionate (Go migrate / Flyway)
- **NFR-043**: Configuration as code: environment variables, ConfigMaps
- **NFR-044**: Documentation: README per serviciu, API docs, architecture diagrams
- **NFR-045**: Linting: golangci-lint, pylint, clippy, ESLint în CI
- **NFR-046**: Code formatting: gofmt, black, rustfmt în pre-commit hooks

---

## QUALITY OF SERVICE (QoS-XXX)

### Latency Targets
- **QoS-001**: P50 latency (mediană) < 500ms pentru toate operațiile
- **QoS-002**: P95 latency < 2 secunde (95% din request-uri)
- **QoS-003**: P99 latency < 5 secunde (99% din request-uri)
- **QoS-004**: Cold start latency < 30 secunde pentru agenți

### Error Rates
- **QoS-005**: Rată de eroare globală < 0.1% pentru operațiuni criptografice
- **QoS-006**: Rată de eroare per agent < 1% în condiții normale
- **QoS-007**: Timeout rate < 0.01% (request-uri care expire)

### Recovery Objectives
- **QoS-008**: RTO (Recovery Time Objective) < 1 oră: restore complet din backup
- **QoS-009**: RPO (Recovery Point Objective) < 15 minute: pierdere maximă de date
- **QoS-010**: Failover time < 30 secunde pentru cluster K8s

### Data Consistency
- **QoS-011**: Strong consistency pentru autentificare/autorizare (PostgreSQL)
- **QoS-012**: Eventual consistency pentru RAG system (ChromaDB replication lag < 5 sec)
- **QoS-013**: Cache invalidation < 1 minut pentru Redis

### Data Retention
- **QoS-014**: Log-uri: 5 ani (archivare în object storage)
- **QoS-015**: Date active: 7 ani (conform reglementări)
- **QoS-016**: Backup offsite: 30 zile (geo-redundancy)

---

## CERINȚE AI/ML SPECIFICE (MLR-XXX)

### 1. Model Specification
#### Password Strength Models
- **MLR-001**: PassGPT accuracy > 85% pe dataset RockYou (test set)
- **MLR-002**: PassStrengthAI (CNN) accuracy > 82% pe dataset proprietar
- **MLR-003**: Ensemble agreement: minimum 2 din 3 modele trebuie să fie de acord
- **MLR-004**: False positive rate < 5% (parole slabe clasificate greșit ca tari)

#### Intent Classification
- **MLR-005**: SecureBERT F1-score > 0.90 pe taxonomy de 10 clase
- **MLR-006**: Intent classification inference time < 500ms pe CPU
- **MLR-007**: Confidence threshold: 0.85 (routare doar dacă confidence > 85%)

#### Embedding Models
- **MLR-008**: Semantic similarity > 0.80 pe domain crypto (evaluat pe dataset manual)
- **MLR-009**: Reranker improvement: +10% relevanță vs baseline
- **MLR-010**: Embedding generation: < 100ms per document chunk

### 2. Data Management
#### Dataset Collection
- **MLR-011**: Parole: doar colecții publice (RockYou, SecLists) - NU date reale utilizatori
- **MLR-012**: Criptografie: RFC-uri, NIST standards, cursuri universitare, cărți (public domain)
- **MLR-013**: Documente: PDF, TXT, Markdown cu metadata sursă

#### Data Preprocessing
- **MLR-014**: Anonimizare: removal PII (nume, email, phone) din documente
- **MLR-015**: Chunking: 512 tokens per chunk cu overlap de 50 tokens
- **MLR-016**: Tokenization: WordPiece pentru BERT models

#### Model Versioning
- **MLR-017**: Toate modelele versionate în MLflow sau DVC
- **MLR-018**: Metadata per model: accuracy, dataset, hyperparameters, data antrenare
- **MLR-019**: Model registry: rollback la versiuni anterioare

#### Drift Detection
- **MLR-020**: Monitorizare accuracy model în producție
- **MLR-021**: Alertă dacă accuracy scade cu > 5% față de baseline
- **MLR-022**: Retraining lunar cu date noi

### 3. Guardrails
#### Output Validation
- **MLR-023**: Length filtering: răspunsuri LLM < 2000 tokens
- **MLR-024**: Profanity filter: blocare conținut ofensator
- **MLR-025**: PII filter: detectare și mascare date personale în output

#### Rate Limiting
- **MLR-026**: 10 req/minut per utilizator pentru operații costisitoare (factorizare)
- **MLR-027**: 100 req/minut per utilizator pentru operații standard
- **MLR-028**: Queue depth: maximum 100 task-uri în așteptare per user

#### Resource Limits
- **MLR-029**: GPU memory limit: 8GB per PassGAN inference
- **MLR-030**: Timeout per model inference: 30 secunde
- **MLR-031**: Max concurrent requests per model: 10

### 4. Ethics
#### Fairness
- **MLR-032**: Password models: fară bias lingvistic/cultural (evaluat pe diverse dataset-uri)
- **MLR-033**: Intent classification: egalitate de tratament pentru toate limbile suportate

#### Transparency
- **MLR-034**: Răspunsurile RAG TREBUIE să includă citări (source document, page, relevance)
- **MLR-035**: Confidence scores afișate utilizatorului pentru toate predicțiile ML
- **MLR-036**: Explicabilitate: highlight în text pentru entity extraction

#### Accountability
- **MLR-037**: Audit trail pentru toate deciziile automate (model version, input, output, timestamp)
- **MLR-038**: Human-in-the-loop pentru operații critice (browsing hash results > 1000 entries)
- **MLR-039**: Feedback mechanism: utilizatori pot semnala răspunsuri incorecte

### 5. Model Lifecycle
#### Training
- **MLR-040**: Train locally pe GPU (NVIDIA RTX 3080+ sau echivalent)
- **MLR-041**: Training time < 24 ore pentru PassGPT fine-tuning
- **MLR-042**: Hyperparameter optimization cu Optuna (50 trials)

#### Deployment
- **MLR-043**: Model export: ONNX format pentru portabilitate
- **MLR-044**: Model serving: FastAPI cu Uvicorn (async)
- **MLR-045**: Model loading: lazy loading la first request

#### Monitoring
- **MLR-046**: Prediction latency: P50 < 100ms, P95 < 500ms
- **MLR-047**: Model throughput: > 100 predictions/secundă
- **MLR-048**: Feature distribution tracking (drift detection)

#### Retraining
- **MLR-049**: Retraining lunar cu date noi
- **MLR-050**: A/B testing înainte de deploy (canary deployment)
- **MLR-051**: Shadow mode: nou model parallel cu vechi pentru comparație

---

## COMPLIANCE (C-XXX)

### 1. GDPR (General Data Protection Regulation)
- **C-001**: Dacă se stochează IP addresses sau user data: consimțământ explicit
- **C-002**: Right to erasure: posibilitatea ștergere cont + toate datele asociate
- **C-003**: Data minimization: stochează doar date necesare
- **C-004**: Data portability: export date utilizator în format JSON/CSV
- **C-005**: Breach notification: notificare în 72 ore în caz de leak

### 2. NIST SP 800-53 (Security and Privacy Controls)
- **C-006**: AC-001: Access control policy
- **C-007**: AU-001: Audit and accountability
- **C-008**: SC-001: System and communications protection
- **C-009**: SI-001: System monitoring
- **C-010**: SA-001: System and services acquisition

### 3. FIPS 140-2 (Cryptographic Modules)
- **C-011**: Toate operațiile criptografice TREBUIE să folosească module FIPS-validated
- **C-012**: OpenSSL FIPS mode pentru producție
- **C-013**: Algoritmi permis: AES (FIPS 197), RSA (FIPS 186-4), SHA-2 (FIPS 180-4)
- **C-014**: Algoritmi PROHIBIȚI: MD5, SHA1, DES, RC4

### 4. NATO STANAG 4761 (dacă aplicabil pentru ATM)
- **C-015**: NATO RESTful Web Services (NATO RESTful WS)
- **C-016**: NATO Network Enabled Capability (NNEC)
- **C-017**: Information Security (INFOSEC)

### 5. ISO 27001 (Information Security Management)
- **C-018**: Risk assessment anual
- **C-019**: Security policy documentată
- **C-020**: Continual improvement process

---

## DESIGN & IMPLEMENTATION CONSTRAINTS

### 1. Installation
- **DI-001**: One-line deployment pentru Docker Compose: `./run_all.sh start`
- **DI-002**: Helm charts pentru Kubernetes deployment (repo GitHub)
- **DI-003**: Suport pentru Linux: Ubuntu 22.04+, RHEL 9+, Debian 12+
- **DI-004**: Prerequisites: Docker 24+, Docker Compose 2.20+, kubectl 1.28+
- **DI-005**: Installation time < 15 minute pe hardware standard

### 2. Build & Delivery (CI/CD)
- **BD-001**: CI/CD pipeline cu GitHub Actions sau GitLab CI
- **BD-002**: Automated testing pe fiecare PR:
  - Unit tests (coverage > 80%)
  - Integration tests (Docker Compose)
  - Linting (golangci-lint, pylint, clippy)
  - Security scanning (Trivy, Snyk)
- **BD-003**: Container images signed cu cosign sau Docker Content Trust
- **BD-004**: SBOM (Software Bill of Materials) generat cu Syft pentru fiecare imagine
- **BD-005**: Automated release pe merge la main (semver: v1.0.0)
- **BD-006**: Deployment: staging → production promotion

### 3. Distribution (Kubernetes)
- **DD-001**: Kubernetes manifests în folder `k8s/`:
  - deployments/ (Deployment YAMLs)
  - services/ (Service YAMLs)
  - ingress/ (Ingress YAMLs)
  - configmaps/ (ConfigMap YAMLs)
  - secrets/ (Secret YAMLs - template)
- **DD-002**: Helm Chart pentru easy deployment:
  - values.yaml pentru configurare
  - templates/ pentru K8s resources
- **DD-003**: Multi-region deployment: posibilitatea deploy în multiple clusters
- **DD-004**: Database replication: master-slave pentru read scalability
- **DD-005**: Redis cluster: sentinel mode pentru high availability
- **DD-006**: Backup automation: cron job pentru PostgreSQL backup (daily)

### 4. Maintainability
- **DM-001**: Modular architecture: agenții decuplați prin API contracts
- **DM-002**: OpenAPI spec pentru fiecare agent (swagger.yaml)
- **DM-003**: Coding standards:
  - Go: golangci-lint cu config personalizat
  - Python: pylint + black formatter
  - Rust: clippy + rustfmt
- **DM-004**: Documentation:
  - Inline comments > 20% din cod
  - README.md per serviciu
  - API docs auto-generate (Swagger UI)
- **DM-005**: Error handling:
  - Standardized error codes (HTTP status + error_code)
  - Error messages user-friendly
  - Stack-trace doar în logs (nu în response)
- **DM-006**: Configuration:
  - Environment variables pentru runtime config
  - ConfigMaps pentru K8s config
  - Secrets pentru sensitive data

### 5. Portability
- **DP-001**: Multi-cloud support: AWS (EKS), GCP (GKE), Azure (AKS), on-prem K8s
- **DP-002**: Container images: multi-arch (amd64, arm64) cu docker buildx
- **DP-003**: No vendor lock-in: avoid AWS-specific services (use standard K8s)
- **DP-004**: Database agnostic: suport PostgreSQL, MySQL (prin ORM abstraction)

### 6. Cost
- **DC-001**: Cloud cost estimation: < $100/lună pentru 100 utilizatori (3 agents x 2 vCPU x 4GB)
- **DC-002**: Optimizare costuri:
  - Spot instances pentru non-critical workloads (training ML)
  - Reserved instances pentru producție (1-3 ani commitment)
  - Auto-scaling pentru plată doar ce consumi
- **DC-003**: Monitoring costurilor: CloudHealth sau cloud provider native
- **DC-004**: On-prem alternative: deployment pe hardware propriu pentru cost zero (doar electricitate + mentenanță)

### 7. Deadlines & Milestones
- **DD-007**: Sprint 1-2: Backend Go cu Auth (FR-054 → FR-061)
- **DD-008**: Sprint 3-4: Kubernetes migration (DI-001 → DD-006)
- **DD-009**: Sprint 5: CI/CD pipeline (BD-001 → BD-006)
- **DD-010**: Sprint 6: Hash Breaking Agent (FR-062 → FR-068)
- **DD-011**: Sprint 7-8: Cryptosystem Detection (FR-069 → FR-073)
- **DD-012**: Sprint 9: Monitoring stack (NFR-025 → NFR-038)

---

## VERIFICATION & VALIDATION

### Matrix Cerințe → Teste
| ID Cerință | Tip Test | Test Case ID | Status | Evidence |
|------------|----------|--------------|--------|----------|
| FR-001 | Unit | TC-AGT-001 | Pending | agents/orchestrator/internal/agents/pool_test.go |
| FR-008 | Integration | TC-PWD-001 | Pending | tests/integration/password_ensemble_test.go |
| FR-015 | Performance | TC-PRM-001 | Pending | tests/performance/prime_factorization_test.go |
| SR-001 | Security | TC-SEC-001 | Pending | tests/security/tls_test.go |
| NFR-001 | Performance | TC-PER-001 | Pending | tests/performance/latency_test.go |

---

## ANEXE DETALII

### A1. Architecture Diagrams
#### C4 Model Diagrams
- **Level 1: System Context**
  - User → Vitruvian Platform → External Services (HIBP, FactorDB)
- **Level 2: Container**
  - React Frontend
  - Backend Go (Auth)
  - Orchestrator
  - Agent Pool (Password, Theory, Prime, Command, Choice)
  - Data Layer (PostgreSQL, Redis)
- **Level 3: Component**
  - Per agent: API, Service, Repository, Model

#### Sequence Diagrams
1. **User Authentication Flow**
   User → Frontend → Backend (JWT) → Orchestrator → Agent
2. **Password Analysis Flow**
   User → Choice Maker → Password Checker → PassGPT + zxcvbn + HIBP → Aggregator → Response
3. **Prime Factorization Flow**
   User → Choice Maker → Prime Checker → YAFU / FactorDB → Cache → Response

### A2. API Contracts (OpenAPI 3.0)
- `/api/v1/auth/login` - POST
- `/api/v1/auth/refresh` - POST
- `/api/v1/password/score` - POST
- `/api/v1/prime/isprime` - POST
- `/api/v1/theory/generate` - POST
- `/api/v1/crypto/encrypt` - POST
- `/api/v1/crypto/decrypt` - POST
- `/api/v1/hash/break` - POST (planificat)

### A3. Data Model
#### PostgreSQL Tables
```sql
users (id, email, password_hash, role, created_at, updated_at)
refresh_tokens (id, user_id, token_hash, expires_at)
audit_logs (id, user_id, operation, resource, details, timestamp)
jobs (id, user_id, agent_type, status, input, output, created_at)
```

#### Redis Cache Structure
```
session:{user_id} -> JSON session data
cache:prime:{number} -> factorization result
cache:password:{hash} -> password score
```

### A4. Kubernetes Manifests
```yaml
# deployments/orchestrator.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orchestrator
spec:
  replicas: 2
  selector:
    matchLabels:
      app: orchestrator
  template:
    metadata:
      labels:
        app: orchestrator
    spec:
      containers:
      - name: orchestrator
        image: vitruvian/orchestrator:v1.0.0
        ports:
        - containerPort: 8200
        resources:
          requests:
            cpu: 250m
            memory: 256Mi
          limits:
            cpu: 1000m
            memory: 1Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8200
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8200
          initialDelaySeconds: 5
          periodSeconds: 10
```

### A5. CI/CD Pipeline (GitHub Actions)
```yaml
name: Vitruvian CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Go
        uses: actions/setup-go@v4
        with:
          go-version: '1.21'
      - name: Run tests
        run: |
          go test -v -race -coverprofile=coverage.out ./...
          go tool cover -html=coverage.out -o coverage.html
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Trivy
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'

  build-push:
    needs: [test, security-scan]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Build and push Docker images
        run: |
          docker buildx build --push \
            --platform linux/amd64,linux/arm64 \
            -t vitruvian/orchestrator:${{ github.sha }} \
            -t vitruvian/orchestrator:latest \
            ./agents/orchestrator
```

---

# NOTA BENE:

1. **Prioritizare**:
   - **High Priority (MUST)**: FR-001 → FR-053 (cei 5 agenți + orchestrator)
   - **Medium Priority (SHOULD)**: FR-054 → FR-061 (Auth), NFR-001 → NFR-012
   - **Low Priority (MAY)**: FR-062 → FR-073 (Hash Breaking + Cryptosystem Detection)

2. **MVP (Minimum Viable Product)**:
   - Password Checker (FR-008 → FR-014)
   - Prime Checker (FR-015 → FR-021)
   - Theory Specialist (FR-022 → FR-029)
   - Command Executor (FR-030 → FR-038)
   - Choice Maker (FR-039 → FR-045)
   - Orchestrator (FR-046 → FR-053)

3. **Post-MVP**:
   - Backend cu Auth (FR-054 → FR-061)
   - Kubernetes deployment (DD-001 → DD-006)
   - CI/CD pipeline (BD-001 → BD-006)
   - Monitoring stack (NFR-025 → NFR-038)

4. **Future Enhancements**:
   - Hash Breaking Agent (FR-062 → FR-068)
   - Cryptosystem Detection (FR-069 → FR-073)
   - Advanced Auth: OAuth2, 2FA (FR-058 → FR-060)
   - Multi-language support (FR-044, FR-045)

5. **Security Focus**:
   - Toate cerințele SR-XXX sunt critice pentru un sistem militar/ATM
   - FIPS 140-2 compliance obligatoriu dacă se folosește pentru misiuni critice
   - Audit trail (SR-028 → SR-032) esențial pentru investigații post-incident

6. **AI/ML Considerations**:
   - Guardrails (MLR-023 → MLR-031) cruciale pentru prevenire abuz
   - Ethics (MLR-032 → MLR-039) important pentru acceptare societală
   - Model lifecycle (MLR-040 → MLR-051) asigură mentenanță pe termen lung
