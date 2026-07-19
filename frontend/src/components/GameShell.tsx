// GameShell — a shared header for every word game so the arcade feels cohesive.
//
// Renders a consistent "← Meniu" back-button (left) and a right-aligned slot for the
// game's status badges (moves, difficulty, lives, …). The optional `accent` tints the
// title so each game keeps its own colour identity while sharing the exact same
// layout, tap-targets, and accessibility wiring.

import type { ReactNode } from "react";
import { Button } from "@roedu/ui";

export function GameShell({
  onExit,
  accent,
  title,
  children,
  busy = false,
}: {
  /** Return to the arcade home. */
  onExit: () => void;
  /** Game accent colour (used for the title glyph + a11y labels). */
  accent?: string;
  /** Optional small title shown next to the back-button. */
  title?: ReactNode;
  /** Right-aligned status badges. */
  children?: ReactNode;
  /** Disable the menu action while the host is creating or replacing a game. */
  busy?: boolean;
}) {
  return (
    <div className="row spread game-shell-header" style={{ gap: 12 }}>
      <div className="row game-shell-main" style={{ gap: 10, alignItems: "center" }}>
        <Button
          variant="secondary"
          size="sm"
          onClick={onExit}
          disabled={busy}
          aria-busy={busy || undefined}
          aria-label={busy ? "Se pregătește jocul" : "Înapoi la meniu"}
        >
          <span aria-hidden>{busy ? "⏳" : "←"}</span>{" "}
          {busy ? "Se pregătește…" : "Meniu"}
        </Button>
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
        <div className="game-shell-status">
          {children}
        </div>
      )}
    </div>
  );
}
