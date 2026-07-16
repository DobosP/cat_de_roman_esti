"""Deterministic source data for the v24 beginner-vocabulary graph wave.

This module is intentionally side-effect free.  ``apply_common_words_v24.py`` consumes
the plain constants and :func:`build_nodes_and_edges`; importing it never reads or writes
the bundled fixture.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

BUILD_VERSION = "fixture-v24-common-words"
NOTE = (
    "v24: beginner everyday Romanian vocabulary with inflection aliases, two semantic "
    "anchors per concept, meaningful local links, and a reproducible 236-surface probe."
)


@dataclass(frozen=True, slots=True)
class ConceptSpec:
    """One new playable concept and the existing graph anchors that explain it."""

    node_id: str
    label: str
    category: str
    salience: float
    description: str
    aliases: tuple[str, ...]
    anchors: tuple[str, str]


@dataclass(frozen=True, slots=True)
class TriadSpec:
    """Three closely related concepts; the builder closes each triad into a triangle."""

    relation: str
    label_ro: str
    members: tuple[ConceptSpec, ConceptSpec, ConceptSpec]


@dataclass(frozen=True, slots=True)
class RecipeSpec:
    """A bounded directed Alchimie recipe: both inputs point to one result."""

    left: str
    right: str
    result: str
    label_ro: str


@dataclass(frozen=True, slots=True)
class DirectedPairSpec:
    """One human-audited direct association used by beginner probes and routes."""

    source: str
    target: str
    source_label: str
    target_label: str


@dataclass(frozen=True, slots=True)
class DiamondSpec:
    """Two equal two-hop routes from one familiar start to one common target."""

    start: str
    left: str
    right: str
    target: str
    label_ro: str


def _norm(surface: str) -> str:
    decomposed = unicodedata.normalize("NFKD", surface)
    no_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(no_accents.casefold().split())


def _clean_aliases(label: str, aliases: tuple[str, ...]) -> tuple[str, ...]:
    """Drop only resolver-redundant spellings; retain real inflections deterministically."""

    seen = {_norm(label)}
    cleaned: list[str] = []
    for alias in aliases:
        key = _norm(alias)
        if key and key not in seen:
            cleaned.append(alias)
            seen.add(key)
    return tuple(cleaned)


def _triad(
    key: str,
    *,
    category: str,
    salience: float,
    group: str,
    anchors: tuple[str, str],
    relation: str,
    rows: tuple[
        tuple[str, str, tuple[str, ...]],
        tuple[str, str, tuple[str, ...]],
        tuple[str, str, tuple[str, ...]],
    ],
) -> TriadSpec:
    """Keep the source compact while retaining explicit labels, aliases and anchors."""

    members = tuple(
        ConceptSpec(
            node_id=f"n_v24_{key}_{slug}",
            label=label,
            category=category,
            salience=salience,
            description=f"Concept cotidian din grupul «{group}»: {label}.",
            aliases=_clean_aliases(label, aliases),
            anchors=anchors,
        )
        for slug, label, aliases in rows
    )
    return TriadSpec(
        relation=relation,
        label_ro=group,
        members=(members[0], members[1], members[2]),
    )


# The benchmark is grouped so its intended audience and exact domain balance stay visible.
BEGINNER_BENCHMARK_BY_DOMAIN: dict[str, tuple[str, ...]] = {
    "food": (
        "mâncare", "pâine", "lapte", "apă", "carne", "ou", "brânză", "orez",
        "supă", "ciorbă", "sare", "zahăr", "făină", "ulei", "unt", "cafea", "ceai",
        "măr", "pară", "prună", "cireașă", "căpșună", "strugure", "pepene", "caisă",
        "piersică", "banană", "portocală", "lămâie", "morcov", "cartof", "ceapă",
        "usturoi", "roșie", "ardei", "varză", "castravete", "salată", "fasole",
        "mazăre", "dovleac", "ridiche", "biscuit", "sandviș", "conopidă", "spanac",
        "iaurt", "mămăligă", "plăcintă", "miere",
    ),
    "home": (
        "casă", "cameră", "bucătărie", "baie", "sufragerie", "dormitor", "balcon",
        "curte", "grădină", "acoperiș", "perete", "podea", "tavan", "comodă cu sertare", "ușă",
        "fereastră", "dulap", "raft", "pat", "saltea", "pernă", "pătură", "cearșaf",
        "scaun", "covor", "canapea", "fotoliu", "lampă", "oglindă",
        "frigider", "aragaz",
    ),
    "people_body": (
        "om", "persoană", "femeie", "bărbat", "copil", "bebeluș", "familie", "mamă",
        "tată", "părinte", "fiu", "fiică", "frate", "soră", "bunică", "bunic", "soț",
        "soție", "unchi", "mătușă", "nepot", "prieten", "vecin", "corp", "cap", "ochi",
        "ureche", "nas", "gură", "dinte", "mână", "deget", "picior", "inimă",
    ),
    "nature": (
        "natură", "copac", "floare", "iarbă", "pădure", "munte", "deal", "câmp", "râu",
        "lac", "pământ", "cer", "soare", "lună", "stea", "ploaie", "zăpadă", "vânt",
        "nor", "furtună", "ceață", "fulger", "tunet", "grindină", "curcubeu", "izvor",
        "cascadă", "peșteră", "insulă", "plajă", "nisip", "piatră", "frunză", "ramură",
        "rădăcină",
    ),
    "transport_places": (
        "mașină", "autobuz", "tren", "tramvai", "metrou", "bicicletă", "motocicletă",
        "camion", "microbuz", "trotinetă", "avion", "vapor", "gară", "aeroport", "stație",
        "stradă", "drum", "dubă", "parc", "magazin", "spital", "farmacie", "bibliotecă",
        "restaurant",
    ),
    "school_work_time": (
        "școală", "elev", "profesor", "clasă școlară", "carte", "caiet", "creion", "pix",
        "stilou", "tablă școlară", "bancă școlară", "ghiozdan", "riglă", "radieră",
        "lecție", "temă pentru acasă", "examen", "catalog școlar", "birou", "serviciu",
        "meserie", "salariu", "ceas", "oră", "zi", "săptămână", "lună calendaristică",
        "an",
    ),
    "actions_feelings": (
        "a mânca", "a bea", "a merge", "a veni", "a vedea", "a auzi", "a spune",
        "a vorbi", "a citi", "a scrie", "a dormi", "a lucra", "a învăța", "a se juca",
        "a găti", "a spăla", "a deschide", "a închide", "a iubi", "a râde", "bucurie",
        "tristețe", "frică", "furie", "surpriză", "rușine", "mândrie", "speranță",
        "iubire", "dor", "liniște", "oboseală", "foame", "sete",
    ),
}

BEGINNER_BENCHMARK: tuple[str, ...] = tuple(
    surface
    for domain in BEGINNER_BENCHMARK_BY_DOMAIN.values()
    for surface in domain
)

# These high-frequency strings are useful probes, but a bare label cannot select one
# intended sense reliably.  They remain visible here so later waves do not silently add
# the wrong adjective/noun/verb meaning.
DEFERRED_AMBIGUOUS_TERMS: tuple[str, ...] = (
    "mare", "rău", "rapid", "masă", "bancă", "temă", "par", "vinete",
    # Current resolver collisions with an unrelated label/alias are kept explicit:
    # Persoană gramaticală, FC Barcelona/„Barça”, and the song „Taxi”.
    "persoană", "barcă", "taxi",
)


TRIADS: tuple[TriadSpec, ...] = (
    _triad(
        "food_pantry",
        category="gastronomie",
        salience=0.88,
        group="ingrediente de bază",
        anchors=("n_v4gas_mancare", "n_v4soc_casa"),
        relation="used_together",
        rows=(
            ("zahar", "Zahăr", ("zahărul", "zahărului")),
            ("faina", "Făină", ("făina", "făinii")),
            ("ulei", "Ulei", ("uleiul", "uleiuri")),
        ),
    ),
    _triad(
        "food_breakfast",
        category="gastronomie",
        salience=0.88,
        group="alimente pentru micul dejun",
        anchors=("n_v4gas_mancare", "n_v4soc_casa"),
        relation="served_together",
        rows=(
            ("unt", "Unt", ("untul", "untului")),
            ("iaurt", "Iaurt", ("iaurtul", "iaurturi")),
            ("miere", "Miere", ("mierea", "mierii")),
        ),
    ),
    _triad(
        "food_orchard",
        category="gastronomie",
        salience=0.91,
        group="fructe de livadă",
        anchors=("n_v4gas_fruct", "n_v4sti_planta"),
        relation="same_kind",
        rows=(
            ("mar", "Măr", ("mărul", "mere")),
            ("para", "Pară", ("para", "pere")),
            ("pruna", "Prună", ("pruna", "prune")),
        ),
    ),
    _triad(
        "food_small_fruit",
        category="gastronomie",
        salience=0.86,
        group="fructe mici",
        anchors=("n_v4gas_fruct", "n_v4sti_planta"),
        relation="same_kind",
        rows=(
            ("cireasa", "Cireașă", ("cireașa", "cireșe")),
            ("capsuna", "Căpșună", ("căpșuna", "căpșuni")),
            ("strugure", "Strugure", ("strugurele", "struguri")),
        ),
    ),
    _triad(
        "food_summer_fruit",
        category="gastronomie",
        salience=0.85,
        group="fructe de vară",
        anchors=("n_v4gas_fruct", "n_v4sti_planta"),
        relation="same_kind",
        rows=(
            ("pepene", "Pepene", ("pepenele", "pepeni")),
            ("caisa", "Caisă", ("caisa", "caise")),
            ("piersica", "Piersică", ("piersica", "piersici")),
        ),
    ),
    _triad(
        "food_imported_fruit",
        category="gastronomie",
        salience=0.88,
        group="fructe din magazin",
        anchors=("n_v4gas_fruct", "n_v4sti_planta"),
        relation="same_kind",
        rows=(
            ("banana", "Banană", ("banana", "banane")),
            ("portocala", "Portocală", ("portocala", "portocale")),
            ("lamaie", "Lămâie", ("lămâia", "lămâi")),
        ),
    ),
    _triad(
        "food_salad_veg",
        category="gastronomie",
        salience=0.91,
        group="legume pentru salată",
        anchors=("n_v4gas_mancare", "n_v4sti_planta"),
        relation="used_together",
        rows=(
            ("morcov", "Morcov", ("morcovul", "morcovi")),
            ("ardei", "Ardei", ("ardeiul", "ardeiului")),
            ("castravete", "Castravete", ("castravetele", "castraveți")),
        ),
    ),
    _triad(
        "food_garden_veg",
        category="gastronomie",
        salience=0.84,
        group="legume de grădină",
        anchors=("n_v4gas_legume", "n_v4sti_planta"),
        relation="same_kind",
        rows=(
            ("mazare", "Mazăre", ("mazărea", "mazării")),
            ("dovleac", "Dovleac", ("dovleacul", "dovleci")),
            ("ridiche", "Ridiche", ("ridichea", "ridichi")),
        ),
    ),
    _triad(
        "food_snack",
        category="gastronomie",
        salience=0.87,
        group="gustare simplă",
        anchors=("n_v4gas_mancare", "n_v4soc_casa"),
        relation="served_together",
        rows=(
            ("ceai", "Ceai", ("ceaiul", "ceaiuri")),
            ("biscuit", "Biscuit", ("biscuitul", "biscuiți")),
            ("sandvis", "Sandviș", ("sandvișul", "sandvișuri")),
        ),
    ),
    _triad(
        "home_rooms",
        category="viata_de_roman",
        salience=0.91,
        group="camere ale locuinței",
        anchors=("n_v4via_usa", "n_v4soc_casa"),
        relation="part_of_same_home",
        rows=(
            ("camera", "Cameră", ("camera", "camere")),
            ("sufragerie", "Sufragerie", ("sufrageria", "sufragerii")),
            ("dormitor", "Dormitor", ("dormitorul", "dormitoare")),
        ),
    ),
    _triad(
        "home_outdoor",
        category="viata_de_roman",
        salience=0.86,
        group="spații de lângă casă",
        anchors=("n_v4via_usa", "n_v4sti_planta"),
        relation="part_of_same_home",
        rows=(
            ("balcon", "Balcon", ("balconul", "balcoane")),
            ("curte", "Curte", ("curtea", "curți")),
            ("gradina", "Grădină", ("grădina", "grădini")),
        ),
    ),
    _triad(
        "home_structure",
        category="viata_de_roman",
        salience=0.84,
        group="părți ale casei",
        anchors=("n_v4via_usa", "n_v4soc_casa"),
        relation="part_of_same_home",
        rows=(
            ("acoperis", "Acoperiș", ("acoperișul", "acoperișuri")),
            ("perete", "Perete", ("peretele", "pereți")),
            ("tavan", "Tavan", ("tavanul", "tavane")),
        ),
    ),
    _triad(
        "home_surfaces",
        category="viata_de_roman",
        salience=0.84,
        group="suprafețe și deschideri",
        anchors=("n_v4via_usa", "n_v4soc_casa"),
        relation="part_of_same_home",
        rows=(
            ("podea", "Podea", ("podeaua", "podele")),
            ("fereastra", "Fereastră", ("fereastra", "ferestre")),
            ("oglinda", "Oglindă", ("oglinda", "oglinzi")),
        ),
    ),
    _triad(
        "home_storage",
        category="viata_de_roman",
        salience=0.82,
        group="mobilier pentru depozitare",
        anchors=("n_v4via_usa", "n_v4soc_casa"),
        relation="used_together",
        rows=(
            ("dulap", "Dulap", ("dulapul", "dulapuri")),
            ("raft", "Raft", ("raftul", "rafturi")),
            (
                "comoda_sertare",
                "Comodă cu sertare",
                ("comoda cu sertare", "comode cu sertare"),
            ),
        ),
    ),
    _triad(
        "home_bed",
        category="viata_de_roman",
        salience=0.91,
        group="obiecte pentru somn",
        anchors=("n_v4via_usa", "n_v4soc_casa"),
        relation="used_together",
        rows=(
            ("pat", "Pat", ("patul", "patului")),
            ("saltea", "Saltea", ("salteaua", "saltele")),
            ("perna", "Pernă", ("perna", "perne")),
        ),
    ),
    _triad(
        "home_textiles",
        category="viata_de_roman",
        salience=0.84,
        group="textile din casă",
        anchors=("n_v4via_usa", "n_v4soc_casa"),
        relation="used_together",
        rows=(
            ("patura", "Pătură", ("pături", "păturii")),
            ("cearsaf", "Cearșaf", ("cearșaful", "cearșafuri")),
            ("covor", "Covor", ("covorul", "covoare")),
        ),
    ),
    _triad(
        "home_seating",
        category="viata_de_roman",
        salience=0.88,
        group="mobilier pentru șezut",
        anchors=("n_v4via_usa", "n_v4soc_casa"),
        relation="same_kind",
        rows=(
            ("scaun", "Scaun", ("scaunul", "scaune")),
            ("canapea", "Canapea", ("canapeaua", "canapele")),
            ("fotoliu", "Fotoliu", ("fotoliul", "fotolii")),
        ),
    ),
    _triad(
        "home_appliances",
        category="viata_de_roman",
        salience=0.9,
        group="obiecte utile în casă",
        anchors=("n_v4via_usa", "n_v4gas_bucatarie"),
        relation="found_in_same_home",
        rows=(
            ("lampa", "Lampă", ("lampa", "lămpi")),
            ("frigider", "Frigider", ("frigiderul", "frigidere")),
            ("aragaz", "Aragaz", ("aragazul", "aragazuri")),
        ),
    ),
    _triad(
        "people_parents",
        category="societate",
        salience=0.94,
        group="părinți și copii mici",
        anchors=("n_v4soc_familie", "n_v4per_om"),
        relation="family_relation",
        rows=(
            ("mama", "Mamă", ("mama", "mame")),
            ("tata", "Tată", ("tatăl", "tați")),
            ("bebelus", "Bebeluș", ("bebelușul", "bebeluși")),
        ),
    ),
    _triad(
        "people_descendants",
        category="societate",
        salience=0.91,
        group="copii și nepoți",
        anchors=("n_v4soc_familie", "n_v4per_om"),
        relation="family_relation",
        rows=(
            ("fiu", "Fiu", ("fiul", "fii")),
            ("fiica", "Fiică", ("fiica", "fiice")),
            ("nepot", "Nepot", ("nepotul", "nepoți")),
        ),
    ),
    _triad(
        "people_relatives",
        category="societate",
        salience=0.9,
        group="rude apropiate",
        anchors=("n_v4soc_familie", "n_v4per_om"),
        relation="family_relation",
        rows=(
            ("frate", "Frate", ("fratele", "frați")),
            ("sora", "Soră", ("sora", "surori")),
            ("unchi", "Unchi", ("unchiul", "unchiului")),
        ),
    ),
    _triad(
        "people_grandparents",
        category="societate",
        salience=0.9,
        group="bunici și mătuși",
        anchors=("n_v4soc_familie", "n_v4per_om"),
        relation="family_relation",
        rows=(
            ("bunica", "Bunică", ("bunica", "bunicile")),
            ("bunic", "Bunic", ("bunicul", "bunicului")),
            ("matusa", "Mătușă", ("mătușa", "mătuși")),
        ),
    ),
    _triad(
        "people_relationships",
        category="societate",
        salience=0.9,
        group="relații apropiate",
        anchors=("n_v4soc_familie", "n_v4per_om"),
        relation="close_relationship",
        rows=(
            ("sot", "Soț", ("soțul", "soțului")),
            ("sotie", "Soție", ("soția", "soțiile")),
            ("prieten", "Prieten", ("prietenul", "prieteni")),
        ),
    ),
    _triad(
        "body_face",
        category="stiinta",
        salience=0.93,
        group="părți ale capului",
        anchors=("n_v4sti_corp", "n_v4per_om"),
        relation="part_of_body",
        rows=(
            ("cap", "Cap", ("capul", "capete")),
            ("nas", "Nas", ("nasul", "nasuri")),
            ("gura", "Gură", ("gura", "guri")),
        ),
    ),
    _triad(
        "body_limbs",
        category="stiinta",
        salience=0.93,
        group="părți ale membrelor",
        anchors=("n_v4sti_corp", "n_v4per_om"),
        relation="part_of_body",
        rows=(
            ("mana", "Mână", ("mâna", "mâini")),
            ("deget", "Deget", ("degetul", "degete")),
            ("picior", "Picior", ("piciorul", "picioare")),
        ),
    ),
    _triad(
        "nature_plant_parts",
        category="stiinta",
        salience=0.86,
        group="plante și părțile lor",
        anchors=("n_v4sti_planta", "n_v4geo_padure"),
        relation="part_of_plant",
        rows=(
            ("iarba", "Iarbă", ("iarba", "ierburi")),
            ("ramura", "Ramură", ("ramura", "ramuri")),
            ("radacina", "Rădăcină", ("rădăcina", "rădăcini")),
        ),
    ),
    _triad(
        "nature_world",
        category="stiinta",
        salience=0.9,
        group="lumea naturală",
        anchors=("n_v4sti_aer", "n_v2geo_munte"),
        relation="part_of_nature",
        rows=(
            ("natura", "Natură", ("natura", "naturii")),
            ("pamant", "Pământ", ("pământul", "pământului")),
            ("cer", "Cer", ("cerul", "ceruri")),
        ),
    ),
    _triad(
        "nature_sky",
        category="stiinta",
        salience=0.94,
        group="corpuri văzute pe cer",
        anchors=("n_v4sti_aer", "n_v2geo_munte"),
        relation="seen_in_sky",
        rows=(
            ("soare", "Soare", ("soarele", "soarelui")),
            ("luna", "Lună", ("luna", "lunii")),
            ("stea", "Stea", ("steaua", "stele")),
        ),
    ),
    _triad(
        "weather_precipitation",
        category="stiinta",
        salience=0.91,
        group="precipitații",
        anchors=("n_v4sti_aer", "n_v4gas_apa"),
        relation="weather_phenomenon",
        rows=(
            ("ploaie", "Ploaie", ("ploi", "ploile")),
            ("zapada", "Zăpadă", ("zăpada", "zăpezi")),
            ("grindina", "Grindină", ("grindina", "grindinii")),
        ),
    ),
    _triad(
        "weather_air",
        category="stiinta",
        salience=0.88,
        group="vreme în atmosferă",
        anchors=("n_v4sti_aer", "n_v2geo_munte"),
        relation="weather_phenomenon",
        rows=(
            ("vant", "Vânt", ("vântul", "vânturi")),
            ("nor", "Nor", ("norul", "nori")),
            ("ceata", "Ceață", ("ceața", "cețuri")),
        ),
    ),
    _triad(
        "weather_storm",
        category="stiinta",
        salience=0.88,
        group="fenomene de furtună",
        anchors=("n_v4sti_aer", "n_v2geo_munte"),
        relation="storm_phenomenon",
        rows=(
            ("furtuna", "Furtună", ("furtuna", "furtuni")),
            ("fulger", "Fulger", ("fulgerul", "fulgere")),
            ("tunet", "Tunet", ("tunetul", "tunete")),
        ),
    ),
    _triad(
        "transport_rail",
        category="societate",
        salience=0.94,
        group="transport pe șine",
        anchors=("n_v4soc_autobuz", "n_v4geo_drum"),
        relation="same_transport_kind",
        rows=(
            ("tren", "Tren", ("trenul", "trenuri")),
            ("tramvai", "Tramvai", ("tramvaiul", "tramvaie")),
            ("metrou", "Metrou", ("metrouri",)),
        ),
    ),
    _triad(
        "transport_personal",
        category="societate",
        salience=0.94,
        group="transport personal",
        anchors=("n_v4soc_autobuz", "n_v4geo_drum"),
        relation="same_transport_kind",
        rows=(
            ("masina", "Mașină", ("mașina", "mașini")),
            ("bicicleta", "Bicicletă", ("bicicleta", "biciclete")),
            ("motocicleta", "Motocicletă", ("motocicleta", "motociclete")),
        ),
    ),
    _triad(
        "transport_road",
        category="societate",
        salience=0.88,
        group="vehicule rutiere",
        anchors=("n_v4soc_autobuz", "n_v4geo_drum"),
        relation="same_transport_kind",
        rows=(
            ("camion", "Camion", ("camionul", "camioane")),
            ("microbuz", "Microbuz", ("microbuzul", "microbuze")),
            ("duba", "Dubă", ("dube", "dubele")),
        ),
    ),
    _triad(
        "transport_terminals",
        category="societate",
        salience=0.9,
        group="puncte de plecare și sosire",
        anchors=("n_v4soc_autobuz", "n_v2sti_avion"),
        relation="travel_place",
        rows=(
            ("gara", "Gară", ("gara", "gări")),
            ("aeroport", "Aeroport", ("aeroportul", "aeroporturi")),
            ("statie", "Stație", ("stația", "stații")),
        ),
    ),
    _triad(
        "places_public",
        category="societate",
        salience=0.91,
        group="locuri publice cotidiene",
        anchors=("n_v4soc_magazin", "n_v4geo_strada"),
        relation="public_place",
        rows=(
            ("parc", "Parc", ("parcul", "parcuri")),
            ("farmacie", "Farmacie", ("farmacia", "farmacii")),
            ("restaurant", "Restaurant", ("restaurantul", "restaurante")),
        ),
    ),
    _triad(
        "school_writing",
        category="viata_de_roman",
        salience=0.94,
        group="obiecte pentru scris",
        anchors=("n_v23via_ghiozdan", "n_v3lit_carte"),
        relation="used_together_at_school",
        rows=(
            ("caiet", "Caiet", ("caietul", "caiete")),
            ("creion", "Creion", ("creionul", "creioane")),
            ("pix", "Pix", ("pixul", "pixuri")),
        ),
    ),
    _triad(
        "school_supplies",
        category="viata_de_roman",
        salience=0.91,
        group="rechizite școlare",
        anchors=("n_v23via_ghiozdan", "n_v3soc_scoala"),
        relation="used_together_at_school",
        rows=(
            ("stilou", "Stilou", ("stiloul", "stilouri")),
            ("rigla", "Riglă", ("rigla", "rigle")),
            ("radiera", "Radieră", ("radiera", "radiere")),
        ),
    ),
    _triad(
        "school_classroom",
        category="viata_de_roman",
        salience=0.93,
        group="sala de clasă",
        anchors=("n_v23via_tabla_scolara", "n_v3soc_scoala"),
        relation="found_in_classroom",
        rows=(
            ("clasa_scolara", "Clasă școlară", ("clasa școlară", "clase școlare")),
            (
                "banca_scolara",
                "Bancă școlară",
                ("banca școlară", "bănci școlare"),
            ),
            ("lectie", "Lecție", ("lecția", "lecții")),
        ),
    ),
    _triad(
        "school_assessment",
        category="viata_de_roman",
        salience=0.88,
        group="activități de evaluare",
        anchors=("n_v23via_tabla_scolara", "n_v4per_profesor"),
        relation="school_activity",
        rows=(
            (
                "tema_acasa",
                "Temă pentru acasă",
                ("tema pentru acasă", "teme pentru acasă"),
            ),
            ("examen", "Examen", ("examenul", "examene")),
            (
                "catalog_scolar",
                "Catalog școlar",
                ("catalogul școlar", "cataloage școlare"),
            ),
        ),
    ),
    _triad(
        "time_day",
        category="societate",
        salience=0.94,
        group="măsurarea timpului zilnic",
        anchors=("n_v4soc_serviciu", "n_v4ist_an"),
        relation="time_unit",
        rows=(
            ("ceas", "Ceas", ("ceasul", "ceasuri")),
            ("ora", "Oră", ("ora", "ore")),
            ("zi", "Zi", ("ziua", "zile")),
        ),
    ),
    _triad(
        "action_food",
        category="viata_de_roman",
        salience=0.94,
        group="acțiuni legate de mâncare",
        anchors=("n_v4via_baie", "n_v4gas_mancare"),
        relation="everyday_action",
        rows=(
            ("a_manca", "A mânca", ("mănânc", "mănâncă", "mâncăm")),
            ("a_bea", "A bea", ("beau", "bea", "bem")),
            ("a_gati", "A găti", ("gătesc", "gătește", "gătim")),
        ),
    ),
    _triad(
        "action_movement",
        category="viata_de_roman",
        salience=0.94,
        group="mișcare și joacă",
        anchors=("n_v4via_usa", "n_v4geo_drum"),
        relation="everyday_action",
        rows=(
            ("a_merge", "A merge", ("merg", "merge", "mergem")),
            ("a_veni", "A veni", ("vine", "venim", "veniți")),
            ("a_se_juca", "A se juca", ("se joacă", "mă joc", "ne jucăm")),
        ),
    ),
    _triad(
        "action_senses",
        category="viata_de_roman",
        salience=0.94,
        group="simțuri și comunicare",
        anchors=("n_v4via_baie", "n_v4sti_corp"),
        relation="human_action",
        rows=(
            ("a_vedea", "A vedea", ("văd", "vede", "vedem")),
            ("a_auzi", "A auzi", ("aud", "aude", "auzim")),
            ("a_vorbi", "A vorbi", ("vorbesc", "vorbește", "vorbim")),
        ),
    ),
    _triad(
        "action_language",
        category="limba",
        salience=0.94,
        group="folosirea limbii scrise",
        anchors=("n_v3lim_limba", "n_v3lit_carte"),
        relation="language_action",
        rows=(
            ("a_spune", "A spune", ("spun", "spune", "spunem")),
            ("a_citi", "A citi", ("citesc", "citește", "citim")),
            ("a_scrie", "A scrie", ("scriu", "scrie", "scriem")),
        ),
    ),
    _triad(
        "action_routine",
        category="viata_de_roman",
        salience=0.93,
        group="rutina zilnică",
        anchors=("n_v4via_usa", "n_v4soc_serviciu"),
        relation="daily_routine",
        rows=(
            ("a_dormi", "A dormi", ("dorm", "doarme", "dormim")),
            ("a_lucra", "A lucra", ("lucrez", "lucrează", "lucrăm")),
            ("a_invata", "A învăța", ("învăț", "învață", "învățăm")),
        ),
    ),
    _triad(
        "action_home",
        category="viata_de_roman",
        salience=0.91,
        group="acțiuni prin casă",
        anchors=("n_v4via_baie", "n_v4soc_casa"),
        relation="home_action",
        rows=(
            ("a_spala", "A spăla", ("spăl", "spală", "spălăm")),
            ("a_deschide", "A deschide", ("deschid", "deschide", "deschidem")),
            ("a_inchide", "A închide", ("închid", "închide", "închidem")),
        ),
    ),
    _triad(
        "feeling_joy",
        category="societate",
        salience=0.93,
        group="afecțiune și bucurie",
        anchors=("n_v4soc_familie", "n_lbax_dor"),
        relation="positive_feeling",
        rows=(
            ("a_iubi", "A iubi", ("iubesc", "iubește", "iubim")),
            ("a_rade", "A râde", ("râd", "râde", "râdem")),
            ("bucurie", "Bucurie", ("bucuria", "bucurii")),
        ),
    ),
    _triad(
        "feeling_difficult",
        category="societate",
        salience=0.91,
        group="emoții dificile",
        anchors=("n_v4soc_familie", "n_lbax_dor"),
        relation="human_feeling",
        rows=(
            ("tristete", "Tristețe", ("tristețea", "tristeți")),
            ("frica", "Frică", ("frica", "frici")),
            ("furie", "Furie", ("furia", "furii")),
        ),
    ),
    _triad(
        "feeling_needs",
        category="societate",
        salience=0.93,
        group="stări și nevoi ale corpului",
        anchors=("n_v4soc_familie", "n_v4sti_corp"),
        relation="body_state",
        rows=(
            ("oboseala", "Oboseală", ("oboseala", "oboseli")),
            ("foame", "Foame", ("foamea", "îmi este foame")),
            ("sete", "Sete", ("setea", "îmi este sete")),
        ),
    ),
)
CONCEPTS: tuple[ConceptSpec, ...] = tuple(
    member for triad in TRIADS for member in triad.members
)
NEW_NODE_IDS: tuple[str, ...] = tuple(concept.node_id for concept in CONCEPTS)

# Controlled, category-local recipes make the home/school shelf deepen over two to four
# sensible crafts without exposing the dense legacy category as a shared result hub.
RECIPES: tuple[RecipeSpec, ...] = (
    RecipeSpec(
        "n_v24_home_rooms_camera",
        "n_v24_home_bed_pat",
        "n_v24_home_rooms_dormitor",
        "formează un dormitor",
    ),
    RecipeSpec(
        "n_v24_home_rooms_dormitor",
        "n_v24_home_bed_pat",
        "n_v24_home_bed_perna",
        "completează locul de dormit",
    ),
    RecipeSpec(
        "n_v24_home_bed_perna",
        "n_v24_home_seating_scaun",
        "n_v24_home_seating_fotoliu",
        "devine un scaun confortabil",
    ),
    RecipeSpec(
        "n_v24_home_bed_perna",
        "n_v24_home_surfaces_podea",
        "n_v24_home_textiles_covor",
        "aleg textile pentru cameră",
    ),
    RecipeSpec(
        "n_v24_home_seating_fotoliu",
        "n_v24_home_appliances_lampa",
        "n_v24_home_rooms_sufragerie",
        "formează un colț de sufragerie",
    ),
    RecipeSpec(
        "n_v24_home_textiles_patura",
        "n_v24_home_surfaces_podea",
        "n_v24_home_textiles_covor",
        "acoperă podeaua",
    ),
    RecipeSpec(
        "n_v24_home_seating_canapea",
        "n_v24_home_appliances_lampa",
        "n_v24_home_rooms_sufragerie",
        "amenajează sufrageria",
    ),
    RecipeSpec(
        "n_v24_action_movement_a_se_juca",
        "n_v24_home_outdoor_curte",
        "n_v24_home_outdoor_gradina",
        "joacă în grădină",
    ),
    RecipeSpec(
        "n_v24_action_food_a_gati",
        "n_v24_home_appliances_frigider",
        "n_v24_home_appliances_aragaz",
        "gătit în bucătărie",
    ),
    RecipeSpec(
        "n_v24_action_routine_a_dormi",
        "n_v24_home_bed_pat",
        "n_v24_home_rooms_dormitor",
        "somn în dormitor",
    ),
    RecipeSpec(
        "n_v24_action_home_a_spala",
        "n_v24_home_textiles_cearsaf",
        "n_v24_home_textiles_patura",
        "textile de spălat",
    ),
    RecipeSpec(
        "n_v24_school_writing_caiet",
        "n_v24_school_writing_creion",
        "n_v24_school_assessment_tema_acasa",
        "scriu tema",
    ),
    RecipeSpec(
        "n_v24_action_routine_a_invata",
        "n_v24_school_classroom_lectie",
        "n_v24_school_assessment_tema_acasa",
        "învăț din lecție",
    ),
    RecipeSpec(
        "n_v24_school_assessment_tema_acasa",
        "n_v24_school_classroom_lectie",
        "n_v24_school_assessment_examen",
        "pregătesc examenul",
    ),
    RecipeSpec(
        "n_v24_school_assessment_examen",
        "n_v24_school_classroom_clasa_scolara",
        "n_v24_school_assessment_catalog_scolar",
        "rezultatul intră în catalog",
    ),
    RecipeSpec(
        "n_v24_school_writing_caiet",
        "n_v24_school_supplies_stilou",
        "n_v24_school_classroom_lectie",
        "notez lecția",
    ),
)

# Direct repairs are deliberately one-way: familiar hubs reveal obvious neighbors while
# the reverse direction does not reopen a dense legacy category during recipe closure.
INTUITIVE_REPAIRS: tuple[DirectedPairSpec, ...] = (
    DirectedPairSpec("n_v4gas_mancare", "n_v4gas_paine", "Mâncare", "Pâine"),
    DirectedPairSpec("n_v4gas_mancare", "n_v4gas_lapte", "Mâncare", "Lapte"),
    DirectedPairSpec("n_v4gas_mancare", "n_v4gas_apa", "Mâncare", "Apă"),
    DirectedPairSpec("n_v4gas_mancare", "n_v4gas_carne", "Mâncare", "Carne"),
    DirectedPairSpec("n_v4gas_mancare", "n_v4gas_ou", "Mâncare", "Ou"),
    DirectedPairSpec("n_v4gas_mancare", "n_v2gas_branza", "Mâncare", "Brânză"),
    DirectedPairSpec("n_v4gas_mancare", "n_v3gas_orez", "Mâncare", "Orez"),
    DirectedPairSpec("n_v4gas_mancare", "n_v4gas_supa", "Mâncare", "Supă"),
    DirectedPairSpec("n_v4gas_mancare", "n_v2gas_ciorba", "Mâncare", "Ciorbă"),
    DirectedPairSpec("n_v4gas_mancare", "n_v4gas_sare", "Mâncare", "Sare"),
    DirectedPairSpec("n_v4gas_mancare", "n_v4gas_legume", "Mâncare", "Legume"),
    DirectedPairSpec("n_v4gas_mancare", "n_v4gas_fruct", "Mâncare", "Fruct"),
    DirectedPairSpec("n_v4gas_mancare", "n_v4gas_bucatarie", "Mâncare", "Bucătărie"),
    DirectedPairSpec("n_v3soc_scoala", "n_v3lit_carte", "Școală", "Carte"),
    DirectedPairSpec("n_v4soc_casa", "n_v4via_usa", "Casă", "Ușă"),
    DirectedPairSpec("n_v4soc_casa", "n_v4via_baie", "Casă", "Baie"),
    DirectedPairSpec("n_v4sti_corp", "n_v4sti_ochi", "Corp", "Ochi"),
    DirectedPairSpec("n_v4sti_corp", "n_v4sti_inima", "Corp", "Inimă"),
    DirectedPairSpec("n_v4sti_corp", "n_v4sti_sange", "Corp", "Sânge"),
    DirectedPairSpec("n_v4geo_padure", "n_v4sti_copac", "Pădure", "Copac"),
    DirectedPairSpec("n_v4gas_legume", "n_v4gas_rosie", "Legume", "Roșie"),
    DirectedPairSpec("n_v4gas_legume", "n_v4gas_ceapa", "Legume", "Ceapă"),
    DirectedPairSpec(
        "n_v4gas_legume", "n_v24_food_salad_veg_morcov", "Legume", "Morcov"
    ),
    DirectedPairSpec("n_v4soc_familie", "n_v4soc_parinte", "Familie", "Părinte"),
    DirectedPairSpec("n_v4soc_copil", "n_v4soc_familie", "Copil", "Familie"),
)

LANT_DIAMONDS: tuple[DiamondSpec, ...] = (
    DiamondSpec(
        "n_v4gas_bucatarie",
        "n_v4gas_mancare",
        "n_v4gas_legume",
        "n_v24_food_salad_veg_morcov",
        "două drumuri prin alimente",
    ),
    DiamondSpec(
        "n_v23via_ghiozdan",
        "n_v3soc_scoala",
        "n_v3lit_carte",
        "n_v24_school_classroom_lectie",
        "două drumuri spre lecție",
    ),
    DiamondSpec(
        "n_v4via_baie",
        "n_v4soc_casa",
        "n_v4via_usa",
        "n_v24_home_rooms_camera",
        "două drumuri prin casă",
    ),
    DiamondSpec(
        "n_v4per_om",
        "n_v4sti_corp",
        "n_v4sti_ochi",
        "n_v24_body_face_nas",
        "două drumuri prin corp",
    ),
    DiamondSpec(
        "n_v4gas_apa",
        "n_v4sti_aer",
        "n_v24_weather_precipitation_ploaie",
        "n_v24_weather_air_nor",
        "două drumuri prin vreme",
    ),
)

# One direct sibling probe per triad plus every audited repair association.
INTUITIVE_PAIRS: tuple[tuple[str, str], ...] = tuple(
    (triad.members[0].label, triad.members[1].label) for triad in TRIADS
) + tuple((repair.source_label, repair.target_label) for repair in INTUITIVE_REPAIRS)

# Exact pending records authored against this graph.  They stay invisible to runtime
# selection until the bound analyst + adversarial-verifier gate promotes them.
GAME_ITEMS: dict[str, tuple[dict[str, object], ...]] = {
    "conexiuni": (
        {
            "id": "cx_gastronomie_292",
            "category": "gastronomie",
            "difficulty": "usor",
            "source": "ai",
            "status": "pending",
            "groups": {
                "g1": [
                    "n_v24_food_pantry_zahar",
                    "n_v24_food_pantry_faina",
                    "n_v24_food_pantry_ulei",
                    "n_v4gas_sare",
                ],
                "g2": [
                    "n_v24_food_breakfast_unt",
                    "n_v24_food_breakfast_iaurt",
                    "n_v24_food_breakfast_miere",
                    "n_v3gas_cafea",
                ],
                "g3": [
                    "n_v24_food_orchard_mar",
                    "n_v24_food_orchard_para",
                    "n_v24_food_orchard_pruna",
                    "n_v24_food_small_fruit_cireasa",
                ],
                "g4": [
                    "n_v24_food_salad_veg_morcov",
                    "n_v24_food_salad_veg_ardei",
                    "n_v24_food_salad_veg_castravete",
                    "n_v4gas_rosie",
                ],
            },
            "group_labels": {
                "g1": "Ingrediente de bază pentru gătit",
                "g2": "La micul dejun",
                "g3": "Fructe de livadă",
                "g4": "Legume pentru salată",
            },
            "order": [
                "n_v24_food_pantry_zahar",
                "n_v24_food_breakfast_unt",
                "n_v24_food_orchard_mar",
                "n_v24_food_salad_veg_morcov",
                "n_v24_food_pantry_faina",
                "n_v24_food_breakfast_iaurt",
                "n_v24_food_orchard_para",
                "n_v24_food_salad_veg_ardei",
                "n_v24_food_pantry_ulei",
                "n_v24_food_breakfast_miere",
                "n_v24_food_orchard_pruna",
                "n_v24_food_salad_veg_castravete",
                "n_v4gas_sare",
                "n_v3gas_cafea",
                "n_v24_food_small_fruit_cireasa",
                "n_v4gas_rosie",
            ],
        },
        {
            "id": "cx_viata_de_roman_293",
            "category": "viata_de_roman",
            "difficulty": "usor",
            "source": "ai",
            "status": "pending",
            "groups": {
                "g1": [
                    "n_v24_home_rooms_camera",
                    "n_v24_home_rooms_sufragerie",
                    "n_v4via_baie",
                    "n_v4gas_bucatarie",
                ],
                "g2": [
                    "n_v24_home_bed_pat",
                    "n_v24_home_bed_saltea",
                    "n_v24_home_bed_perna",
                    "n_v24_home_textiles_patura",
                ],
                "g3": [
                    "n_v24_school_writing_caiet",
                    "n_v24_school_writing_creion",
                    "n_v24_school_writing_pix",
                    "n_v24_school_supplies_stilou",
                ],
                "g4": [
                    "n_v24_school_classroom_clasa_scolara",
                    "n_v24_school_classroom_banca_scolara",
                    "n_v23via_tabla_scolara",
                    "n_v4per_profesor",
                ],
            },
            "group_labels": {
                "g1": "Camere ale locuinței",
                "g2": "Pentru somn",
                "g3": "În ghiozdan, pentru scris",
                "g4": "În sala de clasă",
            },
            "order": [
                "n_v24_home_rooms_camera",
                "n_v24_home_bed_pat",
                "n_v24_school_writing_caiet",
                "n_v24_school_classroom_clasa_scolara",
                "n_v24_home_rooms_sufragerie",
                "n_v24_home_bed_saltea",
                "n_v24_school_writing_creion",
                "n_v24_school_classroom_banca_scolara",
                "n_v4via_baie",
                "n_v24_home_bed_perna",
                "n_v24_school_writing_pix",
                "n_v23via_tabla_scolara",
                "n_v4gas_bucatarie",
                "n_v24_home_textiles_patura",
                "n_v24_school_supplies_stilou",
                "n_v4per_profesor",
            ],
        },
        {
            "id": "cx_societate_294",
            "category": "societate",
            "difficulty": "usor",
            "source": "ai",
            "status": "pending",
            "groups": {
                "g1": [
                    "n_v24_people_parents_mama",
                    "n_v24_people_parents_tata",
                    "n_v24_people_descendants_fiu",
                    "n_v24_people_descendants_fiica",
                ],
                "g2": [
                    "n_v24_people_grandparents_bunica",
                    "n_v24_people_grandparents_bunic",
                    "n_v24_people_relatives_unchi",
                    "n_v24_people_grandparents_matusa",
                ],
                "g3": [
                    "n_v4sti_ochi",
                    "n_v4sti_ureche",
                    "n_v24_body_face_nas",
                    "n_v24_body_face_gura",
                ],
                "g4": [
                    "n_v24_transport_road_camion",
                    "n_v24_transport_road_duba",
                    "n_v24_transport_personal_masina",
                    "n_v24_transport_personal_motocicleta",
                ],
            },
            "group_labels": {
                "g1": "Părinți și copii",
                "g2": "Rude din familia extinsă",
                "g3": "Pe cap și pe față",
                "g4": "Vehicule rutiere",
            },
            "order": [
                "n_v24_people_parents_mama",
                "n_v24_people_grandparents_bunica",
                "n_v4sti_ochi",
                "n_v24_transport_road_camion",
                "n_v24_people_parents_tata",
                "n_v24_people_grandparents_bunic",
                "n_v4sti_ureche",
                "n_v24_transport_road_duba",
                "n_v24_people_descendants_fiu",
                "n_v24_people_relatives_unchi",
                "n_v24_body_face_nas",
                "n_v24_transport_personal_masina",
                "n_v24_people_descendants_fiica",
                "n_v24_people_grandparents_matusa",
                "n_v24_body_face_gura",
                "n_v24_transport_personal_motocicleta",
            ],
        },
        {
            "id": "cx_societate_295",
            "category": "societate",
            "difficulty": "usor",
            "source": "ai",
            "status": "pending",
            "groups": {
                "g1": [
                    "n_v24_transport_rail_tren",
                    "n_v24_transport_rail_tramvai",
                    "n_v24_transport_rail_metrou",
                    "n_v24_transport_road_microbuz",
                ],
                "g2": [
                    "n_v24_transport_terminals_gara",
                    "n_v24_transport_terminals_aeroport",
                    "n_v24_transport_terminals_statie",
                    "n_v2soc_port",
                ],
                "g3": [
                    "n_v24_places_public_parc",
                    "n_v24_places_public_farmacie",
                    "n_v24_places_public_restaurant",
                    "n_v4soc_magazin",
                ],
                "g4": [
                    "n_v24_weather_precipitation_ploaie",
                    "n_v24_weather_precipitation_zapada",
                    "n_v24_weather_air_vant",
                    "n_v24_weather_air_nor",
                ],
            },
            "group_labels": {
                "g1": "Vehicule de transport public",
                "g2": "Locuri de plecare și sosire",
                "g3": "Destinații cotidiene în oraș",
                "g4": "Fenomene meteo",
            },
            "order": [
                "n_v24_transport_rail_tren",
                "n_v24_transport_terminals_gara",
                "n_v24_places_public_parc",
                "n_v24_weather_precipitation_ploaie",
                "n_v24_transport_rail_tramvai",
                "n_v24_transport_terminals_aeroport",
                "n_v24_places_public_farmacie",
                "n_v24_weather_precipitation_zapada",
                "n_v24_transport_rail_metrou",
                "n_v24_transport_terminals_statie",
                "n_v24_places_public_restaurant",
                "n_v24_weather_air_vant",
                "n_v24_transport_road_microbuz",
                "n_v2soc_port",
                "n_v4soc_magazin",
                "n_v24_weather_air_nor",
            ],
        },
    ),
    "contexto": (
        {
            "id": "ct_gastronomie_300",
            "category": "gastronomie",
            "difficulty": "usor",
            "source": "ai",
            "status": "pending",
            "target": "n_v4gas_mancare",
        },
        {
            "id": "ct_gastronomie_301",
            "category": "gastronomie",
            "difficulty": "usor",
            "source": "ai",
            "status": "pending",
            "target": "n_v24_food_salad_veg_morcov",
        },
        {
            "id": "ct_viata_de_roman_302",
            "category": "viata_de_roman",
            "difficulty": "usor",
            "source": "ai",
            "status": "pending",
            "target": "n_v24_home_appliances_frigider",
        },
        {
            "id": "ct_societate_303",
            "category": "societate",
            "difficulty": "usor",
            "source": "ai",
            "status": "pending",
            "target": "n_v4soc_familie",
        },
        {
            "id": "ct_viata_de_roman_304",
            "category": "viata_de_roman",
            "difficulty": "usor",
            "source": "ai",
            "status": "pending",
            "target": "n_v24_school_writing_creion",
        },
        {
            "id": "ct_societate_305",
            "category": "societate",
            "difficulty": "usor",
            "source": "ai",
            "status": "pending",
            "target": "n_v24_places_public_farmacie",
        },
        {
            "id": "ct_stiinta_306",
            "category": "stiinta",
            "difficulty": "usor",
            "source": "ai",
            "status": "pending",
            "target": "n_v24_weather_precipitation_ploaie",
        },
        {
            "id": "ct_limba_307",
            "category": "limba",
            "difficulty": "usor",
            "source": "ai",
            "status": "pending",
            "target": "n_v24_action_language_a_citi",
        },
    ),
    "lant": (
        {
            "id": "lt_gastronomie_212",
            "category": "gastronomie",
            "difficulty": "usor",
            "source": "ai",
            "status": "pending",
            "start": "n_v4gas_bucatarie",
            "target": "n_v24_food_salad_veg_morcov",
            "optimal": 2,
        },
        {
            "id": "lt_viata_de_roman_213",
            "category": "viata_de_roman",
            "difficulty": "usor",
            "source": "ai",
            "status": "pending",
            "start": "n_v23via_ghiozdan",
            "target": "n_v24_school_classroom_lectie",
            "optimal": 2,
        },
        {
            "id": "lt_viata_de_roman_214",
            "category": "viata_de_roman",
            "difficulty": "usor",
            "source": "ai",
            "status": "pending",
            "start": "n_v4via_baie",
            "target": "n_v24_home_rooms_camera",
            "optimal": 2,
        },
        {
            "id": "lt_stiinta_215",
            "category": "stiinta",
            "difficulty": "usor",
            "source": "ai",
            "status": "pending",
            "start": "n_v4per_om",
            "target": "n_v24_body_face_nas",
            "optimal": 2,
        },
        {
            "id": "lt_stiinta_216",
            "category": "stiinta",
            "difficulty": "usor",
            "source": "ai",
            "status": "pending",
            "start": "n_v4gas_apa",
            "target": "n_v24_weather_air_nor",
            "optimal": 2,
        },
        {
            "id": "lt_viata_de_roman_217",
            "category": "viata_de_roman",
            "difficulty": "usor",
            "source": "ai",
            "status": "pending",
            "start": "n_v24_home_seating_scaun",
            "target": "n_v24_home_rooms_dormitor",
            "optimal": 3,
        },
        {
            "id": "lt_gastronomie_218",
            "category": "gastronomie",
            "difficulty": "normal",
            "source": "ai",
            "status": "pending",
            "start": "n_v2gas_ciorba",
            "target": "n_v24_food_salad_veg_morcov",
            "optimal": 4,
        },
        {
            "id": "lt_stiinta_219",
            "category": "stiinta",
            "difficulty": "normal",
            "source": "ai",
            "status": "pending",
            "start": "n_v4sti_corp",
            "target": "n_v24_weather_precipitation_zapada",
            "optimal": 4,
        },
    ),
    "alchimie": (
        {
            "id": "al_viata_de_roman_099",
            "category": "viata_de_roman",
            "difficulty": "usor",
            "source": "ai",
            "status": "pending",
            "seeds": [
                "n_v24_action_routine_a_dormi",
                "n_v24_action_routine_a_invata",
                "n_v24_home_rooms_camera",
                "n_v24_school_classroom_banca_scolara",
                "n_v24_school_writing_caiet",
                "n_v24_school_writing_creion",
                "n_v4via_usa",
            ],
            "target": "n_v24_home_bed_perna",
            "target_depth": 2,
        },
        {
            "id": "al_viata_de_roman_100",
            "category": "viata_de_roman",
            "difficulty": "usor",
            "source": "ai",
            "status": "pending",
            "seeds": [
                "n_v24_action_routine_a_dormi",
                "n_v24_action_routine_a_invata",
                "n_v24_home_rooms_camera",
                "n_v24_school_classroom_clasa_scolara",
                "n_v24_school_writing_caiet",
                "n_v24_school_writing_creion",
                "n_v4via_usa",
            ],
            "target": "n_v24_home_seating_fotoliu",
            "target_depth": 3,
        },
        {
            "id": "al_viata_de_roman_101",
            "category": "viata_de_roman",
            "difficulty": "usor",
            "source": "ai",
            "status": "pending",
            "seeds": [
                "n_v24_action_routine_a_dormi",
                "n_v24_action_routine_a_invata",
                "n_v24_home_bed_pat",
                "n_v24_school_classroom_banca_scolara",
                "n_v24_school_writing_caiet",
                "n_v24_school_writing_creion",
                "n_v4via_usa",
            ],
            "target": "n_v24_home_rooms_sufragerie",
            "target_depth": 3,
        },
        {
            "id": "al_viata_de_roman_102",
            "category": "viata_de_roman",
            "difficulty": "usor",
            "source": "ai",
            "status": "pending",
            "seeds": [
                "n_v24_action_routine_a_dormi",
                "n_v24_action_routine_a_invata",
                "n_v24_home_bed_pat",
                "n_v24_school_classroom_clasa_scolara",
                "n_v24_school_writing_caiet",
                "n_v24_school_writing_creion",
                "n_v4via_usa",
            ],
            "target": "n_v24_school_assessment_examen",
            "target_depth": 3,
        },
        {
            "id": "al_viata_de_roman_103",
            "category": "viata_de_roman",
            "difficulty": "normal",
            "source": "ai",
            "status": "pending",
            "seeds": [
                "n_v24_action_routine_a_dormi",
                "n_v24_action_routine_a_invata",
                "n_v24_home_rooms_sufragerie",
                "n_v24_school_classroom_banca_scolara",
                "n_v24_school_writing_caiet",
                "n_v24_school_writing_creion",
                "n_v4via_usa",
            ],
            "target": "n_v24_school_assessment_catalog_scolar",
            "target_depth": 4,
        },
        {
            "id": "al_viata_de_roman_104",
            "category": "viata_de_roman",
            "difficulty": "usor",
            "source": "ai",
            "status": "pending",
            "seeds": [
                "n_v24_action_routine_a_dormi",
                "n_v24_action_routine_a_invata",
                "n_v24_home_rooms_sufragerie",
                "n_v24_school_classroom_banca_scolara",
                "n_v24_school_classroom_clasa_scolara",
                "n_v24_school_writing_caiet",
                "n_v4via_usa",
            ],
            "target": "n_v24_home_textiles_covor",
            "target_depth": 3,
        },
    ),
}

GAME_ITEM_IDS: tuple[str, ...] = tuple(
    str(record["id"])
    for game in ("conexiuni", "contexto", "lant", "alchimie")
    for record in GAME_ITEMS[game]
)
EXISTING_ALIASES: dict[str, tuple[str, ...]] = {
    "n_v23via_tabla_scolara": ("tablă",),
}


def build_nodes_and_edges() -> dict[str, object]:
    """Return fresh fixture-merge records; callers may mutate the returned containers."""

    nodes = [
        {
            "id": concept.node_id,
            "node_type": "concept",
            "label_ro": concept.label,
            "category": concept.category,
            "description": concept.description,
            "salience": concept.salience,
            "aliases": list(concept.aliases),
        }
        for concept in CONCEPTS
    ]
    edges: list[dict[str, object]] = []
    for triad in TRIADS:
        for concept in triad.members:
            entry_anchor, exit_anchor = concept.anchors
            edges.append(
                {
                    "src": entry_anchor,
                    "dst": concept.node_id,
                    "relation": "beginner_entry",
                    "label_ro": "duce la",
                    "strength": 0.86,
                    "is_distractor": 0,
                    "bidirectional": 0,
                }
            )
            edges.append(
                {
                    "src": concept.node_id,
                    "dst": exit_anchor,
                    "relation": "beginner_exit",
                    "label_ro": "ține de",
                    "strength": 0.86,
                    "is_distractor": 0,
                    "bidirectional": 0,
                }
            )
        # Members 0 + 1 share member 2 as a single intuitive Alchimie result.  The
        # 0 -> 1 edge keeps the triad navigable without adding another shared result.
        for left_index, right_index in ((0, 2), (1, 2), (0, 1)):
            edges.append(
                {
                    "src": triad.members[left_index].node_id,
                    "dst": triad.members[right_index].node_id,
                    "relation": triad.relation,
                    "label_ro": triad.label_ro,
                    "strength": 0.9,
                    "is_distractor": 0,
                    "bidirectional": 0,
                }
            )
    for recipe in RECIPES:
        for source in (recipe.left, recipe.right):
            edges.append(
                {
                    "src": source,
                    "dst": recipe.result,
                    "relation": "beginner_recipe",
                    "label_ro": recipe.label_ro,
                    "strength": 0.94,
                    "is_distractor": 0,
                    "bidirectional": 0,
                }
            )
    for repair in INTUITIVE_REPAIRS:
        edges.append(
            {
                "src": repair.source,
                "dst": repair.target,
                "relation": "beginner_repair",
                "label_ro": "legătură intuitivă",
                "strength": 0.96,
                "is_distractor": 0,
                "bidirectional": 0,
            }
        )
    for diamond in LANT_DIAMONDS:
        for source, target in (
            (diamond.start, diamond.left),
            (diamond.start, diamond.right),
            (diamond.left, diamond.target),
            (diamond.right, diamond.target),
        ):
            edges.append(
                {
                    "src": source,
                    "dst": target,
                    "relation": "beginner_diamond",
                    "label_ro": diamond.label_ro,
                    "strength": 0.93,
                    "is_distractor": 0,
                    "bidirectional": 0,
                }
            )

    # Multiple declarations may intentionally prove the same directed association.
    # One playable edge is enough and avoids inflating fixture degree with parallel links.
    deduped_edges: list[dict[str, object]] = []
    seen_directions: set[tuple[str, str]] = set()
    for edge in edges:
        direction = (str(edge["src"]), str(edge["dst"]))
        if direction not in seen_directions:
            deduped_edges.append(edge)
            seen_directions.add(direction)
    aliases = {node_id: list(values) for node_id, values in EXISTING_ALIASES.items()}
    return {"nodes": nodes, "edges": deduped_edges, "aliases": aliases}


def _validate_source() -> None:
    expected_domain_counts = {
        "food": 50,
        "home": 31,
        "people_body": 34,
        "nature": 35,
        "transport_places": 24,
        "school_work_time": 28,
        "actions_feelings": 34,
    }
    actual_domain_counts = {
        domain: len(surfaces) for domain, surfaces in BEGINNER_BENCHMARK_BY_DOMAIN.items()
    }
    assert actual_domain_counts == expected_domain_counts
    assert len(BEGINNER_BENCHMARK) == len({_norm(term) for term in BEGINNER_BENCHMARK}) == 236
    assert len(TRIADS) == 50
    assert len(CONCEPTS) == len(set(NEW_NODE_IDS)) == 150
    assert all(node_id.startswith("n_v24") for node_id in NEW_NODE_IDS)
    assert len({_norm(concept.label) for concept in CONCEPTS}) == len(CONCEPTS)
    benchmark_keys = {_norm(term) for term in BEGINNER_BENCHMARK}
    assert all(_norm(concept.label) in benchmark_keys for concept in CONCEPTS)
    assert all(
        recipe.left in NEW_NODE_IDS
        and recipe.right in NEW_NODE_IDS
        and recipe.result in NEW_NODE_IDS
        and len({recipe.left, recipe.right, recipe.result}) == 3
        for recipe in RECIPES
    )
    assert len(INTUITIVE_REPAIRS) == len(
        {(repair.source, repair.target) for repair in INTUITIVE_REPAIRS}
    )
    assert all(
        len({diamond.start, diamond.left, diamond.right, diamond.target}) == 4
        for diamond in LANT_DIAMONDS
    )

    owners = {_norm(concept.label): concept.node_id for concept in CONCEPTS}
    for concept in CONCEPTS:
        assert len(set(concept.anchors)) == 2
        assert concept.aliases
        for alias in concept.aliases:
            key = _norm(alias)
            assert key not in owners, (concept.node_id, alias, owners[key])
            owners[key] = concept.node_id


_validate_source()
