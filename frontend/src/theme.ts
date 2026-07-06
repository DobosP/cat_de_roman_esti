// theme.ts — cat_de_roman_esti's bespoke identity as a @roedu/ui ThemeProvider override.
// "Arcada de noapte": a deep violet night sky, hot-coral primary energy, sunny-gold
// accents. Only the identity lives here; anything structural belongs in the shared
// design system, and per-game accent colors live in src/games.ts.

import type { ThemeOverride } from "@roedu/ui";

export const catTheme: ThemeOverride = {
  color: {
    bg: "#0d0b20",
    surface: "rgba(32, 28, 64, 0.66)",
    surfaceMuted: "rgba(20, 17, 44, 0.55)",
    text: "#f4f2ff",
    textMuted: "#a8a1cc",
    border: "rgba(168, 156, 236, 0.2)",
    primary: "#ff5470",
    primaryText: "#2b0714",
    accent: "#ffd166",
    danger: "#ff4d6d",
    success: "#3ddc97",
    focus: "#ffd166",
  },
  font: {
    heading: "'Fredoka Variable', 'Fredoka', system-ui, sans-serif",
    body: "'Inter Variable', 'Inter', system-ui, sans-serif",
  },
  radius: {
    sm: "10px",
    md: "16px",
    lg: "24px",
    pill: "999px",
  },
  shadow: {
    sm: "0 2px 10px rgba(4, 2, 18, 0.4)",
    md: "0 12px 32px -10px rgba(4, 2, 18, 0.6)",
    lg: "0 24px 64px -16px rgba(4, 2, 18, 0.8)",
  },
};
