# Idei: Utilitar AI pentru Analiză Criptografică și Securitate

## 1. Introducere și Prezentare Generală

### 1.1. Contextul Proiectului
Proiectul propune dezvoltarea unui sistem integrat care combină 
inteligența artificială cu diverse tehnici criptografice pentru 
a oferi o platformă completă de analiză a criptogramelor, 
criptare/decriptare, analiză a teoriei numerelor și evaluare a 
securității parolelor. Într-o eră în care securitatea informațiilor 
devine din ce în ce mai importantă, acest sistem va servi ca 
instrument educațional și practic pentru studenți, cercetători și 
profesioniști în domeniul securității informatice.

### 1.2. Obiective
- Crearea unei platforme integrate pentru analiza criptografică
- Implementarea unui motor de conversație bazat pe LLM specializat în criptografie
- Dezvoltarea modulelor de analiză și atac pentru diversi algoritmi criptografici
- Integrarea bazelor de date pentru numere prime și semiprime
- Implementarea algoritmilor post-quantum
- Asigurarea scalabilității și securității sistemului

### 1.3. Valoare Academică și Practică
Lucrarea aduce contribuții semnificative prin:
- Integrarea tehnicilor de AI/ML în analiza criptografică
- Abordarea unitară a mai multor aspecte ale criptografiei
- Implementarea practică a algoritmilor post-quantum
- Crearea unei interfețe conversaționale pentru rezolvarea problemelor criptografice

## 2. Arhitectura Sistemului

### 2.1. Arhitectura Generală

### 2.2. Componente Principale

#### 2.2.1. Frontend
- **Interfața CLI/Terminal**: Interacțiune directă prin comandă
- **Interfața Web**: Acces prin browser cu suport pentru diverse dispozitive
- **API RESTful**: Endpointuri pentru servicii și integrare cu alte sisteme

#### 2.2.2. Backend
- **Motor LLM**: Procesare în limbaj natural și generare de răspunsuri
- **Motor de Analiză Criptografică**: Modulul central pentru analiza și atacarea criptogramelor
- **Modul Teorie Numere**: Gestionarea operațiilor cu numere prime, factorizare
- **Modul Analiză Parole**: Evaluarea securității parolelor și generarea de recomandări
- **Modul Algoritmi Post-Quantum**: Implementarea și testarea algoritmilor rezistenți la atacuri cuantice

#### 2.2.3. Stocare
- **Bază de Date Numere Prime/Semiprime**: Cache și acces rapid la informații despre numere prime
- **Bază de Date Hash-uri**: Pentru verificarea parolelor și hash-urilor cunoscute
- **Stocare Modele AI**: Pentru modelele LLM antrenate și ponderile acestora
- **Bază de Date Utilizatori**: Gestionarea conturilor, preferințelor și istoricului conversațiilor

## 3. Stack Tehnologic

### 3.1. Tehnologii Principale

### 3.2. Justificarea Tehnologiilor

#### 3.2.1. Backend
- **Python**: Versatil, bogat în biblioteci pentru ML și criptografie, productivitate ridicată
- **FastAPI**: Performanță superioară, documentație automată, suport asincron
- **C/C++**: Performanță critică pentru algoritmi criptografici intensivi
- **Rust**: Siguranță la nivel de memorie, performanță apropiată de C/C++

#### 3.2.2. AI și ML
- **PyTorch**: Flexibilitate, comunitate activă, suport excelent pentru NLP
- **Hugging Face**: Acces la modele pre-antrenate, simplificarea fine-tuning-ului
- **ONNX**: Optimizare pentru inferență, portabilitate între framework-uri

#### 3.2.3. Containerizare
- **Docker**: Izolare, reproducibilitate, portabilitate
- **Kubernetes**: Scalabilitate, auto-healing, orchestrare avansată

#### 3.2.4. Securitate
- **JWT**: Standard pentru tokenuri de autentificare
- **OpenSSL**: Bibliotecă matură și testată pentru operații criptografice

## 4. Implementarea Modulelor

### 4.1. Motorul LLM Specializat

#### 4.1.1. Structura Modelului
Se propune utilizarea unui model de tip encoder-decoder bazat pe arhitectura Transformer, cu:
- Dimensiune model: 1-3B parametri (compromis între performanță și resurse)
- Context window: 8K-16K tokeni (pentru a permite analiza textelor mai lungi)
- Arhitectură: Mixtă între transformer standard și arhitecturi specializate

#### 4.1.2. Strategie de Antrenare



#### 4.1.3. Setul de Date pentru Antrenare
- **Corpus General**: Modele pre-antrenate (ex. Llama 3, Mistral, etc.)
- **Corpus Specializat**:
  - Articole academice din domeniul criptografiei
  - Documentație pentru algoritmi criptografici
  - Perechi problemă-soluție din criptografie
  - Exemple de atacuri criptografice și rezolvările lor
  - Dialoguri expert-novice în domeniul criptografiei
  - Manuale și cărți de specialitate în format digital

#### 4.1.4. Fine-tuning și RLHF
- **Fine-tuning Supervizat**: Pe corpus specializat criptografic
- **RLHF (Reinforcement Learning from Human Feedback)**: Pentru aliniere și utilitate
- **Prompting Specializat**: Tehnici de few-shot și chain-of-thought pentru probleme complexe

### 4.2. Motorul de Analiză Criptografică

#### 4.2.1. Componente
- **Detector de Algoritm**: Model de clasificare pentru identificarea tipului de criptare
- **Analizor Frecvențe**: Pentru criptografie clasică
- **Module Specializate**: Pentru fiecare algoritm major (AES, RSA, DES, etc.)
- **Executor de Atacuri**: Implementarea automatizată a atacurilor cunoscute

#### 4.2.2. Fluxuri de Lucru





#### 4.2.3. Detector de Algoritm

Detectorul de algoritm va folosi o abordare hibridă:

1. **Analiza Structurală**:
   - Verificarea lungimii output-ului
   - Identificarea pattern-urilor specifice (ex. padding)
   - Verificarea entropiei

2. **Clasificare ML**:
   - Model CNN + LSTM pentru identificarea algoritmilor din text criptat
   - Features extrase din distribuții statistice

3. **Euristica Bazată pe Reguli**:
   - Reguli predefinite pentru algoritmi cunoscuți
   - Verificări pentru semnături specifice

```python
# Exemplu conceptual pentru detectorul de algoritm
class CipherDetector:
    def __init__(self):
        self.statistical_analyzer = StatisticalAnalyzer()
        self.ml_classifier = load_model("cipher_classifier.h5")
        self.rule_engine = RuleBasedDetector()
        
    def detect(self, ciphertext, additional_info=None):
        # Analiză statistică
        stats_features = self.statistical_analyzer.extract_features(ciphertext)
        
        # Clasificare ML
        ml_predictions = self.ml_classifier.predict(self.preprocess(ciphertext))
        
        # Verificare euristici
        rule_candidates = self.rule_engine.apply_rules(ciphertext, additional_info)
        
        # Fuziune rezultate
        final_candidates = self.fusion_algorithm(stats_features, ml_predictions, rule_candidates)
        
        return sorted(final_candidates, key=lambda x: x['confidence'], reverse=True)
```

### 4.3. Modulul de Teorie a Numerelor

#### 4.3.1. Funcționalități

- **Teste de Primalitate**:
  - Miller-Rabin
  - AKS (Agrawal-Kayal-Saxena)
  - Lucas-Lehmer (pentru numere Mersenne)

- **Factorizare**:
  - Trial division
  - Metoda Pollard Rho
  - Quadratic Sieve
  - Number Field Sieve (pentru numere mari)

- **Operații Speciale**:
  - Calculul logaritmului discret
  - Operații pe curbe eliptice
  - Generare numere prime de dimensiuni specifice

#### 4.3.2. Integrare cu Baze de Date Externe

- Interogare automată FactorDB
- Cache local pentru rezultate frecvente
- Sincronizare periodică cu baze de date publice

### 4.4. Modulul de Analiză Parole

#### 4.4.1. Metrici de Securitate

- **Entropie**: Calculată pe baza seturilor de caractere și lungimii
- **Rezistența la Atacuri**: Estimare timp pentru diferite tipuri de atacuri
- **Verificare în Baze de Date**: CrackStation, HaveIBeenPwned
- **Analiză Structurală**: Identificare pattern-uri comune, substituții predictibile

#### 4.4.2. Vizualizare și Recomandări





### 4.5. Implementarea Algoritmilor Post-Quantum

#### 4.5.1. Algoritmi Selectați

- **Criptare Asimetrică**:
  - Kyber (CRYSTALS-Kyber): Selectat de NIST ca standard
  - NTRU: Alternativă matură și studiată
  
- **Semnături Digitale**:
  - Dilithium (CRYSTALS-Dilithium): Standard NIST
  - FALCON: Pentru aplicații cu semnături compacte
  
- **Schimb de Chei**:
  - SIKE: Supersingular Isogeny Key Encapsulation

#### 4.5.2. Implementare și Integrare

- Utilizarea bibliotecii liboqs ca bază
- Wrapper-uri Python pentru acces simplificat
- Integrare în fluxurile de lucru standard
- Interfețe compatibile cu algoritmi clasici pentru tranziție ușoară

## 5. Securizarea Sistemului

### 5.1. Autentificare și Autorizare

- **JWT** pentru tokenuri de acces
- **OAuth2** pentru autorizare
- **Rate limiting** pentru prevenirea abuzului
- **RBAC** (Role-Based Access Control) pentru permisiuni granulare

### 5.2. Securitatea Comunicațiilor

- **TLS 1.3** pentru toate comunicațiile externe
- **Mutual TLS** pentru comunicații între microservicii
- **Perfect Forward Secrecy** pentru protecție pe termen lung

### 5.3. Securitatea Datelor

- **Criptare la repaus** pentru toate datele sensibile
- **Tokenizare** pentru informații de identificare personală
- **Anonimizare** a datelor utilizate pentru antrenare

## 6. Deployment și Scalabilitate

### 6.1. Arhitectura Docker





### 6.2. Implementare Kubernetes

- **Namespace Dedicat**: Izolare completă a resurselor
- **Deployment** pentru fiecare serviciu cu strategie de rolling update
- **HorizontalPodAutoscaler** pentru scalare bazată pe utilizare
- **Ingress** pentru routare externă și TLS
- **Helm Charts** pentru deployments reproductibile
- **Secrets Management** cu Kubernetes Secrets sau HashiCorp Vault

### 6.3. Monitoring și Logging

- **Prometheus** pentru colectarea metricilor
- **Grafana** pentru dashboards și vizualizare
- **ELK Stack** (Elasticsearch, Logstash, Kibana) pentru logging centralizat
- **Alerting** pentru notificări proactive în caz de probleme

## 7. Fluxuri de Lucru Detaliate

### 7.1. Conversație cu LLM pentru Rezolvarea Problemelor

1. **Inițiere**: Utilizatorul descrie o problemă criptografică
2. **Înțelegere**: LLM procesează și extrage componentele cheie
3. **Clarificare**: LLM cere detalii suplimentare dacă este necesar
4. **Rezolvare**: LLM generează soluția pas cu pas
5. **Explicare**: LLM oferă detalii despre abordarea folosită
6. **Feedback**: Utilizatorul poate cere clarificări sau detalii suplimentare

#### Exemplu Conversație:

```
Utilizator: Cum pot decripta acest text "Uifsf jt b tfdsfu nfttbhf"?

LLM: Acest text pare să fie criptat cu Caesar Cipher (sau ROT). Voi încerca diferite chei:

Cu ROT-1: "There is a secret message"

Această variantă are sens în limba engleză, deci probabil este corectă. Cifrul Caesar înlocuiește fiecare literă cu litera aflată la o anumită poziție fixă în alfabet. În acest caz, fiecare literă a fost înlocuită cu următoarea literă din alfabet (ROT-1).

Doriți să aflați mai multe despre cifrul Caesar sau cum să detectați acest tip de criptare?
```

### 7.2. Analiza Mesajului Criptat

1. **Încărcare**: Utilizatorul trimite textul criptat
2. **Detectare**: Sistemul detectează algoritmul de criptare probabil
3. **Analiză**: Se execută analize statistice și pattern matching
4. **Atac**: Se încearcă metode de atac pentru algoritmul detectat
5. **Raportare**: Se returnează rezultatele și explicațiile







### 7.3. Lucrul cu Algoritmi Post-Quantum

1. **Selecție**: Utilizatorul alege tipul de algoritm post-quantum
2. **Configurare**: Se setează parametrii specifici
3. **Generare**: Se generează cheile criptografice
4. **Operații**: Se efectuează operațiuni (criptare, semnare, etc.)
5. **Analiză**: Se oferă statistic și comparații cu algoritmi clasici

#### Exemplu de Utilizare pentru CRYSTALS-Kyber:

```python
# Exemplu simplificat de integrare Kyber în aplicație
from pqcrypto import kyber

# Generare chei
public_key, secret_key = kyber.keygen()

# Criptare mesaj
ciphertext, shared_secret_enc = kyber.encrypt(public_key, message)

# Decriptare mesaj
shared_secret_dec = kyber.decrypt(secret_key, ciphertext)

# Verificare
assert shared_secret_enc == shared_secret_dec
```

## 8. Antrenarea Modelelor ML/DL

### 8.1. Model pentru Detectarea Algoritmului de Criptare

#### 8.1.1. Procesul de Antrenare

1. **Pregătirea Datelor**:
   - Generarea datelor pentru multiple algoritmi (AES, DES, RSA, etc.)
   - Variații în chei, moduri de operare, padding
   - Augmentarea datelor pentru robustețe

2. **Arhitectura Modelului**:
   - CNN pentru extragerea pattern-urilor locale
   - BiLSTM pentru capturarea dependențelor secvențiale
   - Fully Connected layers pentru clasificare

3. **Strategia de Antrenare**:
   - Transfer learning de la modele antrenate pe clasificare de text
   - Fine-tuning specific pentru date criptografice
   - Validation cruce pentru evitarea overfitting

#### 8.1.2. Evaluare și Optimizare

- Matrice de confuzie pentru înțelegerea erorilor
- Raport de clasificare (precision, recall, F1)
- Evaluare pe date din lumea reală
- Analiza cazurilor de eșec pentru îmbunătățire

### 8.2. Antrenare LLM Specializat

#### 8.2.1. Procesul de Fine-tuning

1. **Selecția Modelului de Bază**:
   - Utilizarea unui model pre-antrenat (ex. Llama 3-8B) 
   - Adaptarea arhitecturii pentru context specializat

2. **Pregătirea Datelor**:
   - Colectarea și curățarea corpusului criptografic
   - Structurarea în formatul instruction-response
   - Augmentarea cu date sintetice

3. **Fine-tuning**:
   - LoRA (Low-Rank Adaptation) pentru eficiență
   - QLoRA pentru training pe hardware accesibil
   - Strategii de optimizare a hiperparametrilor

#### 8.2.2. RLHF (Reinforcement Learning from Human Feedback)

1. **Colectarea Preferințelor**:
   - Evaluări de experți în domeniul criptografiei
   - Comparații între răspunsuri alternative

2. **Antrenarea Modelului de Recompensă**:
   - Model care prezice preferințele umane
   - Calibrare pentru evitarea biasurilor

3. **Optimizare prin PPO**:
   - Fine-tuning folosind Proximal Policy Optimization
   - Balansare între maximizarea recompensei și evitarea devierilor

## 9. Planificarea Proiectului

### 9.1. Etape și Termene







### 9.2. Estimare Efort și Resurse

| Componentă | Efort Estimat (ore) | Nivel Complexitate | Resurse Necesare |
|------------|---------------------|---------------------|------------------|
| Arhitectură și design | 80-120 | Mediu | Documentație, cercetare |
| Motor LLM (fine-tuning) | 150-200 | Înalt | GPU performant, date antrenare |
| Motor criptografic | 100-150 | Mediu-Înalt | Biblioteci criptografice |
| Modul teorie numere | 80-100 | Mediu | Biblioteci matematice |
| Analiză parole | 60-80 | Mediu | Baze de date, biblioteci statistice |
| Algoritmi post-quantum | 100-120 | Înalt | Documentație specializată |
| Frontend și API | 100-120 | Mediu | Biblioteci UI, framework web |
| Integrare și testare | 80-100 | Mediu | Framework-uri de testare |
| Documentație | 70-100 | Mediu | Materiale referință |
| **Total** | **820-1090** | | |

### 9.3. Managementul Riscurilor

| Risc | Probabilitate | Impact | Strategii de Mitigare |
|------|---------------|--------|------------------------|
| Complexitate tehnică neprevăzută | Medie | Înalt | Prototipare rapidă, cercetare aprofundată |
| Limitări hardware pentru antrenare LLM | Înaltă | Mediu | Utilizare modele mai mici, tehnici eficiente (QLoRA) |
| Integrare dificilă a componentelor | Medie | Mediu | Dezvoltare bazată pe API, testare continuă |
| Securitatea sistemului compromisă | Scăzută | Foarte Înalt | Audit de securitate, testare penetrare |
| Timelines nerealist | Medie | Înalt | Buffer în planificare, prioritizare caracteristici |

## 10. Considerații Finale

### 10.1. Contribuții Academice

Proiectul contribuie în mai multe direcții:
- Integrarea tehnicilor de ML/DL în analiza criptografică
- Arhitectură hibridă pentru instrumente criptografice
- Implementarea practică a algoritmilor post-quantum
- Framework conversațional pentru probleme criptografice

### 10.2. Potențiale Extensii

- Suport pentru noi algoritmi criptografici
- Integrarea cu sisteme de PKI (Public Key Infrastructure)
- Dezvoltarea unui framework pentru competiții CTF
- Modul de analiză forensică pentru malware criptat
- Integrare cu sisteme de blockchain

### 10.3. Limitări și Provocări

- Performanța inferenței LLM pe hardware limitat
- Actualizarea constantă a bazelor de date
- Menținerea la curent cu evoluțiile în criptanaliză
- Balanța între exhaustivitate și usability
- Considerații etice pentru unelte de atac criptografic

## 11. Referințe și Resurse Utile

## Concluzii

Acest proiect propune o abordare integrată și modernă pentru analiza criptografică, combinând tehnici tradiționale cu inteligența artificială și machine learning. Prin integrarea unui motor LLM specializat, utilizatorii vor putea interacționa natural cu sistemul pentru a rezolva probleme criptografice complexe, analizând criptograme, evaluând securitatea parolelor și explorând algoritmi post-quantum.

Implementarea folosește tehnologii de vârf precum Docker pentru containerizare, FastAPI pentru backend, PyTorch pentru componente de ML/DL, și implementări native C/C++ pentru algoritmi criptografici performanți. Arhitectura modulară permite extensibilitate și scalabilitate, iar abordarea bazată pe microservicii facilitează dezvoltarea și testarea independentă a componentelor.

Cu un timp estimat de implementare de 800-1000 de ore, proiectul este fezabil pentru o lucrare de licență ambițioasă, oferind atât valoare academică prin cercetarea aplicată, cât și valoare practică prin crearea unui instrument util pentru educație și cercetare în domeniul securității informatice.

Adoptarea unui model de dezvoltare iterativ, cu focus inițial pe funcționalitățile de bază și extindere graduală a capacităților, va permite gestionarea eficientă a complexității și livrarea unui produs funcțional în limitele de timp disponibile.
