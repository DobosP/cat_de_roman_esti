# Testare V1 — Cât de român ești?

Pentru participanți de vârste diferite, pe telefon sau calculator. O sesiune durează
aproximativ 20–30 de minute; poți opri oricând. Nu ai nevoie de cont.

## Înainte să începi

Verifică insigna **V1** din pagina principală. Organizatorul îți oferă adresa versiunii
instalate pentru test. Notează modelul telefonului sau calculatorul, browserul și dacă
ai mărit textul. Nu trimite numele complet, adresa sau alte date personale.

Scorul este un rezultat de joc, nu o evaluare a identității sau a valorii tale.
Cuvintele necunoscute și explicațiile neclare ne ajută să îmbunătățim jocul.

## Încearcă cele șase jocuri

| Joc | Ce încerci | La ce să fii atent |
|---|---|---|
| Alchimie | Combină două concepte în explorare; încearcă apoi o provocare. | Ai o idee firească pentru prima combinație? Înțelegi de ce apare rezultatul? |
| Intrusul | Alege cuvântul care nu se potrivește. | Există un singur răspuns convingător? Explicația este adevărată pentru toate celelalte cuvinte? |
| Perechi | Găsește cele patru perechi. | Mai vezi o altă pereche care ar trebui acceptată? |
| Conexiuni | Selectează patru cuvinte care au ceva precis în comun. | După aflarea temei, fiecare cuvânt se potrivește fără explicații forțate? |
| Cald sau Rece | Scrie câteva cuvinte și urmărește apropierea de țintă. | Cuvintele apropiate în sens primesc reacții care te ajută? |
| Lanțul Cuvintelor | Leagă punctul de plecare de țintă. | Legăturile sunt ușor de explicat? Ai mai mult de un drum plauzibil? |

În timpul sesiunii, deschide „Reguli și ajutor”, încearcă un indiciu și fă intenționat
o greșeală. Reîncarcă pagina în mijlocul unui joc și verifică dacă poți continua.
După un rezultat, pornește încă un joc. Încearcă și o provocare din circuitul zilei.
Pe telefon, verifică dacă poți apăsa comod și citi fără derulare laterală.
Pe calculator, încearcă Tab și Enter; poți mări textul din browser.

Nu trebuie să termini fiecare tablă. Dacă te blochezi, spune ce ai încercat și ce
te așteptai să se întâmple; renunțarea la o rundă este informație utilă.

## Trimite feedback organizatorului

Copiază formularul și completează câte un exemplu concret. Nu există trimitere
automată în aplicație; folosește canalul convenit cu organizatorul.

```text
Versiune: V1
Telefon/calculator și browser:
Joc și mod (liber / provocarea zilei / explorare):
Pașii până la problemă:
Cuvintele sau explicația afișată:
Ce mă așteptam să se întâmple:
Ce s-a întâmplat:
Pot repeta problema? da / nu / nu știu
Ușor de început? 1–5
Explicații convingătoare? 1–5
Aș mai juca? da / poate / nu — de ce:
```

O captură a tablei sau rezultatul copiat poate ajuta. Evită capturile cu informații
personale din alte file. Organizatorul poate grupa feedbackul pe intervale de vârstă
opționale, fără nume sau date exacte de naștere.

Istoricul și colecția se păstrează local, în browserul folosit. Exportă istoricul din
pagina principală înainte de a șterge datele browserului. Exportul scorurilor nu
este un transfer al unei runde active; colecția Alchimie are propriul mecanism de salvare.

## Pornire locală pentru organizator

Dintr-un mediu Python pregătit conform [README](../README.md), rulează din rădăcina
repozitoriului:

```console
python -m cat_de_roman_esti.web --host 127.0.0.1 --port 8000
```

Deschide `http://127.0.0.1:8000` pe același calculator. Această adresă locală nu este
accesibilă automat de pe alte dispozitive. Pentru un test distribuit, folosește o
instalare pregătită conform [ghidului de publicare](DEPLOY.md), cu acces anonim.
Rezultatele verificărilor tehnice și limitele cunoscute sunt în
[revizia V1](reviews/v1-testing-release/README.md) și [STATUS](STATUS.md).
