// Hud — the uniform status cluster next to the GameShell header: small stat
// badges (moves, lives, difficulty, …) that look identical across all four games.

import type { ReactNode } from "react";
import { Badge } from "@roedu/ui";

export function StatBadge({
  label,
  value,
  accent,
  title,
}: {
  /** Tiny uppercase caption (e.g. "MUTARI"). */
  label: string;
  value: ReactNode;
  /** Game accent; defaults to the neutral badge look. */
  accent?: string;
  title?: string;
}) {
  return (
    <Badge color={accent} title={title} className="stat-badge">
      <span className="stat-badge-label">{label}</span>
      <span className="stat-badge-value">{value}</span>
    </Badge>
  );
}

/** Right-aligned wrap row for StatBadges + small actions inside a GameShell. */
export function Hud({ children }: { children: ReactNode }) {
  return (
    <div className="row wrap" style={{ gap: 8, alignItems: "center" }}>
      {children}
    </div>
  );
}
