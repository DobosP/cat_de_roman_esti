import { Csp } from "../components/CspStyle";
// Perechi — eight visible words, four semantic matches. Choosing the second tile
// submits immediately: no drag gesture, no extra confirmation, no client-side answer map.
// The leaving screen is retained by the shell's Presence; `useIsPresent()` locks
// every action and drops the pending focus claims while it exits. Feedback rows
// enter/exit through the kit Presence (mode "wait").

import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "preact/hooks";
import { Button, type ToastKind } from "@roedu/ui";
import { useIsPresent } from "@roedu/ui/motion";
import { ApiError } from "../api/client";
import { createGameActionOwner, recoverOwnedGameAction, type GameActionTicket } from "../gameActionRecovery.mjs";
import {
  perechiApi,
  type CreatePerechiOpts,
  type PerechiState,
} from "../api/perechi";
import { PERECHI_HELP } from "../gameHelp/perechi.mjs";
import { GameFrame, Attempts, CoachLine } from "../components/GameFrame";
import { useCoachMessage } from "../hooks/useCoachMessage";
import { FreeRoundOptions } from "../components/FreeRoundOptions";
import { HintBar } from "../components/HintBar";
import { useEventValue } from "../hooks/useEventValue";
import { useGameEntry, useRoundStart } from "../hooks/useGameEntry";
import { ResultCard } from "../components/ResultCard";
import { nextActiveTileId } from "../perechiFocus.mjs";
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

const GAME_KEY = "perechi";
const DEF = gameByKey(GAME_KEY);

const isTerminalResume = (state: PerechiState) => state.won || state.lost;

interface Props {
  onExit: () => void;
  onToast: (message: string, kind?: ToastKind) => void;
}

interface StartOpts {
  daily?: string;
  previousGameId?: string;
  category?: string;
}

type PendingFocus = (
  | { kind: "tile"; id: string }
  | { kind: "hint"; id: string }
) & {
  gameId: string;
  savedId: string | null;
  origin: HTMLButtonElement;
};

function focusStillOwned(origin: HTMLButtonElement): boolean {
  // Disabling/removing the owned button can leave focus on body. A deliberate
  // move to another control supersedes the asynchronous restoration claim.
  return document.activeElement === document.body || document.activeElement === origin;
}

export default function Perechi({ onExit, onToast }: Props) {
  const active = useActiveGame(GAME_KEY);
  const isPresent = useIsPresent();
  const entry = useGameEntry(GAME_KEY, active);
  const { admit, remember, complete, settleCompletion } = entry;
  const liveRef = useRef(true), lifetimeRef = useRef(0);
  const recordOnce = useRecordScore(GAME_KEY);
  const startInFlight = useEventValue<boolean>(false);
  const actionOwner = useMemo(() => createGameActionOwner(active), [active]);
  const [actionSync, setActionSync] = useState<{
    previous: PerechiState;
    action: "match" | "hint";
    kind: "failed" | "changed";
    savedId: string | null;
  } | null>(null);
  const tileRefs = useRef(new Map<string, HTMLButtonElement>());
  const hintButtonRef = useRef<HTMLButtonElement | null>(null);
  const pendingFocus = useEventValue<PendingFocus | null>(null);
  const focusedTileBeforeMutation = useEventValue<{ id: string; origin: HTMLButtonElement } | null>(null);
  useLayoutEffect(() => {
    liveRef.current = isPresent;
    if (!isPresent) {
      actionOwner.invalidate();
      pendingFocus.write(null);
      focusedTileBeforeMutation.write(null);
    }
    return () => { liveRef.current = false; lifetimeRef.current += 1; actionOwner.invalidate(); };
  }, [actionOwner, isPresent]);
  const [state, setState] = useState<PerechiState | null>(null);
  const [startFailed, setStartFailed] = useState(false);
  const [unavailable, setUnavailable] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const [checking, setChecking] = useState<[string, string] | null>(null);
  const [loading, setLoading] = useState(() => active.peek() !== null);
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback, feedbackRevision] = useCoachMessage();

  const finished = Boolean(state?.won || state?.lost);
  const actionsLocked = !isPresent || loading || busy || actionSync !== null;
  const exitSafely = useCallback(() => {
    if (!liveRef.current || startInFlight.read()) return;
    actionOwner.invalidate();
    pendingFocus.write(null);
    focusedTileBeforeMutation.write(null);
    liveRef.current = false;
    onExit();
  }, [actionOwner, onExit]);
  const queueFocusAfterUpdate = useCallback(
    (fresh: PerechiState, candidateIds: readonly string[]) => {
      const focused = focusedTileBeforeMutation.read();
      if (!focused || !candidateIds.includes(focused.id)) return;
      if (!focusStillOwned(focused.origin)) {
        pendingFocus.write(null);
        focusedTileBeforeMutation.write(null);
        return;
      }
      const focusedId = focused.id;
      const ownership = { gameId: fresh.game_id, savedId: active.peek(), origin: focused.origin };
      if (fresh.won || fresh.lost) return;
      if (!fresh.tiles.find((tile) => tile.id === focusedId)?.solved) return;
      const nextId = nextActiveTileId(fresh.tiles, focusedId);
      pendingFocus.write(nextId
        ? { kind: "tile", id: nextId, ...ownership }
        : null);
    },
    [active],
  );

  // Preact commits each awaited update on its own (React batched the recovered
  // state with the later unlock), so a restoration can meet still-disabled tiles:
  // keep the claim until the target is focusable, and apply it in the same commit
  // that unlocks it (Intrusul's pattern).
  useLayoutEffect(() => {
    const pending = pendingFocus.read();
    if (!pending) return;
    if (pending.kind === "hint" && busy) return;
    if (state?.game_id !== pending.gameId || active.peek() !== pending.savedId) {
      pendingFocus.write(null);
      return;
    }
    if (pending.kind === "hint") {
      pendingFocus.write(null);
      if (actionsLocked || finished) return;
    }
    if (!focusStillOwned(pending.origin)) {
      pendingFocus.write(null);
      focusedTileBeforeMutation.write(null);
      return;
    }
    const target = tileRefs.current.get(pending.id);
    if (!target || ("disabled" in target && target.disabled)) return;
    target.focus();
    pendingFocus.write(null);
  }, [active, actionsLocked, busy, finished, state?.game_id, state?.solved_count, state?.hints_used]);

  const applyResumedGame = useCallback((fresh: PerechiState, { terminal }: { terminal: boolean }) => {
    if (!liveRef.current || !admit(fresh, terminal)) return;
    actionOwner.invalidate();
    setActionSync(null);
    setBusy(false);
    setStartFailed(false);
    setState(fresh);
    setSelected(null);
    setChecking(null);
    pendingFocus.write(null);
    focusedTileBeforeMutation.write(null);
    setFeedback(fresh.won || fresh.lost ? null : fresh.clue?.message ?? (fresh.hint ? "Atinge cele două cuvinte marcate." : "Joc reluat. Atinge primul cuvânt."));
  }, [actionOwner, admit, setFeedback]);
  const { recovery: resumeRecovery, retryResume, cancelResume, dismissRecovery } = useSavedGameResume({
    active,
    load: perechiApi.get,
    isTerminal: isTerminalResume,
    setPending: setLoading,
    onResume: applyResumedGame,
    onReentry: () => {
      const savedId = active.peek();
      startInFlight.write(false);
      setBusy(false); setStartFailed(false); setLoading(savedId !== null);
      pendingFocus.write(null); focusedTileBeforeMutation.write(null);
      setSelected(null); setChecking(null);
      setFeedback(null);
      if (!savedId && state) {
        if (!finished) setActionSync({ previous: state, action: "match", kind: "failed", savedId: null });
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
      pendingFocus.write(null);
      focusedTileBeforeMutation.write(null);
      cancelResume();
      setStartFailed(false);
      setUnavailable(false);
      setLoading(true);
      const opts: CreatePerechiOpts = daily
        ? { daily }
        : {
            category,
            starter: needsDerivedStarter(GAME_KEY),
            previousGameId:
              previousGameId ?? lastDerivedReplayId(GAME_KEY) ?? undefined,
          };
      try {
        const fresh = await perechiApi.create(opts);
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
        setSelected(null);
        setChecking(null);
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
    [active, actionOwner, cancelResume, dismissRecovery, isPresent, remember, retryResume, setFeedback],
  );

  const puzzleKey = useMemo(() => {
    if (!state || !finished || !state.solution) return null;
    const pairs = state.solution
      .map((pair) => pair.tiles.map((tile) => tile.id).sort().join("+"))
      .sort();
    return stableKey([GAME_KEY, state.daily ? `daily-${state.daily}` : "liber", ...pairs]);
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

  const beginAction = useCallback((previous: PerechiState, action: "match" | "hint") => {
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

  const mayAdoptAction = useCallback((ticket: GameActionTicket, previous: PerechiState, action: "match" | "hint") => {
    if (!liveRef.current || !actionOwner.isCurrent(ticket)) return false;
    if (!actionOwner.owns(ticket)) {
      setActionSync({ previous, action, savedId: ticket.savedId, kind: "changed" });
      return false;
    }
    return true;
  }, [actionOwner]);

  const reconcile = useCallback(
    async (ticket: GameActionTicket, previous: PerechiState, action: "match" | "hint") => {
      const recovered = await recoverOwnedGameAction(
        actionOwner, ticket, perechiApi.get,
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
      if (
        action === "match" &&
        (fresh.solved_count > previous.solved_count || fresh.won || fresh.lost)
      ) {
        queueFocusAfterUpdate(fresh, [...tileRefs.current.keys()]);
      }
      setActionSync(null);
      setState(fresh);
      setSelected(null);
      setChecking(null);
      if (fresh.won || fresh.lost) {
        setFeedback(null);
      } else if (action === "hint" && fresh.hints_used > previous.hints_used && (fresh.hint || fresh.clue)) {
        setFeedback(fresh.clue?.message ?? "Atinge cele două cuvinte marcate.");
      } else if (action === "match" && fresh.solved_count > previous.solved_count) {
        setFeedback("Perechea a fost înregistrată. Continuă de aici.");
      } else if (action === "match" && fresh.mistakes > previous.mistakes) {
        setFeedback("Încercarea a fost înregistrată. Continuă de aici.");
      } else {
        setFeedback("Joc sincronizat. Poți continua.");
      }
    },
    [actionOwner, active, mayAdoptAction, onToast, queueFocusAfterUpdate],
  );

  const retryActionSync = useCallback(async (retryOrigin: HTMLButtonElement) => {
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
    const focused = focusedTileBeforeMutation.read();
    if (action === "match" && focused) {
      // A deliberate retry continues the same tile claim from this control.
      // Moving elsewhere before or during the read still supersedes the claim.
      if (focusStillOwned(retryOrigin)) {
        focusedTileBeforeMutation.write({ ...focused, origin: retryOrigin });
      } else {
        pendingFocus.write(null);
        focusedTileBeforeMutation.write(null);
      }
    }
    setBusy(true);
    try {
      await reconcile(ticket, previous, action);
    } finally {
      if (actionOwner.finish(ticket)) setBusy(false);
    }
  }, [state, busy, actionSync, active, actionOwner, beginAction, isPresent, reconcile, retryResume]);

  const submitPair = useCallback(
    async (ids: [string, string]) => {
      if (!state || finished || actionsLocked) return;
      const ticket = beginAction(state, "match");
      if (!ticket) return;
      const focusedId = ids.find((id) => tileRefs.current.get(id) === document.activeElement);
      const focusOrigin = focusedId ? tileRefs.current.get(focusedId) : undefined;
      focusedTileBeforeMutation.write(focusedId && focusOrigin
        ? { id: focusedId, origin: focusOrigin }
        : null);
      setChecking(ids);
      setBusy(true);
      try {
        const result = await perechiApi.match(state.game_id, ids);
        if (!mayAdoptAction(ticket, state, "match")) return;
        if (result.game_id !== ticket.gameId) {
          await reconcile(ticket, state, "match");
          return;
        }
        queueFocusAfterUpdate(result, ids);
        setState(result);
        setSelected(null);
        if (result.correct) {
          setFeedback(`Pereche găsită: ${result.pair?.label ?? "se potrivesc"}.`);
          sound.playHop();
        } else if (result.repeated) {
          setFeedback("Pereche deja încercată · fără cost.");
          sound.playUndo();
        } else {
          setFeedback(
            result.lost
              ? "Ai folosit toate greșelile permise. Îți arăt perechile."
              : "Nu încă. Încearcă altă combinație.",
          );
          sound.playError();
        }
      } catch {
        await reconcile(ticket, state, "match");
      } finally {
        if (actionOwner.finish(ticket)) {
          setChecking(null);
          setBusy(false);
        }
      }
    },
    [actionsLocked, actionOwner, beginAction, finished, mayAdoptAction, queueFocusAfterUpdate, reconcile, state],
  );

  const choose = useCallback(
    (id: string) => {
      if (!state || finished || actionsLocked || actionOwner.hasPending()) return;
      sound.playSelect();
      if (selected === id) {
        setSelected(null);
        setFeedback(null);
        return;
      }
      if (selected === null) {
        setSelected(id);
        setFeedback(null);
        return;
      }
      const pair: [string, string] = [selected, id];
      void submitPair(pair);
    },
    [actionsLocked, actionOwner, finished, selected, state, submitPair],
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
    focusedTileBeforeMutation.write(null);
    const focusOrigin = hintButtonRef.current;
    const restoreFocus = focusOrigin !== null && document.activeElement === focusOrigin;
    setBusy(true);
    try {
      const fresh = await perechiApi.hint(state.game_id);
      if (!mayAdoptAction(ticket, state, "hint")) return;
      if (fresh.game_id !== ticket.gameId) {
        await reconcile(ticket, state, "hint");
        return;
      }
      const nextTile = fresh.hint?.tiles.find((hinted) =>
        fresh.tiles.some((tile) => tile.id === hinted.id && !tile.solved),
      );
      if (restoreFocus && nextTile && fresh.hints_used > state.hints_used && !fresh.won && !fresh.lost) {
        pendingFocus.write({
          kind: "hint",
          gameId: fresh.game_id,
          savedId: ticket.savedId,
          origin: focusOrigin,
          id: nextTile.id,
        });
      }
      setState(fresh);
      setSelected(null);
      setFeedback(fresh.clue?.message ?? "Atinge cele două cuvinte marcate.");
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

  const startEntry = useRoundStart(entry, (!state || entry.readyAfterTerminal(state)) && !loading && !startFailed && !resumeRecovery && !unavailable, retryResume,
    (daily, previousGameId) => void start({ daily, previousGameId, category: entry.options.category ?? undefined }));
  const mode = entry.mode(state);
  useLayoutEffect(() => {
    if (state && finished && isPresent) complete(state);
  }, [state, finished, isPresent, complete]);

  const hintIds = new Set(state?.hint?.tiles.map((tile) => tile.id));
  const activeTiles = state?.tiles.filter((tile) => !tile.solved) ?? [];
  const selectedTile = activeTiles.find((tile) => tile.id === selected);
  return (
    <div className="screen-pad fill perechi-game">
      <div className="container game-container">
        <GameFrame game={DEF} mode={mode} onExit={exitSafely} help={PERECHI_HELP}
          busy={loading} verifying={entry.recoveredTerminal(state) && !entry.readyAfterTerminal(state)}
          startFailed={startFailed} unavailable={unavailable} onStart={() => startEntry(state?.game_id)}
          resumeRecovery={resumeRecovery} onResume={() => { entry.presentRecovery(); retryResume(); }}
          options={<FreeRoundOptions game={GAME_KEY} value={entry.options} onChange={entry.updateOptions} />}
          status={state && !entry.recoveredTerminal(state) && <Attempts remaining={state.remaining_mistakes} />}>
        {state && !entry.recoveredTerminal(state) && <>
        {!finished && actionSync && (
          <Csp.div className="card col perechi-sync-recovery" role="alert" css={{ gap: "8px", padding: "12px" }}>
            <strong>{actionSync.kind === "changed" ? "Jocul salvat s-a schimbat." : "Verificarea jocului nu a reușit."}</strong>
            <span>{actionSync.kind === "changed"
              ? "Încarcă jocul curent pentru a continua."
              : "Acțiunea poate fi deja salvată. Verifică jocul înainte de o nouă alegere sau de un indiciu."}</span>
            <Button type="button" onClick={(event) => void retryActionSync(event.currentTarget)} disabled={busy || !isPresent}>
              {busy ? "Se verifică…" : actionSync.kind === "changed" ? "Încarcă jocul curent" : "Verifică jocul"}
            </Button>
          </Csp.div>
        )}

        {!finished && !actionSync && (
          <CoachLine id="perechi-instruction" revision={feedbackRevision}>
            {selectedTile ? `Atinge perechea pentru „${selectedTile.label}”. Atinge-l din nou ca să renunți la el.`
              : feedback ?? state.clue?.message ?? (state.hint ? "Atinge cele două cuvinte marcate." : "Atinge două cuvinte care se potrivesc.")}
          </CoachLine>
        )}

        {!finished && (
          <div
            className="perechi-grid" role="group"
            aria-label={`Cuvinte de potrivit, ${activeTiles.length} rămase`}
            aria-describedby={!actionSync ? "perechi-instruction" : undefined}
          >
            {activeTiles.map((tile) => {
              const isSelected = selected === tile.id || Boolean(checking?.includes(tile.id));
              const isHinted = hintIds.has(tile.id);
              return (
                <button
                  key={tile.id}
                  ref={(node) => {
                    if (node) tileRefs.current.set(tile.id, node);
                    else tileRefs.current.delete(tile.id);
                  }}
                  type="button"
                  className={`card perechi-tile${
                    isSelected ? " perechi-tile--selected" : ""
                  }${
                    isHinted ? " perechi-tile--hinted" : ""
                  }`}
                  onClick={() => choose(tile.id)}
                  disabled={actionsLocked}
                  aria-pressed={isSelected}
                  aria-label={`${tile.label}${isHinted ? ", marcat de indiciu" : ""}`}
                >
                  <strong>{tile.label}</strong>
                  {isHinted && <span>indiciu</span>}
                </button>
              );
            })}
          </div>
        )}

        {!finished && <HintBar remaining={state.hints_left ?? 0} disabled={actionsLocked}
          buttonRef={hintButtonRef} onHint={() => void requestHint()} />}

        {state.solved_pairs.length > 0 && !finished && (
          <div className="perechi-solved" role="group" aria-label="Perechi găsite">
            {state.solved_pairs.map((pair) => (
              <div className="perechi-solved-row" key={pair.tiles.map((tile) => tile.id).join("+")}>
                <strong>{pair.label}</strong>
                <span>{pair.tiles.map((tile) => tile.label).join(" + ")}</span>
              </div>
            ))}
          </div>
        )}

        {finished && state.solution && (
          <ResultCard title={state.won ? "Toate se potrivesc!" : "Acestea erau perechile"}
            steps={state.steps} perfect={state.perfect && mode !== "Reluare"}
            actionsBusy={loading} onCopy={sharePayload ? copyShare : undefined}
            onReplay={() => startEntry(state.game_id)} onExit={exitSafely}>
              <div className="perechi-solution">
                {!state.won && (
                  <Csp.p css={{ margin: "0 0 2px" }}>
                    Ai găsit {state.solved_count} din 4 perechi.
                  </Csp.p>
                )}
                {state.solution.map((pair) => (
                  <span key={pair.tiles.map((tile) => tile.id).join("+")}>
                    <strong>{pair.label}</strong>:{" "}
                    {pair.tiles.map((tile) => tile.label).join(" + ")}
                  </span>
                ))}
              </div>
          </ResultCard>
        )}
        </>}
        </GameFrame>
      </div>
    </div>
  );
}
