// Recover a browser tab that was left open across a deployment.
//
// Vite lazy routes point at content-hashed chunks. When a release removes the
// previous hashes, an already-open tab can request a chunk that no longer exists.
// Vite emits `vite:preloadError` before the rejected dynamic import reaches React.
// Reload once so the tab picks up the current index and chunk graph; the
// sessionStorage marker prevents a genuinely broken deployment from looping.

export const RELEASE_RECOVERY_KEY = "cat_release_recovery_v1";
export const RELEASE_RECOVERY_RESET_MS = 10_000;

function pageKey(location) {
  return `${location.pathname}${location.search}${location.hash}`;
}

export function installReleaseRecovery({
  target = globalThis.window,
  storage = globalThis.sessionStorage,
  location = globalThis.location,
  schedule = globalThis.setTimeout.bind(globalThis),
} = {}) {
  const loadedPageKey = pageKey(location);

  try {
    if (storage.getItem(RELEASE_RECOVERY_KEY) === loadedPageKey) {
      schedule(() => {
        try {
          if (storage.getItem(RELEASE_RECOVERY_KEY) === loadedPageKey) {
            storage.removeItem(RELEASE_RECOVERY_KEY);
          }
        } catch {
          // Storage is best-effort; a successful current bundle needs no recovery.
        }
      }, RELEASE_RECOVERY_RESET_MS);
    }
  } catch {
    // Safari private mode and hardened browsers may deny sessionStorage.
  }

  const recover = (event) => {
    event.preventDefault();
    const failedPageKey = pageKey(location);
    let shouldReload = true;
    try {
      if (storage.getItem(RELEASE_RECOVERY_KEY) === failedPageKey) {
        shouldReload = false;
      } else {
        storage.setItem(RELEASE_RECOVERY_KEY, failedPageKey);
      }
    } catch {
      // Without storage, a single reload is still the most useful recovery.
    }
    if (shouldReload) location.reload();
  };

  target.addEventListener("vite:preloadError", recover);
  return () => target.removeEventListener("vite:preloadError", recover);
}
