import { Link } from "react-router-dom";

export function AlchimieModes({ mode, busy = false }: { mode: "explore" | "challenges"; busy?: boolean }) {
  return (
    <nav className="alchemy-modes" aria-label="Modul Alchimie" inert={busy}>
      {([ ["explore", "Explorează"], ["challenges", "Provocări"] ] as const).map(([key, label]) =>
        mode === key
          ? <span key={key} aria-current="page">{label}</span>
          : <Link key={key} to={`/alchimie?mode=${key}`}>{label}</Link>,
      )}
    </nav>
  );
}
