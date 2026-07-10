// categories.ts — KG category → color/label map, the single source of truth wherever
// TS needs a concrete category value (CSS variables are invisible to inline/JS code).
// Mirrors the --cat-* variables in styles/arcade.css.

export interface CategoryStyle {
  /** Human, Romanian-flavoured label. */
  label: string;
  /** Bright accent. */
  color: string;
  /** Softer companion for gradients / halos. */
  glow: string;
}

export const CATEGORY_STYLES: Record<string, CategoryStyle> = {
  istorie: { label: "Istorie", color: "#f4a259", glow: "#ffcaa0" },
  literatura: { label: "Literatură", color: "#8ec5ff", glow: "#bfe0ff" },
  geografie: { label: "Geografie", color: "#5fd99b", glow: "#a7f0c8" },
  personalitati: { label: "Personalități", color: "#f178b6", glow: "#ffb0d8" },
  arta_cultura: { label: "Artă și cultură", color: "#c08bff", glow: "#dcc0ff" },
  stiinta: { label: "Știință", color: "#56d4dd", glow: "#a3eef2" },
  societate: { label: "Societate", color: "#ffd166", glow: "#ffe6a8" },
  limba: { label: "Limbă", color: "#7bdff2", glow: "#b8eef9" },
  mixed: { label: "Toate temele", color: "#b8b8d1", glow: "#e0e0f0" },
  // pop-culture shelf (ADR-0011)
  muzica: { label: "Muzică", color: "#ff6f91", glow: "#ffb3c6" },
  film_tv: { label: "Film și seriale", color: "#7c83ff", glow: "#c0c4ff" },
  meme_net: { label: "Internet și meme", color: "#b5e48c", glow: "#d9f7be" },
  sport: { label: "Sport", color: "#f95738", glow: "#ffb59f" },
  viata_de_roman: { label: "Viața în România", color: "#e07a5f", glow: "#f2b9a7" },
  gastronomie: { label: "Gastronomie", color: "#d4a373", glow: "#ecd5b8" },
};

const FALLBACK: CategoryStyle = { label: "Necunoscut", color: "#9aa3b2", glow: "#c9d0db" };

export function categoryStyle(category: string): CategoryStyle {
  return CATEGORY_STYLES[category] ?? FALLBACK;
}

export function categoryColor(category: string): string {
  return categoryStyle(category).color;
}

export function categoryLabel(category: string): string {
  return categoryStyle(category).label;
}
