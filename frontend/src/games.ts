// games.ts — the single registry for the six word games: routes, titles, accents,
// icons, blurbs. Home cards, routing, HUDs and score views all read from here so a
// game's identity is defined exactly once. (`contexto` stays the internal/API/score
// key for Cald sau Rece; only its URL is the user-facing name.)

export type GameKey =
  | "alchimie"
  | "intrusul"
  | "perechi"
  | "conexiuni"
  | "contexto"
  | "lant";

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
  /** Provisional first-play recommendation; never a board-quality score. */
  featured?: boolean;
}

export const GAMES: GameDef[] = [
  {
    key: "alchimie",
    path: "/alchimie",
    title: "Alchimie",
    tag: "Combină și descoperă",
    blurb: "Alege două concepte și făurește ținta.",
    accent: "#c689ff",
    glow: "#e3ccff",
    icon: "⚗️",
    featured: true,
  },
  {
    key: "intrusul",
    path: "/intrusul",
    title: "Intrusul",
    tag: "Găsește ce nu se potrivește",
    blurb: "Trei cuvinte au o legătură. Atinge intrusul.",
    accent: "#ffcf5c",
    glow: "#ffe7a3",
    icon: "🔎",
  },
  {
    key: "perechi",
    path: "/perechi",
    title: "Perechi",
    tag: "Potrivește câte două",
    blurb: "Atinge două cuvinte care merg împreună.",
    accent: "#ff78b7",
    glow: "#ffc4df",
    icon: "🧠",
  },
  {
    key: "conexiuni",
    path: "/conexiuni",
    title: "Conexiuni",
    tag: "Găsește grupurile",
    blurb: "Alege câte patru cuvinte care merg împreună.",
    accent: "#54e39d",
    glow: "#abf2cd",
    icon: "🧩",
  },
  {
    key: "contexto",
    path: "/cald-rece",
    title: "Cald sau Rece",
    tag: "Mai cald, mai rece",
    blurb: "Ghicește secretul urmărind căldura.",
    accent: "#ff8a5c",
    glow: "#ffc9a3",
    icon: "🔥",
  },
  {
    key: "lant",
    path: "/lant",
    title: "Lanțul Cuvintelor",
    tag: "Leagă conceptele",
    blurb: "Sari din cuvânt în cuvânt până la țintă.",
    accent: "#4fd8e0",
    glow: "#a9f0f5",
    icon: "🔗",
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
