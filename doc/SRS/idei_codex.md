# Propuneri Codex pentru SRS

Acest document sintetizeaza propuneri pentru un SRS robust, tehnic, pentru proiectul de licenta in stadiul final: platforma software de unelte AI in criptografie (Vitruvian Cipher). Textul este gandit sa fie integrat in structura din `doc/SRS/srs-template-bare.md` si transpus in LaTeX in `doc/SRS/srs_platforma_management.tex`.

## Directie recomandata

- Pastreaza structura din template (cap. 1-5) pentru claritate si verificabilitate.
- Foloseste cerinte numerotate cu limbaj RFC 2119 (TREBUIE/AR TREBUI/POATE).
- Adauga matrice de verificare (cerinta -> metoda -> evidenta).
- Include sectiune AI/ML dedicata (model, date, guardrails, MLOps).
- Separare clara intre cerinte functionale vs non-functionale vs QoS.

## Analiza proiect (rezumat tehnic)

- Platforma multi-agent, microservicii (Go/Rust/Python) cu orchestrator central.
- Flux principal: UI/CLI -> Orchestrator -> Agenti specializati -> DB/Cache -> raspuns agregat.
- Agentii principali: Password Intelligence, Prime Factorization, Theory RAG, Command Executor, Choice Maker.
- Stadiul final include: backend Go robust cu autentificare/autorizare/audit, observabilitate completa, CI/CD, k8s, security audit, open-source.
- Dependente externe: HIBP, FactorDB, LLM providers, plus tool-uri locale (YAFU, OpenSSL, ChromaDB).

## Scope stadiu final (target)

- Backend central Go pentru identitate, autorizare, audit si management API.
- Infrastructura Kubernetes completa (ingress, namespace segregation, secrets, scaling).
- Module de securitate avansata (WAF/API Gateway, mTLS, RBAC, secrets management).
- Monitorizare continua (metrics, logs, traces, alerte) si dashboard-uri.
- Pipeline CI/CD cu build, test, scanare securitate si deploy automat.
- Publicare open-source pe GitHub cu licenta si documentatie.

## Ce ar mai trebui sa existe in SRS

- Diagrama de context si trust boundaries (frontiera extern/interior).
- Descrierea actorilor (user obisnuit, admin, auditor, serviciu intern, CI/CD).
- Constrangeri tehnice: limbaje, k8s, open-source, portabilitate on-prem/cloud.
- Cerinte pentru managementul datelor (clasificare, retention, stergere, backup).
- Cerinte de securitate (mTLS, RBAC, secret management, audit).
- Cerinte de observabilitate (metrics, logs, traces, alerting).
- Cerinte de conformitate (OWASP, NIST/ENISA, GDPR daca aplica).
- AI/ML: guvernanta modele/dataset, guardrails, drift, retraining.
- Apportioning pe subsisteme si versiuni/livrari.

## Cerinte functionale (stadiu final)

### Identitate si acces
- FR-01: Sistemul trebuie sa permita inregistrare, autentificare si resetare parola.
- FR-02: Sistemul trebuie sa suporte MFA (TOTP/WebAuthn) pentru roluri privilegiate.
- FR-03: Sistemul trebuie sa emita si gestioneze token-uri JWT (access/refresh) cu expirare configurabila.
- FR-04: Sistemul trebuie sa gestioneze API keys cu scope-uri si revocare.
- FR-05: Sistemul trebuie sa implementeze RBAC pentru endpoint-uri si resurse.

### Orchestrare si routing
- FR-06: Orchestratorul trebuie sa detecteze intentia si sa routeze catre agentul potrivit.
- FR-07: Orchestratorul trebuie sa permita executie paralela si agregare de raspunsuri.
- FR-08: Orchestratorul trebuie sa gestioneze timeouts per agent si circuit breaking.
- FR-09: Orchestratorul trebuie sa expuna health endpoints per serviciu.
- FR-10: Orchestratorul trebuie sa ofere fallback cand agentii sunt indisponibili.

### Agenti specializati
- FR-11: Agentul de parole trebuie sa furnizeze scor unificat si recomandari.
- FR-12: Agentul de factorizare trebuie sa evalueze primalitatea si sa returneze factori + metoda.
- FR-13: Agentul RAG trebuie sa ofere raspunsuri cu citari si gestiune de conversatii.
- FR-14: Agentul crypto trebuie sa execute operatii aprobate cu validari stricte.
- FR-15: Sistemul trebuie sa permita adaugarea de agenti noi fara downtime major.

### Date si conversatii
- FR-16: Sistemul trebuie sa stocheze istoricul conversatiilor si sa permita reluare.
- FR-17: Sistemul trebuie sa permita ingestia de documente in baza RAG cu metadata.
- FR-18: Sistemul trebuie sa ofere export rezultate in JSON/PDF.
- FR-19: Sistemul trebuie sa permita stergerea/anonimizarea datelor la cerere.
- FR-20: Sistemul trebuie sa foloseasca cache cu TTL configurabil pentru cereri repetitive.

### Admin, audit si control
- FR-21: Sistemul trebuie sa logheze actiuni critice in audit log.
- FR-22: Sistemul trebuie sa ofere UI de administrare pentru utilizatori, roluri si chei.
- FR-23: Sistemul trebuie sa aplice rate limiting si quota per utilizator/API key.
- FR-24: Sistemul trebuie sa alerteze la pattern-uri anormale (auth failures, brute force).
- FR-25: Sistemul trebuie sa permita configurari centralizate per mediu (dev/stage/prod).
- FR-26: Sistemul trebuie sa genereze rapoarte de audit si export pentru actiuni sensibile.

### Infrastructura si operare
- FR-27: Sistemul trebuie sa ruleze in Kubernetes cu namespace segregation.
- FR-28: Sistemul trebuie sa foloseasca secrets management pentru chei si credentale.
- FR-29: Sistemul trebuie sa expuna metrici Prometheus pentru toate serviciile.
- FR-30: Sistemul trebuie sa exporte loguri structurate in pipeline centralizat.
- FR-31: Sistemul trebuie sa suporte CI/CD cu build, test, scan si deploy automat.
- FR-32: Sistemul trebuie sa integreze scanari de securitate (SAST/DAST/secret scanning) in CI/CD.
- FR-33: Sistemul trebuie sa ofere monitorizare continua si alerte in productie.
- FR-34: Sistemul trebuie sa suporte functionare cu LLM local si cu provider extern, cu fallback.
- FR-35: Sistemul trebuie sa fie publicat ca open-source pe GitHub cu licenta si ghid de contributie.

## Cerinte non-functionale (categorii)

### Securitate
- NFR-S1: Comunicatiile externe trebuie sa foloseasca TLS 1.2+.
- NFR-S2: Comunicatiile inter-servicii trebuie sa foloseasca mTLS in productie.
- NFR-S3: Datele sensibile trebuie criptate at-rest (AES-256/GCM).
- NFR-S4: Secretele nu trebuie stocate in cod sau imagini de container.
- NFR-S5: Sistemul trebuie sa permita audit si investigare incident.

### Performanta si scalare
- NFR-P1: Sistemul trebuie sa permita scalare orizontala in k8s.
- NFR-P2: Serviciile trebuie sa gestioneze backpressure la cereri concurente.
- NFR-P3: Endpoint-urile "light" trebuie sa raspunda p95 < 500ms (conditii nominale).
- NFR-P4: Operatiile "heavy" trebuie sa fie asincrone sau cu status polling.
- NFR-P5: Cache-ul trebuie sa reduca latenta pentru cereri repetate.

### Fiabilitate si disponibilitate
- NFR-R1: Disponibilitate target >= 99.5% pentru orchestrator/backend.
- NFR-R2: Retry cu backoff trebuie sa fie implementat pentru dependente externe.
- NFR-R3: Failover trebuie sa fie disponibil pentru servicii critice.
- NFR-R4: Backup-urile trebuie automate si testate periodic.
- NFR-R5: RTO/RPO trebuie definite si masurabile.

### Mentenabilitate si portabilitate
- NFR-M1: Serviciile trebuie sa fie containerizate si configurabile prin env vars.
- NFR-M2: API-urile trebuie versionate si documentate (OpenAPI).
- NFR-M3: Sistemul trebuie sa fie portabil on-prem si cloud.
- NFR-M4: Logging-ul trebuie sa fie structurat (JSON) si corelabil.
- NFR-M5: Codul trebuie sa fie modular si testabil (clean architecture).

### Observabilitate
- NFR-O1: Fiecare serviciu trebuie sa expuna metrici Prometheus.
- NFR-O2: Sistemul trebuie sa colecteze loguri si trace-uri distribuite.
- NFR-O3: Alertele trebuie sa existe pentru erori, latenta si rate anormale.
- NFR-O4: Health checks trebuie sa acopere dependinte critice.
- NFR-O5: Dashboard-urile trebuie sa acopere RED/USE metrics.

### Conformitate
- NFR-C1: API-urile trebuie sa respecte OWASP ASVS.
- NFR-C2: Criptografia trebuie sa respecte recomandari NIST/ENISA.
- NFR-C3: Datele personale trebuie gestionate conform GDPR (daca aplica).
- NFR-C4: Licentele OSS trebuie inventariate si compatibile.
- NFR-C5: CI/CD trebuie sa includa scanari SAST/DAST.

## QoS / SLO propuse

- QOS-01: Disponibilitate lunara >= 99.5% pentru orchestrator/backend.
- QOS-02: p95 latenta pentru endpoint-uri sincrone <= 500ms (fara operatii heavy).
- QOS-03: p95 latenta pentru routing/intent <= 200ms.
- QOS-04: RPO <= 15 min, RTO <= 1 h pentru DB.
- QOS-05: Rata erorilor 5xx <= 1% pe intervale de 10 min.
- QOS-06: Observabilitate completa pentru >= 95% din request-uri.

## Assumptions si dependente

- Acces la LLM local si/sau provider extern, cu chei de acces valide.
- Acces la HIBP/FactorDB, cu respectarea termenilor de utilizare.
- Resurse compute suficiente pentru factorizare, RAG si ML.
- Acces la cluster k8s si la un registry pentru imagini.

## Verificare si trasabilitate

- Defineste pentru fiecare cerinta metoda de verificare: test automat, review, inspectie, demonstratie.
- Creeaza matrice de trasabilitate (ID cerinta -> test -> evidenta).
- Stabileste criterii de acceptanta per cerinta critica (security/performance).

## Intrebari deschise (de clarificat inainte de final)

- Lista finala de agenti si scope pentru fiecare (inclusiv agenti noi).
- Ce nivel de availability si SLO-uri sunt acceptate pentru fiecare serviciu?
- Ce dependente externe sunt permise in productie si care sunt restrictionate?
- Ce standarde de securitate sunt cerinte academice obligatorii?
