import type { ComponentChildren } from "preact";

/** Starting uses sensible defaults; selecting a theme or mode is optional. */
export function GameSetupOptions({ children, summary = "Personalizează jocul" }: { children: ComponentChildren; summary?: ComponentChildren }) {
  return (
    <details className="game-setup-options">
      <summary>{summary}</summary>
      <div className="game-setup-options-content">{children}</div>
    </details>
  );
}
