# 🎯 Analiză Comprehensivă și Propuneri SRS - Vitruvian Cipher Platform

**Document pregătit de:** GitHub Copilot (Claude Opus 4.5)  
**Data:** 4 Ianuarie 2026  
**Versiune:** 1.0  
**Scop:** Propuneri pentru un SRS robust, tehnic, conform celor mai bune practici din industrie

---

## 📋 Cuprins

1. [Rezumat Executiv](#1-rezumat-executiv)
2. [Analiza Proiectului](#2-analiza-proiectului)
3. [Structura Recomandată SRS](#3-structura-recomandată-srs)
4. [Cerințe Funcționale](#4-cerințe-funcționale)
5. [Cerințe Non-Funcționale](#5-cerințe-non-funcționale)
6. [Quality of Service (QoS)](#6-quality-of-service-qos)
7. [Cerințe AI/ML](#7-cerințe-aiml)
8. [Cerințe de Securitate](#8-cerințe-de-securitate)
9. [Cerințe de Infrastructură și DevOps](#9-cerințe-de-infrastructură-și-devops)
10. [Cerințe de Conformitate](#10-cerințe-de-conformitate)
11. [Verificare și Validare](#11-verificare-și-validare)
12. [Recomandări pentru Document](#12-recomandări-pentru-document)

---

## 1. Rezumat Executiv

### 1.1 Descrierea Proiectului

**Vitruvian Cipher** este o platformă de inteligență criptografică de următoare generație, bazată pe o arhitectură multi-agent autonomă. Platforma orchestrează agenți AI specializați pentru analiza securității parolelor, factorizare prime, asistență teoretică în criptografie, operațiuni criptografice și detecție de criptosisteme cu scor de încredere.

### 1.2 Stack Tehnologic Principal

| Limbaj | Servicii | Scop |
|--------|----------|------|
| **Go** | Orchestrator, Prime Checker, Backend API | Orchestrare, routing, performanță |
| **Rust** | Command Executor | Operațiuni criptografice sigure la nivel de memorie |
| **Python** | Password Checker, Theory Specialist, Choice Maker | ML/AI, NLP, RAG |
| **TypeScript** | React Interface | Frontend modern |

### 1.3 Arhitectura de Bază

> **📐 Instrucțiuni Diagramă UML - Component Diagram (Arhitectură pe Niveluri)**
>
> Creează o **diagramă de componente UML** cu 5 niveluri (package-uri) verticale conectate prin dependențe:
>
> 1. **«package» Nivel Frontend** (sus)
>    - Componente: `React Web`, `CLI Client`, `External API Consumers`
>    - Stereotip: `<<presentation>>`
>
> 2. **«package» Nivel API Gateway**
>    - Componentă: `Go Backend API`
>    - Notă: "Auth, Rate Limiting, Routing, Audit"
>    - Stereotip: `<<gateway>>`
>
> 3. **«package» Nivel Orchestrare**
>    - Componentă: `Orchestrator`
>    - Notă: "Intent Routing, Agent Coordination, LLM"
>    - Stereotip: `<<service>>`
>
> 4. **«package» Nivel Agenți** (cel mai mare)
>    - 9 componente în grilă 3×3:
>      - `Password Checker` [Python/ML]
>      - `Prime Checker` [Go/YAFU]
>      - `Theory Specialist` [Python/RAG]
>      - `Command Executor` [Rust/Crypto]
>      - `Choice Maker` [Python/NLP]
>      - `Cryptosystem Detection` [Node.js]
>      - `Hash Breaker` [Python/Hashcat]
>      - `CTF Tool` [Python/Forensics]
>    - Stereotip pentru fiecare: `<<agent>>`
>
> 5. **«package» Nivel Date** (jos)
>    - Componente: `PostgreSQL`, `Redis Cache`, `ChromaDB (Vector Store)`
>    - Stereotip: `<<database>>`
>
> **Conexiuni**: Săgeți de dependență (`-->`) de sus în jos între niveluri adiacente.

---

## 2. Analiza Proiectului

### 2.1 Componente Identificate

#### 2.1.1 Agenți Specializați (9)

| Agent | Port | Limbaj | Funcționalitate |
|-------|------|--------|-----------------|
| **Password Checker** | 9000 | Python | Ansamblu ML (PassGPT, zxcvbn, HIBP, PassStrengthAI) |
| **Prime Checker** | 5000 | Go | Primalitate, factorizare (Miller-Rabin, YAFU, FactorDB) |
| **Theory Specialist** | 8100 | Python | RAG pentru teorie criptografică (ChromaDB, FastEmbed) |
| **Command Executor** | 8085 | Rust | Operațiuni crypto (AES, RSA, HMAC, PQC) |
| **Choice Maker** | 8081 | Python | NLP intent/entity (SecureBERT 2.0) |
| **Orchestrator** | 8200 | Go | Coordonare, routing, agregare |
| **Cryptosystem Detection** | 18090 | Node.js | Detectare criptosistem cu scor de incredere (CyberChef, heuristici dcode-like) |
| **Hash Breaker** | 8082 | Python | Spargere hash-uri (Hashcat, dicționare, reguli, GPU) |
| **CTF Tool** | 8083 | Python | Asistență CTF (steganografie, forensics, analiză binară) |

#### 2.1.2 Infrastructură

- **Containerizare**: Docker + Docker Compose
- **Orchestrare**: Kubernetes (cluster productie)
- **Baze de Date**: PostgreSQL 16, Redis 7, ChromaDB, BoltDB
- **Observabilitate**: Prometheus + Grafana + loguri centralizate (obligatoriu in productie)
- **CI/CD**: Pipeline-uri automatizate (build/test/scan/deploy)

### 2.2 Dependențe Externe

| Dependență | Tip | Scop |
|------------|-----|------|
| HaveIBeenPwned API | API extern | Verificare parole compromise |
| FactorDB | API extern | Factorizare numere mari |
| YAFU | Tool local | Factorizare avansată |
| CyberChef Magic | Tool/Lib | Detectare criptosisteme |
| OpenSSL 3.x + oqsprovider | Bibliotecă | Operațiuni crypto + PQC |
| LLM Providers (Ollama, OpenAI, Anthropic, Gemini) | API extern | Generare răspunsuri |
| Hugging Face Models | Modele ML | PassGPT, SecureBERT |

### 2.3 Actori și Roluri Identificați

| Actor | Descriere | Nivel Acces |
|-------|-----------|-------------|
| **Anonymous** | Acces limitat la operațiuni demonstrative și informații publice | Minim |
| **User** | Acces complet la funcționalități standard | Standard |
| **Admin** | Management complet al platformei, securitate și audit | Complet |

Actori tehnici (non-rol): servicii interne M2M și pipeline CI/CD pentru build/test/deploy.

---

## 3. Structura Recomandată SRS

Recomand adoptarea structurii din `srs-template-bare.md` cu următoarele adaptări:

```
1. Introduction
   1.1 Document Purpose
   1.2 Product Scope
   1.3 Definitions, Acronyms, and Abbreviations
   1.4 References
   1.5 Document Overview

2. Product Overview
   2.1 Product Perspective
   2.2 Product Functions
   2.3 Product Constraints
   2.4 User Characteristics
   2.5 Assumptions and Dependencies
   2.6 Apportioning of Requirements (Roadmap)

3. Requirements
   3.1 External Interfaces
       3.1.1 User Interfaces
       3.1.2 Hardware Interfaces
       3.1.3 Software Interfaces (APIs)
   3.2 Functional Requirements
       3.2.1 Identity & Access Management
       3.2.2 Orchestration & Routing
       3.2.3 Agent Capabilities
       3.2.4 Data & Conversation Management
       3.2.5 Administration & Audit
   3.3 Quality of Service
       3.3.1 Performance
       3.3.2 Security
       3.3.3 Reliability
       3.3.4 Availability
       3.3.5 Observability
   3.4 Compliance
   3.5 Design and Implementation
       3.5.1 Installation
       3.5.2 Build and Delivery (CI/CD)
       3.5.3 Distribution (K8s)
       3.5.4 Maintainability
       3.5.5 Reusability
       3.5.6 Portability
       3.5.7 Cost
       3.5.8 Deadline
   3.6 AI/ML Requirements
       3.6.1 Model Specification
       3.6.2 Data Management
       3.6.3 Guardrails
       3.6.4 Ethics
       3.6.5 Human-in-the-Loop
       3.6.6 Model Lifecycle (MLOps)

4. Verification
   4.1 Test Matrix
   4.2 Acceptance Criteria

5. Appendixes
   5.1 Use Case Diagrams
   5.2 Sequence Diagrams
   5.3 Architecture Diagrams
   5.4 API Specifications
```

---

## 4. Cerințe Funcționale

### 4.1 Identity & Access Management (IAM)

| ID | Cerință | Prioritate |
|----|---------|------------|
| **FR-IAM-001** | Sistemul TREBUIE să permită înregistrarea utilizatorilor cu email, parolă și confirmare email. | MUST |
| **FR-IAM-002** | Sistemul TREBUIE să implementeze autentificare prin email/parolă cu rate limiting (max 5 încercări/minut). | MUST |
| **FR-IAM-003** | Sistemul TREBUIE să suporte MFA (TOTP RFC 6238) pentru rolul Admin. | MUST |
| **FR-IAM-004** | Sistemul AR TREBUI să suporte WebAuthn/FIDO2 pentru passwordless authentication. | SHOULD |
| **FR-IAM-005** | Sistemul TREBUIE să emită token-uri JWT (access: 15min, refresh: 7 zile) cu rotație automată. | MUST |
| **FR-IAM-006** | Sistemul TREBUIE să permită generarea și revocarea de API keys cu scope-uri configurabile. | MUST |
| **FR-IAM-007** | Sistemul TREBUIE să implementeze RBAC cu 3 roluri predefinite: Anonymous, User, Admin. | MUST |
| **FR-IAM-008** | Sistemul TREBUIE să permită resetarea parolei prin email cu token unic (TTL: 1 oră). | MUST |
| **FR-IAM-009** | Sistemul AR TREBUI să suporte OAuth2/OIDC pentru autentificare externă (GitHub, Google). | SHOULD |
| **FR-IAM-010** | Sistemul TREBUIE să invalideze toate sesiunile active la schimbarea parolei. | MUST |

### 4.2 Orchestration & Routing

| ID | Cerință | Prioritate |
|----|---------|------------|
| **FR-ORC-001** | Orchestratorul TREBUIE să detecteze intenția utilizatorului folosind agentul Choice Maker. | MUST |
| **FR-ORC-002** | Orchestratorul TREBUIE să ruteze cererile către agentul/agenții potriviți pe baza intenției detectate. | MUST |
| **FR-ORC-003** | Orchestratorul TREBUIE să suporte execuție paralelă pentru operații independente. | MUST |
| **FR-ORC-004** | Orchestratorul TREBUIE să agregeze răspunsurile de la mai mulți agenți într-un răspuns unificat. | MUST |
| **FR-ORC-005** | Orchestratorul TREBUIE să implementeze timeout configurabil per agent (default: 30s). | MUST |
| **FR-ORC-006** | Orchestratorul TREBUIE să implementeze circuit breaker pentru agenți cu probleme. | MUST |
| **FR-ORC-007** | Orchestratorul TREBUIE să expună health endpoints pentru fiecare serviciu gestionat. | MUST |
| **FR-ORC-008** | Orchestratorul AR TREBUI să ofere fallback logic când agenții sunt indisponibili. | SHOULD |
| **FR-ORC-009** | Orchestratorul TREBUIE să suporte selectarea dinamică a provider-ului LLM per cerere. | MUST |
| **FR-ORC-010** | Orchestratorul AR TREBUI să permită configurarea priorităților de rutare per agent. | SHOULD |

### 4.3 Password Intelligence Agent

| ID | Cerință | Prioritate |
|----|---------|------------|
| **FR-PWD-001** | Agentul TREBUIE să calculeze scorul de securitate unificat (0-100) din ansamblu ML. | MUST |
| **FR-PWD-002** | Agentul TREBUIE să integreze PassGPT pentru analiza probabilistică a parolelor. | MUST |
| **FR-PWD-003** | Agentul TREBUIE să integreze zxcvbn pentru evaluarea heuristică. | MUST |
| **FR-PWD-004** | Agentul TREBUIE să verifice parola contra bazei HIBP (k-anonymity). | MUST |
| **FR-PWD-005** | Agentul AR TREBUI să integreze PassStrengthAI (CNN) pentru evaluare suplimentară. | SHOULD |
| **FR-PWD-006** | Agentul TREBUIE să returneze recomandări acționabile pentru îmbunătățirea parolei. | MUST |
| **FR-PWD-007** | Agentul TREBUIE să dezactiveze automat PassGPT pentru parole > 10 caractere. | MUST |
| **FR-PWD-008** | Agentul AR TREBUI să aplice penalizări pentru parole scurte (< 8 caractere). | SHOULD |
| **FR-PWD-009** | Agentul TREBUIE să limiteze lungimea parolei acceptate la 128 caractere. | MUST |
| **FR-PWD-010** | Agentul NU TREBUIE să stocheze sau să logheze parola în clar. | MUST |

### 4.4 Prime Factorization Agent

| ID | Cerință | Prioritate |
|----|---------|------------|
| **FR-PRM-001** | Agentul TREBUIE să verifice primalitatea numerelor folosind Miller-Rabin deterministic pentru numere < 2^64. | MUST |
| **FR-PRM-002** | Agentul TREBUIE să integreze YAFU pentru factorizare avansată. | MUST |
| **FR-PRM-003** | Agentul TREBUIE să utilizeze FactorDB ca fallback pentru numere mari. | MUST |
| **FR-PRM-004** | Agentul TREBUIE să implementeze cache LRU in-memory + persistent BoltDB. | MUST |
| **FR-PRM-005** | Agentul TREBUIE să returneze factorii primi și metoda folosită. | MUST |
| **FR-PRM-006** | Agentul TREBUIE să limiteze numărul maxim de cifre acceptate (default: 1000). | MUST |
| **FR-PRM-007** | Agentul TREBUIE să implementeze timeout-uri per backend (YAFU: 5s primality, 8s factor). | MUST |
| **FR-PRM-008** | Agentul AR TREBUI să raporteze timpul de calcul în răspuns. | SHOULD |
| **FR-PRM-009** | Agentul TREBUIE să expună endpoint /history pentru ultimele rezultate. | MUST |
| **FR-PRM-010** | Agentul TREBUIE să gestioneze concurența YAFU cu semaphore (default: 2). | MUST |

### 4.5 Theory Specialist (RAG) Agent

| ID | Cerință | Prioritate |
|----|---------|------------|
| **FR-RAG-001** | Agentul TREBUIE să suporte ingestia documentelor PDF, Markdown și Text. | MUST |
| **FR-RAG-002** | Agentul TREBUIE să stocheze embeddings în ChromaDB cu persistență. | MUST |
| **FR-RAG-003** | Agentul TREBUIE să utilizeze FastEmbed (BAAI/bge-small-en-v1.5) pentru vectorizare. | MUST |
| **FR-RAG-004** | Agentul TREBUIE să implementeze reranking cu cross-encoder (BAAI/bge-reranker-base). | MUST |
| **FR-RAG-005** | Agentul TREBUIE să mențină istoricul conversațiilor cu context tracking. | MUST |
| **FR-RAG-006** | Agentul TREBUIE să returneze surse (citări) pentru fiecare răspuns generat. | MUST |
| **FR-RAG-007** | Agentul AR TREBUI să suporte hybrid retrieval (vector + BM25). | SHOULD |
| **FR-RAG-008** | Agentul TREBUIE să suporte multiple LLM providers (Ollama, OpenAI, Gemini). | MUST |
| **FR-RAG-009** | Agentul TREBUIE să permită auto-ingestia documentelor noi din folder monitorizat. | MUST |
| **FR-RAG-010** | Agentul AR TREBUI să permită selectarea direct_rag pentru bypass LLM. | SHOULD |

### 4.6 Command Executor Agent

| ID | Cerință | Prioritate |
|----|---------|------------|
| **FR-CMD-001** | Agentul TREBUIE să suporte operațiuni de encoding: Base64, Hex. | MUST |
| **FR-CMD-002** | Agentul TREBUIE să suporte hashing: SHA-256/384/512, SHA3, BLAKE2, MD5, HMAC. | MUST |
| **FR-CMD-003** | Agentul TREBUIE să suporte criptare simetrică AES-CBC + HMAC (Encrypt-then-MAC). | MUST |
| **FR-CMD-004** | Agentul TREBUIE să suporte criptare asimetrică RSA cu OAEP padding. | MUST |
| **FR-CMD-005** | Agentul TREBUIE să suporte semnături post-quantum (ML-DSA/Dilithium, Falcon). | MUST |
| **FR-CMD-006** | Agentul TREBUIE să valideze toate inputurile contra injection attacks. | MUST |
| **FR-CMD-007** | Agentul TREBUIE să redacteze secretele din logs/erori. | MUST |
| **FR-CMD-008** | Agentul TREBUIE să returneze comanda OpenSSL executată (scop educațional). | MUST |
| **FR-CMD-009** | Agentul TREBUIE să implementeze timeout per operație (default: 30s). | MUST |
| **FR-CMD-010** | Agentul TREBUIE să raporteze disponibilitatea PQC provider la /pqc/health. | MUST |

### 4.7 Choice Maker (NLP) Agent

| ID | Cerință | Prioritate |
|----|---------|------------|
| **FR-NLP-001** | Agentul TREBUIE să clasifice intenția utilizatorului cu confidence score. | MUST |
| **FR-NLP-002** | Agentul TREBUIE să extragă entități relevante (numere, algoritmi, parole, chei). | MUST |
| **FR-NLP-003** | Agentul TREBUIE să utilizeze SecureBERT 2.0 pentru clasificare. | MUST |
| **FR-NLP-004** | Agentul TREBUIE să suporte minim 10 clase de intenție (encrypt, decrypt, hash, etc.). | MUST |
| **FR-NLP-005** | Agentul TREBUIE să returneze threshold de confidence configurabil. | MUST |
| **FR-NLP-006** | Agentul AR TREBUI să detecteze cereri ambigue și să solicite clarificare. | SHOULD |
| **FR-NLP-007** | Agentul TREBUIE să proceseze cereri în limba engleză. | MUST |
| **FR-NLP-008** | Agentul AR TREBUI să suporte input multilingv cu traducere automată. | MAY |

### 4.8 Cryptosystem Detection Agent

| ID | Cerință | Prioritate |
|----|---------|------------|
| **FR-CRY-001** | Agentul TREBUIE să detecteze tipul de criptosistem din ciphertext. | MUST |
| **FR-CRY-002** | Agentul TREBUIE să integreze CyberChef Magic detector. | MUST |
| **FR-CRY-003** | Agentul AR TREBUI să integreze euristici inspirate din dcode.fr. | SHOULD |
| **FR-CRY-004** | Agentul TREBUIE să agregeze rezultatele de la mai mulți detectori. | MUST |
| **FR-CRY-005** | Agentul TREBUIE să returneze scor de incredere (0-1) pentru fiecare detecție, similar dcode.fr. | MUST |
| **FR-CRY-006** | Agentul TREBUIE să returneze top N candidați ordonați după scor (N configurabil). | MUST |

### 4.9 Hash Breaker Agent

| ID | Cerință | Prioritate |
|----|---------|------------|
| **FR-HSH-001** | Agentul TREBUIE să suporte spargerea hash-urilor MD5, SHA1, SHA256, bcrypt, NTLM. | MUST |
| **FR-HSH-002** | Agentul TREBUIE să integreze Hashcat pentru atacuri GPU-accelerate. | MUST |
| **FR-HSH-003** | Agentul TREBUIE să suporte atacuri pe dicționar cu wordlist-uri configurabile. | MUST |
| **FR-HSH-004** | Agentul TREBUIE să suporte atacuri bazate pe reguli (rule-based). | MUST |
| **FR-HSH-005** | Agentul AR TREBUI să suporte atacuri combinator și mask attack. | SHOULD |
| **FR-HSH-006** | Agentul TREBUIE să integreze PassGPT pentru generare candidată inteligentă. | MUST |
| **FR-HSH-007** | Agentul TREBUIE să returneze parola găsită, timpul de spargere și metoda folosită. | MUST |
| **FR-HSH-008** | Agentul TREBUIE să implementeze timeout configurabil (default: 5 minute). | MUST |
| **FR-HSH-009** | Agentul TREBUIE să suporte mod batch pentru mai multe hash-uri simultan. | MUST |
| **FR-HSH-010** | Agentul AR TREBUI să estimeze dificultatea hash-ului înainte de atac. | SHOULD |
| **FR-HSH-011** | Agentul TREBUIE să raporteze progresul atacului în timp real. | MUST |
| **FR-HSH-012** | Agentul TREBUIE să gestioneze concurența GPU cu semaphore. | MUST |

### 4.10 CTF Tool Agent

| ID | Cerință | Prioritate |
|----|---------|------------|
| **FR-CTF-001** | Agentul TREBUIE să suporte analiză steganografică pentru imagini (PNG, JPEG, BMP). | MUST |
| **FR-CTF-002** | Agentul TREBUIE să integreze instrumente standard: steghide, zsteg, exiftool. | MUST |
| **FR-CTF-003** | Agentul TREBUIE să suporte extracție metadate din fișiere (EXIF, IPTC, XMP). | MUST |
| **FR-CTF-004** | Agentul AR TREBUI să suporte analiză forensică de bază (strings, binwalk, file carving). | SHOULD |
| **FR-CTF-005** | Agentul TREBUIE să suporte decodare automată multi-nivel (Base64, ROT13, XOR). | MUST |
| **FR-CTF-006** | Agentul AR TREBUI să suporte analiză de fișiere binare (hex dump, magic bytes). | SHOULD |
| **FR-CTF-007** | Agentul TREBUIE să suporte identificare flag-uri CTF cu pattern matching. | MUST |
| **FR-CTF-008** | Agentul AR TREBUI să ofere hint-uri contextuale bazate pe tipul challenge-ului. | SHOULD |
| **FR-CTF-009** | Agentul TREBUIE să suporte upload fișiere pentru analiză (limită: 10MB). | MUST |
| **FR-CTF-010** | Agentul TREBUIE să returneze rezultatele într-un format structurat cu explicații. | MUST |
| **FR-CTF-011** | Agentul AR TREBUI să suporte analiză audio pentru steganografie. | MAY |
| **FR-CTF-012** | Agentul TREBUIE să șteargă fișierele uploadate după procesare (securitate). | MUST |

### 4.11 Data & Conversation Management

| ID | Cerință | Prioritate |
|----|---------|------------|
| **FR-DAT-001** | Sistemul TREBUIE să stocheze istoricul conversațiilor per utilizator. | MUST |
| **FR-DAT-002** | Sistemul TREBUIE să permită reluarea conversațiilor anterioare. | MUST |
| **FR-DAT-003** | Sistemul TREBUIE să permită exportul rezultatelor în JSON. | MUST |
| **FR-DAT-004** | Sistemul AR TREBUI să permită exportul rapoartelor în PDF. | SHOULD |
| **FR-DAT-005** | Sistemul TREBUIE să implementeze TTL configurabil pentru cache (default: 1h). | MUST |
| **FR-DAT-006** | Sistemul TREBUIE să permită ștergerea datelor utilizatorului la cerere (GDPR). | MUST |
| **FR-DAT-007** | Sistemul TREBUIE să anonimizeze datele în log-uri. | MUST |
| **FR-DAT-008** | Sistemul AR TREBUI să implementeze backup automat al bazelor de date. | SHOULD |
| **FR-DAT-009** | Sistemul TREBUIE să definească retention policy pentru date (default: 90 zile). | MUST |
| **FR-DAT-010** | Sistemul AR TREBUI să permită exportul metadatelor conversațiilor. | SHOULD |

### 4.12 Administration & Audit

| ID | Cerință | Prioritate |
|----|---------|------------|
| **FR-ADM-001** | Sistemul TREBUIE să logheze toate acțiunile administrative în audit log. | MUST |
| **FR-ADM-002** | Sistemul TREBUIE să înregistreze timestamp, user ID, acțiune, resursa afectată, IP. | MUST |
| **FR-ADM-003** | Sistemul TREBUIE să ofere UI de administrare pentru utilizatori și roluri. | MUST |
| **FR-ADM-004** | Sistemul TREBUIE să ofere dashboard pentru management API keys. | MUST |
| **FR-ADM-005** | Sistemul TREBUIE să implementeze rate limiting configurabil per endpoint. | MUST |
| **FR-ADM-006** | Sistemul TREBUIE să implementeze quota per utilizator/API key. | MUST |
| **FR-ADM-007** | Sistemul AR TREBUI să alerteze la pattern-uri anormale (brute force, anomalii). | SHOULD |
| **FR-ADM-008** | Sistemul TREBUIE să permită configurări centralizate per mediu (dev/staging/prod). | MUST |
| **FR-ADM-009** | Sistemul TREBUIE să păstreze audit log-ul minim 5 ani. | MUST |
| **FR-ADM-010** | Sistemul AR TREBUI să ofere export audit log în format SIEM-compatible. | SHOULD |

### 4.13 User Interface

| ID | Cerință | Prioritate |
|----|---------|------------|
| **FR-UI-001** | Interfața web TREBUIE să ofere input conversațional pentru cereri. | MUST |
| **FR-UI-002** | Interfața TREBUIE să afișeze rezultatele într-un format structurat și lizibil. | MUST |
| **FR-UI-003** | Interfața TREBUIE să afișeze sursele (citări) pentru răspunsurile RAG. | MUST |
| **FR-UI-004** | Interfața TREBUIE să permită navigarea între conversații anterioare. | MUST |
| **FR-UI-005** | Interfața TREBUIE să fie responsive pentru desktop, tabletă și mobil. | MUST |
| **FR-UI-006** | Interfața AR TREBUI să ofere mod întunecat (dark mode). | SHOULD |
| **FR-UI-007** | Interfața TREBUIE să afișeze status de loading pentru operații async. | MUST |
| **FR-UI-008** | Interfața TREBUIE să afișeze erori într-un mod user-friendly. | MUST |
| **FR-UI-009** | CLI-ul TREBUIE să ofere acces la toate funcționalitățile core. | MUST |
| **FR-UI-010** | CLI-ul AR TREBUI să suporte output în format JSON pentru scripting. | SHOULD |

---

## 5. Cerințe Non-Funcționale

### 5.1 Performanță

| ID | Cerință | Prioritate |
|----|---------|------------|
| **NFR-PRF-001** | Endpoint-urile lightweight (health, status) TREBUIE să răspundă în p95 < 100ms. | MUST |
| **NFR-PRF-002** | Clasificarea intenției (Choice Maker) TREBUIE să se finalizeze în p95 < 500ms. | MUST |
| **NFR-PRF-003** | Evaluarea parolei TREBUIE să se finalizeze în p95 < 2s. | MUST |
| **NFR-PRF-004** | Verificarea primalității pentru numere < 64 biți TREBUIE să fie < 100ms. | MUST |
| **NFR-PRF-005** | Operațiunile criptografice standard TREBUIE să se finalizeze în < 1s. | MUST |
| **NFR-PRF-006** | Generarea RAG TREBUIE să returneze răspuns în p95 < 10s (dependent de LLM). | MUST |
| **NFR-PRF-007** | Sistemul TREBUIE să suporte minim 100 de cereri concurente. | MUST |
| **NFR-PRF-008** | Sistemul AR TREBUI să suporte minim 500 de utilizatori concurenți activi. | SHOULD |
| **NFR-PRF-009** | Cache-ul TREBUIE să reducă latența pentru cereri repetitive cu minim 80%. | MUST |
| **NFR-PRF-010** | Operațiile heavy (factorizare, RAG extins) TREBUIE să fie async cu polling. | MUST |

### 5.2 Scalabilitate

| ID | Cerință | Prioritate |
|----|---------|------------|
| **NFR-SCL-001** | Arhitectura TREBUIE să permită scalare orizontală pentru toți agenții. | MUST |
| **NFR-SCL-002** | Sistemul TREBUIE să funcționeze corect cu minim 2 replici per agent critic. | MUST |
| **NFR-SCL-003** | Baza de date TREBUIE să suporte connection pooling eficient. | MUST |
| **NFR-SCL-004** | Sistemul AR TREBUI să implementeze auto-scaling pe bază de load în K8s. | SHOULD |
| **NFR-SCL-005** | Sistemul TREBUIE să gestioneze backpressure la cereri excesive. | MUST |

### 5.3 Fiabilitate

| ID | Cerință | Prioritate |
|----|---------|------------|
| **NFR-REL-001** | Disponibilitatea target pentru orchestrator și backend: ≥ 99.5%. | MUST |
| **NFR-REL-002** | Disponibilitatea target pentru agenți individuali: ≥ 99%. | MUST |
| **NFR-REL-003** | Sistemul TREBUIE să implementeze retry cu exponential backoff pentru dependențe externe. | MUST |
| **NFR-REL-004** | Sistemul TREBUIE să implementeze circuit breaker cu threshold configurabil. | MUST |
| **NFR-REL-005** | Sistemul TREBUIE să funcționeze în mod degradat când agenți non-critici sunt indisponibili. | MUST |
| **NFR-REL-006** | MTBF target pentru servicii critice: ≥ 720 ore. | SHOULD |
| **NFR-REL-007** | MTTR target: ≤ 30 minute. | SHOULD |
| **NFR-REL-008** | Backup-urile bazelor de date TREBUIE să fie automate și testate periodic. | MUST |
| **NFR-REL-009** | RTO (Recovery Time Objective): ≤ 4 ore. | MUST |
| **NFR-REL-010** | RPO (Recovery Point Objective): ≤ 1 oră. | MUST |

---

## 6. Quality of Service (QoS)

### 6.1 SLA Targets

| Metric | Target | Măsurare |
|--------|--------|----------|
| **Uptime** | 99.5% monthly | Prometheus + Alertmanager |
| **Response Time (p50)** | < 500ms | Grafana dashboard |
| **Response Time (p95)** | < 2s | Grafana dashboard |
| **Response Time (p99)** | < 5s | Grafana dashboard |
| **Error Rate** | < 0.1% | Error counters |
| **Throughput** | > 100 req/s | Rate metrics |

### 6.2 Observability

| ID | Cerință | Prioritate |
|----|---------|------------|
| **NFR-OBS-001** | Toate serviciile TREBUIE să expună metrici Prometheus pe /metrics. | MUST |
| **NFR-OBS-002** | Sistemul TREBUIE să colecteze metrici RED (Rate, Errors, Duration). | MUST |
| **NFR-OBS-003** | Sistemul TREBUIE să colecteze metrici USE (Utilization, Saturation, Errors). | MUST |
| **NFR-OBS-004** | Toate serviciile TREBUIE să emită loguri structurate (JSON). | MUST |
| **NFR-OBS-005** | Log-urile TREBUIE să includă: timestamp, level, service, trace_id, message. | MUST |
| **NFR-OBS-006** | Sistemul AR TREBUI să implementeze distributed tracing (OpenTelemetry). | SHOULD |
| **NFR-OBS-007** | Sistemul TREBUIE să ofere dashboards Grafana pentru monitorizare. | MUST |
| **NFR-OBS-008** | Sistemul TREBUIE să configureze alerting pentru metrici critice. | MUST |
| **NFR-OBS-009** | Alertele critice TREBUIE să fie notificate în < 5 minute de la incident. | MUST |
| **NFR-OBS-010** | Sistemul AR TREBUI să implementeze anomaly detection pentru pattern-uri neobișnuite. | SHOULD |

### 6.3 Maintenance Windows

| Tip | Fereastră | Notificare |
|-----|-----------|------------|
| Planned Maintenance | Duminică 02:00-06:00 UTC | 72h în avans |
| Emergency Maintenance | Oricând | ASAP |
| Security Patches | Vineri 22:00-02:00 UTC | 24h în avans |

---

## 7. Cerințe AI/ML

### 7.1 Model Specification

| ID | Cerință | Prioritate |
|----|---------|------------|
| **ML-MOD-001** | PassGPT TREBUIE să utilizeze model pre-antrenat (javirandor/passgpt-10characters). | MUST |
| **ML-MOD-002** | SecureBERT TREBUIE să utilizeze versiunea 2.0 pentru clasificare. | MUST |
| **ML-MOD-003** | Embedding model pentru RAG TREBUIE să fie BAAI/bge-small-en-v1.5. | MUST |
| **ML-MOD-004** | Reranker TREBUIE să fie BAAI/bge-reranker-base (ONNX). | MUST |
| **ML-MOD-005** | Toate modelele TREBUIE să aibă checksum verificat la încărcare. | MUST |
| **ML-MOD-006** | Modelele TREBUIE să fie versionate și etichetate în registry. | MUST |

### 7.2 Data Management

| ID | Cerință | Prioritate |
|----|---------|------------|
| **ML-DAT-001** | Documentele ingestate TREBUIE să fie clasificate și etichetate. | MUST |
| **ML-DAT-002** | Sistemul TREBUIE să păstreze metadata pentru fiecare document. | MUST |
| **ML-DAT-003** | Sistemul AR TREBUI să permită actualizarea incrementală a vectorilor. | SHOULD |
| **ML-DAT-004** | Sistemul TREBUIE să permită ștergerea selectivă din vector store. | MUST |
| **ML-DAT-005** | Dataset-urile de antrenament TREBUIE să fie documentate și versionate. | MUST |

### 7.3 Guardrails & Safety

| ID | Cerință | Prioritate |
|----|---------|------------|
| **ML-GRD-001** | Sistemul TREBUIE să valideze inputul înainte de procesare ML. | MUST |
| **ML-GRD-002** | Sistemul TREBUIE să limiteze lungimea inputului acceptat (context window). | MUST |
| **ML-GRD-003** | Sistemul TREBUIE să filtreze output-urile pentru conținut harmful. | MUST |
| **ML-GRD-004** | Sistemul TREBUIE să implementeze limită de acțiuni per sesiune. | MUST |
| **ML-GRD-005** | Sistemul AR TREBUI să detecteze și să blocheze prompt injection attempts. | SHOULD |
| **ML-GRD-006** | Sistemul NU TREBUIE să expună informații sensibile prin model outputs. | MUST |

### 7.4 Model Lifecycle (MLOps)

| ID | Cerință | Prioritate |
|----|---------|------------|
| **ML-OPS-001** | Sistemul TREBUIE să suporte blue-green deployment pentru modele. | MUST |
| **ML-OPS-002** | Sistemul TREBUIE să monitorizeze drift-ul modelelor. | MUST |
| **ML-OPS-003** | Sistemul AR TREBUI să implementeze A/B testing pentru modele noi. | SHOULD |
| **ML-OPS-004** | Sistemul TREBUIE să permită rollback rapid la versiunea anterioară. | MUST |
| **ML-OPS-005** | Sistemul TREBUIE să păstreze metrici de performanță per versiune model. | MUST |

### 7.5 Ethics & Transparency

| ID | Cerință | Prioritate |
|----|---------|------------|
| **ML-ETH-001** | Sistemul TREBUIE să informeze utilizatorii că răspunsurile sunt generate de AI. | MUST |
| **ML-ETH-002** | Sistemul TREBUIE să ofere confidence scores pentru predicții. | MUST |
| **ML-ETH-003** | Sistemul AR TREBUI să documenteze limitările cunoscute ale modelelor. | SHOULD |
| **ML-ETH-004** | Sistemul NU TREBUIE să pretindă certitudine pentru rezultate probabilistice. | MUST |

---

## 8. Cerințe de Securitate

### 8.1 Transport Security

| ID | Cerință | Prioritate |
|----|---------|------------|
| **SR-TLS-001** | Toate comunicațiile externe TREBUIE să utilizeze TLS 1.2+. | MUST |
| **SR-TLS-002** | Comunicațiile inter-servicii în producție TREBUIE să utilizeze mTLS. | MUST |
| **SR-TLS-003** | Certificatele TREBUIE să aibă minimum 2048-bit RSA sau ECDSA P-256. | MUST |
| **SR-TLS-004** | Sistemul TREBUIE să implementeze certificate rotation automată. | MUST |
| **SR-TLS-005** | Sistemul TREBUIE să forțeze HSTS cu max-age ≥ 1 an. | MUST |

### 8.2 Data Security

| ID | Cerință | Prioritate |
|----|---------|------------|
| **SR-DAT-001** | Datele sensibile at-rest TREBUIE să fie criptate (AES-256-GCM). | MUST |
| **SR-DAT-002** | Parolele TREBUIE să fie hashuite cu bcrypt/Argon2 (cost ≥ 12). | MUST |
| **SR-DAT-003** | API keys TREBUIE să fie stocate hashuite, afișate o singură dată. | MUST |
| **SR-DAT-004** | Secretele NU TREBUIE să fie stocate în cod sau imagini container. | MUST |
| **SR-DAT-005** | Sistemul TREBUIE să utilizeze secrets management (Vault/K8s Secrets). | MUST |
| **SR-DAT-006** | Log-urile NU TREBUIE să conțină date sensibile în clar. | MUST |
| **SR-DAT-007** | Baza de date TREBUIE să fie accesibilă doar din rețeaua internă. | MUST |

### 8.3 Input Validation & Injection Prevention

| ID | Cerință | Prioritate |
|----|---------|------------|
| **SR-INJ-001** | Sistemul TREBUIE să prevină SQL Injection prin parametrizare. | MUST |
| **SR-INJ-002** | Sistemul TREBUIE să prevină Command Injection prin validare strictă. | MUST |
| **SR-INJ-003** | Sistemul TREBUIE să prevină XSS prin sanitizare input și output encoding. | MUST |
| **SR-INJ-004** | Sistemul TREBUIE să prevină CSRF prin token-uri per sesiune. | MUST |
| **SR-INJ-005** | Sistemul TREBUIE să prevină Path Traversal cu validare și sandboxing. | MUST |
| **SR-INJ-006** | Sistemul TREBUIE să implementeze allowlist pentru algoritmi și operațiuni. | MUST |
| **SR-INJ-007** | Sistemul TREBUIE să valideze toate inputurile server-side. | MUST |
| **SR-INJ-008** | Sistemul TREBUIE să implementeze request size limits (default: 1MB). | MUST |

### 8.4 Access Control

| ID | Cerință | Prioritate |
|----|---------|------------|
| **SR-ACC-001** | Sistemul TREBUIE să implementeze principiul privilegiilor minime. | MUST |
| **SR-ACC-002** | Sistemul TREBUIE să verifice autorizarea pentru fiecare cerere. | MUST |
| **SR-ACC-003** | Sistemul TREBUIE să implementeze rate limiting per IP și per user. | MUST |
| **SR-ACC-004** | Sistemul TREBUIE să blocheze conturile după 5 încercări eșuate (30 min). | MUST |
| **SR-ACC-005** | Sistemul AR TREBUI să implementeze IP reputation și blacklisting. | SHOULD |
| **SR-ACC-006** | Sistemul AR TREBUI să detecteze și să blocheze brute force attacks. | SHOULD |

### 8.5 Security Headers

| ID | Cerință | Prioritate |
|----|---------|------------|
| **SR-HDR-001** | Sistemul TREBUIE să seteze Content-Security-Policy restrictiv. | MUST |
| **SR-HDR-002** | Sistemul TREBUIE să seteze X-Frame-Options: DENY. | MUST |
| **SR-HDR-003** | Sistemul TREBUIE să seteze X-Content-Type-Options: nosniff. | MUST |
| **SR-HDR-004** | Sistemul TREBUIE să seteze Referrer-Policy: strict-origin-when-cross-origin. | MUST |
| **SR-HDR-005** | Sistemul TREBUIE să configureze CORS restrictiv (nu wildcard în producție). | MUST |

### 8.6 Audit & Incident Response

| ID | Cerință | Prioritate |
|----|---------|------------|
| **SR-AUD-001** | Sistemul TREBUIE să logheze toate accesele la resurse sensibile. | MUST |
| **SR-AUD-002** | Sistemul TREBUIE să logheze toate operațiunile administrative. | MUST |
| **SR-AUD-003** | Sistemul TREBUIE să păstreze audit logs imutabile pentru investigații. | MUST |
| **SR-AUD-004** | Sistemul AR TREBUI să alerteze la comportament suspect (anomalii). | SHOULD |
| **SR-AUD-005** | Sistemul TREBUIE să permită investigație și forensics post-incident. | MUST |
| **SR-AUD-006** | Sistemul AR TREBUI să ofere export pentru SIEM integration. | SHOULD |

---

## 9. Cerințe de Infrastructură și DevOps

### 9.1 Containerization & Orchestration

| ID | Cerință | Prioritate |
|----|---------|------------|
| **INF-K8S-001** | Sistemul TREBUIE să ruleze în Kubernetes cu namespace segregation. | MUST |
| **INF-K8S-002** | Sistemul TREBUIE să definească resource limits pentru toate container-ele. | MUST |
| **INF-K8S-003** | Sistemul TREBUIE să implementeze network policies pentru izolare. | MUST |
| **INF-K8S-004** | Sistemul TREBUIE să utilizeze non-root containers. | MUST |
| **INF-K8S-005** | Sistemul TREBUIE să implementeze pod security standards. | MUST |
| **INF-K8S-006** | Sistemul AR TREBUI să utilizeze service mesh (Istio/Linkerd). | SHOULD |
| **INF-K8S-007** | Sistemul TREBUIE să implementeze health checks (liveness/readiness). | MUST |
| **INF-K8S-008** | Sistemul AR TREBUI să suporte horizontal pod autoscaling. | SHOULD |

### 9.2 CI/CD Pipeline

| ID | Cerință | Prioritate |
|----|---------|------------|
| **INF-CIC-001** | Pipeline TREBUIE să execute build automat la fiecare commit. | MUST |
| **INF-CIC-002** | Pipeline TREBUIE să execute unit tests cu coverage ≥ 70%. | MUST |
| **INF-CIC-003** | Pipeline TREBUIE să execute static analysis (linters). | MUST |
| **INF-CIC-004** | Pipeline TREBUIE să execute security scanning (Trivy, Snyk). | MUST |
| **INF-CIC-005** | Pipeline TREBUIE să execute integration tests. | MUST |
| **INF-CIC-006** | Pipeline AR TREBUI să execute SAST și DAST. | SHOULD |
| **INF-CIC-007** | Pipeline TREBUIE să genereze și să publice imagini cu tag semantic. | MUST |
| **INF-CIC-008** | Pipeline TREBUIE să implementeze deployment automat în staging. | MUST |
| **INF-CIC-009** | Pipeline AR TREBUI să suporte canary deployments în producție. | SHOULD |
| **INF-CIC-010** | Pipeline TREBUIE să permită rollback rapid (< 5 minute). | MUST |

### 9.3 Deployment & Portability

| ID | Cerință | Prioritate |
|----|---------|------------|
| **INF-DEP-001** | Sistemul TREBUIE să suporte deployment on-premise. | MUST |
| **INF-DEP-002** | Sistemul AR TREBUI să suporte deployment în cloud (AWS/GCP/Azure). | SHOULD |
| **INF-DEP-003** | Sistemul TREBUIE să funcționeze pe Linux (Ubuntu 22.04+, Debian 12+). | MUST |
| **INF-DEP-004** | Sistemul AR TREBUI să suporte air-gapped deployment. | SHOULD |
| **INF-DEP-005** | Configurația TREBUIE să fie externalizată prin env vars/ConfigMaps. | MUST |
| **INF-DEP-006** | Sistemul TREBUIE să ofere documentație completă pentru deployment. | MUST |

---

### 9.4 Operational Readiness (Production)

| ID | Cerință | Prioritate |
|----|---------|------------|
| **INF-OPS-001** | Sistemul TREBUIE să aibă runbook-uri pentru incident response și operațiuni critice. | MUST |
| **INF-OPS-002** | Procedurile de backup și restore TREBUIE să fie documentate și testate periodic. | MUST |
| **INF-OPS-003** | Sistemul TREBUIE să aibă plan de disaster recovery cu RTO/RPO validate. | MUST |
| **INF-OPS-004** | Audit log-urile TREBUIE să fie protejate împotriva modificării și accesate doar cu roluri dedicate. | MUST |
| **INF-OPS-005** | Release-urile TREBUIE să treacă prin quality gates (teste, scanări, verificări de securitate). | MUST |
| **INF-OPS-006** | Sistemul TREBUIE să efectueze audit de securitate periodic (cel puțin anual sau per release major). | MUST |
| **INF-OPS-007** | Alertele critice TREBUIE să fie rutate către un canal de on-call. | MUST |

---

## 10. Cerințe de Conformitate

### 10.1 Security Standards

| ID | Cerință | Prioritate |
|----|---------|------------|
| **CMP-SEC-001** | Sistemul TREBUIE să respecte OWASP Top 10 (2021). | MUST |
| **CMP-SEC-002** | Sistemul AR TREBUI să respecte CIS Benchmarks pentru containerizare. | SHOULD |
| **CMP-SEC-003** | Sistemul AR TREBUI să respecte NIST Cybersecurity Framework. | SHOULD |
| **CMP-SEC-004** | Operațiunile criptografice AR TREBUI să respecte NIST SP 800-57. | SHOULD |
| **CMP-SEC-005** | Post-quantum crypto AR TREBUI să respecte NIST PQC standards. | SHOULD |

### 10.2 Data Protection

| ID | Cerință | Prioritate |
|----|---------|------------|
| **CMP-GDP-001** | Sistemul TREBUIE să permită exercitarea dreptului la ștergere (Art. 17 GDPR). | MUST |
| **CMP-GDP-002** | Sistemul TREBUIE să permită exportul datelor personale (Art. 20 GDPR). | MUST |
| **CMP-GDP-003** | Sistemul TREBUIE să documenteze fluxurile de date personale. | MUST |
| **CMP-GDP-004** | Sistemul TREBUIE să minimizeze colectarea datelor (Art. 5 GDPR). | MUST |
| **CMP-GDP-005** | Sistemul AR TREBUI să implementeze pseudonimizare unde posibil. | SHOULD |

### 10.3 Licensing & Open Source

| ID | Cerință | Prioritate |
|----|---------|------------|
| **CMP-LIC-001** | Proiectul TREBUIE să fie licențiat sub MIT License. | MUST |
| **CMP-LIC-002** | Sistemul TREBUIE să documenteze toate dependențele și licențele lor. | MUST |
| **CMP-LIC-003** | Sistemul NU TREBUIE să includă dependențe cu licențe incompatibile. | MUST |
| **CMP-LIC-004** | Sistemul TREBUIE să ofere SBOM (Software Bill of Materials). | MUST |

---

## 11. Verificare și Validare

### 11.1 Matrice de Verificare

| Requirement ID | Metoda Verificare | Criteriu Acceptare | Artifact |
|----------------|-------------------|-------------------|----------|
| FR-IAM-001 | Test Integration | User poate înregistra cont și primește email | Test suite |
| FR-IAM-003 | Test Manual | MFA funcțional pentru admin | QA checklist |
| FR-ORC-002 | Test Unit + Integration | Routing corect pentru 10+ intenții | Test coverage |
| FR-PWD-001 | Test Unit | Scor calculat corect pentru 100 parole test | Test suite |
| NFR-PRF-001 | Load Test | p95 < 100ms la 100 req/s | k6 report |
| NFR-REL-001 | Monitoring | Uptime ≥ 99.5% pe 30 zile | Prometheus |
| SR-TLS-001 | Security Scan | SSL Labs grade A | SSLLabs report |
| ML-MOD-005 | Automated Check | Checksum match pentru toate modelele | CI pipeline |

### 11.2 Tipuri de Testare

| Tip Test | Scop | Tool-uri | Frecvență |
|----------|------|----------|-----------|
| Unit Tests | Logică individuală | pytest, go test, cargo test | Per commit |
| Integration Tests | Interacțiune servicii | pytest, testcontainers | Per PR |
| E2E Tests | Flow complet utilizator | Playwright, Cypress | Daily |
| Load Tests | Performanță sub load | k6, locust | Weekly |
| Security Tests | Vulnerabilități | OWASP ZAP, Trivy | Per PR + Weekly |
| Chaos Tests | Resilience | chaos-monkey | Monthly |

---

## 12. Recomandări pentru Document

### 12.1 Structura Recomandată

✅ **Adoptă** structura din `srs-template-bare.md` - este modernă și comprehensivă.

✅ **Modifică** fișierul `srs_platforma_management.tex` păstrând formatul LaTeX dar actualizând conținutul pentru Vitruvian Cipher.

✅ **Include** toate secțiunile din acest document, în special:
- Cerințele AI/ML (secțiunea 3.6) - critice pentru acest tip de proiect
- Quality of Service cu metrici concrete
- Matricea de verificare

### 12.2 Convenții de Numerotare

```
FR-XXX-NNN    Cerințe Funcționale (FR = Functional Requirement)
              XXX = Modul (IAM, ORC, PWD, PRM, RAG, CMD, NLP, CRY, DAT, ADM, UI)
              NNN = Număr secvențial (001-999)

NFR-XXX-NNN   Cerințe Non-Funcționale
              XXX = Categorie (PRF=Performance, SCL=Scalability, REL=Reliability, OBS=Observability)

SR-XXX-NNN    Cerințe de Securitate
              XXX = Categorie (TLS, DAT, INJ, ACC, HDR, AUD)

ML-XXX-NNN    Cerințe AI/ML
              XXX = Categorie (MOD=Model, DAT=Data, GRD=Guardrails, OPS=MLOps, ETH=Ethics)

INF-XXX-NNN   Cerințe Infrastructură
              XXX = Categorie (K8S, CIC=CI/CD, DEP=Deployment)

CMP-XXX-NNN   Cerințe Conformitate
              XXX = Categorie (SEC=Security, GDP=GDPR, LIC=Licensing)
```

### 12.3 Limba RFC 2119

| Termen | LaTeX Macro | Semnificație |
|--------|-------------|--------------|
| **TREBUIE** | `\reqshall` | Obligatoriu, must-have |
| **AR TREBUI** | `\reqshould` | Recomandat, should-have |
| **POATE** | `\reqmay` | Opțional, nice-to-have |

### 12.4 Elemente Adiționale pentru SRS

1. **Diagrame UML**:
   - Use Case Diagrams per actor
   - Sequence Diagrams pentru fluxuri critice
   - Activity Diagrams pentru fluxuri asincrone și orchestrare
   - State Diagrams pentru lifecycle (job-uri, sesiuni, token-uri)
   - Component Diagram pentru arhitectură
   - Deployment Diagram pentru infrastructură K8s

2. **API Specification** (Anexă):
   - OpenAPI 3.0 spec pentru toate endpoint-urile
   - gRPC proto files

3. **Trust Boundaries Diagram**:
   - Vizualizare clară a graniței intern/extern
   - Zonele de securitate

4. **Data Flow Diagrams**:
   - DFD pentru fluxurile principale
   - Identificarea datelor sensibile

5. **Threat Model Summary**:
   - STRIDE analysis pentru componente critice
   - Top 10 riscuri identificate

### 12.5 Glosar Specific Proiect

| Termen | Definiție |
|--------|-----------|
| Agent | Microserviciu specializat care îndeplinește o funcție specifică |
| RAG | Retrieval-Augmented Generation - tehnică de augmentare a LLM-urilor |
| PQC | Post-Quantum Cryptography - algoritmi rezistenți la atacuri cuantice |
| HIBP | Have I Been Pwned - serviciu de verificare parole compromise |
| YAFU | Yet Another Factorization Utility - tool pentru factorizare |
| mTLS | Mutual TLS - autentificare bidirecțională prin certificate |
| Circuit Breaker | Pattern de resilience pentru gestionarea eșecurilor |
| Ensemble | Combinație de mai multe modele ML pentru predicție îmbunătățită |
| ChromaDB | Bază de date vectorială pentru embeddings |
| FastEmbed | Bibliotecă pentru generare rapidă de embeddings |

---

## 13. Model de Amenințări (Analiză STRIDE)

### 13.1 Diagrama Granițelor de Încredere

> **📐 Instrucțiuni Diagramă UML - Deployment Diagram cu Trust Boundaries**
>
> Creează o **diagramă de deployment UML** cu 6 zone (noduri) separate de granițe de încredere:
>
> **Zone (de sus în jos):**
>
> 1. **«node» Zonă Externă** (fundal roșu deschis, stereotip `<<untrusted>>`)
>    - Componente: `Navigator`, `Client CLI`, `Consumatori API Terți`
>    - Pictograme: actor uman + terminal
>
> 2. **─── GÎ1: Internet ───** (linie întreruptă roșie, etichetă "TLS obligatoriu, WAF")
>
> 3. **«node» Zonă DMZ** (fundal portocaliu deschis)
>    - `WAF / Proxy Invers (Nginx/Traefik)` - notă: "Terminare TLS, Limitare Rată"
>    - `Frontend React (Static)`
>
> 4. **─── GÎ2: DMZ/Aplicație ───** (linie întreruptă, etichetă "Autentificare necesară")
>
> 5. **«node» Zonă Aplicație** (fundal galben deschis)
>    - `API Backend Go` - notă: "Auth, RBAC, Audit, Rate Limit"
>    - `Orchestrator` - notă: "Rutare Intenții"
>
> 6. **─── GÎ3: Aplicație/Agenți ───** (linie întreruptă, etichetă "mTLS, doar intern")
>
> 7. **«node» Zonă Agenți** (fundal verde deschis, stereotip `<<isolated>>`)
>    - 9 componente în grilă 3×3:
>      - `Verificare Parole`, `Verificare Primalitate`, `Specialist Teorie`
>      - `Executor Comenzi`, `Selector Alegeri`, `Detectare Criptosistem`
>      - `Spărgător Hash`, `Instrument CTF`, (slot liber sau Orchestrator intern)
>
> 8. **─── GÎ4: Agenți/Date ───** (linie întreruptă, etichetă "Credențiale, connection pooling")
>
> 9. **«node» Zonă Date** (fundal albastru deschis, stereotip `<<restricted>>`)
>    - `PostgreSQL (Utilizatori, Audit)`, `Redis Cache (Sesiuni)`, `ChromaDB (Embeddings)`
>
> 10. **─── GÎ5: API-uri Externe ───** (linie întreruptă, etichetă "TLS, chei API, timeout-uri")
>
> 11. **«node» Dependențe Externe** (fundal gri, stereotip `<<external>>`)
>     - `API HIBP`, `FactorDB`, `API-uri LLM`, `Modele Hugging Face`
>
> **Stil**: Folosește culori diferite pentru fiecare zonă. Granițele de încredere (GÎ1-GÎ5) sunt linii orizontale întrerupte cu etichete.

**Legendă Granițe de Încredere (GÎ):**
- **GÎ1**: Internet ↔ DMZ (TLS obligatoriu, WAF)
- **GÎ2**: DMZ ↔ Aplicație (Autentificare necesară)
- **GÎ3**: Aplicație ↔ Agenți (mTLS, doar intern)
- **GÎ4**: Agenți ↔ Date (Connection pooling, credențiale)
- **GÎ5**: Intern ↔ API-uri Externe (TLS, chei API, timeout-uri)

---

### 13.2 Analiză STRIDE per Componentă

#### 13.2.1 Nivel Frontend (React)

| Amenințare | Categorie | Risc | Mitigare |
|------------|-----------|------|----------|
| XSS prin input utilizator | **F**alsificare | RIDICAT | CSP strict, codificare output, sanitizare input |
| Deturnare sesiune | **U**zurpare | RIDICAT | Cookie-uri HttpOnly, flag Secure, SameSite=Strict |
| Clickjacking | **F**alsificare | MEDIU | X-Frame-Options: DENY |
| CSRF | **U**zurpare | MEDIU | Token-uri CSRF, cookie-uri SameSite |
| Date sensibile în localStorage | **D**ivulgare Info | MEDIU | Stocare token-uri în memorie/cookie-uri httpOnly |

#### 13.2.2 API Backend (Go)

| Amenințare | Categorie | Risc | Mitigare |
|------------|-----------|------|----------|
| Autentificare brute force | **U**zurpare | RIDICAT | Limitare rată (5/min), blocare cont |
| Furt/replay JWT | **U**zurpare | RIDICAT | TTL scurt (15min), rotație refresh, blacklist |
| Injecție SQL | **F**alsificare | CRITIC | Doar interogări parametrizate |
| Escaladare privilegii | **E**scaladare | RIDICAT | Aplicare RBAC, validare input |
| Manipulare log-uri audit | **R**epudiere | MEDIU | Log-uri append-only, DB audit separat |
| DoS prin payload-uri mari | **D**oS | MEDIU | Limite dimensiune cereri (1MB), timeout-uri |

#### 13.2.3 Orchestrator

| Amenințare | Categorie | Risc | Mitigare |
|------------|-----------|------|----------|
| Uzurpare identitate agent | **U**zurpare | RIDICAT | mTLS între servicii |
| Manipulare intenții | **F**alsificare | MEDIU | Validare output Choice Maker, verificări prag |
| Epuizare resurse | **D**oS | RIDICAT | Circuit breaker, timeout-uri, semafoare |
| Injecție prompt LLM | **F**alsificare | RIDICAT | Sanitizare input, filtrare output |
| Scurgeri goroutine | **D**oS | MEDIU | Anulare context, curățare corespunzătoare |

#### 13.2.4 Agent Verificare Parole

| Amenințare | Categorie | Risc | Mitigare |
|------------|-----------|------|----------|
| Logare parole | **D**ivulgare Info | CRITIC | Nu se logează niciodată parole, redactare în erori |
| Atacuri de timing | **D**ivulgare Info | SCĂZUT | Comparații în timp constant (nu se aplică aici) |
| Otrăvire model | **F**alsificare | MEDIU | Verificare checksum, modele imutabile |
| Expunere date HIBP | **D**ivulgare Info | SCĂZUT | k-anonimitate (doar prefix trimis) |

#### 13.2.5 Executor Comenzi (Rust)

| Amenințare | Categorie | Risc | Mitigare |
|------------|-----------|------|----------|
| Injecție comenzi | **F**alsificare | CRITIC | Fără shell, argumente separate, allowlist |
| Traversare cale | **F**alsificare | RIDICAT | Sandbox fișiere temporare, validare căi |
| Expunere material cheie | **D**ivulgare Info | CRITIC | Redactare secrete în log-uri, memorie securizată |
| Module OpenSSL malițioase | **F**alsificare | RIDICAT | Validare variabile env, căi fixe |
| Atacuri oracle cripto | **D**ivulgare Info | MEDIU | Encrypt-then-MAC, HMAC în timp constant |

#### 13.2.6 Agent Verificare Primalitate

| Amenințare | Categorie | Risc | Mitigare |
|------------|-----------|------|----------|
| Injecție comenzi YAFU | **F**alsificare | RIDICAT | Validare input, fără shell |
| MITM FactorDB | **F**alsificare | MEDIU | Verificare TLS, certificate pinning |
| Epuizare resurse (numere mari) | **D**oS | RIDICAT | Limită max cifre (1000), timeout-uri |
| Otrăvire cache | **F**alsificare | MEDIU | Validare input înainte de cache |

#### 13.2.7 Specialist Teorie (RAG)

| Amenințare | Categorie | Risc | Mitigare |
|------------|-----------|------|----------|
| Traversare cale documente | **D**ivulgare Info | RIDICAT | Verificări symlink, chroot/sandbox |
| Injecție prompt prin documente | **F**alsificare | MEDIU | Sanitizare conținut ingerat |
| Manipulare model embeddings | **F**alsificare | RIDICAT | Verificare checksum |
| Scurgere date conversație | **D**ivulgare Info | MEDIU | Izolare utilizator, control acces |
| Halucinare LLM | **R**epudiere | SCĂZUT | Citare surse, scoruri de încredere |

#### 13.2.8 Agent Spărgător Hash (Hash Breaker)

| Amenințare | Categorie | Risc | Mitigare |
|------------|-----------|------|----------|
| Injecție comenzi Hashcat | **F**alsificare | CRITIC | Fără shell, argumente validate, allowlist |
| Epuizare resurse GPU | **D**oS | RIDICAT | Timeout-uri stricte, queue management |
| Exfiltrare parole sparte | **D**ivulgare Info | CRITIC | Criptare rezultate, ștergere automată |
| Wordlist injection | **F**alsificare | MEDIU | Validare path-uri, sandbox |
| Acces neautorizat la GPU | **E**scaladare | MEDIU | Izolare container, cgroups |

#### 13.2.9 Agent Instrument CTF (CTF Tool)

| Amenințare | Categorie | Risc | Mitigare |
|------------|-----------|------|----------|
| Upload fișiere malițioase | **F**alsificare | CRITIC | Validare MIME, limită 10MB, sandbox analiză |
| Path traversal prin filename | **F**alsificare | RIDICAT | Sanitizare nume fișiere, director izolat |
| Execuție cod arbitrar via binwalk | **E**scaladare | RIDICAT | Sandbox strict, forks limitate |
| Expunere date forensic | **D**ivulgare Info | MEDIU | Ștergere automată după procesare |
| Steganografie inversă (exfiltrare) | **D**ivulgare Info | SCĂZUT | Monitorizare output, limite dimensiune |

#### 13.2.10 Nivel Date

| Amenințare | Categorie | Risc | Mitigare |
|------------|-----------|------|----------|
| Furt credențiale bază de date | **U**zurpare | CRITIC | Management secrete (Vault/K8s Secrets) |
| Date necriptate în repaus | **D**ivulgare Info | RIDICAT | Criptare AES-256-GCM |
| Expunere backup-uri | **D**ivulgare Info | RIDICAT | Backup-uri criptate, stocare securizată |
| Expunere connection string | **D**ivulgare Info | RIDICAT | Variabile de mediu, nu în cod |

---

### 13.3 Top 10 Riscuri de Securitate (Prioritizate)

| Rang | Risc | Componentă | STRIDE | Probabilitate | Impact | Scor |
|------|------|------------|--------|---------------|--------|------|
| 1 | **Injecție Comenzi Hashcat** | Spărgător Hash | F | Medie | Critic | 🔴 9.5 |
| 2 | **Injecție Comenzi** | Executor Comenzi | F | Medie | Critic | 🔴 9.0 |
| 3 | **Upload Fișiere Malițioase** | CTF Tool | F | Ridicată | Critic | 🔴 8.8 |
| 4 | **Injecție SQL** | API Backend | F | Scăzută | Critic | 🔴 8.5 |
| 5 | **Logare Parole** | Verificare Parole | D | Medie | Critic | 🔴 8.5 |
| 6 | **Exfiltrare Parole Sparte** | Spărgător Hash | D | Medie | Critic | 🔴 8.5 |
| 7 | **Furt Token JWT** | API Backend | U | Medie | Ridicat | 🟠 7.5 |
| 8 | **Traversare Cale** | Specialist Teorie/CTF | D | Medie | Ridicat | 🟠 7.5 |
| 9 | **Injecție Prompt** | Orchestrator/RAG | F | Ridicată | Mediu | 🟠 7.0 |
| 10 | **DoS prin Input Mare** | Toți Agenții | D | Ridicată | Mediu | 🟠 6.5 |

---

### 13.4 Sumar Suprafață de Atac

| Punct de Intrare | Expus Către | Flux de Date | Controale |
|------------------|-------------|--------------|----------|
| HTTPS :443 | Internet | Utilizator → Frontend → Backend | WAF, TLS, Limitare Rată |
| API :8000 | Utilizatori Autentificați | Cereri → Backend → Orchestrator | JWT, RBAC, Audit |
| Orchestrator :8200 | Doar Backend | Backend → Orchestrator → Agenți | mTLS, Rețea Internă |
| Agenți :diverse | Doar Orchestrator | Orchestrator → Agent → Răspuns | mTLS, Timeout-uri |
| PostgreSQL :5432 | Doar Nivel Aplicație | Backend ↔ BD | Credențiale, SSL, Firewall |
| Redis :6379 | Doar Nivel Aplicație | Backend ↔ Cache | Parolă, Rețea Internă |
| API-uri Externe | Agenți (ieșire) | Agent → HIBP/FactorDB/LLM | TLS, Chei API, Timeout-uri |

---

### 13.5 Matrice Controale de Securitate

| Control | GÎ1 | GÎ2 | GÎ3 | GÎ4 | GÎ5 |
|---------|-----|-----|-----|-----|-----|
| TLS 1.2+ | ✅ | ✅ | ✅ | ✅ | ✅ |
| mTLS | ❌ | ❌ | ✅ | ✅ | ❌ |
| Autentificare | ❌ | ✅ | ✅ | ✅ | ✅ |
| Limitare Rată | ✅ | ✅ | ✅ | ❌ | ✅ |
| Validare Input | ✅ | ✅ | ✅ | ✅ | N/A |
| Criptare în Repaus | N/A | N/A | N/A | ✅ | N/A |
| Logare Audit | ✅ | ✅ | ✅ | ✅ | ✅ |
| Izolare Rețea | ✅ | ✅ | ✅ | ✅ | N/A |

---

### 13.6 Plan de Mitigare Amenințări

| Fază | Amenințări Adresate | Implementare |
|------|---------------------|---------------|
| **Faza 1 (MVP)** | Injecție SQL/Comenzi, XSS, CSRF, Logare Parole | Validare input, interogări parametrizate, CSP |
| **Faza 2 (Autentificare)** | Brute Force, Furt JWT, Escaladare Privilegii | RBAC, limitare rată, rotație token-uri |
| **Faza 3 (Întărire)** | mTLS, Traversare Cale, Manipulare Model | Service mesh, sandboxing, checksum-uri |
| **Faza 4 (Monitorizare)** | DoS, Anomalii, Manipulare Audit | Alertare, reguli WAF, log-uri append-only |

---

## 📎 Anexe Recomandate

1. **Anexa A**: Diagrame UML (Use Case, Sequence, Component, Deployment)
2. **Anexa B**: OpenAPI Specification
3. **Anexa C**: Data Dictionary
4. **Anexa D**: Security Threat Model
5. **Anexa E**: Deployment Architecture (K8s manifests summary)
6. **Anexa F**: Model Cards pentru componentele ML
7. **Anexa G**: SBOM (Software Bill of Materials)

---

**Document generat:** 4 Ianuarie 2026  
**Versiune:** 1.0  
**Autor:** GitHub Copilot (Claude Opus 4.5)  
**Pentru:** Sd. Sg. Maj. Moldovan Andrei - Proiect Licență ATM

---

> 💡 **Notă**: Acest document reprezintă o analiză comprehensivă și propuneri pentru SRS. Cerințele sunt formulate pe baza analizei codului existent și a documentației din proiect. Cerințele MUST definesc scope-ul final, iar SHOULD/MAY sunt optimizări sau capabilități opționale compatibile cu stadiul final.
