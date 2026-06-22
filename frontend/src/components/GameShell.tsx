// GameShell — a shared header for every word game so the arcade feels cohesive.
//
// Renders a consistent "← Meniu" back-button (left) and a right-aligned slot for the
// game's status badges (moves, difficulty, lives, …). The optional `accent` tints the
// back-button hover/title so each game keeps its own colour identity while sharing the
// exact same layout, tap-targets, and accessibility wiring.

import type { ReactNode } from "react";

export function GameShell({
  onExit,
  accent,
  title,
  children,
}: {
  /** Return to the arcade home. */
  onExit: () => void;
  /** Game accent colour (used for the title glyph + a11y labels). */
  accent?: string;
  /** Optional small title shown next to the back-button. */
  title?: ReactNode;
  /** Right-aligned status badges. */
  children?: ReactNode;
}) {
  return (
    <div className="row spread wrap game-shell-header" style={{ gap: 12 }}>
      <div className="row" style={{ gap: 10, alignItems: "center" }}>
        <button
          type="button"
          className="btn btn-ghost"
          onClick={onExit}
          aria-label="Inapoi la meniu"
        >
          <span aria-hidden>←</span> Meniu
        </button>
        {title && (
          <strong
            className="game-shell-title"
            style={{ fontFamily: "var(--font-display)", color: accent, fontSize: "1.05rem" }}
          >
            {title}
          </strong>
        )}
      </div>
      {children && (
        <div className="row wrap" style={{ gap: 8, alignItems: "center" }}>
          {children}
        </div>
      )}
    </div>
  );
}
