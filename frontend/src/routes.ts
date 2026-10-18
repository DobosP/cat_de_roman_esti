// routes.ts — all M3 screen paths. The current shell also owns document
// fallbacks; only known app links are intercepted so native account/legal/API
// navigation keeps its server owner. App handles a known trailing slash and
// sends an unknown document path Home without broad path normalization.

export const PORTED_PATHS = Object.freeze(["/", "/intrusul", "/perechi", "/conexiuni", "/alchimie", "/cald-rece", "/lant", "/clasament"] as const);
export type PortedPath = (typeof PORTED_PATHS)[number];

/** Exact document path match; queries and hashes never select. */
export function portedPath(pathname: string): pathname is PortedPath {
  return (PORTED_PATHS as readonly string[]).includes(pathname);
}

/** Same-origin links the location provider may handle client-side. */
export const PORTED_LINK_SCOPE = /^\/(?:(?:intrusul|perechi|conexiuni|alchimie|cald-rece|lant|clasament)\/?)?(?:[?#]|$)/;

/** Target URL's path without its query/hash, for a ported-set decision. */
export function pathOf(url: string): string {
  return url.split(/[?#]/, 1)[0] ?? url;
}
