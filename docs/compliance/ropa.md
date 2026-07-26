# Registrul activităților de prelucrare / Article 30 ROPA

**DRAFT — not legal advice — requires review by a qualified Romanian data-protection lawyer before publication.**

**DRAFT — REQUIRES LEGAL REVIEW**

Operator: `[[PLACEHOLDER: controller legal name / interim personal identity]]`  
Adresă: `[[PLACEHOLDER: controller address]]`  
Contact: `[[PLACEHOLDER: DPO or privacy contact email]]`  
Domeniu / aplicație: `[[PLACEHOLDER: domain name]]`  
Data ultimei actualizări: `[[PLACEHOLDER: last updated date]]`

## Registru art. 30 GDPR

| Activitate | Persoane vizate | Categorii de date | Scop | Temei legal | Destinatari / împuterniciți | Transferuri | Retenție | Măsuri de securitate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Autentificare cont cu Google | utilizatori, inclusiv minori; părinți/tutori unde e cazul | e-mail, nume, avatar, Google `sub`, identificator cont intern, consimțământ și vârstă | creare cont, login, administrare cont | art. 6(1)(b); art. 6(1)(a) pentru consimțământ opțional și copii; art. 8 GDPR | Google Identity; Hetzner; Cloudflare | baza cont în UE/SEE; transferuri Google/Cloudflare `[[CONFIRM]]` | implementarea curentă șterge imediat profilul și `ConsentRecord` prin cascadă; păstrarea consimțământului 3 ani este propusă, neimplementată și necesită confirmarea temeiului | OIDC, scope-uri minime, TLS, cookie `HttpOnly/Secure/SameSite`, CSRF, access control |
| Copie privată a rezultatelor terminate | utilizatori autentificați, inclusiv minori | joc, scor, descriere, timestamp și opțional ID puzzle, dată zilnică, dificultate, categorie; maximum 500 de rânduri | backup privat solicitat de utilizator și răspuns DSAR; fără restaurare sau combinare automată în browser | art. 6(1)(b); art. 6(1)(a)/art. 8 pentru sub 16 | Hetzner; Cloudflare pentru trafic | stocare UE/SEE pe Hetzner `[[CONFIRM: region]]`; fără transfer intenționat al bazei de cont în afara SEE | durata contului; ștergere odată cu contul `[[CONFIRM]]` | minimizare, consimțământ curent, control acces, limită 500, ștergere la cerere |
| Evitare repetări și clasament opțional | utilizatori autentificați cu consimțământ curent; numai utilizatori cu opt-in pentru afișare | `PlayedPuzzle`: joc, ID opac al pachetului curatoriat și timestamp de terminare, niciodată joc minat sau soluție; `VerifiedBest`: joc, record verificat, poreclă și preferință de vizibilitate | evitarea repetării puzzle-urilor curatoriate; publicarea recordului verificat numai cu opt-in | art. 6(1)(b); art. 6(1)(a), după caz | Hetzner; Cloudflare pentru trafic; răspunsul public conține poreclă, joc, scor, rang de competiție și markerul `is_me` limitat la cerere; poate include un rând personal limitat în afara topului | stocare UE/SEE pe Hetzner `[[CONFIRM: region]]`; răspunsul public nu conține ID de pachet, soluție sau identitate Google | durata contului; ștergere imediată prin cascadă odată cu contul | separare de istoricul încărcat, poreclă aleasă explicit, opt-in implicit oprit, consimțământ verificat |
| Logare securitate și prevenire abuz | vizitatori, utilizatori autentificați, minori, administratori | IP, user agent, request metadata, timestamp, evenimente login, erori, identificatori sesiune | securitate, prevenire atacuri, depanare, integritate serviciu | art. 6(1)(f) interes legitim; art. 6(1)(c) unde există obligație legală | Cloudflare; Hetzner; personal autorizat | Cloudflare poate procesa date în afara SEE `[[CONFIRM: DPA/SCC/TIA]]`; server logs UE/SEE `[[CONFIRM]]` | 90 zile, mai mult pentru incidente active `[[CONFIRM]]` | rate limiting, firewall/CDN, access logs, TLS, acces limitat, rotație loguri |
| Administrare cereri DSAR și ștergere | utilizatori, părinți/tutori, reprezentanți legali | date de contact, dovadă identitate minimă, conținut cerere, răspunsuri, audit trail | răspuns la drepturi GDPR și cereri parentale | art. 6(1)(c); art. 6(1)(f) apărarea drepturilor | furnizor e-mail/ticketing `[[PLACEHOLDER: provider]]`; Hetzner | `[[CONFIRM: email provider transfer]]` | 3 ani după închiderea cererii `[[CONFIRM]]` | verificare identitate proporțională, acces limitat, evidență cereri |
| Gestionare incidente de securitate | utilizatori afectați, vizitatori, minori, personal | loguri relevante, date cont afectate, corespondență, evaluare risc | detectare, investigare, notificare GDPR în 72h unde e cazul | art. 6(1)(c); art. 6(1)(f) | Hetzner, Cloudflare, consultanți juridici/tehnici `[[CONFIRM]]`, ANSPDCP unde e cazul | depinde de furnizori și consultanți `[[CONFIRM]]` | durata incidentului + 3 ani `[[CONFIRM]]` | incident response, audit trail, acces need-to-know, containment |

## Note

- Operatorul trebuie să confirme dacă este obligatorie desemnarea unui DPO. `[[CONTROLLER DECISION]]`
- Toate contractele cu persoanele împuternicite trebuie să includă cerințele art. 28 GDPR. `[[PLACEHOLDER: DPA references]]`
- Pentru orice transfer în afara SEE trebuie documentat mecanismul legal, inclusiv SCC/TIA unde este necesar. `[[CONFIRM]]`
