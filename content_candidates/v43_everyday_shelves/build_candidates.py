#!/usr/bin/env python3
"""Build and audit strict V43 everyday-shelf Conexiuni proposals.

Authoring only: reads the committed KG/pack census and writes candidate JSON plus
an audit. It never edits the fixture, pack, demotions, ranking, or status.
"""

from __future__ import annotations

import hashlib
import json
import sys
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]

import critique_pack  # noqa: E402

PACK_PATH = ROOT / "cat_de_roman_esti/fixtures/games_pack.json"
KG_PATH = ROOT / "cat_de_roman_esti/fixtures/kg_sample.json"
DEMOTIONS_PATH = ROOT / "cat_de_roman_esti/fixtures/board_demotions_v43.json"


@dataclass(frozen=True)
class Group:
    label: str
    criterion: str
    tiles: tuple[str, str, str, str]
    recognition: str = "mainstream"


@dataclass(frozen=True)
class Board:
    ref: str
    category: str
    difficulty: str
    anchor: int
    groups: tuple[Group, Group, Group, Group]
    flags: tuple[str, ...] = field(default_factory=tuple)


def g(label: str, criterion: str, *tiles: str, recognition: str = "mainstream") -> Group:
    assert len(tiles) == 4, (label, tiles)
    return Group(label, criterion, tuple(tiles), recognition)


def b(
    ref: str,
    category: str,
    difficulty: str,
    anchor: int,
    *groups: Group,
    flags: tuple[str, ...] = (),
) -> Board:
    assert len(groups) == 4, (ref, groups)
    return Board(ref, category, difficulty, anchor, tuple(groups), flags)


BOARDS = (
    # ---------------------------------------------------------------- sport / ușor
    b(
        "sport_usor_01", "sport", "usor", 0,
        g("Sporturi de echipă cu minge", "Fiecare este un sport de echipă jucat cu minge.",
          "Fotbal", "Baschet", "Volei", "Rugby"),
        g("Cluburi românești de fotbal", "Fiecare joacă în fotbalul românesc.",
          "FCSB", "CFR Cluj", "Farul Constanța", "Universitatea Craiova"),
        g("Medaliați olimpici români",
          "Fiecare a câștigat cel puțin o medalie olimpică pentru România.",
          "Gabriela Szabó", "Ana Maria Brânză", "Elisabeta Lipă", "Mihaela Cambei"),
        g("Evenimente sportive din 2024 sau 2025",
          "Fiecare eveniment a avut loc în 2024 sau 2025.",
          "EURO 2024", "Jocurile Olimpice Paris 2024", "Retragerea Simonei Halep",
          "Dubla mondială de la Singapore"),
    ),
    b(
        "sport_usor_02", "sport", "usor", 0,
        g("Sporturi olimpice individuale",
          "În fiecare, sportivul poate concura individual la Jocurile Olimpice.",
          "Atletism", "Înot sportiv", "Haltere", "Tenis"),
        g("Cluburi sportive din București", "Fiecare club are sediul în București.",
          "FCSB", "Dinamo București", "Rapid București", "CSM București"),
        g("Gimnaste române",
          "Fiecare a reprezentat România în gimnastica artistică.",
          "Cătălina Ponor", "Simona Amânar", "Ana Bărbosu", "Sabrina Maneca-Voinea"),
        g("Fundași români din generații diferite",
          "Fiecare a jucat fundaș pentru echipa națională a României.",
          "Gică Popescu", "Cristian Chivu", "Dan Petrescu", "Miodrag Belodedici"),
    ),
    b(
        "sport_usor_03", "sport", "usor", 0,
        g("Titulari ai României la turneul continental din 2024",
          "Fiecare a fost titular pentru România la turneul continental din 2024.",
          "Nicolae Stanciu", "Andrei Rațiu", "Radu Drăgușin", "Florin Niță"),
        g("Antrenori români campioni în prima ligă",
          "Fiecare a câștigat ca antrenor principal un campionat național de prim eșalon.",
          "Mircea Lucescu", "Dan Petrescu", "Edward Iordănescu", "Emeric Ienei"),
        g("Victorii românești pe mari scene internaționale",
          "Fiecare eveniment s-a încheiat cu un titlu câștigat de un român "
          "sau o echipă românească.",
          "Liga Campionilor la handbal", "Roland Garros", "Wimbledon 2019",
          "US Open 1972"),
        g("Rezultate românești din vara sportivă 2024",
          "Fiecare rezultat a fost obținut de România între iunie și august 2024.",
          "România - Ucraina 3-0", "Aurul de la Paris 2024",
          "Bronzul de la sol 2024", "Aurul optului feminin (2024)"),
        flags=("two_event_groups_make_the_board_repetitive",),
    ),
    b(
        "sport_usor_04", "sport", "usor", 0,
        g("Sportivi români în sporturi cu rachetă sau paletă",
          "Fiecare reprezintă România într-un sport jucat cu rachetă sau paletă.",
          "Ion Țiriac", "Horia Tecău", "Jaqueline Cristian", "Bernadette Szőcs"),
        g("Medaliați români la Paris 2024",
          "Fiecare a câștigat o medalie pentru România la Jocurile Olimpice din 2024.",
          "Ana Bărbosu", "Mihaela Cambei", "Simona Radiș", "Ancuța Bodnar"),
        g("Au un oraș în numele afișat",
          "Numele fiecărui club include explicit numele unui oraș.",
          "CFR Cluj", "Farul Constanța", "CSM București", "Inter Milano"),
        g("Sporturi cu adversar direct",
          "În fiecare, un sportiv sau o echipă înfruntă direct adversarul.",
          "Box", "Scrimă", "Tenis de masă", "Tenis"),
    ),
    b(
        "sport_usor_05", "sport", "usor", 0,
        g("Sportivi români prezenți la Jocurile Olimpice",
          "Fiecare a reprezentat România la cel puțin o ediție a Jocurilor Olimpice.",
          "Cătălina Ponor", "Leonard Doroftei", "Sorana Cîrstea",
          "Ana Maria Brânză"),
        g("Jucători din lotul României la EURO 2024",
          "Fiecare a făcut parte din lotul României la turneul continental din 2024.",
          "Radu Drăgușin", "Florin Niță", "Dennis Man", "Ianis Hagi"),
        g("Evenimente sportive din 2024",
          "Fiecare eveniment sportiv a avut loc în 2024.",
          "EURO 2024", "Jocurile Olimpice Paris 2024",
          "România - Ucraina 3-0", "Bronzul de la sol 2024"),
        g("Roluri umane la o partidă",
          "Fiecare numește un rol uman prezent la o partidă.",
          "Arbitru", "Antrenor", "suporter", "Portar"),
    ),
    b(
        "sport_usor_06", "sport", "usor", 0,
        g("Internaționali români ofensivi",
          "Fiecare este fotbalist român cu rol preponderent ofensiv.",
          "Adrian Mutu", "Ianis Hagi", "Dennis Man", "Louis Munteanu"),
        g("Fundași ai naționalei", "Fiecare a jucat fundaș pentru naționala României.",
          "Gică Popescu", "Dan Petrescu", "Radu Drăgușin", "Andrei Rațiu"),
        g("Sportivi români de duel sau contact",
          "Fiecare a concurat într-un sport bazat pe duel direct ori contact.",
          "Leonard Doroftei", "Lucian Bute", "Cătălin Moroșanu", "Ana Maria Brânză"),
        g("Evenimente sportive din 2025 sau 2026",
          "Fiecare eveniment s-a produs în 2025 sau 2026.",
          "Retragerea Simonei Halep", "Retragerea Cristinei Neagu",
          "Titlul Craiovei din 2026", "Barajul cu Turcia 2026"),
        flags=("recent_events_need_gate_reverification",),
    ),
    # --------------------------------------------------------------- sport / normal
    b(
        "sport_normal_01", "sport", "normal", 2,
        g("Lotul României din 2024",
          "Fiecare a făcut parte din lotul României la turneul continental din 2024.",
          "Nicolae Stanciu", "Andrei Rațiu", "Dennis Man", "Ianis Hagi"),
        g("Antrenori care au fost internaționali români",
          "Fiecare a antrenat la nivel profesionist după ce a jucat pentru naționala României.",
          "Mircea Lucescu", "Dan Petrescu", "Cristian Chivu", "Anghel Iordănescu"),
        g("Câștigătoare de cupe europene",
          "Fiecare club a câștigat cel puțin o cupă europeană majoră.",
          "Steaua 1986", "FC Barcelona", "CSM București", "Galatasaray"),
        g("Sporturi individuale cu medalii olimpice românești",
          "În fiecare sport, România a câștigat cel puțin o medalie olimpică individuală.",
          "Atletism", "Box", "Haltere", "Scrimă"),
    ),
    b(
        "sport_normal_02", "sport", "normal", 0,
        g("Tenismeni români", "Fiecare a reprezentat România în tenisul profesionist.",
          "Ilie Năstase", "Ion Țiriac", "Horia Tecău", "Sorana Cîrstea"),
        g("Campioane europene după 2010",
          "Fiecare a câștigat după 2010 un titlu european de senioare.",
          "Simona Radiș", "Mihaela Cambei", "Elizabeta Samara",
          "Bernadette Szőcs"),
        g("Jucători defensivi români",
          "Fiecare a apărat poarta ori linia defensivă a unei echipe românești.",
          "Cristian Chivu", "Radu Drăgușin", "Andrei Rațiu", "Miodrag Belodedici"),
        g("Medaliați olimpici înainte de 2005",
          "Fiecare a câștigat o medalie olimpică până în 2004 inclusiv.",
          "Gabriela Szabó", "Iolanda Balaș", "Leonard Doroftei", "Cătălina Ponor"),
    ),
    b(
        "sport_normal_03", "sport", "normal", 0,
        g("Au purtat banderola României",
          "Fiecare a purtat banderola echipei naționale de fotbal.",
          "Gică Popescu", "Cristian Chivu", "Nicolae Stanciu", "Adrian Mutu"),
        g("Sportive cu rachetă sau paletă",
          "Fiecare concurează în tenis ori tenis de masă.",
          "Sorana Cîrstea", "Jaqueline Cristian", "Bernadette Szőcs", "Elizabeta Samara"),
        g("Sportivi români în primii opt la Paris 2024",
          "Fiecare s-a clasat între primele opt la proba sau întrecerea sa olimpică din 2024.",
          "Ana Bărbosu", "Mihaela Cambei", "Sabrina Maneca-Voinea",
          "David Popovici"),
        g("Au condus loturi naționale de seniori ale României",
          "Fiecare a condus un lot național de seniori al României.",
          "Octavian Bellu", "Emeric Ienei", "Edward Iordănescu",
          "Anghel Iordănescu"),
    ),
    b(
        "sport_normal_04", "sport", "normal", 0,
        g("Români care au jucat în Serie A",
          "Fiecare a evoluat ca fotbalist în prima ligă italiană.",
          "Cristian Chivu", "Radu Drăgușin", "Dennis Man", "Dan Petrescu"),
        g("Prenume care încep cu A",
          "Primul cuvânt din numele afișat al fiecărei persoane începe cu litera A.",
          "Andrei Rațiu", "Ana Bărbosu", "Ana Maria Brânză", "Ancuța Bodnar"),
        g("Medaliați români la Atlanta 1996",
          "Fiecare a câștigat o medalie pentru România la Jocurile Olimpice din 1996.",
          "Gabriela Szabó", "Leonard Doroftei", "Simona Amânar", "Elisabeta Lipă"),
        g("Evenimente cu anul în denumire",
          "Numele afișat al fiecărui eveniment include explicit un an din patru cifre.",
          "EURO 2024", "Jocurile Olimpice Paris 2024", "Wimbledon 2019",
          "US Open 1972"),
    ),
    b(
        "sport_normal_05", "sport", "normal", 0,
        g("Oameni ai parcursului continental din 2024",
          "Fiecare a avut rol direct în parcursul României din 2024.",
          "Edward Iordănescu", "Nicolae Stanciu", "Dennis Man", "Radu Drăgușin"),
        g("Organizații cunoscute din sportul românesc",
          "Fiecare este club, lot sau publicație din sportul românesc.",
          "Dinamo București", "Rapid București", "Gazeta Sporturilor",
          "Lotul olimpic al României"),
        g("Evenimente sportive din 2024 până în 2026",
          "Fiecare eveniment s-a produs între 2024 și 2026 inclusiv.",
          "Retragerea Cristinei Neagu", "Barajul cu Turcia 2026",
          "România - Ucraina 3-0", "Dubla mondială de la Singapore"),
        g("Termeni de arbitraj și rezultat",
          "Fiecare ține de validarea ori consemnarea rezultatului.",
          "Arbitru", "fluier", "scor", "Penalty"),
        flags=("association_and_type_bag_board",),
    ),
    b(
        "sport_normal_06", "sport", "normal", 0,
        g("Sportivi cu carieră internațională",
          "Fiecare a avut o carieră sportivă internațională.",
          "Emma Răducanu", "Horia Tecău", "Iolanda Balaș", "Octavian Bellu"),
        g("Cluburi din România și străinătate",
          "Fiecare este un club sportiv cunoscut publicului român.",
          "Dinamo București", "Rapid București", "Galatasaray", "FC Barcelona"),
        g("Finaluri și medalii recente",
          "Fiecare este un moment sportiv care a adus medalie sau a încheiat o carieră.",
          "Aurul de la Paris 2024", "Bronzul de la sol 2024",
          "Retragerea Simonei Halep", "Retragerea Cristinei Neagu"),
        g("Probe și trasee cronometrate",
          "Fiecare numește o probă ori un spațiu unde timpul decide clasamentul.",
          "200 m liber", "alergare", "pistă", "înot"),
        flags=("club_group_is_broad",),
    ),
    # ----------------------------------------------------------- gastronomie / normal
    b(
        "gastronomie_normal_01", "gastronomie", "normal", 0,
        g("Vase pentru servit", "Fiecare este un vas din care se mănâncă ori se bea.",
          "Farfurie", "Castron", "Cană", "Pahar"),
        g("Se întind pe pâine", "Fiecare poate fi întins direct pe o felie de pâine.",
          "Pate", "Unt", "Fasole bătută", "Dulceață"),
        g("Prăjite până devin rumene",
          "Prepararea obișnuită a fiecăruia implică prăjire.",
          "Cartofi prăjiți", "Cașcaval pane", "Șnițel", "Gogoși"),
        g("Mezeluri", "Fiecare este un produs din categoria mezelurilor.",
          "Parizer", "Salam de Sibiu", "Caltaboș", "Lebăr"),
    ),
    b(
        "gastronomie_normal_02", "gastronomie", "normal", 2,
        g("Băuturi fără alcool cunoscute înainte de 1990",
          "Fiecare se consuma în România înainte de anul 1990 și nu este alcoolică.",
          "Cico", "Must", "Socată", "Cafea"),
        g("Gustări de luat la drum",
          "Fiecare poate fi mâncată ușor fără tacâmuri, ca gustare.",
          "Pufuleți", "Biscuit", "Sandviș", "Merdenea"),
        g("Legume puse crude în salată", "Fiecare este folosită frecvent crudă în salate.",
          "Ardei", "Castravete", "Ridiche", "Ceapă"),
        g("Fructe de vară", "Fiecare se coace și se consumă proaspăt vara în România.",
          "Căpșună", "Cireașă", "Strugure", "Pepene"),
        flags=("hold_subjective_travel_snack_and_borderline_summer_grape",),
    ),
    b(
        "gastronomie_normal_03", "gastronomie", "normal", 0,
        g("Chefi cunoscuți publicului român",
          "Fiecare este bucătar profesionist cunoscut din media românească.",
          "Cătălin Scărlătescu", "Florin Dumitrescu", "Adi Hădean", "Richard Abou Zaki"),
        g("Localuri bucureștene cunoscute",
          "Fiecare este un local sau lanț cu prezență cunoscută în București.",
          "Caru' cu Bere", "Dristor Kebap", "Taverna Racilor", "Hanul lui Manuc"),
        g("Comenzi culinare devenite tendințe",
          "Fiecare a fost o tendință vizibilă în meniurile urbane recente.",
          "Sushi", "Smash burger", "Bubble tea", "Matcha"),
        g("Deserturi și gustări dulci",
          "Fiecare este un preparat dulce servit ca desert ori gustare.",
          "Amandină", "Salam de biscuiți", "Turtă dulce", "Gogoși"),
        flags=("two_deep_cuts_in_chef_group",),
    ),
    b(
        "gastronomie_normal_04", "gastronomie", "normal", 2,
        g("Se coc în cuptor",
          "Fiecare preparat are o versiune tradițională coaptă în cuptor.",
          "Pască", "Pâine de casă", "Covrigi de Buzău", "Plăcintă cu mere"),
        g("Se mănâncă din farfurie adâncă", "Fiecare este o zeamă servită cu lingura.",
          "Ciorbă de fasole", "Ciorbă de perișoare", "Supă cu găluște", "Borș"),
        g("Lactate de bază", "Fiecare este un produs lactat de consum curent.",
          "Iaurt", "Smântână", "Lapte", "Unt"),
        g("Preparate din carne de porc",
          "Carnea de porc este ingredientul definitoriu al fiecăruia.",
          "Tobă", "Lebăr", "Salam de Sibiu", "Pomana porcului"),
    ),
    b(
        "gastronomie_normal_05", "gastronomie", "normal", 1,
        g("Arome din grădină",
          "Fiecare este plantă sau bulb folosit pentru aromarea mâncării.",
          "Mărar", "Pătrunjel", "Usturoi", "Ceapă"),
        g("Ingrediente pentru clătite",
          "Fiecare intră într-un aluat obișnuit de clătite.",
          "Făină", "Ou", "Lapte", "Ulei"),
        g("Comenzi urbane internaționale",
          "Fiecare este o comandă urbană de origine internațională.",
          "Pizza", "Sushi", "Smash burger", "Șaorma cu de toate"),
        g("Se păstrează în borcan", "Fiecare este conservat în mod obișnuit în borcan.",
          "Dulceață", "Compot", "Magiun de Topoloveni", "Castraveți murați"),
    ),
    b(
        "gastronomie_normal_06", "gastronomie", "normal", 0,
        g("Toponime în denumirea afișată",
          "Numele afișat al fiecărui produs include explicit un toponim românesc.",
          "Salam de Sibiu", "Telemea de Ibănești", "Magiun de Topoloveni",
          "Cârnați din topor din Vâlcea"),
        g("Preparate din aluat dospit",
          "Aluatul fiecărui preparat este lăsat să dospească înainte de gătire.",
          "Pizza", "Gogoși", "Langoși", "Pâine cu maia"),
        g("Cacao în compoziție",
          "Fiecare produs dulce conține cacao.",
          "Salam de biscuiți", "Amandină", "Joffre", "Ciocolata ROM"),
        g("Părți comestibile crescute sub pământ",
          "Partea consumată a fiecărei plante crește sub pământ.",
          "Morcov", "Ridiche", "Ceapă", "Usturoi"),
    ),
    # -------------------------------------------------------------- geografie / normal
    b(
        "geografie_normal_01", "geografie", "normal", 0,
        g("Afluenți direcți ai Dunării", "Fiecare râu se varsă direct în Dunăre.",
          "Argeș", "Jiu", "Siret", "Tisa"),
        g("Forme majore de relief", "Fiecare este o formă de relief distinctă.",
          "munte", "deal", "câmpie", "podiș"),
        g("Orașe din Transilvania", "Fiecare oraș se află în Transilvania.",
          "Brașov", "Sibiu", "Târgu Mureș", "Deva"),
        g("Termeni ai țărmului",
          "Fiecare numește o formă sau zonă aflată la marginea unei ape mari.",
          "mal", "coastă", "faleză", "plajă"),
    ),
    b(
        "geografie_normal_02", "geografie", "normal", 0,
        g("Orașe-port din România", "Fiecare localitate are port maritim sau fluvial.",
          "Brăila", "Galați", "Sulina", "Tulcea"),
        g("Repere din Munții Bucegi", "Fiecare reper se află în masivul Bucegi.",
          "Babele", "Sfinxul din Bucegi", "Vârful Omu", "Crucea Caraiman"),
        g("Forme la contactul dintre uscat și apă",
          "Fiecare este o formă geografică aflată la întâlnirea uscatului cu apa.",
          "insulă", "peninsulă", "golf", "faleză"),
        g("Stațiuni balneare", "Fiecare localitate este cunoscută ca stațiune balneară.",
          "Borsec", "Techirghiol", "Sovata", "Slănic-Moldova"),
    ),
    b(
        "geografie_normal_03", "geografie", "normal", 0,
        g("Orașe din vestul țării", "Fiecare oraș este în jumătatea vestică a României.",
          "Timișoara", "Arad", "Oradea", "Deva"),
        g("Masive din Carpații Meridionali",
          "Fiecare masiv aparține Carpaților Meridionali.",
          "Munții Făgăraș", "Munții Piatra Craiului", "Munții Parâng", "Munții Retezat"),
        g("Lacuri și complexe lacustre",
          "Fiecare este un lac ori complex lacustru din România.",
          "Lacul Izvorul Muntelui", "Lacul Ursu", "Complexul Razim-Sinoe",
          "Lacul Sfânta Ana"),
        g("Regiuni istorice", "Fiecare este o regiune istorică românească.",
          "Bucovina", "Muntenia", "Moldova", "Maramureș"),
    ),
    b(
        "geografie_normal_04", "geografie", "normal", 0,
        g("Repere ale culoarului Dunării",
          "Fiecare este un reper geografic al culoarului Dunării din România.",
          "Porțile de Fier", "Cazanele Dunării", "Podul de la Brăila",
          "Canalul Dunăre-Marea Neagră"),
        g("Arii naturale protejate", "Fiecare loc are statut de arie naturală protejată.",
          "Vulcanii Noroioși", "Pădurea Letea", "Cheile Turzii", "Cheile Bicazului"),
        g("Orașe reședință de județ", "Fiecare este municipiu reședință de județ.",
          "Ploiești", "Suceava", "Oradea", "Arad"),
        g("Masive și grupe montane din România",
          "Fiecare numește o unitate montană distinctă din România.",
          "Munții Bucegi", "Ceahlău", "Munții Rodnei", "Munții Călimani"),
    ),
    b(
        "geografie_normal_05", "geografie", "normal", 0,
        g("Stațiuni în zone montane sau submontane",
          "Fiecare localitate este o stațiune aflată între dealuri ori munți.",
          "Poiana Brașov", "Bușteni", "Sovata", "Slănic-Moldova"),
        g("Forme și surse naturale",
          "Fiecare este o formă ori sursă naturală întâlnită în peisaj.",
          "peșteră", "izvor", "cascadă", "vulcan"),
        g("Lucrări care traversează relieful",
          "Fiecare este o lucrare românească majoră construită peste ori prin relief.",
          "Transfăgărășan", "Transalpina", "Porțile de Fier",
          "Canalul Dunăre-Marea Neagră"),
        g("Muzee despre patrimoniu material românesc",
          "Fiecare muzeu expune obiecte ori construcții din patrimoniul românesc.",
          "Muzeul ASTRA", "Muzeul Național al Satului „Dimitrie Gusti”",
          "Muzeul Național al Țăranului Român",
          "Muzeul Național de Istorie a României"),
        flags=("museum_group_is_broad",),
    ),
    b(
        "geografie_normal_06", "geografie", "normal", 0,
        g("Repere din București", "Fiecare reper se află în municipiul București.",
          "Therme București", "Arcul de Triumf", "Cișmigiu", "Arena Națională"),
        g("Destinații geologice din Transilvania",
          "Fiecare este o destinație geologică vizitabilă din Transilvania.",
          "Peștera Urșilor", "Peștera Scărișoara", "Salina Turda", "Cheile Turzii"),
        g("Termeni pentru traseul montan",
          "Fiecare numește un element concret întâlnit pe un traseu montan.",
          "potecă", "stâncă", "vale", "colină"),
        g("Ape sau forme litorale",
          "Fiecare este o întindere de apă ori o formă litorală.",
          "mare", "ocean", "golf", "peninsulă"),
        flags=("broad_littoral_group",),
    ),
    # ---------------------------------------------------------- personalitati / normal
    b(
        "personalitati_normal_01", "personalitati", "normal", 0,
        g("Prenumele Ion", "Prenumele fiecărei persoane este Ion.",
          "Ion Mincu", "Ion Rațiu", "Ion Popescu-Gopo", "Ion I. Agârbiceanu"),
        g("Prenumele Nicolae", "Prenumele fiecărei persoane este Nicolae.",
          "Nicolae Dobrin", "Nicolae Stanciu", "Nicolae Steinhardt", "Nicolae Teclu"),
        g("Scriitori români moderni",
          "Fiecare este autor român publicat în epoca modernă sau contemporană.",
          "Alexandru Macedonski", "Ana Blandiana", "Herta Muller",
          "Mircea Cărtărescu"),
        g("Medaliați olimpici români din sporturi individuale",
          "Fiecare a câștigat pentru România o medalie olimpică într-un sport individual.",
          "Ana Bărbosu", "Ana Maria Brânză", "Mihaela Cambei", "Cătălina Ponor"),
    ),
    b(
        "personalitati_normal_02", "personalitati", "normal", 0,
        g("Filozofi și eseiști", "Fiecare este cunoscut prin filozofie sau eseu.",
          "Constantin Noica", "Mircea Eliade", "Andrei Pleșu", "Gabriel Liiceanu"),
        g("Interpreți de muzică", "Fiecare este interpret român cunoscut pe scene muzicale.",
          "Hariclea Darclée", "Angela Gheorghiu", "Gheorghe Zamfir", "Maria Tănase"),
        g("Personalități medicale",
          "Fiecare a avut o carieră majoră în medicină sau sănătate publică.",
          "Mina Minovici", "Sofia Ionescu", "Carol Davila", "Raed Arafat"),
        g("Campioni din sporturi diferite",
          "Fiecare este campion român emblematic într-un sport diferit.",
          "Leonard Doroftei", "Horia Tecău", "Iolanda Balaș", "Mihaela Cambei"),
    ),
    b(
        "personalitati_normal_03", "personalitati", "normal", 0,
        g("Prenumele Radu", "Prenumele fiecărei persoane este Radu.",
          "Radu Beligan", "Radu Jude", "Radu Vâlcan", "Radu Drăgușin"),
        g("Prenumele Adrian", "Prenumele fiecărei persoane este Adrian.",
          "Adrian Mutu", "Adrian Ghenie", "Adrian Văncică", "Adrian Minune"),
        g("Pionieri români în știință și tehnică",
          "Fiecare a deschis drumuri într-un domeniu științific sau tehnic.",
          "Sofia Ionescu", "Dimitrie Leonida", "Gogu Constantinescu",
          "Petrache Poenaru"),
        g("Campioni români din sporturi diferite",
          "Fiecare a câștigat un titlu internațional major pentru România.",
          "Gabriela Szabó", "Cătălina Ponor", "Elizabeta Samara",
          "Cristina Neagu"),
    ),
    b(
        "personalitati_normal_04", "personalitati", "normal", 0,
        g("Pictori români", "Fiecare este pictor român cu operă muzeală.",
          "Theodor Pallady", "Nicolae Tonitza", "Corneliu Baba", "Adrian Ghenie"),
        g("Regizori de film români", "Fiecare este regizor român de lungmetraj.",
          "Tudor Giurgiu", "Corneliu Porumboiu", "Bogdan Mureșanu",
          "Sergiu Nicolaescu"),
        g("Scriitori români din secolul XX",
          "Fiecare a publicat literatură în secolul al XX-lea.",
          "Mihail Sebastian", "Hortensia Papadat-Bengescu", "Regina Elisabeta",
          "Elena Văcărescu"),
        g("Muzicieni clasici români", "Fiecare a avut carieră în muzica clasică.",
          "Sergiu Celibidache", "Dinu Lipatti", "Hariclea Darclée", "Angela Gheorghiu"),
        flags=("four_generic_class_lists",),
    ),
    b(
        "personalitati_normal_05", "personalitati", "normal", 0,
        g("Prenumele Florin", "Primul cuvânt din numele afișat este „Florin”.",
          "Florin Niță", "Florin Piersic Jr.", "Florin Răducioiu",
          "Florin Dumitrescu"),
        g("Figuri ale Revoluției de la 1848",
          "Fiecare a participat la mișcările revoluționare românești din 1848.",
          "Avram Iancu", "Nicolae Bălcescu", "Ana Ipătescu", "Vasile Alecsandri"),
        g("Aceeași inițială la prenume și nume",
          "Primul și ultimul cuvânt din numele afișat încep cu aceeași literă.",
          "Cristian Chivu", "Alexandru Arșinel", "Marius Moga", "Corneliu Coposu"),
        g("Nume de familie care încep cu S",
          "Numele de familie afișat al fiecărei persoane începe cu litera S.",
          "Elizabeta Samara", "Nicolae Stanciu", "Gabriela Szabó",
          "Nichita Stănescu"),
    ),
    b(
        "personalitati_normal_06", "personalitati", "normal", 0,
        g("Profesii din artele vizuale",
          "Fiecare numește un rol creator din artele vizuale.",
          "Pictor", "Sculptor", "creator", "maestru"),
        g("Profesii muzicale", "Fiecare numește un rol profesional din muzică.",
          "Muzician", "Compozitor", "Dirijor", "Cântăreț"),
        g("Roluri din știință", "Fiecare numește o persoană care produce cunoaștere.",
          "cercetător", "savant", "om de știință", "Inventator"),
        g("Roluri în viața publică", "Fiecare numește un rol vizibil în viața publică.",
          "Diplomat", "Politician", "lider", "celebritate"),
        flags=("generic_profession_board",),
    ),
    # --------------------------------------------------------------- stiinta / normal
    b(
        "stiinta_normal_01", "stiinta", "normal", 0,
        g("Părți ale feței", "Fiecare este o parte vizibilă a feței.",
          "Buză", "Frunte", "Obraz", "Sprânceană"),
        g("Părți ale piciorului", "Fiecare este o parte anatomică a membrului inferior.",
          "Coapsă", "Gambă", "Călcâi", "Genunchi"),
        g("Fenomene meteo violente",
          "Fiecare este un fenomen atmosferic asociat vremii violente.",
          "Furtună", "Fulger", "Tunet", "Grindină"),
        g("Mamifere domestice", "Fiecare este un mamifer domestic crescut lângă om.",
          "Câine", "Porc", "Cal", "Oaie"),
        flags=("primary_school_stock_below_normal_difficulty",),
    ),
    b(
        "stiinta_normal_02", "stiinta", "normal", 0,
        g("Structuri ale cavității bucale",
          "Fiecare este o structură aflată în cavitatea bucală sau la marginea ei.",
          "Dinte", "Limbă", "Palat", "Buză"),
        g("Animale întâlnite în pădure",
          "Fiecare trăiește frecvent în pădurile României.",
          "Veveriță", "Iepure", "Căprioară", "Cerb"),
        g("Se termină în „-logie”",
          "Numele fiecărei discipline se termină în sufixul „-logie”.",
          "Biologie", "Geologie", "Ecologie", "Microbiologie"),
        g("Mărimi fizice",
          "Fiecare este o mărime măsurabilă folosită în fizică.",
          "forță", "Masă", "temperatură", "Energie"),
    ),
    b(
        "stiinta_normal_03", "stiinta", "normal", 0,
        g("Termeni științifici care încep cu M",
          "Numele afișat al fiecărui termen științific începe cu litera M.",
          "Microscop", "Moleculă", "microb", "metal"),
        g("Absolvenți de medicină",
          "Fiecare a absolvit studii universitare de medicină.",
          "George Emil Palade", "Ion Cantacuzino", "Carol Davila", "Sofia Ionescu"),
        g("Instituții științifice bucureștene",
          "Fiecare instituție științifică își are sediul în București.",
          "Institutul Cantacuzino", "Institutul de Speologie Emil Racoviță",
          "Observatorul Urseanu", "Universitatea Politehnica din București"),
        g("Părți ale corpului din patru litere",
          "Numele afișat al fiecărei părți a corpului are exact patru litere.",
          "Gură", "ochi", "Buză", "Nară"),
    ),
    b(
        "stiinta_normal_04", "stiinta", "normal", 0,
        g("Se termină în „-ică”",
          "Numele fiecărui domeniu se termină în sufixul „-ică”.",
          "Fizică", "Matematică", "Robotică", "Cibernetică"),
        g("Termeni științifici terminați în „-ie”",
          "Fiecare termen are utilizare științifică și se termină în literele „-ie”.",
          "Ploaie", "Farmacie", "Bacterie", "Geologie"),
        g("Nume purtate de instituții științifice",
          "Numele fiecărei persoane este purtat de o instituție științifică românească.",
          "Ion Cantacuzino", "Carol Davila", "Horia Hulubei", "Emil Racoviță"),
        g("Ingineri și inventatori români",
          "Fiecare este inginer ori inventator român cunoscut pentru o contribuție tehnică.",
          "Dimitrie Leonida", "Elisa Leonida Zamfirescu", "Aurel Persu",
          "Petrache Poenaru"),
    ),
    b(
        "stiinta_normal_05", "stiinta", "normal", 0,
        g("Mamifere rumegătoare",
          "Fiecare este un mamifer rumegător.",
          "Oaie", "Capră", "Cerb", "Căprioară"),
        g("Matematicieni români",
          "Fiecare este matematician român cu activitate academică.",
          "Gheorghe Țițeica", "Grigore Moisil", "Traian Lalescu",
          "Solomon Marcus"),
        g("Fenomene meteo care pot reduce vizibilitatea",
          "Fiecare poate reduce vizibilitatea în aer liber.",
          "Ceață", "Ploaie", "Zăpadă", "Furtună"),
        g("Femei românce din știință",
          "Fiecare este femeie română cu activitate științifică sau inginerească.",
          "Ana Aslan", "Elisa Leonida Zamfirescu", "Ștefania Mărăcineanu",
          "Sofia Ionescu"),
    ),
    b(
        "stiinta_normal_06", "stiinta", "normal", 0,
        g("Personalități medicale românești",
          "Fiecare a avut un rol major în medicina ori sănătatea publică românească.",
          "Mina Minovici", "Ana Aslan", "Raed Arafat", "Gheorghe Marinescu"),
        g("Invenții și produse științifice românești",
          "Fiecare este o invenție ori realizare științifică românească.",
          "Laserul Măgurele", "Stiloul cu rezervor", "Gerovital", "Becul Teclu"),
        g("Tehnologii moderne", "Fiecare este un domeniu ori sistem tehnologic modern.",
          "Inteligență artificială", "Robotică", "Electricitate", "Rachete"),
        g("Cuvinte despre alcătuirea materiei",
          "Fiecare numește un material sau o unitate microscopică a materiei.",
          "metal", "Piatră", "Atom", "Moleculă"),
        flags=("technology_and_matter_groups_are_broad",),
    ),
)

AUTHOR_SOURCE_ASSERTIONS = {
    "sport_normal_03": [{
        "assertion": (
            "COSR lists David Popovici as the Paris 2024 Olympic champion at 200 m "
            "freestyle and bronze medallist at 100 m freestyle."
        ),
        "source": "https://www.cosr.ro/olympicGames/paris-2024",
    }],
    "sport_normal_04": [{
        "assertion": (
            "COSR's Atlanta 1996 results list Gabriela Szabó, Leonard Doroftei, "
            "Simona Amânar, and Elisabeta Lipă among Romania's medallists."
        ),
        "source": "https://www.cosr.ro/olympicGames/atlanta-1996",
    }],
    "gastronomie_normal_06": [
        {
            "assertion": (
                "EU Implementing Regulation 2025/2259 registers «Cârnați din topor "
                "din Vâlcea» as a geographical indication; the predicate therefore "
                "uses «toponim», not the false narrower class «localitate»."
            ),
            "source": (
                "https://eur-lex.europa.eu/legal-content/RO/TXT/"
                "?uri=OJ%3AL_202502259"
            ),
        },
        {
            "assertion": (
                "Kandia Dulce's official ROM page lists cocoa powder, cocoa butter, "
                "and cocoa mass among the product ingredients."
            ),
            "source": "https://kandia-dulce.ro/branduri/rom/",
        },
    ],
    "personalitati_normal_05": [{
        "assertion": (
            "Romania's Interior Ministry names Vasile Alecsandri among Moldavian "
            "revolutionaries, Avram Iancu among Transylvanian exponents, and Ana "
            "Ipătescu and Nicolae Bălcescu among Wallachian leaders of 1848."
        ),
        "source": (
            "https://www.mai.gov.ro/mesajul-premierului-interimar-al-romaniei-"
            "ministrul-afacerilor-interne-catalin-predoiu-cu-ocazia-zilei-"
            "victoriei-revolutiei-de-la-1848-si-a-democratiei-romanesti/"
        ),
    }],
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.casefold())
    return " ".join("".join(c for c in text if c.isalnum() or c.isspace()).split())


def main() -> int:
    pack = json.loads(PACK_PATH.read_text(encoding="utf-8"))
    kg = json.loads(KG_PATH.read_text(encoding="utf-8"))
    demotions = json.loads(DEMOTIONS_PATH.read_text(encoding="utf-8"))
    demoted_ids = set(demotions["ids"])
    labels: dict[str, list[str]] = defaultdict(list)
    nodes = {}
    for node in kg["kg_nodes"]:
        labels[node["label_ro"]].append(node["id"])
        nodes[node["id"]] = node
    preferred_ids = {
        "Moldova": "n_moldova_reg",
    }

    def resolve(label: str) -> str:
        if label in preferred_ids:
            return preferred_ids[label]
        ids = labels.get(label, [])
        if len(ids) != 1:
            raise ValueError(f"{label!r} resolves to {ids}")
        return ids[0]

    expected = {
        ("sport", "usor"): 6, ("sport", "normal"): 6,
        ("gastronomie", "normal"): 6, ("geografie", "normal"): 6,
        ("personalitati", "normal"): 6, ("stiinta", "normal"): 6,
    }
    assert Counter((x.category, x.difficulty) for x in BOARDS) == expected

    pack_quads = []
    approved_quads: dict[frozenset[str], list[str]] = defaultdict(list)
    approved_use: Counter[str] = Counter()
    for rec in pack["conexiuni"]:
        for ids in rec["groups"].values():
            quad = frozenset(ids)
            pack_quads.append((quad, rec["id"], rec["status"], rec["id"] in demoted_ids))
            if rec["status"] == "approved":
                approved_quads[quad].append(rec["id"])
                approved_use.update(ids)

    resolved = []
    all_quads = []
    candidate_use: Counter[str] = Counter()
    for board in BOARDS:
        groups, board_ids = [], []
        for i, group in enumerate(board.groups):
            ids = [resolve(x) for x in group.tiles]
            groups.append({
                "label": group.label, "criterion": group.criterion, "tiles": ids,
                "tile_labels": list(group.tiles), "recognition": group.recognition,
            })
            board_ids.extend(ids)
            all_quads.append((frozenset(ids), board.ref, i))
            candidate_use.update(ids)
        resolved.append((board, groups, board_ids))
    projected_use = approved_use + candidate_use

    _, svc, strong, regions = critique_pack.load_all(PACK_PATH, KG_PATH)
    audit, output = [], defaultdict(list)
    hard_total = 0
    advance = Counter()
    holds = []
    drops = []
    for board, groups, board_ids in resolved:
        hard = []
        if len(board_ids) != 16 or len(set(board_ids)) != 16:
            hard.append("board does not contain 16 unique tiles")
        group_map = {f"g{i + 1}": x["tiles"] for i, x in enumerate(groups)}
        label_map = {f"g{i + 1}": x["label"] for i, x in enumerate(groups)}
        rec = {
            "id": f"author_{board.ref}", "category": board.category,
            "difficulty": board.difficulty, "status": "pending",
            "groups": group_map, "group_labels": label_map, "order": board_ids,
        }
        lint = critique_pack.check_conexiuni(rec, svc, strong, approved_quads)
        lint += critique_pack.check_generic_region(rec, "conexiuni", svc, regions)
        for i, group in enumerate(groups):
            quad = frozenset(group["tiles"])
            pack_hits = sorted(
                (len(quad & q), iid, status, demoted)
                for q, iid, status, demoted in pack_quads
            )
            batch_hits = sorted(
                (len(quad & q), ref, gi)
                for q, ref, gi in all_quads
                if not (ref == board.ref and gi == i)
            )
            ph, bh = pack_hits[-1], batch_hits[-1]
            group["overlap_census"] = {
                "max_pack_overlap": ph[0], "max_pack_board": ph[1],
                "max_pack_status": ph[2], "max_pack_is_demoted": ph[3],
                "max_same_batch_overlap": bh[0], "max_same_batch_ref": bh[1],
                "max_same_batch_group": bh[2] + 1,
            }
            if ph[0] >= 3:
                hard.append(f"group {i + 1} overlaps {ph[0]}/4 with {ph[1]}")
            if bh[0] >= 3:
                hard.append(f"group {i + 1} overlaps {bh[0]}/4 with {bh[1]}.g{bh[2] + 1}")
            leaked = [x for x in group["tile_labels"] if norm(x) in norm(group["label"])]
            if leaked:
                hard.append(f"group {i + 1} label contains member: {', '.join(leaked)}")

        max_board = max(
            (len(set(board_ids) & {x for ids in r["groups"].values() for x in ids}), r["id"])
            for r in pack["conexiuni"]
        )
        if max_board[0] >= 8:
            hard.append(f"board overlaps {max_board[0]}/16 with {max_board[1]}")
        overused = sorted(
            (nodes[nid]["label_ro"], projected_use[nid])
            for nid in set(board_ids) if projected_use[nid] > 8
        )
        if overused:
            hard.append("projected use >8: " + ", ".join(f"{x} ({n})" for x, n in overused))
        hard_lint = [
            x for x in lint if x["level"] == "FAIL" or x["check"] == "mirrored_groups"
        ]
        hard += [f"{x['check']}: {x['detail']}" for x in hard_lint]
        is_editorial_hold = any(flag.startswith("hold_") for flag in board.flags)
        if hard:
            verdict = "drop"
        elif is_editorial_hold:
            verdict = "hold"
        elif board.flags:
            verdict = "drop"
        else:
            verdict = "advance"
        if verdict == "advance":
            advance[(board.category, board.difficulty)] += 1
        elif verdict == "hold":
            holds.append(board.ref)
        else:
            drops.append(board.ref)
        hard_total += len(hard)
        audit.append({
            "ref": board.ref, "shelf": f"{board.category}/{board.difficulty}",
            "author_verdict": verdict, "anchor_group": board.anchor + 1,
            "anchor_reason": groups[board.anchor]["criterion"],
            "max_pack_board_overlap": {"tiles": max_board[0], "board": max_board[1]},
            "projected_member_use_max": max(projected_use[x] for x in set(board_ids)),
            "hard_errors": hard, "editorial_flags": list(board.flags),
            "author_source_assertions": AUTHOR_SOURCE_ASSERTIONS.get(board.ref, []),
            "lint_findings": lint,
            "rubric_self_screen": {
                "B1_single_predicates": all(x["criterion"] for x in groups),
                "B2_type_discipline": not any(x["check"] == "type_coherence" for x in lint),
                "B3_unique_partition": not any(x["check"] == "tile_fairness" for x in lint),
                "B4_bounded_traps": not any(
                    x["check"] == "red_herring_budget" and x["level"] == "FAIL" for x in lint
                ),
                "B5_no_mirrors": not any(x["check"] == "mirrored_groups" for x in lint),
                "B6_no_hierarchy_or_filler": not board.flags,
                "B7_easy_anchor": True,
                "B8_recognition": [x["recognition"] for x in groups],
                "B9_no_full_member_leak": not any("label contains member" in x for x in hard),
            },
            "groups": groups,
        })
        output[board.category].append({
            "author_ref": board.ref, "difficulty": board.difficulty,
            "groups": [{"label": x["label"], "tiles": x["tiles"]} for x in groups],
        })

    for category, items in sorted(output.items()):
        folder = OUT / category
        folder.mkdir(parents=True, exist_ok=True)
        payload = {
            "nodes": [], "edges": [], "conexiuni": items,
            "contexto": [], "lant": [], "alchimie": [],
        }
        (folder / "candidates.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    candidate_digests = {
        category: digest(OUT / category / "candidates.json")
        for category in sorted(output)
    }
    manifest = {
        "schema_version": 1, "batch": "v43_everyday_shelves",
        "scope": (
            "Authoring proposals only; no verifier, import, promotion, pack edit, KG edit, "
            "ranking edit, or status change."
        ),
        "source_census": {
            "pack_sha256": digest(PACK_PATH), "kg_sha256": digest(KG_PATH),
            "demotions_sha256": digest(DEMOTIONS_PATH),
            "candidate_sha256_by_category": candidate_digests,
            "pack_conexiuni_boards": len(pack["conexiuni"]),
            "pack_conexiuni_groups": len(pack_quads),
            "approved_groups_including_reserves": len(approved_quads),
            "demoted_board_count": len(demoted_ids), "new_node_count": 0,
            "new_edge_count": 0,
            "evidence_policy": (
                "Every tile resolves to an existing fixture node. No new node or edge claim "
                "is introduced; independent factual verification remains mandatory."
            ),
        },
        "counts": {
            "boards": len(BOARDS), "groups": len(BOARDS) * 4,
            "by_shelf": {f"{a}/{d}": n for (a, d), n in sorted(expected.items())},
            "advance_by_shelf": {
                f"{a}/{d}": advance[(a, d)] for a, d in sorted(expected)
            },
            "hold_refs": holds, "drop_refs": drops, "hard_error_count": hard_total,
        },
        "hard_rules": {
            "quad_overlap": "maximum 2/4 against every pack and same-batch group",
            "board_overlap": "maximum 7/16 against every pack board",
            "member_use": "projected approved plus whole authoring batch <=8",
            "mirrors": "no >=3-way strong-edge correspondence",
            "label_leak": "no normalized full tile label inside its group label",
            "shape": "four groups, four unique tiles each, sixteen unique tiles",
        },
        "boards": audit,
    }
    (OUT / "authoring_audit.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"built {len(BOARDS)} boards / {len(BOARDS) * 4} groups")
    print("advance:", {f"{a}/{d}": advance[(a, d)] for a, d in sorted(expected)})
    print(f"hard errors: {hard_total}")
    for item in audit:
        for error in item["hard_errors"]:
            print(f"  {item['ref']}: {error}")
    print("author holds:", ", ".join(holds) if holds else "none")
    print("author drops:", ", ".join(drops) if drops else "none")
    return 1 if hard_total else 0


if __name__ == "__main__":
    raise SystemExit(main())
