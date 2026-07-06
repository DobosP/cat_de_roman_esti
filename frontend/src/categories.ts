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
  literatura: { label: "Literatura", color: "#8ec5ff", glow: "#bfe0ff" },
  geografie: { label: "Geografie", color: "#5fd99b", glow: "#a7f0c8" },
  personalitati: { label: "Personalitati", color: "#f178b6", glow: "#ffb0d8" },
  arta_cultura: { label: "Arta & Cultura", color: "#c08bff", glow: "#dcc0ff" },
  stiinta: { label: "Stiinta", color: "#56d4dd", glow: "#a3eef2" },
  societate: { label: "Societate", color: "#ffd166", glow: "#ffe6a8" },
  limba: { label: "Limba", color: "#7bdff2", glow: "#b8eef9" },
  mixed: { label: "Mixt", color: "#b8b8d1", glow: "#e0e0f0" },
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
