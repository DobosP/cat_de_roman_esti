// games.ts — the single registry for the four word games: routes, titles, accents,
// icons, blurbs. Home cards, routing, HUDs and score views all read from here so a
// game's identity is defined exactly once. (`contexto` stays the internal/API/score
// key for Cald sau Rece; only its URL is the user-facing name.)

export type GameKey = "alchimie" | "contexto" | "lant" | "conexiuni";

export interface GameDef {
  key: GameKey;
  /** SPA route (also what players share/bookmark). */
  path: string;
  title: string;
  /** The familiar concept it riffs on. */
  tag: string;
  blurb: string;
  /** Game accent color (mirrors --game-<key> in arcade.css). */
  accent: string;
  /** Softer companion for gradients / halos. */
  glow: string;
  icon: string;
}

export const GAMES: GameDef[] = [
  {
    key: "alchimie",
    path: "/alchimie",
    title: "Alchimie",
    tag: "à la Infinite Craft",
    blurb:
      "Combina doua concepte ca sa descoperi unul nou. Creste-ti inventarul pas cu pas pana cand croiesti conceptul-tinta.",
    accent: "#c689ff",
    glow: "#e3ccff",
    icon: "⚗️",
  },
  {
    key: "contexto",
    path: "/cald-rece",
    title: "Cald sau Rece",
    tag: "à la Contexto",
    blurb:
      "Un concept secret te asteapta. Fiecare incercare iti spune cat de aproape esti — de la inghetat la fierbinte. Gaseste-l.",
    accent: "#ff8a5c",
    glow: "#ffc9a3",
    icon: "🔥",
  },
  {
    key: "lant",
    path: "/lant",
    title: "Lantul Cuvintelor",
    tag: "à la The Wiki Game",
    blurb:
      "De la START la TINTA: scrie de fiecare data un concept legat de cel curent si sari din cuvant in cuvant, in cat mai putine miscari.",
    accent: "#4fd8e0",
    glow: "#a9f0f5",
    icon: "🔗",
  },
  {
    key: "conexiuni",
    path: "/conexiuni",
    title: "Conexiuni",
    tag: "à la NYT Connections",
    blurb:
      "Saisprezece concepte, patru categorii ascunse. Grupeaza-le cate patru — ai voie la patru greseli.",
    accent: "#54e39d",
    glow: "#abf2cd",
    icon: "🧩",
  },
];

export function gameByKey(key: GameKey): GameDef {
  const def = GAMES.find((g) => g.key === key);
  if (!def) throw new Error(`unknown game: ${key}`);
  return def;
}

export const GAME_TITLES: Record<GameKey, string> = Object.fromEntries(
  GAMES.map((g) => [g.key, g.title]),
) as Record<GameKey, string>;
