// GameShell — a shared header for every word game so the arcade feels cohesive.
//
// Renders a consistent "← Ieși" navigation button (left) and a right-aligned slot for the
// game's status badges (moves, difficulty, lives, …). The optional `accent` tints the
// title so each game keeps its own colour identity while sharing the exact same
// layout, tap-targets, and accessibility wiring.

import { useLayoutEffect, useRef, type ReactNode } from "react";
import { Button } from "@roedu/ui";
import type { GameKey } from "../games";
import { GameHelp } from "./GameHelp";

export function GameShell({
  onExit,
  accent,
  title,
  children,
  busy = false,
  helpGame,
}: {
  /** Return to the arcade home. */
  onExit: () => void;
  /** Game accent colour (used for the title glyph + a11y labels). */
  accent?: string;
  /** Optional small title shown next to the exit button. */
  title?: ReactNode;
  /** Right-aligned status badges. */
  children?: ReactNode;
  /** Disable the exit action while the host is creating or replacing a game. */
  busy?: boolean;
  /** Answer-free rules below the header for an active round. */
  helpGame?: GameKey;
}) {
  const headerRef = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
    const header = headerRef.current;
    const scroller = header?.closest<HTMLElement>(".screen-pad");
    if (!header || !scroller) return;
    // Badges can wrap again after a clue, font load, resize or text zoom. Keep
    // the other sticky controls below the actual header, including those cases.
    const measure = () => scroller.style.setProperty(
      "--game-shell-header-height", `${header.offsetHeight}px`,
    );
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(header);
    return () => {
      observer.disconnect();
      scroller.style.removeProperty("--game-shell-header-height");
    };
  }, []);

  return (
    <>
      <div ref={headerRef} className="row spread game-shell-header" style={{ gap: 12 }}>
        <div className="row game-shell-main" style={{ gap: 10, alignItems: "center" }}>
          <Button
            variant="secondary"
            size="sm"
            onClick={onExit}
            disabled={busy}
            aria-busy={busy || undefined}
            aria-label={busy ? "Se pregătește jocul" : "Ieși la lista de jocuri"}
          >
            <span aria-hidden>{busy ? "⏳" : "←"}</span>{" "}
            {busy ? "Se pregătește…" : "Ieși"}
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
      {helpGame && <GameHelp game={helpGame} />}
    </>
  );
}
