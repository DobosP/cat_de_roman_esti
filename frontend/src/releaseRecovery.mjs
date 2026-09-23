// Recover a browser tab that was left open across a deployment.
//
// Vite lazy routes point at content-hashed chunks. When a release removes the
// previous hashes, an already-open tab can request a chunk that no longer exists.
// Vite emits `vite:preloadError` before the rejected dynamic import reaches React.
// Reload once so the tab picks up the current index and chunk graph; the
// sessionStorage marker prevents a genuinely broken deployment from looping.

export const RELEASE_RECOVERY_KEY = "cat_release_recovery_v1";

function pageKey(location) {
  return `${location.pathname}${location.search}${location.hash}`;
}

export function installReleaseRecovery({
  target = globalThis.window,
  storage,
  location = globalThis.location,
} = {}) {
  // Even reading window.sessionStorage can throw before any Storage method runs.
  if (storage === undefined) {
    try {
      storage = globalThis.sessionStorage;
    } catch {
      // Startup must work when the browser denies access to storage entirely.
    }
  }
  // Retain one last-failed-page string for this tab session. A timer cannot prove
  // that a pending lazy chunk loaded: clearing the marker would let slow failures
  // reload every new document. Explicit reload and navigation remain available.
  let reloadRequested = false;

  const recover = (event) => {
    if (reloadRequested) {
      event.preventDefault();
      return;
    }
    const failedPageKey = pageKey(location);
    let shouldReload = false;
    try {
      if (storage.getItem(RELEASE_RECOVERY_KEY) === failedPageKey) {
        shouldReload = false;
      } else {
        storage.setItem(RELEASE_RECOVERY_KEY, failedPageKey);
        shouldReload = storage.getItem(RELEASE_RECOVERY_KEY) === failedPageKey;
      }
    } catch {
      // An in-memory guard disappears on reload. Without a durable marker, a
      // broken chunk would therefore cause an endless cross-document reload loop.
    }
    if (shouldReload) {
      event.preventDefault();
      reloadRequested = true;
      location.reload();
    }
  };

  target.addEventListener("vite:preloadError", recover);
  return () => target.removeEventListener("vite:preloadError", recover);
}
