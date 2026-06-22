// Conexiuni — NYT Connections over the Romanian KG. Text-only: a 4x4 grid of selectable
// tile buttons. Pick exactly 4 and "Verifica"; the server says whether they share a
// category (locks it as a coloured row) or not (one_away feedback + a lost life). Win when
// all 4 groups are found; lose at 0 lives — then the full solution is revealed.
//
// Server-authoritative: the grouping + solution live on the server; this component renders
// what it returns and surfaces a personal best + a shareable result on finish.

import { useCallback, useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ApiError } from "../api/client";
import {
  conexiuniApi,
  type ConexiuniState,
  type Difficulty,
  type GuessResult,
  type SolvedGroup,
} from "../api/conexiuni";
import type { ToastKind } from "../components/Toast";
import { sound } from "../sound";
import { categoryColor } from "../theme/tokens";
import { recordScore, bestScore } from "../scores";
import { copyResult, todayLocal } from "../share";

const GAME_KEY = "conexiuni";
const ACCENT = "#5fd99b";

interface SelfProps {
  onExit: () => void;
  onToast: (message: string, kind?: ToastKind) => void;
}

const DIFF_LABEL: Record<Difficulty, string> = {
  usor: "Usor",
  normal: "Normal",
  greu: "Greu",
};

type StartMode =
  | { kind: "seed"; difficulty: Difficulty }
  | { kind: "daily" };

export default function Conexiuni({ onExit, onToast }: SelfProps) {
  const [state, setState] = useState<ConexiuniState | null>(null);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [selected, setSelected] = useState<string[]>([]);
  const [difficulty, setDifficulty] = useState<Difficulty>("normal");
  const [recordHit, setRecordHit] = useState(false);
  const [shake, setShake] = useState(0);

  // Recompute the persisted best whenever the game state changes (e.g. after a
  // finished round writes a new record and we return to the start screen).
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const best = useMemo(() => bestScore(GAME_KEY), [state]);

  const start = useCallback(
    async (mode: StartMode) => {
      setLoading(true);
      setRecordHit(false);
      try {
        const s =
          mode.kind === "daily"
            ? await conexiuniApi.create({ daily: todayLocal() })
            : await conexiuniApi.create({ difficulty: mode.difficulty });
        setState(s);
        setSelected([]);
      } catch (err) {
        onToast(
          err instanceof ApiError
            ? `Nu am putut porni jocul (${err.status}).`
            : "Nu am putut porni jocul.",
          "error",
        );
      } finally {
        setLoading(false);
      }
    },
    [onToast],
  );

  // Solved-id set so solved tiles drop out of the grid.
  const solvedIds = useMemo(() => {
    const s = new Set<string>();
    state?.solved.forEach((g) => g.tiles.forEach((t) => s.add(t.id)));
    return s;
  }, [state]);

  const remainingTiles = useMemo(
    () => (state ? state.tiles.filter((t) => !solvedIds.has(t.id)) : []),
    [state, solvedIds],
  );

  const finished = (state?.won ?? false) || (state?.lost ?? false);

  // Record the score + best once, on transition into a finished state.
  useEffect(() => {
    if (!state || !finished || state.score === undefined) return;
    const detail = state.won
      ? `${state.mistakes} greseli`
      : `pierdut · ${state.mistakes} greseli`;
    const { isBest } = recordScore(GAME_KEY, state.score, detail);
    if (state.won) sound.playWin();
    else sound.playError();
    if (isBest) {
      setRecordHit(true);
      sound.playRecord();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [finished, state?.score]);

  const toggle = useCallback(
    (id: string) => {
      if (busy || finished) return;
      sound.playSelect();
      setSelected((prev) => {
        if (prev.includes(id)) return prev.filter((x) => x !== id);
        if (prev.length >= 4) return prev;
        return [...prev, id];
      });
    },
    [busy, finished],
  );

  const submit = useCallback(async () => {
    if (!state || selected.length !== 4 || busy) return;
    setBusy(true);
    try {
      const res: GuessResult = await conexiuniApi.guess(state.game_id, selected);
      if (res.correct) {
        sound.playWin();
        setSelected([]);
        // refresh authoritative state
        const fresh = await conexiuniApi.get(state.game_id);
        setState(fresh);
        if (!fresh.won && res.category) {
          onToast(`Grup gasit: ${res.category.label}!`, "info");
        }
      } else {
        sound.playError();
        setShake((n) => n + 1);
        if (res.one_away) onToast("Aproape! 3 din 4.", "info");
        else onToast("Gresit.", "info");
        // refresh authoritative state (lives, lost, solution)
        const fresh = await conexiuniApi.get(state.game_id);
        setState(fresh);
        setSelected([]);
      }
    } catch (err) {
      sound.playError();
      onToast(
        err instanceof ApiError
          ? err.message || `Verificare respinsa (${err.status}).`
          : "Verificare respinsa.",
        "error",
      );
    } finally {
      setBusy(false);
    }
  }, [state, selected, busy, onToast]);

  const copyShare = useCallback(async () => {
    if (!state?.share) return;
    const ok = await copyResult(state.share);
    if (ok) onToast("Copiat!", "info");
    else onToast("Nu am putut copia.", "error");
  }, [state, onToast]);

  // ----------------------------------------------------------------- INTRO
  if (!state) {
    return (
      <div className="screen-pad fill" style={{ overflowY: "auto" }}>
        <div className="container col" style={{ gap: 18, paddingBottom: 32 }}>
          <div className="row spread wrap" style={{ gap: 12 }}>
            <button type="button" className="btn btn-ghost" onClick={onExit}>
              ← Meniu
            </button>
            <span className="badge" style={{ borderColor: ACCENT, color: ACCENT }}>
              🔗 Conexiuni
            </span>
          </div>

          <motion.div
            className="card col"
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            style={{ padding: 20, gap: 12, borderColor: ACCENT }}
          >
            <h2 style={{ margin: 0 }}>Conexiuni</h2>
            <p className="muted" style={{ margin: 0 }}>
              16 concepte, 4 grupuri ascunse. Alege exact 4 care impart o categorie. Ai 4
              vieti — gaseste toate grupurile!
            </p>
            {best && (
              <p className="faint" style={{ margin: 0 }}>
                Record: {best.score} pct · {best.detail}
              </p>
            )}
          </motion.div>

          <div className="col" style={{ gap: 8 }}>
            <span className="faint" style={{ letterSpacing: "0.06em", fontSize: "0.72rem" }}>
              DIFICULTATE
            </span>
            <div className="row wrap" style={{ gap: 8 }}>
              {(["usor", "normal", "greu"] as Difficulty[]).map((d) => (
                <button
                  key={d}
                  type="button"
                  className="btn"
                  onClick={() => setDifficulty(d)}
                  style={{
                    borderColor: difficulty === d ? ACCENT : "var(--surface-border)",
                    color: difficulty === d ? ACCENT : undefined,
                    fontWeight: difficulty === d ? 700 : 500,
                  }}
                >
                  {DIFF_LABEL[d]}
                </button>
              ))}
            </div>
          </div>

          <div className="row wrap center" style={{ gap: 12, marginTop: 8 }}>
            <button
              type="button"
              className="btn btn-primary"
              disabled={loading}
              onClick={() => void start({ kind: "seed", difficulty })}
              style={{ borderColor: ACCENT }}
            >
              {loading ? "…" : "Joaca"}
            </button>
            <button
              type="button"
              className="btn btn-ghost"
              disabled={loading}
              onClick={() => void start({ kind: "daily" })}
            >
              ★ Provocarea zilei
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ----------------------------------------------------------------- BOARD
  const lifeDots = Array.from({ length: 4 }, (_, i) => i < state.lives);

  return (
    <div className="screen-pad fill" style={{ overflowY: "auto" }}>
      <div className="container col" style={{ gap: 16, paddingBottom: 32 }}>
        {/* Header */}
        <div className="row spread wrap" style={{ gap: 12 }}>
          <button type="button" className="btn btn-ghost" onClick={onExit}>
            ← Meniu
          </button>
          <div className="row wrap" style={{ gap: 8, alignItems: "center" }}>
            <span className="badge" style={{ borderColor: ACCENT, color: ACCENT }}>
              🔗 Conexiuni
            </span>
            {state.daily && <span className="badge">★ {state.daily}</span>}
            <span className="badge">{DIFF_LABEL[state.difficulty]}</span>
            <span className="row" style={{ gap: 4 }} aria-label={`${state.lives} vieti`}>
              {lifeDots.map((alive, i) => (
                <span key={i} aria-hidden style={{ opacity: alive ? 1 : 0.25 }}>
                  {alive ? "●" : "○"}
                </span>
              ))}
            </span>
          </div>
        </div>

        {/* Solved groups as locked coloured rows */}
        <AnimatePresence initial={false}>
          {state.solved.map((g) => (
            <SolvedRow key={g.key} group={g} />
          ))}
        </AnimatePresence>

        {/* Active board */}
        {!finished && (
          <motion.div
            key={shake}
            animate={shake ? { x: [0, -8, 8, -6, 6, 0] } : {}}
            transition={{ duration: 0.4 }}
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(4, 1fr)",
              gap: 8,
            }}
          >
            <AnimatePresence initial={false}>
              {remainingTiles.map((t) => {
                const isSel = selected.includes(t.id);
                return (
                  <motion.button
                    key={t.id}
                    type="button"
                    layout
                    initial={{ scale: 0.6, opacity: 0 }}
                    animate={{
                      scale: isSel ? 1.05 : 1,
                      opacity: 1,
                    }}
                    exit={{ scale: 0.4, opacity: 0 }}
                    transition={{ type: "spring", stiffness: 320, damping: 20 }}
                    onClick={() => toggle(t.id)}
                    disabled={busy}
                    className="card center"
                    style={{
                      padding: "12px 6px",
                      minHeight: 64,
                      cursor: "pointer",
                      textAlign: "center",
                      fontSize: "0.82rem",
                      lineHeight: 1.15,
                      borderColor: isSel ? ACCENT : "var(--surface-border)",
                      background: isSel
                        ? `color-mix(in srgb, var(--surface) 65%, ${ACCENT})`
                        : undefined,
                      color: isSel ? "var(--text)" : undefined,
                      fontWeight: isSel ? 700 : 500,
                      boxShadow: isSel ? `0 0 18px -6px ${ACCENT}` : undefined,
                    }}
                  >
                    {t.label}
                  </motion.button>
                );
              })}
            </AnimatePresence>
          </motion.div>
        )}

        {/* Controls */}
        {!finished && (
          <div className="row center wrap" style={{ gap: 12 }}>
            <span className="faint">{selected.length}/4 selectate</span>
            {selected.length > 0 && (
              <button
                type="button"
                className="btn btn-ghost"
                disabled={busy}
                onClick={() => setSelected([])}
              >
                Goleste
              </button>
            )}
            <button
              type="button"
              className="btn btn-primary"
              disabled={busy || selected.length !== 4}
              onClick={submit}
              style={{ borderColor: ACCENT }}
            >
              {busy ? "…" : "Verifica"}
            </button>
          </div>
        )}

        {/* Lose reveal */}
        {state.lost && state.solution && (
          <div className="col" style={{ gap: 8 }}>
            <span className="faint" style={{ letterSpacing: "0.06em", fontSize: "0.72rem" }}>
              SOLUTIA
            </span>
            {state.solution.map((g) => (
              <SolvedRow key={g.key} group={g} dim />
            ))}
          </div>
        )}

        {/* Finish banner */}
        <AnimatePresence>
          {finished && (
            <motion.div
              className="card center col"
              initial={{ scale: 0.85, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ type: "spring", stiffness: 240, damping: 18 }}
              style={{
                padding: 22,
                textAlign: "center",
                gap: 6,
                borderColor: state.won ? ACCENT : "var(--surface-border)",
                boxShadow: state.won ? `0 0 60px -18px ${ACCENT}` : undefined,
              }}
            >
              <div style={{ fontSize: "2.2rem" }} aria-hidden>
                {state.won ? "🎉" : "💔"}
              </div>
              <h2 style={{ margin: 0, color: state.won ? ACCENT : "var(--text)" }}>
                {state.won ? "Toate grupurile gasite!" : "Ai ramas fara vieti."}
              </h2>
              <p className="muted" style={{ margin: 0 }}>
                Scor: <strong style={{ color: "var(--text)" }}>{state.score}</strong> ·{" "}
                {state.mistakes} greseli
              </p>
              {recordHit && (
                <motion.p
                  initial={{ scale: 0.6, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  style={{ margin: 0, color: "#ffd166", fontWeight: 700 }}
                >
                  ★ Record!
                </motion.p>
              )}
              <div className="row center wrap" style={{ gap: 12, marginTop: 14 }}>
                {state.share && (
                  <button type="button" className="btn btn-ghost" onClick={copyShare}>
                    Copiaza rezultatul
                  </button>
                )}
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => void start({ kind: "seed", difficulty })}
                  style={{ borderColor: ACCENT }}
                >
                  Joc nou →
                </button>
                <button type="button" className="btn btn-ghost" onClick={onExit}>
                  Meniu
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

function SolvedRow({ group, dim }: { group: SolvedGroup; dim?: boolean }) {
  const color = categoryColor(group.key);
  return (
    <motion.div
      layout
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: dim ? 0.7 : 1 }}
      transition={{ type: "spring", stiffness: 260, damping: 20 }}
      className="card col"
      style={{
        padding: 12,
        gap: 6,
        borderColor: color,
        background: `color-mix(in srgb, var(--surface) 78%, ${color})`,
      }}
    >
      <span style={{ fontWeight: 700, color: "var(--text)", letterSpacing: "0.03em" }}>
        {group.label}
      </span>
      <div className="row wrap" style={{ gap: 6 }}>
        {group.tiles.map((t) => (
          <span key={t.id} className="chip" style={{ borderColor: color }}>
            {t.label}
          </span>
        ))}
      </div>
    </motion.div>
  );
}
