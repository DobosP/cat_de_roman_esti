# Spec produs — age gate și consimțământ / Product Spec — Age Gate and Consent

**DRAFT — not legal advice — requires review by a qualified Romanian data-protection lawyer before publication.**

**DRAFT — REQUIRES LEGAL REVIEW**

Aplicație: `cât-de-român-ești`  
Feature: primul login cu Google, cont opțional, salvare progres server-side  
Owner: `[[PLACEHOLDER: product/engineering owner]]`  
Data: `[[PLACEHOLDER: spec date]]`

## 1. Obiectiv

La primul „Sign in with Google”, aplicația trebuie să stabilească dacă utilizatorul poate crea un cont:

- 16+ ani: poate accepta Termenii și Politica de confidențialitate;
- sub 16 ani în România: necesită consimțământ verificabil de la părinte/tutore sau blocarea contului;
- fără consimțământ valid: nu se creează cont server-side și nu se salvează progres pe server.

Contul este opțional. Jocul fără cont și progresul local trebuie să rămână disponibile unde practic.

## 2. Ecrane UX

### 2.1 Înainte de Google login

Text scurt:

„Contul este opțional. Îl folosim pentru a salva progresul tău pe server. Dacă ai sub 16 ani, avem nevoie de acordul părintelui sau tutorelui.”

Acțiuni:

- „Continuă cu Google”
- „Joacă fără cont”

Linkuri:

- Politica de confidențialitate: `[[PLACEHOLDER: URL]]`
- Termeni și condiții: `[[PLACEHOLDER: URL]]`

### 2.2 Age gate după întoarcerea de la Google, înainte de creare cont

Variantă recomandată: bandă de vârstă, nu data completă a nașterii, pentru minimizarea datelor.

Întrebare: „Ce vârstă ai?”

Opțiuni:

- „16 ani sau mai mult”
- „Sub 16 ani”

Alternativă: data nașterii, doar dacă avocatul o aprobă și există motiv operațional. Dacă se folosește data nașterii, stochează doar rezultatul calculat sau anul/banda de vârstă, nu data completă, dacă nu este necesară. `[[CONTROLLER DECISION]]`

### 2.3 Acceptare pentru 16+

Afișează:

- checkbox: „Am citit și accept Termenii și condițiile.”
- checkbox: „Am citit Politica de confidențialitate.”
- buton: „Creează cont”
- link: „Joacă fără cont”

Nu pre-bifa checkboxurile.

### 2.4 Flux pentru sub 16

Opțiunea A — blocare cont:

- mesaj: „Pentru cont și progres salvat pe server avem nevoie de acordul părintelui sau tutorelui. Poți continua să joci fără cont.”
- acțiuni: „Joacă fără cont”, „Înapoi”

Opțiunea B — consimțământ parental verificabil:

- cere e-mailul părintelui/tutorelui;
- trimite un link unic cu expirare;
- pagina pentru părinte explică datele, scopurile, drepturile și ștergerea;
- părintele acceptă Termenii și Politica de confidențialitate pentru copil;
- după confirmare, contul copilului este activat.

Metode acceptabile de verificare, de ales cu avocatul:

| Metodă | Avantaje | Riscuri / note |
| --- | --- | --- |
| Parent email double opt-in | simplu, implementabil, minim intruziv | verifică acces la e-mail, nu dovedește complet identitatea parentală |
| Confirmare prin cont adult | mai puternică dacă există mecanism adult | mai complexă; poate colecta mai multe date |
| Semnătură electronică / document | mai puternică | disproporționată pentru joc gratuit, colectează date excesive |
| Blocare cont sub 16 | cel mai simplu și minim | limitează funcția de salvare server-side pentru copii |

Decizie necesară: `[[CONTROLLER DECISION: choose block-under-16 or parental-consent flow]]`

## 3. Stări de cont

| Stare | Descriere | Acces |
| --- | --- | --- |
| `no_account` | utilizator neautentificat | joc local, localStorage |
| `pending_age_gate` | Google login primit, cont intern nefinalizat | nu salva progres server-side |
| `pending_parent_consent` | utilizator sub 16, e-mail părinte trimis | nu salva progres server-side, sau păstrează temporar doar date minime `[[CONTROLLER DECISION]]` |
| `active_adult_or_16plus` | 16+ cu acceptări | cont și progres server-side |
| `active_child_parent_consented` | sub 16 cu consimțământ parental | cont privat și progres server-side |
| `blocked_under_16` | sub 16 fără consimțământ sau flux blocat | fără cont; joc local |
| `deleted` | cont șters | fără acces, date șterse/anomizate |

## 4. Date de stocat pentru consimțământ

| Câmp | Exemplu | Notă |
| --- | --- | --- |
| `user_id` | UUID intern | nu folosi e-mail ca cheie primară |
| `age_band` | `16_plus` / `under_16` | preferat față de data nașterii |
| `parent_email_hash` | hash + salt/pepper `[[CONFIRM]]` | dacă se folosește flux parental |
| `consent_type` | `tos`, `privacy`, `parental` | granular |
| `consent_status` | `granted`, `withdrawn`, `expired` | audit |
| `document_version` | `privacy-v1.0` | versiunea afișată |
| `document_url` | URL public | document publicat |
| `text_hash` | SHA-256 al textului afișat | dovadă exactă |
| `timestamp_utc` | ISO 8601 | obligatoriu |
| `ip_truncated_or_full` | `[[CONTROLLER DECISION]]` | minimizare; full IP doar dacă justificat |
| `user_agent` | string sau hash | minimizare |
| `method` | `self_16plus`, `parent_email_double_opt_in` | audit |
| `withdrawn_at` | ISO 8601 | dacă se retrage |

## 5. Reguli backend

- Nu crea cont activ înainte de finalizarea age gate + acceptări.
- Nu salva progres server-side pentru `pending_age_gate`, `pending_parent_consent` sau `blocked_under_16`, cu excepția unui buffer temporar aprobat și minim. `[[CONTROLLER DECISION]]`
- Scope-uri Google: `openid email profile`; nu cere Drive, Contacts, Calendar sau alte scope-uri.
- Nu afișa public nume, avatar, scoruri sau profiluri ale minorilor.
- Leaderboard-urile publice cu identitate reală sunt în afara acestui spec și necesită DPIA actualizat.
- Setează toate conturile ca private implicit.
- Permite ștergerea contului din setări.
- Permite export date din setări sau prin cerere.
- Permite retragerea consimțământului parental; efectul implicit este dezactivarea și ștergerea contului copilului după confirmare.
- La schimbarea materială a documentelor, cere reacceptare și salvează un nou record.

## 6. Cerințe de securitate

- Cookie sesiune: `HttpOnly`, `Secure`, `SameSite=Lax` sau `Strict` după testare.
- CSRF pentru formulare și mutații.
- Link parental: token random, one-time use, expiră în 7 zile `[[CONFIRM]]`.
- Rate limiting pentru age gate, email parental și login callbacks.
- Audit log pentru creare, consimțământ, retragere, ștergere.
- Nu loga tokenuri OAuth, ID tokenuri complete sau date sensibile inutile.
- Șterge automat stările `pending_*` expirate după 14 zile `[[CONFIRM]]`.

## 7. Copy minim pentru părinți

Pagina părintelui trebuie să explice:

- copilul dorește cont pentru salvarea progresului;
- date colectate: e-mail/nume/avatar Google, progres joc, loguri tehnice;
- scopuri: cont, progres, securitate;
- fără publicitate comportamentală și fără profil public implicit;
- dreptul de retragere și ștergere;
- contact: `[[PLACEHOLDER: privacy contact email]]`;
- linkuri către Politica de confidențialitate și Termeni.

## 8. Teste de acceptanță

| Test | Rezultat așteptat |
| --- | --- |
| utilizator alege „Joacă fără cont” | nu se creează cont, progresul rămâne local |
| 16+ acceptă documentele | cont activ, record consimțământ salvat |
| 16+ nu bifează checkboxurile | buton creare cont dezactivat |
| sub 16 fără flux parental | cont blocat, joc local disponibil |
| sub 16 cu părinte confirmat | cont activ copil, privat implicit, record parental salvat |
| link parental expirat | consimțământ refuzat/expirat, cont neactivat |
| părinte retrage consimțământul | cont copil dezactivat și ștergere declanșată |
| document nou publicat | utilizatorul trebuie să re-accepte dacă schimbarea este materială |
