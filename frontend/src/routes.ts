// routes.ts — the M2 pilot route set served by this Preact shell (ADR-0197).
// The Go server serves exactly these document paths from the current bundle
// and every other path from the frozen legacy bundle, so the shell must leave
// every other navigation to the browser: a client-side route into an unported
// path would render nothing the server does not already own.

export const PORTED_PATHS = Object.freeze(["/", "/intrusul", "/perechi", "/conexiuni"] as const);
export type PortedPath = (typeof PORTED_PATHS)[number];

/** Exact document path match; queries and hashes never select. */
export function portedPath(pathname: string): pathname is PortedPath {
  return (PORTED_PATHS as readonly string[]).includes(pathname);
}

/** Same-origin links the location provider may handle client-side. */
export const PORTED_LINK_SCOPE = /^\/(?:intrusul|perechi|conexiuni)?(?:[?#]|$)/;

/** Target URL's path without its query/hash, for a ported-set decision. */
export function pathOf(url: string): string {
  return url.split(/[?#]/, 1)[0] ?? url;
}
