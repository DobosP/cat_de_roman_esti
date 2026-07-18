"""Authored, Contexto-only projection for broad everyday Romanian guesses.

The shared knowledge graph stays the source of target selection and semantic distance.
These extra surfaces are *guess-only*: each one borrows an existing node's feedback,
with a tiny rank penalty where the meaning is deliberately broader.  They never become
KG nodes, aliases, targets, recipes, or Lanț moves.

The inventory is plain project-owned data and uses only the Python standard library.
"""

from __future__ import annotations

import difflib
import hashlib
import unicodedata
from dataclasses import dataclass


def normalize_projection_surface(text: str) -> str:
    """Match the KG resolver's accent-insensitive, whitespace-stable normalization."""

    decomposed = unicodedata.normalize("NFKD", text)
    no_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(no_accents.casefold().split())


@dataclass(frozen=True, slots=True)
class ProjectionTerm:
    surface: str
    anchor_id: str
    domain: str
    rank_penalty: int = 1
    mapping_kind: str = "explicit"

    @property
    def key(self) -> str:
        return normalize_projection_surface(self.surface)

    @property
    def label(self) -> str:
        return self.surface[:1].upper() + self.surface[1:]

    @property
    def public_id(self) -> str:
        # Deliberately cannot resemble a KG node id or reveal the private anchor id.
        digest = hashlib.blake2s(self.key.encode("utf-8"), digest_size=10).hexdigest()
        return f"ctxp_{digest}"


@dataclass(frozen=True, slots=True)
class DomainPolicy:
    """Honest broad fallback, or an explicit declaration that every term is clustered."""

    fallback_anchor_id: str | None
    rationale: str


# A fallback is named and justified per domain; it is never inferred from table position.
# ``None`` means the domain has no honest hypernym in the KG and every live term must be
# present in an explicit semantic cluster below.
PROJECTION_DOMAIN_POLICIES: dict[str, DomainPolicy] = {
    "mâncare gătită": DomainPolicy("n_v4gas_mancare", "broad prepared-food concept"),
    "ingrediente": DomainPolicy("n_v4gas_mancare", "broad edible-ingredient context"),
    "băuturi": DomainPolicy("n_v4gas_apa", "broad drink/liquid context"),
    "mobilier și casă": DomainPolicy("n_v4soc_casa", "broad home context"),
    "ustensile de bucătărie": DomainPolicy("n_v4gas_bucatarie", "broad kitchen context"),
    "igienă": DomainPolicy("n_v4via_baie", "broad personal-hygiene room context"),
    "curățenie": DomainPolicy(None, "no honest generic cleaning hypernym; map every term"),
    "îmbrăcăminte": DomainPolicy("n_v29_clothing_everyday_haina", "broad clothing item"),
    "corp": DomainPolicy("n_v4sti_corp", "body hypernym"),
    "sănătate": DomainPolicy("n_medicina", "medicine and health hypernym"),
    "oameni și relații": DomainPolicy("n_v4soc_familie", "broad social/family context"),
    "stări și emoții": DomainPolicy(None, "no generic emotion node; map every term"),
    "școală": DomainPolicy("n_v3soc_scoala", "school hypernym/context"),
    "muncă": DomainPolicy("n_v4soc_munca", "work hypernym/context"),
    "tehnologie": DomainPolicy("n_v2sti_calculator", "broad digital-device context"),
    "transport rutier": DomainPolicy(
        "n_v24_transport_personal_masina", "road-vehicle context after route overrides"
    ),
    "locuri din oraș": DomainPolicy("n_v2geo_oras", "urban-place hypernym/context"),
    "peisaj": DomainPolicy("n_v24_nature_world_natura", "natural-landscape hypernym"),
    "plante și grădină": DomainPolicy("n_v4sti_planta", "plant hypernym"),
    "animale domestice și păsări": DomainPolicy("n_v4sti_animal", "animal hypernym"),
    "viețuitoare mici și marine": DomainPolicy("n_v4sti_animal", "animal hypernym"),
    "vreme și momente ale zilei": DomainPolicy(
        "n_v24_nature_world_natura", "broad natural/time-of-day context"
    ),
    "sport": DomainPolicy("n_v4spo_sport", "sport hypernym"),
    "timp liber și artă": DomainPolicy("n_v3art_arta", "broad creative/leisure context"),
    "acțiuni de mișcare": DomainPolicy(
        "n_v24_action_movement_a_merge", "locomotion proxy; non-locomotion terms removed"
    ),
    "acțiuni cotidiene": DomainPolicy(None, "no generic action node; map every term"),
}


# (domain, penalty, canonical guess surfaces). Surfaces are screened against every
# normalized KG label/id/alias. Mapping comes only from an explicit cluster or the named
# domain policy above.
_GROUPS: tuple[tuple[str, int, tuple[str, ...]], ...] = (
    (
        "mâncare gătită",
        1,
        (
            "pizza",
            "hamburger",
            "paste făinoase",
            "tăiței",
            "omletă",
            "tocăniță",
            "pilaf",
            "friptură",
            "chiftea",
            "clătită",
            "gogoașă",
            "cereale",
            "desert",
            "înghețată",
            "prăjitură",
            "sos",
            "ketchup",
            "maioneză",
            "ramen",
            "lasagna",
            "shaorma",
            "burrito",
            "taco",
            "budincă",
            "brioșă",
            "chec",
            "covrig",
            "croasant",
            "salată de fructe",
            "cartofi prăjiți",
        ),
    ),
    (
        "ingrediente",
        1,
        (
            "quinoa",
            "linte",
            "năut",
            "broccoli",
            "avocado",
            "țelină",
            "pătrunjel",
            "mărar",
            "oregano",
            "busuioc",
            "scorțișoară",
            "piper",
            "boia",
            "oțet",
            "drojdie",
            "smântână",
            "gem",
            "dulceață",
            "nucă",
            "alună",
        ),
    ),
    (
        "băuturi",
        1,
        (
            "suc",
            "limonadă",
            "cola",
            "cacao",
            "cappuccino",
            "espresso",
            "ciocolată caldă",
            "apă minerală",
            "apă plată",
            "milkshake",
            "smoothie",
            "compot",
            "sirop",
            "băutură răcoritoare",
            "ceai verde",
            "cafea cu lapte",
        ),
    ),
    (
        "mobilier și casă",
        1,
        (
            "noptieră",
            "bibliotecă de perete",
            "cuier",
            "veioză",
            "clanță",
            "cheie de casă",
            "sonerie",
            "interfon",
            "perdea",
            "draperie",
            "jaluzea",
            "coș de gunoi",
            "preș",
            "taburet",
            "birou de acasă",
            "scară interioară",
            "hol",
            "debara",
        ),
    ),
    (
        "ustensile de bucătărie",
        0,
        (
            "tel de bucătărie",
            "polonic",
            "spatulă",
            "strecurătoare",
            "răzătoare",
            "tocător de bucătărie",
            "tirbușon",
            "desfăcător de sticle",
            "tavă",
            "capac",
            "ibric",
            "fierbător",
            "blender",
            "mixer",
            "prăjitor de pâine",
            "cuptor cu microunde",
            "congelator",
            "hotă de bucătărie",
        ),
    ),
    (
        "igienă",
        1,
        (
            "deodorant",
            "parfum",
            "cremă de corp",
            "loțiune",
            "gel de duș",
            "ață dentară",
            "apă de gură",
            "aparat de ras",
            "lamă de ras",
            "uscător de păr",
            "unghieră",
            "vată",
            "bețișor de urechi",
            "șervețel umed",
            "balsam de păr",
            "prosop de mâini",
            "covoraș de baie",
            "săpun lichid",
        ),
    ),
    (
        "curățenie",
        1,
        (
            "mătură",
            "cârpă de praf",
            "lavetă",
            "perie de curățat",
            "pămătuf",
            "soluție de geamuri",
            "dezinfectant",
            "înălbitor",
            "sac de gunoi",
            "uscător de rufe",
            "mașină de spălat",
            "mașină de spălat vase",
            "fier de călcat",
            "masă de călcat",
            "clește de rufe",
            "coș de rufe",
        ),
    ),
    (
        "îmbrăcăminte",
        0,
        (
            "tricou",
            "pulover",
            "hanorac",
            "maiou",
            "sacou",
            "costum",
            "cravată",
            "curea",
            "mănușă",
            "căciulă",
            "pălărie",
            "șapcă",
            "eșarfă",
            "pijama",
            "papuc",
            "sandală",
            "cizmă",
            "bocanc",
            "adidaș",
            "lenjerie",
        ),
    ),
    (
        "corp",
        1,
        (
            "cot",
            "umăr",
            "braț",
            "încheietură",
            "palmă",
            "unghie",
            "spate",
            "piept",
            "burtă",
            "talie",
            "șold",
            "piele",
            "os",
            "mușchi",
            "sânge",
            "creier",
            "stomac",
            "plămân",
            "ficat",
            "rinichi",
        ),
    ),
    (
        "sănătate",
        1,
        (
            "doctor",
            "asistentă medicală",
            "pacient",
            "boală",
            "răceală",
            "febră",
            "tuse",
            "durere",
            "rană",
            "bandaj",
            "plasture",
            "medicament",
            "pastilă",
            "sirop de tuse",
            "rețetă medicală",
            "ambulanță",
            "cabinet medical",
            "operație",
        ),
    ),
    (
        "oameni și relații",
        1,
        (
            "verișor",
            "verișoară",
            "cumnat",
            "cumnată",
            "naș",
            "nașă",
            "logodnic",
            "logodnică",
            "colegă",
            "șef",
            "client",
            "musafir",
            "adult",
            "adolescent",
            "tânăr",
            "bătrân",
            "mire",
            "mireasă",
        ),
    ),
    (
        "stări și emoții",
        1,
        (
            "fericire",
            "mulțumire",
            "entuziasm",
            "curaj",
            "calm",
            "neliniște",
            "grijă",
            "plictiseală",
            "nerăbdare",
            "gelozie",
            "vinovăție",
            "dezamăgire",
            "uimire",
            "încredere",
            "respect",
            "prietenie",
            "singurătate",
            "stres",
            "relaxare",
        ),
    ),
    (
        "școală",
        1,
        (
            "student",
            "studentă",
            "învățător",
            "învățătoare",
            "director de școală",
            "directoare de școală",
            "coleg de clasă",
            "manual școlar",
            "dicționar",
            "penar",
            "acuarelă",
            "foarfecă",
            "lipici",
            "marker",
            "calculator de buzunar",
            "recreație",
            "vacanță școlară",
            "notă școlară",
            "diplomă",
        ),
    ),
    (
        "muncă",
        1,
        (
            "job",
            "profesie",
            "angajat",
            "angajator",
            "ședință",
            "proiect de lucru",
            "termen limită",
            "concediu",
            "pauză de lucru",
            "program de lucru",
            "schimb de noapte",
            "uniformă de lucru",
            "atelier",
            "fabrică",
            "depozit",
            "magazioner",
            "mecanic",
            "electrician",
            "instalator",
            "tâmplar",
        ),
    ),
    (
        "tehnologie",
        1,
        (
            "laptop",
            "tabletă",
            "tastatură",
            "mouse de calculator",
            "monitor",
            "imprimantă",
            "căști audio",
            "difuzor",
            "microfon",
            "cameră web",
            "încărcător",
            "baterie externă",
            "memorie USB",
            "router",
            "internet",
            "parolă",
            "aplicație",
            "mesaj text",
            "apel video",
            "fotografie digitală",
        ),
    ),
    (
        "transport rutier",
        1,
        (
            "volan",
            "pedală",
            "frână",
            "motor de mașină",
            "roată",
            "anvelopă",
            "centură de siguranță",
            "scaun auto",
            "portbagaj",
            "parbriz",
            "semafor",
            "trecere de pietoni",
            "sens giratoriu",
            "intersecție",
            "parcare",
            "bilet de autobuz",
            "abonament de transport",
            "peron",
            "călător",
            "șofer",
        ),
    ),
    (
        "locuri din oraș",
        1,
        (
            "brutărie",
            "măcelărie",
            "cofetărie",
            "cafenea",
            "piață agroalimentară",
            "supermarket",
            "mall",
            "poștă",
            "bancă comercială",
            "primărie",
            "secție de poliție",
            "stație de pompieri",
            "loc de joacă",
            "sală de sport",
            "cinematograf",
            "teatru",
            "muzeu",
            "hotel",
            "pensiune",
            "benzinărie",
        ),
    ),
    (
        "peisaj",
        1,
        (
            "vale",
            "coastă",
            "câmpie",
            "deltă",
            "ocean",
            "golf marin",
            "peninsulă",
            "continent",
            "țară",
            "frontieră",
            "potecă",
            "poiană",
            "stâncă",
            "bolovan",
            "noroi",
            "praf",
            "lut",
            "argilă",
            "scoică",
            "val al mării",
            "canion",
            "recif",
            "lagună",
            "mlaștină",
            "pajiște",
            "vulcan",
            "ghețar",
            "oază",
            "deșert",
            "prăpastie",
            "mal de râu",
            "țărm stâncos",
        ),
    ),
    (
        "plante și grădină",
        1,
        (
            "sămânță",
            "răsad",
            "buruiană",
            "mușchi de pădure",
            "ferigă",
            "cactus",
            "trandafir",
            "lalea",
            "margaretă",
            "floarea-soarelui",
            "viorea",
            "crin",
            "bujor",
            "ghindă",
            "con de brad",
            "scoarță de copac",
            "mugur",
            "tulpină",
            "petală",
            "spin",
        ),
    ),
    (
        "animale domestice și păsări",
        1,
        (
            "hamster",
            "papagal",
            "porumbel",
            "vrabie",
            "cioară",
            "rândunică",
            "bufniță",
            "vultur",
            "rață",
            "gâscă",
            "curcan",
            "măgar",
            "taur",
            "vițel",
            "miel",
            "șarpe",
            "broască",
            "șopârlă",
            "melc",
            "fluture",
        ),
    ),
    (
        "viețuitoare mici și marine",
        1,
        (
            "albină",
            "furnică",
            "păianjen",
            "muscă",
            "țânțar",
            "gândac",
            "râmă",
            "pește",
            "rechin",
            "delfin",
            "balenă",
            "caracatiță",
            "crab",
            "meduză",
            "focă",
            "pinguin",
        ),
    ),
    (
        "vreme și momente ale zilei",
        1,
        (
            "primăvară",
            "vară",
            "toamnă",
            "iarnă",
            "dimineață",
            "prânz",
            "seară",
            "miezul nopții",
            "răsărit",
            "apus",
            "temperatură",
            "căldură",
            "frig",
            "ger",
            "brumă",
            "rouă",
            "umbră",
            "lumină",
            "întuneric",
        ),
    ),
    (
        "sport",
        1,
        (
            "baschet",
            "volei",
            "handbal",
            "tenis",
            "înot",
            "alergare",
            "ciclism",
            "schi",
            "patinaj",
            "minge",
            "poartă de fotbal",
            "teren de sport",
            "stadion",
            "echipă",
            "antrenor",
            "arbitru",
            "scor",
            "medalie",
            "trofeu",
            "campionat",
            "badminton",
            "ping-pong",
            "gimnastică aerobică",
            "yoga",
            "fitness",
            "box",
            "judo",
            "karate",
            "surf",
            "escaladă",
            "rachetă de tenis",
            "fluier de arbitru",
        ),
    ),
    (
        "timp liber și artă",
        1,
        (
            "desen",
            "pictură",
            "fotografie",
            "film",
            "serial",
            "desen animat",
            "poveste",
            "poezie",
            "roman polițist",
            "revistă",
            "ziar",
            "puzzle",
            "joc de masă",
            "joc video",
            "jucărie",
            "păpușă",
            "cuburi de construit",
            "chitară",
            "pian",
            "vioară",
            "tobă",
            "cântec",
            "origami",
            "colaj",
            "croșetat",
            "tricotat",
            "colecție personală",
            "bandă desenată",
            "carte de colorat",
            "karaoke",
            "audiocarte",
            "concert acustic",
            "spectacol de magie",
            "dans de societate",
        ),
    ),
    (
        "acțiuni de mișcare",
        1,
        (
            "a alerga",
            "a sări",
            "a urca",
            "a coborî",
            "a pleca",
            "a întoarce",
            "a călători",
            "a conduce",
            "a fugi",
            "a păși",
            "a traversa",
            "a se plimba",
            "a se deplasa",
            "a pedala",
        ),
    ),
    (
        "acțiuni cotidiene",
        1,
        (
            "a curăța",
            "a mătura",
            "a aspira",
            "a șterge",
            "a repara",
            "a construi",
            "a tăia",
            "a aprinde",
            "a stinge",
            "a asculta",
            "a întreba",
            "a răspunde",
            "a explica",
            "a povesti",
            "a cânta",
            "a desena",
            "a cumpăra",
            "a vinde",
            "a plăti",
        ),
    ),
)


# These otherwise-useful candidates already resolve through the shared KG.  Keeping the
# screen explicit proves that the projection does not shadow a label or true alias; the
# normal KG resolver continues to own them.  Tests also detect any *new* fixture collision.
_EXISTING_KG_SURFACES = frozenset(
    normalize_projection_surface(surface)
    for surface in (
        "pizza",
        "paste făinoase",
        "friptură",
        "chiftea",
        "clătită",
        "gogoașă",
        "desert",
        "înghețată",
        "prăjitură",
        "sos",
        "smântână",
        "dulceață",
        "compot",
        "interfon",
        "tricou",
        "costum",
        "piele",
        "os",
        "sânge",
        "creier",
        "doctor",
        "pacient",
        "ambulanță",
        "naș",
        "colegă",
        "student",
        "dicționar",
        "penar",
        "fabrică",
        "microfon",
        "internet",
        "parcare",
        "piață agroalimentară",
        "poștă",
        "primărie",
        "cinematograf",
        "teatru",
        "muzeu",
        "vale",
        "coastă",
        "câmpie",
        "deltă",
        "ocean",
        "peninsulă",
        "continent",
        "țară",
        "frontieră",
        "potecă",
        "poiană",
        "stâncă",
        "lut",
        "argilă",
        "pește",
        "focă",
        "temperatură",
        "căldură",
        "lumină",
        "baschet",
        "volei",
        "handbal",
        "tenis",
        "înot",
        "alergare",
        "minge",
        "stadion",
        "echipă",
        "antrenor",
        "arbitru",
        "scor",
        "medalie",
        "campionat",
        "desen",
        "pictură",
        "fotografie",
        "film",
        "serial",
        "desen animat",
        "poveste",
        "poezie",
        "revistă",
        "ziar",
        "chitară",
        "pian",
        "vioară",
        "tobă",
        "cântec",
        "cartofi prăjiți",
        "vulcan",
        "ping-pong",
        "fitness",
        "box",
    )
)


# Explicit semantic sub-clusters override a domain's honest broad default.  This is
# intentionally authored by meaning rather than distributed by position: "espresso"
# borrows Cafea, never whichever anchor happens to be fourth in a list.
_ANCHOR_CLUSTERS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("n_v4gas_paine", ("brioșă", "chec", "covrig", "croasant")),
    ("n_v24_food_pantry_faina", ("tăiței", "cereale", "ramen", "lasagna")),
    (
        "n_v4gas_legume",
        ("linte", "năut", "broccoli", "avocado", "țelină", "pătrunjel", "mărar"),
    ),
    ("n_v24_food_breakfast_miere", ("gem", "nucă", "alună")),
    ("n_v3gas_cafea", ("cacao", "cappuccino", "espresso", "cafea cu lapte")),
    ("n_v24_food_snack_ceai", ("ceai verde", "ciocolată caldă")),
    ("n_v4gas_lapte", ("milkshake", "smoothie")),
    ("n_v4soc_apartament", ("interfon", "hol", "debara", "scară interioară")),
    ("n_v24_home_storage_dulap", ("cuier", "bibliotecă de perete")),
    ("n_v24_home_bed_pat", ("noptieră", "veioză")),
    ("n_v29_kitchen_table_cutit", ("tocător de bucătărie", "tirbușon", "desfăcător de sticle")),
    (
        "n_v30_kitchen_utensil_lingura",
        ("tel de bucătărie", "polonic", "spatulă", "strecurătoare", "răzătoare"),
    ),
    ("n_v30_kitchen_cookware_oala", ("tavă", "capac", "ibric", "fierbător")),
    ("n_v24_home_appliances_frigider", ("congelator",)),
    ("n_v31_hygiene_hair_sampon", ("balsam de păr", "uscător de păr")),
    ("n_v31_hygiene_oral_periuta_dinti", ("ață dentară", "apă de gură")),
    ("n_v31_hygiene_bath_sapun", ("gel de duș", "săpun lichid")),
    ("n_v31_cleaning_floor_aspirator", ("mătură", "pămătuf")),
    ("n_v31_cleaning_floor_mop", ("cârpă de praf", "lavetă", "perie de curățat")),
    ("n_v31_cleaning_water_galeata", ("soluție de geamuri", "înălbitor", "dezinfectant")),
    ("n_v31_cleaning_supply_detergent", ("sac de gunoi",)),
    ("n_v4soc_casa", ("uscător de rufe", "mașină de spălat")),
    ("n_v4gas_bucatarie", ("mașină de spălat vase",)),
    (
        "n_v29_clothing_everyday_haina",
        ("fier de călcat", "masă de călcat", "clește de rufe", "coș de rufe"),
    ),
    ("n_v30_clothing_footwear_pantof", ("papuc", "sandală", "cizmă", "bocanc", "adidaș")),
    ("n_v30_clothing_outer_geaca", ("pulover", "hanorac", "sacou", "mănușă", "căciulă")),
    ("n_v30_clothing_everyday_pantaloni", ("curea", "pijama", "lenjerie")),
    ("n_v24_body_limbs_mana", ("cot", "umăr", "braț", "încheietură", "palmă", "unghie")),
    ("n_v24_body_face_cap", ("creier",)),
    ("n_v24_body_limbs_picior", ("șold", "talie")),
    (
        "n_v17soc_medicul_de_familie",
        ("asistentă medicală", "boală", "răceală", "febră", "tuse", "durere", "rană", "operație"),
    ),
    (
        "n_v24_places_public_farmacie",
        ("bandaj", "plasture", "medicament", "pastilă", "sirop de tuse", "rețetă medicală"),
    ),
    ("n_v24_people_relationships_prieten", ("logodnic", "logodnică", "client", "musafir")),
    ("n_v29_people_coleg", ("colegă", "șef")),
    ("n_v4soc_copil", ("adolescent", "tânăr")),
    (
        "n_v24_feeling_difficult_tristete",
        (
            "neliniște",
            "grijă",
            "plictiseală",
            "gelozie",
            "vinovăție",
            "dezamăgire",
            "singurătate",
            "stres",
        ),
    ),
    ("n_v24_feeling_difficult_frica", ("curaj", "nerăbdare")),
    ("n_v28_feeling_positive_liniste", ("calm", "încredere", "respect", "prietenie", "relaxare")),
    ("n_v24_feeling_joy_bucurie", ("fericire", "mulțumire", "entuziasm")),
    ("n_v28_feeling_social_surpriza", ("uimire",)),
    ("n_v3lit_carte", ("manual școlar", "dicționar", "diplomă")),
    ("n_v24_school_writing_caiet", ("penar", "acuarelă", "foarfecă", "lipici", "marker")),
    ("n_v24_school_classroom_lectie", ("recreație", "vacanță școlară", "notă școlară")),
    (
        "n_v28_work_occupation_meserie",
        ("job", "profesie", "mecanic", "electrician", "instalator", "tâmplar"),
    ),
    ("n_v29_people_coleg", ("angajat", "angajator", "șef")),
    ("n_v4mem_telefon", ("tabletă", "căști audio", "încărcător", "mesaj text", "apel video")),
    ("n_v3sti_electricitate", ("baterie externă",)),
    ("n_v4geo_drum", ("semafor", "trecere de pietoni", "sens giratoriu", "intersecție")),
    (
        "n_v24_transport_terminals_statie",
        ("bilet de autobuz", "abonament de transport", "peron", "călător"),
    ),
    ("n_v29_city_street_trotuar", ("parcare",)),
    (
        "n_v29_routine_shopping_cumparaturi",
        ("brutărie", "măcelărie", "cofetărie", "supermarket", "mall"),
    ),
    ("n_v4soc_banca", ("bancă comercială",)),
    ("n_v24_places_public_restaurant", ("cafenea", "hotel", "pensiune")),
    ("n_v24_places_public_parc", ("loc de joacă", "sală de sport")),
    ("n_v2geo_rau", ("canion", "mlaștină", "mal de râu")),
    ("n_v24_nature_world_pamant", ("bolovan", "noroi", "praf")),
    ("n_v4sti_copac", ("ghindă", "con de brad", "scoarță de copac", "mugur")),
    (
        "n_v24_nature_plant_parts_iarba",
        ("sămânță", "răsad", "buruiană", "mușchi de pădure", "ferigă"),
    ),
    (
        "n_v24_home_outdoor_gradina",
        (
            "cactus",
            "trandafir",
            "lalea",
            "margaretă",
            "floarea-soarelui",
            "viorea",
            "crin",
            "bujor",
        ),
    ),
    (
        "n_v4sti_pasare",
        (
            "papagal",
            "porumbel",
            "vrabie",
            "cioară",
            "rândunică",
            "bufniță",
            "vultur",
            "rață",
            "gâscă",
            "curcan",
        ),
    ),
    ("n_v30_animal_farm_vaca", ("măgar", "taur", "vițel", "miel")),
    ("n_v4sti_peste", ("rechin",)),
    ("n_v4sti_pasare", ("pinguin",)),
    ("n_v24_weather_air_vant", ("ger", "brumă", "rouă", "frig")),
    ("n_v24_time_day_zi", ("dimineață", "prânz", "seară", "miezul nopții")),
    ("n_v24_nature_sky_soare", ("răsărit", "apus", "umbră", "întuneric")),
    ("n_v2spo_club_sportiv", ("teren de sport", "echipă", "trofeu", "campionat")),
    ("n_v2spo_inot_sportiv", ("surf",)),
    (
        "n_v3lit_carte",
        ("roman polițist", "puzzle", "bandă desenată", "carte de colorat", "audiocarte"),
    ),
    ("n_v4art_muzica", ("karaoke", "concert acustic", "dans de societate")),
    ("n_v24_action_home_a_spala", ("a curăța", "a mătura", "a aspira", "a șterge")),
    ("n_v32_workshop_hand_ciocan", ("a repara", "a construi")),
    ("n_v29_kitchen_table_cutit", ("a tăia",)),
    ("n_v4sti_foc", ("a aprinde", "a stinge")),
    ("n_v24_action_senses_a_auzi", ("a asculta",)),
    (
        "n_v24_action_language_a_spune",
        ("a întreba", "a răspunde", "a explica", "a povesti"),
    ),
    ("n_v4art_muzica", ("a cânta",)),
    ("n_v3art_desen", ("a desena",)),
    ("n_v29_routine_shopping_cumparaturi", ("a cumpăra",)),
    ("n_v4soc_bani", ("a vinde", "a plăti")),
)


def _build_anchor_overrides() -> dict[str, str]:
    overrides: dict[str, str] = {}
    for anchor_id, surfaces in _ANCHOR_CLUSTERS:
        for surface in surfaces:
            key = normalize_projection_surface(surface)
            previous = overrides.setdefault(key, anchor_id)
            if previous != anchor_id:
                raise RuntimeError(f"conflicting Contexto anchors for {surface!r}")
    return overrides


_ANCHOR_OVERRIDES = _build_anchor_overrides()
# Public read-only audit surface: tests validate every authored cluster, including
# candidates intentionally screened out because the KG already owns them.
PROJECTION_OVERRIDE_CLUSTERS = _ANCHOR_CLUSTERS


def _build_terms() -> tuple[ProjectionTerm, ...]:
    terms: list[ProjectionTerm] = []
    group_domains = {domain for domain, _penalty, _surfaces in _GROUPS}
    if group_domains != set(PROJECTION_DOMAIN_POLICIES):
        raise RuntimeError("Contexto domains and named fallback policies must match exactly")
    for domain, penalty, surfaces in _GROUPS:
        policy = PROJECTION_DOMAIN_POLICIES[domain]
        if not policy.rationale.strip():
            raise RuntimeError(f"Contexto domain {domain!r} has no fallback rationale")
        for surface in surfaces:
            key = normalize_projection_surface(surface)
            if key in _EXISTING_KG_SURFACES:
                continue
            anchor_id = _ANCHOR_OVERRIDES.get(key)
            mapping_kind = "explicit"
            if anchor_id is None:
                anchor_id = policy.fallback_anchor_id
                mapping_kind = "domain_fallback"
            if anchor_id is None:
                raise RuntimeError(
                    f"Contexto term {surface!r} needs an explicit anchor; "
                    f"domain {domain!r} has no honest fallback"
                )
            terms.append(ProjectionTerm(surface, anchor_id, domain, penalty, mapping_kind))
    result = tuple(terms)
    keys = [term.key for term in result]
    public_ids = [term.public_id for term in result]
    if not all(keys) or len(keys) != len(set(keys)):
        raise RuntimeError("Contexto projection surfaces must normalize uniquely")
    if len(public_ids) != len(set(public_ids)):
        raise RuntimeError("Contexto projection public ids must be unique")
    if any(term.rank_penalty not in (0, 1) for term in result):
        raise RuntimeError("Contexto projection penalties must stay bounded to 0..1")
    unused_overrides = set(_ANCHOR_OVERRIDES) - set(keys) - _EXISTING_KG_SURFACES
    if unused_overrides:
        raise RuntimeError(f"Contexto anchor overrides name unknown surfaces: {unused_overrides}")
    return result


PROJECTION_TERMS = _build_terms()
PROJECTION_INDEX = {term.key: term for term in PROJECTION_TERMS}

# One human-legible representative per authored domain. Tests pin these semantic
# pairings and require the audit to cover every domain, preventing a later mechanical
# redistribution from silently turning the projection into arbitrary rank noise.
PROJECTION_LEGIBILITY_AUDIT: tuple[tuple[str, str, str], ...] = (
    ("mâncare gătită", "brioșă", "n_v4gas_paine"),
    ("ingrediente", "linte", "n_v4gas_legume"),
    ("băuturi", "espresso", "n_v3gas_cafea"),
    ("mobilier și casă", "noptieră", "n_v24_home_bed_pat"),
    ("ustensile de bucătărie", "polonic", "n_v30_kitchen_utensil_lingura"),
    ("igienă", "ață dentară", "n_v31_hygiene_oral_periuta_dinti"),
    ("curățenie", "mătură", "n_v31_cleaning_floor_aspirator"),
    ("îmbrăcăminte", "sandală", "n_v30_clothing_footwear_pantof"),
    ("corp", "palmă", "n_v24_body_limbs_mana"),
    ("sănătate", "pastilă", "n_v24_places_public_farmacie"),
    ("oameni și relații", "logodnic", "n_v24_people_relationships_prieten"),
    ("stări și emoții", "calm", "n_v28_feeling_positive_liniste"),
    ("școală", "manual școlar", "n_v3lit_carte"),
    ("muncă", "electrician", "n_v28_work_occupation_meserie"),
    ("tehnologie", "apel video", "n_v4mem_telefon"),
    ("transport rutier", "semafor", "n_v4geo_drum"),
    ("locuri din oraș", "supermarket", "n_v29_routine_shopping_cumparaturi"),
    ("peisaj", "mal de râu", "n_v2geo_rau"),
    ("plante și grădină", "ghindă", "n_v4sti_copac"),
    ("animale domestice și păsări", "papagal", "n_v4sti_pasare"),
    ("viețuitoare mici și marine", "rechin", "n_v4sti_peste"),
    ("vreme și momente ale zilei", "seară", "n_v24_time_day_zi"),
    ("sport", "teren de sport", "n_v2spo_club_sportiv"),
    ("timp liber și artă", "roman polițist", "n_v3lit_carte"),
    ("acțiuni de mișcare", "a călători", "n_v24_action_movement_a_merge"),
    ("acțiuni cotidiene", "a explica", "n_v24_action_language_a_spune"),
)


def resolve_projection(text: str) -> ProjectionTerm | None:
    """Resolve only an exact normalized authored surface; never fuzzy-auto-play it."""

    return PROJECTION_INDEX.get(normalize_projection_surface(text))


def suggest_projection(text: str, *, limit: int = 6) -> list[ProjectionTerm]:
    """Return deterministic, bounded fill-only suggestions for projection typos."""

    key = normalize_projection_surface(text)
    if not key:
        return []
    matches = difflib.get_close_matches(key, PROJECTION_INDEX, n=limit, cutoff=0.78)
    return [PROJECTION_INDEX[matched] for matched in matches]
