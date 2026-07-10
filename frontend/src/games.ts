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
    tag: "Combină și descoperă",
    blurb:
      "Combină două concepte ca să descoperi unul nou. Crește-ți inventarul pas cu pas până când făurești conceptul-țintă.",
    accent: "#c689ff",
    glow: "#e3ccff",
    icon: "⚗️",
  },
  {
    key: "contexto",
    path: "/cald-rece",
    title: "Cald sau Rece",
    tag: "Mai cald, mai rece",
    blurb:
      "Un concept secret te așteaptă. Fiecare încercare îți spune cât de aproape ești — de la înghețat la fierbinte. Găsește-l.",
    accent: "#ff8a5c",
    glow: "#ffc9a3",
    icon: "🔥",
  },
  {
    key: "lant",
    path: "/lant",
    title: "Lanțul Cuvintelor",
    tag: "Leagă conceptele",
    blurb:
      "De la START la ȚINTĂ: scrie de fiecare dată un concept legat de cel curent și sari din cuvânt în cuvânt, în cât mai puține mișcări.",
    accent: "#4fd8e0",
    glow: "#a9f0f5",
    icon: "🔗",
  },
  {
    key: "conexiuni",
    path: "/conexiuni",
    title: "Conexiuni",
    tag: "Găsește grupurile",
    blurb:
      "Șaisprezece concepte, patru categorii ascunse. Grupează-le câte patru — ai voie la patru greșeli.",
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
