import { Csp } from "../components/CspStyle";
// Intrusul — tap the one concept that does not belong with the other three.
// Every decision and point comes from the server; the browser only adds compact,
// touch-first feedback around the earned public state. The leaving screen is
// retained by the shell's Presence; `useIsPresent()` locks every action while
// it exits. Feedback rows enter/exit through the kit Presence (mode "wait").

import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "preact/hooks";
import { Button, type ToastKind } from "@roedu/ui";
import { useIsPresent } from "@roedu/ui/motion";
import { ApiError } from "../api/client";
import { createGameActionOwner, recoverOwnedGameAction, type GameActionTicket } from "../gameActionRecovery.mjs";
import {
  intrusulApi,
  type CreateIntrusulOpts,
  type IntrusulState,
} from "../api/intrusul";
import { INTRUSUL_HELP } from "../gameHelp/intrusul.mjs";
import { GameFrame, Attempts, CoachLine } from "../components/GameFrame";
import { useCoachMessage } from "../hooks/useCoachMessage";
import { FreeRoundOptions } from "../components/FreeRoundOptions";
import { HintBar } from "../components/HintBar";
import { useEventValue } from "../hooks/useEventValue";
import { useGameEntry, useRoundStart } from "../hooks/useGameEntry";
import { BoardPlacePodium } from "../components/BoardPlacePodium";
import { ResultCard } from "../components/ResultCard";
import { gameByKey } from "../games";
import { useActiveGame } from "../hooks/useActiveGame";
import { useRecordScore } from "../hooks/useRecordScore";
import { useSavedGameResume } from "../hooks/useSavedGameResume";
import {
  lastDerivedReplayId,
  rememberDerivedReplayId,
} from "../derivedReplay";
import { needsDerivedStarter } from "../scores/daily";
import { buildSharePayload, copyResult, stableKey } from "../share";
import { sound } from "../sound";

const GAME_KEY = "intrusul";
const DEF = gameByKey(GAME_KEY);

const isTerminalResume = (state: IntrusulState) => state.won || state.lost;

interface Props {
  onExit: () => void;
  onToast: (message: string, kind?: ToastKind) => void;
}

interface StartOpts {
  daily?: string;
  previousGameId?: string;
  category?: string;
}

export default function Intrusul({ onExit, onToast }: Props) {
  const active = useActiveGame(GAME_KEY);
  const isPresent = useIsPresent();
  const entry = useGameEntry(GAME_KEY, active);
  const { admit, remember, complete, settleCompletion, replayFor } = entry;
  const liveRef = useRef(true), lifetimeRef = useRef(0);
  const recordOnce = useRecordScore(GAME_KEY);
  const startInFlight = useEventValue<boolean>(false);
  const actionOwner = useMemo(() => createGameActionOwner(active), [active]);
  const tileRefs = useRef(new Map<string, HTMLButtonElement>());
  const hintButtonRef = useRef<HTMLButtonElement | null>(null);
  const pendingHintFocus = useEventValue<{
    gameId: string;
    savedId: string | null;
    origin: HTMLButtonElement;
    tileId: string;
  } | null>(null);
  const [actionSync, setActionSync] = useState<{
    previous: IntrusulState;
    action: "guess" | "hint";
    kind: "failed" | "changed";
    savedId: string | null;
  } | null>(null);
  useLayoutEffect(() => {
    liveRef.current = isPresent;
    if (!isPresent) {
      actionOwner.invalidate();
      pendingHintFocus.write(null);
    }
    return () => { liveRef.current = false; lifetimeRef.current += 1; actionOwner.invalidate(); };
  }, [actionOwner, isPresent]);
  const [state, setState] = useState<IntrusulState | null>(null);
  const [startFailed, setStartFailed] = useState(false);
  const [unavailable, setUnavailable] = useState(false);
  const [loading, setLoading] = useState(() => active.peek() !== null);
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback, feedbackRevision] = useCoachMessage();

  const finished = Boolean(state?.won || state?.lost);
  const actionsLocked = !isPresent || loading || busy || actionSync !== null;
  useLayoutEffect(() => {
    const pending = pendingHintFocus.read();
    if (!pending || busy) return;
    pendingHintFocus.write(null);
    if (!state || finished || actionsLocked || state.game_id !== pending.gameId ||
      active.peek() !== pending.savedId) return;
    // Disabling/removing the initiating hint button can move focus to body. Keep
    // deliberate navigation to options or another control during the request.
    if (document.activeElement !== document.body && document.activeElement !== pending.origin) return;
    const target = tileRefs.current.get(pending.tileId);
    if (target && !target.disabled) target.focus();
  }, [active, actionsLocked, busy, finished, state]);
  const exitSafely = useCallback(() => {
    if (!liveRef.current || startInFlight.read()) return;
    actionOwner.invalidate();
    pendingHintFocus.write(null);
    liveRef.current = false;
    onExit();
  }, [actionOwner, onExit]);

  const applyResumedGame = useCallback((fresh: IntrusulState, { terminal }: { terminal: boolean }) => {
    if (!liveRef.current || !admit(fresh, terminal)) return;
    actionOwner.invalidate();
    pendingHintFocus.write(null);
    setActionSync(null);
    setBusy(false);
    setStartFailed(false);
    setState(fresh);
    setFeedback(
      fresh.won || fresh.lost
        ? null
        : fresh.clue?.message ?? "Joc reluat. Atinge cuvântul care nu se potrivește.",
    );
  }, [actionOwner, admit, setFeedback]);
  const { recovery: resumeRecovery, pending: resumePending, retryResume, cancelResume, dismissRecovery } = useSavedGameResume({
    active,
    load: intrusulApi.get,
    isTerminal: isTerminalResume,
    setPending: setLoading,
    onResume: applyResumedGame,
    onReentry: () => {
      const savedId = active.peek();
      startInFlight.write(false);
      setBusy(false); setStartFailed(false); setLoading(savedId !== null);
      pendingHintFocus.write(null);
      setFeedback(null);
      if (!savedId && state) {
        if (!finished) setActionSync({ previous: state, action: "guess", kind: "failed", savedId: null });
      } else { setState(null); setActionSync(null); }
    },
  });

  const start = useCallback(
    async ({ daily, previousGameId, category }: StartOpts = {}) => {
      if (!isPresent || !liveRef.current) return;
      if (startInFlight.read()) return;
      startInFlight.write(true);
      const epoch = lifetimeRef.current;
      const expected = active.peek();
      actionOwner.invalidate();
      pendingHintFocus.write(null);
      cancelResume();
      setStartFailed(false);
      setUnavailable(false);
      setLoading(true);
      const opts: CreateIntrusulOpts = daily
        ? { daily, replay: replayFor(daily) }
        : {
            category,
            starter: needsDerivedStarter(GAME_KEY),
            previousGameId:
              previousGameId ?? lastDerivedReplayId(GAME_KEY) ?? undefined,
          };
      try {
        const fresh = await intrusulApi.create(opts);
        if (!liveRef.current || epoch !== lifetimeRef.current) return;
        if (!remember(fresh, expected)) {
          setState(null);
          retryResume();
          return;
        }
        setState(fresh);
        setActionSync(null);
        setBusy(false);
        dismissRecovery();
        setFeedback(null);
      } catch {
        if (liveRef.current && epoch === lifetimeRef.current) setStartFailed(true);
      } finally {
        if (epoch === lifetimeRef.current) {
          startInFlight.write(false);
          if (liveRef.current) setLoading(false);
        }
      }
    },
    [replayFor, active, actionOwner, cancelResume, dismissRecovery, isPresent, remember, retryResume, setFeedback],
  );

  const puzzleKey = useMemo(() => {
    if (!state || !finished || !state.solution) return null;
    return stableKey([
      GAME_KEY,
      state.daily ? `daily-${state.daily}` : state.difficulty,
      state.solution.intruder.id,
      ...state.solution.group.tiles.map((tile) => tile.id).sort(),
    ]);
  }, [finished, state]);

  const sharePayload = useMemo(() => {
    if (!state || !finished || !state.share) return null;
    return buildSharePayload({
      gameTitle: DEF.title,
      serverShare: state.share,
      puzzleKey,
    });
  }, [finished, puzzleKey, state]);

  useEffect(() => {
    if (!isPresent || !liveRef.current || !state || !finished || state.score === undefined) return;
    if (!state.daily) rememberDerivedReplayId(GAME_KEY, state.game_id);
    const detail = state.won
      ? `${state.mistakes} ${state.mistakes === 1 ? "greșeală" : "greșeli"}`
      : `pierdut · ${state.mistakes} greșeli`;
    let current = true;
    void recordOnce(state.game_id, state.score, detail, {
      puzzleKey,
      daily: state.daily,
      steps: state.steps,
      difficulty: state.difficulty,
      category: state.board_category,
    }).then((outcome) => {
      settleCompletion(state);
      if (!current || !liveRef.current || !outcome) return;
      if (state.won) sound.playWin();
      else sound.playError();
    });
    return () => {
      current = false;
    };
  }, [finished, isPresent, puzzleKey, recordOnce, settleCompletion, state]);

  const beginAction = useCallback((previous: IntrusulState, action: "guess" | "hint") => {
    if (!isPresent || !liveRef.current || startInFlight.read()) return null;
    const ticket = actionOwner.begin(previous.game_id);
    if (!ticket) return null;
    if (!actionOwner.owns(ticket)) {
      actionOwner.finish(ticket);
      setActionSync({ previous, action, savedId: ticket.savedId, kind: "changed" });
      return null;
    }
    return ticket;
  }, [actionOwner, isPresent]);

  const mayAdoptAction = useCallback((ticket: GameActionTicket, previous: IntrusulState, action: "guess" | "hint") => {
    if (!liveRef.current || !actionOwner.isCurrent(ticket)) return false;
    if (!actionOwner.owns(ticket)) {
      setActionSync({ previous, action, savedId: ticket.savedId, kind: "changed" });
      return false;
    }
    return true;
  }, [actionOwner]);

  const reconcile = useCallback(
    async (ticket: GameActionTicket, previous: IntrusulState, action: "guess" | "hint") => {
      const recovered = await recoverOwnedGameAction(
        actionOwner, ticket, intrusulApi.get,
        (error) => error instanceof ApiError && error.status === 404,
      );
      if (!mayAdoptAction(ticket, previous, action)) return;
      if (recovered.kind === "missing") {
        if (ticket.savedId === ticket.gameId && !active.forgetIfCurrent(ticket.gameId)) {
          setActionSync({ previous, action, savedId: ticket.savedId, kind: "changed" });
          return;
        }
        setActionSync(null);
        setState(null);
        setUnavailable(true);
        setFeedback(null);
        onToast("Jocul nu mai este disponibil. Poți începe altul.", "info");
        return;
      }
      if (recovered.kind !== "recovered") {
        setActionSync({ previous, action, savedId: ticket.savedId, kind: "failed" });
        setFeedback(null);
        return;
      }
      const fresh = recovered.state;
      setActionSync(null);
      setState(fresh);
      if (fresh.won || fresh.lost) {
        setFeedback(null);
      } else if (action === "hint" && fresh.hints_used > previous.hints_used && fresh.clue) {
        setFeedback(fresh.clue.message);
      } else if (action === "guess" && fresh.mistakes > previous.mistakes) {
        setFeedback("Încercarea a fost înregistrată. Continuă de aici.");
      } else {
        setFeedback("Joc sincronizat. Poți continua.");
      }
    },
    [actionOwner, active, mayAdoptAction, onToast],
  );

  const retryActionSync = useCallback(async () => {
    if (!isPresent || !liveRef.current || !state || busy || !actionSync) return;
    if (actionSync.kind === "changed") {
      actionOwner.invalidate();
      setActionSync(null);
      setState(null);
      setUnavailable(active.peek() === null);
      setLoading(true);
      retryResume();
      return;
    }
    const { previous, action } = actionSync;
    if (state.game_id !== previous.game_id) return;
    const ticket = beginAction(previous, action);
    if (!ticket) return;
    // A retry continues the original ownership claim, including a known saved ID.
    // It must not reinterpret a pointer removed since the failed read as unavailable storage.
    if (ticket.savedId !== actionSync.savedId) {
      actionOwner.finish(ticket);
      setActionSync({ ...actionSync, kind: "changed" });
      return;
    }
    setBusy(true);
    try {
      await reconcile(ticket, previous, action);
    } finally {
      if (actionOwner.finish(ticket)) setBusy(false);
    }
  }, [state, busy, actionSync, active, actionOwner, beginAction, isPresent, reconcile, retryResume]);

  const choose = useCallback(
    async (id: string) => {
      if (!state || finished || actionsLocked) return;
      const ticket = beginAction(state, "guess");
      if (!ticket) return;
      setBusy(true);
      try {
        const result = await intrusulApi.guess(state.game_id, id);
        if (!mayAdoptAction(ticket, state, "guess")) return;
        if (result.game_id !== ticket.gameId) {
          await reconcile(ticket, state, "guess");
          return;
        }
        setState(result);
        setFeedback(result.message);
        // The terminal effect owns the win sound and score recording.
        if (!result.correct && result.already_tried) sound.playUndo();
        else if (!result.correct) sound.playError();
      } catch {
        await reconcile(ticket, state, "guess");
      } finally {
        if (actionOwner.finish(ticket)) setBusy(false);
      }
    },
    [actionsLocked, actionOwner, beginAction, finished, mayAdoptAction, reconcile, state],
  );

  const requestHint = useCallback(async () => {
    if (
      !state ||
      finished ||
      actionsLocked ||
      !state.hints_left
    ) {
      return;
    }
    const ticket = beginAction(state, "hint");
    if (!ticket) return;
    const focusOrigin = hintButtonRef.current;
    const restoreFocus = focusOrigin !== null && document.activeElement === focusOrigin;
    setBusy(true);
    try {
      const fresh = await intrusulApi.hint(state.game_id);
      if (!mayAdoptAction(ticket, state, "hint")) return;
      if (fresh.game_id !== ticket.gameId) {
        await reconcile(ticket, state, "hint");
        return;
      }
      const nextTile = fresh.tiles.find((tile) => !fresh.wrong_ids.includes(tile.id));
      if (restoreFocus && nextTile && fresh.hints_used > state.hints_used && !fresh.won && !fresh.lost) {
        pendingHintFocus.write({
          gameId: fresh.game_id,
          savedId: ticket.savedId,
          origin: focusOrigin,
          tileId: nextTile.id,
        });
      }
      setState(fresh);
      setFeedback(fresh.clue?.message ?? "Indiciul este pe tablă.");
      sound.playSelect();
    } catch {
      await reconcile(ticket, state, "hint");
    } finally {
      if (actionOwner.finish(ticket)) setBusy(false);
    }
  }, [actionsLocked, actionOwner, beginAction, finished, mayAdoptAction, reconcile, state]);

  const copyShare = useCallback(async () => {
    if (!sharePayload) return;
    onToast((await copyResult(sharePayload)) ? "Copiat!" : "Nu am putut copia.", "info");
  }, [onToast, sharePayload]);

  const resumeEntry = () => {
    if (entry.readyAfterTerminal(state)) setState(null);
    retryResume();
  };
  const startEntry = useRoundStart(entry, (!state || entry.readyAfterTerminal(state)) && !loading && !startFailed && !resumePending && !resumeRecovery && !unavailable, resumeEntry,
    (daily, previousGameId) => void start({ daily, previousGameId, category: entry.options.category ?? undefined }));
  const mode = entry.mode(state);
  useLayoutEffect(() => {
    if (state && finished && isPresent) complete(state);
  }, [state, finished, isPresent, complete]);

  const wrong = new Set(state?.wrong_ids);
  return (
    <div className="screen-pad fill intrusul-game">
      <div className="container game-container">
        <GameFrame game={DEF} mode={mode} onExit={exitSafely} help={INTRUSUL_HELP}
          busy={loading} verifying={entry.recoveredTerminal(state) && !entry.readyAfterTerminal(state)}
          startFailed={startFailed} unavailable={unavailable} onStart={() => startEntry(state?.game_id)}
          resumeRecovery={resumeRecovery} onResume={() => { entry.presentRecovery(); retryResume(); }}
          options={<FreeRoundOptions game={GAME_KEY} value={entry.options} onChange={entry.updateOptions} />}
          status={state && !entry.recoveredTerminal(state) && <Attempts remaining={state.remaining_mistakes} />}>
        {state && !entry.recoveredTerminal(state) && <>
        {!finished && actionSync && (
          <Csp.div className="card col intrusul-sync-recovery" role="alert" css={{ gap: "8px", padding: "12px" }}>
            <strong>{actionSync.kind === "changed" ? "Jocul salvat s-a schimbat." : "Verificarea jocului nu a reușit."}</strong>
            <span>{actionSync.kind === "changed"
              ? "Încarcă jocul curent pentru a continua."
              : "Acțiunea poate fi deja salvată. Verifică jocul înainte de o nouă alegere sau de un indiciu."}</span>
            <Button type="button" onClick={() => void retryActionSync()} disabled={busy || !isPresent}>
              {busy ? "Se verifică…" : actionSync.kind === "changed" ? "Încarcă jocul curent" : "Verifică jocul"}
            </Button>
          </Csp.div>
        )}

        {!finished && !actionSync && (
          <CoachLine id="intrusul-instruction" revision={feedbackRevision}>
            {feedback ?? state.clue?.message ?? "Atinge cuvântul care nu se potrivește."}
          </CoachLine>
        )}

        {!finished && (
          <div className="intrusul-grid" role="group" aria-label="Cuvinte pentru Intrusul" aria-describedby={!actionSync ? "intrusul-instruction" : undefined}>
            {state.tiles.map((tile) => {
              const tried = wrong.has(tile.id);
              return (
                <button
                  key={tile.id}
                  ref={(node) => {
                    if (node) tileRefs.current.set(tile.id, node);
                    else tileRefs.current.delete(tile.id);
                  }}
                  type="button"
                  className={`card intrusul-tile${tried ? " intrusul-tile--tried" : ""}`}
                  onClick={() => void choose(tile.id)}
                  disabled={actionsLocked}
                  aria-label={`${tile.label}${tried ? ", face parte din grup; repetarea este fără cost" : ""}`}
                >
                  <strong>{tile.label}</strong>
                  {tried && <span>ține de grup</span>}
                </button>
              );
            })}
          </div>
        )}

        {!finished && <HintBar remaining={state.hints_left ?? 0} disabled={actionsLocked}
          buttonRef={hintButtonRef} onHint={() => void requestHint()} />}

        {finished && state.solution && (
          <ResultCard title={state.won ? "L-ai găsit!" : "Nu a ieșit de data asta"}
            podium={<BoardPlacePodium round={state} gameTitle={DEF.title} replay={mode === "Reluare"} />}
            steps={state.steps} perfect={state.perfect && mode !== "Reluare"}
            actionsBusy={loading} onCopy={sharePayload ? copyShare : undefined}
            onReplay={() => startEntry(state.game_id)} onExit={exitSafely}>
            <div className="intrusul-solution">
              {state.won ? (
                <>
                  <strong className="intrusul-answer">{state.solution.intruder.label}</strong>
                  <span>
                    Celelalte trei: <strong>{state.solution.group.label}</strong>
                  </span>
                </>
              ) : (
                <>
                  <strong className="intrusul-answer">
                    Intrusul era: {state.solution.intruder.label}.
                  </strong>
                  <span>
                    Grupul: <strong>{state.solution.group.label}</strong>.
                  </span>
                </>
              )}
              <span>{state.solution.group.tiles.map((tile) => tile.label).join(" · ")}</span>
            </div>
          </ResultCard>
        )}
        </>}
        </GameFrame>
      </div>
    </div>
  );
}
