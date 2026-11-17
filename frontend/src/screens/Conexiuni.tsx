import { Csp } from "../components/CspStyle";
// Conexiuni — NYT Connections over the Romanian KG. Text-only: a 4x4 grid of selectable
// tile buttons. Pick exactly 4 and "Verifică"; the server says whether they share a
// category (locks it as a coloured row) or not (one_away feedback + a lost life). Win when
// all 4 groups are found; lose at 0 lives — then the full solution is revealed.
//
// Server-authoritative: the grouping + solution live on the server; this component renders
// what it returns and surfaces a personal best + a shareable result on finish.
//
// Motion: the kit Presence owns per-tile exits (enter scale .6 -> 1, exit scale
// -> .4, spring 320/20 per roedu-ui ADR-0021), the feedback swap and the solved
// rows; the wrong-guess shake and the solved-row entrance are CSS keyframes.

import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "preact/hooks";
import { Presence, useIsPresent, type PresenceVariant } from "@roedu/ui/motion";
import { ApiError } from "../api/client";
import { createGameActionOwner, recoverOwnedGameAction, type GameActionTicket } from "../gameActionRecovery.mjs";
import {
  conexiuniApi,
  GROUP_SIZE,
  type ConexiuniState,
  type GuessResult,
  type SolvedGroup,
} from "../api/conexiuni";
import { Button, type ToastKind } from "@roedu/ui";
import { CONEXIUNI_HELP } from "../gameHelp/conexiuni.mjs";
import { GameFrame, Attempts, CoachLine } from "../components/GameFrame";
import { useCoachMessage } from "../hooks/useCoachMessage";
import { FreeRoundOptions } from "../components/FreeRoundOptions";
import { HintBar } from "../components/HintBar";
import { useEventValue } from "../hooks/useEventValue";
import { useGameEntry, useRoundStart } from "../hooks/useGameEntry";
import { BoardPlacePodium } from "../components/BoardPlacePodium";
import { ResultCard } from "../components/ResultCard";
import { useActiveGame } from "../hooks/useActiveGame";
import { useRecordScore } from "../hooks/useRecordScore";
import { useSavedGameResume } from "../hooks/useSavedGameResume";
import { sound } from "../sound";
import { selectionKey } from "../conexiuniSelectionKey";
import { gameByKey } from "../games";
import { buildSharePayload, copyResult, stableKey } from "../share";

const GAME_KEY = "conexiuni";
const DEF = gameByKey("conexiuni");

const isTerminalResume = (state: ConexiuniState) => state.won || state.lost;

interface SelfProps {
  onExit: () => void;
  onToast: (message: string, kind?: ToastKind) => void;
}

// Presence-per-tile exits: the exact original Framer keyframes (Conexiuni.tsx:714-728).
const TILE_VARIANT: PresenceVariant = {
  enter: { opacity: [0, 1], transform: ["scale(0.6)", "scale(1)"] },
  exit: { opacity: [1, 0], transform: ["scale(1)", "scale(0.4)"] },
  transition: { spring: { stiffness: 320, damping: 20 } },
};

const ONE_AWAY_GUIDANCE =
  "Aproape: 3 din 4. Schimbă o piesă.";
type BlockedGuess = { key: string; oneAway: boolean };
type DuplicateRecovery = { guess: string[]; message: string };
type ActionSync = { gameId: string; kind: "failed" | "changed"; duplicate?: DuplicateRecovery };

const unsolvedTileIds = (fresh: ConexiuniState) => {
  const solved = new Set(
    fresh.solved.flatMap((group) => group.tiles.map((tile) => tile.id)),
  );
  return new Set(
    fresh.tiles.filter((tile) => !solved.has(tile.id)).map((tile) => tile.id),
  );
};

export default function Conexiuni({ onExit, onToast }: SelfProps) {
  const active = useActiveGame(GAME_KEY);
  const isPresent = useIsPresent();
  const entry = useGameEntry(GAME_KEY, active);
  const { admit, remember, complete, settleCompletion, replayFor } = entry;
  const liveRef = useRef(true), lifetimeRef = useRef(0);
  const [state, setState] = useState<ConexiuniState | null>(null);
  const [startFailed, setStartFailed] = useState(false);
  const [unavailable, setUnavailable] = useState(false);
  const startInFlight = useEventValue<boolean>(false);
  const [loading, setLoading] = useState(() => active.peek() !== null);
  const [busy, setBusy] = useState(false);
  const [actionSync, setActionSync] = useState<ActionSync | null>(null);
  const actionOwner = useMemo(() => createGameActionOwner(active), [active]);
  useLayoutEffect(() => {
    liveRef.current = isPresent;
    if (!isPresent) actionOwner.invalidate();
    return () => { liveRef.current = false; lifetimeRef.current += 1; actionOwner.invalidate(); };
  }, [actionOwner, isPresent]);
  const actionsLocked = !isPresent || busy || loading || actionSync !== null;
  const [selected, setSelected] = useState<string[]>([]);
  // A server-confirmed one-away or duplicate set that must change before resubmission.
  // Only the oneAway flag may surface the stronger 3-of-4 guidance.
  const [blockedGuess, setBlockedGuess] = useState<BlockedGuess | null>(null);
  const [shake, setShake] = useState(0);
  // Client-only display order for the remaining tiles (the "shuffle" button reorders
  // these; the authoritative grouping never changes). Keyed by tile id.
  const [shuffleNonce, setShuffleNonce] = useState(0);
  // Transient inline feedback shown beside the board. Recovery remains until
  // the player makes the requested selection change, then clears immediately.
  const [hint, setHint, feedbackRevision] = useCoachMessage();
  const recordOnce = useRecordScore(GAME_KEY);

  // Solved-id set so solved tiles drop out of the grid.
  const solvedIds = useMemo(() => {
    const s = new Set<string>();
    state?.solved.forEach((g) => g.tiles.forEach((t) => s.add(t.id)));
    return s;
  }, [state]);

  const remainingTiles = useMemo(() => {
    const base = state ? state.tiles.filter((t) => !solvedIds.has(t.id)) : [];
    if (shuffleNonce === 0) return base;
    // Deterministic-ish shuffle driven by the nonce so re-renders are stable until the
    // player presses "Amestecă" again. Purely cosmetic — ids/grouping are untouched.
    const arr = [...base];
    let seed = shuffleNonce * 2654435761;
    for (let i = arr.length - 1; i > 0; i--) {
      seed = (seed * 1103515245 + 12345) & 0x7fffffff;
      const j = seed % (i + 1);
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
  }, [state, solvedIds, shuffleNonce]);

  const finished = (state?.won ?? false) || (state?.lost ?? false);
  const exactBlockedRetry =
    selected.length === GROUP_SIZE &&
    blockedGuess !== null &&
    selectionKey(selected) === blockedGuess.key;
  const feedback = blockedGuess?.oneAway ? ONE_AWAY_GUIDANCE : hint;
  const earnedClue = state?.clues[state.clues.length - 1]?.message;
  const applyAuthoritativeState = useCallback((fresh: ConexiuniState) => {
    const available = unsolvedTileIds(fresh);
    setState(fresh);
    setSelected((current) =>
      fresh.won || fresh.lost ? [] : current.filter((id) => available.has(id)),
    );
    setBlockedGuess(null);
    setHint(null);
  }, []);

  const applyResumedGame = useCallback(
    (s: ConexiuniState, { terminal }: { terminal: boolean }) => {
      if (!liveRef.current || !admit(s, terminal)) return;
      actionOwner.invalidate();
      setActionSync(null);
      setBusy(false);
      setStartFailed(false);
      setState(s);
      setSelected([]);
      setBlockedGuess(null);
      setHint(null);
      setShuffleNonce(0);
      setShake(0);
      if (!terminal && !s.clues.length) setHint("Joc reluat. Alege patru cuvinte care merg împreună.");
    },
    [actionOwner, admit, setHint],
  );

  const { recovery: resumeRecovery, pending: resumePending, retryResume, cancelResume, dismissRecovery } = useSavedGameResume({
    active,
    load: conexiuniApi.get,
    isTerminal: isTerminalResume,
    setPending: setLoading,
    onResume: applyResumedGame,
    onReentry: () => {
      const savedId = active.peek();
      startInFlight.write(false);
      setBusy(false); setStartFailed(false); setLoading(savedId !== null);
      setSelected([]); setBlockedGuess(null); setHint(null);
      if (!savedId && state) {
        if (!finished) setActionSync({ gameId: state.game_id, kind: "failed" });
      } else { setState(null); setActionSync(null); }
    },
  });

  const start = useCallback(
    async (daily?: string) => {
      if (!liveRef.current || startInFlight.read()) return;
      startInFlight.write(true);
      const epoch = lifetimeRef.current;
      const expected = active.peek();
      const replay = replayFor(daily);
      actionOwner.invalidate();
      cancelResume();
      setStartFailed(false);
      setUnavailable(false);
      setLoading(true);
      try {
        const s = await conexiuniApi.create(daily
          ? { daily, replay, difficulty: "usor" }
          : { difficulty: entry.options.difficulty, category: entry.options.category ?? undefined });
        if (!liveRef.current || epoch !== lifetimeRef.current) return;
        if (!remember(s, expected, replay)) {
          setState(null);
          retryResume();
          return;
        }
        setState(s);
        setActionSync(null);
        setBusy(false);
        dismissRecovery();
        setSelected([]);
        setBlockedGuess(null);
        setHint(null);
        setShuffleNonce(0);
        setShake(0);
      } catch {
        if (liveRef.current && epoch === lifetimeRef.current) setStartFailed(true);
      } finally {
        if (epoch === lifetimeRef.current) {
          startInFlight.write(false);
          if (liveRef.current) setLoading(false);
        }
      }
    },
    [replayFor, active, actionOwner, cancelResume, dismissRecovery, entry.options, remember, retryResume, setHint],
  );

  const puzzleKey = useMemo(() => {
    if (!state || !finished) return null;
    const groups = state.solution ?? (state.won ? state.solved : []);
    if (groups.length === 0) return null;
    const groupKey = groups
      .map((group) => `${group.key}=${group.tiles.map((tile) => tile.id).sort().join(",")}`)
      .sort()
      .join("|");
    return stableKey([
      GAME_KEY,
      state.daily ? `daily-${state.daily}` : state.difficulty,
      groupKey,
      state.board_category,
    ]);
  }, [state, finished]);

  const sharePayload = useMemo(() => {
    if (!state || !finished || !state.share) return null;
    return buildSharePayload({
      gameTitle: DEF.title,
      serverShare: state.share,
      puzzleKey,
    });
  }, [state, finished, puzzleKey]);

  // Record the score + best once, on transition into a finished state.
  useEffect(() => {
    if (!liveRef.current || !state || !finished || state.score === undefined) return;
    const detail = state.won
      ? `${state.mistakes} ${state.mistakes === 1 ? "greșeală" : "greșeli"}`
      : `pierdut · ${state.mistakes} greșeli`;
    void recordOnce(state.game_id, state.score, detail, {
      puzzleKey,
      difficulty: state.difficulty,
      daily: state.daily,
      steps: state.steps,
      category: state.board_category,
    }).then(() => { settleCompletion(state); });
  }, [finished, isPresent, puzzleKey, recordOnce, settleCompletion, state]);

  const toggle = useCallback(
    (id: string) => {
      if (actionsLocked || finished || actionOwner.hasPending()) return;
      // Decide outside the updater so the sound side-effect stays StrictMode-safe and
      // fires only on a real change (selecting/deselecting, not a capped 5th click).
      const wasSelected = selected.includes(id);
      const changed = wasSelected || selected.length < 4;
      if (changed) {
        sound.playSelect();
        setBlockedGuess(null);
        setHint(null);
      }
      setSelected((prev) => {
        if (prev.includes(id)) return prev.filter((x) => x !== id);
        if (prev.length >= 4) return prev;
        return [...prev, id];
      });
    },
    [actionsLocked, actionOwner, finished, selected],
  );

  const clearSelection = useCallback(() => {
    if (actionsLocked || finished || actionOwner.hasPending()) return;
    setSelected([]);
    setBlockedGuess(null);
    setHint(null);
  }, [actionsLocked, actionOwner, finished]);

  const shuffle = useCallback(() => {
    if (actionsLocked || finished || actionOwner.hasPending()) return;
    sound.playSelect();
    setShuffleNonce((n) => n + 1);
  }, [actionsLocked, actionOwner, finished]);

  const beginAction = useCallback((previous: ConexiuniState) => {
    if (!liveRef.current || startInFlight.read()) return null;
    const ticket = actionOwner.begin(previous.game_id);
    if (!ticket) return null;
    if (!actionOwner.owns(ticket)) {
      actionOwner.finish(ticket);
      setBlockedGuess(null);
      setHint(null);
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

  const reconcileAction = useCallback(async (ticket: GameActionTicket, duplicate?: DuplicateRecovery) => {
    const outcome = await recoverOwnedGameAction(
      actionOwner, ticket, conexiuniApi.get,
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
      setSelected([]);
      setBlockedGuess(null);
      setHint(null);
      onToast("Jocul nu mai este disponibil. Poți începe altul.", "info");
      return;
    }
    if (outcome.kind !== "recovered") {
      setActionSync({ gameId: ticket.gameId, kind: outcome.kind === "changed" ? "changed" : "failed", duplicate });
      return;
    }
    const fresh = outcome.state;
    setActionSync(null);
    applyAuthoritativeState(fresh);
    // GET exposes earned groups/clues and terminal results, never the lost one-away verdict.
    if (!fresh.won && !fresh.lost) {
      const freshAvailable = unsolvedTileIds(fresh);
      if (duplicate && duplicate.guess.every((id) => freshAvailable.has(id))) {
        setSelected(duplicate.guess);
        setBlockedGuess({ key: selectionKey(duplicate.guess), oneAway: false });
        setHint(`${duplicate.message} Schimbă cel puțin o piesă înainte de o nouă verificare.`);
      } else {
        setHint("Joc sincronizat. Poți continua.");
      }
    }
  }, [actionOwner, active, applyAuthoritativeState, mayAdoptAction, onToast]);

  const retryActionSync = useCallback(async () => {
    if (!liveRef.current || !state || busy || !actionSync) return;
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
      await reconcileAction(ticket, actionSync.duplicate);
    } finally {
      if (actionOwner.finish(ticket)) setBusy(false);
    }
  }, [state, busy, actionSync, actionOwner, beginAction, reconcileAction, retryResume]);

  const submit = useCallback(async () => {
    if (!state || finished || selected.length !== GROUP_SIZE || actionsLocked || exactBlockedRetry) return;
    const ticket = beginAction(state);
    if (!ticket) return;
    const guess = [...selected];
    const guessKey = selectionKey(guess);
    setBusy(true);
    try {
      const res: GuessResult = await conexiuniApi.guess(state.game_id, guess);
      if (!mayAdoptAction(ticket)) return;
      setState(res);
      if (res.correct) {
        sound.playWin();
        setSelected([]);
        setBlockedGuess(null);
        setHint(null);
        if (!res.won && res.category) {
          onToast(`Grup găsit: ${res.category.label}!`, "success");
        }
      } else {
        sound.playError();
        setShake((n) => n + 1);
        const recoverableOneAway = Boolean(res.one_away && !res.lost);
        if (res.one_away) {
          setHint(
            recoverableOneAway
              ? ONE_AWAY_GUIDANCE
              : "Aproape! 3 din 4 sunt din aceeași categorie.",
          );
        } else {
          setHint("Niciun grup complet — încearcă altă combinație.");
        }
        if (recoverableOneAway) {
          setSelected(guess);
          setBlockedGuess({ key: guessKey, oneAway: true });
        } else {
          setSelected([]);
          setBlockedGuess(null);
        }
      }
    } catch (err) {
      const duplicate = err instanceof ApiError && err.status === 409
        ? { guess, message: err.message || "Combinația a fost deja verificată." }
        : undefined;
      await reconcileAction(ticket, duplicate);
    } finally {
      if (actionOwner.finish(ticket)) setBusy(false);
    }
  }, [state, finished, selected, actionsLocked, exactBlockedRetry, beginAction,
    mayAdoptAction, onToast, reconcileAction, actionOwner]);

  const requestClue = useCallback(async () => {
    if (!state || actionsLocked || finished || !state.hints_left) return;
    const ticket = beginAction(state);
    if (!ticket) return;
    setBusy(true);
    try {
      const res = await conexiuniApi.clue(state.game_id);
      if (!mayAdoptAction(ticket)) return;
      sound.playSelect();
      applyAuthoritativeState(res);
      setHint(res.clue?.message ?? null);
    } catch {
      await reconcileAction(ticket);
    } finally {
      if (actionOwner.finish(ticket)) setBusy(false);
    }
  }, [state, actionsLocked, finished, beginAction, mayAdoptAction,
    applyAuthoritativeState, reconcileAction, actionOwner, setHint]);

  const copyShare = useCallback(async () => {
    if (!liveRef.current || !sharePayload) return;
    const ok = await copyResult(sharePayload);
    if (!liveRef.current) return;
    if (ok) onToast("Copiat!", "info");
    else onToast("Nu am putut copia.", "error");
  }, [sharePayload, onToast]);

  const handleExit = useCallback(() => {
    if (!liveRef.current || startInFlight.read()) return;
    actionOwner.invalidate();
    setSelected([]);
    setBlockedGuess(null);
    setHint(null);
    liveRef.current = false;
    onExit();
  }, [actionOwner, onExit, setHint]);

  // Keyboard: Enter submits a full selection, Escape/Backspace clears it. Inert when
  // no board is active, while a request is in flight, or once the game is finished.
  useLayoutEffect(() => {
    if (!state || finished) return;
    const onKey = (e: KeyboardEvent) => {
      if (!liveRef.current || actionsLocked || actionOwner.hasPending()) return;
      const target = e.target instanceof Element ? e.target : null;
      if (
        e.defaultPrevented || target?.closest("dialog[open]") ||
        (e.key === "Enter" &&
          target?.closest(
            'button, a, input, textarea, select, summary, [role="button"], [contenteditable="true"]',
          ))
      ) {
        return;
      }
      if (e.key === "Enter" && selected.length === GROUP_SIZE && !exactBlockedRetry) {
        e.preventDefault();
        void submit();
      } else if (e.key === "Escape" || e.key === "Backspace") {
        if (selected.length > 0) {
          e.preventDefault();
          clearSelection();
        }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [state, finished, actionsLocked, actionOwner, selected, exactBlockedRetry, submit, clearSelection]);

  const resumeEntry = () => {
    if (entry.readyAfterTerminal(state)) setState(null);
    retryResume();
  };
  const startEntry = useRoundStart(entry, (!state || entry.readyAfterTerminal(state)) && !loading && !startFailed && !resumePending && !resumeRecovery && !unavailable, resumeEntry,
    (daily) => void start(daily));
  const mode = entry.mode(state);
  useLayoutEffect(() => {
    if (state && finished && isPresent) complete(state);
  }, [state, finished, isPresent, complete]);

  return (
    <div className="screen-pad fill connections-screen">
      <div className="container game-container connections-game">
        <GameFrame game={DEF} mode={mode} onExit={handleExit} help={CONEXIUNI_HELP}
          busy={loading} verifying={entry.recoveredTerminal(state) && !entry.readyAfterTerminal(state)}
          startFailed={startFailed} unavailable={unavailable} onStart={() => startEntry(state?.game_id)}
          resumeRecovery={resumeRecovery} onResume={() => { entry.presentRecovery(); retryResume(); }}
          options={<FreeRoundOptions game={GAME_KEY} value={entry.options} onChange={entry.updateOptions} />}
          status={state && !entry.recoveredTerminal(state) && <Attempts remaining={state.lives} />}>
        {state && !entry.recoveredTerminal(state) && <>
        {!finished && !actionSync && (
          <CoachLine revision={feedbackRevision}>
            {feedback || earnedClue ? <>
              {feedback && <span>{feedback}</span>}
              {earnedClue && earnedClue !== feedback && <span>{earnedClue}</span>}
            </> : selected.length === GROUP_SIZE ? "Grup gata de verificat."
              : selected.length === 0 ? "Alege patru cuvinte care merg împreună." : `Mai alege ${GROUP_SIZE - selected.length}.`}
          </CoachLine>
        )}

        <Presence initial={false}>
          {state.solved.map((group, index) => (
            <SolvedRow key={group.key} group={group} index={index} />
          ))}
        </Presence>

        {!finished && actionSync ? (
          <Csp.div className="card col connections-sync-recovery" role="alert" css={{ gap: "8px", padding: "12px" }}>
            <strong>{actionSync.kind === "changed" ? "Jocul salvat s-a schimbat." : "Verificarea jocului nu a reușit."}</strong>
            <span>{actionSync.kind === "changed"
              ? "Încarcă jocul curent pentru a continua."
              : "Acțiunea poate fi deja salvată. Verifică jocul înainte de o nouă combinație sau un indiciu."}</span>
            <Button type="button" onClick={() => void retryActionSync()} disabled={busy}>
              {busy ? "Se verifică…" : actionSync.kind === "changed" ? "Încarcă jocul curent" : "Verifică jocul"}
            </Button>
          </Csp.div>
        ) : null}

        {/* Active board: a wrong guess remounts the grid with the shake keyframe. */}
        {!finished && (
          <div key={shake} className={shake ? "connections-grid connections-grid--shake" : "connections-grid"}>
            <Presence initial={false} variant={TILE_VARIANT}>
              {remainingTiles.map((t) => {
                const isSel = selected.includes(t.id);
                return (
                  <button key={t.id} type="button" onClick={() => toggle(t.id)}
                    disabled={actionsLocked} aria-pressed={isSel} className="card connection-tile">
                    {t.label}
                  </button>
                );
              })}
            </Presence>
          </div>
        )}

        {!finished && (
          <div className="game-frame-actions">
            <HintBar remaining={state.hints_left ?? 0} disabled={actionsLocked} onHint={() => void requestClue()} />
            <div className="row wrap">
              <Button type="button" variant="secondary" disabled={actionsLocked || remainingTiles.length <= GROUP_SIZE}
                onClick={shuffle}>Amestecă</Button>
              <Button type="button" variant="secondary" disabled={actionsLocked || selected.length === 0}
                onClick={clearSelection}>Golește</Button>
              <Button type="button" disabled={actionsLocked || selected.length !== GROUP_SIZE || exactBlockedRetry}
                onClick={submit}>{busy ? "Se verifică…" : exactBlockedRetry ? "Schimbă o piesă" : "Verifică"}</Button>
            </div>
          </div>
        )}

        {/* Lose reveal */}
        {state.lost && state.solution && (
          <Csp.div className="col" css={{ gap: "8px" }}>
            <Csp.span className="faint" css={{ letterSpacing: "0.06em", fontSize: "0.72rem" }}>
              GRUPURILE RĂMASE
            </Csp.span>
            {state.solution
              .filter((group) => !state.solved.some((solved) => solved.key === group.key))
              .map((g, index) => (
                <SolvedRow
                  key={g.key}
                  group={g}
                  index={state.solved.length + index}
                />
              ))}
          </Csp.div>
        )}

        {finished && (
          <ResultCard title={state.won ? "Ai găsit toate grupurile!" : "Nu a ieșit de data asta"}
            podium={<BoardPlacePodium round={state} gameTitle={DEF.title} replay={mode === "Reluare"} />}
            steps={state.steps} perfect={state.perfect && mode !== "Reluare"} actionsBusy={loading}
            onCopy={sharePayload ? copyShare : undefined} onReplay={() => startEntry(state.game_id)} onExit={handleExit} />
        )}
        </>}
        </GameFrame>
      </div>
    </div>
  );
}

function SolvedRow({ group, index }: { group: SolvedGroup; index: number }) {
  return (
    <div className={`card connections-solved-row connections-group-${index + 1}`}>
      <strong>{group.label}</strong>
      <span>{group.tiles.map((tile) => tile.label).join(" · ")}</span>
    </div>
  );
}
