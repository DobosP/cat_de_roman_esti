// useDailyIntent — the circuit's `?challenge=daily` is a single-use hint. The
// first explicit start (daily or free) drops it with a replace navigation that
// keeps every other param; routes are keyed by pathname, so the screen stays
// mounted. preact-iso's location is `pathname + search`; the hash is read from
// the document so it survives the rewrite exactly as before.

import { useLocation } from "preact-iso";

export interface DailyIntent {
  active: boolean;
  consume: () => void;
}

export function useDailyIntent(): DailyIntent {
  const { url, route } = useLocation();
  const target = new URL(url, "http://local.invalid");
  const active = target.searchParams.get("challenge") === "daily";
  const consume = () => {
    const params = new URL(url, "http://local.invalid").searchParams;
    if (!params.has("challenge")) return;
    params.delete("challenge");
    const search = params.toString();
    const hash = typeof location === "undefined" ? "" : location.hash;
    route(`${target.pathname}${search ? `?${search}` : ""}${hash}`, true);
  };
  return { active, consume };
}
