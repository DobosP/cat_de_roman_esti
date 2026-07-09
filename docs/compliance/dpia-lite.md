# DPIA Lite — evaluare de impact pentru datele minorilor

**DRAFT — not legal advice — requires review by a qualified Romanian data-protection lawyer before publication.**

**DRAFT — REQUIRES LEGAL REVIEW**

Document: Data Protection Impact Assessment screening  
Aplicație: `cât-de-român-ești`  
Data: `[[PLACEHOLDER: assessment date]]`  
Operator: `[[PLACEHOLDER: controller legal name / interim personal identity]]`  
Responsabil: `[[PLACEHOLDER: responsible person / DPO]]`

## 1. Rezumat

Aplicația este un joc web educațional gratuit, în limba română, destinat publicului larg și accesibil minorilor. Funcționalitatea nouă permite conturi opționale prin Google și salvarea progresului pe server.

Prelucrarea include date de cont, progres în joc și loguri tehnice. Deoarece serviciul este child-facing și implică date ale minorilor, se recomandă o evaluare DPIA completată și semnată înainte de lansare.

## 2. Descrierea prelucrării

| Element | Descriere |
| --- | --- |
| Persoane vizate | utilizatori ai aplicației, inclusiv minori; părinți/tutori pentru consimțământ |
| Date | e-mail, nume, avatar, Google `sub`, scoruri, completări zilnice, per-puzzle bests, loguri IP/user agent, consimțământ/vârstă |
| Surse | Google Identity, browser, server aplicație, Cloudflare |
| Scopuri | autentificare, salvare progres, securitate, prevenire abuz, răspuns DSAR |
| Temeiuri | art. 6(1)(b), art. 6(1)(a), art. 6(1)(f), art. 6(1)(c); art. 8 pentru consimțământ copii |
| Destinatari | Google Identity, Hetzner, Cloudflare, persoane autorizate intern |
| Transferuri | baza cont/progres în UE/SEE; transferuri tehnice ale Google/Cloudflare de confirmat |
| Retenție | vezi `data-retention-and-dsar.md`; perioade marcate `[[CONFIRM]]` |

## 3. Necesitate și proporționalitate

| Întrebare | Evaluare draft |
| --- | --- |
| Este contul necesar pentru joc? | Nu pentru jocul de bază; da pentru sincronizarea progresului pe server. Contul trebuie să fie opțional. |
| Sunt datele Google minime? | Trebuie solicitate doar scope-uri OIDC minime: `openid email profile`. `[[CONTROLLER DECISION: confirm scopes]]` |
| Este progresul necesar? | Da, pentru funcția cerută de utilizator: istoric scoruri, completări zilnice, per-puzzle bests. |
| Sunt logurile necesare? | Da, limitat la securitate, depanare și prevenire abuz. Retenția trebuie să fie scurtă. |
| Există profilare? | Nu trebuie implementată profilare publicitară sau scoring cu efecte semnificative. |
| Există alternative mai puțin intruzive? | Joc fără cont și progres local în localStorage trebuie să rămână disponibile unde practic. |

## 4. Riscuri pentru copii

| Risc | Impact | Probabilitate draft | Măsuri propuse |
| --- | --- | --- | --- |
| Crearea contului de către copil sub 16 fără consimțământ parental | ridicat | medie | age gate, consimțământ parental verificabil sau blocare cont |
| Expunere publică a progresului/profilului minorului | ridicat | scăzută dacă nu există profil public | conturi private implicit, fără leaderboard public cu identitate reală |
| Colectare excesivă prin Google scopes | mediu | medie | scope-uri minime, fără acces la contacte/Drive/calendar |
| Reidentificare prin avatar/nume real | mediu | medie | nu afișa numele/avatarul public; permite ascundere/ștergere |
| Păstrare excesivă a datelor | mediu | medie | retenție documentată, ștergere cont, ștergere conturi inactive `[[CONFIRM]]` |
| Acces neautorizat la cont/progres | ridicat | medie | OIDC, TLS, cookie-uri securizate, CSRF, control acces, logging |
| Transferuri internaționale neclare | mediu | medie | DPA-uri, SCC/TIA unde e cazul, confirmare setări Google/Cloudflare |
| Dark patterns sau consimțământ neclar | mediu | medie | UX simplu, limbaj pe înțelesul copiilor, refuz la fel de ușor ca acceptare |
| Publicitate/profilare pentru minori | ridicat | scăzută dacă nu se implementează | interdicție de tracking ads și profilare publicitară |

## 5. Măsuri obligatorii înainte de go-live

| Măsură | Status |
| --- | --- |
| Conturi private implicit; fără profil public al minorilor | `[[CONTROLLER DECISION]]` |
| Joc utilizabil fără cont unde practic | `[[CONTROLLER DECISION]]` |
| Age gate la primul Google login | `[[CONTROLLER DECISION]]` |
| Flux consimțământ parental pentru sub 16 sau blocare cont | `[[CONTROLLER DECISION]]` |
| Înregistrare consimțământ: timestamp, versiune documente, hash text, metodă | `[[CONTROLLER DECISION]]` |
| Scope-uri Google minime | `[[CONTROLLER DECISION]]` |
| Ștergere cont și export date în aplicație | `[[CONTROLLER DECISION]]` |
| Retenție loguri 90 zile sau alt termen aprobat | `[[CONFIRM]]` |
| DPA-uri cu Google, Hetzner, Cloudflare | `[[PLACEHOLDER: DPA references]]` |
| Fără cookie-uri de tracking sau advertising | `[[CONTROLLER DECISION]]` |
| Revizuire juridică GDPR/Legea 190/2018/DSA | `[[PLACEHOLDER: lawyer sign-off]]` |

## 6. Consultare prealabilă ANSPDCP — art. 36 GDPR

Verdict draft: consultarea prealabilă ANSPDCP nu pare necesară dacă măsurile de mai sus sunt implementate, deoarece riscurile ridicate pentru minori sunt reduse prin minimizare, consimțământ parental, lipsa profilării, conturi private și ștergere ușoară.

Aceasta este o concluzie preliminară. Dacă operatorul decide să adauge profiluri publice, leaderboard cu identitate reală, analiză comportamentală extinsă, publicitate, date sensibile, decizii automate cu efecte semnificative sau transferuri necontrolate, riscul rezidual trebuie reevaluat și consultarea ANSPDCP poate deveni necesară.

`[[CONTROLLER DECISION: final residual-risk rating and Art. 36 decision]]`

## 7. Risc rezidual

| Arie | Risc rezidual propus |
| --- | --- |
| Autentificare și cont | mediu-scăzut după age gate și consimțământ parental |
| Progres joc | scăzut dacă nu este public și se poate șterge ușor |
| Loguri tehnice | scăzut spre mediu, dependent de retenție și acces |
| Transferuri furnizori | mediu până la confirmarea DPA/SCC/TIA |
| Protecția minorilor | mediu-scăzut dacă nu există profilare, publicitate sau funcții sociale |

Semnătură operator: `[[PLACEHOLDER: name, role, date]]`
