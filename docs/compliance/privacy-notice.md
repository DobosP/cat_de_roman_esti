# Politica de confidențialitate / Privacy Notice

**DRAFT — not legal advice — requires review by a qualified Romanian data-protection lawyer before publication.**

**DRAFT — REQUIRES LEGAL REVIEW**

Versiune: `[[PLACEHOLDER: notice version]]`  
Data intrării în vigoare: `[[PLACEHOLDER: effective date]]`  
Domeniu / aplicație: `[[PLACEHOLDER: domain name]]`  
Operator: `[[PLACEHOLDER: controller legal name / interim personal identity]]`  
Adresă: `[[PLACEHOLDER: controller address]]`  
Nr. înregistrare: `[[PLACEHOLDER: registration number, if any]]`  
Contact protecția datelor: `[[PLACEHOLDER: DPO or privacy contact email]]`

## RO — Politica de confidențialitate

### 1. Pe scurt

`cât-de-român-ești` este o aplicație web gratuită, educațională, în limba română, cu jocuri de cuvinte și cunoștințe. Jocurile pot fi folosite fără cont, în măsura în care funcționalitatea permite. Dacă alegi să folosești „Sign in with Google”, aplicația va putea salva progresul tău pe server: istoricul scorurilor, completările zilnice și cele mai bune rezultate pe puzzle.

Acest document explică ce date personale prelucrăm, de ce, pe ce temei legal, cât timp le păstrăm și ce drepturi ai. Pentru utilizatorii sub 16 ani se aplică reguli speciale de consimțământ parental.

### 2. Cine este operatorul

Operatorul datelor este `[[PLACEHOLDER: controller legal name / interim personal identity]]`. Entitatea juridică finală nu este încă stabilită; înainte de publicare, această secțiune trebuie completată și verificată juridic.

### 3. Ce date colectăm

| Categoria | Date | Sursa |
| --- | --- | --- |
| Date de cont Google | adresă de e-mail, nume afișat, avatar/fotografie de profil, identificator Google `sub` | Google Identity, după autentificare |
| Date de progres în joc | scoruri, istoric scoruri, completări zilnice, cele mai bune rezultate pe puzzle, setări de joc asociate contului | generate prin folosirea aplicației |
| Date tehnice și de securitate | adrese IP, user agent, timestamp-uri, evenimente de autentificare, erori, identificatori de sesiune, loguri anti-abuz | browserul tău, Cloudflare, serverele aplicației |
| Stocare locală | progres offline, preferințe locale, identificatori tehnici necesari funcționării | browserul tău |
| Consimțământ și vârstă | confirmare vârstă / bandă de vârstă, acceptare termeni, versiuni documente, timestamp, hash text consimțământ, dovadă consimțământ parental dacă este cazul | formularele aplicației |

Nu intenționăm să colectăm categorii speciale de date conform GDPR art. 9, date de plată sau conținut generat public de utilizatori.

### 4. Scopuri și temeiuri legale

| Scop | Date folosite | Temei GDPR |
| --- | --- | --- |
| Crearea și administrarea contului opțional | date cont Google, identificator cont intern, consimțământ/acceptare | art. 6(1)(b) contract, pentru furnizarea contului; art. 6(1)(a) consimțământ unde contul este opțional și pentru copil conform art. 8 |
| Salvarea progresului pe server | scoruri, completări, per-puzzle bests, setări asociate contului | art. 6(1)(b) contract; art. 6(1)(a) consimțământ pentru utilizatorii sub 16 ani prin părinte/tutore |
| Autentificare cu Google | Google `sub`, e-mail, nume, avatar | art. 6(1)(b) contract; art. 6(1)(a) consimțământ pentru conectarea opțională |
| Securitate, prevenirea abuzului, depanare | IP, user agent, loguri, evenimente tehnice | art. 6(1)(f) interes legitim: securitatea serviciului, prevenirea fraudei și funcționarea tehnică |
| Respectarea obligațiilor legale și răspuns la cereri | date cont, loguri necesare, corespondență DSAR | art. 6(1)(c) obligație legală |
| Comunicări strict legate de cont | e-mail, starea contului, cereri de ștergere/export | art. 6(1)(b) contract sau art. 6(1)(c) obligație legală, după caz |

Nu folosim datele pentru publicitate comportamentală, profilare publicitară sau vânzarea datelor.

### 5. Copii și consimțământ parental

Aplicația se adresează și minorilor. Pentru servicii ale societății informaționale oferite direct copilului, în România consimțământul copilului este valabil numai dacă acesta are cel puțin 16 ani. Dacă utilizatorul are sub 16 ani, este necesar consimțământul verificabil al părintelui sau tutorelui legal înainte de crearea contului și salvarea progresului pe server.

Părintele/tutorele poate:

- cere acces la datele copilului;
- cere corectarea sau ștergerea contului și progresului;
- retrage consimțământul;
- cere exportul datelor, unde se aplică;
- contacta operatorul la `[[PLACEHOLDER: DPO or privacy contact email]]`.

Conturile copiilor trebuie să fie private în mod implicit. Aplicația nu trebuie să afișeze profiluri publice ale minorilor și nu trebuie să folosească profilare pentru publicitate. Aceste măsuri sunt aliniate cu GDPR și, unde este aplicabil, cu obligațiile privind protecția minorilor din Digital Services Act.

### 6. Perioade de păstrare

| Date | Perioadă propusă | Notă |
| --- | --- | --- |
| Cont Google și profil intern | cât timp contul este activ; ștergere sau anonimizare în 30 de zile după cererea de ștergere | `[[CONFIRM: final retention period]]` |
| Progres de joc | cât timp contul este activ; ștergere odată cu contul | `[[CONFIRM: whether inactive accounts are deleted after 24 months]]` |
| Loguri de securitate | 90 de zile, cu păstrare mai lungă doar pentru investigarea unui incident | `[[CONFIRM: operational log retention]]` |
| Consimțământ și acceptări legale | pe durata contului + 3 ani după ștergere, doar pentru apărarea drepturilor | `[[CONFIRM: limitation period and legal basis with counsel]]` |
| Cereri DSAR și corespondență | 3 ani după închiderea cererii | `[[CONFIRM: final retention period]]` |
| Date în localStorage | până când utilizatorul le șterge din browser sau folosește funcția de resetare locală | date stocate pe dispozitiv |

### 7. Destinatari și persoane împuternicite

| Furnizor | Rol | Date posibile | Localizare / transfer |
| --- | --- | --- | --- |
| Google Identity | persoană împuternicită / sub-procesator pentru autentificare, conform contractelor aplicabile | e-mail, nume, avatar, Google `sub`, evenimente autentificare | `[[CONFIRM: Google DPA, subprocessors, transfer mechanism]]` |
| Hetzner | persoană împuternicită pentru hosting | baza de date cont/progres, loguri server | Germania/Finlanda, UE/SEE `[[CONFIRM: exact region and DPA]]` |
| Cloudflare | persoană împuternicită pentru DNS, CDN, securitate, proxy | IP, user agent, request metadata, securitate | `[[CONFIRM: Cloudflare DPA, EU settings, transfer mechanism]]` |

Datele de cont și progres sunt proiectate să fie găzduite în UE/SEE pe infrastructura Hetzner. Operatorul nu intenționează să transfere baza de date de cont/progres în afara SEE. Orice transfer tehnic posibil prin Google Identity sau Cloudflare trebuie verificat înainte de lansare și acoperit prin clauze contractuale standard, decizii de adecvare sau alt mecanism GDPR valid, după caz.

### 8. Cookies, localStorage și tehnologii similare

Aplicația folosește cookie-uri strict necesare pentru sesiune și protecție CSRF. Acestea nu necesită consimțământ separat, deoarece sunt necesare pentru furnizarea serviciului solicitat.

Browserul poate folosi localStorage pentru progres offline și preferințe. Aplicația nu folosește cookie-uri de publicitate sau tracking. Orice cookie sau SDK opțional de analiză, marketing sau tracking trebuie introdus numai după consimțământ opt-in și după actualizarea acestei politici.

### 9. Drepturile tale

Ai dreptul, în condițiile GDPR, la:

- acces la date;
- rectificare;
- ștergere;
- restricționarea prelucrării;
- portabilitate;
- opoziție la prelucrarea bazată pe interes legitim;
- retragerea consimțământului, fără a afecta prelucrarea anterioară retragerii;
- depunerea unei plângeri la autoritatea de supraveghere.

Pentru exercitarea drepturilor, scrie la `[[PLACEHOLDER: DPO or privacy contact email]]`. Vom răspunde, de regulă, în cel mult o lună, conform GDPR. Pentru cereri complexe, termenul poate fi prelungit cu până la două luni, cu informarea solicitantului.

Autoritatea de supraveghere din România este Autoritatea Națională de Supraveghere a Prelucrării Datelor cu Caracter Personal (ANSPDCP): `https://www.dataprotection.ro/`.

### 10. Securitate

Măsuri propuse: autentificare prin Google OAuth/OIDC, cookie-uri `HttpOnly`, `Secure` și `SameSite`, protecție CSRF, criptare TLS, control acces administrativ, loguri de securitate, backup-uri limitate, minimizarea datelor, ștergere la cerere și separarea secretelor de cod. `[[CONFIRM: final technical and organisational measures]]`

### 11. Modificări

Putem actualiza această politică. Pentru modificări importante, vom afișa o notificare în aplicație și, unde este necesar, vom cere un nou consimțământ.

---

## EN — Privacy Notice

### 1. Summary

`cât-de-român-ești` is a free Romanian-language educational word-game web app. The app can be used without an account where functionality allows. If you choose “Sign in with Google”, the app can save server-side game progress: score history, daily completions and per-puzzle bests.

This notice explains what personal data we process, why, the lawful basis, retention and your rights. Special parental-consent rules apply to users under 16.

### 2. Controller

Controller: `[[PLACEHOLDER: controller legal name / interim personal identity]]`  
Address: `[[PLACEHOLDER: controller address]]`  
Registration number: `[[PLACEHOLDER: registration number, if any]]`  
Privacy contact: `[[PLACEHOLDER: DPO or privacy contact email]]`

The final legal entity has not yet been confirmed and must be completed before publication.

### 3. Data We Collect

| Category | Data | Source |
| --- | --- | --- |
| Google account data | email, display name, avatar/profile photo, Google subject id | Google Identity after login |
| Game progress | scores, score history, daily completions, per-puzzle bests, account-linked settings | app usage |
| Technical/security data | IP address, user agent, timestamps, login events, errors, session identifiers, anti-abuse logs | browser, Cloudflare, app servers |
| Local storage | offline progress, local preferences, necessary technical identifiers | browser |
| Consent and age records | age band/date-of-birth confirmation, terms acceptance, document versions, timestamp, text hash, parental-consent evidence where needed | app forms |

We do not intend to collect special-category data, payment data or public user-generated content.

### 4. Purposes and Lawful Bases

| Purpose | Data | GDPR lawful basis |
| --- | --- | --- |
| Optional account creation and management | Google account data, internal account id, consent/acceptance | Art. 6(1)(b) contract; Art. 6(1)(a) consent where account is optional and for children under Art. 8 |
| Server-side progress saving | scores, completions, per-puzzle bests, settings | Art. 6(1)(b) contract; Art. 6(1)(a) parental consent for under-16 users |
| Google authentication | Google `sub`, email, name, avatar | Art. 6(1)(b) contract; Art. 6(1)(a) consent for optional login |
| Security, abuse prevention and debugging | IP, user agent, logs, technical events | Art. 6(1)(f) legitimate interests |
| Legal compliance and requests | account data, necessary logs, DSAR correspondence | Art. 6(1)(c) legal obligation |
| Account-related communications | email, account status, export/deletion requests | Art. 6(1)(b) or Art. 6(1)(c), as applicable |

We do not use personal data for behavioural advertising, advertising profiling or data sales.

### 5. Children

In Romania, a child may validly consent to information-society services only from age 16. If a user is under 16, verifiable consent from a parent or legal guardian is required before account creation and server-side progress saving.

Parents/guardians may request access, correction, deletion, export or withdrawal of consent by contacting `[[PLACEHOLDER: DPO or privacy contact email]]`.

Children’s accounts must be private by default. The app must not show public minor profiles and must not use advertising profiling. These measures align with GDPR and, where applicable, Digital Services Act minor-protection duties.

### 6. Retention

| Data | Proposed retention | Note |
| --- | --- | --- |
| Account/profile | active account lifetime; deletion/anonymisation within 30 days after deletion request | `[[CONFIRM: final retention period]]` |
| Game progress | active account lifetime; deleted with account | `[[CONFIRM: inactive account policy]]` |
| Security logs | 90 days, longer only for incident investigation | `[[CONFIRM: operational log retention]]` |
| Consent/legal acceptance records | account lifetime + 3 years | `[[CONFIRM: limitation period with counsel]]` |
| DSAR correspondence | 3 years after request closure | `[[CONFIRM: final retention period]]` |
| localStorage | until cleared by the user/browser or reset in app | stored on device |

### 7. Recipients and Processors

| Provider | Role | Possible data | Location/transfer |
| --- | --- | --- | --- |
| Google Identity | processor/sub-processor for authentication under applicable terms | email, name, avatar, Google `sub`, login events | `[[CONFIRM: Google DPA, subprocessors, transfer mechanism]]` |
| Hetzner | hosting processor | account/progress database, server logs | Germany/Finland, EU/EEA `[[CONFIRM: exact region and DPA]]` |
| Cloudflare | processor for DNS, CDN, security and proxying | IP, user agent, request metadata, security events | `[[CONFIRM: Cloudflare DPA, EU settings, transfer mechanism]]` |

The account/progress database is intended to be hosted in the EU/EEA on Hetzner. The controller does not intend to transfer the account/progress database outside the EEA. Any technical transfers by Google Identity or Cloudflare must be confirmed before launch and covered by valid GDPR transfer mechanisms.

### 8. Cookies and localStorage

The app uses strictly necessary session and CSRF cookies. Separate consent is not required for these cookies because they are necessary to provide the requested service.

The browser may use localStorage for offline progress and preferences. The app does not use advertising or tracking cookies. Any optional analytics, marketing or tracking technology must be opt-in and reflected in this notice before use.

### 9. Your Rights

You may exercise GDPR rights of access, rectification, erasure, restriction, portability, objection, withdrawal of consent and complaint to a supervisory authority. Contact: `[[PLACEHOLDER: DPO or privacy contact email]]`.

Romanian supervisory authority: Autoritatea Națională de Supraveghere a Prelucrării Datelor cu Caracter Personal (ANSPDCP), `https://www.dataprotection.ro/`.

### 10. Security and Changes

Proposed safeguards include OAuth/OIDC login, `HttpOnly`, `Secure` and `SameSite` cookies, CSRF protection, TLS, admin access controls, security logs, limited backups, data minimisation and deletion workflows. `[[CONFIRM: final technical and organisational measures]]`

We may update this notice. Material changes will be announced in-app and, where required, renewed consent will be requested.
