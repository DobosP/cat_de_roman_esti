import { useEffect, useState } from "preact/hooks";
import type { ToastKind } from "@roedu/ui";
import intrusul from "../art/intrusul.svg";
import perechi from "../art/perechi.svg";
import conexiuni from "../art/conexiuni.svg";
import lant from "../art/lant.svg";
import contexto from "../art/cald-rece.svg";
import alchimie from "../art/alchimie.svg";
import { dailyStatus, localDay } from "../entry";
import { gameByKey } from "../games";
import { lazyScreen } from "../lazyScreen";
import { sound } from "../sound";
import { currentTheme, toggleTheme } from "../theme";

const Results = lazyScreen(() => import("../components/ResultsHistory"));
const cards = [
  { key: "intrusul", image: intrusul, description: "Unul nu se potrivește." },
  { key: "perechi", image: perechi, description: "Potrivește câte două." },
  { key: "conexiuni", image: conexiuni, description: "Patru grupuri ascunse." },
  { key: "lant", image: lant, description: "Din cuvânt în cuvânt, până la țintă." },
  { key: "contexto", image: contexto, description: "Ghicește cuvântul secret." },
  { key: "alchimie", image: alchimie, description: "Combină cuvinte, creează altele." },
] as const;

export default function Home({ onToast }: { onToast: (message: string, kind?: ToastKind) => void }) {
  const [theme, setTheme] = useState(currentTheme);
  const [resultsOpen, setResultsOpen] = useState(false);
  const [, refresh] = useState(0);
  useEffect(() => {
    const media = matchMedia("(prefers-color-scheme: dark)");
    const synchronizeTheme = () => setTheme(currentTheme());
    const synchronizeDay = () => refresh((value) => value + 1);
    media.addEventListener("change", synchronizeTheme);
    document.addEventListener("visibilitychange", synchronizeDay);
    window.addEventListener("storage", synchronizeDay);
    return () => {
      media.removeEventListener("change", synchronizeTheme);
      document.removeEventListener("visibilitychange", synchronizeDay);
      window.removeEventListener("storage", synchronizeDay);
    };
  }, []);
  const day = localDay();
  return (
    <main className="home-screen">
      <header className="home-header">
        <div className="home-tools">
          <button type="button" className="home-icon" onClick={() => setTheme(toggleTheme())}
            aria-label={theme === "light" ? "Trece pe modul întunecat" : "Trece pe modul luminos"}>
            <svg viewBox="0 0 24 24" aria-hidden="true">
              {theme === "light" ? <path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z" /> :
                <path d="M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zM12 2v3m0 14v3M2 12h3m14 0h3M5 5l2 2m10 10 2 2M5 19l2-2M17 7l2-2" />}
            </svg>
          </button>
          <button type="button" className="home-icon" aria-label="Rezultatele mele" aria-haspopup="dialog"
            onClick={() => setResultsOpen(true)}>
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M8 4h8v5a4 4 0 0 1-8 0zM8 6H5a3 3 0 0 0 3 4M16 6h3a3 3 0 0 1-3 4M12 13v4M8 20h8M9 17h6" />
            </svg>
          </button>
        </div>
        <h1>Cât de român ești?</h1>
        <p>Șase jocuri scurte din cultura și viața românească.</p>
      </header>
      <div className="games-grid">
        {cards.map(({ key, image, description }) => {
          const game = gameByKey(key);
          return (
            <a key={key} href={game.path} className={`game-card game-color-${key}`}
              onClick={() => { sound.unlockAudio(); sound.playSelect(); }}>
              <img src={image} alt="" width="160" height="110" />
              <strong>{game.title}</strong>
              <span>{description}</span>
              {dailyStatus(key, day).done && <span className="game-card-done">✓ Gata azi</span>}
            </a>
          );
        })}
      </div>
      <p className="home-daily-note">Prima rundă de azi e jocul zilei, la fel pentru toată lumea. După ea, joci cât vrei.</p>
      {resultsOpen && <Results onClose={() => setResultsOpen(false)} onToast={onToast} />}
    </main>
  );
}
