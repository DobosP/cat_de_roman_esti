// useAuth — loads /api/me once, exposes auth state + a refresh, and keeps score-sync in
// step with the session's save capability. Anonymous/offline play needs none of this; the
// hook degrades to {accounts_enabled:false} if /api/me is unreachable or disabled.

import { useCallback, useEffect, useState } from "react";
import { getMe, type MeResponse } from "../api/auth";
import { setScoreSyncEnabled, syncAllLocalOnce } from "../scoreSync";

const DISABLED: MeResponse = { accounts_enabled: false, authenticated: false, user: null };

export interface UseAuth {
  me: MeResponse | null;
  loading: boolean;
  refresh: () => Promise<void>;
}

export function useAuth(): UseAuth {
  const [me, setMe] = useState<MeResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const next = await getMe();
      setMe(next);
      const canSave = Boolean(next.user?.can_save_progress);
      setScoreSyncEnabled(canSave);
      if (canSave) void syncAllLocalOnce();
    } catch {
      setMe(DISABLED);
      setScoreSyncEnabled(false);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { me, loading, refresh };
}
