// Home — the arcade lobby: playful wordmark, one card per game (each with its own
// color identity), and the local records/history panel. Navigation is real URL
// routing; opening a game also unlocks the shared WebAudio context (user gesture).

import { useCallback, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { m } from "framer-motion";
import { Badge, Button, type ToastKind } from "@roedu/ui";
import { GAMES, GAME_TITLES, type GameDef, type GameKey } from "../games";
import { SoundToggle } from "../components/SoundToggle";
import { sound } from "../sound";
import {
  exportScores,
  importScores,
  scoreBoard,
  type GameScoreEntry,
  type ScoreEntry,
} from "../scores";
import { todayLocal } from "../share";

type HistoryTab = "top" | "today" | "recent";

const EASE = [0.22, 1, 0.36, 1] as const;
const TITLE_WORDS = ["Cât", "de", "român", "ești?"];

export default function Home({
  onToast,
}: {
  onToast: (message: string, kind?: ToastKind) => void;
}) {
  const navigate = useNavigate();
  const [historyTab, setHistoryTab] = useState<HistoryTab>("top");
  const [gameFilter, setGameFilter] = useState<GameKey | "all">("all");
  const [board, setBoard] = useState(() => scoreBoard());
  const fileRef = useRef<HTMLInputElement>(null);
  const today = todayLocal();

  const totals = useMemo(
    () => GAMES.map((game) => ({ ...game, record: board[game.key] })),
    [board],
  );
  const allRows = useMemo(
    () =>
      Object.entries(board)
        .flatMap(([game, record]) => record.recent.map((entry) => ({ ...entry, game })))
        .sort((a, b) => b.at - a.at),
    [board],
  );
  const topRows = useMemo(
    () =>
      Object.entries(board)
        .flatMap(([game, record]) => (record.best ? [{ ...record.best, game }] : []))
        .sort((a, b) => b.score - a.score || b.at - a.at)
        .slice(0, 12),
    [board],
  );
  const todayRows = useMemo(
    () => allRows.filter((entry) => entry.daily === today).slice(0, 20),
    [allRows, today],
  );
  const recentRows = useMemo(
    () =>
      allRows
        .filter((entry) => gameFilter === "all" || entry.game === gameFilter)
        .slice(0, 30),
    [allRows, gameFilter],
  );
  const playedTotal = totals.reduce((sum, row) => sum + (row.record?.played ?? 0), 0);

  const openGame = useCallback(
    (game: GameDef) => {
      sound.unlockAudio();
      sound.playSelect();
      navigate(game.path);
    },
    [navigate],
  );

  const handleExport = useCallback(() => {
    const blob = new Blob([exportScores()], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `cat-de-roman-istoric-${todayLocal()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    onToast("Istoricul local a fost exportat.", "success");
  }, [onToast]);

  const handleImport = useCallback(
    async (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      event.target.value = "";
      if (!file) return;
      try {
        const outcome = importScores(await file.text());
        setBoard(scoreBoard());
        onToast(
          `Importat: ${outcome.entries} rezultate în ${outcome.games} jocuri.`,
          "success",
        );
      } catch (err) {
        onToast(err instanceof Error ? err.message : "Import invalid.", "error");
      }
    },
    [onToast],
  );

  return (
    <div className="screen-pad fill" style={{ overflowY: "auto" }}>
      <div className="container col" style={{ gap: 28, paddingBlock: 16 }}>
        <header className="col" style={{ gap: 10 }}>
          <div className="row spread" style={{ gap: 12, alignItems: "flex-start" }}>
            <h1 className="hero-title" aria-label="Cât de român ești?">
              {TITLE_WORDS.map((word, i) => (
                <m.span
                  key={word}
                  className={word === "ești?" ? "wordmark-gradient" : undefined}
                  initial={{ opacity: 0, y: 26, rotate: i % 2 ? 3 : -3 }}
                  animate={{ opacity: 1, y: 0, rotate: 0 }}
                  transition={{
                    delay: 0.05 + i * 0.08,
                    type: "spring",
                    stiffness: 320,
                    damping: 22,
                  }}
                >
                  {word}
                </m.span>
              ))}
            </h1>
            <SoundToggle />
          </div>
          <m.p
            className="muted"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.35, duration: 0.5 }}
            style={{ maxWidth: 640, fontSize: "1.05rem", margin: 0 }}
          >
            Patru jocuri românești. Alege unul și intri direct în ritm.
          </m.p>
        </header>

        <div className="games-grid">
          {GAMES.map((g, i) => (
            <m.button
              key={g.key}
              type="button"
              onClick={() => openGame(g)}
              aria-label={`Joacă ${g.title} — ${g.tag}`}
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 + 0.07 * i, duration: 0.4, ease: EASE }}
              whileHover={{ y: -5, rotate: i % 2 ? 0.4 : -0.4 }}
              whileTap={{ scale: 0.97 }}
              className="card game-card"
            >
              <div
                aria-hidden
                className="game-card-halo"
                style={{
                  background: `radial-gradient(190px 130px at 100% 0%, ${g.glow}26, transparent 70%)`,
                }}
              />
              <div className="row spread" style={{ position: "relative" }}>
                <span
                  className="game-card-icon"
                  aria-hidden
                  style={{ background: `${g.accent}1f`, borderColor: `${g.accent}55` }}
                >
                  {g.icon}
                </span>
                <Badge color={g.accent} size="sm">
                  {g.tag}
                </Badge>
              </div>
              <strong className="game-card-title" style={{ color: g.accent }}>
                {g.title}
              </strong>
              <p className="muted game-card-blurb">{g.blurb}</p>
              <span className="row game-card-footer" style={{ gap: 10 }}>
                <span className="game-card-cta" style={{ color: g.accent }}>
                  Joacă →
                </span>
                {board[g.key]?.best && (
                  <span className="faint" style={{ fontSize: "0.8rem" }}>
                    ★ record {board[g.key]!.best!.score}
                  </span>
                )}
              </span>
            </m.button>
          ))}
        </div>

        <section className="col" style={{ gap: 14 }}>
          <div className="row spread wrap" style={{ gap: 12, alignItems: "center" }}>
            <div className="segment history-tabs" role="group" aria-label="Istoric">
              {(["top", "today", "recent"] as const).map((tab) => (
                <button
                  key={tab}
                  type="button"
                  className="segment-item"
                  aria-pressed={historyTab === tab}
                  onClick={() => setHistoryTab(tab)}
                >
                  {tab === "top" ? "Top" : tab === "today" ? "Azi" : "Istoric"}
                </button>
              ))}
            </div>
            <div className="row wrap" style={{ gap: 8 }}>
              <Button variant="secondary" size="sm" onClick={handleExport} disabled={playedTotal === 0}>
                <span aria-hidden>⬇</span> Export
              </Button>
              <Button variant="secondary" size="sm" onClick={() => fileRef.current?.click()}>
                <span aria-hidden>⬆</span> Import
              </Button>
              <input
                ref={fileRef}
                type="file"
                accept="application/json,.json"
                onChange={handleImport}
                style={{ display: "none" }}
              />
            </div>
          </div>

          <div className="totals-grid">
            {totals.map((row) => (
              <div key={row.key} className="card" style={{ padding: 14, display: "grid", gap: 8 }}>
                <div className="row spread" style={{ gap: 8 }}>
                  <Badge color={row.accent} size="sm">
                    {row.title}
                  </Badge>
                  <strong style={{ fontVariantNumeric: "tabular-nums" }}>
                    {row.record?.played ?? 0}
                  </strong>
                </div>
                <ScoreLine entry={row.record?.best ?? null} accent={row.accent} empty="Fără scor" />
              </div>
            ))}
          </div>

          {historyTab === "recent" && (
            <label className="row" style={{ gap: 8, alignSelf: "flex-start" }}>
              <span className="faint" style={{ fontSize: "0.78rem" }}>Joc</span>
              <select
                value={gameFilter}
                onChange={(event) => setGameFilter(event.target.value as GameKey | "all")}
                className="field"
                style={{ width: 210, padding: "9px 12px" }}
              >
                <option value="all">Toate</option>
                {GAMES.map((game) => (
                  <option key={game.key} value={game.key}>
                    {game.title}
                  </option>
                ))}
              </select>
            </label>
          )}

          <HistoryRows
            rows={
              historyTab === "top"
                ? topRows
                : historyTab === "today"
                  ? todayRows
                  : recentRows
            }
            empty={
              historyTab === "top"
                ? "Nu ai încă scoruri locale."
                : historyTab === "today"
                  ? "Nicio provocare zilnică terminată azi."
                  : "Istoricul local este gol."
            }
          />
        </section>

        <p className="faint" style={{ fontSize: "0.8rem" }}>
          Toate cele patru jocuri folosesc aceeași hartă de legături culturale românești.
        </p>
      </div>
    </div>
  );
}

function HistoryRows({ rows, empty }: { rows: GameScoreEntry[]; empty: string }) {
  if (rows.length === 0) {
    return (
      <div className="card center muted" style={{ minHeight: 82, padding: 18 }}>
        {empty}
      </div>
    );
  }
  return (
    <div className="col" style={{ gap: 8 }}>
      {rows.map((entry, index) => (
        <div
          key={`${entry.game}-${entry.at}-${entry.score}-${index}`}
          className="card row spread wrap"
          style={{ gap: 12, padding: "12px 14px", alignItems: "center" }}
        >
          <div className="row" style={{ gap: 10, minWidth: 0 }}>
            <span className="faint" style={{ width: 24, textAlign: "right" }}>
              {index + 1}
            </span>
            <div className="col" style={{ gap: 2, minWidth: 0 }}>
              <strong>{GAME_TITLES[entry.game as GameKey] ?? entry.game}</strong>
              <span className="muted" style={{ fontSize: "0.84rem" }}>
                {entry.detail}
              </span>
            </div>
          </div>
          <div className="row" style={{ gap: 12, alignItems: "center" }}>
            <span className="faint" style={{ fontSize: "0.78rem" }}>
              {formatWhen(entry.at)}
            </span>
            <strong style={{ fontVariantNumeric: "tabular-nums" }}>{entry.score}</strong>
          </div>
        </div>
      ))}
    </div>
  );
}

function ScoreLine({
  entry,
  accent,
  empty,
}: {
  entry: ScoreEntry | null;
  accent: string;
  empty: string;
}) {
  if (!entry) return <span className="muted" style={{ fontSize: "0.86rem" }}>{empty}</span>;
  return (
    <div className="row spread" style={{ gap: 8, alignItems: "baseline" }}>
      <span className="muted" style={{ fontSize: "0.82rem" }}>
        {entry.detail}
      </span>
      <strong style={{ color: accent, fontVariantNumeric: "tabular-nums" }}>
        {entry.score}
      </strong>
    </div>
  );
}

function formatWhen(ms: number): string {
  return new Intl.DateTimeFormat("ro-RO", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(ms));
}
