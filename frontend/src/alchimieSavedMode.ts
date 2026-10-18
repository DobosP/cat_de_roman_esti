/** Only absence selects the old saved challenge; all exploration bytes stay owned by Explore. */
export function legacyAlchimieResume(storage?: Pick<Storage, "getItem"> | null): boolean {
  try {
    const saved = storage === undefined ? localStorage : storage;
    return Boolean(saved?.getItem("cat_active_game_v1_alchimie"))
      && saved?.getItem("cat_alchimie_exploration_v1") === null;
  } catch { return false; }
}
