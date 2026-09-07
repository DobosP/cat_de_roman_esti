// Answer-free guidance. Opening it never requests a clue or changes a round.
export const GAME_HELP = {
  alchimie: {
    goal: "Combină două concepte din inventar și descoperă idei legate de amândouă, până făurești ținta.",
    feedback: "După o descoperire, citește legăturile dintre rezultat și cele două concepte. Ele explică asocierea.",
    recovery: "Dacă nu apare nimic nou, schimbă un concept. „Utile” arată ce mai poate contribui; cere un indiciu când devine disponibil.",
  },
  intrusul: {
    goal: "Trei cuvinte au o legătură comună. Alege-l pe al patrulea, care nu aparține acelui grup.",
    feedback: "Un cuvânt marcat „ține de grup” este exclus dintre răspunsuri. Repetarea lui nu consumă o încercare.",
    recovery: "După prima greșeală, indiciul arată legătura celor trei. La final poți vedea grupul complet.",
  },
  perechi: {
    goal: "Găsește cele patru perechi. Fiecare are o legătură proprie; cuvintele nu trebuie să fie sinonime.",
    feedback: "A doua alegere verifică imediat perechea. Numele legăturii apare când o găsești; repetările greșite nu costă.",
    recovery: "Atinge din nou primul cuvânt ca să-l deselectezi. După două greșeli, poți cere marcarea unei perechi.",
  },
  conexiuni: {
    goal: "Împarte cele 16 cuvinte în patru grupuri de câte patru. Fiecare grup are o categorie comună.",
    feedback: "„Aproape: 3 din 4” înseamnă că trei din cele patru aparțin aceluiași grup. Păstrează ideea și schimbă o piesă.",
    recovery: "Poți deselecta sau amesteca piesele înainte de Verifică. Butonul Indiciu arată când poți primi ajutor.",
  },
  contexto: {
    goal: "Ghicește conceptul secret după sens. Cuvintele înrudite te pot apropia, dar câștigi când găsești ținta.",
    feedback: "#1 este ținta. Un număr mai mic înseamnă mai aproape; compară ultima încercare cu cea mai bună.",
    recovery: "Un cuvânt nerecunoscut nu consumă o încercare. Alege o sugestie, încearcă altă formulare sau cere un indiciu.",
  },
  lant: {
    goal: "Ajungi de la start la țintă prin concepte legate direct. Citește relația afișată lângă fiecare salt.",
    feedback: "Un salt valid poate apropia sau ocoli ținta. Urmărește mesajul de progres, nu doar faptul că mutarea a fost acceptată.",
    recovery: "Poți scrie alt concept legat de cel curent. Dacă te îndepărtezi, Înapoi este gratuit; indiciul te poate reorienta.",
  },
};
