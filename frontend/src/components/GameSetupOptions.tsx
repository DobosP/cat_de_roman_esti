import type { ReactNode } from "react";
import "../styles/game-options.css";

/** Starting uses sensible defaults; selecting a theme or mode is optional. */
export function GameSetupOptions({ children, summary = "Personalizează jocul" }: { children: ReactNode; summary?: ReactNode }) {
  return (
    <details className="game-setup-options">
      <summary>{summary}</summary>
      <div className="game-setup-options-content">{children}</div>
    </details>
  );
}
