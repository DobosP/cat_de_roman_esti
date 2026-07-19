// Intrusul — tap the one concept that does not belong with the other three.
// Every decision and point comes from the server; the browser only adds compact,
// touch-first feedback around the earned public state.

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
  intrusulApi,
  type CreateIntrusulOpts,
  type IntrusulState,
} from "../api/intrusul";
import { GameIntro } from "../components/GameIntro";
import { GameShell } from "../components/GameShell";
import { Hud, StatBadge } from "../components/Hud";
import { NextMove } from "../components/PlayGuide";
import { ResultCard } from "../components/ResultCard";
import { gameByKey } from "../games";
import { useActiveGame } from "../hooks/useActiveGame";
import { useRecordScore } from "../hooks/useRecordScore";
import { bestScore, timesPlayed } from "../scores";
import { buildSharePayload, copyResult, stableKey, todayLocal } from "../share";
import { sound } from "../sound";
import "../styles/intrusul.css";

const GAME_KEY = "intrusul";
const DEF = gameByKey(GAME_KEY);
const DIFFICULTY_LABEL = { usor: "Ușor", normal: "Normal", greu: "Greu" } as const;

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
  const recordOnce = useRecordScore(GAME_KEY);
  const resumeOnce = useRef(false);
  const startInFlight = useRef(false);
  const actionInFlight = useRef(false);
  const [state, setState] = useState<IntrusulState | null>(null);
  const [loading, setLoading] = useState(() => active.peek() !== null);
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [recordHit, setRecordHit] = useState(false);
  const [puzzleRecordHit, setPuzzleRecordHit] = useState(false);

  const finished = Boolean(state?.won || state?.lost);
  // Re-read after a terminal write when the player returns to this intro.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const best = useMemo(() => bestScore(GAME_KEY), [state]);
  const exitSafely = useCallback(() => {
    if (!startInFlight.current) onExit();
  }, [onExit]);

  const start = useCallback(
    async ({ daily, previousGameId }: StartOpts = {}) => {
      if (!acquireFlight(startInFlight)) return;
      setLoading(true);
      setFeedback(null);
      setRecordHit(false);
      setPuzzleRecordHit(false);
      const opts: CreateIntrusulOpts = daily
        ? { daily }
        : {
            starter: timesPlayed(GAME_KEY) === 0,
            previousGameId,
          };
      try {
        const fresh = await intrusulApi.create(opts);
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
        const fresh = await intrusulApi.get(gameId);
        setState(fresh);
        setFeedback(
          fresh.won || fresh.lost
            ? null
            : "Joc reluat. Atinge cuvântul care nu se potrivește.",
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
    if (!state || !finished || state.score === undefined) return;
    active.forget();
    const detail = state.won
      ? `${state.mistakes} ${state.mistakes === 1 ? "greșeală" : "greșeli"}`
      : `pierdut · ${state.mistakes} greșeli`;
    const outcome = recordOnce(state.game_id, state.score, detail, {
      puzzleKey,
      daily: state.daily,
      difficulty: state.difficulty,
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
    async (previous: IntrusulState, action: "guess" | "hint") => {
      const recovered = await recoverAuthoritative(() => intrusulApi.get(previous.game_id));
      if (!recovered.ok) {
        setFeedback("Nu am putut confirma acțiunea. Jocul rămâne salvat; încearcă din nou.");
        return null;
      }
      const fresh = recovered.value;
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
      return fresh;
    },
    [],
  );

  const choose = useCallback(
    async (id: string) => {
      if (!state || finished || busy || !acquireFlight(actionInFlight)) return;
      setBusy(true);
      try {
        const result = await intrusulApi.guess(state.game_id, id);
        setState(result);
        setFeedback(result.message);
        // The terminal effect owns the win sound and score recording.
        if (!result.correct && result.already_tried) sound.playUndo();
        else if (!result.correct) sound.playError();
      } catch {
        const fresh = await reconcile(state, "guess");
        if (!fresh) sound.playError();
      } finally {
        releaseFlight(actionInFlight);
        setBusy(false);
      }
    },
    [busy, finished, reconcile, state],
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
    setBusy(true);
    try {
      const fresh = await intrusulApi.hint(state.game_id);
      setState(fresh);
      setFeedback(fresh.clue?.message ?? "Indiciul este pe tablă.");
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
          <GameShell onExit={exitSafely} accent={DEF.accent} />
          <GameIntro
            icon={DEF.icon}
            title={DEF.title}
            tag={DEF.tag}
            accent={DEF.accent}
            glow={DEF.glow}
            description={<p style={{ margin: 0 }}>Trei cuvinte au ceva în comun. Unul nu.</p>}
            steps={[
              { icon: "👀", label: "Privește cele patru" },
              { icon: "👆", label: "Atinge intrusul" },
              { icon: "💡", label: "Cere un indiciu" },
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
        <GameShell onExit={exitSafely} accent={DEF.accent} title={DEF.title}>
          <Hud>
            {state.daily && <StatBadge label="ZILNIC" value={state.daily} accent={DEF.accent} />}
            <StatBadge
              label="NIVEL"
              value={DIFFICULTY_LABEL[state.difficulty]}
              accent={DEF.accent}
            />
            <StatBadge
              label="ÎNCERCĂRI"
              value={`${state.remaining_mistakes} rămase`}
              accent={DEF.accent}
            />
          </Hud>
        </GameShell>

        {!finished && (
          <NextMove
            icon="🔎"
            title="Care este intrusul?"
            detail="Atinge un cuvânt. Repetările nu costă."
            progress={`${state.mistakes}/3`}
            accent={DEF.accent}
          />
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
          <div className="intrusul-grid" aria-label="Cuvinte pentru Intrusul">
            {state.tiles.map((tile) => {
              const tried = wrong.has(tile.id);
              return (
                <m.button
                  key={tile.id}
                  type="button"
                  className={`card intrusul-tile${tried ? " intrusul-tile--tried" : ""}`}
                  onClick={() => void choose(tile.id)}
                  disabled={busy}
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
          {!finished && feedback && (
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

        {!finished && (
          <div className="intrusul-actions">
            <Button
              variant="secondary"
              disabled={busy || !state.hint_available}
              onClick={() => void requestHint()}
              title={
                state.hint_available
                  ? "Arată legătura celor trei cuvinte"
                  : state.hints_used
                    ? "Indiciul a fost folosit"
                    : "Disponibil după prima greșeală"
              }
            >
              {state.hints_used
                ? "Indiciu folosit"
                : state.hint_available
                  ? "💡 Arată indiciul"
                  : "💡 Indiciu după 1 greșeală"}
            </Button>
          </div>
        )}

        {finished && state.solution && (
          <ResultCard
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
            onOptions={() => {
              if (startInFlight.current) return;
              active.forget();
              setState(null);
            }}
            onExit={exitSafely}
          >
            <div className="intrusul-solution">
              <strong className="intrusul-answer">{state.solution.intruder.label}</strong>
              <span>
                Celelalte trei: <strong>{state.solution.group.label}</strong>
              </span>
              <span>{state.solution.group.tiles.map((tile) => tile.label).join(" · ")}</span>
            </div>
          </ResultCard>
        )}
      </div>
    </div>
  );
}
