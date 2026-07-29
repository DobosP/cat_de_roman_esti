export const RELEASE_RECOVERY_KEY: string;
export const RELEASE_RECOVERY_RESET_MS: number;

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
  removeItem(key: string): void;
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
  schedule?: (callback: () => void, delay: number) => unknown;
}

export function installReleaseRecovery(
  options?: InstallReleaseRecoveryOptions,
): () => void;
