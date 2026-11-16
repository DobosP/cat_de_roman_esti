import { useEffect, useState } from "preact/hooks";
import { getCategories, type CategoryInfo, type Difficulty } from "../api/meta";
import type { GameKey } from "../games";

interface Options {
  difficulty: Difficulty;
  category: string | null;
}

export function FreeRoundOptions({ game, value, onChange }: {
  game: GameKey;
  value: Options;
  onChange: (value: Options) => void;
}) {
  const [categories, setCategories] = useState<CategoryInfo[]>([]);
  useEffect(() => {
    let mounted = true;
    void getCategories().then((items) => { if (mounted) setCategories(items); }, () => {});
    return () => { mounted = false; };
  }, []);
  const derived = game === "intrusul" || game === "perechi";
  const available = (item: CategoryInfo, difficulty: Difficulty) => derived
    // The derived games use their curated, fixed-difficulty shelves.
    ? item.key !== "mixed" && (game === "intrusul" || !["gastronomie", "meme_net"].includes(item.key))
    : item.available_by_difficulty[game]?.[difficulty];
  return (
    <>
      {!derived && (
        <label className="game-help-select">
          Dificultate
          <select className="field" value={value.difficulty} onChange={(event) => {
            const difficulty = event.currentTarget.value as Difficulty;
            const category = categories.some((item) => item.key === value.category && available(item, difficulty))
              ? value.category : null;
            onChange({ difficulty, category });
          }}>
            <option value="usor">Ușor</option>
            <option value="normal">Normal</option>
            <option value="greu">Greu</option>
          </select>
        </label>
      )}
      {categories.length > 0 && (
        <label className="game-help-select">
          Temă
          <select className="field" value={value.category ?? ""} onChange={(event) => {
            onChange({ ...value, category: event.currentTarget.value || null });
          }}>
            <option value="">Toate temele</option>
            {categories.filter((item) => available(item, value.difficulty)).map((item) => (
              <option key={item.key} value={item.key}>{item.label}</option>
            ))}
          </select>
        </label>
      )}
    </>
  );
}
