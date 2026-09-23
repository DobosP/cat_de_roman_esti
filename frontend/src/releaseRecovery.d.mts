export const RELEASE_RECOVERY_KEY: string;

interface ReleaseRecoveryEvent {
  preventDefault(): void;
}

interface ReleaseRecoveryTarget {
  addEventListener(
    type: "vite:preloadError",
    listener: (event: ReleaseRecoveryEvent) => void,
  ): void;
  removeEventListener(
    type: "vite:preloadError",
    listener: (event: ReleaseRecoveryEvent) => void,
  ): void;
}

interface ReleaseRecoveryStorage {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
}

interface ReleaseRecoveryLocation {
  pathname: string;
  search: string;
  hash: string;
  reload(): void;
}

interface InstallReleaseRecoveryOptions {
  target?: ReleaseRecoveryTarget;
  storage?: ReleaseRecoveryStorage;
  location?: ReleaseRecoveryLocation;
}

export function installReleaseRecovery(
  options?: InstallReleaseRecoveryOptions,
): () => void;
