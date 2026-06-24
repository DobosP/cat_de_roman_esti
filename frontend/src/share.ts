// share.ts — deterministic local share helpers. The server owns the game result text;
// the client wraps it with a stable app URL + puzzle id for a richer copy payload.
// Clipboard writes use the async API with a hidden-textarea fallback and never throw.

export interface SharePayloadOptions {
  gameTitle: string;
  serverShare: string;
  score?: number;
  puzzleKey?: string | null;
  appUrl?: string;
}

export function appUrl(): string {
  if (typeof window === "undefined") return "cat_de_roman_esti";
  return `${window.location.origin}${window.location.pathname}`;
}

export function stableKey(parts: Array<string | number | null | undefined>): string {
  return parts
    .filter((part): part is string | number => part !== null && part !== undefined && part !== "")
    .map((part) => String(part).trim().toLowerCase())
    .join(":");
}

export function buildSharePayload({
  gameTitle,
  serverShare,
  score,
  puzzleKey,
  appUrl: url = appUrl(),
}: SharePayloadOptions): string {
  const lines = [serverShare.trim(), "", `Joaca: ${url}`];
  if (score !== undefined) lines.push(`Scor: ${score}`);
  if (puzzleKey) lines.push(`Puzzle: ${gameTitle} · ${puzzleKey}`);
  return lines.join("\n");
}

export async function copyResult(text: string): Promise<boolean> {
  try {
    if (typeof navigator !== "undefined" && navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch {
    /* fall through to the legacy path */
  }
  try {
    if (typeof document === "undefined") return false;
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    const ok = document.execCommand("copy");
    document.body.removeChild(ta);
    return ok;
  } catch {
    return false;
  }
}

/** Today's local date as YYYY-MM-DD — pass to a game's ?daily= for a shared daily puzzle. */
export function todayLocal(): string {
  const d = new Date();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${m}-${day}`;
}
