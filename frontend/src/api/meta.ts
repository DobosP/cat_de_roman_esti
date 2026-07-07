// Typed wrapper for the category taxonomy endpoint (ADR-0011). Fetched once per
// page load and shared by every game's CategoryPicker — availability decides which
// categories a game can actually start (curated content or a minable node pool).

import { getJson } from "./client";

export type GameKey = "alchimie" | "contexto" | "lant" | "conexiuni";

export interface CategoryInfo {
  key: string;
  label: string;
  kind: "pop" | "serious";
  node_count: number;
  curated: Record<GameKey, number>;
  available: Record<GameKey, boolean>;
}

let cached: Promise<CategoryInfo[]> | null = null;

/** GET /api/categories — cached for the page's lifetime (taxonomy is static). */
export function getCategories(): Promise<CategoryInfo[]> {
  if (!cached) {
    cached = getJson<{ categories: CategoryInfo[] }>("/api/categories")
      .then((body) => body.categories)
      .catch((err) => {
        cached = null; // allow a retry on the next screen visit
        throw err;
      });
  }
  return cached;
}
