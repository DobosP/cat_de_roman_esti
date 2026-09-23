// useDailyIntent — the circuit's `?challenge=daily` is a single-use hint. The
// first explicit start (daily or free) drops it with a replace navigation that
// keeps every other param (Alchimie's `mode=challenges`); routes are keyed by
// pathname, so the screen stays mounted.

import { useLocation, useNavigate } from "react-router-dom";

export interface DailyIntent {
  active: boolean;
  consume: () => void;
}

export function useDailyIntent(): DailyIntent {
  const location = useLocation();
  const navigate = useNavigate();
  const active = new URLSearchParams(location.search).get("challenge") === "daily";
  const consume = () => {
    const params = new URLSearchParams(location.search);
    if (!params.has("challenge")) return;
    params.delete("challenge");
    const search = params.toString();
    navigate({ pathname: location.pathname, search: search ? `?${search}` : "", hash: location.hash }, { replace: true });
  };
  return { active, consume };
}
