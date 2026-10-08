// CategoryPicker — chip row for choosing a game's category/theme (ADR-0011).
// The unfiltered mix (no category) keeps the curated-first default; the rest come
// from /api/categories filtered to what THIS game can actually start. Renders
// nothing while loading or when the endpoint is unavailable — the picker is an
// additive layer, never a blocker.

import { useEffect, useState } from "react";
import { categoryStyle } from "../categories";
import {
  getCategories,
  type CategoryInfo,
  type Difficulty,
  type GameKey,
} from "../api/meta";

export function CategoryPicker({
  game,
  difficulty,
  value,
  onChange,
  onInvalid,
  accent,
}: {
  game: GameKey;
  difficulty: Difficulty;
  /** Selected category key, or null for all available themes. */
  value: string | null;
  onChange: (key: string | null) => void;
  /** Silently clear a selection invalidated by a difficulty change. */
  onInvalid: () => void;
  accent: string;
}) {
  const [categories, setCategories] = useState<CategoryInfo[] | null>(null);

  useEffect(() => {
    let alive = true;
    getCategories()
      .then((cats) => {
        if (alive) setCategories(cats);
      })
      .catch(() => {
        if (alive) setCategories([]);
      });
    return () => {
      alive = false;
    };
  }, []);

  const visible = (categories ?? []).filter(
    (category) => category.available_by_difficulty[game][difficulty],
  );

  useEffect(() => {
    if (categories === null || categories.length === 0 || value === null) return;
    const selected = categories.find((category) => category.key === value);
    if (!selected?.available_by_difficulty[game][difficulty]) onInvalid();
  }, [categories, difficulty, game, onInvalid, value]);

  if (categories === null || categories.length === 0) return null;

  const chip = (
    key: string | null,
    label: string,
    color: string,
    kind?: "pop" | "serious",
  ) => {
    const selected = value === key;
    return (
      <button
        key={key ?? "__mix__"}
        type="button"
        className="chip"
        aria-pressed={selected}
        onClick={() => onChange(key)}
        title={kind === "pop" ? "Cultură pop" : undefined}
        style={{
          cursor: "pointer",
          borderColor: selected ? color : "var(--surface-border)",
          background: selected
            ? `color-mix(in srgb, var(--surface) 70%, ${color})`
            : undefined,
          fontWeight: selected ? 700 : 500,
          boxShadow: selected ? `0 0 14px -6px ${color}` : undefined,
        }}
      >
        {label}
      </button>
    );
  };

  const pop = visible.filter((category) => category.kind === "pop");
  const serious = visible.filter((category) => category.kind === "serious");
  const chipFor = (category: CategoryInfo) => {
    const style = categoryStyle(category.key);
    return chip(category.key, style.label, style.color, category.kind);
  };

  return (
    <div className="col" style={{ gap: 8 }}>
      <span
        className="faint"
        style={{ letterSpacing: "0.08em", fontSize: "0.72rem" }}
        id="category-label"
      >
        CATEGORIE
      </span>
      <div
        className="row wrap category-picker-options"
        role="group"
        aria-labelledby="category-label"
        style={{ gap: 6 }}
      >
        {chip(null, "Toate temele", accent)}
        {pop.map(chipFor)}
        {serious.map(chipFor)}
      </div>
      <span className="faint category-picker-note" style={{ fontSize: "0.72rem" }}>
        Tema se aplică doar jocurilor libere.
      </span>
    </div>
  );
}
