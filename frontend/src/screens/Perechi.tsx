// Perechi — eight visible words, four semantic matches. Choosing the second tile
// submits immediately: no drag gesture, no extra confirmation, no client-side answer map.

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, m } from "framer-motion";
import { Button, type ToastKind } from "@roedu/ui";
import { ApiError } from "../api/client";
import {
  acquireFlight,
  recoverAuthoritative,
  releaseFlight,
} from "../asyncControl.mjs";
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

interface Props {
  onExit: () => void;
  onToast: (message: string, kind?: ToastKind) => void;
}

interface StartOpts {
  daily?: string;
  previousGameId?: string;
}

type PendingFocus = { kind: "tile"; id: string } | { kind: "result" } | null;

export default function Perechi({ onExit, onToast }: Props) {
  const active = useActiveGame(GAME_KEY);
  const recordOnce = useRecordScore(GAME_KEY);
  const resumeOnce = useRef(false);
  const startInFlight = useRef(false);
  const actionInFlight = useRef(false);
  const tileRefs = useRef(new Map<string, HTMLButtonElement>());
  const resultFocusRef = useRef<HTMLDivElement>(null);
  const pendingFocus = useRef<PendingFocus>(null);
  const focusedTileBeforeMutation = useRef<string | null>(null);
  const [state, setState] = useState<PerechiState | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [checking, setChecking] = useState<[string, string] | null>(null);
  const [loading, setLoading] = useState(() => active.peek() !== null);
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [recordHit, setRecordHit] = useState(false);
  const [puzzleRecordHit, setPuzzleRecordHit] = useState(false);

  const finished = Boolean(state?.won || state?.lost);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const best = useMemo(() => bestScore(GAME_KEY), [state]);
  const exitSafely = useCallback(() => {
    if (!startInFlight.current) onExit();
  }, [onExit]);
  const queueFocusAfterUpdate = useCallback(
    (fresh: PerechiState, candidateIds: readonly string[]) => {
      const focusedId = focusedTileBeforeMutation.current;
      if (!focusedId || !candidateIds.includes(focusedId)) return;
      if (fresh.won || fresh.lost) {
        pendingFocus.current = { kind: "result" };
        return;
      }
      if (!fresh.tiles.find((tile) => tile.id === focusedId)?.solved) return;
      const nextId = nextActiveTileId(fresh.tiles, focusedId);
      pendingFocus.current = nextId
        ? { kind: "tile", id: nextId }
        : { kind: "result" };
    },
    [],
  );

  useEffect(() => {
    const pending = pendingFocus.current;
    if (!pending) return;
    const target =
      pending.kind === "tile"
        ? tileRefs.current.get(pending.id)
        : resultFocusRef.current?.querySelector<HTMLButtonElement>("button:not(:disabled)");
    if (!target) return;
    target.focus();
    pendingFocus.current = null;
  }, [finished, state?.solved_count]);

  const start = useCallback(
    async ({ daily, previousGameId }: StartOpts = {}) => {
      if (!acquireFlight(startInFlight)) return;
      setLoading(true);
      setSelected(null);
      setChecking(null);
      setFeedback(null);
      setRecordHit(false);
      setPuzzleRecordHit(false);
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
        active.remember(fresh.game_id);
      } catch (error) {
        onToast(
          error instanceof ApiError
            ? error.message || `Nu am putut porni jocul (${error.status}).`
            : "Nu am putut porni jocul.",
          "error",
        );
      } finally {
        releaseFlight(startInFlight);
        setLoading(false);
      }
    },
    [active, onToast],
  );

  useEffect(() => {
    if (resumeOnce.current) return;
    resumeOnce.current = true;
    const gameId = active.peek();
    if (!gameId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    void (async () => {
      try {
        const fresh = await perechiApi.get(gameId);
        setState(fresh);
        setSelected(null);
        setChecking(null);
        setFeedback(
          fresh.won || fresh.lost ? null : "Joc reluat. Atinge primul cuvânt.",
        );
      } catch (error) {
        if (error instanceof ApiError && error.status === 404) {
          active.forget();
        } else {
          onToast("Nu am putut relua jocul. Încercăm din nou la următoarea deschidere.", "error");
        }
      } finally {
        setLoading(false);
      }
    })();
  }, [active, onToast]);

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
    if (!state || !finished || state.score === undefined) return;
    if (!state.daily) rememberDerivedReplayId(GAME_KEY, state.game_id);
    active.forget();
    const detail = state.won
      ? `${state.mistakes} ${state.mistakes === 1 ? "greșeală" : "greșeli"}`
      : `pierdut · ${state.mistakes} greșeli`;
    const outcome = recordOnce(state.game_id, state.score, detail, {
      puzzleKey,
      daily: state.daily,
      category: state.board_category,
    });
    if (!outcome) return;
    if (state.won) sound.playWin();
    else sound.playError();
    setRecordHit(outcome.isBest);
    setPuzzleRecordHit(outcome.isPuzzleBest);
    if (outcome.isBest || outcome.isPuzzleBest) sound.playRecord();
  }, [active, finished, puzzleKey, recordOnce, state]);

  const reconcile = useCallback(
    async (previous: PerechiState, action: "match" | "hint") => {
      const recovered = await recoverAuthoritative(() => perechiApi.get(previous.game_id));
      if (!recovered.ok) {
        setFeedback("Nu am putut confirma acțiunea. Jocul rămâne salvat; încearcă din nou.");
        return null;
      }
      const fresh = recovered.value;
      if (
        action === "match" &&
        (fresh.solved_count > previous.solved_count || fresh.won || fresh.lost)
      ) {
        queueFocusAfterUpdate(fresh, [...tileRefs.current.keys()]);
      }
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
      return fresh;
    },
    [queueFocusAfterUpdate],
  );

  const submitPair = useCallback(
    async (ids: [string, string]) => {
      if (!state || finished || busy || !acquireFlight(actionInFlight)) return;
      focusedTileBeforeMutation.current =
        ids.find((id) => tileRefs.current.get(id) === document.activeElement) ?? null;
      setChecking(ids);
      setBusy(true);
      try {
        const result = await perechiApi.match(state.game_id, ids);
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
        const fresh = await reconcile(state, "match");
        if (!fresh) sound.playError();
      } finally {
        releaseFlight(actionInFlight);
        focusedTileBeforeMutation.current = null;
        setChecking(null);
        setBusy(false);
      }
    },
    [busy, finished, queueFocusAfterUpdate, reconcile, state],
  );

  const choose = useCallback(
    (id: string) => {
      if (!state || finished || busy) return;
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
    [busy, finished, selected, state, submitPair],
  );

  const requestHint = useCallback(async () => {
    if (
      !state ||
      finished ||
      busy ||
      !state.hint_available ||
      !acquireFlight(actionInFlight)
    ) {
      return;
    }
    focusedTileBeforeMutation.current = null;
    setBusy(true);
    try {
      const fresh = await perechiApi.hint(state.game_id);
      setState(fresh);
      setSelected(null);
      setFeedback(`Indiciu: ${fresh.hint.label}. Atinge cele două cuvinte marcate.`);
      sound.playSelect();
    } catch {
      const fresh = await reconcile(state, "hint");
      if (!fresh) sound.playError();
    } finally {
      releaseFlight(actionInFlight);
      setBusy(false);
    }
  }, [busy, finished, reconcile, state]);

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
            icon={DEF.icon}
            title={DEF.title}
            tag={DEF.tag}
            accent={DEF.accent}
            glow={DEF.glow}
            description={<p style={{ margin: 0 }}>Opt cuvinte ascund patru perechi cu sens.</p>}
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
        <GameShell onExit={exitSafely} accent={DEF.accent} title={DEF.title} busy={loading}>
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

        {!finished && (
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
                  disabled={busy}
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
          {!finished && feedback && (
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
              disabled={busy || !state.hint_available}
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
                disabled={busy}
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
                active.forget();
                setState(null);
              }}
              onExit={exitSafely}
            >
              <div className="perechi-solution">
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
