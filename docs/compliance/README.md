# Compliance Document Pack — `cât-de-român-ești`

**DRAFT — not legal advice — requires review by a qualified Romanian data-protection lawyer before publication.**

**DRAFT — REQUIRES LEGAL REVIEW**

Acest director conține drafturi practice pentru lansarea conturilor opționale prin „Sign in with Google” și salvarea progresului pe server pentru aplicația web educațională `cât-de-român-ești`.

Documentele sunt intenționat incomplete în zonele unde lipsesc fapte juridice sau operaționale. Completați toate marcajele `[[PLACEHOLDER: ...]]`, `[[CONFIRM: ...]]` și `[[CONTROLLER DECISION: ...]]` înainte de publicare.

## Fișiere

| Fișier | Scop |
| --- | --- |
| `privacy-notice.md` | Politica de confidențialitate RO + EN |
| `terms-of-service.md` | Termeni și condiții RO + EN |
| `cookie-notice.md` | Notificare scurtă cookies/localStorage RO + EN |
| `dpia-lite.md` | Screening DPIA pentru datele minorilor |
| `ropa.md` | Registru art. 30 GDPR al activităților de prelucrare |
| `data-retention-and-dsar.md` | retenție, DSAR, ștergere cont și checklist incident 72 ore |
| `consent-and-age-gate-spec.md` | specificație produs pentru age gate și consimțământ |
| `README.md` | index și checklist go-live |

## Checklist înainte de go-live

### Identitate operator

- completați numele legal al operatorului;
- confirmați dacă operatorul este persoană fizică interim sau asociație/ONG;
- completați adresa, nr. de înregistrare și datele de contact;
- decideți dacă este necesar DPO sau contact privacy dedicat;
- obțineți semnătura avocatului român specializat în protecția datelor.

### Documente și publicare

- completați data efectivă și versiunile documentelor;
- publicați URL-urile finale pentru Privacy Notice, ToS și Cookie Notice;
- păstrați hash-ul textului fiecărei versiuni legale;
- pregătiți procesul de reacceptare la schimbări materiale;
- verificați traducerea EN față de textul RO.

### Copii și consimțământ

- decideți între blocarea conturilor sub 16 sau flux parental verificabil;
- implementați age gate la primul Google login;
- nu pre-bifați acceptările;
- stocați recordul de consimțământ: timestamp, versiune, text hash, metodă;
- setați conturile copiilor private implicit;
- nu adăugați profil public, chat sau leaderboard cu identitate reală fără DPIA nou.

### Furnizori și transferuri

- semnați/verificați DPA-urile art. 28 cu Google, Hetzner și Cloudflare;
- confirmați regiunile Hetzner Germania/Finlanda;
- confirmați setările Cloudflare pentru minimizare și transferuri;
- documentați mecanismele de transfer pentru Google/Cloudflare, inclusiv SCC/TIA unde este necesar;
- confirmați că baza cont/progres rămâne în UE/SEE.

### Implementare tehnică

- folosiți numai scope-uri Google minime: `openid email profile`;
- folosiți cookie-uri `HttpOnly`, `Secure`, `SameSite`;
- activați CSRF și rate limiting;
- nu logați tokenuri OAuth sau ID tokenuri complete;
- implementați export și ștergere cont din setări;
- implementați ștergerea localStorage separat;
- configurați retenția automată pentru loguri, backup-uri și stări pending;
- verificați că nu există cookie-uri de advertising/tracking.

### Operațional

- creați registrul DSAR;
- creați registrul incidentelor;
- desemnați persoanele care pot răspunde cererilor și incidentelor;
- testați exportul și ștergerea pe un cont demo;
- testați fluxul parental sau blocarea sub 16;
- pregătiți notificarea ANSPDCP pentru incidente, dacă va fi necesară;
- finalizați DPIA și decizia privind consultarea prealabilă art. 36 GDPR.

## Note importante

- În România, consimțământul copilului pentru servicii ale societății informaționale este valabil de la 16 ani. Sub 16 ani este necesar consimțământul părintelui sau tutorelui.
- ANSPDCP este autoritatea română de supraveghere.
- Nu introduceți publicitate comportamentală, tracking sau profilare pentru minori fără revizuire juridică majoră și DPIA actualizat.
- Aceste documente sunt drafturi de lucru, nu documente gata de publicare.
