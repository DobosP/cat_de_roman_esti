// CategoryPicker — chip row for choosing a game's category/theme (ADR-0011).
// "Mix clasic" (no category) keeps the historical mined behavior; the rest come
// from /api/categories filtered to what THIS game can actually start. Renders
// nothing while loading or when the endpoint is unavailable — the picker is an
// additive layer, never a blocker.

import { useEffect, useState } from "react";
import { categoryStyle } from "../categories";
import { getCategories, type CategoryInfo, type GameKey } from "../api/meta";

export function CategoryPicker({
  game,
  value,
  onChange,
  accent,
}: {
  game: GameKey;
  /** Selected category key, or null for the classic mix. */
  value: string | null;
  onChange: (key: string | null) => void;
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

  const playable = (categories ?? []).filter((c) => c.available[game]);
  if (playable.length === 0) return null;

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

  const pop = playable.filter((c) => c.kind === "pop");
  const serious = playable.filter((c) => c.kind === "serious");

  return (
    <div className="col" style={{ gap: 8 }}>
      <span
        className="faint"
        style={{ letterSpacing: "0.08em", fontSize: "0.72rem" }}
        id="category-label"
      >
        CATEGORIE
      </span>
      <div className="row wrap" role="group" aria-labelledby="category-label" style={{ gap: 6 }}>
        {chip(null, "Mix clasic", accent)}
        {pop.map((c) => chip(c.key, categoryStyle(c.key).label, categoryStyle(c.key).color, c.kind))}
        {serious.map((c) =>
          chip(c.key, categoryStyle(c.key).label, categoryStyle(c.key).color, c.kind),
        )}
      </div>
    </div>
  );
}
