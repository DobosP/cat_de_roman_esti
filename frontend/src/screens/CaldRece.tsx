// CaldRece — "Cald sau Rece" (Contexto/Semantle-style) screen.
//
// A hidden secret concept lives on the server. The player types concept guesses; each
// guess comes back with a rank, graph distance, temperature tier, and 0..100 closeness.
// The server is the only source of truth (it holds the secret + sorts the guess list
// best-first); this component only renders what it returns and surfaces errors as toasts.

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, m } from "framer-motion";
import { Button, type ToastKind } from "@roedu/ui";
import { GameShell } from "../components/GameShell";
import { GameIntro } from "../components/GameIntro";
import { Hud, StatBadge } from "../components/Hud";
import { ResultCard } from "../components/ResultCard";
import { DifficultyPicker } from "../components/DifficultyPicker";
import { NextMove } from "../components/PlayGuide";
import { sound } from "../sound";
import {
  contextoApi,
  ApiError,
  type ContextoState,
  type CreateOpts,
  type Difficulty,
  type Guess,
  type GuessFeedback,
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
const CLUE_UNLOCK_ATTEMPTS = 3;

const DIFFICULTY_LABEL: Record<Difficulty, string> = {
  usor: "Ușor",
  normal: "Normal",
  greu: "Greu",
};

const DIFFICULTIES: { id: Difficulty; label: string; hint: string }[] = [
  { id: "usor", label: DIFFICULTY_LABEL.usor, hint: "recomandat" },
  { id: "normal", label: "Normal", hint: "echilibrat" },
  { id: "greu", label: DIFFICULTY_LABEL.greu, hint: "concept mai rar" },
];

type GuessRecovery = {
  message: string;
  choices: string[];
  tone: "info" | "warning";
};

type GuessView = "best" | "recent";

const FEEDBACK_ICON: Record<GuessFeedback["kind"], string> = {
  first: "📍",
  "new-best": "✨",
  warmer: "🔥",
  colder: "❄️",
  same: "↔️",
  repeat: "↻",
  found: "🎯",
};

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
    <m.div
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
        borderColor: isLatest ? color : "var(--surface-border)",
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
            style={{ borderColor: color, color, fontWeight: 700 }}
          >
            {TEMP_LABEL[g.temperature]}
          </span>
          <span
            className="badge"
            style={{
              borderColor: color,
              color,
              fontWeight: 800,
              fontVariantNumeric: "tabular-nums",
            }}
            title="Al câtelea cel mai apropiat de conceptul secret (#1 = secretul)"
          >
            #{g.rank}
          </span>
        </span>
      </div>
    </m.div>
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
  const [feedback, setFeedback] = useState<GuessFeedback | null>(null);
  const [guessView, setGuessView] = useState<GuessView>("best");
  const [confirmReveal, setConfirmReveal] = useState(false);
  const [recovery, setRecovery] = useState<GuessRecovery | null>(null);
  const [difficulty, setDifficulty] = useState<Difficulty>("usor");
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
        setFeedback(null);
        setGuessView("best");
        setConfirmReveal(false);
        setText("");
        setRecovery(null);
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
        setFeedback(null);
        setGuessView("best");
        setConfirmReveal(false);
        setText("");
        setRecovery(null);
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
      setConfirmReveal(false);
      setFeedback(null);
      setBusy(true);
      setRecovery(null);
      try {
        const res: GuessResult = await contextoApi.submitGuess(
          state.game_id,
          q,
        );
        if (!res.ok) {
          sound.playError();
          setRecovery({
            message: res.message,
            choices: res.suggestions,
            tone: "warning",
          });
          setState((prev) =>
            prev
              ? {
                  ...prev,
                  guesses: res.guesses,
                  attempts: res.attempts,
                  clues_used: res.clues_used,
                  clue_available: res.clue_available,
                  next_clue_kind: res.next_clue_kind,
                  clue: res.clue ?? prev.clue,
                  warm_clue: res.warm_clue ?? prev.warm_clue,
                }
              : prev,
          );
          return;
        }
        setText("");
        setLatestId(res.guess.id);
        setFeedback(res.feedback);
        if (res.message) {
          setRecovery({ message: res.message, choices: [], tone: "info" });
        }
        setState((prev) =>
          prev
            ? {
                ...prev,
                guesses: res.guesses,
                attempts: res.attempts,
                won: res.won,
                clues_used: res.clues_used,
                clue_available: res.clue_available,
                next_clue_kind: res.next_clue_kind,
                clue: res.clue ?? prev.clue,
                warm_clue: res.warm_clue ?? prev.warm_clue,
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
    setConfirmReveal(false);
    setBusy(true);
    setRecovery(null);
    try {
      const res = await contextoApi.requestClue(state.game_id);
      sound.playSelect();
      setState(res);
      onToast(res.message, "info");
    } catch (err) {
      sound.playError();
      // A stale tab may ask just after its last safe candidate was played elsewhere.
      // Refresh authoritative availability so a rejected clue cannot leave the button on.
      if (err instanceof ApiError && err.status === 400) {
        try {
          setState(await contextoApi.getGame(state.game_id));
        } catch {
          // Keep the current recoverable game visible if the refresh itself fails.
        }
      }
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
    setConfirmReveal(false);
    setFeedback(null);
    setBusy(true);
    setRecovery(null);
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

  const requestRevealConfirmation = useCallback(() => {
    if (!state || busy || finished) return;
    sound.playSelect();
    setConfirmReveal(true);
  }, [state, busy, finished]);

  const handleCopy = useCallback(async () => {
    if (!sharePayload) return;
    const ok = await copyResult(sharePayload);
    onToast(ok ? "Copiat!" : "Nu am putut copia.", ok ? "info" : "error");
  }, [sharePayload, onToast]);

  const showOptions = useCallback(() => {
    active.forget();
    setConfirmReveal(false);
    setFeedback(null);
    setRecovery(null);
    setShowIntro(true);
  }, [active]);

  // Leaving to the menu is permanent: drop the resume token so the game does not
  // silently reappear when the player comes back (they start fresh from the intro).
  // A genuine page refresh — which never calls this — still resumes via useActiveGame.
  const handleExit = useCallback(() => {
    active.forget();
    setConfirmReveal(false);
    setFeedback(null);
    onExit();
  }, [active, onExit]);

  const guesses = state?.guesses ?? [];
  const bestGuess = guesses[0];
  const displayedGuesses =
    guessView === "best"
      ? guesses
      : [...guesses].sort(
          (left, right) => right.attempt_number - left.attempt_number,
        );
  const clueCountdown = Math.max(
    0,
    CLUE_UNLOCK_ATTEMPTS - (state?.attempts ?? 0),
  );
  const clueActionLabel = state?.clue_available
    ? state.next_clue_kind === "warmer"
      ? "Mai cald"
      : "Indiciu"
    : clueCountdown > 0
      ? `Indiciu în ${clueCountdown}`
      : "Indiciu";
  // The most recently played guess (may sort anywhere in the list) — surfaced as an
  // explicit verdict so feedback is always visible, not buried by best-first sorting.
  const latestGuess = latestId
    ? (guesses.find((g) => g.id === latestId) ?? null)
    : null;

  // ---- Intro: difficulty picker + daily challenge + personal best. ----
  if (showIntro) {
    return (
      <div className="screen-pad fill">
        <div
          className="container col game-container"
          style={{ gap: 18, paddingBlock: 8 }}
        >
          <div style={{ width: "100%" }}>
            <GameShell onExit={handleExit} accent={DEF.accent} />
          </div>

          <GameIntro
            icon={`${DEF.icon}🧊`}
            title={DEF.title}
            tag={DEF.tag}
            accent={DEF.accent}
            glow={DEF.glow}
            description={
              <p style={{ margin: 0 }}>
                Găsește secretul urmărind cât de cald e fiecare cuvânt.
              </p>
            }
            steps={[
              { icon: "⌨️", label: "Scrie un cuvânt" },
              { icon: "🔥", label: "Vezi căldura" },
              { icon: "🎯", label: "Apropie-te" },
            ]}
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
    // Whole-screen scroll (the .screen-pad owns overflow-y): the header/title flow
    // and scroll away; the input plus its compact action row stay pinned. The old fixed-header +
    // inner-scroll-list layout collapsed the list to ~0px on short/phone viewports
    // (worst with the keyboard up), stranding the guesses; single-scroll keeps every
    // guess reachable at any height.
    <div className="screen-pad fill">
      <div className="container col game-container" style={{ gap: 16, paddingBlock: 8 }}>
        {/* header */}
        <GameShell onExit={handleExit} accent={DEF.accent} title={DEF.title}>
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
          </Hud>
        </GameShell>

        <NextMove
          icon={latestGuess ? TEMP_ICON[latestGuess.temperature] : "⌨️"}
          title={latestGuess ? "Urmează căldura" : "Încearcă un cuvânt"}
          detail={
            latestGuess
              ? `${TEMP_HINT[latestGuess.temperature]} Încearcă ceva înrudit.`
              : "Sensul contează, nu literele."
          }
          progress={`${state?.attempts ?? 0} încercări`}
          accent={latestGuess ? barColor(latestGuess) : DEF.accent}
          ready={Boolean(latestGuess && latestGuess.rank <= 10)}
        />
        <p className="rank-legend faint" style={{ margin: 0 }}>
          Număr mai mic = mai aproape · #1 = răspunsul
        </p>

        {/* The form and its three recovery actions stay together above the scrolling list. */}
        <div className="contexto-sticky-controls">
          <form onSubmit={handleGuess} className="row contexto-input-bar" style={{ gap: 8 }}>
            <input
              ref={inputRef}
              className="field fill"
              placeholder={finished ? "Joc terminat" : "Încearcă un cuvânt…"}
              value={text}
              onChange={(e) => {
                setText(e.target.value);
                setConfirmReveal(false);
              }}
              onKeyDown={(e) => {
                // Escape clears a half-typed guess or an accidental reveal confirmation.
                if (e.key === "Escape" && (text || recovery || confirmReveal)) {
                  e.preventDefault();
                  setText("");
                  setRecovery(null);
                  setConfirmReveal(false);
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

          <div className="contexto-action-row" aria-label="Acțiuni joc">
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => void handleClue()}
              disabled={busy || finished || !state?.clue_available}
              title={
                state?.clue_available
                  ? state.next_clue_kind === "warmer"
                    ? "Arată un cuvânt sigur mai cald"
                    : "Arată categoria conceptului secret"
                  : clueCountdown > 0
                    ? `Disponibil după încă ${clueCountdown} încercări`
                    : "Nu mai există un indiciu sigur"
              }
            >
              {clueActionLabel}
            </Button>
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={requestRevealConfirmation}
              disabled={busy || finished || !state}
              aria-expanded={confirmReveal}
              aria-controls="contexto-reveal-confirmation"
            >
              Răspuns
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
          </div>

          <AnimatePresence initial={false}>
            {confirmReveal && !finished && (
              <m.div
                id="contexto-reveal-confirmation"
                key="reveal-confirmation"
                className="contexto-reveal-confirm"
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -4 }}
                role="alert"
              >
                <span>Arătăm răspunsul?</span>
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => setConfirmReveal(false)}
                  disabled={busy}
                >
                  Nu
                </Button>
                <Button
                  type="button"
                  size="sm"
                  onClick={() => void handleGiveUp()}
                  disabled={busy}
                >
                  Da, arată
                </Button>
              </m.div>
            )}
          </AnimatePresence>
        </div>

        <span
          className="visually-hidden"
          role="status"
          aria-live="polite"
          aria-atomic="true"
        >
          {!finished ? (recovery?.message ?? "") : ""}
        </span>

        <AnimatePresence>
          {!finished && recovery && (
            <m.div
              key={`${recovery.tone}-${recovery.message}`}
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              className="card"
              style={{
                padding: 12,
                borderColor: recovery.tone === "warning" ? "var(--warn)" : DEF.accent,
              }}
            >
              <div className="col" style={{ gap: 8 }}>
                <span>
                  <span aria-hidden="true" style={{ marginRight: 6 }}>
                    {recovery.tone === "warning" ? "⚠" : "ℹ"}
                  </span>
                  {recovery.message}
                </span>
                {recovery.choices.length > 0 ? (
                  <div className="row wrap" style={{ gap: 8 }}>
                    <span className="faint">Ai vrut să scrii:</span>
                    {recovery.choices.map((choice) => (
                      <Button
                        key={choice}
                        type="button"
                        variant="secondary"
                        onClick={() => {
                          sound.playSelect();
                          setText(choice);
                          setConfirmReveal(false);
                          inputRef.current?.focus();
                        }}
                      >
                        {choice}
                      </Button>
                    ))}
                  </div>
                ) : null}
              </div>
            </m.div>
          )}
        </AnimatePresence>

        {(state?.clue || state?.warm_clue) && !finished && (
          <div
            className="col"
            style={{ gap: 8 }}
            aria-label="Indicii folosite"
            aria-live="polite"
          >
            {state.clue && (
              <div
                className="row spread"
                style={{
                  gap: 10,
                  alignItems: "center",
                  padding: "9px 12px",
                  borderRadius: 12,
                  border: `1px solid ${DEF.accent}66`,
                  background: `${DEF.accent}12`,
                }}
              >
                <span className="muted" style={{ fontSize: "0.82rem" }}>
                  🧭 Categorie
                </span>
                <strong>{state.clue.category.label}</strong>
              </div>
            )}
            {state.warm_clue && (
              <div
                className="row spread"
                style={{
                  gap: 10,
                  alignItems: "center",
                  padding: "10px 12px",
                  borderRadius: 12,
                  border: "1px solid #f4a25999",
                  background: "rgba(244, 162, 89, 0.12)",
                }}
              >
                <span className="muted" style={{ fontSize: "0.82rem" }}>
                  🔥 Încearcă
                </span>
                <button
                  type="button"
                  className="contexto-warm-clue-button"
                  title="Pune cuvântul în căsuță"
                  aria-label={`Pune ${state.warm_clue.label} în câmpul de răspuns`}
                  onClick={() => {
                    const word = state.warm_clue?.label;
                    if (!word) return;
                    sound.playSelect();
                    setText(word);
                    setConfirmReveal(false);
                    if (window.matchMedia("(pointer: fine)").matches) {
                      inputRef.current?.focus();
                    }
                  }}
                >
                  {state.warm_clue.label}
                </button>
                <span
                  className="badge"
                  title="Acest cuvânt era mai aproape decât cea mai bună încercare"
                >
                  #{state.warm_clue.rank}
                </span>
              </div>
            )}
          </div>
        )}

        {/* One short, server-authored comparison for the accepted guess just played. */}
        <AnimatePresence mode="wait">
          {latestGuess && feedback && (
            <m.div
              key={`${latestGuess.id}-${feedback.kind}-${state?.attempts ?? 0}`}
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ type: "spring", stiffness: 320, damping: 24 }}
              className={`contexto-comparison contexto-comparison--${feedback.kind}`}
              aria-live="polite"
              role="status"
            >
              <span aria-hidden>{FEEDBACK_ICON[feedback.kind]}</span>
              <span className="contexto-comparison-copy">
                <strong>{latestGuess.label}</strong>
                <span>{feedback.message}</span>
              </span>
              <strong
                className="contexto-comparison-rank"
                title="Al câtelea cel mai apropiat de conceptul secret (#1 = secretul)"
              >
                #{latestGuess.rank}
              </strong>
            </m.div>
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
              onExit={handleExit}
            >
              <span style={{ fontSize: "1.4rem", color: "var(--text)", display: "block" }}>
                {state.target.label}
              </span>
              {state.target.description && (
                <span style={{ fontSize: "0.85rem" }}>{state.target.description}</span>
              )}
              {won && recovery?.message ? (
                <span className="muted" style={{ display: "block", marginTop: 8 }}>
                  <span aria-hidden="true" style={{ marginRight: 6 }}>
                    ℹ
                  </span>
                  {recovery.message}
                </span>
              ) : null}
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
            <span title="Al câtelea cel mai apropiat de conceptul secret (#1 = secretul)">
              (#{bestGuess.rank})
            </span>
          </p>
        )}

        {guesses.length > 1 && (
          <div
            className="contexto-guess-tabs"
            role="tablist"
            aria-label="Ordinea încercărilor"
          >
            <button
              type="button"
              role="tab"
              aria-selected={guessView === "best"}
              aria-controls="contexto-guess-list"
              className={guessView === "best" ? "is-active" : ""}
              onClick={() => {
                sound.playSelect();
                setGuessView("best");
              }}
            >
              Bune
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={guessView === "recent"}
              aria-controls="contexto-guess-list"
              className={guessView === "recent" ? "is-active" : ""}
              onClick={() => {
                sound.playSelect();
                setGuessView("recent");
              }}
            >
              Recente
            </button>
          </div>
        )}

        {/* Bune keeps server rank order; Recente uses stable server attempt ordinals. */}
        <div id="contexto-guess-list" className="col" style={{ gap: 8 }}>
          {guesses.length === 0 && !finished && (
            <p className="faint center" style={{ marginTop: 24 }}>
              Nicio încercare încă. Începe cu orice idee!
            </p>
          )}
          <AnimatePresence initial={false}>
            {displayedGuesses.map((g) => (
              <GuessRow key={g.id} g={g} isLatest={g.id === latestId} />
            ))}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
