# Retenție date, DSAR, ștergere și incidente / Retention, DSAR, Deletion and Breach Checklist

**DRAFT — not legal advice — requires review by a qualified Romanian data-protection lawyer before publication.**

**DRAFT — REQUIRES LEGAL REVIEW**

Aplicație: `cât-de-român-ești`  
Operator: `[[PLACEHOLDER: controller legal name / interim personal identity]]`  
Contact privacy: `[[PLACEHOLDER: DPO or privacy contact email]]`  
Data: `[[PLACEHOLDER: effective date]]`

## 1. Program de retenție

| Date | Sistem | Retenție propusă | Acțiune la expirare |
| --- | --- | --- | --- |
| Profil cont | baza de date aplicație | durata contului | ștergere sau anonimizare în 30 zile de la ștergerea contului `[[CONFIRM]]` |
| Google `sub`, e-mail, nume, avatar | baza de date aplicație | durata contului | ștergere odată cu contul |
| Progres joc | baza de date aplicație | durata contului | ștergere odată cu contul |
| Conturi inactive | baza de date aplicație | 24 luni de inactivitate, după notificare unde practic | ștergere sau anonimizare `[[CONTROLLER DECISION]]` |
| Loguri aplicație | servere Hetzner | 90 zile | rotație și ștergere automată `[[CONFIRM]]` |
| Loguri Cloudflare | Cloudflare | termenul din plan/contract | configurare minimă disponibilă `[[CONFIRM]]` |
| Backup-uri | storage backup `[[PLACEHOLDER]]` | 30 zile | suprascriere automată; ștergerea din backup la rotație `[[CONFIRM]]` |
| Consimțământ și acceptări | baza de date aplicație | durata contului + 3 ani | ștergere după termen `[[CONFIRM with counsel]]` |
| DSAR și corespondență | e-mail/ticketing `[[PLACEHOLDER]]` | 3 ani după închidere | ștergere/arhivare limitată `[[CONFIRM]]` |
| Incident records | incident register | incident + 3 ani | ștergere după termen `[[CONFIRM]]` |

## 2. Cereri privind drepturile persoanelor vizate

Canale:

- în aplicație: `[[PLACEHOLDER: account settings path, e.g. Settings > Account > Export/Delete]]`;
- e-mail: `[[PLACEHOLDER: DPO or privacy contact email]]`;
- pentru părinți/tutori: același e-mail, cu verificare proporțională a relației cu copilul.

Drepturi acoperite: acces, rectificare, ștergere, restricționare, portabilitate, opoziție, retragere consimțământ.

Termene:

- confirmare primire: 7 zile calendaristice `[[CONFIRM]]`;
- răspuns final: cel mult o lună de la primire;
- prelungire: până la două luni suplimentare pentru cereri complexe, cu informare în prima lună;
- cereri de ștergere cont: executare tehnică în maximum 30 zile `[[CONFIRM]]`.

## 3. Procedură DSAR

1. Înregistrează cererea în registrul DSAR: dată, canal, solicitant, drept invocat, cont afectat, termen limită.
2. Verifică identitatea proporțional: login existent, link trimis la e-mailul contului sau alte informații minime. Nu cere documente de identitate decât dacă este necesar și proporțional.
3. Pentru părinte/tutore, verifică legătura cu copilul prin metoda aprobată: `[[CONTROLLER DECISION: parent verification method]]`.
4. Identifică datele în sistem: cont, progres, loguri rezonabil căutabile, consimțământ, corespondență.
5. Aplică excepțiile legale unde este cazul și documentează motivul.
6. Răspunde în limbaj clar. Pentru copii, folosește explicații simple.
7. Execută cererea: export, corectare, ștergere, restricționare sau retragere consimțământ.
8. Închide cererea și păstrează evidența conform retenției.

## 4. Export de date

Format recomandat: JSON sau CSV comprimat.

Conținut export:

- profil cont: e-mail, nume, avatar URL dacă este stocat, Google `sub` sau identificator pseudonimizat;
- progres: scoruri, completări, per-puzzle bests, timestamp-uri;
- consimțăminte: versiuni documente, timestamp, metodă;
- setări cont.

Nu include date care ar afecta securitatea serviciului sau drepturile altor persoane.

## 5. Ștergere cont în aplicație

Cerință produs:

- locație: `[[PLACEHOLDER: Settings > Account > Delete account]]`;
- confirmare: reautentificare sau confirmare prin e-mail;
- avertizare clară: contul, progresul server-side și istoricul scorurilor vor fi șterse;
- pentru sub 16: părintele/tutorele poate retrage consimțământul și declanșa ștergerea;
- după ștergere: revocare sesiuni active, ștergere progres, dezlegare de Google `sub`, păstrare minimă a evidenței legale;
- localStorage: oferă buton separat „Șterge progresul de pe acest dispozitiv”.

## 6. Checklist incident și notificare 72 ore

Declanșator: orice incident care duce accidental sau ilegal la distrugerea, pierderea, modificarea, divulgarea neautorizată sau accesul neautorizat la date personale.

În primele 24 ore:

- identifică incidentul, sistemele afectate și perioada;
- conține incidentul: revocare chei, suspendare acces, patch, blocare trafic;
- păstrează logurile relevante;
- estimează categoriile de persoane afectate, inclusiv dacă sunt minori;
- estimează datele afectate: cont, progres, IP, loguri, consimțământ;
- informează responsabilul intern și avocatul/DPO: `[[PLACEHOLDER: incident contacts]]`.

În 48 ore:

- evaluează riscul pentru drepturile și libertățile persoanelor;
- decide dacă notificarea ANSPDCP este obligatorie;
- pregătește notificarea: natura incidentului, categorii și număr aproximativ de persoane/date, consecințe probabile, măsuri luate;
- decide dacă utilizatorii trebuie informați direct, mai ales dacă riscul este ridicat.

Până la 72 ore de la momentul luării la cunoștință:

- notifică ANSPDCP dacă incidentul este susceptibil să genereze risc pentru drepturile și libertățile persoanelor;
- dacă notificarea întârzie, documentează motivele;
- notifică persoanele vizate fără întârzieri nejustificate dacă riscul este ridicat;
- actualizează registrul incidentelor.

După incident:

- finalizează analiza cauzei;
- aplică măsuri corective;
- verifică furnizorii afectați;
- actualizează DPIA, ROPA și procedurile;
- documentează lecțiile și deciziile.

## 7. EN Summary

This document sets the draft retention schedule, DSAR/export/deletion procedure and 72-hour breach checklist. GDPR response deadline is one month, extendable by two months for complex requests. Breaches likely to risk individuals’ rights must be notified to ANSPDCP within 72 hours of awareness; high-risk breaches also require notification to affected individuals.
