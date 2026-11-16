import { Csp } from "../components/CspStyle";
// CaldRece — "Cald sau Rece" (Contexto/Semantle-style) screen.
//
// A hidden secret concept lives on the server. The player types concept guesses; each
// guess comes back with a rank, graph distance, temperature tier, and 0..100 closeness.
// The server is the only source of truth (it holds the secret + sorts the guess list
// best-first); this component only renders what it returns and surfaces errors as toasts.

import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "preact/hooks";
import { Presence, useIsPresent, type PresenceVariant } from "@roedu/ui/motion";
import { useElementMotion } from "../hooks/useElementMotion";
import { Button, type ToastKind } from "@roedu/ui";
import { CONTEXTO_HELP } from "../gameHelp/contexto.mjs";
import { GameFrame, Attempts, CoachLine } from "../components/GameFrame";
import { FreeRoundOptions } from "../components/FreeRoundOptions";
import { HintBar } from "../components/HintBar";
import { useGameEntry, useRoundStart } from "../hooks/useGameEntry";
import { ResultCard } from "../components/ResultCard";
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
import { useRecordScore } from "../hooks/useRecordScore";
import { useActiveGame } from "../hooks/useActiveGame";
import { useSavedGameResume } from "../hooks/useSavedGameResume";
import {
  createGameActionOwner,
  recoverOwnedGameAction,
  type GameActionTicket,
} from "../gameActionRecovery.mjs";
import { gameByKey } from "../games";
import { buildSharePayload, copyResult, stableKey } from "../share";

const GAME_KEY = "contexto";
const DEF = gameByKey("contexto");
const RECOVERY_VARIANT: PresenceVariant = { enter: { opacity: [0, 1], transform: ["translateY(-6px)", "translateY(0px)"] }, exit: { opacity: [1, 0], transform: ["translateY(0px)", "translateY(-6px)"] } };

const isTerminalResume = (state: ContextoState) => state.won || state.gave_up;

const DIFFICULTY_LABEL: Record<Difficulty, string> = {
  usor: "Ușor",
  normal: "Normal",
  greu: "Greu",
};

type GuessRecovery = {
  message: string;
  choices: string[];
  tone: "info" | "warning";
  /** A fuzzy correction the player must accept before it costs an attempt. */
  confirm?: { label: string; token: string };
};

type GuessView = "best" | "recent";
type ActionSync = { gameId: string; kind: "failed" | "changed" };

const TEMP_ICON: Record<Temperature, string> = {
  Gasit: "🎯",
  Fierbinte: "🔥",
  Cald: "♨️",
  Caldut: "🌤️",
  Rece: "❄️",
  "Foarte rece": "🥶",
  Inghetat: "🧊",
};

// API tokens stay ASCII for compatibility; only their player-facing labels are localized.
const THERMOMETER_ZONES: Temperature[] = ["Inghetat", "Rece", "Caldut", "Cald", "Fierbinte", "Gasit"];

const TEMP_LABEL: Record<Temperature, string> = {
  Gasit: "Găsit",
  Fierbinte: "Fierbinte",
  Cald: "Cald",
  Caldut: "Călduț",
  Rece: "Rece",
  "Foarte rece": "Foarte rece",
  Inghetat: "Înghețat",
};

function GuessRow({ g, isLatest }: { g: Guess; isLatest: boolean }) {
  const pct = Math.max(2, Math.min(100, g.closeness));
  const element = useRef<HTMLDivElement>(null);
  useElementMotion(element, isLatest ? { opacity: [0, 1], transform: ["translateY(-10px) scale(0.97)", "translateY(0px) scale(1)"] } : false,
    { spring: { stiffness: 380, damping: 28 } }, []);
  return (
    <Csp.div ref={element} className="card contexto-guess-row" data-temperature={g.temperature}
      css={{ "--guess-progress": `${pct}%` }}>
      <strong>{g.label}</strong>
      <span className="contexto-temperature">
        <span aria-hidden="true">{TEMP_ICON[g.temperature]}</span> {TEMP_LABEL[g.temperature]}
      </span>
      <strong className="contexto-rank" title="Locul 1 este cuvântul secret">#{g.rank}</strong>
    </Csp.div>
  );
}

function RevealCancelButton({ disabled, onCancel }: { disabled: boolean; onCancel: () => void }) {
  const element = useRef<HTMLButtonElement>(null), present = useIsPresent();
  // Presence mounts this child in its own commit, after the parent's request.
  useLayoutEffect(() => { if (present && !disabled) element.current?.focus(); }, [present, disabled]);
  return <Button type="button" variant="secondary" size="sm" ref={element} onClick={onCancel} disabled={disabled || !present}>Nu</Button>;
}

export default function CaldRece({
  onExit,
  onToast,
}: {
  onExit: () => void;
  onToast: (message: string, kind?: ToastKind) => void;
}) {
  const isPresent = useIsPresent(), liveRef = useRef(true);
  const active = useActiveGame(GAME_KEY);
  const entry = useGameEntry(GAME_KEY, active);
  const { admit, remember, complete, settleCompletion } = entry;
  const lifetimeRef = useRef(0);
  const [state, setState] = useState<ContextoState | null>(null);
  const [startFailed, setStartFailed] = useState(false);
  const [unavailable, setUnavailable] = useState(false);
  const startInFlightRef = useRef(false);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(() => active.peek() !== null);
  const [feedbackRevision, repeatFeedback] = useState(0);
  const [latestId, setLatestId] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<GuessFeedback | null>(null);
  const [guessView, setGuessView] = useState<GuessView>("best");
  const [confirmReveal, setConfirmReveal] = useState(false);
  const [recovery, setRecovery] = useState<GuessRecovery | null>(null);
  const [actionSync, setActionSync] = useState<ActionSync | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const restoreInputFocusRef = useRef(false);
  const recordOnce = useRecordScore("contexto");
  const actionOwner = useMemo(() => createGameActionOwner(active), [active]);

  useLayoutEffect(() => {
    liveRef.current = isPresent;
    if (!isPresent) { actionOwner.invalidate(); restoreInputFocusRef.current = false; }
    return () => { liveRef.current = false; lifetimeRef.current += 1; actionOwner.invalidate(); };
  }, [actionOwner, isPresent]);

  const applyResumedGame = useCallback(
    (saved: ContextoState, { terminal }: { terminal: boolean }) => {
      if (!liveRef.current || !admit(saved, terminal)) return;
      actionOwner.invalidate();
      setActionSync(null);
      setStartFailed(false);
      setState(saved);


      setLatestId(null);
      setFeedback(null);
      setGuessView("best");
      setConfirmReveal(false);
      setText("");
      setRecovery(null);



      restoreInputFocusRef.current = true;

    },
    [actionOwner, admit],
  );

  const { recovery: resumeRecovery, retryResume, cancelResume, dismissRecovery } = useSavedGameResume({
    active,
    load: contextoApi.getGame,
    isTerminal: isTerminalResume,
    setPending: setBusy,
    onResume: applyResumedGame,
    onReentry: () => {
      startInFlightRef.current = false;
      setBusy(false); setStartFailed(false); setConfirmReveal(false);
      if (!active.peek() && state) {
        if (!isTerminalResume(state)) setActionSync({ gameId: state.game_id, kind: "failed" });
      } else {
        setState(null); setActionSync(null); setRecovery(null);
      }
    },
  });

  const start = useCallback(
    async (opts: CreateOpts = {}) => {
      if (!liveRef.current || startInFlightRef.current) return;
      startInFlightRef.current = true;
      const epoch = lifetimeRef.current;
      const expected = active.peek();
      actionOwner.invalidate();
      cancelResume();
      setStartFailed(false);
      setUnavailable(false);
      setBusy(true);
      try {
        const fresh = await contextoApi.createGame(opts);
        if (!liveRef.current || epoch !== lifetimeRef.current) return;
        if (!remember(fresh, expected)) {
          setState(null);
          retryResume();
          return;
        }
        setState(fresh);
        dismissRecovery();
        setActionSync(null);
        setLatestId(null);
        setFeedback(null);
        setGuessView("best");
        setConfirmReveal(false);
        setText("");
        setRecovery(null);



        restoreInputFocusRef.current = true;
      } catch {
        if (liveRef.current && epoch === lifetimeRef.current) setStartFailed(true);
      } finally {
        if (epoch === lifetimeRef.current) {
          startInFlightRef.current = false;
          if (liveRef.current) setBusy(false);
        }
      }
    },
    [active, actionOwner, cancelResume, dismissRecovery, remember, retryResume],
  );

  const won = state?.won ?? false;
  const gaveUp = state?.gave_up ?? false;
  const finished = won || gaveUp;

  // A disabled field cannot receive focus in the request's finally block. Wait
  // for an enabled Preact commit, preserving deliberate navigation during a request.
  useLayoutEffect(() => {
    if (!liveRef.current || busy || !restoreInputFocusRef.current) return;
    const input = inputRef.current;
    if (!input || finished || actionSync) return;
    if (input.disabled) return;
    restoreInputFocusRef.current = false;
    if (document.activeElement === document.body || document.activeElement === input) {
      input.focus({ preventScroll: true });
    }
  }, [busy, finished, actionSync]);

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
    if (!state?.target || (!state.won && !state.gave_up)) return null;
    return buildSharePayload({
      gameTitle: DEF.title,
      serverShare: state.share ?? `Am renunțat. Cuvântul secret era „${state.target.label}”.`,
      puzzleKey,
    });
  }, [state, puzzleKey]);

  // Record the score exactly once when a game is won.
  useEffect(() => {
    if (!liveRef.current || !state || (!state.won && !state.gave_up)) return;
    const attemptsLabel = state.attempts === 1 ? "încercare" : "încercări";
    const detail = state.gave_up ? "Renunțare"
      : state.daily ? `Zilnic ${state.daily} · ${state.attempts} ${attemptsLabel}`
      : `${DIFFICULTY_LABEL[state.difficulty]} · ${state.attempts} ${attemptsLabel}`;
    void recordOnce(state.game_id, state.score ?? 0, detail, {
      puzzleKey,
      difficulty: state.difficulty,
      daily: state.daily,
      steps: state.steps,
      category: state.board_category,
    }).then(() => { settleCompletion(state); });
  }, [state, puzzleKey, recordOnce, settleCompletion, isPresent]);

  const beginAction = useCallback((previous: ContextoState) => {
    if (!liveRef.current || startInFlightRef.current) return null;
    const ticket = actionOwner.begin(previous.game_id);
    if (!ticket) return null;
    if (!actionOwner.owns(ticket)) {
      actionOwner.finish(ticket);
      setRecovery(null);
      setConfirmReveal(false);
      setActionSync({ gameId: previous.game_id, kind: "changed" });
      return null;
    }
    return ticket;
  }, [actionOwner]);

  const mayAdoptAction = useCallback((ticket: GameActionTicket) => {
    if (!liveRef.current || !actionOwner.isCurrent(ticket)) return false;
    if (!actionOwner.owns(ticket)) {
      setActionSync({ gameId: ticket.gameId, kind: "changed" });
      return false;
    }
    return true;
  }, [actionOwner]);

  const reconcileAction = useCallback(async (
    ticket: GameActionTicket,
    previous: ContextoState,
  ) => {
    const outcome = await recoverOwnedGameAction(
      actionOwner, ticket, contextoApi.getGame,
      (error) => error instanceof ApiError && error.status === 404,
    );
    if (!mayAdoptAction(ticket)) return;
    if (outcome.kind === "changed") {
      setActionSync({ gameId: ticket.gameId, kind: "changed" });
      return;
    }
    if (outcome.kind === "missing") {
      if (ticket.savedId === ticket.gameId && !active.forgetIfCurrent(ticket.gameId)) {
        setActionSync({ gameId: ticket.gameId, kind: "changed" });
        return;
      }
      setActionSync(null);
      setState(null);
      setUnavailable(true);

      onToast("Jocul nu mai este disponibil. Poți începe altul.", "info");
      return;
    }
    if (outcome.kind !== "recovered") {
      setActionSync({ gameId: ticket.gameId, kind: "failed" });
      return;
    }
    const fresh = outcome.state;
    setActionSync(null);
    setState(fresh);
    setConfirmReveal(false);
    setFeedback(null);
    setLatestId(null);
    if (fresh.won || fresh.gave_up) {
      setText("");
      setRecovery(null);
      if (fresh.won && !previous.won) sound.playWin();
    } else {
      setRecovery({ message: "Joc sincronizat. Poți continua.", choices: [], tone: "info" });
    }
  }, [actionOwner, active, mayAdoptAction, onToast]);

  const retryActionSync = useCallback(async () => {
    if (!state || busy || !actionSync) return;
    if (actionSync.kind === "changed") {
      actionOwner.invalidate();
      setActionSync(null);

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
      if (actionOwner.finish(ticket)) setBusy(false);
    }
  }, [state, busy, actionSync, actionOwner, beginAction, reconcileAction, retryResume]);

  const handleGuess = useCallback(
    // ``confirm`` accepts a correction the server asked about; only then does it count.
    async (e?: Event, confirm?: string) => {
      e?.preventDefault();
      if (!state || busy || finished || actionSync) return;
      const q = text.trim();
      if (!q) return;
      const ticket = beginAction(state);
      if (!ticket) return;
      setConfirmReveal(false);
      setFeedback(null);
      setBusy(true);
      setRecovery(null);
      try {
        const res: GuessResult = await contextoApi.submitGuess(
          state.game_id,
          q,
          confirm,
        );
        if (!mayAdoptAction(ticket)) return;
        if (!res.ok) {
          sound.playError();
          setRecovery({
            message: res.message,
            choices: res.suggestions,
            tone: "warning",
            confirm:
              res.needs_confirmation && res.resolved_label && res.resolved_token
                ? { label: res.resolved_label, token: res.resolved_token }
                : undefined,
          });
          setState((prev) =>
            prev?.game_id === ticket.gameId
              ? {
                  ...prev,
                  guesses: res.guesses,
                  attempts: res.attempts,
                  steps: res.steps,
                  hints_left: res.hints_left,
                  hint_level: res.hint_level,
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
        repeatFeedback((revision) => revision + 1);
        if (res.message) {
          setRecovery({ message: res.message, choices: [], tone: "info" });
        }
        setState((prev) =>
          prev?.game_id === ticket.gameId
            ? {
                ...prev,
                guesses: res.guesses,
                attempts: res.attempts,
                steps: res.steps,
                hints_left: res.hints_left,
                hint_level: res.hint_level,
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
      } catch {
        await reconcileAction(ticket, state);
      } finally {
        if (actionOwner.finish(ticket)) {
          restoreInputFocusRef.current = true;
          setBusy(false);
        }
      }
    },
    [state, busy, finished, text, actionSync, beginAction, mayAdoptAction, reconcileAction, actionOwner],
  );

  const handleClue = useCallback(async () => {
    if (!state || busy || finished || actionSync || !state.hints_left) return;
    const ticket = beginAction(state);
    if (!ticket) return;
    setConfirmReveal(false);
    setBusy(true);
    setRecovery(null);
    try {
      const res = await contextoApi.requestClue(state.game_id);
      if (!mayAdoptAction(ticket)) return;
      sound.playSelect();
      setFeedback(null);
      setState(res);
    } catch {
      await reconcileAction(ticket, state);
    } finally {
      if (actionOwner.finish(ticket)) {
        restoreInputFocusRef.current = true;
        setBusy(false);
      }
    }
  }, [state, busy, finished, actionSync, beginAction, mayAdoptAction, reconcileAction, actionOwner]);

  const handleGiveUp = useCallback(async () => {
    if (!state || busy || finished || actionSync) return;
    const ticket = beginAction(state);
    if (!ticket) return;
    setConfirmReveal(false);
    setFeedback(null);
    setBusy(true);
    setRecovery(null);
    try {
      const res = await contextoApi.giveUp(state.game_id);
      if (!mayAdoptAction(ticket)) return;
      sound.playUndo();
      setState(res);
    } catch {
      await reconcileAction(ticket, state);
    } finally {
      if (actionOwner.finish(ticket)) setBusy(false);
    }
  }, [state, busy, finished, actionSync, beginAction, mayAdoptAction, reconcileAction, actionOwner]);

  const requestRevealConfirmation = useCallback(() => {
    if (!state || busy || finished || actionSync) return;
    sound.playSelect();
    setConfirmReveal(true);
  }, [state, busy, finished, actionSync]);

  const handleCopy = useCallback(async () => {
    if (!sharePayload) return;
    const ok = await copyResult(sharePayload);
    onToast(ok ? "Copiat!" : "Nu am putut copia.", ok ? "info" : "error");
  }, [sharePayload, onToast]);

  const handleExit = useCallback(() => {
    if (startInFlightRef.current) return;
    actionOwner.invalidate();
    setConfirmReveal(false);
    setFeedback(null);
    liveRef.current = false;
    cancelResume();
    onExit();
  }, [actionOwner, cancelResume, onExit]);

  const guesses = state?.guesses ?? [];
  const bestGuess = guesses[0];
  const displayedGuesses =
    guessView === "best"
      ? guesses
      : [...guesses].sort(
          (left, right) => right.attempt_number - left.attempt_number,
        );
  // The most recently played guess (may sort anywhere in the list) — surfaced as an
  // explicit verdict so feedback is always visible, not buried by best-first sorting.
  const latestGuess = latestId
    ? (guesses.find((g) => g.id === latestId) ?? null)
    : null;

  const nextRound = () => void start({ difficulty: entry.options.difficulty, category: entry.options.category ?? undefined });
  const startEntry = useRoundStart(entry, (!state || entry.readyAfterTerminal(state)) && !busy && !startFailed && !resumeRecovery && !unavailable, retryResume,
    (daily) => daily ? void start({ daily, difficulty: "usor" }) : nextRound());
  const mode = entry.mode(state);
  useLayoutEffect(() => {
    if (state && finished && isPresent) complete(state);
  }, [state, finished, isPresent, complete]);

  return (
    <div className="screen-pad fill contexto-screen">
      <div className="container game-container">
        <GameFrame game={DEF} mode={mode} onExit={handleExit} help={CONTEXTO_HELP} busy={busy && (!state || finished)}
          verifying={entry.recoveredTerminal(state) && !entry.readyAfterTerminal(state)}
          startFailed={startFailed} unavailable={unavailable} onStart={() => startEntry(state?.game_id)} resumeRecovery={resumeRecovery} onResume={() => { entry.presentRecovery(); retryResume(); }}
          status={state && !entry.recoveredTerminal(state) && <Attempts remaining={state.attempts} />}
          options={<FreeRoundOptions game={GAME_KEY} value={entry.options} onChange={entry.updateOptions} />}
          tools={state && !finished ? (
            confirmReveal ? (
              <div className="contexto-reveal-confirm" id="contexto-reveal-confirmation" role="alert">
                <span>Arătăm răspunsul?</span>
                <RevealCancelButton onCancel={() => setConfirmReveal(false)} disabled={!isPresent || busy || actionSync !== null} />
                <Button type="submit" onClick={() => void handleGiveUp()} disabled={busy || actionSync !== null}>
                  Da, arată
                </Button>
              </div>
            ) : <Button type="button" variant="secondary" onClick={requestRevealConfirmation} disabled={busy || actionSync !== null}>
              Renunț la rundă și vreau să văd răspunsul
            </Button>
          ) : undefined}>
        {state && !entry.recoveredTerminal(state) && <>
        {!finished && !actionSync && (
          <CoachLine revision={feedbackRevision}>
            {feedback && latestGuess ? `${latestGuess.label} · ${feedback.message}`
              : state.warm_clue?.message ?? state.clue?.message ?? "Scrie un cuvânt și vezi cât de aproape ești."}
          </CoachLine>
        )}

        {/* The guess field stays within reach while the ranked words scroll. */}
        <div className="contexto-sticky-controls">
          {actionSync && !finished && (
            <Csp.div className="card col contexto-sync-recovery" role="alert" css={{ gap: "8px", padding: "12px" }}>
              <span>
                {actionSync.kind === "failed"
                  ? "Nu am putut verifica dacă acțiunea s-a înregistrat. Verifică jocul înainte să continui."
                  : "Jocul salvat s-a schimbat. Încarcă jocul curent pentru a continua."}
              </span>
              <Button type="button" onClick={() => void retryActionSync()} disabled={!isPresent || busy}>
                {busy ? "Se verifică…" : actionSync.kind === "changed" ? "Încarcă jocul curent" : "Verifică jocul"}
              </Button>
            </Csp.div>
          )}
          <Csp.form onSubmit={handleGuess} className="row contexto-input-bar" css={{ gap: "8px" }}>
            <input
              ref={inputRef}
              className="field fill"
              placeholder={finished ? "Joc terminat" : "Încearcă un cuvânt…"}
              value={text}
              onInput={(e) => {
                setText(e.currentTarget.value);
                setRecovery(null);
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
              disabled={!isPresent || busy || finished || actionSync !== null}
              autoComplete="off"
              spellcheck={false}
              aria-label="Concept de ghicit"
              aria-describedby="contexto-rank-guide"
              enterKeyHint="send"
            />
            <Button
              type="submit"
              disabled={!isPresent || busy || finished || actionSync !== null || !text.trim()}
            >
              Trimite
            </Button>
          </Csp.form>
          <p id="contexto-rank-guide" className="faint contexto-rank-guide">
            Un număr mai mic = mai aproape. <strong>#1 este ținta.</strong>
          </p>
        </div>

        <Presence variant={RECOVERY_VARIANT}>
          {!finished && recovery && (
            <Csp.div
              key={`${recovery.tone}-${recovery.message}`}
              className="card" role="alert"
              css={{ padding: "12px" }}
            >
              <Csp.div className="col" css={{ gap: "8px" }}>
                <span>
                  <Csp.span aria-hidden="true" css={{ marginRight: "6px" }}>
                    {recovery.tone === "warning" ? "⚠" : "ℹ"}
                  </Csp.span>
                  {recovery.message}
                </span>
                {recovery.choices.length > 0 ? (
                  <Csp.div className="row wrap" css={{ gap: "8px" }}>
                    <span className="faint">Variante de scriere:</span>
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
                  </Csp.div>
                ) : null}
                {recovery.confirm ? (
                  <Csp.div className="row wrap" css={{ gap: "8px" }}>
                    <Button
                      type="button"
                      className="contexto-confirm-chip"
                      disabled={!isPresent || busy || actionSync !== null}
                      onClick={() => {
                        sound.playSelect();
                        void handleGuess(undefined, recovery.confirm?.token);
                      }}
                    >
                      Joacă {recovery.confirm.label}
                    </Button>
                    <span className="faint">sau corectează textul.</span>
                  </Csp.div>
                ) : null}
              </Csp.div>
            </Csp.div>
          )}
        </Presence>

        {state.warm_clue && !finished && (
          <button type="button" className="btn game-result-secondary contexto-warm-clue-button"
            aria-label={`Pune ${state.warm_clue.label} în câmpul de răspuns`}
            onClick={() => {
              const word = state.warm_clue?.label;
              if (!word) return;
              sound.playSelect();
              setText(word);
              if (window.matchMedia("(pointer: fine)").matches) inputRef.current?.focus();
            }}>
            Încearcă „{state.warm_clue.label}” · #{state.warm_clue.rank}
          </button>
        )}
        {bestGuess && (
          <div className="contexto-best">
            <strong>Cel mai aproape: {bestGuess.label} (#{bestGuess.rank})</strong>
            <div className="contexto-thermometer" role="img" aria-label={`Termometru: ${TEMP_LABEL[bestGuess.temperature]}`}>
              {THERMOMETER_ZONES.map((zone) => (
                <span key={zone} data-temperature={zone}
                  data-current={(bestGuess.temperature === "Foarte rece" ? "Rece" : bestGuess.temperature) === zone || undefined}
                  aria-hidden="true">{TEMP_LABEL[zone]}</span>
              ))}
            </div>
          </div>
        )}
        <div className="row wrap contexto-list-heading">
          <h2 className="contexto-list-title">
            {guessView === "best" ? "Cele mai apropiate cuvinte" : "Ultimele încercări"}
          </h2>
          {guesses.length > 1 && <div className="contexto-guess-tabs" role="group" aria-label="Ordinea încercărilor">
            <button type="button" aria-pressed={guessView === "best"} onClick={() => setGuessView("best")}>Bune</button>
            <button type="button" aria-pressed={guessView === "recent"} onClick={() => setGuessView("recent")}>Recente</button>
          </div>}
        </div>
        <div id="contexto-guess-list" className="col">
          {displayedGuesses.map((g) => <GuessRow key={g.id} g={g} isLatest={g.id === latestId} />)}
        </div>
        {!finished && <HintBar remaining={state.hints_left ?? 0} disabled={!isPresent || busy || actionSync !== null}
          onHint={() => void handleClue()} />}
        {finished && state.target && (
          <ResultCard title={won ? "Ai găsit cuvântul!" : "Conceptul secret era:"} steps={state.steps}
            actionsBusy={busy} onCopy={sharePayload ? handleCopy : undefined} onReplay={() => startEntry(state.game_id)} onExit={handleExit}>
            <strong>{state.target.label}</strong>
            {state.target.description && <p>{state.target.description}</p>}
            {won && recovery?.message && <p>{recovery.message}</p>}
          </ResultCard>
        )}
        </>}
        </GameFrame>
      </div>
    </div>
  );
}
