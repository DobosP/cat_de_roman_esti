// Alchimie — Infinite-Craft over the Romanian KG. Text-only: the inventory is a grid of
// clickable concept chips; pick two and "Combina" to discover their shared neighbour(s).
// Server-authoritative: we render whatever the backend returns and never know the target
// id until the server reveals it on a win.

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, m } from "framer-motion";
import { Button, Spinner, type ToastKind } from "@roedu/ui";
import {
  alchimieApi,
  ApiError,
  type AlchimieState,
  type Concept,
  type CreateOpts,
  type Difficulty,
  type InventoryItem,
} from "../api/alchimie";
import { GameShell } from "../components/GameShell";
import { ResultCard } from "../components/ResultCard";
import { GameIntro } from "../components/GameIntro";
import { Hud, StatBadge } from "../components/Hud";
import { DifficultyPicker } from "../components/DifficultyPicker";
import { useActiveGame } from "../hooks/useActiveGame";
import { useRecordScore } from "../hooks/useRecordScore";
import { gameByKey } from "../games";
import { sound } from "../sound";
import { bestScore } from "../scores";
import { categoryColor, categoryLabel } from "../categories";
import { CategoryPicker } from "../components/CategoryPicker";
import { buildSharePayload, copyResult, stableKey, todayLocal } from "../share";

const GAME_KEY = "alchimie";
const DEF = gameByKey("alchimie");

const GOLD = "#ffd166";

const DIFFICULTY_LABEL: Record<Difficulty, string> = {
  usor: "Ușor",
  normal: "Normal",
  greu: "Greu",
};

const DIFFICULTIES: { id: Difficulty; label: string; hint: string }[] = [
  { id: "usor", label: DIFFICULTY_LABEL.usor, hint: "țintă apropiată" },
  { id: "normal", label: "Normal", hint: "echilibrat" },
  { id: "greu", label: DIFFICULTY_LABEL.greu, hint: "țintă îndepărtată" },
];

export default function Alchimie({
  onExit,
  onToast,
}: {
  onExit: () => void;
  onToast: (m: string, k?: ToastKind) => void;
}) {
  const [state, setState] = useState<AlchimieState | null>(null);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [selected, setSelected] = useState<string[]>([]);
  // ids discovered by the most recent combine — used to animate them in.
  const [freshIds, setFreshIds] = useState<Set<string>>(new Set());
  // The pair the most recent nudge suggested — gets a glowing outline.
  const [hintIds, setHintIds] = useState<Set<string>>(new Set());
  const [lastMessage, setLastMessage] = useState<string | null>(null);
  const [difficulty, setDifficulty] = useState<Difficulty>("normal");
  const [category, setCategory] = useState<string | null>(null);
  const [isRecord, setIsRecord] = useState(false);
  const [isPuzzleRecord, setIsPuzzleRecord] = useState(false);
  const resumeAttempted = useRef(false);
  const active = useActiveGame("alchimie");
  const recordOnce = useRecordScore("alchimie");

  const best = useMemo(() => bestScore(GAME_KEY), []);

  useEffect(() => {
    if (resumeAttempted.current) return;
    resumeAttempted.current = true;
    const id = active.peek();
    if (!id) return;

    // No abort/cleanup on purpose: the ref guard blocks StrictMode's second run, so
    // the FIRST run's result must be allowed to land (a cancelled-flag cleanup would
    // discard it and resume would never happen in dev). Modern React ignores a
    // post-unmount state update.
    setLoading(true);
    void (async () => {
      try {
        const s = await alchimieApi.get(id);
        if (s.won === true) {
          active.forget();
          return;
        }
        setState(s);
        setDifficulty(s.difficulty);
        setCategory(s.board_category ?? null);
        setSelected([]);
        setFreshIds(new Set());
        setHintIds(new Set());
        setLastMessage(null);
        setIsRecord(false);
        setIsPuzzleRecord(false);
        onToast("Joc reluat.", "info");
      } catch {
        active.forget();
      } finally {
        setLoading(false);
      }
    })();
  }, [active, onToast]);

  const start = useCallback(
    async (opts: CreateOpts = {}) => {
      setLoading(true);
      try {
        const s = await alchimieApi.create(opts);
        setState(s);
        active.remember(s.game_id);
        setSelected([]);
        setFreshIds(new Set());
        setHintIds(new Set());
        setLastMessage(null);
        setIsRecord(false);
        setIsPuzzleRecord(false);
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
    [active, onToast],
  );

  const won = state?.won ?? false;

  const puzzleKey = useMemo(() => {
    if (!state?.won || !state.target.id) return null;
    const seeds = state.inventory
      .filter((item) => item.parents === null)
      .map((item) => item.id)
      .sort()
      .join(",");
    return stableKey([
      GAME_KEY,
      state.daily ? `daily-${state.daily}` : state.difficulty,
      state.target.id,
      seeds,
      state.board_category,
    ]);
  }, [state]);

  const sharePayload = useMemo(() => {
    if (!state?.won || !state.share) return null;
    return buildSharePayload({
      gameTitle: "Alchimie",
      serverShare: state.share,
      score: state.score,
      puzzleKey,
    });
  }, [state, puzzleKey]);

  // Win arpeggio fires once when we transition into the won state.
  useEffect(() => {
    if (won) sound.playWin();
  }, [won]);

  // Record the score exactly once when a game is won.
  useEffect(() => {
    if (!state || !state.won || state.score === undefined) return;
    active.forget();
    const movesLabel = state.moves === 1 ? "combinație" : "combinații";
    const detail = state.daily
      ? `Zilnic ${state.daily} · ${state.moves} ${movesLabel}`
      : `${DIFFICULTY_LABEL[state.difficulty]} · ${state.moves} ${movesLabel}`;
    const outcome = recordOnce(state.game_id, state.score, detail, {
      puzzleKey,
      difficulty: state.difficulty,
      daily: state.daily,
      category: state.board_category,
    });
    if (!outcome) return;
    const { isBest, isPuzzleBest } = outcome;
    setIsPuzzleRecord(isPuzzleBest);
    if (isBest) {
      setIsRecord(true);
      sound.playRecord();
    } else if (isPuzzleBest) {
      sound.playRecord();
    }
  }, [state, puzzleKey, recordOnce, active]);

  const toggle = useCallback(
    (id: string) => {
      if (busy || won) return;
      sound.playSelect();
      setSelected((prev) => {
        if (prev.includes(id)) return prev.filter((x) => x !== id);
        if (prev.length >= 2) return [prev[1], id];
        return [...prev, id];
      });
    },
    [busy, won],
  );

  const clearSelection = useCallback(() => {
    setSelected([]);
    setHintIds(new Set());
  }, []);

  const doCombine = useCallback(async () => {
    if (!state || selected.length !== 2 || busy) return;
    setBusy(true);
    const [a, b] = selected;
    try {
      const res = await alchimieApi.combine(state.game_id, a, b);
      setState(res);
      setSelected([]);
      setHintIds(new Set());
      setLastMessage(res.message);
      if (res.discovered.length > 0) {
        setFreshIds(new Set(res.discovered.map((d: Concept) => d.id)));
        if (!res.won) sound.playHop();
        // win sound handled by the won effect
      } else {
        setFreshIds(new Set());
        sound.playUndo();
        const hint = res.hint_available
          ? " Apasă „Indiciu” dacă te-ai blocat."
          : "";
        onToast(`Nicio combinație nouă din această pereche.${hint}`, "info");
      }
    } catch (err) {
      sound.playError();
      onToast(
        err instanceof ApiError
          ? err.message || `Combinație respinsă (${err.status}).`
          : "Combinație respinsă.",
        "error",
      );
    } finally {
      setBusy(false);
    }
  }, [state, selected, busy, onToast]);

  const doReset = useCallback(async () => {
    if (!state || busy) return;
    setBusy(true);
    try {
      const s = await alchimieApi.reset(state.game_id);
      setState(s);
      active.remember(s.game_id);
      setSelected([]);
      setFreshIds(new Set());
      setHintIds(new Set());
      setLastMessage(null);
      sound.playUndo();
    } catch (err) {
      onToast(
        err instanceof ApiError
          ? `Nu am putut reseta (${err.status}).`
          : "Nu am putut reseta.",
        "error",
      );
    } finally {
      setBusy(false);
    }
  }, [state, busy, active, onToast]);

  const newGame = useCallback(() => {
    active.forget();
    setState(null);
  }, [active]);

  // Ask for a gentle nudge: the server points at a useful pair (it costs some score).
  const doHint = useCallback(async () => {
    if (!state || busy || won) return;
    setBusy(true);
    try {
      const res = await alchimieApi.hint(state.game_id);
      setState(res);
      setLastMessage(res.message);
      if (res.hint) {
        const ids = res.hint.map((c) => c.id);
        setHintIds(new Set(ids));
        // Pre-select the suggested pair so the player can just press Combina.
        setSelected(ids);
        sound.playSelect();
      } else {
        setHintIds(new Set());
        onToast(res.message, "info");
      }
    } catch (err) {
      sound.playError();
      onToast(
        err instanceof ApiError
          ? err.message || `Niciun indiciu (${err.status}).`
          : "Niciun indiciu.",
        "error",
      );
    } finally {
      setBusy(false);
    }
  }, [state, busy, won, onToast]);

  const handleCopy = useCallback(async () => {
    if (!sharePayload) return;
    const ok = await copyResult(sharePayload);
    onToast(ok ? "Copiat!" : "Nu am putut copia.", ok ? "info" : "error");
  }, [sharePayload, onToast]);

  // Reveal a parent hint on hover/long-press: which two concepts produced a chip.
  const parentsOf = useCallback(
    (item: InventoryItem): string | null =>
      item.parents
        ? `${item.parents[0].label} + ${item.parents[1].label}`
        : null,
    [],
  );

  const inventory = useMemo(() => state?.inventory ?? [], [state]);
  const selectedItems = useMemo(
    () =>
      selected
        .map((id) => inventory.find((i) => i.id === id))
        .filter(Boolean) as InventoryItem[],
    [selected, inventory],
  );

  // Keyboard: Enter combines a ready pair, Escape clears the bench. Ignored while
  // typing in an input (none here) or once the game is finished.
  useEffect(() => {
    if (!state || won) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Enter" && selected.length === 2 && !busy) {
        e.preventDefault();
        void doCombine();
      } else if (e.key === "Escape" && selected.length > 0) {
        e.preventDefault();
        clearSelection();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [state, won, selected, busy, doCombine, clearSelection]);

  if (loading) {
    return (
      <div className="screen-pad fill center">
        <Spinner size="lg" label="Se încarcă…" />
      </div>
    );
  }

  // ---- Intro: difficulty picker + daily challenge + personal best. ----
  if (!state) {
    return (
      <div className="screen-pad fill">
        <div className="container col" style={{ gap: 18 }}>
          <GameShell onExit={onExit} accent={DEF.accent} />

          <GameIntro
            icon={DEF.icon}
            title={DEF.title}
            tag={DEF.tag}
            accent={DEF.accent}
            glow={DEF.glow}
            best={best}
            description={
              <p style={{ margin: 0 }}>
                Combină două concepte ca să le descoperi vecinii comuni și ajungi
                la ținta afișată. Cu cât folosești mai puține combinații, cu atât
                scorul este mai mare.
              </p>
            }
            startLabel="Joacă →"
            onStart={() => void start({ difficulty, category: category ?? undefined })}
            onDaily={() => void start({ difficulty, daily: todayLocal() })}
            dailyLabel="Provocarea zilei"
            starting={loading}
          >
            <DifficultyPicker
              options={DIFFICULTIES}
              value={difficulty}
              onChange={(id) => {
                sound.playSelect();
                setDifficulty(id);
              }}
            />
            <CategoryPicker
              game="alchimie"
              value={category}
              onChange={(key) => {
                sound.playSelect();
                setCategory(key);
              }}
              accent={DEF.accent}
            />
          </GameIntro>
        </div>
      </div>
    );
  }

  return (
    <div className="screen-pad fill" style={{ overflowY: "auto" }}>
      <div className="container col" style={{ gap: 18, paddingBottom: 32 }}>
        {/* Header */}
        <GameShell onExit={onExit} accent={DEF.accent} title={DEF.title}>
          <Hud>
            {state.daily ? (
              <StatBadge
                label="Zi"
                value={state.daily}
                accent={DEF.accent}
                title="Provocarea zilei"
              />
            ) : (
              <StatBadge
                label="Mod"
                value={DIFFICULTY_LABEL[state.difficulty]}
                accent={DEF.accent}
                title="Dificultate"
              />
            )}
            {state.board_category && (
              <StatBadge
                label="Categorie"
                value={categoryLabel(state.board_category)}
                accent={categoryColor(state.board_category)}
              />
            )}
            <StatBadge label="Combinații" value={state.moves} accent={DEF.accent} />
            <StatBadge
              label="Descoperite"
              value={state.discovered_count}
              accent={DEF.accent}
            />
            {state.hints_used > 0 && (
              <StatBadge
                label="Indicii"
                value={state.hints_used}
                accent={DEF.accent}
                title="Indicii folosite"
              />
            )}
          </Hud>
        </GameShell>

        {/* Target */}
        <m.div
          className="card"
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          style={{
            padding: 18,
            borderColor: won ? GOLD : DEF.accent,
            boxShadow: won
              ? `0 0 50px -16px ${GOLD}`
              : `0 0 36px -20px ${DEF.accent}`,
          }}
        >
          <div className="col" style={{ gap: 6 }}>
            <span
              className="faint"
              style={{ letterSpacing: "0.08em", fontSize: "0.72rem" }}
            >
              {won ? "ȚINTA FĂURITĂ" : "ȚINTA DE FĂURIT"}
            </span>
            <div className="row" style={{ gap: 10, alignItems: "baseline" }}>
              <span style={{ fontSize: "1.5rem" }} aria-hidden>
                {won ? "★" : "◎"}
              </span>
              <h2 style={{ margin: 0, color: won ? GOLD : "var(--text)" }}>
                {state.target.label}
              </h2>
            </div>
            {state.target.description && (
              <p className="muted" style={{ margin: 0, fontSize: "0.9rem" }}>
                {state.target.description}
              </p>
            )}
          </div>
        </m.div>

        {/* Combine bench */}
        {!won && (
          <div
            className="card row spread wrap"
            style={{ padding: 14, gap: 12, alignItems: "center" }}
          >
            <div
              className="row wrap"
              style={{ gap: 8, alignItems: "center", minHeight: 38 }}
            >
              <Slot item={selectedItems[0]} />
              <span
                className="faint"
                style={{ fontSize: "1.4rem" }}
                aria-hidden
              >
                +
              </span>
              <Slot item={selectedItems[1]} />
            </div>
            <div className="row wrap" style={{ gap: 8 }}>
              {selected.length > 0 && (
                <Button
                  type="button"
                  variant="secondary"
                  disabled={busy}
                  onClick={clearSelection}
                  title="Golește alambicul (Esc)"
                >
                  Golește
                </Button>
              )}
              {state.hint_available && (
                <Button
                  type="button"
                  variant="secondary"
                  disabled={busy}
                  onClick={() => void doHint()}
                  title="Îți arată o pereche utilă (costă puțin din scor)"
                  style={{ borderColor: GOLD, color: GOLD }}
                >
                  💡 Indiciu
                </Button>
              )}
              <Button
                type="button"
                disabled={busy || selected.length !== 2}
                onClick={doCombine}
                title="Combină cele două concepte (Enter)"
                aria-label="Combină cele două concepte selectate"
                style={{ borderColor: DEF.accent }}
              >
                {busy ? "…" : "⚗ Combină"}
              </Button>
            </div>
          </div>
        )}

        {/* Last combine feedback */}
        <AnimatePresence mode="wait">
          {lastMessage && (
            <m.p
              key={lastMessage + state.moves}
              className="muted center"
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              style={{ margin: 0, fontSize: "0.92rem" }}
            >
              {lastMessage}
            </m.p>
          )}
        </AnimatePresence>

        {/* Inventory */}
        <div className="col" style={{ gap: 8 }}>
          <span
            className="faint"
            style={{ letterSpacing: "0.06em", fontSize: "0.72rem" }}
          >
            INVENTAR ({inventory.length})
          </span>
          <div className="wrap" style={{ display: "flex", gap: 8 }}>
            <AnimatePresence initial={false}>
              {inventory.map((item) => {
                const isSel = selected.includes(item.id);
                const isFresh = freshIds.has(item.id);
                const isHint = hintIds.has(item.id);
                const isCrafted = item.parents !== null;
                const title = parentsOf(item) ?? "Concept de start";
                return (
                  <m.button
                    key={item.id}
                    type="button"
                    layout
                    initial={isFresh ? { scale: 0.4, opacity: 0 } : false}
                    animate={{
                      scale: 1,
                      opacity: 1,
                      // Suggested-by-hint chips give a soft attention pulse.
                      ...(isHint && !isSel
                        ? { scale: [1, 1.08, 1] }
                        : {}),
                    }}
                    transition={{ type: "spring", stiffness: 320, damping: 18 }}
                    onClick={() => toggle(item.id)}
                    disabled={won || busy}
                    aria-pressed={isSel}
                    title={title}
                    className="chip"
                    style={{
                      cursor: won ? "default" : "pointer",
                      borderColor: isSel
                        ? DEF.accent
                        : isHint
                          ? GOLD
                          : isFresh
                            ? GOLD
                            : "var(--surface-border)",
                      background: isSel
                        ? "color-mix(in srgb, var(--surface) 70%, " +
                          DEF.accent +
                          ")"
                        : isFresh
                          ? "color-mix(in srgb, var(--surface) 80%, " +
                            GOLD +
                            ")"
                          : undefined,
                      color: isSel || isFresh ? "var(--text)" : undefined,
                      fontWeight: isCrafted ? 600 : 500,
                      boxShadow:
                        isFresh || isHint ? `0 0 16px -4px ${GOLD}` : undefined,
                    }}
                  >
                    {isCrafted ? "✦ " : ""}
                    {item.label}
                  </m.button>
                );
              })}
            </AnimatePresence>
          </div>
        </div>

        {/* Footer actions */}
        <div className="row center wrap" style={{ gap: 12, marginTop: 8 }}>
          <Button
            type="button"
            variant="secondary"
            disabled={busy}
            onClick={doReset}
          >
            ↻ Reia același joc
          </Button>
          <Button
            type="button"
            variant="secondary"
            disabled={busy}
            onClick={newGame}
          >
            ⚙ Schimbă opțiunile
          </Button>
        </div>

        {/* Win banner */}
        <AnimatePresence>
          {won && (
            <ResultCard
              icon="★"
              title="Ai făurit ținta!"
              accent={GOLD}
              score={state.score}
              isRecord={isRecord}
              isPuzzleRecord={isPuzzleRecord}
              shareText={sharePayload}
              onCopy={() => void handleCopy()}
              onReplay={() =>
                void start({
                  difficulty: state.difficulty,
                  category: category ?? undefined,
                })
              }
              onOptions={newGame}
              onExit={onExit}
            >
              <strong style={{ color: "var(--text)" }}>{state.target.label}</strong> în{" "}
              {state.moves} {state.moves === 1 ? "combinație" : "combinații"} ·{" "}
              {state.discovered_count} concepte descoperite.
            </ResultCard>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

function Slot({ item }: { item: InventoryItem | undefined }) {
  if (!item) {
    return (
      <span
        className="chip faint"
        style={{
          borderStyle: "dashed",
          minWidth: 90,
          justifyContent: "center",
        }}
      >
        alege…
      </span>
    );
  }
  return (
    <span className="chip" style={{ borderColor: DEF.accent, color: "var(--text)" }}>
      {item.parents ? "✦ " : ""}
      {item.label}
    </span>
  );
}
