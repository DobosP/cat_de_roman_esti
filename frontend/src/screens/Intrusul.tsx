// Intrusul — tap the one concept that does not belong with the other three.
// Every decision and point comes from the server; the browser only adds compact,
// touch-first feedback around the earned public state.

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
  intrusulApi,
  type CreateIntrusulOpts,
  type IntrusulState,
} from "../api/intrusul";
import { GameIntro } from "../components/GameIntro";
import { GameOptions } from "../components/GameOptions";
import { GameShell } from "../components/GameShell";
import { Hud, StatBadge } from "../components/Hud";
import { ResultCard } from "../components/ResultCard";
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
import "../styles/intrusul.css";

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
}

export default function Intrusul({ onExit, onToast }: Props) {
  const active = useActiveGame(GAME_KEY);
  const isPresent = useIsPresent();
  const recordOnce = useRecordScore(GAME_KEY);
  const startInFlight = useRef(false);
  const actionOwner = useMemo(() => createGameActionOwner(active), [active]);
  const tileRefs = useRef(new Map<string, HTMLButtonElement>());
  const hintButtonRef = useRef<HTMLButtonElement>(null);
  const pendingHintFocus = useRef<{
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
  useEffect(() => () => actionOwner.invalidate(), [actionOwner]);
  useLayoutEffect(() => {
    if (!isPresent) {
      actionOwner.invalidate();
      pendingHintFocus.current = null;
    }
  }, [actionOwner, isPresent]);
  const [state, setState] = useState<IntrusulState | null>(null);
  const [startFailed, setStartFailed] = useState(false);
  const [loading, setLoading] = useState(() => active.peek() !== null);
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [recordHit, setRecordHit] = useState(false);
  const [puzzleRecordHit, setPuzzleRecordHit] = useState(false);

  const finished = Boolean(state?.won || state?.lost);
  const actionsLocked = !isPresent || loading || busy || actionSync !== null;
  useLayoutEffect(() => {
    const pending = pendingHintFocus.current;
    if (!pending || busy) return;
    pendingHintFocus.current = null;
    if (!state || finished || actionsLocked || state.game_id !== pending.gameId ||
      active.peek() !== pending.savedId) return;
    // Disabling/removing the initiating hint button can move focus to body. Keep
    // deliberate navigation to options or another control during the request.
    if (document.activeElement !== document.body && document.activeElement !== pending.origin) return;
    const target = tileRefs.current.get(pending.tileId);
    if (target && !target.disabled) target.focus();
  }, [active, actionsLocked, busy, finished, state]);
  // Re-read after a terminal write when the player returns to this intro.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const best = useMemo(() => bestScore(GAME_KEY), [state]);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const starterVisible = useMemo(() => needsDerivedStarter(GAME_KEY), [state]);
  const exitSafely = useCallback(() => {
    if (startInFlight.current) return;
    actionOwner.invalidate();
    pendingHintFocus.current = null;
    onExit();
  }, [actionOwner, onExit]);

  const applyResumedGame = useCallback((fresh: IntrusulState) => {
    actionOwner.invalidate();
    pendingHintFocus.current = null;
    setActionSync(null);
    setBusy(false);
    setStartFailed(false);
    setState(fresh);
    setFeedback(
      fresh.won || fresh.lost
        ? null
        : "Joc reluat. Atinge cuvântul care nu se potrivește.",
    );
  }, [actionOwner]);
  const { recovery: resumeRecovery, retryResume, cancelResume, dismissRecovery } = useSavedGameResume({
    active,
    load: intrusulApi.get,
    isTerminal: isTerminalResume,
    setPending: setLoading,
    onResume: applyResumedGame,
  });

  const start = useCallback(
    async ({ daily, previousGameId }: StartOpts = {}) => {
      if (!isPresent) return;
      if (!acquireFlight(startInFlight)) return;
      actionOwner.invalidate();
      pendingHintFocus.current = null;
      cancelResume();
      setStartFailed(false);
      setLoading(true);
      const opts: CreateIntrusulOpts = daily
        ? { daily }
        : {
            starter: needsDerivedStarter(GAME_KEY),
            previousGameId:
              previousGameId ?? lastDerivedReplayId(GAME_KEY) ?? undefined,
          };
      try {
        const fresh = await intrusulApi.create(opts);
        setState(fresh);
        setActionSync(null);
        setBusy(false);
        active.remember(fresh.game_id);
        dismissRecovery();
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
      difficulty: state.difficulty,
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

  const beginAction = useCallback((previous: IntrusulState, action: "guess" | "hint") => {
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

  const mayAdoptAction = useCallback((ticket: GameActionTicket, previous: IntrusulState, action: "guess" | "hint") => {
    if (!actionOwner.isCurrent(ticket)) return false;
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
      !state.hint_available
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
        pendingHintFocus.current = {
          gameId: fresh.game_id,
          savedId: ticket.savedId,
          origin: focusOrigin,
          tileId: nextTile.id,
        };
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
                <p style={{ margin: 0 }}>Trei cuvinte au ceva în comun. Unul nu.</p>
                {starterVisible && (
                  <p className="faint" style={{ margin: "6px 0 0", fontSize: "0.82rem" }}>
                    Primele runde sunt mai blânde. Câștigă una și deblochezi tot catalogul.
                  </p>
                )}
              </>
            }
            steps={[
              { icon: "👀", label: "Privește cele patru" },
              { icon: "👆", label: "Atinge intrusul" },
              { icon: "✨", label: "Descoperă legătura" },
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

  const wrong = new Set(state.wrong_ids);
  return (
    <div className="screen-pad fill intrusul-game">
      <div className="container col game-container" style={{ gap: 14, paddingBottom: 32 }}>
        <GameShell onExit={exitSafely} accent={DEF.accent} title={DEF.title} busy={loading}>
          <Hud>
            {state.daily && <StatBadge label="ZILNIC" value={state.daily} accent={DEF.accent} />}
            <StatBadge
              label="GREȘELI"
              value={`${state.remaining_mistakes} rămase`}
              accent={DEF.accent}
            />
          </Hud>
        </GameShell>

        {!finished && actionSync && (
          <div className="card col intrusul-sync-recovery" role="alert" style={{ gap: 8, padding: 12 }}>
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
          <p className="intrusul-instruction" id="intrusul-instruction">
            Atinge cuvântul care nu se potrivește.
          </p>
        )}

        {!finished && state.clue && (
          <div className="intrusul-clue card">
            <span aria-hidden>💡</span>
            <span>
              Trei țin de <strong>{state.clue.label}</strong>.
            </span>
          </div>
        )}

        {!finished && (
          <div className="intrusul-grid" aria-label="Cuvinte pentru Intrusul" aria-describedby={!actionSync ? "intrusul-instruction" : undefined}>
            {state.tiles.map((tile) => {
              const tried = wrong.has(tile.id);
              return (
                <m.button
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
                  whileTap={{ scale: 0.97 }}
                >
                  <strong>{tile.label}</strong>
                  {tried && <span>ține de grup</span>}
                </m.button>
              );
            })}
          </div>
        )}

        <AnimatePresence mode="wait">
          {!finished && !actionSync && feedback && (
            <m.div
              key={feedback}
              className="intrusul-feedback card"
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

        {!finished && !state.hints_used && (
          <div className="intrusul-actions">
            {state.hint_available ? (
              <Button
                ref={hintButtonRef}
                variant="secondary"
                disabled={actionsLocked}
                onClick={() => void requestHint()}
                title="Arată legătura celor trei cuvinte. Costă 150 de puncte."
              >
                💡 Arată indiciul · −150 pct
              </Button>
            ) : (
              <span className="intrusul-hint-status">Indiciu disponibil după prima greșeală.</span>
            )}
          </div>
        )}

        {!finished && <GameOptions game={GAME_KEY} />}

        {finished && state.solution && (
          <ResultCard
              startFailed={startFailed}
            icon={state.won ? "🎯" : "🔎"}
            title={state.won ? "L-ai găsit!" : "Acesta era intrusul"}
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
            onExit={exitSafely}
          >
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
      </div>
    </div>
  );
}
