import { Csp } from "../components/CspStyle";
import type { ComponentProps } from "preact";
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "preact/hooks";
import { Presence, useIsPresent, animateHeight, springs, type PresenceVariant } from "@roedu/ui/motion";
import { useElementMotion } from "../hooks/useElementMotion";
import { Button, type ToastKind } from "@roedu/ui";
import {
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
import { LANT_HELP } from "../gameHelp/lant.mjs";
import { GameFrame, CoachLine } from "../components/GameFrame";
import { FreeRoundOptions } from "../components/FreeRoundOptions";
import { HintBar } from "../components/HintBar";
import { useGameEntry, useRoundStart } from "../hooks/useGameEntry";
import { ResultCard } from "../components/ResultCard";
import { useActiveGame } from "../hooks/useActiveGame";
import { useRecordScore } from "../hooks/useRecordScore";
import { useSavedGameResume } from "../hooks/useSavedGameResume";
import { sound } from "../sound";
import { gameByKey } from "../games";
import { buildSharePayload, copyResult, roNoun, stableKey } from "../share";

const GAME_KEY = "lant";
const DEF = gameByKey("lant");

const isTerminalResume = (state: LantState) => state.won;

// Lanțul Cuvintelor — choose a direct link from CURRENT toward TARGET.
// Free typing remains available for concepts outside the server's local choices.
// All logic is server-authoritative; this screen only renders state + sends actions.

const FEEDBACK_VARIANT: PresenceVariant = { enter: { opacity: [0, 1], transform: ["translateY(-6px)", "translateY(0px)"] }, exit: { opacity: [1, 0], transform: ["translateY(0px)", "translateY(-6px)"] } };
const HINT_VARIANT: PresenceVariant = { enter: { opacity: [0, 1] }, exit: { opacity: [1, 0] }, transition: { spring: springs.gentle } };


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
    <Csp.div className="row wrap breadcrumb-trail" role="group" aria-label="Traseul parcurs"
      tabIndex={0} css={{ gap: "6px", alignItems: "center" }}>
      {path.map((step, index) => <BreadcrumbStep key={`${step.id}-${index}`} step={step} index={index} last={index === path.length - 1} />)}
    </Csp.div>
  );
}

function BreadcrumbStep({ step, index, last }: { step: PathStep; index: number; last: boolean }) {
  const element = useRef<HTMLSpanElement>(null);
  useElementMotion(element, { opacity: [0, 1], transform: ["translateY(-6px) scale(0.8)", "translateY(0px) scale(1)"] },
    { spring: { stiffness: 420, damping: 26 } }, []);
  return <Csp.span ref={element} className="row lant-trail-step" css={{ gap: "6px", alignItems: "center" }}>
            {index > 0 && (
              <Csp.span
                className="faint lant-trail-relation"
                css={{ fontSize: "0.7rem" }}
                title={step.relation}
              >
                ―{step.relation ? ` ${step.relation} →` : " →"}
              </Csp.span>
            )}
            <Csp.span
              className="chip"
              css={{
                borderColor: last ? "var(--surface-border-strong)" : undefined,
                fontWeight: last ? 700 : undefined,
              }}
            >
              {step.label}
            </Csp.span>
          </Csp.span>;
}

function HintPanel(props: ComponentProps<typeof Csp.div>) {
  const element = useRef<HTMLDivElement>(null), present = useIsPresent();
  useLayoutEffect(() => {
    const node = element.current;
    if (!node) return;
    const control = animateHeight(node, present ? 0 : node.getBoundingClientRect().height, present ? node.scrollHeight : 0);
    let active = true;
    void control.then(() => { if (active && present) node.style.height = "auto"; });
    return () => { active = false; control.cancel(); };
  }, [present]);
  return <Csp.div {...props} ref={element} />;
}

export default function Lant({
  onExit,
  onToast,
}: {
  onExit: () => void;
  onToast: (message: string, kind?: ToastKind) => void;
}) {
  const isPresent = useIsPresent(), liveRef = useRef(true);
  const lifetimeRef = useRef(0);
  const active = useActiveGame(GAME_KEY);
  const entry = useGameEntry(GAME_KEY, active);
  const { admit, remember, complete, settleCompletion } = entry;
  const [state, setState] = useState<LantState | null>(null);
  const [startFailed, setStartFailed] = useState(false);
  const [unavailable, setUnavailable] = useState(false);
  const startInFlightRef = useRef(false);
  const [loading, setLoading] = useState(() => active.peek() !== null);
  const [creating, setCreating] = useState(false);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [actionSync, setActionSync] = useState<ActionSync | null>(null);
  const actionOwner = useMemo(() => createGameActionOwner(active), [active]);
  const pendingActionFocusRef = useRef<ActionFocus | null>(null);
  useLayoutEffect(() => {
    liveRef.current = isPresent;
    if (!isPresent) { actionOwner.invalidate(); pendingActionFocusRef.current = null; }
    return () => { liveRef.current = false; lifetimeRef.current += 1; actionOwner.invalidate(); };
  }, [actionOwner, isPresent]);
  const [shake, setShake] = useState(0);
  const [hint, setHint] = useState<HintResult | null>(null);
  const [progress, setProgress] = useState<LantProgress | null>(null);
  const [recovery, setRecovery] = useState<RecoveryFeedback | null>(null);
  const [gaveUp, setGaveUp] = useState(false);
  const [feedbackRevision, repeatFeedback] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const choicesRef = useRef<HTMLElement>(null);
  const initiallyFocusedGameRef = useRef<string | null>(null);

  const focusInputForFinePointer = useCallback(() => {
    if (liveRef.current && window.matchMedia("(pointer: fine)").matches) {
      inputRef.current?.focus();
    }
  }, []);

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
    if (!state || (!state.won && !gaveUp)) return null;
    return buildSharePayload({
      gameTitle: "Lanțul Cuvintelor",
      serverShare: state.share ?? `Am renunțat la lanțul de la „${state.start.label}” la „${state.target.label}”.`,
      puzzleKey,
    });
  }, [state, puzzleKey, gaveUp]);

  const applyResumedGame = useCallback(
    (fresh: LantState, { terminal }: { terminal: boolean }) => {
      if (!liveRef.current || !admit(fresh, terminal)) return;
      actionOwner.invalidate();
      pendingActionFocusRef.current = null;
      setActionSync(null);
      setBusy(false);
      setHint(fresh.earned_hint ?? null);
      setRecovery(null);
      setProgress(null);
      setStartFailed(false);
      setState(fresh);
      setText("");
      setGaveUp(false);
      if (!terminal) onToast("Joc reluat.", "info");
    },
    [actionOwner, admit, onToast],
  );

  const { recovery: resumeRecovery, pending: resumePending, retryResume, cancelResume, dismissRecovery } = useSavedGameResume({
    active,
    load: getLant,
    isTerminal: isTerminalResume,
    setPending: setLoading,
    onResume: applyResumedGame,
    onReentry: () => {
      startInFlightRef.current = false;
      setBusy(false); setCreating(false); setStartFailed(false);
      if (!active.peek() && state) {
        if (!state.won) setActionSync({ gameId: state.game_id, kind: "failed" });
      } else { setState(null); setActionSync(null); setRecovery(null); }
    },
  });

  const exitSafely = useCallback(() => {
    if (!startInFlightRef.current) { liveRef.current = false; actionOwner.invalidate(); cancelResume(); onExit(); }
  }, [actionOwner, cancelResume, onExit]);

  const abandonChain = () => {
    if (!state || !liveRef.current || startInFlightRef.current || actionOwner.hasPending() || actionSync) return;
    actionOwner.invalidate();
    pendingActionFocusRef.current = null;
    complete(state);
    active.forgetIfCurrent(state.game_id);
    setGaveUp(true);
    setHint(null);
    setProgress(null);
    setRecovery(null);
  };

  const start = useCallback(
    async (daily?: string) => {
      if (!liveRef.current || startInFlightRef.current) return;
      startInFlightRef.current = true;
      const epoch = lifetimeRef.current;
      const expected = active.peek();
      actionOwner.invalidate();
      pendingActionFocusRef.current = null;
      cancelResume();
      setStartFailed(false);
      setUnavailable(false);
      setCreating(true);
      try {
        const fresh = await createLant(daily
          ? { daily, difficulty: "usor" }
          : { difficulty: entry.options.difficulty, category: entry.options.category ?? undefined });
        if (!liveRef.current || epoch !== lifetimeRef.current) return;
        if (!remember(fresh, expected)) {
          setState(null);
          retryResume();
          return;
        }
        setGaveUp(false);
        dismissRecovery();
        setActionSync(null);
        setBusy(false);
        setHint(fresh.earned_hint ?? null);
        setProgress(null);
        setRecovery(null);
        setState(fresh);
        setText("");
      } catch {
        if (liveRef.current && epoch === lifetimeRef.current) setStartFailed(true);
      } finally {
        if (epoch === lifetimeRef.current) {
          startInFlightRef.current = false;
          if (liveRef.current) setCreating(false);
        }
      }
    },
    [active, actionOwner, cancelResume, dismissRecovery, entry.options, remember, retryResume],
  );

  const currentGameId = state?.game_id;
  const won = state?.won ?? false;
  const finished = won || gaveUp;

  useEffect(() => {
    if (!liveRef.current || !state || !finished) return;
    const detail = gaveUp ? "Renunțare" : `${state.moves}/${state.optimal} salturi`;
    void recordOnce(state.game_id, state.score ?? 0, detail, {
      puzzleKey,
      difficulty: state.difficulty,
      daily: state.daily,
      steps: state.steps,
      category: state.board_category,
    }).then(() => { settleCompletion(state); });
  }, [state, finished, gaveUp, puzzleKey, recordOnce, settleCompletion]);

  useLayoutEffect(() => {
    if (!liveRef.current || !currentGameId || won || busy || loading || creating || actionSync || inputRef.current?.disabled) return;
    if (initiallyFocusedGameRef.current === currentGameId) return;
    initiallyFocusedGameRef.current = currentGameId;
    // Focus only a newly opened round, without stealing navigation during loading
    // or summoning the phone keyboard over the tap-first local choices.
    if (active.peek() === currentGameId &&
        (document.activeElement === document.body || document.activeElement === inputRef.current)) {
      focusInputForFinePointer();
    }
  }, [currentGameId, won, busy, loading, creating, actionSync, active, focusInputForFinePointer]);

  useLayoutEffect(() => {
    const pending = pendingActionFocusRef.current;
    if (!liveRef.current || busy || loading || creating || !pending?.ready) return;
    pendingActionFocusRef.current = null;
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

  const actionsLocked = !isPresent || busy || loading || creating || gaveUp || actionSync !== null;

  function beginAction(previous: LantState) {
    if (!liveRef.current || startInFlightRef.current) return null;
    const ticket = actionOwner.begin(previous.game_id);
    if (!ticket) return null;
    if (!actionOwner.owns(ticket)) {
      actionOwner.finish(ticket);
      setRecovery(null);
      setActionSync({ gameId: previous.game_id, kind: "changed" });
      return null;
    }
    const origin = document.activeElement;
    pendingActionFocusRef.current = origin instanceof HTMLElement && origin !== document.body
      ? { ticket, origin, ready: false }
      : null;
    return ticket;
  }

  function finishAction(ticket: GameActionTicket) {
    if (!actionOwner.finish(ticket)) {
      if (pendingActionFocusRef.current?.ticket === ticket) pendingActionFocusRef.current = null;
      return;
    }
    if (pendingActionFocusRef.current?.ticket === ticket) pendingActionFocusRef.current.ready = true;
    setBusy(false);
  }

  function mayAdoptAction(ticket: GameActionTicket) {
    if (!liveRef.current || !actionOwner.isCurrent(ticket)) return false;
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
      setUnavailable(true);
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
              steps: res.steps,
              perfect: res.perfect,
              hints_left: res.hints_left,
              hint_level: res.hint_level,
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
      repeatFeedback((revision) => revision + 1);
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
    if (!state || actionsLocked || won || !state.hints_left) return;
    const ticket = beginAction(state);
    if (!ticket) return;
    setBusy(true);
    setRecovery(null);
    try {
      const res = await hintLant(state.game_id);
      if (!mayAdoptAction(ticket)) return;
      setHint(res);
      setProgress(null);
      repeatFeedback((revision) => revision + 1);
      setState((previous) => previous?.game_id === ticket.gameId
        ? { ...previous, earned_hint: res, steps: res.steps, hints_left: res.hints_left, hint_level: res.hint_level } : previous);
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

  const resumeEntry = () => {
    if (entry.readyAfterTerminal(state)) setState(null);
    retryResume();
  };
  const startEntry = useRoundStart(entry, (!state || entry.readyAfterTerminal(state)) && !loading && !creating && !startFailed && !resumePending && !resumeRecovery && !unavailable, resumeEntry, (daily) => void start(daily));
  const mode = entry.mode(state);
  useLayoutEffect(() => {
    if (state && finished && isPresent) complete(state);
  }, [state, finished, isPresent, complete]);

  return (
    <div className="screen-pad fill lant-screen">
      <div className="container game-container">
        <GameFrame game={DEF} mode={mode} onExit={exitSafely} help={LANT_HELP} busy={creating || loading}
          verifying={entry.recoveredTerminal(state) && !entry.readyAfterTerminal(state)}
          startFailed={startFailed} unavailable={unavailable} onStart={() => startEntry(state?.game_id)} resumeRecovery={resumeRecovery} onResume={() => { entry.presentRecovery(); retryResume(); }}
          status={state && !entry.recoveredTerminal(state) && <span>{state.moves} {roNoun(state.moves, "salt", "salturi")}</span>}
          options={<FreeRoundOptions game={GAME_KEY} value={entry.options} onChange={entry.updateOptions} />}
          onTool={abandonChain}
          tools={state && !finished ? (
            <Button type="submit" variant="secondary" disabled={busy || creating || actionSync !== null}
              value="give-up">Renunț la rundă</Button>
          ) : undefined}>
        {state && !entry.recoveredTerminal(state) && <>
        <section className="card lant-route" aria-label="Poziția și ținta">
          <div className="lant-current" aria-live={finished ? "off" : "polite"} aria-atomic="true">
            <span className="faint">EȘTI ACUM LA</span>
            <div className="lant-route-word">
              {state.current.label}
            </div>
          </div>
          <span className="lant-route-arrow muted" aria-hidden>→</span>
          <div className="lant-target">
            <span className="faint">ȚINTĂ</span>
            <strong className="lant-route-word">
              {state.target.label}
            </strong>
          </div>
          {state.target.description && (
            <p className="muted lant-target-description">{state.target.description}</p>
          )}
        </section>

        <Breadcrumb path={state.path} />
        {!finished && !actionSync && <CoachLine revision={feedbackRevision}>
          {hint?.message ?? progress?.message ?? "Alege următorul cuvânt."}
        </CoachLine>}

        {!finished && state.choices?.length > 0 ? (
          <section ref={choicesRef} className="lant-choice-panel col" aria-labelledby="lant-choice-title">
            <Csp.div className="spread row" css={{ gap: "10px", alignItems: "baseline" }}>
              <strong id="lant-choice-title">Atinge următorul cuvânt</strong>
            </Csp.div>
            <div className="lant-choice-grid">
              {state.choices.map((choice) => (
                <button
                  key={`${choice.label}-${choice.relation}`}
                  type="button"
                  className="lant-choice"
                  disabled={actionsLocked}
                  onClick={() => void submit(choice)}
                >
                  <strong>{choice.label}</strong>
                  <span>{choice.relation}</span>
                </button>
              ))}
            </div>
          </section>
        ) : null}

        <span
          className="visually-hidden"
          role="status"
          aria-live="polite"
          aria-atomic="true"
        >
          {recovery?.message ?? ""}
        </span>

        {!finished && (
          <Csp.div
            key={shake}
            className={shake ? "col lant-shake" : "col"}
            css={{ gap: "10px" }}
          >
        {actionSync ? (
          <Csp.div className="card col lant-sync-recovery" role="alert" css={{ gap: "8px", padding: "12px" }}>
            <strong>{actionSync.kind === "changed" ? "Jocul salvat s-a schimbat." : "Verificarea jocului nu a reușit."}</strong>
            <span>{actionSync.kind === "changed"
              ? "Încarcă jocul curent pentru a continua."
              : "Acțiunea poate fi deja salvată. Verifică jocul înainte de următorul salt sau indiciu."}</span>
            <Button type="button" onClick={() => void retryActionSync()} disabled={!isPresent || busy}>
              {busy ? "Se verifică…" : actionSync.kind === "changed" ? "Încarcă jocul curent" : "Verifică jocul"}
            </Button>
          </Csp.div>
        ) : null}

            <Csp.div className="row word-hop-input" css={{ gap: "8px" }}>
              <Csp.input
                ref={inputRef}
                className="field fill"
                placeholder="Sau scrie alt concept…"
                value={text}
                disabled={actionsLocked}
                onInput={(e) => setText(e.currentTarget.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") void submit();
                  else if (e.key === "Escape") setText("");
                }}
                autoComplete="off"
                autoCapitalize="off"
                autoCorrect="off"
                spellcheck={false}
                enterKeyHint="send"
                aria-label="Următorul concept"
                css={{ flex: 1 }}
              />
              <Button
                type="button"
                disabled={actionsLocked || !text.trim()}
                onClick={() => void submit()}
              >
                {busy ? "…" : "Salt"}
              </Button>
            </Csp.div>

            <Csp.div className="row wrap lant-tools" css={{ gap: "8px" }}>
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
              <HintBar remaining={state.hints_left ?? 0} disabled={actionsLocked} onHint={() => void handleHint()} />
            </Csp.div>

            <Presence variant={FEEDBACK_VARIANT}>
              {recovery && (
                <Csp.div
                  key={`${recovery.tone}-${recovery.message}`}
                  className="card"
                  css={{
                    padding: "12px",
                    borderColor: "var(--surface-border-strong)",
                  }}
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
                      </Csp.div>
                    ) : null}
                  </Csp.div>
                </Csp.div>
              )}
            </Presence>

            <Presence variant={HINT_VARIANT}>
              {hint && (hint.stage || hint.hint) && (
                <HintPanel key="hint"
                  className="card lant-hint-panel"
                  css={{ padding: "12px", borderColor: "var(--warn)" }}
                >
                  <Csp.div className="col" css={{ gap: "8px" }}>
                    <Csp.strong css={{ color: "var(--warn)", fontSize: "0.8rem" }}>
                      {hint.stage === "direction"
                        ? "O DIRECȚIE"
                        : hint.stage === "alternatives"
                          ? "VARIANTE UTILE"
                          : hint.stage === "backtrack"
                            ? "UN PAS ÎNAPOI"
                            : "UN SALT"}
                    </Csp.strong>
                    {hint.alternatives_choices?.length ? (
                      <Csp.div className="row wrap" css={{ gap: "8px" }}>
                        {hint.alternatives_choices.map((choice) => (
                          <Button
                            key={`${choice.label}-${choice.relation}`}
                            type="button"
                            variant="secondary"
                            title={choice.relation}
                            disabled={actionsLocked}
                            onClick={() => void submit(choice)}
                          >
                            {choice.label}
                          </Button>
                        ))}
                      </Csp.div>
                    ) : null}
                    {hint.hint ? (
                      <button
                        type="button"
                        className="hint-fill-button"
                        disabled={actionsLocked}
                        title="Fă acest salt"
                        onClick={() => {
                          if (hint.hint) void submit({ label: hint.hint.label, relation: hint.relation ?? "" });
                        }}
                      >
                        Încearcă <strong>{hint.hint.label}</strong>
                        {hint.relation ? ` · ${hint.relation}` : ""}
                      </button>
                    ) : null}
                  </Csp.div>
                </HintPanel>
              )}
            </Presence>
          </Csp.div>
        )}

        {finished && (
          <ResultCard title={won ? "Ai reușit!" : "Ai renunțat la rundă"} steps={state.steps}
            perfect={won && state.perfect && mode !== "Reluare"} actionsBusy={creating}
            onCopy={sharePayload ? () => void handleCopy() : undefined} onReplay={() => startEntry(state.game_id)} onExit={exitSafely}>
            <p>{won ? "Ai ajuns la" : "Ținta era"} <strong>{state.target.label}</strong>.
              {" "}Drumul cel mai scurt: {state.optimal} {roNoun(state.optimal, "salt", "salturi")}.</p>
            {recovery?.message && <p>{recovery.message}</p>}
          </ResultCard>
        )}
        </>}
        </GameFrame>
      </div>
    </div>
  );
}
