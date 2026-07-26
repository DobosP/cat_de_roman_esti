import type { PerechiTile } from "./api/perechi";

export function nextActiveTileId(
  tiles: readonly PerechiTile[],
  afterId: string,
): string | null;
