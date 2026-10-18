import "../styles/shared-game-controls.css";
// DifficultyPicker — a shared segmented control for the three difficulty tiers so every
// game's intro card picks difficulty the same way (same look, tap-targets, a11y wiring).
//
// Generic over the difficulty id type so each game can keep its own union ("usor" | …).
// Presentational + controlled: the host owns the selected value and the onChange.

export interface DifficultyOption<T extends string> {
  id: T;
  label: string;
  /** Short gloss shown under the label (e.g. "echilibrat"). */
  hint?: string;
}

export function DifficultyPicker<T extends string>({
  options,
  value,
  onChange,
  label = "DIFICULTATE",
}: {
  options: DifficultyOption<T>[];
  value: T;
  onChange: (id: T) => void;
  label?: string;
}) {
  return (
    <div className="col difficulty-picker">
      <span
        className="faint difficulty-picker-label"
        id="difficulty-label"
      >
        {label}
      </span>
      <div className="segment" role="group" aria-labelledby="difficulty-label">
        {options.map((o) => (
          <button
            key={o.id}
            type="button"
            className="segment-item"
            aria-pressed={value === o.id}
            onClick={() => onChange(o.id)}
          >
            <span>{o.label}</span>
            {o.hint && <span className="seg-hint">{o.hint}</span>}
          </button>
        ))}
      </div>
    </div>
  );
}
