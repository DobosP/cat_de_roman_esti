// CaldRece — "Cald sau Rece" (Contexto/Semantle-style) screen.
//
// A hidden secret concept lives on the server. The player types concept guesses; each
// guess comes back with a rank, graph distance, temperature tier, and 0..100 closeness.
// The server is the only source of truth (it holds the secret + sorts the guess list
// best-first); this component only renders what it returns and surfaces errors as toasts.

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Button, type ToastKind } from "@roedu/ui";
import { GameShell } from "../components/GameShell";
import { GameIntro } from "../components/GameIntro";
import { Hud, StatBadge } from "../components/Hud";
import { ResultCard } from "../components/ResultCard";
import { DifficultyPicker } from "../components/DifficultyPicker";
import { sound } from "../sound";
import {
  contextoApi,
  ApiError,
  type ContextoState,
  type CreateOpts,
  type Difficulty,
  type Guess,
  type GuessResult,
  type Temperature,
} from "../api/contexto";
import { bestScore } from "../scores";
import { useRecordScore } from "../hooks/useRecordScore";
import { useActiveGame } from "../hooks/useActiveGame";
import { gameByKey } from "../games";
import { categoryColor, categoryLabel } from "../categories";
import { CategoryPicker } from "../components/CategoryPicker";
import { buildSharePayload, copyResult, stableKey, todayLocal } from "../share";

const GAME_KEY = "contexto";
const DEF = gameByKey("contexto");

const DIFFICULTY_LABEL: Record<Difficulty, string> = {
  usor: "Ușor",
  normal: "Normal",
  greu: "Greu",
};

const DIFFICULTIES: { id: Difficulty; label: string; hint: string }[] = [
  { id: "usor", label: DIFFICULTY_LABEL.usor, hint: "concept cunoscut" },
  { id: "normal", label: "Normal", hint: "echilibrat" },
  { id: "greu", label: DIFFICULTY_LABEL.greu, hint: "concept mai rar" },
];

// Temperature -> colour on a hot/cold gradient (hot = red/orange, cold = blue).
const TEMP_COLOR: Record<Temperature, string> = {
  Gasit: "#5fd99b",
  Fierbinte: "#ff5d3b",
  Cald: "#f4a259",
  Caldut: "#ffd166",
  Rece: "#8ec5ff",
  Inghetat: "#7bb8f2",
};

const TEMP_ICON: Record<Temperature, string> = {
  Gasit: "🎯",
  Fierbinte: "🔥",
  Cald: "♨️",
  Caldut: "🌤️",
  Rece: "❄️",
  Inghetat: "🧊",
};

// API tokens stay ASCII for compatibility; only their player-facing labels are localized.
const TEMP_LABEL: Record<Temperature, string> = {
  Gasit: "Găsit",
  Fierbinte: "Fierbinte",
  Cald: "Cald",
  Caldut: "Călduț",
  Rece: "Rece",
  Inghetat: "Înghețat",
};

// Short, encouraging gloss per tier so the latest verdict reads as feedback, not a number.
const TEMP_HINT: Record<Temperature, string> = {
  Gasit: "Exact!",
  Fierbinte: "Arde! Ești la un pas.",
  Cald: "Foarte aproape.",
  Caldut: "Te apropii.",
  Rece: "Cam departe.",
  Inghetat: "Înghețat — încearcă altă direcție.",
};

function barColor(g: Guess): string {
  return TEMP_COLOR[g.temperature] ?? "#9aa3b2";
}

function GuessRow({ g, isLatest }: { g: Guess; isLatest: boolean }) {
  const color = barColor(g);
  const pct = Math.max(2, Math.min(100, g.closeness));
  return (
    <motion.div
      layout
      initial={isLatest ? { opacity: 0, y: -10, scale: 0.97 } : false}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ type: "spring", stiffness: 380, damping: 28 }}
      className="card"
      style={{
        position: "relative",
        overflow: "hidden",
        padding: "10px 14px",
        display: "grid",
        gap: 8,
        borderColor: isLatest ? color : "var(--border)",
        boxShadow: isLatest ? `0 0 22px -10px ${color}` : undefined,
      }}
    >
      {/* hot/cold fill bar */}
      <div
        aria-hidden
        style={{
          position: "absolute",
          inset: 0,
          width: `${pct}%`,
          background: `linear-gradient(90deg, ${color}26, ${color}0d)`,
          transition: "width 0.5s cubic-bezier(0.2,0.7,0.3,1)",
        }}
      />
      <div
        className="row spread"
        style={{ position: "relative", gap: 10, alignItems: "center" }}
      >
        <span className="row" style={{ gap: 8, alignItems: "center" }}>
          <span aria-hidden style={{ fontSize: "1.1rem" }}>
            {TEMP_ICON[g.temperature]}
          </span>
          <strong style={{ fontSize: "0.98rem" }}>{g.label}</strong>
        </span>
        <span className="row" style={{ gap: 8, alignItems: "center" }}>
          <span
            className="badge"
            style={{
              borderColor: color,
              color,
              fontWeight: 800,
              fontVariantNumeric: "tabular-nums",
            }}
            title="Rang față de conceptul secret"
          >
            #{g.rank}
          </span>
          <span
            className="badge"
            style={{ borderColor: color, color, fontWeight: 700 }}
          >
            {TEMP_LABEL[g.temperature]}
          </span>
          <span
            className="muted"
            style={{
              fontVariantNumeric: "tabular-nums",
              fontSize: "0.82rem",
              minWidth: 38,
              textAlign: "right",
            }}
            title={`Distanță: ${g.distance} salturi`}
          >
            {g.closeness}/100
          </span>
        </span>
      </div>
    </motion.div>
  );
}

export default function CaldRece({
  onExit,
  onToast,
}: {
  onExit: () => void;
  onToast: (message: string, kind?: ToastKind) => void;
}) {
  const [state, setState] = useState<ContextoState | null>(null);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [latestId, setLatestId] = useState<string | null>(null);
  const [difficulty, setDifficulty] = useState<Difficulty>("normal");
  const [category, setCategory] = useState<string | null>(null);
  // Intro is shown until the player picks how to start.
  const [showIntro, setShowIntro] = useState(true);
  const [isRecord, setIsRecord] = useState(false);
  const [isPuzzleRecord, setIsPuzzleRecord] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const recordOnce = useRecordScore("contexto");
  const active = useActiveGame("contexto");
  const resumeOnce = useRef(false);

  const best = bestScore(GAME_KEY);

  const start = useCallback(
    async (opts: CreateOpts = {}) => {
      setBusy(true);
      try {
        const fresh = await contextoApi.createGame(opts);
        setState(fresh);
        active.remember(fresh.game_id);
        setLatestId(null);
        setText("");
        setIsRecord(false);
        setIsPuzzleRecord(false);
        setShowIntro(false);
        inputRef.current?.focus();
      } catch (err) {
        onToast(
          err instanceof ApiError
            ? `Nu am putut porni jocul (${err.status}).`
            : "Nu am putut porni jocul. Verifică serverul.",
          "error",
        );
      } finally {
        setBusy(false);
      }
    },
    [active, onToast],
  );

  useEffect(() => {
    if (resumeOnce.current) return;
    resumeOnce.current = true;

    const id = active.peek();
    if (!id) return;

    const resume = async () => {
      setBusy(true);
      try {
        const saved = await contextoApi.getGame(id);
        if (saved.won || saved.gave_up) {
          active.forget();
          return;
        }
        setState(saved);
        setDifficulty(saved.difficulty);
        setCategory(saved.board_category ?? null);
        setLatestId(null);
        setText("");
        setIsRecord(false);
        setIsPuzzleRecord(false);
        setShowIntro(false);
        window.setTimeout(() => inputRef.current?.focus(), 0);
        onToast("Joc reluat.", "info");
      } catch {
        active.forget();
      } finally {
        setBusy(false);
      }
    };

    void resume();
  }, [active, onToast]);

  const won = state?.won ?? false;
  const gaveUp = state?.gave_up ?? false;
  const finished = won || gaveUp;

  const puzzleKey = useMemo(() => {
    if (!state?.won || !state.target) return null;
    return stableKey([
      GAME_KEY,
      state.daily ? `daily-${state.daily}` : state.difficulty,
      state.target.id,
      state.board_category,
    ]);
  }, [state]);

  const sharePayload = useMemo(() => {
    if (!state?.won || !state.share) return null;
    return buildSharePayload({
      gameTitle: DEF.title,
      serverShare: state.share,
      score: state.score,
      puzzleKey,
    });
  }, [state, puzzleKey]);

  // Record the score exactly once when a game is won.
  useEffect(() => {
    if (!state || (!state.won && !state.gave_up)) return;
    active.forget();
    if (!state.won || state.score === undefined) return;
    const attemptsLabel = state.attempts === 1 ? "încercare" : "încercări";
    const detail = state.daily
      ? `Zilnic ${state.daily} · ${state.attempts} ${attemptsLabel}`
      : `${DIFFICULTY_LABEL[state.difficulty]} · ${state.attempts} ${attemptsLabel}`;
    const outcome = recordOnce(state.game_id, state.score, detail, {
      puzzleKey,
      difficulty: state.difficulty,
      daily: state.daily,
      category: state.board_category,
    });
    if (!outcome) return;
    const { isBest, isPuzzleBest } = outcome;
    setIsPuzzleRecord(isPuzzleBest);
    if (isBest) {
      setIsRecord(true);
      sound.playRecord();
    } else if (isPuzzleBest) {
      sound.playRecord();
    }
  }, [state, puzzleKey, recordOnce, active]);

  const handleGuess = useCallback(
    async (e?: React.FormEvent) => {
      e?.preventDefault();
      if (!state || busy || finished) return;
      const q = text.trim();
      if (!q) return;
      setBusy(true);
      try {
        const res: GuessResult = await contextoApi.submitGuess(
          state.game_id,
          q,
        );
        if (!res.ok) {
          sound.playError();
          onToast(res.message, "error");
          setState((prev) =>
            prev
              ? {
                  ...prev,
                  guesses: res.guesses,
                  attempts: res.attempts,
                  clues_used: res.clues_used,
                  clue_available: res.clue_available,
                  clue: res.clue ?? prev.clue,
                }
              : prev,
          );
          return;
        }
        setText("");
        setLatestId(res.guess.id);
        setState((prev) =>
          prev
            ? {
                ...prev,
                guesses: res.guesses,
                attempts: res.attempts,
                won: res.won,
                clues_used: res.clues_used,
                clue_available: res.clue_available,
                clue: res.clue ?? prev.clue,
                target: res.target ?? prev.target,
                score: res.score ?? prev.score,
                share: res.share ?? prev.share,
              }
            : prev,
        );
        if (res.won) {
          sound.playWin();
        } else {
          sound.playHop();
        }
      } catch (err) {
        onToast(
          err instanceof ApiError
            ? `Încercarea a eșuat (${err.status}).`
            : "Încercarea a eșuat. Verifică serverul.",
          "error",
        );
      } finally {
        setBusy(false);
        inputRef.current?.focus();
      }
    },
    [state, busy, finished, text, onToast],
  );

  const handleClue = useCallback(async () => {
    if (!state || busy || finished || !state.clue_available) return;
    setBusy(true);
    try {
      const res = await contextoApi.requestClue(state.game_id);
      sound.playSelect();
      setState(res);
      onToast(res.message, "info");
    } catch (err) {
      sound.playError();
      onToast(
        err instanceof ApiError
          ? `Indiciul nu este disponibil (${err.status}).`
          : "Nu am putut cere indiciul.",
        "error",
      );
    } finally {
      setBusy(false);
      inputRef.current?.focus();
    }
  }, [state, busy, finished, onToast]);

  const handleGiveUp = useCallback(async () => {
    if (!state || busy || finished) return;
    setBusy(true);
    try {
      const res = await contextoApi.giveUp(state.game_id);
      sound.playUndo();
      setState(res);
    } catch (err) {
      onToast(
        err instanceof ApiError
          ? `Nu am putut renunța (${err.status}).`
          : "Nu am putut renunța.",
        "error",
      );
    } finally {
      setBusy(false);
    }
  }, [state, busy, finished, onToast]);

  const handleCopy = useCallback(async () => {
    if (!sharePayload) return;
    const ok = await copyResult(sharePayload);
    onToast(ok ? "Copiat!" : "Nu am putut copia.", ok ? "info" : "error");
  }, [sharePayload, onToast]);

  const showOptions = useCallback(() => {
    active.forget();
    setShowIntro(true);
  }, [active]);

  const guesses = state?.guesses ?? [];
  const bestGuess = guesses[0];
  // The most recently played guess (may sort anywhere in the list) — surfaced as an
  // explicit verdict so feedback is always visible, not buried by best-first sorting.
  const latestGuess = latestId
    ? (guesses.find((g) => g.id === latestId) ?? null)
    : null;

  // ---- Intro: difficulty picker + daily challenge + personal best. ----
  if (showIntro) {
    return (
      <div className="screen-pad fill" style={{ display: "flex" }}>
        <div
          className="container col fill center"
          style={{ gap: 18, paddingBlock: 8, justifyContent: "center" }}
        >
          <div style={{ width: "100%" }}>
            <GameShell onExit={onExit} accent={DEF.accent} />
          </div>

          <GameIntro
            icon={`${DEF.icon}🧊`}
            title={DEF.title}
            tag={DEF.tag}
            accent={DEF.accent}
            glow={DEF.glow}
            description={
              <p style={{ margin: 0 }}>
                Există un concept secret. Scrie ce-ți vine în minte — îți spun cât
                de aproape ești. Cu cât folosești mai puține încercări, cu atât
                scorul este mai mare.
              </p>
            }
            best={best}
            startLabel="Joacă"
            onStart={() => void start({ difficulty, category: category ?? undefined })}
            onDaily={() => void start({ difficulty, daily: todayLocal() })}
            dailyLabel="Provocarea zilei"
            starting={busy}
          >
            <div style={{ width: "100%", maxWidth: 420 }}>
              <DifficultyPicker
                options={DIFFICULTIES}
                value={difficulty}
                onChange={(id) => {
                  sound.playSelect();
                  setDifficulty(id);
                }}
              />
            </div>
            <div style={{ width: "100%", maxWidth: 420 }}>
              <CategoryPicker
                game="contexto"
                value={category}
                onChange={(key) => {
                  sound.playSelect();
                  setCategory(key);
                }}
                accent={DEF.accent}
              />
            </div>
          </GameIntro>
        </div>
      </div>
    );
  }

  return (
    <div className="screen-pad fill" style={{ display: "flex" }}>
      <div
        className="container col fill"
        style={{ gap: 16, minHeight: 0, paddingBlock: 8 }}
      >
        {/* header */}
        <GameShell onExit={onExit} accent={DEF.accent} title={DEF.title}>
          <Hud>
            <StatBadge
              label="Mod"
              value={
                state?.daily
                  ? `📅 ${state.daily}`
                  : DIFFICULTY_LABEL[state?.difficulty ?? difficulty]
              }
              accent={DEF.accent}
              title="Mod de joc"
            />
            {state?.board_category && (
              <StatBadge
                label="Categorie"
                value={categoryLabel(state.board_category)}
                accent={categoryColor(state.board_category)}
              />
            )}
            <StatBadge
              label="Încercări"
              value={`${state?.attempts ?? 0} ${state?.attempts === 1 ? "încercare" : "încercări"}`}
              accent={DEF.accent}
              title="Încercări"
            />
            {(state?.clues_used ?? 0) > 0 && (
              <StatBadge
                label="Indiciu"
                value={`x${state?.clues_used}`}
                accent={DEF.accent}
                title="Indicii folosite"
              />
            )}
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => void handleClue()}
              disabled={busy || finished || !state?.clue_available}
              title={
                state?.clue_available
                  ? "Arată categoria conceptului secret"
                  : "Disponibil după 3 încercări"
              }
            >
              Indiciu
            </Button>
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => void handleGiveUp()}
              disabled={busy || finished || !state}
            >
              Arată răspunsul
            </Button>
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={showOptions}
              disabled={busy}
              title="Schimbă opțiunile"
            >
              ⚙ Opțiuni
            </Button>
          </Hud>
        </GameShell>

        {/* title */}
        <div className="col" style={{ gap: 4 }}>
          <h1 style={{ fontSize: "clamp(1.5rem, 4vw, 2.2rem)", margin: 0 }}>
            {DEF.title}
          </h1>
          <p className="muted" style={{ margin: 0, fontSize: "0.9rem" }}>
            Există un concept secret. Scrie ce-ți vine în minte — îți spun cât
            de aproape ești. 🔥 fierbinte … 🧊 înghețat.
          </p>
        </div>

        {/* input */}
        <form onSubmit={handleGuess} className="row" style={{ gap: 8 }}>
          <input
            ref={inputRef}
            className="field fill"
            placeholder={finished ? "Joc terminat" : "Scrie un concept…"}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              // Escape clears a half-typed guess without leaving the field.
              if (e.key === "Escape" && text) {
                e.preventDefault();
                setText("");
              }
            }}
            disabled={busy || finished}
            autoComplete="off"
            autoFocus
            spellCheck={false}
            aria-label="Concept de ghicit"
            enterKeyHint="send"
          />
          <Button
            type="submit"
            disabled={busy || finished || !text.trim()}
          >
            Ghicește
          </Button>
        </form>

        {state?.clue && !finished && (
          <div
            className="row spread"
            style={{
              gap: 10,
              alignItems: "center",
              padding: "8px 12px",
              borderRadius: 10,
              border: "1px solid var(--border)",
              background: "rgba(255,255,255,0.04)",
            }}
            aria-live="polite"
          >
            <span className="muted" style={{ fontSize: "0.88rem" }}>
              Categoria secretului
            </span>
            <strong>{state.clue.category.label}</strong>
          </div>
        )}

        {/* latest verdict — always-visible feedback for the last guess */}
        <AnimatePresence mode="wait">
          {!finished && latestGuess && (
            <motion.div
              key={`${latestGuess.id}-${latestGuess.distance}`}
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ type: "spring", stiffness: 320, damping: 24 }}
              className="row spread"
              style={{
                gap: 10,
                alignItems: "center",
                padding: "8px 12px",
                borderRadius: 10,
                border: `1px solid ${barColor(latestGuess)}`,
                background: `${barColor(latestGuess)}1a`,
              }}
              aria-live="polite"
            >
              <span className="row" style={{ gap: 8, alignItems: "center" }}>
                <span aria-hidden style={{ fontSize: "1.2rem" }}>
                  {TEMP_ICON[latestGuess.temperature]}
                </span>
                <span style={{ fontSize: "0.9rem" }}>
                  <strong>{latestGuess.label}</strong>{" "}
                  <span className="muted">— {TEMP_HINT[latestGuess.temperature]}</span>
                </span>
              </span>
              <strong
                style={{
                  color: barColor(latestGuess),
                  fontVariantNumeric: "tabular-nums",
                }}
              >
                #{latestGuess.rank} · {latestGuess.closeness}
              </strong>
            </motion.div>
          )}
        </AnimatePresence>

        {/* win / giveup banner */}
        <AnimatePresence>
          {finished && state?.target && (
            <ResultCard
              icon={won ? "🎯" : "🫥"}
              title={won ? "Ai găsit conceptul!" : "Conceptul secret era:"}
              accent={won ? "var(--good)" : "var(--warn)"}
              won={won}
              score={won ? state.score : undefined}
              isRecord={isRecord}
              isPuzzleRecord={isPuzzleRecord}
              shareText={sharePayload}
              onCopy={() => void handleCopy()}
              onReplay={() =>
                void start({
                  difficulty: state.difficulty,
                  category: category ?? undefined,
                })
              }
              onOptions={showOptions}
              onExit={onExit}
            >
              <span style={{ fontSize: "1.4rem", color: "var(--text)", display: "block" }}>
                {state.target.label}
              </span>
              {state.target.description && (
                <span style={{ fontSize: "0.85rem" }}>{state.target.description}</span>
              )}
            </ResultCard>
          )}
        </AnimatePresence>

        {/* best so far */}
        {!finished && bestGuess && (
          <p className="faint center" style={{ fontSize: "0.82rem", margin: 0 }}>
            Cel mai aproape:{" "}
            <strong style={{ color: barColor(bestGuess) }}>
              {bestGuess.label}
            </strong>{" "}
            (#{bestGuess.rank}, {bestGuess.closeness}/100)
          </p>
        )}

        {/* guess list (server-sorted best-first) */}
        <div
          className="col fill"
          style={{ gap: 8, overflowY: "auto", minHeight: 0, paddingRight: 4 }}
        >
          {guesses.length === 0 && !finished && (
            <p className="faint center" style={{ marginTop: 24 }}>
              Nicio încercare încă. Începe cu orice idee!
            </p>
          )}
          <AnimatePresence initial={false}>
            {guesses.map((g) => (
              <GuessRow key={g.id} g={g} isLatest={g.id === latestId} />
            ))}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
