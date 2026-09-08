// Perechi — eight visible words, four semantic matches. Choosing the second tile
// submits immediately: no drag gesture, no extra confirmation, no client-side answer map.

import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, m, useIsPresent } from "framer-motion";
import { Button, type ToastKind } from "@roedu/ui";
import {
  acquireFlight,
  releaseFlight,
} from "../asyncControl.mjs";
import { ApiError } from "../api/client";
import { createGameActionOwner, recoverOwnedGameAction, type GameActionTicket } from "../gameActionRecovery.mjs";
import {
  perechiApi,
  type CreatePerechiOpts,
  type PerechiState,
} from "../api/perechi";
import { GameIntro } from "../components/GameIntro";
import { GameShell } from "../components/GameShell";
import { Hud, StatBadge } from "../components/Hud";
import { NextMove } from "../components/PlayGuide";
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
import { bestScore, needsDerivedStarter } from "../scores";
import { buildSharePayload, copyResult, stableKey, todayLocal } from "../share";
import { sound } from "../sound";
import "../styles/perechi.css";

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
}

type PendingFocus = ({ kind: "tile"; id: string } | { kind: "result" }) & {
  gameId: string;
  savedId: string | null;
};

export default function Perechi({ onExit, onToast }: Props) {
  const active = useActiveGame(GAME_KEY);
  const isPresent = useIsPresent();
  const recordOnce = useRecordScore(GAME_KEY);
  const startInFlight = useRef(false);
  const actionOwner = useMemo(() => createGameActionOwner(active), [active]);
  const [actionSync, setActionSync] = useState<{
    previous: PerechiState;
    action: "match" | "hint";
    kind: "failed" | "changed";
    savedId: string | null;
  } | null>(null);
  useEffect(() => () => actionOwner.invalidate(), [actionOwner]);
  const tileRefs = useRef(new Map<string, HTMLButtonElement>());
  const resultFocusRef = useRef<HTMLDivElement>(null);
  const pendingFocus = useRef<PendingFocus | null>(null);
  const focusedTileBeforeMutation = useRef<string | null>(null);
  useLayoutEffect(() => {
    if (!isPresent) {
      actionOwner.invalidate();
      pendingFocus.current = null;
      focusedTileBeforeMutation.current = null;
    }
  }, [actionOwner, isPresent]);
  const [state, setState] = useState<PerechiState | null>(null);
  const [startFailed, setStartFailed] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const [checking, setChecking] = useState<[string, string] | null>(null);
  const [loading, setLoading] = useState(() => active.peek() !== null);
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [recordHit, setRecordHit] = useState(false);
  const [puzzleRecordHit, setPuzzleRecordHit] = useState(false);

  const finished = Boolean(state?.won || state?.lost);
  const actionsLocked = !isPresent || loading || busy || actionSync !== null;
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const best = useMemo(() => bestScore(GAME_KEY), [state]);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const starterVisible = useMemo(() => needsDerivedStarter(GAME_KEY), [state]);
  const exitSafely = useCallback(() => {
    if (startInFlight.current) return;
    actionOwner.invalidate();
    pendingFocus.current = null;
    focusedTileBeforeMutation.current = null;
    onExit();
  }, [actionOwner, onExit]);
  const queueFocusAfterUpdate = useCallback(
    (fresh: PerechiState, candidateIds: readonly string[]) => {
      const focusedId = focusedTileBeforeMutation.current;
      if (!focusedId || !candidateIds.includes(focusedId)) return;
      const ownership = { gameId: fresh.game_id, savedId: active.peek() };
      if (fresh.won || fresh.lost) {
        pendingFocus.current = { kind: "result", ...ownership };
        return;
      }
      if (!fresh.tiles.find((tile) => tile.id === focusedId)?.solved) return;
      const nextId = nextActiveTileId(fresh.tiles, focusedId);
      pendingFocus.current = nextId
        ? { kind: "tile", id: nextId, ...ownership }
        : { kind: "result", ...ownership };
    },
    [active],
  );

  useEffect(() => {
    const pending = pendingFocus.current;
    if (!pending) return;
    if (state?.game_id !== pending.gameId || active.peek() !== pending.savedId) {
      pendingFocus.current = null;
      return;
    }
    const target =
      pending.kind === "tile"
        ? tileRefs.current.get(pending.id)
        : resultFocusRef.current?.querySelector<HTMLButtonElement>("button:not(:disabled)");
    if (!target) return;
    target.focus();
    pendingFocus.current = null;
  }, [active, finished, state?.game_id, state?.solved_count]);

  const applyResumedGame = useCallback((fresh: PerechiState) => {
    actionOwner.invalidate();
    setActionSync(null);
    setBusy(false);
    setStartFailed(false);
    setState(fresh);
    setSelected(null);
    setChecking(null);
    pendingFocus.current = null;
    focusedTileBeforeMutation.current = null;
    setFeedback(fresh.won || fresh.lost ? null : "Joc reluat. Atinge primul cuvânt.");
  }, [actionOwner]);
  const { recovery: resumeRecovery, retryResume, cancelResume, dismissRecovery } = useSavedGameResume({
    active,
    load: perechiApi.get,
    isTerminal: isTerminalResume,
    setPending: setLoading,
    onResume: applyResumedGame,
  });

  const start = useCallback(
    async ({ daily, previousGameId }: StartOpts = {}) => {
      if (!isPresent) return;
      if (!acquireFlight(startInFlight)) return;
      actionOwner.invalidate();
      pendingFocus.current = null;
      focusedTileBeforeMutation.current = null;
      cancelResume();
      setStartFailed(false);
      setLoading(true);
      const opts: CreatePerechiOpts = daily
        ? { daily }
        : {
            starter: needsDerivedStarter(GAME_KEY),
            previousGameId:
              previousGameId ?? lastDerivedReplayId(GAME_KEY) ?? undefined,
          };
      try {
        const fresh = await perechiApi.create(opts);
        setState(fresh);
        setActionSync(null);
        setBusy(false);
        active.remember(fresh.game_id);
        dismissRecovery();
        setSelected(null);
        setChecking(null);
        setFeedback(null);
        setRecordHit(false);
        setPuzzleRecordHit(false);
      } catch {
        setStartFailed(true);
      } finally {
        releaseFlight(startInFlight);
        setLoading(false);
      }
    },
    [active, actionOwner, cancelResume, dismissRecovery, isPresent],
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
      score: state.score,
      puzzleKey,
    });
  }, [finished, puzzleKey, state]);

  useEffect(() => {
    if (!isPresent || !state || !finished || state.score === undefined) return;
    if (!state.daily) rememberDerivedReplayId(GAME_KEY, state.game_id);
    const detail = state.won
      ? `${state.mistakes} ${state.mistakes === 1 ? "greșeală" : "greșeli"}`
      : `pierdut · ${state.mistakes} greșeli`;
    let current = true;
    void recordOnce(state.game_id, state.score, detail, {
      puzzleKey,
      daily: state.daily,
      category: state.board_category,
    }).then((outcome) => {
      active.forgetIfCurrent(state.game_id);
      if (!current || !outcome) return;
      if (state.won) sound.playWin();
      else sound.playError();
      setRecordHit(outcome.isBest);
      setPuzzleRecordHit(outcome.isPuzzleBest);
      if (outcome.isBest || outcome.isPuzzleBest) sound.playRecord();
    });
    return () => {
      current = false;
    };
  }, [active, finished, isPresent, puzzleKey, recordOnce, state]);

  const beginAction = useCallback((previous: PerechiState, action: "match" | "hint") => {
    if (!isPresent || startInFlight.current) return null;
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
    if (!actionOwner.isCurrent(ticket)) return false;
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
      } else if (action === "hint" && fresh.hints_used > previous.hints_used && fresh.hint) {
        setFeedback(`Indiciu: ${fresh.hint.label}. Atinge cele două cuvinte marcate.`);
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

  const retryActionSync = useCallback(async () => {
    if (!isPresent || !state || busy || !actionSync) return;
    if (actionSync.kind === "changed") {
      actionOwner.invalidate();
      setActionSync(null);
      setState(null);
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
  }, [state, busy, actionSync, actionOwner, beginAction, isPresent, reconcile, retryResume]);

  const submitPair = useCallback(
    async (ids: [string, string]) => {
      if (!state || finished || actionsLocked) return;
      const ticket = beginAction(state, "match");
      if (!ticket) return;
      focusedTileBeforeMutation.current =
        ids.find((id) => tileRefs.current.get(id) === document.activeElement) ?? null;
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
              ? "S-au terminat încercările. Îți arăt perechile."
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
        setFeedback("Alegerea a fost golită.");
        return;
      }
      if (selected === null) {
        setSelected(id);
        setFeedback("Primul cuvânt este ales. Atinge perechea lui.");
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
      !state.hint_available
    ) {
      return;
    }
    const ticket = beginAction(state, "hint");
    if (!ticket) return;
    focusedTileBeforeMutation.current = null;
    setBusy(true);
    try {
      const fresh = await perechiApi.hint(state.game_id);
      if (!mayAdoptAction(ticket, state, "hint")) return;
      if (fresh.game_id !== ticket.gameId) {
        await reconcile(ticket, state, "hint");
        return;
      }
      setState(fresh);
      setSelected(null);
      setFeedback(`Indiciu: ${fresh.hint.label}. Atinge cele două cuvinte marcate.`);
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

  if (!state) {
    return (
      <div className="screen-pad fill">
        <div className="container col game-container" style={{ gap: 18, paddingBottom: 32 }}>
          <GameShell onExit={exitSafely} accent={DEF.accent} busy={loading} />
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
              <>
                <p style={{ margin: 0 }}>Opt cuvinte ascund patru perechi cu sens.</p>
                {starterVisible && (
                  <p className="faint" style={{ margin: "6px 0 0", fontSize: "0.82rem" }}>
                    Primele runde sunt mai blânde. Câștigă una și deblochezi tot catalogul.
                  </p>
                )}
              </>
            }
            steps={[
              { icon: "👆", label: "Atinge un cuvânt" },
              { icon: "👆", label: "Atinge perechea" },
              { icon: "✨", label: "Găsește-le pe toate" },
            ]}
            best={best}
            startLabel="Joacă"
            onStart={() => void start()}
            onDaily={() => void start({ daily: todayLocal() })}
            starting={loading}
          />
        </div>
      </div>
    );
  }

  const hintIds = new Set(state.hint?.tiles.map((tile) => tile.id) ?? []);
  const activeTiles = state.tiles.filter((tile) => !tile.solved);
  return (
    <div className="screen-pad fill perechi-game">
      <div className="container col game-container" style={{ gap: 14, paddingBottom: 32 }}>
        <GameShell onExit={exitSafely} accent={DEF.accent} title={DEF.title} helpGame={GAME_KEY} busy={loading}>
          <Hud>
            {state.daily && <StatBadge label="ZILNIC" value={state.daily} accent={DEF.accent} />}
            <StatBadge label="PERECHI" value={`${state.solved_count}/4`} accent={DEF.accent} />
            <StatBadge
              label="ÎNCERCĂRI"
              value={`${state.remaining_mistakes} rămase`}
              accent={DEF.accent}
            />
          </Hud>
        </GameShell>

        {!finished && actionSync && (
          <div className="card col perechi-sync-recovery" role="alert" style={{ gap: 8, padding: 12 }}>
            <strong>{actionSync.kind === "changed" ? "Jocul salvat s-a schimbat." : "Verificarea jocului nu a reușit."}</strong>
            <span>{actionSync.kind === "changed"
              ? "Încarcă jocul curent pentru a continua."
              : "Acțiunea poate fi deja salvată. Verifică jocul înainte de o nouă alegere sau de un indiciu."}</span>
            <Button type="button" onClick={() => void retryActionSync()} disabled={busy || !isPresent}>
              {busy ? "Se verifică…" : actionSync.kind === "changed" ? "Încarcă jocul curent" : "Verifică jocul"}
            </Button>
          </div>
        )}

        {!finished && !actionSync && (
          <NextMove
            icon={selected ? "👉" : "👆"}
            title={selected ? "Atinge perechea lui" : "Atinge primul cuvânt"}
            detail="Două atingeri verifică imediat. Repetările nu costă."
            progress={`${state.solved_count}/4`}
            accent={DEF.accent}
            ready={selected !== null}
          />
        )}

        {state.solved_pairs.length > 0 && !finished && (
          <div className="perechi-solved" aria-label="Perechi găsite">
            {state.solved_pairs.map((pair) => (
              <div className="perechi-solved-row" key={pair.tiles.map((tile) => tile.id).join("+")}>
                <strong>{pair.label}</strong>
                <span>{pair.tiles.map((tile) => tile.label).join(" + ")}</span>
              </div>
            ))}
          </div>
        )}

        {!finished && state.hint && (
          <div className="perechi-hint card">
            <span aria-hidden>💡</span>
            <span>
              <strong>{state.hint.label}</strong> · cele două marcate formează o pereche.
            </span>
          </div>
        )}

        {!finished && (
          <div
            className="perechi-grid"
            aria-label={`Cuvinte de potrivit, ${activeTiles.length} rămase`}
          >
            {activeTiles.map((tile) => {
              const isSelected = selected === tile.id || Boolean(checking?.includes(tile.id));
              const isHinted = hintIds.has(tile.id);
              return (
                <m.button
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
                  whileTap={{ scale: 0.97 }}
                >
                  <strong>{tile.label}</strong>
                  {isHinted && <span>indiciu</span>}
                </m.button>
              );
            })}
          </div>
        )}

        <AnimatePresence mode="wait">
          {!finished && !actionSync && feedback && (
            <m.div
              key={feedback}
              className="perechi-feedback card"
              role="status"
              aria-live="polite"
              initial={{ opacity: 0, y: -5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
            >
              {feedback}
            </m.div>
          )}
        </AnimatePresence>

        {!finished && (
          <div className="perechi-actions">
            <Button
              variant="secondary"
              disabled={actionsLocked || !state.hint_available}
              onClick={() => void requestHint()}
              title={
                state.hint_available
                  ? "Marchează o pereche nerezolvată"
                  : state.hints_used
                    ? "Indiciul a fost folosit"
                    : `Disponibil după ${Math.max(0, 2 - state.mistakes)} greșeli`
              }
            >
              {state.hints_used
                ? "Indiciu folosit"
                : state.hint_available
                  ? "💡 Arată o pereche"
                  : `Indiciu în ${Math.max(0, 2 - state.mistakes)}`}
            </Button>
            {selected && (
              <Button
                variant="secondary"
                disabled={actionsLocked}
                onClick={() => {
                  setSelected(null);
                  setFeedback("Alegerea a fost golită.");
                }}
              >
                Golește
              </Button>
            )}
          </div>
        )}

        {finished && state.solution && (
          <div ref={resultFocusRef}>
            <ResultCard
              startFailed={startFailed}
              icon={state.won ? "✨" : "🧠"}
              title={state.won ? "Toate se potrivesc!" : "Acestea erau perechile"}
              accent={DEF.accent}
              won={state.won}
              score={state.score}
              isRecord={recordHit}
              isPuzzleRecord={puzzleRecordHit}
              actionsBusy={loading}
              shareText={sharePayload}
              onCopy={copyShare}
              onReplay={() => void start({ previousGameId: state.game_id })}
              replayLabel={state.daily ? "Joacă liber →" : undefined}
              onOptions={() => {
                if (startInFlight.current) return;
                actionOwner.invalidate();
                setState(null);
              }}
              onExit={exitSafely}
            >
              <div className="perechi-solution">
                {!state.won && (
                  <p style={{ margin: "0 0 2px" }}>
                    Ai găsit {state.solved_count} din 4 perechi.
                  </p>
                )}
                {state.solution.map((pair) => (
                  <span key={pair.tiles.map((tile) => tile.id).join("+")}>
                    <strong>{pair.label}</strong>:{" "}
                    {pair.tiles.map((tile) => tile.label).join(" + ")}
                  </span>
                ))}
              </div>
            </ResultCard>
          </div>
        )}
      </div>
    </div>
  );
}
