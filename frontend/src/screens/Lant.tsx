import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, m } from "framer-motion";
import { Button, Spinner, type ToastKind } from "@roedu/ui";
import {
  type Difficulty,
  type HintResult,
  type LantChoice,
  type LantProgress,
  type LantState,
  type PathStep,
  createLant,
  getLant,
  hintLant,
  moveLant,
  undoLant,
} from "../api/lant";
import { ApiError } from "../api/client";
import { createGameActionOwner, recoverOwnedGameAction, type GameActionTicket } from "../gameActionRecovery.mjs";
import { GameShell } from "../components/GameShell";
import { GameIntro } from "../components/GameIntro";
import { GameOptions } from "../components/GameOptions";
import { GameSetupOptions } from "../components/GameSetupOptions";
import { Hud, StatBadge } from "../components/Hud";
import { ResultCard } from "../components/ResultCard";
import { DifficultyPicker } from "../components/DifficultyPicker";
import { useActiveGame } from "../hooks/useActiveGame";
import { useRecordScore } from "../hooks/useRecordScore";
import { useSavedGameResume } from "../hooks/useSavedGameResume";
import { sound } from "../sound";
import { bestScore } from "../scores";
import { gameByKey } from "../games";
import { categoryLabel } from "../categories";
import { CategoryPicker } from "../components/CategoryPicker";
import { buildSharePayload, copyResult, formatDayKey, roNoun, stableKey, todayLocal } from "../share";
import "../styles/lant.css";

const GAME_KEY = "lant";
const DEF = gameByKey("lant");

const isTerminalResume = (state: LantState) => state.won;

const DIFFICULTIES: { key: Difficulty; label: string; hint: string }[] = [
  { key: "usor", label: "Ușor", hint: "recomandat" },
  { key: "normal", label: "Normal", hint: "3–4 salturi" },
  { key: "greu", label: "Greu", hint: "4–6 salturi" },
];

// Lanțul Cuvintelor — choose a direct link from CURRENT toward TARGET.
// Free typing remains available for concepts outside the server's local choices.
// All logic is server-authoritative; this screen only renders state + sends actions.

const TARGET_COLOR = "#f178b6";

const PROGRESS_ICON: Record<LantProgress["kind"], string> = {
  closer: "↗",
  lateral: "↔",
  farther: "↘",
  dead_end: "↶",
  won: "✓",
};

type ActionSync = { gameId: string; kind: "failed" | "changed" };

type ActionFocus = {
  ticket: GameActionTicket;
  origin: HTMLElement;
  ready: boolean;
};

type RecoveryFeedback = {
  message: string;
  choices: string[];
  tone: "info" | "warning";
};

function Breadcrumb({ path }: { path: PathStep[] }) {
  return (
    <div className="row wrap breadcrumb-trail" role="group" aria-label="Traseul parcurs"
      tabIndex={0} style={{ gap: 6, alignItems: "center" }}>
      <AnimatePresence initial={false}>
        {path.map((step, i) => (
          <m.span
            key={`${step.id}-${i}`}
            layout
            initial={{ opacity: 0, scale: 0.8, y: -6 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ type: "spring", stiffness: 420, damping: 26 }}
            className="row lant-trail-step"
            style={{ gap: 6, alignItems: "center" }}
          >
            {i > 0 && (
              <span
                className="faint lant-trail-relation"
                style={{ fontSize: "0.7rem" }}
                title={step.relation}
              >
                ―{step.relation ? ` ${step.relation} →` : " →"}
              </span>
            )}
            <span
              className="chip"
              style={
                i === path.length - 1
                  ? {
                      borderColor: DEF.accent,
                      color: DEF.accent,
                      fontWeight: 700,
                    }
                  : undefined
              }
            >
              {step.label}
            </span>
          </m.span>
        ))}
      </AnimatePresence>
    </div>
  );
}

export default function Lant({
  onExit,
  onToast,
}: {
  onExit: () => void;
  onToast: (message: string, kind?: ToastKind) => void;
}) {
  const active = useActiveGame(GAME_KEY);
  const [state, setState] = useState<LantState | null>(null);
  const [startFailed, setStartFailed] = useState(false);
  const startInFlight = useRef(false);
  const [loading, setLoading] = useState(() => active.peek() !== null);
  const [creating, setCreating] = useState(false);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [actionSync, setActionSync] = useState<ActionSync | null>(null);
  const actionOwner = useMemo(() => createGameActionOwner(active), [active]);
  useEffect(() => () => actionOwner.invalidate(), [actionOwner]);
  const [shake, setShake] = useState(0);
  const [hint, setHint] = useState<HintResult | null>(null);
  const [progress, setProgress] = useState<LantProgress | null>(null);
  const [recovery, setRecovery] = useState<RecoveryFeedback | null>(null);
  const [difficulty, setDifficulty] = useState<Difficulty>("usor");
  const [category, setCategory] = useState<string | null>(null);
  const [showHow, setShowHow] = useState(false);
  const [scored, setScored] = useState<{
    score: number;
    isBest: boolean;
    isPuzzleBest: boolean;
  } | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const choicesRef = useRef<HTMLElement>(null);
  const pendingActionFocus = useRef<ActionFocus | null>(null);
  const initiallyFocusedGame = useRef<string | null>(null);

  const focusInputForFinePointer = useCallback(() => {
    if (window.matchMedia("(pointer: fine)").matches) {
      inputRef.current?.focus();
    }
  }, []);

  const best = useMemo(() => bestScore(GAME_KEY), []);
  const recordOnce = useRecordScore("lant");

  const puzzleKey = useMemo(() => {
    if (!state?.won) return null;
    return stableKey([
      GAME_KEY,
      state.daily ? `daily-${state.daily}` : state.difficulty,
      state.start.id,
      state.target.id,
      state.optimal,
      state.board_category,
    ]);
  }, [state]);

  const sharePayload = useMemo(() => {
    if (!state?.won || !state.share) return null;
    return buildSharePayload({
      gameTitle: "Lanțul Cuvintelor",
      serverShare: state.share,
      score: state.score,
      puzzleKey,
    });
  }, [state, puzzleKey]);

  const applyResumedGame = useCallback(
    (fresh: LantState, { terminal, bypassed }: { terminal: boolean; bypassed: boolean }) => {
      actionOwner.invalidate();
      pendingActionFocus.current = null;
      setActionSync(null);
      setBusy(false);
      setHint(fresh.earned_hint ?? null);
      setRecovery(null);
      setProgress(null);
      setScored(null);
      setDifficulty(fresh.difficulty);
      setCategory(fresh.board_category ?? null);
      setStartFailed(false);
      setState(fresh);
      setText("");
      // The daily-bypass notice already says the round was resumed.
      if (!terminal && !bypassed) onToast("Joc reluat.", "info");
    },
    [actionOwner, onToast],
  );

  const { recovery: resumeRecovery, retryResume, cancelResume, dismissRecovery } = useSavedGameResume({
    active,
    load: getLant,
    isTerminal: isTerminalResume,
    setPending: setLoading,
    onResume: applyResumedGame,
    onDailyBypassed: () => onToast("Ai continuat jocul liber început. Provocarea zilei te așteaptă după ce îl termini.", "info"),
  });

  const exitSafely = useCallback(() => {
    if (!startInFlight.current) onExit();
  }, [onExit]);

  // Giving up forgets only a settled live board: an uncertain move keeps its pointer
  // so ordinary saved-game recovery can still reconcile it.
  const abandonChain = useCallback(() => {
    if (startInFlight.current || actionOwner.hasPending() || actionSync) return;
    actionOwner.invalidate();
    cancelResume();
    dismissRecovery();
    if (state) active.forgetIfCurrent(state.game_id);
    setHint(null);
    setProgress(null);
    setRecovery(null);
    setScored(null);
    setText("");
    pendingActionFocus.current = null;
    setState(null);
  }, [active, state, actionOwner, actionSync, cancelResume, dismissRecovery]);

  const start = useCallback(
    async (opts?: { difficulty?: Difficulty; daily?: string }) => {
      if (startInFlight.current) return;
      startInFlight.current = true;
      actionOwner.invalidate();
      pendingActionFocus.current = null;
      cancelResume();
      setStartFailed(false);
      setCreating(true);
      try {
        const fresh = await createLant({
          difficulty: opts?.difficulty ?? difficulty,
          daily: opts?.daily,
          // The theme applies to picked games only; the daily stays the shared classic.
          category: opts?.daily ? undefined : (category ?? undefined),
        });
        active.remember(fresh.game_id);
        dismissRecovery();
        setActionSync(null);
        setBusy(false);
        setHint(fresh.earned_hint ?? null);
        setProgress(null);
        setRecovery(null);
        setScored(null);
        setState(fresh);
        setText("");
      } catch {
        setStartFailed(true);
      } finally {
        startInFlight.current = false;
        setCreating(false);
      }
    },
    [difficulty, category, active, actionOwner, cancelResume, dismissRecovery],
  );

  // Record the score exactly once when the game is won.
  useEffect(() => {
    if (!state?.won || state.score === undefined) return;
    const score = state.score;
    const detail = `${state.moves}/${state.optimal} salturi${
      state.daily ? ` · ${state.daily}` : ""
    }`;
    let current = true;
    void recordOnce(state.game_id, score, detail, {
      puzzleKey,
      difficulty: state.difficulty,
      daily: state.daily,
      category: state.board_category,
    }).then((outcome) => {
      active.forgetIfCurrent(state.game_id);
      if (!current || !outcome) return;
      const { isBest, isPuzzleBest } = outcome;
      setScored({ score, isBest, isPuzzleBest });
      if (isBest || isPuzzleBest) sound.playRecord();
    });
    return () => {
      current = false;
    };
  }, [state, puzzleKey, recordOnce, active]);

  const currentGameId = state?.game_id;
  const won = state?.won ?? false;

  useEffect(() => {
    if (!currentGameId || won || busy || loading || creating || actionSync) return;
    if (initiallyFocusedGame.current === currentGameId) return;
    initiallyFocusedGame.current = currentGameId;
    // Focus only a newly opened round, without stealing navigation during loading
    // or summoning the phone keyboard over the tap-first local choices.
    if (active.peek() === currentGameId &&
        (document.activeElement === document.body || document.activeElement === inputRef.current)) {
      focusInputForFinePointer();
    }
  }, [currentGameId, won, busy, loading, creating, actionSync, active, focusInputForFinePointer]);

  useEffect(() => {
    const pending = pendingActionFocus.current;
    if (busy || loading || creating || !pending?.ready) return;
    pendingActionFocus.current = null;
    if (won || actionSync || currentGameId !== pending.ticket.gameId ||
        active.peek() !== pending.ticket.gameId) return;
    const focused = document.activeElement;
    if (focused !== document.body && focused !== pending.origin) return;
    const input = inputRef.current;
    if (pending.origin.closest(".word-hop-input") && input && !input.disabled) {
      input.focus({ preventScroll: true });
      return;
    }
    // Keep the initiating input/button when it survives. A used hint can linger
    // briefly during its exit animation, so focus the next usable link instead.
    if (pending.origin.isConnected && !pending.origin.matches(":disabled") &&
        !pending.origin.closest(".lant-hint-panel")) {
      if (focused !== pending.origin) pending.origin.focus({ preventScroll: true });
      return;
    }
    const nextChoice = choicesRef.current?.querySelector<HTMLButtonElement>("button:not(:disabled)");
    if (nextChoice) nextChoice.focus({ preventScroll: true });
    else if (input && !input.disabled) input.focus({ preventScroll: true });
  }, [busy, loading, creating, currentGameId, won, actionSync, active]);

  // On the win screen, Enter starts another chain with the same free-play filters.
  useEffect(() => {
    if (!state?.won) return;
    const onKey = (e: KeyboardEvent) => {
      if (startInFlight.current) return;
      const target = e.target instanceof Element ? e.target : null;
      if (
        e.defaultPrevented ||
        target?.closest('button, a, input, textarea, select, summary, [role="button"], [contenteditable="true"]')
      ) {
        return;
      }
      if (e.key === "Enter") {
        e.preventDefault();
        void start({ difficulty: state.difficulty });
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [state?.won, state?.difficulty, start]);

  const actionsLocked = busy || loading || actionSync !== null;
  // Moves spent beyond the optimal path length from the original start.
  const overPar = useMemo(() => {
    if (!state) return 0;
    return state.moves - state.optimal;
  }, [state]);
  // True distance left, learned from the most recent hint for THIS current node.
  const hintRemaining = hint?.remaining ?? null;

  function beginAction(previous: LantState) {
    if (startInFlight.current) return null;
    const ticket = actionOwner.begin(previous.game_id);
    if (!ticket) return null;
    if (!actionOwner.owns(ticket)) {
      actionOwner.finish(ticket);
      setRecovery(null);
      setActionSync({ gameId: previous.game_id, kind: "changed" });
      return null;
    }
    const origin = document.activeElement;
    pendingActionFocus.current = origin instanceof HTMLElement && origin !== document.body
      ? { ticket, origin, ready: false }
      : null;
    return ticket;
  }

  function finishAction(ticket: GameActionTicket) {
    if (!actionOwner.finish(ticket)) {
      if (pendingActionFocus.current?.ticket === ticket) pendingActionFocus.current = null;
      return;
    }
    if (pendingActionFocus.current?.ticket === ticket) pendingActionFocus.current.ready = true;
    setBusy(false);
  }

  function mayAdoptAction(ticket: GameActionTicket) {
    if (!actionOwner.isCurrent(ticket)) return false;
    if (!actionOwner.owns(ticket)) {
      setActionSync({ gameId: ticket.gameId, kind: "changed" });
      return false;
    }
    return true;
  }

  async function reconcileAction(ticket: GameActionTicket, previous: LantState) {
    const outcome = await recoverOwnedGameAction(
      actionOwner, ticket, getLant,
      (error) => error instanceof ApiError && error.status === 404,
    );
    if (!mayAdoptAction(ticket)) return;
    if (outcome.kind === "missing") {
      if (ticket.savedId === ticket.gameId && !active.forgetIfCurrent(ticket.gameId)) {
        setActionSync({ gameId: ticket.gameId, kind: "changed" });
        return;
      }
      setActionSync(null);
      setState(null);
      onToast("Jocul nu mai este disponibil. Poți începe altul.", "info");
      return;
    }
    if (outcome.kind !== "recovered") {
      setActionSync({ gameId: ticket.gameId, kind: outcome.kind === "changed" ? "changed" : "failed" });
      return;
    }
    const fresh = outcome.state;
    setActionSync(null);
    setState(fresh);
    setHint(fresh.earned_hint ?? null);
    // GET carries authoritative position and earned help, not a reconstructed move verdict.
    setProgress(null);
    if (fresh.current.id !== previous.current.id || fresh.won) setText("");
    setRecovery(fresh.won ? null : {
      message: "Joc sincronizat. Poți continua.", choices: [], tone: "info",
    });
    if (fresh.won && !previous.won) sound.playWin();
  }

  async function retryActionSync() {
    if (!state || busy || !actionSync) return;
    if (actionSync.kind === "changed") {
      actionOwner.invalidate();
      setActionSync(null);
      setState(null);
      setLoading(true);
      retryResume();
      return;
    }
    if (state.game_id !== actionSync.gameId) return;
    const ticket = beginAction(state);
    if (!ticket) return;
    setBusy(true);
    try {
      await reconcileAction(ticket, state);
    } finally {
      finishAction(ticket);
    }
  }

  async function submit(choice?: LantChoice) {
    if (!state || actionsLocked || won) return;
    const value = (choice?.label ?? text).trim();
    if (!value) return;
    const ticket = beginAction(state);
    if (!ticket) return;
    setBusy(true);
    setProgress(null);
    setRecovery(null);
    try {
      const res = await moveLant(state.game_id, value);
      if (!mayAdoptAction(ticket)) return;
      if (!res.ok) {
        sound.playError();
        setShake((s) => s + 1);
        const message = res.last_error ?? "Mutare invalidă";
        setRecovery({
          message,
          choices: res.suggestions ?? [],
          tone: "warning",
        });
        return;
      }
      setHint(null);
      // Successful hop: server returns the partial state — fold it into our full state.
      setState((prev) =>
        prev?.game_id === ticket.gameId
          ? {
              ...prev,
              earned_hint: undefined,
              current: res.current ?? prev.current,
              path: res.path ?? prev.path,
              moves: res.moves ?? prev.moves,
              won: res.won ?? prev.won,
              score: res.score ?? prev.score,
              share: res.share ?? prev.share,
              choices: res.choices ?? prev.choices,
              backtrack_recommended:
                res.backtrack_recommended ?? prev.backtrack_recommended,
            }
          : prev,
      );
      setProgress(res.progress ?? null);
      setText("");
      if (res.message) {
        setRecovery({
          message: res.message,
          choices: [],
          tone: res.dead_end ? "warning" : "info",
        });
      }
      if (res.won) {
        sound.playWin();
        onToast("Ai ajuns la țintă!", "success");
      } else {
        sound.playHop();
      }
    } catch {
      await reconcileAction(ticket, state);
    } finally {
      finishAction(ticket);
    }
  }

  async function handleUndo() {
    if (!state || actionsLocked || won || state.moves === 0) return;
    const ticket = beginAction(state);
    if (!ticket) return;
    setBusy(true);
    setHint(null);
    setProgress(null);
    setRecovery(null);
    try {
      const fresh = await undoLant(state.game_id);
      if (!mayAdoptAction(ticket)) return;
      setState(fresh);
      setHint(fresh.earned_hint ?? null);
      sound.playUndo();
    } catch {
      await reconcileAction(ticket, state);
    } finally {
      finishAction(ticket);
    }
  }

  async function handleHint() {
    if (!state || actionsLocked || won) return;
    const ticket = beginAction(state);
    if (!ticket) return;
    setBusy(true);
    setRecovery(null);
    try {
      const res = await hintLant(state.game_id);
      if (!mayAdoptAction(ticket)) return;
      setHint(res);
      setState((previous) => previous?.game_id === ticket.gameId
        ? { ...previous, earned_hint: res } : previous);
      if (res.hint || res.stage) {
        sound.playSelect();
      } else {
        const message = res.message ?? "Niciun indiciu.";
        setRecovery({ message, choices: [], tone: "warning" });
      }
    } catch {
      await reconcileAction(ticket, state);
    } finally {
      finishAction(ticket);
    }
  }

  async function handleCopy() {
    if (!sharePayload) return;
    const ok = await copyResult(sharePayload);
    if (ok) onToast("Copiat!", "info");
    else onToast("Nu am putut copia.", "error");
  }

  if (loading && !state) {
    return (
      <div className="screen-pad fill center">
        <Spinner size="lg" label="Se încarcă…" />
      </div>
    );
  }

  // Intro: difficulty picker + daily challenge.
  if (!state) {
    return (
      <div className="screen-pad fill" aria-busy={creating}>
        {creating && <span className="visually-hidden" role="status">Se pregătește jocul…</span>}
        <div inert={creating} className="container col game-container" style={{ gap: 18 }}>
          <GameShell onExit={exitSafely} accent={DEF.accent} busy={creating} />

          <GameIntro
            startFailed={startFailed}
            resumeRecovery={resumeRecovery ? {
              kind: resumeRecovery.kind,
              canRetry: resumeRecovery.kind === "failed" || resumeRecovery.hasCurrent,
              onRetry: retryResume,
            } : null}
            icon={DEF.icon}
            title={DEF.title}
            tag={DEF.tag}
            accent={DEF.accent}
            glow={DEF.glow}
            description={
              <div className="col" style={{ gap: 8 }}>
                <p style={{ margin: 0 }}>
                  Ajungi la țintă prin concepte legate direct.
                </p>
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  className="lant-intro-disclosure-toggle"
                  aria-expanded={showHow}
                  aria-controls="lant-intro-disclosure"
                  onClick={() => setShowHow((v) => !v)}
                >
                  Cum funcționează <span aria-hidden>{showHow ? "▲" : "▼"}</span>
                </Button>
                {showHow && (
                  <ul id="lant-intro-disclosure" className="lant-intro-disclosure faint">
                    <li>Salturile afișate amestecă drumul cel mai scurt cu ocoluri sigure.</li>
                    <li>Înapoi e gratuit și nelimitat.</li>
                    <li>Poți scrie orice concept legat — nu doar din listă.</li>
                    <li>Limită: 64 de salturi pe lanț.</li>
                  </ul>
                )}
              </div>
            }
            steps={[
              { icon: "👆", label: "Alege o legătură" },
              { icon: "🔗", label: "Fă un salt" },
              { icon: "🎯", label: "Ajungi la țintă" },
            ]}
            best={best}
            startLabel="Joacă →"
            onStart={() => void start({ difficulty })}
            onDaily={() => void start({ difficulty, daily: todayLocal() })}
            dailyLabel="Provocarea zilei"
            starting={creating || loading}
          >
            <GameSetupOptions>
              <DifficultyPicker
                options={DIFFICULTIES.map((d) => ({ id: d.key, label: d.label, hint: d.hint }))}
                value={difficulty}
                onChange={(id) => {
                  sound.playSelect();
                  setDifficulty(id);
                }}
              />
              <CategoryPicker
                game="lant"
                difficulty={difficulty}
                value={category}
                onChange={(key) => {
                  sound.playSelect();
                  setCategory(key);
                }}
                onInvalid={() => setCategory(null)}
                accent={DEF.accent}
              />
            </GameSetupOptions>
          </GameIntro>
        </div>
      </div>
    );
  }

  return (
    <div className="screen-pad fill lant-screen" aria-busy={creating}>
      {creating && <span className="visually-hidden" role="status">Se pregătește jocul…</span>}
      <div inert={creating} className="container col game-container">
        {/* header */}
        <GameShell onExit={exitSafely} accent={DEF.accent} title={DEF.title} busy={creating}>
          <Hud>
            <StatBadge
              label="SALTURI"
              value={`${state.moves} ${roNoun(state.moves, "salt", "salturi")}`}
              accent={DEF.accent}
              title="Salturi făcute"
            />
          </Hud>
        </GameShell>

        <section className="card lant-route" aria-label="Poziția și ținta">
          <div className="lant-current" aria-live={won ? "off" : "polite"} aria-atomic="true">
            <span className="faint">EȘTI ACUM LA</span>
            <div
              className="lant-route-word"
              style={{ color: won ? TARGET_COLOR : DEF.accent }}
            >
              {state.current.label}
            </div>
          </div>
          <span className="lant-route-arrow muted" aria-hidden>→</span>
          <div className="lant-target">
            <span className="faint">ȚINTĂ</span>
            <strong className="lant-route-word" style={{ color: TARGET_COLOR }}>
              {state.target.label}
            </strong>
          </div>
          {state.target.description && (
            <p className="muted lant-target-description">{state.target.description}</p>
          )}
        </section>

        {!won && state.choices?.length > 0 ? (
          <section ref={choicesRef} className="lant-choice-panel col" aria-labelledby="lant-choice-title">
            <div className="spread row" style={{ gap: 10, alignItems: "baseline" }}>
              <strong id="lant-choice-title">Atinge următorul cuvânt</strong>
            </div>
            <div className="lant-choice-grid">
              {state.choices.map((choice) => (
                <button
                  key={`${choice.label}-${choice.relation}`}
                  type="button"
                  className="lant-choice"
                  disabled={actionsLocked}
                  aria-label={`Salt la ${choice.label}: ${choice.relation}`}
                  onClick={() => void submit(choice)}
                >
                  <strong>{choice.label}</strong>
                  <span>{choice.relation}</span>
                </button>
              ))}
            </div>
          </section>
        ) : null}

        {progress ? (
          <m.div
            key={progress.kind + "-" + state.moves}
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            className={"lant-progress lant-progress--" + progress.kind}
            role="status"
            aria-live="polite"
          >
            <span aria-hidden="true">{PROGRESS_ICON[progress.kind]}</span>
            <strong>{progress.message}</strong>
          </m.div>
        ) : null}

        <span
          className="visually-hidden"
          role="status"
          aria-live="polite"
          aria-atomic="true"
        >
          {recovery?.message ?? ""}
        </span>

        {/* input + actions OR win */}
        {won ? (
          <ResultCard
              startFailed={startFailed}
              actionsBusy={creating}
            icon={state.moves <= state.optimal ? "★" : "✦"}
            title={state.moves <= state.optimal ? "Lanț perfect!" : "Ai reușit!"}
            accent={TARGET_COLOR}
            score={state.score}
            isRecord={scored?.isBest ?? false}
            isPuzzleRecord={scored?.isPuzzleBest ?? false}
            shareText={sharePayload}
            onCopy={() => void handleCopy()}
            onReplay={() => void start({ difficulty: state.difficulty })}
            onOptions={() => {
              if (startInFlight.current) return;
              setState(null);
            }}
            onExit={exitSafely}
            replayLabel="Încă un lanț →"
          >
            Ai ajuns la <strong style={{ color: "var(--text)" }}>{state.target.label}</strong>{" "}
            în <strong style={{ color: "var(--text)" }}>{state.moves}</strong>{" "}
            {roNoun(state.moves, "salt", "salturi")} (drumul cel mai scurt: {state.optimal}).
            {recovery?.message ? (
              <span className="muted" style={{ display: "block", marginTop: 8 }}>
                <span aria-hidden="true" style={{ marginRight: 6 }}>
                  ℹ
                </span>
                {recovery.message}
              </span>
            ) : null}
          </ResultCard>
        ) : (
          <m.div
            key={shake}
            animate={shake ? { x: [0, -8, 8, -6, 6, 0] } : {}}
            transition={{ duration: 0.32 }}
            className="col"
            style={{ gap: 10 }}
          >
        {actionSync ? (
          <div className="card col lant-sync-recovery" role="alert" style={{ gap: 8, padding: 12 }}>
            <strong>{actionSync.kind === "changed" ? "Jocul salvat s-a schimbat." : "Verificarea jocului nu a reușit."}</strong>
            <span>{actionSync.kind === "changed"
              ? "Încarcă jocul curent pentru a continua."
              : "Acțiunea poate fi deja salvată. Verifică jocul înainte de următorul salt sau indiciu."}</span>
            <Button type="button" onClick={() => void retryActionSync()} disabled={busy}>
              {busy ? "Se verifică…" : actionSync.kind === "changed" ? "Încarcă jocul curent" : "Verifică jocul"}
            </Button>
          </div>
        ) : null}

            <div className="row word-hop-input" style={{ gap: 8 }}>
              <input
                ref={inputRef}
                className="field fill"
                placeholder="Sau scrie alt concept…"
                value={text}
                disabled={actionsLocked}
                onChange={(e) => setText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") void submit();
                  else if (e.key === "Escape") setText("");
                }}
                autoComplete="off"
                autoCapitalize="off"
                autoCorrect="off"
                spellCheck={false}
                enterKeyHint="send"
                aria-label="Următorul concept"
                style={{ flex: 1 }}
              />
              <Button
                type="button"
                disabled={actionsLocked || !text.trim()}
                onClick={() => void submit()}
              >
                {busy ? "…" : "Salt"}
              </Button>
            </div>

            <div className="row wrap lant-tools" style={{ gap: 8 }}>
              <Button
                type="button"
                variant="secondary"
                className={
                  state.backtrack_recommended || hint?.stage === "backtrack"
                    ? "lant-undo lant-undo--recommended"
                    : "lant-undo"
                }
                disabled={actionsLocked || state.moves === 0}
                onClick={() => void handleUndo()}
                aria-label={
                  state.backtrack_recommended
                    ? "Înapoi, recomandat după două salturi fără progres"
                    : "Înapoi"
                }
              >
                {state.backtrack_recommended ? "↶ Înapoi · recomandat" : "↶ Înapoi"}
              </Button>
              <Button
                type="button"
                variant="secondary"
                disabled={actionsLocked}
                onClick={() => void handleHint()}
              >
                {hint?.stage === "direction" || hint?.stage === "alternatives"
                  ? "💡 Mai clar"
                  : "💡 Indiciu"}
              </Button>
            </div>

            <AnimatePresence>
              {recovery && (
                <m.div
                  key={`${recovery.tone}-${recovery.message}`}
                  initial={{ opacity: 0, y: -6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -6 }}
                  className="card"
                  style={{
                    padding: 12,
                    borderColor:
                      recovery.tone === "warning" ? "var(--bad)" : DEF.accent,
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
                            disabled={actionsLocked}
                            onClick={() => {
                              setText(choice);
                              focusInputForFinePointer();
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

            <AnimatePresence>
              {hint && (hint.stage || hint.hint) && (
                <m.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="card lant-hint-panel"
                  style={{ padding: 12, borderColor: "var(--warn)" }}
                  role="status"
                  aria-live="polite"
                >
                  <div className="col" style={{ gap: 8 }}>
                    <strong style={{ color: "var(--warn)", fontSize: "0.8rem" }}>
                      {hint.stage === "direction"
                        ? "O DIRECȚIE"
                        : hint.stage === "alternatives"
                          ? "VARIANTE UTILE"
                          : hint.stage === "backtrack"
                            ? "UN PAS ÎNAPOI"
                            : "UN SALT"}
                    </strong>
                    {hint.message ? (
                      <span className="muted" style={{ fontSize: "0.85rem" }}>
                        {hint.message}
                      </span>
                    ) : null}
                    {hintRemaining !== null && (
                      <span className="muted">
                        {hintRemaining <= 1
                          ? "Ești la un pas de țintă!"
                          : `${hintRemaining} ${roNoun(hintRemaining, "salt", "salturi")} până la țintă`}
                      </span>
                    )}
                    {hint.alternatives_choices?.length ? (
                      <div className="row wrap" style={{ gap: 8 }}>
                        {hint.alternatives_choices.map((choice) => (
                          <Button
                            key={`${choice.label}-${choice.relation}`}
                            type="button"
                            variant="secondary"
                            title={choice.relation}
                            disabled={actionsLocked}
                            aria-label={`Salt la ${choice.label}: ${choice.relation}`}
                            onClick={() => void submit(choice)}
                          >
                            {choice.label}
                          </Button>
                        ))}
                      </div>
                    ) : null}
                    {hint.hint ? (
                      <button
                        type="button"
                        className="hint-fill-button"
                        disabled={actionsLocked}
                        title="Fă acest salt"
                        aria-label={`Salt la ${hint.hint.label}${hint.relation ? `: ${hint.relation}` : ""}`}
                        onClick={() => {
                          if (hint.hint) void submit({ label: hint.hint.label, relation: hint.relation ?? "" });
                        }}
                      >
                        Încearcă <strong>{hint.hint.label}</strong>
                        {hint.relation ? ` · ${hint.relation}` : ""}
                      </button>
                    ) : null}
                  </div>
                </m.div>
              )}
            </AnimatePresence>
          </m.div>
        )}

        <GameOptions game="lant">
          <p className="muted lant-round-details">
            De la <strong>{state.start.label}</strong> la <strong>{state.target.label}</strong>.
            {" "}Drumul cel mai scurt: {state.optimal} {roNoun(state.optimal, "salt", "salturi")}{overPar > 0 ? ` · ai făcut ${overPar} ${roNoun(overPar, "salt", "salturi")} în plus` : ""}.
            {state.daily ? ` Provocarea zilei: ${formatDayKey(state.daily)}.` : ""}
            {state.board_category ? ` Categoria: ${categoryLabel(state.board_category)}.` : ""}
          </p>
          <strong>Drumul tău</strong>
          <Breadcrumb path={state.path} />
          {!state.won && (
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={abandonChain}
              disabled={busy || creating || actionSync !== null}
              title="Renunță la acest lanț și alege altul"
            >
              Începe alt lanț
            </Button>
          )}
        </GameOptions>
      </div>
    </div>
  );
}
