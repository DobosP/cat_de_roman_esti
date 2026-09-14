"""Editorial source for the shared Alchimie kitchen world; never loaded by serving.

Pairs express a recognisable culinary idea, not a complete cooking instruction.
The generated candidate artifact requires independent factual and quality review.
"""

WORLD = {
    "id": "bucataria-romaneasca-v1",
    "title": "Bucătăria românească",
    "description": (
        "Descoperă ingrediente și preparate, apoi folosește-le în combinații noi. "
        "Perechile surprind ideea unui preparat, nu întreaga rețetă de gătit."
    ),
}

# Reviewed presentation corrections; the original KG record remains in snapshot.
DESCRIPTIONS = {
    "Compot": ("Fructe fierte în apă, de obicei îndulcite; "
               "se consumă proaspăt sau se păstrează la borcan."),
    "Ardei umpluți": "Ardei umpluți cu orez, legume și uneori carne, fierți într-un sos.",
    "Sarmale": "Frunze de varză sau de viță umplute cu orez, legume și uneori carne.",
    "Paste": "Preparat din aluat de făină, cu apă sau ou, modelat și apoi fiert.",
    "Tigaie": "Vas puțin adânc, folosit pentru prăjit și rumenit alimente.",
    "Cartof": "Tubercul comestibil, gătit prin fierbere, coacere sau prăjire.",
    "Ceapă": "Legumă cu bulb, folosită crudă sau gătită pentru gust și aromă.",
    "Miere": "Produs dulce făcut de albine din nectar sau mană.",
    "Scorțișoară": "Condiment aromat din scoarța unor arbori, folosit mai ales în deserturi.",
    "Semințe de floarea-soarelui": "Semințe cu miez comestibil, folosite și la halva sau ulei.",
    "Cașcaval": "Brânză cu pastă opărită, folosită în sandvișuri și preparate calde.",
    "Prună": "Fruct cu sâmbure, folosit proaspăt, în compoturi, dulcețuri și plăcinte.",
    "Căpșună": "Fruct roșu și aromat, consumat proaspăt sau în deserturi și conserve.",
    "Dovleac": "Plantă cu fruct mare; soiurile comestibile se folosesc și la plăcinte.",
    "Untură": "Grăsime animală topită și strecurată, folosită inclusiv în aluaturi fragede.",
    "Zer": "Lichid rămas după coagularea și scurgerea laptelui, folosit și la urdă.",
    "Oală": "Vas adânc pentru fierberea și gătirea alimentelor.",
    "Arpacaș": "Boabe de cereale decorticate, folosite fierte în diferite preparate.",
    "Iaurt": "Produs obținut prin fermentarea laptelui cu culturi de bacterii lactice.",
    "Grătar": "Mod de a frige alimente pe un suport încins, deasupra unei surse de căldură.",
    "Sandviș": "Gustare cu pâine și o umplutură sau un strat de ingrediente.",
    "Clătite": "Foi subțiri din aluat fluid, coapte în tigaie și servite dulci sau sărate.",
    "Pizza": "Preparat copt din aluat întins, acoperit cu sos, brânză și alte ingrediente.",
    "Cartofi prăjiți": "Bucăți de cartof prăjite în ulei sau altă grăsime.",
    "Șnițel": "Felie subțire de carne, de obicei acoperită cu făină, ou și pesmet, apoi prăjită.",
    "Chiftele": "Porții modelate din carne tocată sau legume, apoi prăjite ori coapte.",
    "Frigărui": "Bucăți de carne, legume sau alte alimente înșirate pe bețe și fripte.",
    "Ciorbă de perișoare": "Ciorbă cu mici bile din carne tocată, de obicei legată cu orez și ou.",
    "Piftie": "Preparat rece din carne și zeamă de carne închegată, aromatizat adesea cu usturoi.",
    "Zacuscă": "Preparat de legume gătite, adesea cu ardei, ceapă, roșii și vinete sau fasole.",
    "Urdă": "Produs lactat obținut prin încălzirea zerului și adunarea proteinelor coagulate.",
    "Mucenici": ("Preparate în formă de opt pentru 9 martie: copți și unși cu miere în "
                 "varianta moldovenească, fierți în zeamă dulce în cea muntenească."),
    "Alivenci": "Preparat moldovenesc copt din mălai și lactate, în variante dulci sau sărate.",
    "Cornulețe": "Fursecuri fragede modelate ca mici cornuri, cu umplutură dulce.",
    "Turtă dulce": "Prăjitură aromată cu miere sau sirop și condimente, precum scorțișoara.",
    "Halva": "Preparat dulce din semințe măcinate și o compoziție îndulcită.",
    "Colivă": "Preparat din grâu sau arpacaș fiert, îndulcit și amestecat de obicei cu nucă.",
    "Firimitură": ("Bucățică mică de pâine sau alt aliment; "
                   "pâinea uscată se poate mărunți pentru pesmet."),
    "Cașcaval pane": "Felii de cașcaval acoperite cu făină, ou și pesmet, apoi prăjite.",
    "Plăcinte": "Preparate din aluat cu umplutură dulce sau sărată, coapte ori prăjite.",
}

STARTERS = ["Făină", "Apă", "Lapte", "Sare", "Cheag alimentar", "Mălai",
            "Cuptor de bucătărie", "Ou"]

UNLOCKS = [
    ("camara", 3, "Se deschide cămara", [
        "Fruct", "Zahăr", "Lămâie", "Castravete", "Legume",
    ]),
    ("pranz", 8, "Ingrediente pentru prânz", [
        "Usturoi", "Orez", "Ardei", "Carne", "Borș", "Fasole", "Roșie",
    ]),
    ("cofetarie", 16, "Atelierul de dulciuri", [
        "Unt", "Smântână", "Smântână dulce pentru frișcă", "Mixer de bucătărie",
        "Vanilie", "Cacao", "Lapte praf", "Nucă", "Măr", "Griș",
    ]),
    ("sarbatoare", 24, "Pentru o masă de sărbătoare", [
        "Congelator", "Stafide", "Gelatină alimentară", "Pișcot",
        "Varză murată", "Ulei",
    ]),
    ("gustari", 30, "Gustări și preparate la tigaie", [
        "Tigaie", "Cartof", "Ceapă", "Cașcaval", "Grătar", "Iaurt", "Firimitură",
    ]),
    ("traditii", 36, "Mai departe prin cămară", [
        "Miere", "Scorțișoară", "Semințe de floarea-soarelui", "Prună", "Căpșună",
        "Dovleac", "Untură", "Zer", "Oală", "Arpacaș",
    ]),
]

# id, ingredient A, ingredient B, result, short original explanation.
# Sources below are reference entry points, individually verified by the factual reviewer.
RECIPES = [
    ("aluat-apa", "Făină", "Apă", "Aluat",
     "Făina amestecată și frământată cu apă formează un aluat simplu."),
    ("aluat-lapte", "Făină", "Lapte", "Aluat",
     "Laptele poate înlocui apa în aluaturi; frământarea leagă făina cu lichidul."),
    ("paste-ou", "Făină", "Ou", "Paste",
     "Făina și oul formează aluatul de paste proaspete, întins și tăiat apoi."),
    ("paste-aluat", "Aluat", "Ou", "Paste",
     "Un aluat cu ou, întins subțire și tăiat, devine paste de casă."),
    ("pandispan-ou-zahar", "Ou", "Zahăr", "Pandișpan",
     "Ouăle bătute cu zahăr dau baza unui pandișpan; se încorporează făină și se coace."),
    ("paine-cuptor", "Aluat", "Cuptor de bucătărie", "Pâine",
     "Aluatul de pâine se coace în cuptor; dospirea depinde de sortiment."),
    ("branza-cheag", "Lapte", "Cheag alimentar", "Brânză",
     "Cheagul coagulează laptele; prin scurgerea zerului se obține brânza."),
    ("branza-lamaie", "Lapte", "Lămâie", "Brânză",
     "Zeama de lămâie poate coagula laptele încălzit pentru o brânză proaspătă."),
    ("saramura", "Apă", "Sare", "Saramură",
     "Sarea dizolvată în apă formează saramură."),
    ("mamaliga-apa", "Mălai", "Apă", "Mămăligă",
     "Mălaiul fiert în apă și amestecat devine mămăligă."),
    ("mamaliga-lapte", "Mălai", "Lapte", "Mămăligă",
     "Există și mămăligă fiartă în lapte, în loc de apă sau împreună cu aceasta."),
    ("telemea", "Brânză", "Saramură", "Telemea",
     "Telemeaua este o brânză care se sărează și se păstrează în saramură."),
    ("bulz-branza", "Mămăligă", "Brânză", "Bulz",
     "Mămăliga umplută cu brânză și coaptă formează bulzul."),
    ("bulz-telemea", "Mămăligă", "Telemea", "Bulz",
     "Telemeaua poate umple un bulz de mămăligă, copt apoi."),
    ("dulceata-fruct", "Fruct", "Zahăr", "Dulceață",
     "Fructele fierte cu zahăr dau dulceață; timpul și proporțiile depind de fruct."),
    ("dulceata-mar", "Măr", "Zahăr", "Dulceață",
     "Bucățile de măr se pot fierbe în sirop de zahăr pentru dulceață de mere."),
    ("compot-fruct", "Fruct", "Apă", "Compot",
     "Fructele fierte în apă formează compot, îndulcit după gust."),
    ("compot-mar", "Măr", "Apă", "Compot",
     "Merele fierte în apă dau compot de mere, cu zahăr după gust."),
    ("muraturi-legume", "Legume", "Saramură", "Murături",
     "Legumele se pot conserva prin fermentare în saramură."),
    ("castraveti-saramura", "Castravete", "Saramură", "Castraveți murați",
     "Castraveții ținuți în saramură fermentează și devin castraveți murați."),
    ("supa-legume", "Legume", "Apă", "Supă",
     "Legumele fierte în apă dau baza unei supe de legume."),
    ("ciorba-bors", "Supă", "Borș", "Ciorbă",
     "Borșul acrește o supă de legume sau carne, transformând-o într-o ciorbă."),
    ("ciorba-fasole", "Ciorbă", "Fasole", "Ciorbă de fasole",
     "Fasolea fiartă este ingredientul principal al ciorbei de fasole."),
    ("ciorba-fasole-bors", "Fasole", "Borș", "Ciorbă de fasole",
     "Fasolea fiartă cu legume se poate acri cu borș pentru ciorbă de fasole."),
    ("mujdei", "Usturoi", "Apă", "Mujdei",
     "Usturoiul zdrobit, frecat cu sare și diluat cu apă dă un mujdei simplu."),
    ("mujdei-ulei", "Usturoi", "Ulei", "Mujdei",
     "Usturoiul zdrobit poate fi frecat cu ulei pentru un mujdei cremos."),
    ("fasole-batuta", "Fasole", "Usturoi", "Fasole bătută",
     "Fasolea fiartă, pasată și aromatizată cu usturoi formează fasole bătută."),
    ("ardei-orez", "Ardei", "Orez", "Ardei umpluți",
     "Ardeii se pot umple cu orez și legume pentru o variantă de post."),
    ("ardei-carne", "Ardei", "Carne", "Ardei umpluți",
     "Ardeii umpluți pot avea o compoziție cu carne tocată, orez și condimente."),
    ("friptura-cuptor", "Carne", "Cuptor de bucătărie", "Friptură",
     "Carnea pregătită și coaptă în cuptor devine friptură."),
    ("salata", "Roșie", "Castravete", "Salată",
     "Roșiile și castraveții tăiați sunt baza unei salate proaspete de vară."),
    ("branza-smantana", "Brânză", "Smântână", "Brânză cu smântână",
     "Brânza proaspătă se poate amesteca și servi cu smântână."),
    ("frisca-mixer", "Smântână dulce pentru frișcă", "Mixer de bucătărie", "Frișcă",
     "Smântâna dulce rece, potrivită pentru bătut, devine frișcă folosind mixerul."),
    ("crema-vanilie", "Lapte", "Vanilie", "Cremă de vanilie",
     "Laptele aromatizat cu vanilie este baza cremei, îngroșată cu ou sau amidon."),
    ("crema-ou", "Ou", "Vanilie", "Cremă de vanilie",
     "Oul și vanilia intră în crema de vanilie, preparată cu lapte și zahăr."),
    ("ciocolata-casa", "Cacao", "Lapte praf", "Ciocolată",
     "Cacaua și laptele praf formează ciocolata de casă împreună cu sirop de zahăr și unt."),
    ("biscuit-unt", "Făină", "Unt", "Biscuit",
     "Făina și untul formează baza biscuiților fragezi, cu zahăr și coacere."),
    ("salam-cacao", "Biscuit", "Cacao", "Salam de biscuiți",
     "Biscuiții rupți și cacaua sunt ingredientele caracteristice ale salamului de biscuiți."),
    ("salam-ciocolata", "Biscuit", "Ciocolată", "Salam de biscuiți",
     "O variantă de salam de biscuiți leagă biscuiții cu o compoziție de ciocolată."),
    ("placinta-mere", "Aluat", "Măr", "Plăcintă cu mere",
     "Foile de aluat învelesc umplutura de mere pentru plăcinta cu mere."),
    ("cozonac-nuca", "Aluat", "Nucă", "Cozonac",
     "Aluatul dulce dospit și umplutura de nucă alcătuiesc cozonacul cu nucă."),
    ("cozonac-cacao", "Aluat", "Cacao", "Cozonac",
     "Cacaua poate aromatiza umplutura unui cozonac din aluat dulce dospit."),
    ("papanasi-faina", "Brânză", "Făină", "Papanași",
     "Brânza proaspătă și făina intră în aluatul de papanași, alături de ou."),
    ("papanasi-gris", "Brânză", "Griș", "Papanași",
     "Papanașii fierți pot lega brânza proaspătă cu griș și ou."),
    ("supa-galuste", "Supă", "Griș", "Supă cu găluște",
     "Găluștele din griș și ou se fierb în supă pentru supă cu găluște."),
    ("cremsnit", "Aluat", "Cremă de vanilie", "Cremșnit",
     "Foile coapte de foietaj, un tip de aluat, se umplu cu cremă de vanilie pentru cremșnit."),
    ("poale-brau", "Aluat", "Brânză", "Poale-n brâu",
     "Poalele-n brâu sunt plăcinte din aluat dospit, împăturite peste brânză dulce."),
    ("inghetata-frisca", "Frișcă", "Congelator", "Înghețată",
     "O bază îndulcită cu frișcă, congelată, poate deveni înghețată de casă."),
    ("inghetata-crema", "Cremă de vanilie", "Congelator", "Înghețată",
     "O cremă de vanilie potrivită poate fi răcită și congelată ca bază de înghețată."),
    ("diplomat-piscot", "Frișcă", "Pișcot", "Tort Diplomat",
     "Tortul Diplomat poate avea pișcoturi și o cremă cu frișcă, fructe și gelatină."),
    ("diplomat-gelatina", "Frișcă", "Gelatină alimentară", "Tort Diplomat",
     "Frișca și gelatina intră în crema de Diplomat, împreună cu ou, lapte și fructe."),
    ("pasca-stafide", "Brânză", "Stafide", "Pască",
     "Brânza dulce și stafidele formează umplutura clasică a unei păști."),
    ("amandina-cacao", "Pandișpan", "Cacao", "Amandină",
     "Amandina pornește de la un blat de pandișpan cu cacao, completat cu sirop și cremă."),
    ("amandina-ciocolata", "Pandișpan", "Ciocolată", "Amandină",
     "O amandină poate avea blat de pandișpan cu cacao și cremă sau glazură de ciocolată."),
    ("sarmale-carne", "Varză murată", "Carne", "Sarmale",
     "Frunzele de varză murată învelesc umplutura de carne, orez și condimente a sarmalelor."),
    ("sarmale-orez", "Varză murată", "Orez", "Sarmale",
     "Sarmalele de post pot avea orez și legume învelite în frunze de varză murată."),
    ("gogosi", "Aluat", "Ulei", "Gogoși",
     "Bucățile de aluat dospit, prăjite în ulei și îndulcite, devin gogoși."),
    ("sandvis-branza", "Pâine", "Brânză", "Sandviș",
     "Brânza pusă pe pâine sau între două felii formează un sandviș simplu."),
    ("sandvis-telemea", "Pâine", "Telemea", "Sandviș",
     "Telemeaua poate fi umplutura unui sandviș, singură sau alături de legume."),
    ("sandvis-friptura", "Pâine", "Friptură", "Sandviș",
     "Feliile de friptură rămase de la masă pot umple un sandviș."),
    ("sandvis-fasole", "Pâine", "Fasole bătută", "Sandviș",
     "Fasolea bătută întinsă pe pâine formează o gustare de tip sandviș deschis."),
    ("sandvis-salata", "Pâine", "Salată", "Sandviș",
     "Salata de legume poate umple un sandviș vegetarian, cu pâine și un sos după gust."),
    ("sandvis-zacusca", "Pâine", "Zacuscă", "Sandviș",
     "Zacusca întinsă pe pâine formează un sandviș deschis de legume."),
    ("sandvis-cascaval", "Pâine", "Cașcaval", "Sandviș",
     "Feliile de cașcaval puse între felii de pâine formează un sandviș."),
    ("sandvis-snitel", "Pâine", "Șnițel", "Sandviș",
     "Șnițelul pus în pâine, cu legume sau sos, devine umplutură de sandviș."),
    ("sandvis-chiftele", "Pâine", "Chiftele", "Sandviș",
     "Chiftelele pot umple un sandviș, alături de legume și sos."),
    ("clatite-tigaie", "Aluat", "Tigaie", "Clătite",
     "Un aluat fluid cu făină, lapte și ou se întinde în tigaie pentru clătite subțiri."),
    ("pizza-rosie", "Aluat", "Roșie", "Pizza",
     "Aluatul întins și sosul din roșii formează baza unei pizza, coaptă cu toppinguri."),
    ("pizza-cascaval", "Aluat", "Cașcaval", "Pizza",
     "Cașcavalul se poate topi peste un blat de pizza din aluat, cu sos și alte ingrediente."),
    ("cartofi-ulei", "Cartof", "Ulei", "Cartofi prăjiți",
     "Cartoful tăiat în bucăți și prăjit în ulei devine cartofi prăjiți."),
    ("cartofi-tigaie", "Cartof", "Tigaie", "Cartofi prăjiți",
     "Cartofii tăiați se pot prăji într-o tigaie cu ulei încins."),
    ("snitel-faina", "Carne", "Făină", "Șnițel",
     "Feliile subțiri de carne trecute prin făină, apoi ou și pesmet, se prăjesc ca șnițele."),
    ("snitel-firimitura", "Carne", "Firimitură", "Șnițel",
     "Firimiturile de pâine uscată, măcinate ca pesmet, acoperă carnea cu ou pentru șnițel pane."),
    ("cascaval-pane-ou", "Cașcaval", "Ou", "Cașcaval pane",
     "Feliile de cașcaval se trec prin făină, ou bătut și pesmet, apoi se prăjesc."),
    ("cascaval-pane-firimitura", "Cașcaval", "Firimitură", "Cașcaval pane",
     "Firimiturile uscate și măcinate pentru pesmet formează crusta cașcavalului pane, "
     "cu făină și ou."),
    ("chiftele-ou", "Carne", "Ou", "Chiftele",
     "Oul ajută să lege carnea tocată cu legume și condimente pentru chiftele."),
    ("chiftele-usturoi", "Carne", "Usturoi", "Chiftele",
     "Carnea tocată aromatizată cu usturoi se poate modela în chiftele și prăji ori coace."),
    ("frigarui-ceapa", "Carne", "Ceapă", "Frigărui",
     "Cuburile de carne și bucățile de ceapă înșirate pe bețe se frig ca frigărui."),
    ("friptura-tigaie", "Carne", "Tigaie", "Friptură",
     "Bucățile de carne pot fi fripte și rumenite în tigaie."),
    ("friptura-gratar", "Carne", "Grătar", "Friptură",
     "Carnea friptă la grătar este o variantă de friptură."),
    ("perisoare-orez", "Carne", "Orez", "Ciorbă de perișoare",
     "Carnea tocată și orezul formează perișoare, legate cu ou și fierte într-o ciorbă."),
    ("piftie-supa", "Supă", "Gelatină alimentară", "Piftie",
     "O supă de carne poate fi închegată cu gelatină și răcită, "
     "cu carne și usturoi, pentru piftie."),
    ("piftie-carne", "Carne", "Gelatină alimentară", "Piftie",
     "Carnea fiartă în zeamă aromată poate fi legată cu gelatină și răcită într-o piftie."),
    ("zacusca-rosie", "Ardei", "Roșie", "Zacuscă",
     "Ardeii copți și roșiile intră în zacuscă, gătite cu ceapă și, "
     "după variantă, vinete sau fasole."),
    ("zacusca-fasole", "Ardei", "Fasole", "Zacuscă",
     "Ardeii copți și fasolea fiartă intră în zacusca de fasole, cu ceapă și roșii."),
    ("fasole-mujdei", "Fasole", "Mujdei", "Fasole bătută",
     "Fasolea fiartă și pasată se poate aromatiza cu mujdei pentru fasole bătută."),
    ("urda-oala", "Zer", "Oală", "Urdă",
     "Zerul încălzit în oală dă flocoane de proteine, care se adună și se scurg ca urdă."),
    ("urda-lamaie", "Zer", "Lămâie", "Urdă",
     "La încălzirea zerului, puțină zeamă de lămâie poate ajuta "
     "coagularea proteinelor pentru urdă."),
    ("papanasi-urda-faina", "Urdă", "Făină", "Papanași",
     "Urda poate înlocui brânza proaspătă într-un aluat de papanași cu făină și ou."),
    ("papanasi-urda-gris", "Urdă", "Griș", "Papanași",
     "Urda poate fi legată cu griș, făină și ou pentru o variantă de papanași copți."),
    ("poale-brau-urda", "Aluat", "Urdă", "Poale-n brâu",
     "Poalele-n brâu pot avea umplutură de urdă îndulcită, învelită în aluat dospit."),
    ("urda-smantana", "Urdă", "Smântână", "Brânză cu smântână",
     "Urda este un produs lactat care poate fi amestecat cu smântână, "
     "ca variantă de brânză cu smântână."),
    ("mucenici-miere", "Aluat", "Miere", "Mucenici",
     "Mucenicii moldovenești se modelează din aluat dospit ca opturi, se coc și se ung cu miere."),
    ("mucenici-paste", "Paste", "Nucă", "Mucenici",
     "Pastele mici în formă de opt se fierb în zeamă dulce cu nucă pentru mucenici muntenești."),
    ("alivenci-branza", "Mălai", "Brânză", "Alivenci",
     "Mălaiul și brânza intră în compoziția de alivenci, coaptă cu ou și alte lactate."),
    ("alivenci-smantana", "Mălai", "Smântână", "Alivenci",
     "Mălaiul și smântâna se combină cu ou și lactate în variante de alivenci coapte."),
    ("cornulete-dulceata", "Aluat", "Dulceață", "Cornulețe",
     "Aluatul fraged rulat în mici cornuri poate înveli o umplutură de dulceață bine scursă."),
    ("cornulete-untura", "Aluat", "Untură", "Cornulețe",
     "Untura frăgezește un aluat modelat în cornulețe, umplute și apoi coapte."),
    ("cornulete-smantana", "Aluat", "Smântână", "Cornulețe",
     "Smântâna intră în unele aluaturi fragede pentru cornulețe cu umplutură dulce."),
    ("turta-faina", "Făină", "Miere", "Turtă dulce",
     "Făina și mierea formează baza aluatului de turtă dulce, cu mirodenii și coacere."),
    ("turta-scortisoara", "Miere", "Scorțișoară", "Turtă dulce",
     "Mierea și scorțișoara dau gust caracteristic turtei dulci, într-un aluat cu făină."),
    ("halva-zahar", "Semințe de floarea-soarelui", "Zahăr", "Halva",
     "Miezul de semințe de floarea-soarelui măcinat se leagă cu sirop de zahăr pentru halva."),
    ("halva-miere", "Semințe de floarea-soarelui", "Miere", "Halva",
     "O variantă de halva de casă leagă semințele de floarea-soarelui măcinate cu miere."),
    ("coliva-nuca", "Arpacaș", "Nucă", "Colivă",
     "Arpacașul fiert, îndulcit și amestecat cu nucă este baza unei colive."),
    ("coliva-zahar", "Arpacaș", "Zahăr", "Colivă",
     "Arpacașul fiert se îndulcește cu zahăr și se completează de obicei cu nucă pentru colivă."),
    ("placinte-dovleac", "Aluat", "Dovleac", "Plăcinte",
     "Aluatul învelește dovleacul ras și pregătit ca umplutură pentru plăcinte."),
    ("placinte-telemea", "Aluat", "Telemea", "Plăcinte",
     "Telemeaua poate umple foi de aluat pentru plăcinte sărate."),
    ("placinte-pruna", "Aluat", "Prună", "Plăcinte",
     "Prunele fără sâmburi pot umple un aluat de plăcintă, îndulcite după gust."),
    ("dulceata-pruna", "Prună", "Zahăr", "Dulceață",
     "Prunele fierte cu zahăr, cu fructele păstrate în bucăți, dau dulceață de prune."),
    ("dulceata-capsuna", "Căpșună", "Zahăr", "Dulceață",
     "Căpșunile fierte cu zahăr dau dulceață de căpșuni."),
    ("compot-pruna", "Prună", "Apă", "Compot",
     "Prunele fierte în apă dau compot de prune, îndulcit după gust."),
    ("compot-capsuna", "Căpșună", "Apă", "Compot",
     "Căpșunile fierte scurt în apă pot fi păstrate în compot, cu zahăr după gust."),
    ("inghetata-iaurt", "Iaurt", "Congelator", "Înghețată",
     "Iaurtul îndulcit, eventual cu fructe, poate fi congelat ca înghețată de iaurt."),
    ("gogosi-iaurt", "Aluat", "Iaurt", "Gogoși",
     "Iaurtul intră în aluaturi moi de gogoși, porționate cu lingura și prăjite."),
    ("supa-oala", "Legume", "Oală", "Supă",
     "Legumele fierte în apă într-o oală dau o supă de legume."),
    ("mamaliga-oala", "Mălai", "Oală", "Mămăligă",
     "Mălaiul se fierbe și se amestecă într-o oală cu apă pentru mămăligă."),
]

GOALS = [
    ("paine", "Pâine", "Prima pâine"),
    ("bulz", "Bulz", "Gust de stână"),
    ("muraturi", "Murături", "Cămara pentru iarnă"),
    ("ciorba-fasole", "Ciorbă de fasole", "O ciorbă de casă"),
    ("cozonac", "Cozonac", "Cozonacul de sărbătoare"),
    ("papanasi", "Papanași", "Papanași pentru desert"),
    ("inghetata", "Înghețată", "Un desert rece"),
    ("diplomat", "Tort Diplomat", "Tortul de sărbătoare"),
    ("sarmale", "Sarmale", "Sarmale pentru masă"),
    ("sandvis", "Sandviș", "O gustare din ce ai descoperit"),
    ("clatite", "Clătite", "Clătite la tigaie"),
    ("pizza", "Pizza", "Pizza de casă"),
    ("snitel", "Șnițel", "Crusta crocantă"),
    ("zacusca", "Zacuscă", "Încă un borcan în cămară"),
    ("urda", "Urdă", "Din zer, o nouă brânză"),
    ("mucenici", "Mucenici", "Opturi dulci"),
    ("cornulete", "Cornulețe", "Cornulețe fragede"),
    ("halva", "Halva", "Dulce din semințe"),
    ("placinte", "Plăcinte", "Plăcinte dulci sau sărate"),
]

# Further reviewed expansion: keep the earlier book intact and give its pantry new uses.
DESCRIPTIONS.update({
    "Pară": "Fruct dulce, cu miez zemos, consumat proaspăt sau în compoturi și deserturi.",
    "Cireașă": "Fruct mic cu sâmbure, consumat proaspăt, în compoturi sau în dulceață.",
    "Strugure": "Fruct al viței-de-vie, alcătuit din boabe grupate în ciorchine.",
    "Pepene": "Fruct mare și zemos; în aceste rețete, pepenele verde cu miez roșu.",
    "Caisă": "Fruct cu sâmbure și pulpă portocalie, folosit și la compoturi ori dulcețuri.",
    "Piersică": "Fruct cu sâmbure și pulpă zemoasă, consumat proaspăt sau în deserturi.",
    "Banană": "Fruct cu coajă galbenă la coacere și miez moale, folosit și în deserturi.",
    "Portocală": "Fruct citric cu pulpă zemoasă, folosit în sucuri, creme și dulcețuri.",
    "Morcov": "Legumă rădăcinoasă, de obicei portocalie, folosită crudă sau gătită.",
    "Mazăre": "Plantă ale cărei boabe verzi se folosesc în supe, salate și mâncăruri.",
    "Ridiche": "Legumă cu rădăcină crocantă și gust ușor iute, consumată mai ales crudă.",
    "Conopidă": "Legumă cu inflorescență compactă, folosită fiartă, coaptă sau murată.",
    "Spanac": "Plantă cu frunze verzi comestibile, folosită în salate și preparate gătite.",
    "Varză": "Legumă cu frunze strânse în căpățână, folosită crudă, gătită sau murată.",
    "Mărar": "Plantă aromatică ale cărei frunze se folosesc în salate, umpluturi și mâncăruri.",
    "Pătrunjel": "Plantă aromatică folosită pentru frunze și rădăcină în bucătărie.",
    "Leuștean": "Plantă aromatică ale cărei frunze parfumează multe ciorbe românești.",
    "Cimbru": "Plantă aromatică folosită drept condiment pentru carne, fasole și alte preparate.",
    "Drojdie": "Preparat cu microorganisme care ajută aluaturile de panificație să dospească.",
    "Grâu": "Cereală din care se obțin făină și griș; boabele se folosesc și fierte.",
    "Orz": "Cereală ale cărei boabe decorticate se pot folosi la arpacaș și mâncăruri fierte.",
    "Ovăz": "Cereală folosită în alimentație ca boabe, fulgi sau făină.",
    "Secară": "Cereală din care se obține făină pentru pâine și alte produse coapte.",
    "Migdale": "Miezuri comestibile de migdal dulce, folosite în deserturi și ca gustare.",
    "Alune de pădure": "Fructe cu coajă lemnoasă și miez comestibil, folosite și în deserturi.",
    "Albuș": "Partea transparentă a oului, care se poate bate spumă și se albește prin gătire.",
    "Gălbenuș": "Partea galbenă a oului, folosită întreagă sau separat în creme și aluaturi.",
    "Zahăr pudră": (
        "Zahăr măcinat foarte fin, folosit în aluaturi, creme și la decorarea "
        "deserturilor."
    ),
    "Amidon alimentar": (
        "Ingredient care îngroașă creme și sosuri atunci când este gătit cu "
        "lichid."
    ),
    "Praf de copt": "Amestec de ingrediente care ajută aluaturile să crească la coacere.",
    "Bicarbonat de sodiu alimentar": (
        "Ingredient pentru uz alimentar folosit în unele aluaturi și preparate."
    ),
    "Fistic": "Miez comestibil, verzui, al fructului de fistic, folosit și în deserturi.",
    "Tavă de copt": "Vas cu margini ridicate în care se așază preparatele pentru cuptor.",
    "Sucitor": "Unealtă cilindrică folosită pentru a întinde foi de aluat.",
    "Cratiță": "Vas de bucătărie folosit pentru fierberea, înăbușirea sau prăjirea alimentelor.",
    "Afumături": "Carne sau produse din carne aromate și conservate prin afumare.",
    "Parizer": "Mezel fiert cu textură fină, servit de obicei feliat.",
    "Pate": "Pastă tartinabilă, aici preparată din ficat, grăsime și condimente.",
    "Pastramă": "Carne sărată și condimentată, uneori afumată ori uscată, servită și friptă.",
    "Muștar": "Condiment sub formă de pastă, preparat din semințe de muștar și alte ingrediente.",
    "pește": "Animal acvatic vertebrat; în rețete se folosește carnea speciilor comestibile.",
    "Mici": "Rulouri din carne tocată și condimentată, fripte la grătar fără înveliș de maț.",
    "Salată de boeuf": (
        "Salată cu legume fierte, murături și maioneză, cu carne în varianta "
        "clasică."
    ),
    "Varză a la Cluj": "Preparat copt în straturi de varză, carne tocată și orez.",
    "Ouă roșii": "Ouă fierte și colorate în nuanțe de roșu, pregătite tradițional pentru Paște.",
    "Brânză de burduf": "Brânză frământată și sărată, de obicei din caș de oaie, apoi maturată.",
    "Langoși": (
        "Turte din aluat dospit prăjite în ulei, simple, umplute sau cu diferite "
        "toppinguri."
    ),
    "Merdenea": "Produs de patiserie din foi de aluat grase, cu umplutură sărată de brânză.",
    "Savarină": "Prăjitură din aluat dospit, bine însiropată și umplută cu frișcă.",
    "Ecler": "Prăjitură alungită din aluat opărit și copt, umplută cu cremă și adesea glazurată.",
    "Chec": (
        "Prăjitură din aluat fluid, coaptă de obicei în formă alungită, simplă "
        "sau cu adaosuri."
    ),
    "Brioșă": "Produs de patiserie copt în formă mică; aici, varianta din aluat de prăjitură.",
    "Pepene murat": "Pepene verde mic pus la murat, de obicei întreg, în saramură.",
    "Gogonele": "Roșii încă verzi, necoapte, folosite mai ales pentru murături.",
    "Sushi": "Preparat japonez cu orez asezonat cu oțet, asociat cu pește sau alte ingrediente.",
    "Ciocolata Dubai": "Tabletă de ciocolată cu umplutură de fistic și fidea kataif rumenită.",
    "Tochitură moldovenească": (
        "Preparat cu bucăți de carne de porc rumenite, servit adesea cu "
        "mămăligă, ou și brânză."
    ),
    "Fasole cu ciolan": "Mâncare de fasole boabe cu ciolan de porc, adesea afumat.",
    "Slănină cu ceapă": "Gustare din felii de slănină și ceapă crudă, servită frecvent cu pâine.",
    "Ciorbă rădăuțeană": "Ciorbă cu carne de pui, legume, smântână și usturoi, acrită după gust.",
})

UNLOCKS.extend([
    ("livada", 45, "Fructe din livadă și din piață", [
        "Pară", "Cireașă", "Strugure", "Pepene", "Caisă", "Piersică", "Banană", "Portocală",
    ]),
    ("brutarie", 55, "Mai multe idei la brutărie", [
        "Drojdie", "Grâu", "Orz", "Ovăz", "Secară", "Migdale", "Alune de pădure",
        "Albuș", "Gălbenuș", "Zahăr pudră", "Amidon alimentar", "Praf de copt",
    ]),
    ("gradina", 65, "Verdețuri și legume pentru masă", [
        "Morcov", "Mazăre", "Ridiche", "Conopidă", "Spanac", "Varză",
        "Mărar", "Pătrunjel", "Leuștean", "Cimbru",
    ]),
    ("meniuri", 72, "Gusturi noi pentru meniul de acasă", [
        "Afumături", "Parizer", "Pate", "Pastramă", "Muștar", "pește", "Fistic",
        "Bicarbonat de sodiu alimentar", "Tavă de copt", "Sucitor", "Cratiță", "Formă de brioșe",
    ]),
])

RECIPES.extend([
    ("dulceata-para", "Pară", "Zahăr", "Dulceață",
     "Perele curățate și tăiate se fierb cu zahăr pentru dulceață de pere."),
    ("compot-para", "Pară", "Apă", "Compot",
     "Perele fierte în apă dau compot, îndulcit după gust."),
    ("placinte-para", "Aluat", "Pară", "Plăcinte",
     "Perele tăiate și pregătite ca umplutură se pot coace în foi de plăcintă."),
    ("dulceata-cireasa", "Cireașă", "Zahăr", "Dulceață",
     "Cireșele fără sâmburi, fierte cu zahăr, dau dulceață de cireșe."),
    ("compot-cireasa", "Cireașă", "Apă", "Compot",
     "Cireșele se pot fierbe și păstra în compot, cu apă și zahăr după gust."),
    ("placinte-cireasa", "Aluat", "Cireașă", "Plăcinte",
     "Cireșele fără sâmburi pot umple o plăcintă, bine scurse și îndulcite după gust."),
    ("dulceata-strugure", "Strugure", "Zahăr", "Dulceață",
     "Boabele de strugure pregătite fără sâmburi se pot fierbe cu zahăr în dulceață."),
    ("compot-strugure", "Strugure", "Apă", "Compot",
     "Boabele de strugure se pot păstra în compot de apă și zahăr."),
    ("pepene-saramura", "Pepene", "Saramură", "Pepene murat",
     "Pepenii verzi mici se pun la fermentat în saramură, cu aromele potrivite pentru murături."),
    ("dulceata-pepene", "Pepene", "Zahăr", "Dulceață",
     "Partea albă a cojii de pepene verde, curățată și tăiată, se fierbe cu zahăr în dulceață."),
    ("dulceata-caisa", "Caisă", "Zahăr", "Dulceață",
     "Caisele fără sâmburi, fierte cu zahăr, dau dulceață de caise."),
    ("compot-caisa", "Caisă", "Apă", "Compot",
     "Caisele fără sâmburi se pot fierbe și păstra în compot, îndulcit după gust."),
    ("placinte-caisa", "Aluat", "Caisă", "Plăcinte",
     "Caisele fără sâmburi pot umple o plăcintă din foi de aluat, îndulcite după gust."),
    ("dulceata-piersica", "Piersică", "Zahăr", "Dulceață",
     "Piersicile curățate și tăiate se fierb cu zahăr pentru dulceață de piersici."),
    ("compot-piersica", "Piersică", "Apă", "Compot",
     "Piersicile fără sâmburi, întregi sau tăiate, se pot păstra în compot."),
    ("placinte-piersica", "Aluat", "Piersică", "Plăcinte",
     "Piersicile feliate și bine scurse pot umple o plăcintă coaptă."),
    ("inghetata-banana", "Banană", "Congelator", "Înghețată",
     "Bucățile de banană congelate și apoi pasate dau un desert cu textura înghețatei."),
    ("clatite-banana", "Banană", "Ou", "Clătite",
     "Banana pasată și oul pot forma clătite mici, rumenite pe ambele părți în tigaie."),
    ("dulceata-portocala", "Portocală", "Zahăr", "Dulceață",
     "Pulpa de portocală pregătită fără sâmburi și membrane tari se fierbe cu zahăr în dulceață."),
    ("inghetata-portocala", "Portocală", "Frișcă", "Înghețată",
     "Sucul de portocală și frișca pot intra într-o bază îndulcită de înghețată, apoi congelată."),
    ("branza-burduf-sare", "Brânză", "Sare", "Brânză de burduf",
     (
         "Cașul de oaie, un tip de brânză, se mărunțește, se frământă cu sare și "
         "se maturează ca brânză de burduf."
     )),
    ("bulz-burduf", "Mămăligă", "Brânză de burduf", "Bulz",
     "Brânza de burduf umple bulzul de mămăligă, încălzit sau copt apoi."),
    ("sandvis-burduf", "Pâine", "Brânză de burduf", "Sandviș",
     "Brânza de burduf întinsă pe pâine formează un sandviș deschis."),
    ("langosi-mujdei", "Aluat", "Mujdei", "Langoși",
     "Turtele de aluat dospit se prăjesc în ulei și se ung cu mujdei pentru langoși cu usturoi."),
    ("langosi-burduf", "Aluat", "Brânză de burduf", "Langoși",
     "Aluatul dospit poate înveli brânză de burduf în langoși umpluți, prăjiți în ulei."),
    ("merdenea-telemea", "Foietaj", "Telemea", "Merdenea",
     (
         "Foietajul poate înveli o umplutură de telemea într-o variantă de casă "
         "de merdenele, coapte apoi."
     )),
    ("merdenea-branza-smantana", "Foietaj", "Brânză cu smântână", "Merdenea",
     (
         "O umplutură sărată de brânză cu smântână poate intra în merdenele de "
         "casă din foietaj, coapte apoi."
     )),
    ("savarina-frisca", "Aluat", "Frișcă", "Savarină",
     (
         "Aluatul dospit pentru savarine se coace în forme mici, se însiropează "
         "și se umple cu frișcă."
     )),
    ("ecler-oparit-crema", "Aluat opărit", "Cremă de vanilie", "Ecler",
     (
         "Aluatul opărit se modelează alungit și se coace; cojile răcite se "
         "umplu cu cremă de vanilie pentru eclere."
     )),
    ("ecler-oparit-ciocolata", "Aluat opărit", "Ciocolată", "Ecler",
     (
         "Cojile alungite și coapte din aluat opărit se umplu cu cremă și se "
         "glazurează cu ciocolată pentru eclere."
     )),
    ("chec-stafide", "Aluat", "Stafide", "Chec",
     "Stafidele se încorporează într-un aluat fluid de chec, copt într-o formă alungită."),
    ("chec-banana", "Aluat", "Banană", "Chec",
     (
         "Banana pasată intră într-un aluat fluid cu făină și agent de afânare, "
         "copt ca un chec cu banane."
     )),
    ("chec-portocala", "Aluat", "Portocală", "Chec",
     "Sucul de portocală aromatizează un aluat fluid de chec, copt apoi în formă."),
    ("briose-forma", "Aluat", "Formă de brioșe", "Brioșă",
     "Aluatul fluid de prăjitură se porționează în forme de brioșe și se coace până devine pufos."),
    ("briose-iaurt", "Făină", "Iaurt", "Brioșă",
     (
         "Făina și iaurtul intră în brioșe, alături de ou, zahăr, grăsime și "
         "praf de copt; compoziția se coace în forme mici."
     )),
    ("mici-bicarbonat", "Carne", "Bicarbonat de sodiu alimentar", "Mici",
     (
         "Carnea tocată pentru mici se frământă cu condimente și puțin "
         "bicarbonat alimentar, apoi se modelează și se frige la grătar."
     )),
    ("oua-rosii-ceapa", "Ou", "Ceapă", "Ouă roșii",
     (
         "Ouăle fierte cu coji de ceapă se pot colora natural în nuanțe roșcate; "
         "culoarea depinde de coji și timpul de fierbere."
     )),
    ("gogonele-saramura", "Roșie", "Saramură", "Gogonele",
     "Roșiile încă verzi, necoapte, se aleg ca gogonele și se pun la murat în saramură."),
    ("aluat-drojdie", "Făină", "Drojdie", "Aluat",
     "Făina, drojdia și un lichid se frământă într-un aluat care se lasă la dospit."),
    ("paine-drojdie", "Aluat", "Drojdie", "Pâine",
     "Un aluat de pâine cu drojdie se lasă să dospească, se modelează și se coace."),
    ("coliva-grau", "Grâu", "Nucă", "Colivă",
     "Grâul fiert, îndulcit și amestecat cu nucă formează baza unei colive."),
    ("coliva-orz", "Orz", "Nucă", "Colivă",
     (
         "Arpacașul din orz decorticat se poate fierbe și îndulci, apoi amesteca "
         "cu nucă pentru colivă."
     )),
    ("biscuit-ovaz", "Ovăz", "Unt", "Biscuit",
     "Fulgii sau făina de ovăz intră în biscuiți cu unt, zahăr și alte ingrediente, copți apoi."),
    ("biscuit-ovaz-banana", "Ovăz", "Banană", "Biscuit",
     "Fulgii de ovăz legați cu banană pasată se pot porționa și coace ca biscuiți moi."),
    ("paine-secara", "Aluat", "Secară", "Pâine",
     "Făina obținută din secară intră în aluatul de pâine, dospit și copt apoi."),
    ("biscuit-secara", "Secară", "Unt", "Biscuit",
     "Făina de secară se poate folosi în biscuiți cu unt și zahăr, formați și copți apoi."),
    ("biscuit-migdale", "Făină", "Migdale", "Biscuit",
     "Migdalele măcinate și făina intră în aluat de biscuiți, cu grăsime, zahăr și coacere."),
    ("biscuit-alune", "Făină", "Alune de pădure", "Biscuit",
     "Alunele de pădure măcinate se pot adăuga în aluatul de biscuiți cu făină, unt și zahăr."),
    ("cornulete-migdale", "Aluat", "Migdale", "Cornulețe",
     "Migdalele măcinate intră în aluat fraged modelat în cornulețe și copt."),
    ("cornulete-alune", "Aluat", "Alune de pădure", "Cornulețe",
     "Alunele de pădure măcinate pot aromatiza aluatul fraged al cornulețelor coapte."),
    ("pandispan-albus", "Albuș", "Făină", "Pandișpan",
     "Albușurile bătute cu zahăr primesc făină încorporată ușor și se coc într-un pandișpan alb."),
    ("crema-galbenus", "Gălbenuș", "Vanilie", "Cremă de vanilie",
     "Gălbenușul și vanilia intră în crema fiartă cu lapte, zahăr și făină sau amidon."),
    ("crema-amidon", "Lapte", "Amidon alimentar", "Cremă de vanilie",
     "Laptele se îngroașă prin fierbere cu amidon și zahăr, iar vanilia aromatizează crema."),
    ("biscuit-zahar-pudra", "Făină", "Zahăr pudră", "Biscuit",
     "Făina și zahărul pudră intră în biscuiți fragezi, cu unt și apoi coacere."),
    ("turta-bicarbonat", "Miere", "Bicarbonat de sodiu alimentar", "Turtă dulce",
     (
         "Mierea și bicarbonatul alimentar intră în unele aluaturi de turtă "
         "dulce cu făină, condimente și coacere."
     )),
    ("varza-cluj-tocata", "Varză călită", "Carne tocată", "Varză a la Cluj",
     (
         "Varza călită, carnea tocată pregătită și orezul se așază în straturi "
         "și se coc ca varză a la Cluj."
     )),
    ("paste-sucitor", "Făină", "Sucitor", "Paste",
     (
         "Făina se frământă cu ou sau apă; sucitorul întinde foaia, care se taie "
         "în paste și se fierbe."
     )),
    ("compot-cratita", "Fruct", "Cratiță", "Compot",
     "Fructele se fierb în apă într-o cratiță pentru compot, îndulcit după gust."),
    ("salata-boeuf-cartofi", "Cartof", "Maioneză", "Salată de boeuf",
     (
         "Cartofii fierți se taie cuburi și se leagă cu maioneză, alături de "
         "morcov, murături și carne după variantă, în salată de boeuf."
     )),
    ("salata-boeuf-legume", "Legume", "Maioneză", "Salată de boeuf",
     (
         "Legumele fierte și tăiate cuburi se leagă cu maioneză, cu murături și "
         "carne după variantă, în salată de boeuf."
     )),
    ("supa-morcov", "Morcov", "Apă", "Supă",
     "Morcovul fiert în apă, cu alte legume și condimente după gust, dă o supă de legume."),
    ("supa-mazare", "Mazăre", "Apă", "Supă",
     "Mazărea fiartă în apă cu legume și condimente poate deveni o supă, simplă sau pasată."),
    ("salata-ridiche", "Ridiche", "Castravete", "Salată",
     "Ridichile și castraveții tăiați formează o salată proaspătă, asezonată după gust."),
    ("salata-ridiche-rosie", "Ridiche", "Roșie", "Salată",
     "Ridichile și roșiile tăiate se pot combina într-o salată de legume."),
    ("supa-conopida", "Conopidă", "Apă", "Supă",
     "Conopida fiartă în apă cu alte legume și condimente dă o supă, pasată sau cu buchețele."),
    ("muraturi-conopida", "Conopidă", "Saramură", "Murături",
     "Buchețelele de conopidă se pot pune la fermentat în saramură pentru murături."),
    ("placinte-spanac", "Aluat", "Spanac", "Plăcinte",
     "Spanacul pregătit și bine scurs poate umple foi de plăcintă, singur sau cu brânză."),
    ("salata-spanac", "Spanac", "Roșie", "Salată",
     "Frunzele tinere de spanac și roșiile tăiate se pot servi într-o salată."),
    ("salata-varza", "Varză", "Morcov", "Salată",
     "Varza tăiată fin și morcovul ras formează o salată, asezonată după gust."),
    ("placinte-varza", "Aluat", "Varză", "Plăcinte",
     "Varza tăiată și călită poate umple plăcinte din aluat, coapte sau prăjite."),
    ("placinte-marar", "Brânză", "Mărar", "Plăcinte",
     (
         "Brânza amestecată cu mărar formează o umplutură sărată, învelită în "
         "foi de plăcintă și gătită."
     )),
    ("chiftele-patrunjel", "Carne", "Pătrunjel", "Chiftele",
     (
         "Pătrunjelul tocat aromatizează carnea tocată pentru chiftele, legată "
         "cu ou și alte ingrediente și apoi gătită."
     )),
    ("ciorba-fasole-leustean", "Fasole", "Leuștean", "Ciorbă de fasole",
     (
         "Leușteanul aromatizează ciorba de fasole, preparată din boabe fierte, "
         "legume și un ingredient pentru acrire."
     )),
    ("crutoane-cimbru", "Pâine", "Cimbru", "Crutoane",
     (
         "Cubulețele de pâine se stropesc cu ulei, se aromatizează cu cimbru și "
         "se coc până devin crutoane crocante."
     )),
    ("fasole-ciolan-afumat", "Fasole", "Ciolan afumat", "Fasole cu ciolan",
     (
         "Un ciolan de porc afumat se fierbe și se gătește cu fasole boabe și "
         "legume pentru fasole cu ciolan."
     )),
    ("slanina-ceapa", "Slănină", "Ceapă", "Slănină cu ceapă",
     "Slănina gata de consum se servește feliată cu ceapă crudă și pâine."),
    ("sandvis-parizer", "Pâine", "Parizer", "Sandviș",
     "Feliile de parizer puse pe pâine sau între două felii formează un sandviș."),
    ("sandvis-pate", "Pâine", "Pate", "Sandviș",
     "Pateul întins pe pâine formează un sandviș deschis."),
    ("sandvis-pastrama", "Pâine", "Pastramă", "Sandviș",
     "Pastrama gata de consum, feliată, poate umple un sandviș, cu legume după gust."),
    ("friptura-pastrama", "Pastramă", "Grătar", "Friptură",
     "Pastrama pregătită pentru gătit se poate frige pe grătar ca friptură condimentată."),
    ("friptura-mustar", "Carne", "Muștar", "Friptură",
     "Carnea se poate unge sau marina cu muștar și condimente, apoi se coace ca friptură."),
    ("sushi-peste", "Orez", "pește", "Sushi",
     (
         "Orezul fiert și asezonat cu oțet se poate combina cu pește gătit "
         "pentru sushi; unele variante folosesc și alge."
     )),
    ("snitel-peste", "pește", "Firimitură", "Șnițel",
     (
         "Fileul de pește trecut prin făină, ou și pesmet din pâine uscată se "
         "poate prăji ca șnițel de pește."
     )),
    ("ciocolata-dubai-umplutura", "Ciocolată", "Umplutură de fistic și kataif", "Ciocolata Dubai",
     (
         "O cochilie de ciocolată învelește umplutura de cremă de fistic și "
         "fidea kataif rumenită pentru ciocolata Dubai."
     )),
    ("biscuit-fistic", "Făină", "Fistic", "Biscuit",
     "Fisticul mărunțit se poate adăuga în aluat de biscuiți cu făină, unt și zahăr, copt apoi."),
    ("inghetata-fistic", "Fistic", "Frișcă", "Înghețată",
     "Fisticul măcinat fin aromatizează o bază îndulcită cu frișcă, apoi congelată ca înghețată."),
    ("tochitura-mamaliga", "Friptură", "Mămăligă", "Tochitură moldovenească",
     (
         "Bucățile de carne de porc rumenite ca friptură se servesc cu mămăligă, "
         "adesea cu ou și brânză, într-o tochitură moldovenească."
     )),
    ("radauteana-smantana", "Carne de pui", "Smântână", "Ciorbă rădăuțeană",
     (
         "Carnea de pui se fierbe cu legume; zeama se drege cu smântână și "
         "gălbenuș, se aromatizează cu usturoi și se acrește pentru ciorbă "
         "rădăuțeană."
     )),
])

GOALS.extend([
    ("pepene-murat", "Pepene murat", "Pepeni pentru cămara de iarnă"),
    ("branza-burduf", "Brânză de burduf", "Brânză frământată la stână"),
    ("langosi", "Langoși", "Turte calde cu usturoi"),
    ("merdenea", "Merdenea", "Foi fragede cu brânză"),
    ("savarina", "Savarină", "Frișcă și prăjitură însiropată"),
    ("ecler", "Ecler", "O nouă idee pentru crema de vanilie"),
    ("chec", "Chec", "Checul din tava de acasă"),
    ("briose", "Brioșă", "Prăjituri în forme mici"),
    ("mici", "Mici", "Mici pe grătar"),
    ("oua-rosii", "Ouă roșii", "Culori din coji de ceapă"),
    ("salata-boeuf", "Salată de boeuf", "Salata mesei de sărbătoare"),
    ("sushi", "Sushi", "Orezul întâlnește peștele"),
    ("ciocolata-dubai", "Ciocolata Dubai", "Fistic și ciocolată crocantă"),
])

# Original, world-local definitions. References support the facts, not copied prose.
WORLD_CONCEPTS = {'Vânătă': {'id': 'alw_food_vanata',
            'description': 'Legumă cu pulpă deschisă la culoare, folosită coaptă, prăjită sau '
                           'în mâncăruri.',
            'sources': ['https://www.lauralaurentiu.ro/retete-culinare/retete-diverse/salata-de-vinete-romaneasca.html']},
 'Carne de pui': {'id': 'alw_food_carne_pui',
                  'description': 'Carne de pasăre folosită în supe, ciorbe, fripturi și alte '
                                 'preparate.',
                  'sources': ['https://www.lauralaurentiu.ro/retete-culinare/supe-ciorbe/ciorba-radauteana.html']},
 'Ciolan afumat': {'id': 'alw_food_ciolan_afumat',
                   'description': 'Bucată de picior de porc cu os, aromată prin afumare și '
                                  'folosită după gătire.',
                   'sources': ['https://www.lauralaurentiu.ro/retete-culinare/retete-mancare/fasole-boabe-cu-ciolan-afumat.html']},
 'Slănină': {'id': 'alw_food_slanina',
             'description': 'Grăsime de sub pielea porcului, folosită la gătit sau conservată '
                            'prin sărare și uneori afumare.',
             'sources': ['https://www.youtube.com/watch?v=9Z4BwqQpv58']},
 'Busuioc': {'id': 'alw_food_busuioc',
             'description': 'Plantă aromatică ale cărei frunze comestibile se folosesc în '
                            'sosuri și alte preparate.',
             'sources': ['https://www.kotanyi.com/ro/condimente/busuioc/']},
 'Măsline': {'id': 'alw_food_masline',
             'description': 'Fructe ale măslinului, consumate după pregătire și conservare, '
                            'folosite și în bucătărie.',
             'sources': ['https://eur-lex.europa.eu/legal-content/RO/ALL/?uri=CELEX%3A32012R0426']},
 'Năut': {'id': 'alw_food_naut',
          'description': 'Plantă leguminoasă ale cărei boabe fierte se folosesc în mâncăruri '
                         'și paste tartinabile.',
          'sources': ['https://www.youtube.com/watch?v=mKCkPoY5XG8']},
 'Maioneză': {'id': 'alw_food_maioneza',
              'description': 'Sos cremos obținut prin emulsionarea uleiului cu gălbenuș și '
                             'ingrediente pentru gust.',
              'sources': ['https://www.lauraadamache.ro/2010/02/maioneza-de-casa-reteta-clasica.html']},
 'Aluat opărit': {'id': 'alw_food_aluat_oparit',
                  'description': 'Aluat gătit întâi pe foc din lichid, grăsime și făină, în '
                                 'care se încorporează apoi ouă.',
                  'sources': ['https://www.lalena.ro/reteta/1208/Eclere-cu-crema-de-vanilie/']},
 'Lipie': {'id': 'alw_food_lipie',
           'description': 'Pâine plată, întinsă subțire, coaptă repede și folosită și pentru a '
                          'înveli umpluturi.',
           'sources': ['https://jamilacuisine.ro/lipii-pentru-shaorma-quesadilla-si-tacos-reteta-video/']},
 'Sos de roșii': {'id': 'alw_food_sos_rosii',
                  'description': 'Sos preparat din roșii, de obicei gătite și aromatizate, '
                                 'folosit la paste și alte mâncăruri.',
                  'sources': ['https://www.lalena.ro/reteta/1487/Sos-de-rosii-Marinara-clasic/']},
 'Piure de cartofi': {'id': 'alw_food_piure_cartofi',
                      'description': 'Cartofi fierți și pasați, amestecați de obicei cu unt și '
                                     'lapte.',
                      'sources': ['https://www.lalena.ro/reteta/120/Piure-de-cartofi/']},
 'Limonadă': {'id': 'alw_food_limonada',
              'description': 'Băutură din apă și zeamă de lămâie, îndulcită după gust.',
              'sources': ['https://www.bucataras.ro/retete/limonada-cu-miere-si-lamaie-86571.html']},
 'Bezea': {'id': 'alw_food_bezea',
           'description': 'Preparat din albuș bătut cu zahăr, modelat și uscat prin coacere '
                          'blândă.',
           'sources': ['https://www.oetker.ro/retete/r/bezele-cremoase-cu-ciocolata']},
 'Mousse de ciocolată': {'id': 'alw_food_mousse_ciocolata',
                         'description': 'Desert aerat cu ciocolată, obținut prin încorporarea '
                                        'unei spume sau a frișcăi.',
                         'sources': ['https://sallysbakingaddiction.com/dark-chocolate-mousse-cake/']},
 'Pastă dulce de fistic': {'id': 'alw_food_crema_fistic',
                           'description': 'Pastă fină din fistic măcinat, aici îndulcită și '
                                          'folosită ca umplutură pentru deserturi.',
                           'sources': ['https://www.seriouseats.com/homemade-pistachio-paste']},
 'Foietaj': {'id': 'alw_food_foietaj',
             'description': 'Aluat cu straturi de grăsime, întins și împăturit astfel încât să '
                            'se desfacă în foi la copt.',
             'sources': ['https://bucate-aromate.ro/2022/02/foietaj-de-casa/']},
 'Caramel': {'id': 'alw_food_caramel',
             'description': 'Zahăr încălzit până capătă culoare brun-aurie și aromă '
                            'caracteristică.',
             'sources': ['https://www.lalena.ro/reteta/13/Crema-de-zahar-ars/']},
 'Sos de caramel': {'id': 'alw_food_sos_caramel',
                    'description': 'Sos dulce din zahăr caramelizat și smântână dulce, uneori '
                                   'cu unt.',
                    'sources': ['https://www.oetker.ro/retete/r/placinta-cu-mere-cu-sos-de-caramel']},
 'Ganache': {'id': 'alw_food_ganache',
             'description': 'Compoziție fină din ciocolată și smântână dulce, folosită la '
                            'creme, umpluturi și glazuri.',
             'sources': ['https://www.kingarthurbaking.com/blog/2019/02/13/how-to-make-ganache']},
 'Tartă': {'id': 'alw_food_tarta',
           'description': 'Preparat cu o bază de aluat sau biscuiți și o umplutură dulce ori '
                          'sărată, de obicei fără capac de aluat.',
           'sources': ['https://www.petitchef.ro/retete/desert/tarta-oreo-si-ciocolata-fara-coacere-fid-1574303']},
 'Budincă de orez': {'id': 'alw_food_budinca_orez',
                     'description': 'Desert închegat din orez fiert cu lapte, adesea legat cu '
                                    'ou și copt.',
                     'sources': ['https://www.lalena.ro/reteta/1854/Budinca-de-orez-la-cuptor/']},
 'Griș cu lapte': {'id': 'alw_food_gris_lapte',
                   'description': 'Desert din griș fiert în lapte și îndulcit, servit simplu '
                                  'sau cu adaosuri.',
                   'sources': ['https://www.lalena.ro/reteta/1781/Gris-cu-lapte/']},
 'Piure de mazăre': {'id': 'alw_food_piure_mazare',
                     'description': 'Mazăre fiartă și pasată fin, cu unt sau alte ingrediente '
                                    'pentru gust și textură.',
                     'sources': ['https://www.lalena.ro/reteta/1019/Piure-de-mazare-verde/']},
 'Salată de cartofi': {'id': 'alw_food_salata_cartofi',
                       'description': 'Salată din cartofi fierți și răciți, cu legume, '
                                      'dressing și alte adaosuri după variantă.',
                       'sources': ['https://www.lauralaurentiu.ro/retete-culinare/retete-de-salate/salata-orientala-reteta-simpla-de-post.html']},
 'Chiftele de legume': {'id': 'alw_food_chiftele_legume',
                        'description': 'Porții modelate din legume mărunțite și ingrediente de '
                                       'legare, apoi prăjite sau coapte.',
                        'sources': ['https://www.lauralaurentiu.ro/retete-culinare/retete-mancare/chiftele-de-legume.html']},
 'Omletă': {'id': 'alw_food_omleta',
            'description': 'Preparat din ouă bătute și gătite în tigaie, simplu sau cu '
                           'umpluturi.',
            'sources': ['https://jamilacuisine.ro/omleta-delicioasa-reteta-video/']},
 'Ou fiert': {'id': 'alw_food_ou_fiert',
              'description': 'Ou gătit în apă fierbinte, cu albușul și gălbenușul închegate în '
                             'grade diferite.',
              'sources': ['https://www.lauralaurentiu.ro/retete-culinare/retete-diverse/oua-vopsite-cu-coji-de-ceapa.html']},
 'Pâine prăjită': {'id': 'alw_food_paine_prajita',
                   'description': 'Felie de pâine încălzită până când suprafața se rumenește '
                                  'și devine crocantă.',
                   'sources': ['https://www.e-retete.ro/retete/paine-prajita-cu-usturoi']},
 'Crutoane': {'id': 'alw_food_crutoane',
              'description': 'Bucățele de pâine rumenite și uscate, folosite în supe și '
                             'salate.',
              'sources': ['https://www.lauralaurentiu.ro/retete-culinare/retete-diverse/crutoane-de-casa.html']},
 'Frigănele': {'id': 'alw_food_friganele',
               'description': 'Felii de pâine trecute prin lapte și ou bătut, apoi rumenite în '
                              'tigaie.',
               'sources': ['https://www.lauralaurentiu.ro/retete-culinare/retete-diverse/friganele-bundas-kenyer-pain-perdu-french-toast.html']},
 'Supă cremă': {'id': 'alw_food_supa_crema',
                'description': 'Supă cu legumele pasate fin, astfel încât lichidul să aibă o '
                               'textură cremoasă.',
                'sources': ['https://www.lauralaurentiu.ro/retete-culinare/supe-ciorbe/supa-crema-de-spanac-cu-crutoane-de-casa-cu-parmezan.html']},
 'Sos de iaurt': {'id': 'alw_food_sos_iaurt',
                  'description': 'Sos rece pe bază de iaurt, aromatizat de exemplu cu usturoi, '
                                 'verdețuri sau lămâie.',
                  'sources': ['https://www.bucataras.ro/retete/sos-din-iaurt-cu-usturoi-93431.html']},
 'Cartofi copți': {'id': 'alw_food_cartofi_copti',
                   'description': 'Cartofi gătiți în cuptor, întregi sau tăiați, cu sau fără '
                                  'coajă.',
                   'sources': ['https://www.lalena.ro/reteta/156/Cartofi-crocanti-la-cuptor/']},
 'Legume la grătar': {'id': 'alw_food_legume_gratar',
                      'description': 'Legume feliate sau întregi, fripte pe grătar și '
                                     'asezonate după gust.',
                      'sources': ['https://www.lauralaurentiu.ro/retete-culinare/retete-de-garnitura/legume-la-gratar.html']},
 'Sos de brânză': {'id': 'alw_food_sos_branza',
                   'description': 'Sos cald și cremos în care brânza topită se combină cu '
                                  'lapte sau o bază albă.',
                   'sources': ['https://www.lauralaurentiu.ro/retete-culinare/sos-bechamel.html']},
 'Paste cu sos de roșii': {'id': 'alw_food_paste_sos_rosii',
                           'description': 'Paste fierte și amestecate cu sos de roșii, cu '
                                          'arome și adaosuri după gust.',
                           'sources': ['https://www.lalena.ro/reteta/1498/Sos-de-rosii-pentru-paste-si-pizza-reteta-mea/']},
 'Paste cu brânză': {'id': 'alw_food_paste_branza',
                     'description': 'Paste fierte amestecate cu brânză, servite direct sau '
                                    'rumenite la cuptor.',
                     'sources': ['https://www.lalena.ro/u/reteta/659/Paste-cu-branza-la-cuptor/']},
 'Pesto': {'id': 'alw_food_pesto',
           'description': 'Sos rece din frunze aromatice mărunțite cu ulei, nuci sau semințe '
                          'și adesea brânză.',
           'sources': ['https://bucate-aromate.ro/2023/08/pesto-de-busuioc/']},
 'Focaccia': {'id': 'alw_food_focaccia',
              'description': 'Pâine italiană plată și pufoasă, unsă cu ulei de măsline și '
                             'coaptă în tavă.',
              'sources': ['https://www.lalena.ro/reteta/1929/Focaccia-cu-rosii-si-masline-sau-Focaccia-Barese/']},
 'Hummus': {'id': 'alw_food_hummus',
            'description': 'Pastă din năut fiert și pasat, de obicei cu tahini, lămâie și '
                           'usturoi.',
            'sources': ['https://www.youtube.com/watch?v=mKCkPoY5XG8']},
 'Cremă de brânză': {'id': 'alw_food_crema_branza',
                     'description': 'Pastă fină și tartinabilă pe bază de brânză, simplă sau '
                                    'aromatizată.',
                     'sources': ['https://g4food.ro/video-foto-crema-de-branza-cu-masline/']},
 'Varză călită': {'id': 'alw_food_varza_calita',
                  'description': 'Varză tăiată și gătită cu grăsime, apoi înăbușită până '
                                 'devine fragedă; poate fi dulce sau murată.',
                  'sources': ['https://www.lauralaurentiu.ro/retete-culinare/retete-mancare/varza-a-la-cluj.html']},
 'Carne tocată': {'id': 'alw_food_carne_tocata',
                  'description': 'Carne mărunțită cu mașina de tocat sau cu un cuțit, folosită '
                                 'în umpluturi și preparate modelate.',
                  'sources': ['https://www.e-retete.ro/retete/biftec-tartar']},
 'Formă de brioșe': {'id': 'alw_food_forma_briose',
                     'description': 'Recipient cu adâncituri mici în care se porționează și se '
                                    'coc brioșele.',
                     'sources': ['https://www.oetker.ro/retete/r/briose-cu-afine']},
 'Kataif': {'id': 'alw_food_kataif',
            'description': 'Fidea foarte fină din aluat, folosită în deserturi; aici '
                           'ingredientul, nu prăjitura cu același nume.',
            'sources': ['https://www.oetker.co.uk/recipes/r/dubai-chocolate']},
 'Umplutură de fistic și kataif': {'id': 'alw_food_umplutura_fistic_kataif',
                                   'description': 'Compoziție dulce cu fistic și fidea kataif '
                                                  'rumenită, folosită pentru textura crocantă '
                                                  'a unor deserturi.',
                                   'sources': ['https://www.oetker.co.uk/recipes/r/dubai-chocolate']}}

DESCRIPTIONS.update({
    "Cuțit": "Unealtă de bucătărie cu lamă și mâner, folosită pentru a tăia alimente.",
    "Salată de vinete": (
        "Pastă din vinete coapte, curățate și tocate, frecată cu ulei și "
        "asezonată."
    ),
    "Șaorma cu de toate": "Lipie umplută cu carne friptă, legume, cartofi prăjiți și sosuri.",
})
UNLOCKS.extend([
    ("baze", 82, "Sosuri, umpluturi și un meniu mai bogat", [
        "Vânătă", "Carne de pui", "Ciolan afumat", "Slănină", "Cuțit", "Kataif",
    ]),
    ("mediterana", 95, "O cămară cu idei mediteraneene", [
        "Busuioc", "Măsline", "Năut",
    ]),
])

RECIPES.extend([
    ("maioneza-galbenus", "Gălbenuș", "Ulei", "Maioneză",
     "Uleiul încorporat treptat în gălbenuș prin amestecare formează maioneză, asezonată apoi."),
    ("maioneza-ou", "Ou", "Ulei", "Maioneză",
     "Oul întreg se poate emulsiona cu ulei folosind un blender vertical pentru maioneză."),
    ("oparit-cratita", "Făină", "Cratiță", "Aluat opărit",
     (
         "Făina se amestecă în cratiță cu apă și unt fierbinți; compoziția se "
         "gătește, se răcorește și primește ouă pentru aluat opărit."
     )),
    ("foietaj-unt", "Aluat", "Unt", "Foietaj",
     (
         "Untul se închide în aluat, care se întinde și se împăturește repetat, "
         "cu răcire între etape, pentru foietaj."
     )),
    ("lipie-sucitor", "Aluat", "Sucitor", "Lipie",
     (
         "Aluatul pentru lipie se întinde subțire cu sucitorul și se coace "
         "repede, de obicei în tigaie."
     )),
    ("sos-rosii-cratita", "Roșie", "Cratiță", "Sos de roșii",
     "Roșiile pregătite se gătesc în cratiță până se leagă într-un sos, aromatizat după gust."),
    ("sos-rosii-usturoi", "Roșie", "Usturoi", "Sos de roșii",
     "Roșiile se gătesc cu usturoi și puțin ulei pentru un sos de roșii aromat."),
    ("piure-cartofi-unt", "Cartof", "Unt", "Piure de cartofi",
     "Cartofii fierți se pasează și se amestecă cu unt și lapte pentru piure."),
    ("piure-cartofi-lapte", "Cartof", "Lapte", "Piure de cartofi",
     "Laptele cald se încorporează în cartofii fierți și pasați, cu unt după gust, pentru piure."),
    ("limonada-apa", "Lămâie", "Apă", "Limonadă",
     "Zeama de lămâie amestecată cu apă dă limonadă, îndulcită după gust."),
    ("limonada-miere", "Lămâie", "Miere", "Limonadă",
     "Mierea îndulcește zeama de lămâie diluată cu apă pentru limonadă."),
    ("bezea-albus", "Albuș", "Zahăr", "Bezea",
     "Albușurile bătute spumă cu zahăr se modelează și se usucă prin coacere blândă în bezele."),
    ("mousse-frisca", "Ciocolată", "Frișcă", "Mousse de ciocolată",
     (
         "Ciocolata topită și răcorită se încorporează în frișcă pentru un "
         "mousse de ciocolată, răcit apoi."
     )),
    ("crema-fistic-zahar", "Fistic", "Zahăr", "Pastă dulce de fistic",
     (
         "Fisticul curățat se macină foarte fin cu zahăr până se transformă "
         "într-o pastă dulce pentru deserturi."
     )),
    ("caramel-cratita", "Zahăr", "Cratiță", "Caramel",
     "Zahărul încălzit în cratiță până se topește și devine brun-auriu formează caramel."),
    ("caramel-apa", "Zahăr", "Apă", "Caramel",
     "Zahărul umezit cu puțină apă se fierbe până se evaporă apa și zahărul se caramelizează."),
    ("sos-caramel-smantana", "Caramel", "Smântână dulce pentru frișcă", "Sos de caramel",
     "Caramelul se combină cu smântână dulce caldă și, după rețetă, unt, pentru un sos fin."),
    ("ganache-smantana", "Ciocolată", "Smântână dulce pentru frișcă", "Ganache",
     "Smântâna dulce încălzită se amestecă cu ciocolata până se obține un ganache omogen."),
    ("tarta-foietaj-mar", "Foietaj", "Măr", "Tartă",
     "Feliile de măr se așază pe o bază de foietaj, cu zahăr după gust, și se coc într-o tartă."),
    ("tarta-foietaj-fruct", "Foietaj", "Fruct", "Tartă",
     "Fructele pregătite acoperă o bază de foietaj, coaptă ca tartă dulce."),
    ("tarta-ganache", "Biscuit", "Ganache", "Tartă",
     (
         "Biscuiții mărunțiți și legați cu unt formează o bază de tartă, umplută "
         "cu ganache și răcită."
     )),
    ("budinca-orez-lapte", "Orez", "Lapte", "Budincă de orez",
     "Orezul se fierbe în lapte îndulcit, apoi se leagă cu ou și se coace într-o budincă."),
    ("gris-lapte", "Griș", "Lapte", "Griș cu lapte",
     "Grișul se fierbe în lapte îndulcit, amestecând până se îngroașă."),
    ("piure-mazare-unt", "Mazăre", "Unt", "Piure de mazăre",
     "Mazărea fiartă se pasează fin și se amestecă cu unt pentru un piure."),
    ("salata-cartofi-ceapa", "Cartof", "Ceapă", "Salată de cartofi",
     (
         "Cartofii fierți și răciți se taie și se amestecă cu ceapă, ulei și "
         "condimente într-o salată."
     )),
    ("salata-cartofi-masline", "Cartof", "Măsline", "Salată de cartofi",
     (
         "Măslinele se combină cu cartofi fierți și răciți, ceapă și dressing "
         "într-o salată de cartofi."
     )),
    ("chiftele-legume-ou", "Legume", "Ou", "Chiftele de legume",
     (
         "Legumele mărunțite și bine scurse se leagă cu ou și făină sau pesmet, "
         "apoi se modelează și se gătesc."
     )),
    ("chiftele-cartofi-ou", "Cartof", "Ou", "Chiftele de legume",
     (
         "Cartofii pregătiți și mărunțiți se leagă cu ou, verdețuri și puțină "
         "făină, apoi se prăjesc ori se coc ca chiftele."
     )),
    ("omleta-tigaie", "Ou", "Tigaie", "Omletă",
     "Ouăle bătute se gătesc în tigaie cu puțină grăsime până se încheagă într-o omletă."),
    ("omleta-lapte", "Ou", "Lapte", "Omletă",
     "O cantitate mică de lapte se poate adăuga ouălor bătute, gătite apoi în tigaie ca omletă."),
    ("ou-fiert-oala", "Ou", "Oală", "Ou fiert",
     "Oul în coajă se gătește în apă fierbinte, într-o oală, până se încheagă în gradul dorit."),
    ("ou-fiert-apa", "Ou", "Apă", "Ou fiert",
     "Oul în coajă se fierbe în apă pentru un ou fiert, moale sau tare după timpul de gătire."),
    ("paine-prajita-tigaie", "Pâine", "Tigaie", "Pâine prăjită",
     "Felia de pâine rumenită pe ambele părți într-o tigaie devine pâine prăjită."),
    ("paine-prajita-cuptor", "Pâine", "Cuptor de bucătărie", "Pâine prăjită",
     "Feliile de pâine se rumenesc pe ambele părți în cuptor pentru pâine prăjită."),
    ("friganele-ou", "Pâine", "Ou", "Frigănele",
     "Feliile de pâine trecute prin lapte și ou bătut se rumenesc în tigaie ca frigănele."),
    ("supa-crema-mazare", "Supă", "Piure de mazăre", "Supă cremă",
     "Piureul de mazăre se subțiază cu supă și se omogenizează într-o supă cremă."),
    ("supa-crema-cartofi", "Supă", "Piure de cartofi", "Supă cremă",
     "Piureul de cartofi se poate omogeniza cu supă într-o supă cremă, asezonată după gust."),
    ("sos-iaurt-usturoi", "Iaurt", "Usturoi", "Sos de iaurt",
     (
         "Usturoiul zdrobit se amestecă în iaurt, cu sare și alte arome după "
         "gust, pentru un sos rece."
     )),
    ("sos-iaurt-mujdei", "Iaurt", "Mujdei", "Sos de iaurt",
     "Mujdeiul amestecat cu iaurt formează un sos rece cu usturoi."),
    ("cartofi-copti-cuptor", "Cartof", "Cuptor de bucătărie", "Cartofi copți",
     "Cartofii întregi sau tăiați se gătesc în cuptor până sunt fragezi și rumeniți."),
    ("legume-gratar", "Legume", "Grătar", "Legume la grătar",
     "Legumele pregătite și feliate se frig pe grătar și se asezonează după gust."),
    ("legume-gratar-vanata", "Vânătă", "Grătar", "Legume la grătar",
     "Vânăta feliată și unsă ușor cu ulei se poate frige pe grătar ca garnitură de legume."),
    ("sos-branza-lapte", "Brânză", "Lapte", "Sos de brânză",
     (
         "O brânză care se topește se încorporează într-o bază caldă cu lapte, "
         "făină și unt pentru un sos de brânză."
     )),
    ("sos-cascaval-lapte", "Cașcaval", "Lapte", "Sos de brânză",
     "Cașcavalul ras se topește într-o bază albă cu lapte, unt și făină pentru un sos cremos."),
    ("paste-sos-rosii", "Paste", "Sos de roșii", "Paste cu sos de roșii",
     "Pastele fierte se amestecă și se încălzesc împreună cu sosul de roșii."),
    ("paste-branza", "Paste", "Brânză", "Paste cu brânză",
     (
         "Pastele fierte se amestecă cu brânză, dulci sau sărate după sortiment, "
         "și se pot rumeni la cuptor."
     )),
    ("paste-sos-branza", "Paste", "Sos de brânză", "Paste cu brânză",
     "Sosul cald de brânză se amestecă cu pastele fierte pentru un preparat cremos."),
    ("pesto-busuioc", "Busuioc", "Ulei", "Pesto",
     (
         "Frunzele de busuioc se mărunțesc cu ulei de măsline, usturoi, nuci sau "
         "semințe și brânză tare pentru pesto."
     )),
    ("pesto-patrunjel", "Pătrunjel", "Nucă", "Pesto",
     "Pătrunjelul se poate mărunți cu nucă, usturoi și ulei într-o variantă de pesto."),
    ("focaccia-masline", "Aluat", "Măsline", "Focaccia",
     (
         "Aluatul dospit și bine hidratat se întinde în tavă cu ulei de măsline, "
         "se adaugă măsline și se coace ca focaccia."
     )),
    ("hummus-lamaie", "Năut", "Lămâie", "Hummus",
     "Năutul fiert se pasează cu zeamă de lămâie, tahini, usturoi și apă sau ulei pentru hummus."),
    ("hummus-usturoi", "Năut", "Usturoi", "Hummus",
     "Usturoiul aromatizează pasta de năut fiert, cu tahini și lămâie, pentru hummus."),
    ("crema-branza-iaurt", "Brânză", "Iaurt", "Cremă de brânză",
     "Brânza bine scursă se pasează fin cu iaurt pentru o cremă tartinabilă."),
    ("salata-vinete-ulei", "Vânătă", "Ulei", "Salată de vinete",
     "Vinetele coapte, curățate și scurse se toacă și se freacă cu ulei pentru salată de vinete."),
    ("salata-vinete-maioneza", "Vânătă", "Maioneză", "Salată de vinete",
     "Vinetele coapte, curățate și tocate se pot amesteca cu maioneză pentru salată de vinete."),
    ("zacusca-vinete", "Vânătă", "Ardei", "Zacuscă",
     "Vinetele și ardeii copți se gătesc împreună cu ceapă, roșii și ulei în zacuscă."),
    ("shaorma-lipie-friptura", "Lipie", "Friptură", "Șaorma cu de toate",
     (
         "Lipia învelește carne friptă și feliată, completată cu legume, cartofi "
         "prăjiți și sosuri pentru șaorma."
     )),
    ("shaorma-lipie-cartofi", "Lipie", "Cartofi prăjiți", "Șaorma cu de toate",
     "Cartofii prăjiți intră în lipia de șaorma alături de carne friptă, legume și sosuri."),
    ("sandvis-lipie-hummus", "Lipie", "Hummus", "Sandviș",
     "Lipia umplută cu hummus și legume după gust se rulează ca un sandviș."),
    ("sandvis-vinete", "Pâine", "Salată de vinete", "Sandviș",
     "Salata de vinete întinsă pe pâine formează un sandviș deschis."),
    ("sandvis-crema-branza", "Pâine", "Cremă de brânză", "Sandviș",
     "Crema de brânză întinsă pe pâine este baza unui sandviș, cu adaosuri după gust."),
    ("sandvis-paine-prajita", "Pâine prăjită", "Brânză", "Sandviș",
     "Brânza pusă pe pâine prăjită formează un sandviș crocant."),
    ("sandvis-focaccia", "Focaccia", "Cașcaval", "Sandviș",
     "Focaccia tăiată pe grosime și umplută cu cașcaval formează un sandviș."),
    ("pizza-sos-rosii", "Aluat", "Sos de roșii", "Pizza",
     "Sosul de roșii se întinde pe blatul de aluat, se adaugă toppinguri și se coace pizza."),
    ("pizza-pesto", "Aluat", "Pesto", "Pizza",
     (
         "Pesto poate aromatiza blatul unei pizza, completat cu brânză și alte "
         "ingrediente înainte de coacere."
     )),
    ("cremsnit-foietaj", "Foietaj", "Cremă de vanilie", "Cremșnit",
     "Foile coapte de foietaj se umplu cu cremă de vanilie pentru cremșnit."),
    ("cornulete-crema-fistic", "Aluat", "Pastă dulce de fistic", "Cornulețe",
     "Crema de fistic poate umple cornulețe din aluat fraged, coapte apoi."),
    ("inghetata-sos-caramel", "Sos de caramel", "Frișcă", "Înghețată",
     "Sosul de caramel se încorporează într-o bază cu frișcă, apoi se congelează ca înghețată."),
    ("mousse-ganache", "Ganache", "Frișcă", "Mousse de ciocolată",
     "Ganache-ul răcorit se încorporează în frișcă pentru o compoziție aerată de mousse."),
    ("pui-cuptor", "Carne de pui", "Cuptor de bucătărie", "Friptură",
     "Carnea de pui pregătită și condimentată se coace în cuptor ca friptură."),
    ("pui-firimitura", "Carne de pui", "Firimitură", "Șnițel",
     (
         "Feliile de piept de pui se trec prin făină, ou și pesmet din pâine "
         "uscată, apoi se prăjesc ca șnițele."
     )),
    ("carne-cutit", "Carne", "Cuțit", "Carne tocată",
     "Carnea dezosată se poate toca foarte mărunt cu un cuțit pentru umpluturi și alte preparate."),
])
RECIPES.extend([
    ("varza-calita-tigaie", "Varză", "Tigaie", "Varză călită",
     "Varza tăiată fin se călește în tigaie cu grăsime și se înăbușă până devine fragedă."),
    ("varza-murata-calita", "Varză murată", "Tigaie", "Varză călită",
     "Varza murată tăiată și scursă se călește cu grăsime în tigaie, "
     "apoi se gătește până se înmoaie."),
    ("crutoane-cutit", "Pâine prăjită", "Cuțit", "Crutoane",
     "Pâinea prăjită se taie în cubulețe cu un cuțit pentru crutoane de pus în supe și salate."),
    ("umplutura-fistic-kataif", "Pastă dulce de fistic", "Kataif", "Umplutură de fistic și kataif",
     "Fideaua kataif rumenită în unt se amestecă cu pasta dulce de fistic "
     "pentru umplutură crocantă."),
    ("aluat-praf-copt", "Făină", "Praf de copt", "Aluat",
     (
         "Făina și praful de copt se combină cu lichid și alte ingrediente "
         "într-un aluat afânat pentru copt."
     )),
    ("crutoane-tava", "Pâine", "Tavă de copt", "Crutoane",
     (
         "Cubulețele de pâine se așază în tavă, se stropesc cu ulei și se coc "
         "până devin crutoane crocante."
     )),
    ("ciorba-fasole-afumaturi", "Fasole", "Afumături", "Ciorbă de fasole",
     "Afumăturile se fierb cu fasole și legume într-o ciorbă de fasole, acrită după gust."),
    ("mici-tocata-bicarbonat", "Carne tocată", "Bicarbonat de sodiu alimentar", "Mici",
     (
         "Carnea tocată se frământă cu condimente și puțin bicarbonat alimentar, "
         "apoi se modelează și se frige la grătar ca mici."
     )),
    ("chiftele-tocata-ou", "Carne tocată", "Ou", "Chiftele",
     (
         "Oul leagă carnea tocată cu legume, pesmet și condimente; compoziția se "
         "modelează și se gătește în chiftele."
     )),
])

# Session 02: reuse three previously terminal discoveries.
RECIPES.extend([
    ('sandvis-omleta', 'Omletă', 'Pâine', 'Sandviș',
     'Omleta gătită, așezată între felii de pâine, formează un sandviș; '
     'se pot adăuga legume sau brânză.'),
    ('salata-cartofi-ou-fiert', 'Ou fiert', 'Cartof', 'Salată de cartofi',
     'Cartofii fierți, răciți și tăiați se amestecă cu ou fiert și un sos '
     'pentru o salată de cartofi.'),
    ('piure-cartofi-copti-unt', 'Cartofi copți', 'Unt', 'Piure de cartofi',
     'Miezul cartofilor copți se scoate din coajă și se pasează cu unt; '
     'se adaugă lapte pentru consistența dorită.'),
])

# Preparation-specific references for the newly authored reuse recipes.
RECIPE_SOURCES = {
    'sandvis-omleta': ['https://pofta-buna.com/sandvisuri-cu-omleta/'],
    'salata-cartofi-ou-fiert': ['https://www.lauralaurentiu.ro/retete-culinare/retete-diverse/salata-de-cartofi-cu-oua-fierte.html'],
    'piure-cartofi-copti-unt': ['https://www.crunchtimekitchen.com/ultimate-guide-to-mashed-potatoes/'],
}

# Session 03: new recognizable preparations and onward uses.
WORLD_CONCEPTS.update(
    {'Mere coapte': {'id': 'alw_food_mere_coapte',
                     'description': 'Mere gătite în cuptor până se înmoaie, servite simple '
                                    'sau cu umpluturi dulci și arome.',
                     'sources': ['https://www.kamis.ro/retete/deserturi-si-bauturi/mere-coapte']},
     'Ardei copți': {'id': 'alw_food_ardei_copti',
                     'description': 'Ardei gătiți la căldură puternică și curățați de '
                                    'pieliță, folosiți în salate, garnituri sau alte '
                                    'preparate.',
                     'sources': ['https://www.lauralaurentiu.ro/retete-culinare/retete-diverse/ardei-copti-in-cuptor-cea-mai-simpla-si-igienica-metoda-de-copt-ardeii.html']},
     'Pilaf de legume': {'id': 'alw_food_pilaf_legume',
                         'description': 'Preparat din orez gătit cu legume și apă sau supă, '
                                        'până când boabele absorb lichidul și se înmoaie.',
                         'sources': ['https://www.barbatlacratita.ro/2011/01/pilaf-de-orez-cu-legume.html']},
     'Dovleac copt': {'id': 'alw_food_dovleac_copt',
                      'description': 'Bucăți de dovleac gătite în cuptor până când pulpa se '
                                     'înmoaie; pot fi servite ca atare sau folosite în alte '
                                     'preparate.',
                      'sources': ['https://www.lauralaurentiu.ro/retete-culinare/retete-diverse/dovleac-copt-cum-se-coace-dovleacul-placintar-la-cuptor.html']}}
)
RECIPES.extend(
    [('mere-coapte-cuptor',
      'Măr',
      'Cuptor de bucătărie',
      'Mere coapte',
      'Merele pregătite se coc în cuptor până se înmoaie, simple sau umplute cu nucă, miere '
      'și scorțișoară.'),
     ('ardei-copti-cuptor',
      'Ardei',
      'Cuptor de bucătărie',
      'Ardei copți',
      'Ardeii se coc în cuptor până se înmoaie și li se rumenește pielița, apoi se curăță.'),
     ('dovleac-copt-cuptor',
      'Dovleac',
      'Cuptor de bucătărie',
      'Dovleac copt',
      'Dovleacul curățat de semințe și tăiat în bucăți se coace până când pulpa devine '
      'moale.'),
     ('pilaf-orez-legume',
      'Orez',
      'Legume',
      'Pilaf de legume',
      'Orezul se gătește împreună cu legume călite și apă sau supă până absoarbe lichidul și '
      'se înmoaie.'),
     ('zacusca-ardei-copti',
      'Ardei copți',
      'Vânătă',
      'Zacuscă',
      'Ardeii copți și curățați se toacă împreună cu vinete coapte, apoi se gătesc cu ceapă, '
      'roșii și ulei în zacuscă.'),
     ('supa-crema-dovleac-copt',
      'Dovleac copt',
      'Supă',
      'Supă cremă',
      'Pulpa dovleacului copt se pasează cu supă și se încălzește până se obține o supă '
      'cremă, asezonată după gust.')]
)
RECIPE_SOURCES.update(
    {'mere-coapte-cuptor': ['https://www.kamis.ro/retete/deserturi-si-bauturi/mere-coapte'],
     'ardei-copti-cuptor': ['https://www.lauralaurentiu.ro/retete-culinare/retete-diverse/ardei-copti-in-cuptor-cea-mai-simpla-si-igienica-metoda-de-copt-ardeii.html'],
     'dovleac-copt-cuptor': ['https://www.lauralaurentiu.ro/retete-culinare/retete-diverse/dovleac-copt-cum-se-coace-dovleacul-placintar-la-cuptor.html'],
     'pilaf-orez-legume': ['https://www.barbatlacratita.ro/2011/01/pilaf-de-orez-cu-legume.html'],
     'zacusca-ardei-copti': ['https://www.lauralaurentiu.ro/retete-culinare/conserve/zacusca-de-vinete.html'],
     'supa-crema-dovleac-copt': ['https://www.retetelemeledragi.com/2024/11/supa-crema-de-dovleac-copt.html/']}
)
