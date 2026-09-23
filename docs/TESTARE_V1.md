# Testare V1 — Cât de român ești?

Pentru participanți de vârste diferite, pe telefon sau calculator. O sesiune durează
aproximativ 20–30 de minute; poți opri oricând. Nu ai nevoie de cont.

## Înainte să începi

Organizatorul îți dă adresa jocului. Uită-te la insigna mică de sub butonul de sunet
din pagina principală (de exemplu **V1.0.1**) și scrie textul ei în formular. Notează
telefonul sau calculatorul, browserul și dacă ai mărit textul. Nu trimite numele complet,
adresa sau alte date personale. Pentru participanții sub 16 ani, un adult completează
și trimite formularul.

Scorul este un rezultat de joc, nu o evaluare a identității sau a valorii tale.
Cuvintele necunoscute și explicațiile neclare ne ajută să îmbunătățim jocul.

## Încearcă cele șase jocuri

| Joc | Ce încerci | La ce să fii atent |
|---|---|---|
| Alchimie | Combină două cuvinte în „Explorează”; încearcă apoi „Provocări”. | Ai o idee firească pentru prima combinație? Înțelegi de ce apare rezultatul? |
| Intrusul | Alege cuvântul care nu se potrivește. | Există un singur răspuns convingător? Explicația este adevărată pentru toate celelalte cuvinte? |
| Perechi | Găsește cele patru perechi. | Mai vezi o altă pereche care ar trebui acceptată? |
| Conexiuni | Alege câte patru cuvinte care au ceva precis în comun. | După aflarea temei, fiecare cuvânt se potrivește fără explicații forțate? |
| Cald sau Rece | Scrie câteva cuvinte și urmărește cât de aproape ești de cuvântul ascuns. | Cuvintele apropiate ca sens primesc reacții care te ajută? |
| Lanțul Cuvintelor | Mergi din cuvânt în cuvânt, de la start până la țintă. | Legăturile sunt ușor de explicat? Ai mai mult de un drum posibil? |

În timpul sesiunii, deschide „Reguli și ajutor”. Fă intenționat o greșeală, apoi încearcă
un indiciu: în unele jocuri, indiciul apare abia după una sau două greșeli. În Alchimie,
la „Explorează”, ajutorul se numește „Cum explorezi” și „O idee?”.
Reîncarcă pagina în mijlocul unui joc și verifică dacă poți continua.
După un rezultat, pornește încă un joc. Din „Circuitul de azi”, alege un joc și apasă
„Joacă provocarea zilei”.
Pe telefon, verifică dacă poți apăsa comod și citi fără să derulezi în lateral.
Pe calculator, încearcă tastele Tab și Enter; poți mări textul din browser.

Nu trebuie să termini fiecare joc. Dacă te blochezi, spune ce ai încercat și ce te
așteptai să se întâmple; renunțarea este și ea o informație utilă. Poți renunța din
„Opțiuni de joc”: „Arată răspunsul” în Cald sau Rece, „Începe alt lanț” în Lanțul Cuvintelor.

### Știm deja (nu e nevoie să raportezi)

- Unele descrieri de cuvinte nu au încă diacritice; le corectăm într-o etapă următoare.
- Pentru unele teme la dificultatea Greu există o singură tablă, deci se poate repeta.
- În Alchimie, un joc Greu pe unele teme poate porni în câteva secunde.

## Trimite feedback organizatorului

Copiază formularul și completează câte un exemplu concret. Nu există trimitere
automată în aplicație; folosește canalul convenit cu organizatorul.

```text
Versiune (textul insignei din pagina principală):
Telefon/calculator și browser:
Text mărit? nu / da (cât):
Interval de vârstă (opțional): sub 12 / 12–15 / 16–29 / 30–59 / 60+
Joc și mod (joc liber / provocarea zilei / Alchimie: Explorează sau Provocări):
Pașii până la problemă:
Cuvintele sau explicația afișată:
Ce mă așteptam să se întâmple:
Ce s-a întâmplat:
Pot repeta problema? da / nu / nu știu
Ușor de început? 1–5
Explicații convingătoare? 1–5
Aș mai juca? da / poate / nu — de ce:
```

O captură a ecranului sau rezultatul copiat poate ajuta. Evită capturile cu informații
personale din alte file.

Scorurile și colecția Alchimie se păstrează doar în browserul folosit. După primul joc
terminat, secțiunea de istoric din pagina principală are butonul „Export”. Exportul
salvează doar scorurile jocurilor terminate, nu jocul în desfășurare și nici colecția
Alchimie. O filă privată sau ștergerea datelor browserului pierde colecția.

## Pentru organizator

### Pe același calculator

Dintr-un mediu Python pregătit conform [README](../README.md), rulează din rădăcina
repozitoriului:

```console
python -m cat_de_roman_esti.web --host 127.0.0.1 --port 8000
```

Deschide `http://127.0.0.1:8000`. Această adresă nu funcționează de pe alte dispozitive.

### Pe telefoane din aceeași rețea Wi-Fi

Pornește serverul pe toate interfețele și lasă-l pornit toată sesiunea; jocurile în
desfășurare sunt ținute în memoria serverului și se pierd la repornire:

```console
python -m cat_de_roman_esti.web --host 0.0.0.0 --port 8000
```

Află adresa calculatorului în rețea (`ipconfig` pe Windows, `ip addr` pe Linux) și
deschide pe telefoane `http://<adresa>:8000`. Verifică insigna versiunii. Folosește
doar o rețea Wi-Fi privată, de încredere; dacă Windows întreabă, permite accesul doar
pentru rețele private. Lasă `CAT_ACCOUNTS_ENABLED` nesetat. Dacă ai setat `CAT_DOMAIN`
sau `CAT_ALLOWED_HOSTS`, adaugă adresa calculatorului în `CAT_ALLOWED_HOSTS`. Telefoanele
conectate prin date mobile nu pot ajunge la această adresă.

Include în test cel puțin un iPhone (Safari), un telefon Android și un participant
care folosește text mărit. Un joc Alchimie Greu care pornește lent încetinește puțin
și ceilalți jucători pentru câteva secunde.

### Test la distanță

Pentru participanți din alte rețele, folosește o instalare pregătită conform
[ghidului de publicare](DEPLOY.md), cu acces anonim. Rezultatele verificărilor tehnice
și limitele cunoscute sunt în [revizia V1](reviews/v1-testing-release/README.md) și în
[STATUS](STATUS.md).
