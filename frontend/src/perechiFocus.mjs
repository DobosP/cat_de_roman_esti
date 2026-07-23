// Preserve board-order keyboard flow when a solved Perechi pair leaves the grid.
export function nextActiveTileId(tiles, afterId) {
  const afterIndex = tiles.findIndex((tile) => tile.id === afterId);
  const splitAt = afterIndex < 0 ? 0 : afterIndex + 1;
  const wrappedOrder = [...tiles.slice(splitAt), ...tiles.slice(0, splitAt)];
  return wrappedOrder.find((tile) => !tile.solved)?.id ?? null;
}
