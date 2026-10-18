import { Csp } from "./CspStyle";
// GameShell — a shared header for every word game so the arcade feels cohesive.
//
// Renders a consistent "← Ieși" navigation button (left) and a right-aligned slot for the
// game's status badges (moves, difficulty, lives, …). The optional `accent` tints the
// title so each game keeps its own colour identity while sharing the exact same
// layout, tap-targets, and accessibility wiring.

import type { ComponentChildren } from "preact";
import { useLayoutEffect, useRef } from "preact/hooks";
import { Button } from "@roedu/ui";
import type { GameHelpCopy } from "../gameHelp.mjs";
import { GameHelp } from "./GameHelp";

export function GameShell({
  onExit,
  accent,
  title,
  children,
  busy = false,
  help,
}: {
  /** Return to the arcade home. */
  onExit: () => void;
  /** Game accent colour (used for the title glyph + a11y labels). */
  accent?: string;
  /** Optional small title shown next to the exit button. */
  title?: ComponentChildren;
  /** Right-aligned status badges. */
  children?: ComponentChildren;
  /** Disable the exit action while the host is creating or replacing a game. */
  busy?: boolean;
  /** Answer-free rules below the header for an active round. */
  help?: GameHelpCopy;
}) {
  const headerRef = useRef<HTMLDivElement | null>(null);

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
      <div ref={headerRef} className="row spread game-shell-header">
        <div className="row game-shell-main">
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
            <Csp.strong
              className="game-shell-title"
              css={{ color: accent }}
            >
              {title}
            </Csp.strong>
          )}
        </div>
        {children && (
          <div className="game-shell-status">
            {children}
          </div>
        )}
      </div>
      {help && <GameHelp help={help} />}
    </>
  );
}
