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
import { createGameActionOwner, recoverOwnedGameAction, type GameActionTicket } from "../gameActionRecovery.mjs";
import { GameShell } from "../components/GameShell";
import { ResultCard } from "../components/ResultCard";
import { GameIntro } from "../components/GameIntro";
import { StartFailureNotice } from "../components/StartFailureNotice";
import { Hud, StatBadge } from "../components/Hud";
import { NextMove } from "../components/PlayGuide";
import { DifficultyPicker } from "../components/DifficultyPicker";
import { useActiveGame } from "../hooks/useActiveGame";
import { useRecordScore } from "../hooks/useRecordScore";
import { useSavedGameResume } from "../hooks/useSavedGameResume";
import { gameByKey } from "../games";
import { sound } from "../sound";
import { bestScore } from "../scores";
import { categoryColor, categoryLabel } from "../categories";
import { CategoryPicker } from "../components/CategoryPicker";
import { buildSharePayload, copyResult, stableKey, todayLocal } from "../share";

const GAME_KEY = "alchimie";
const DEF = gameByKey("alchimie");

const GOLD = "#ffd166";
const REACTION_LOG_LIMIT = 12;

const isTerminalResume = (state: AlchimieState) => state.won === true;

type ActionSync = { gameId: string; kind: "failed" | "changed" };

type CraftedItem = InventoryItem & { parents: [Concept, Concept] };

interface Reaction {
  ingredientKey: string;
  parents: [Concept, Concept];
  results: CraftedItem[];
}

type InventoryView = "recent" | "useful" | "all";

const INVENTORY_VIEW_LABEL: Record<InventoryView, string> = {
  recent: "Recente",
  useful: "Utile",
  all: "Toate",
};

function isCraftedItem(item: InventoryItem): item is CraftedItem {
  return item.parents !== null;
}

function buildReactionLog(inventory: InventoryItem[]): Reaction[] {
  const chronological: Reaction[] = [];

  for (const item of inventory) {
    if (!isCraftedItem(item)) continue;
    const ingredientKey = JSON.stringify(item.parents.map((parent) => parent.id).sort());
    const previous = chronological[chronological.length - 1];
    if (previous?.ingredientKey === ingredientKey) {
      previous.results.push(item);
    } else {
      chronological.push({
        ingredientKey,
        parents: item.parents,
        results: [item],
      });
    }
  }

  return chronological.slice(-REACTION_LOG_LIMIT).reverse();
}

function pairKey(ids: readonly string[]): string | null {
  return ids.length === 2 ? JSON.stringify([...ids].sort()) : null;
}

function normalizeInventorySearch(value: string): string {
  return value
    .normalize("NFD")
    .replace(/\p{M}/gu, "")
    .toLocaleLowerCase("ro-RO")
    .trim();
}

const DIFFICULTY_LABEL: Record<Difficulty, string> = {
  usor: "Ușor",
  normal: "Normal",
  greu: "Greu",
};

const DIFFICULTIES: { id: Difficulty; label: string; hint: string }[] = [
  { id: "usor", label: DIFFICULTY_LABEL.usor, hint: "recomandat" },
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
  const [startFailed, setStartFailed] = useState(false);
  const startInFlight = useRef(false);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [busy, setBusy] = useState(false);
  const [selected, setSelected] = useState<string[]>([]);
  const [emptyPairKey, setEmptyPairKey] = useState<string | null>(null);
  const [emptyRecoveryActive, setEmptyRecoveryActive] = useState(false);
  // ids discovered by the most recent combine — used to animate them in.
  const [freshIds, setFreshIds] = useState<Set<string>>(new Set());
  // The pair the most recent nudge suggested — gets a glowing outline.
  const [hintIds, setHintIds] = useState<Set<string>>(new Set());
  const [inventoryView, setInventoryView] = useState<InventoryView>("useful");
  const [inventoryQuery, setInventoryQuery] = useState("");
  const [lastMessage, setLastMessage] = useState<string | null>(null);
  const [difficulty, setDifficulty] = useState<Difficulty>("usor");
  const [category, setCategory] = useState<string | null>(null);
  const [isRecord, setIsRecord] = useState(false);
  const [isPuzzleRecord, setIsPuzzleRecord] = useState(false);
  const inventoryButtons = useRef(new Map<string, HTMLButtonElement>());
  const active = useActiveGame("alchimie");
  const [actionSync, setActionSync] = useState<ActionSync | null>(null);
  const actionOwner = useMemo(() => createGameActionOwner(active), [active]);
  useEffect(() => () => actionOwner.invalidate(), [actionOwner]);
  const actionsLocked = creating || busy || loading || actionSync !== null;
  const recordOnce = useRecordScore("alchimie");

  const best = useMemo(() => bestScore(GAME_KEY), []);

  const applyAuthoritativeState = useCallback((fresh: AlchimieState) => {
    setState(fresh);
    setSelected(fresh.earned_hint?.hint?.map((item) => item.id) ?? []);
    setEmptyPairKey(null);
    setEmptyRecoveryActive(false);
    setFreshIds(new Set());
    setHintIds(new Set(fresh.earned_hint?.hint?.map((item) => item.id) ?? []));
    setInventoryView("useful");
    setInventoryQuery("");
    setLastMessage(null);
  }, []);

  const applyResumedGame = useCallback(
    (s: AlchimieState, { terminal }: { terminal: boolean }) => {
      actionOwner.invalidate();
      setActionSync(null);
      setBusy(false);
      setStartFailed(false);
      applyAuthoritativeState(s);
      setDifficulty(s.difficulty);
      setCategory(s.board_category ?? null);
      setIsRecord(false);
      setIsPuzzleRecord(false);
      if (!terminal) onToast("Joc reluat.", "info");
    },
    [actionOwner, applyAuthoritativeState, onToast],
  );

  const { recovery: resumeRecovery, retryResume, cancelResume, dismissRecovery } = useSavedGameResume({
    active,
    load: alchimieApi.get,
    isTerminal: isTerminalResume,
    setPending: setLoading,
    onResume: applyResumedGame,
  });

  const exitSafely = useCallback(() => {
    if (startInFlight.current) return;
    actionOwner.invalidate();
    onExit();
  }, [actionOwner, onExit]);

  const start = useCallback(
    async (opts: CreateOpts = {}) => {
      if (startInFlight.current) return;
      startInFlight.current = true;
      actionOwner.invalidate();
      cancelResume();
      setStartFailed(false);
      setCreating(true);
      try {
        const s = await alchimieApi.create(opts);
        setState(s);
        setActionSync(null);
        setBusy(false);
        active.remember(s.game_id);
        dismissRecovery();
        setSelected([]);
        setEmptyPairKey(null);
        setEmptyRecoveryActive(false);
        setFreshIds(new Set());
        setHintIds(new Set());
        setInventoryView("useful");
        setInventoryQuery("");
        setLastMessage(null);
        setIsRecord(false);
        setIsPuzzleRecord(false);
      } catch {
        setStartFailed(true);
      } finally {
        startInFlight.current = false;
        setCreating(false);
      }
    },
    [active, actionOwner, cancelResume, dismissRecovery],
  );

  const won = state?.won ?? false;
  const selectedPairKey = pairKey(selected);
  const isEmptyRetry =
    selectedPairKey !== null && selectedPairKey === emptyPairKey;

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
    const movesLabel = state.moves === 1 ? "combinație" : "combinații";
    const detail = state.daily
      ? `Zilnic ${state.daily} · ${state.moves} ${movesLabel}`
      : `${DIFFICULTY_LABEL[state.difficulty]} · ${state.moves} ${movesLabel}`;
    let current = true;
    void recordOnce(state.game_id, state.score, detail, {
      puzzleKey,
      difficulty: state.difficulty,
      daily: state.daily,
      category: state.board_category,
    }).then((outcome) => {
      active.forgetIfCurrent(state.game_id);
      if (!current || !outcome) return;
      const { isBest, isPuzzleBest } = outcome;
      setIsPuzzleRecord(isPuzzleBest);
      if (isBest) {
        setIsRecord(true);
        sound.playRecord();
      } else if (isPuzzleBest) {
        sound.playRecord();
      }
    });
    return () => {
      current = false;
    };
  }, [state, puzzleKey, recordOnce, active]);

  const toggle = useCallback(
    (id: string) => {
      if (startInFlight.current || actionsLocked || won || actionOwner.hasPending()) return;
      sound.playSelect();
      if (emptyRecoveryActive) {
        const nextSelectionCount = selected.includes(id)
          ? selected.length - 1
          : Math.min(selected.length + 1, 2);
        setLastMessage(
          nextSelectionCount === 0
            ? "Alambicul este gol. Alege două concepte."
            : nextSelectionCount === 1
              ? "Un concept este ales. Alege încă unul."
              : "Perechea nouă este gata. Apasă Combină.",
        );
      }
      setEmptyPairKey(null);
      setSelected((prev) => {
        if (prev.includes(id)) return prev.filter((x) => x !== id);
        if (prev.length >= 2) return [prev[1], id];
        return [...prev, id];
      });
    },
    [actionsLocked, actionOwner, won, emptyRecoveryActive, selected],
  );

  const clearSelection = useCallback(() => {
    if (startInFlight.current || actionsLocked || actionOwner.hasPending()) return;
    if (emptyRecoveryActive) {
      setLastMessage("Alambicul este gol. Alege două concepte.");
    }
    setSelected([]);
    setEmptyPairKey(null);
    setHintIds(new Set());
  }, [actionsLocked, actionOwner, emptyRecoveryActive]);

  const removeFromBench = useCallback(
    (id: string) => {
      if (startInFlight.current) return;
      toggle(id);
      requestAnimationFrame(() => inventoryButtons.current.get(id)?.focus());
    },
    [toggle],
  );

  const beginAction = useCallback((previous: AlchimieState) => {
    if (startInFlight.current) return null;
    const ticket = actionOwner.begin(previous.game_id);
    if (!ticket) return null;
    if (!actionOwner.owns(ticket)) {
      actionOwner.finish(ticket);
      setActionSync({ gameId: previous.game_id, kind: "changed" });
      return null;
    }
    return ticket;
  }, [actionOwner]);

  const mayAdoptAction = useCallback((ticket: GameActionTicket) => {
    if (!actionOwner.isCurrent(ticket)) return false;
    if (!actionOwner.owns(ticket)) {
      setActionSync({ gameId: ticket.gameId, kind: "changed" });
      return false;
    }
    return true;
  }, [actionOwner]);

  const reconcileAction = useCallback(async (ticket: GameActionTicket) => {
    const outcome = await recoverOwnedGameAction(
      actionOwner, ticket, alchimieApi.get,
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
      setSelected([]);
      onToast("Jocul nu mai este disponibil. Poți începe altul.", "info");
      return;
    }
    if (outcome.kind !== "recovered") {
      setActionSync({ gameId: ticket.gameId, kind: outcome.kind === "changed" ? "changed" : "failed" });
      return;
    }
    setActionSync(null);
    applyAuthoritativeState(outcome.state);
    // GET has current inventory and an earned cue, not the lost combine verdict.
    if (!outcome.state.won) setLastMessage("Joc sincronizat. Poți continua.");
  }, [actionOwner, active, applyAuthoritativeState, mayAdoptAction, onToast]);

  const retryActionSync = useCallback(async () => {
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
      await reconcileAction(ticket);
    } finally {
      if (actionOwner.finish(ticket)) setBusy(false);
    }
  }, [state, busy, actionSync, actionOwner, beginAction, reconcileAction, retryResume]);

  const doCombine = useCallback(async () => {
    if (
      !state ||
      startInFlight.current ||
      selected.length !== 2 ||
      actionsLocked ||
      isEmptyRetry
    ) {
      return;
    }
    const ticket = beginAction(state);
    if (!ticket) return;
    setBusy(true);
    const [a, b] = selected;
    try {
      const res = await alchimieApi.combine(state.game_id, a, b);
      if (!mayAdoptAction(ticket)) return;
      if (res.game_id !== ticket.gameId) {
        await reconcileAction(ticket);
        return;
      }
      setState(res);
      const recoverableEmpty = res.discovered.length === 0 && !res.won;
      if (recoverableEmpty) {
        setSelected([a, b]);
        setEmptyPairKey(pairKey([a, b]));
        setEmptyRecoveryActive(true);
      } else {
        setSelected([]);
        setEmptyPairKey(null);
        setEmptyRecoveryActive(false);
      }
      setHintIds(new Set());
      let feedback = res.message;
      if (recoverableEmpty && !res.already_tried) {
        feedback += " Perechea rămâne în alambic — schimbă un ingredient.";
      }
      if (recoverableEmpty && res.hint_available) {
        feedback += " Apasă „Indiciu” dacă te-ai blocat.";
      }
      setLastMessage(feedback);
      if (res.discovered.length > 0) {
        setFreshIds(new Set(res.discovered.map((d: Concept) => d.id)));
        setInventoryView("recent");
        setInventoryQuery("");
        if (!res.won) sound.playHop();
        // win sound handled by the won effect
      } else {
        setFreshIds(new Set());
        sound.playUndo();
      }
    } catch {
      await reconcileAction(ticket);
    } finally {
      if (actionOwner.finish(ticket)) setBusy(false);
    }
  }, [state, selected, actionsLocked, isEmptyRetry, beginAction, mayAdoptAction,
    reconcileAction, actionOwner]);

  const doReset = useCallback(async () => {
    if (startInFlight.current || !state || actionsLocked) return;
    const ticket = beginAction(state);
    if (!ticket) return;
    setBusy(true);
    try {
      const fresh = await alchimieApi.reset(state.game_id);
      if (!mayAdoptAction(ticket)) return;
      if (fresh.game_id !== ticket.gameId) {
        await reconcileAction(ticket);
        return;
      }
      applyAuthoritativeState(fresh);
      sound.playUndo();
    } catch {
      await reconcileAction(ticket);
    } finally {
      if (actionOwner.finish(ticket)) setBusy(false);
    }
  }, [state, actionsLocked, beginAction, mayAdoptAction, applyAuthoritativeState,
    reconcileAction, actionOwner]);

  const newGame = useCallback(() => {
    if (startInFlight.current) return;
    if (state && !state.won && !busy && !actionSync && !actionOwner.hasPending()) {
      active.forgetIfCurrent(state.game_id);
    }
    actionOwner.invalidate();
    setActionSync(null);
    setBusy(false);
    setSelected([]);
    setEmptyPairKey(null);
    setEmptyRecoveryActive(false);
    setInventoryView("useful");
    setInventoryQuery("");
    setState(null);
  }, [active, state, busy, actionSync, actionOwner]);

  // Ask for a gentle nudge: the server points at a useful pair (it costs some score).
  const doHint = useCallback(async () => {
    if (startInFlight.current || !state || actionsLocked || won || !state.hint_available) return;
    const ticket = beginAction(state);
    if (!ticket) return;
    setBusy(true);
    try {
      const fresh = await alchimieApi.hint(state.game_id);
      if (!mayAdoptAction(ticket)) return;
      if (fresh.game_id !== ticket.gameId) {
        await reconcileAction(ticket);
        return;
      }
      applyAuthoritativeState(fresh);
      // Defensive no-cue response remains visible, without pretending it was earned.
      if (!fresh.earned_hint) setLastMessage(fresh.message);
      sound.playSelect();
    } catch {
      await reconcileAction(ticket);
    } finally {
      if (actionOwner.finish(ticket)) setBusy(false);
    }
  }, [state, actionsLocked, won, beginAction, mayAdoptAction, applyAuthoritativeState,
    reconcileAction, actionOwner]);

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
  const inventoryById = useMemo(
    () => new Map(inventory.map((item) => [item.id, item])),
    [inventory],
  );
  const inventoryCounts = useMemo(
    () => ({
      recent: inventory.filter((item) => item.recent && !item.depleted).length,
      useful: inventory.filter((item) => item.useful && !item.depleted).length,
      all: inventory.length,
    }),
    [inventory],
  );
  const normalizedInventoryQuery = useMemo(
    () => normalizeInventorySearch(inventoryQuery),
    [inventoryQuery],
  );
  const visibleInventory = useMemo(
    () =>
      inventory.filter((item) => {
        if (normalizedInventoryQuery) {
          return normalizeInventorySearch(item.label).includes(normalizedInventoryQuery);
        }
        if (inventoryView === "all") return true;
        if (inventoryView === "recent") return item.recent && !item.depleted;
        return item.useful && !item.depleted;
      }),
    [inventory, inventoryView, normalizedInventoryQuery],
  );
  const selectedItems = useMemo(
    () =>
      selected
        .map((id) => inventory.find((i) => i.id === id))
        .filter(Boolean) as InventoryItem[],
    [selected, inventory],
  );
  const reactionLog = useMemo(() => buildReactionLog(inventory), [inventory]);
  const winningTargetId = state?.target.id;
  const winningReaction =
    won && winningTargetId
      ? (reactionLog.find((reaction) =>
          reaction.results.some((item) => item.id === winningTargetId),
        ) ?? null)
      : null;

  // Keyboard: Enter combines a ready pair, Escape clears the bench. Ignored while
  // typing in an input (none here) or once the game is finished.
  useEffect(() => {
    if (!state || won) return;
    const onKey = (e: KeyboardEvent) => {
      if (startInFlight.current) return;
      const target = e.target instanceof Element ? e.target : null;
      if (
        e.defaultPrevented ||
        (e.key === "Enter" &&
          target?.closest(
            'button, a, input, textarea, select, summary, [role="button"], [contenteditable="true"]',
          ))
      ) {
        return;
      }
      if (
        e.key === "Enter" &&
        selected.length === 2 &&
        !actionsLocked &&
        !isEmptyRetry
      ) {
        e.preventDefault();
        void doCombine();
      } else if (e.key === "Escape" && selected.length > 0) {
        e.preventDefault();
        clearSelection();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [state, won, selected, actionsLocked, isEmptyRetry, doCombine, clearSelection]);

  if (loading && !state) {
    return (
      <div className="screen-pad fill center">
        <Spinner size="lg" label="Se încarcă…" />
      </div>
    );
  }

  // ---- Intro: difficulty picker + daily challenge + personal best. ----
  if (!state) {
    return (
      <div className="screen-pad fill" aria-busy={creating}>
        {creating && <span className="visually-hidden" role="status">Se pregătește jocul…</span>}
        <div inert={creating} className="container col game-container" style={{ gap: 18 }}>
          <GameShell onExit={exitSafely} accent={DEF.accent} busy={creating} />

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
            best={best}
            description={
              <p style={{ margin: 0 }}>
                Combină două concepte și ajungi la ținta afișată.
              </p>
            }
            steps={[
              { icon: "👆", label: "Alege două" },
              { icon: "⚗️", label: "Combină" },
              { icon: "✨", label: "Descoperă" },
            ]}
            startLabel="Joacă →"
            onStart={() => void start({ difficulty, category: category ?? undefined })}
            onDaily={() => void start({ difficulty, daily: todayLocal() })}
            dailyLabel="Provocarea zilei"
            starting={creating || loading}
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
              difficulty={difficulty}
              value={category}
              onChange={(key) => {
                sound.playSelect();
                setCategory(key);
              }}
              onInvalid={() => setCategory(null)}
              accent={DEF.accent}
            />
          </GameIntro>
        </div>
      </div>
    );
  }

  return (
    <div className="screen-pad fill" style={{ overflowY: "auto" }} aria-busy={creating}>
      {creating && <span className="visually-hidden" role="status">Se pregătește jocul…</span>}
      <div inert={creating} className="container col game-container" style={{ gap: 18, paddingBottom: 32 }}>
        {/* Header */}
        <GameShell onExit={exitSafely} accent={DEF.accent} title={DEF.title} helpGame={GAME_KEY} busy={creating}>
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

        {!won && (
          <NextMove
            icon={isEmptyRetry ? "↔" : selected.length === 2 ? "✨" : "👆"}
            title={
              isEmptyRetry
                ? "Schimbă un ingredient"
                : selected.length === 0
                ? "Alege două concepte"
                : selected.length === 1
                  ? "Mai alege unul"
                  : "Pereche gata"
            }
            detail={
              isEmptyRetry
                ? "Perechea aceasta nu a descoperit nimic."
                : selected.length === 1
                ? `${selectedItems[0]?.label ?? "Primul concept"} este ales.`
                : selected.length === 2
                  ? "Apasă Combină."
                  : "Pornește din inventar."
            }
            progress={isEmptyRetry ? "schimbă 1" : `${selected.length}/2`}
            accent={DEF.accent}
            ready={selected.length === 2 && !isEmptyRetry}
            announce={false}
          />
        )}

        {/* Combine bench */}
        {!won && (
          <div
            className="card row spread wrap alchemy-bench"
            style={{ padding: 14, gap: 12, alignItems: "center" }}
          >
            <div
              className="row wrap"
              style={{ gap: 8, alignItems: "center", minHeight: 38 }}
            >
              <Slot
                item={selectedItems[0]}
                onRemove={removeFromBench}
                disabled={actionsLocked}
              />
              <span
                className="faint"
                style={{ fontSize: "1.4rem" }}
                aria-hidden
              >
                +
              </span>
              <Slot
                item={selectedItems[1]}
                onRemove={removeFromBench}
                disabled={actionsLocked}
              />
            </div>
            <div className="row wrap" style={{ gap: 8 }}>
              {selected.length > 0 && (
                <Button
                  type="button"
                  variant="secondary"
                  disabled={actionsLocked}
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
                  disabled={actionsLocked}
                  onClick={() => void doHint()}
                  title={
                    state.hint_stage === "output"
                      ? "Îți arată un rezultat apropiat"
                      : "Îți arată o pereche utilă"
                  }
                  style={{ borderColor: GOLD, color: GOLD }}
                >
                  💡 Indiciu
                </Button>
              )}
              <Button
                type="button"
                disabled={actionsLocked || selected.length !== 2 || isEmptyRetry}
                onClick={doCombine}
                title={
                  isEmptyRetry
                    ? "Schimbă un ingredient înainte de o nouă combinare"
                    : "Combină cele două concepte (Enter)"
                }
                aria-label="Combină cele două concepte selectate"
                style={{ borderColor: DEF.accent }}
              >
                {busy ? "…" : "⚗ Combină"}
              </Button>
            </div>
          </div>
        )}

        {!won && actionSync ? (
          <div className="card col alchemy-sync-recovery" role="alert" style={{ gap: 8, padding: 12 }}>
            <strong>{actionSync.kind === "changed" ? "Jocul salvat s-a schimbat." : "Verificarea jocului nu a reușit."}</strong>
            <span>{actionSync.kind === "changed"
              ? "Încarcă jocul curent pentru a continua."
              : "Acțiunea poate fi deja salvată. Verifică jocul înainte de o nouă combinație, un indiciu sau o reluare."}</span>
            <Button type="button" onClick={() => void retryActionSync()} disabled={busy}>
              {busy ? "Se verifică…" : actionSync.kind === "changed" ? "Încarcă jocul curent" : "Verifică jocul"}
            </Button>
          </div>
        ) : null}

        {!won && state.earned_hint ? (
          <div className="card alchemy-earned-hint" role="status" style={{ padding: 12, borderColor: GOLD }}>
            {state.earned_hint.message}
          </div>
        ) : null}

        {/* Last combine feedback */}
        <AnimatePresence mode="wait">
          {lastMessage && !won && (
            <m.p
              key={lastMessage + state.moves}
              className="muted center"
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              style={{ margin: 0, fontSize: "0.92rem" }}
              role="status"
              aria-live="polite"
              aria-atomic="true"
            >
              {lastMessage}
            </m.p>
          )}
        </AnimatePresence>

        {/* Server-authored lineage: latest stays visible, older reactions opt in. */}
        {!won && reactionLog.length > 0 && (
          <section
            className="card col"
            aria-labelledby="alchemy-reaction-log-title"
            style={{ gap: 10, padding: 14 }}
          >
            <div className="row spread wrap" style={{ gap: 8, alignItems: "center" }}>
              <span
                id="alchemy-reaction-log-title"
                className="faint"
                style={{ letterSpacing: "0.06em", fontSize: "0.72rem" }}
              >
                ULTIMA DESCOPERIRE
              </span>
              <span className="muted" style={{ fontSize: "0.78rem" }}>
                {reactionLog.length === 1
                  ? "1 reacție păstrată"
                  : reactionLog.length + " reacții păstrate"}
              </span>
            </div>

            <ReactionRow
              reaction={reactionLog[0]}
              selected={selected}
              freshIds={freshIds}
              inventoryById={inventoryById}
              busy={actionsLocked}
              onSelect={toggle}
            />

            {reactionLog.length > 1 && (
              <details className="alchemy-reaction-log">
                <summary
                  className="chip alchemy-reaction-log-toggle"
                  style={{
                    cursor: "pointer",
                    minHeight: 44,
                    width: "fit-content",
                    maxWidth: "100%",
                  }}
                >
                  Vezi jurnalul ({reactionLog.length})
                </summary>
                <div className="col" style={{ gap: 8, marginTop: 10 }}>
                  {reactionLog.slice(1).map((reaction) => (
                    <ReactionRow
                      key={
                        reaction.ingredientKey +
                        ":" +
                        reaction.results.map((item) => item.id).join(",")
                      }
                      reaction={reaction}
                      selected={selected}
                      freshIds={freshIds}
                      inventoryById={inventoryById}
                      busy={actionsLocked}
                      onSelect={toggle}
                    />
                  ))}
                </div>
              </details>
            )}
          </section>
        )}

        {/* Inventory */}
        <section className="col" style={{ gap: 10 }} aria-label="Inventar">
          <div className="row spread wrap" style={{ gap: 8, alignItems: "center" }}>
            <span
              className="faint"
              style={{ letterSpacing: "0.06em", fontSize: "0.72rem" }}
            >
              INVENTAR · {state.inventory_summary.active} ÎN JOC
            </span>
            <span className="row wrap" style={{ gap: 10 }}>
              <span className="muted" style={{ fontSize: "0.76rem" }}>
                <span aria-hidden="true">●</span> pereche gata
              </span>
              {state.inventory_summary.depleted > 0 && (
                <span className="muted" style={{ fontSize: "0.76rem" }}>
                  {state.inventory_summary.depleted} puse deoparte
                </span>
              )}
            </span>
          </div>
          <div
            className="alchemy-inventory-tabs"
            role="group"
            aria-label="Filtrează inventarul"
          >
            {(["recent", "useful", "all"] as InventoryView[]).map((view) => (
              <button
                key={view}
                type="button"
                aria-pressed={inventoryView === view}
                className="chip alchemy-inventory-tab"
                onClick={() => {
                  sound.playSelect();
                  setInventoryView(view);
                }}
                style={{
                  borderColor: inventoryView === view ? DEF.accent : undefined,
                  color: inventoryView === view ? "var(--text)" : undefined,
                }}
              >
                {INVENTORY_VIEW_LABEL[view]} {inventoryCounts[view]}
              </button>
            ))}
          </div>
          <input
            type="search"
            className="field alchemy-inventory-search"
            value={inventoryQuery}
            onChange={(event) => setInventoryQuery(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Escape" && inventoryQuery) {
                event.preventDefault();
                event.stopPropagation();
                setInventoryQuery("");
              }
            }}
            placeholder="Caută în toate…"
            aria-label="Caută în toate conceptele descoperite"
            autoComplete="off"
            spellCheck={false}
          />
          <div className="alchemy-inventory-grid">
            <AnimatePresence initial={false}>
              {visibleInventory.map((item) => {
                const isSel = selected.includes(item.id);
                const isFresh = freshIds.has(item.id);
                const isHint = hintIds.has(item.id);
                const isCrafted = item.parents !== null;
                const title = item.depleted
                  ? "Nu mai produce elemente noi"
                  : item.ready
                    ? `${parentsOf(item) ?? "Concept de start"} · Pereche utilă gata`
                    : (parentsOf(item) ?? "Concept de start");
                const accessibleLabel = item.depleted
                  ? `${item.label}, pus deoparte`
                  : item.ready
                    ? `${item.label}, gata pentru o combinație utilă`
                    : item.label;
                return (
                  <m.button
                    key={item.id}
                    ref={(node) => {
                      if (node) inventoryButtons.current.set(item.id, node);
                      else inventoryButtons.current.delete(item.id);
                    }}
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
                    disabled={actionsLocked || won || item.depleted}
                    aria-pressed={isSel}
                    aria-label={accessibleLabel}
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
                      opacity: item.depleted ? 0.5 : 1,
                      boxShadow:
                        isFresh || isHint
                          ? `0 0 16px -4px ${GOLD}`
                          : item.ready
                            ? `0 0 12px -8px ${DEF.accent}`
                            : undefined,
                    }}
                  >
                    {item.ready && !item.depleted ? (
                      <span aria-hidden="true">● </span>
                    ) : isCrafted ? (
                      <span aria-hidden="true">✦ </span>
                    ) : null}
                    {item.label}
                  </m.button>
                );
              })}
            </AnimatePresence>
            {normalizedInventoryQuery && visibleInventory.length === 0 && (
              <p className="faint center" style={{ gridColumn: "1 / -1", margin: 8 }}>
                Niciun concept găsit.
              </p>
            )}
          </div>
        </section>

        {/* Footer actions stay in-play only; ResultCard owns the terminal actions. */}
        {!won && (
          <>
            <StartFailureNotice failed={startFailed} reserveSpace />
            <div className="row center wrap" style={{ gap: 12, marginTop: 8 }}>
            <Button
              type="button"
              variant="secondary"
              disabled={actionsLocked}
              onClick={doReset}
            >
              ↻ Reia același joc
            </Button>
            <Button
              type="button"
              variant="secondary"
              className="alchimie-other-board"
              disabled={creating || busy}
              onClick={() =>
                void start({
                  difficulty: state.difficulty,
                  category: state.board_category ?? undefined,
                })
              }
            >
              ⚗ Alt joc
            </Button>
            <Button
              type="button"
              variant="secondary"
              disabled={creating || busy}
              onClick={newGame}
            >
              ⚙ Schimbă opțiunile
            </Button>
            </div>
          </>
        )}

        {/* Win banner */}
        <AnimatePresence>
          {won && (
            <ResultCard
              startFailed={startFailed}
              actionsBusy={creating}
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
                  category: state.board_category ?? undefined,
                })
              }
              onOptions={newGame}
              onExit={exitSafely}
            >
              <>
                <strong style={{ color: "var(--text)" }}>{state.target.label}</strong> în{" "}
                {state.moves} {state.moves === 1 ? "combinație" : "combinații"} ·{" "}
                {state.discovered_count} concepte descoperite.
                {winningReaction && (
                  <span style={{ display: "block", marginTop: 8 }}>
                    <span
                      className="faint"
                      style={{ display: "block", fontSize: "0.72rem" }}
                    >
                      CUM AI FĂURIT-O
                    </span>
                    {winningReaction.parents[0].label} +{" "}
                    {winningReaction.parents[1].label} →{" "}
                    <strong style={{ color: "var(--text)" }}>
                      {winningReaction.results.map((item) => item.label).join(", ")}
                    </strong>
                  </span>
                )}
                {winningReaction?.results.map((item) => (
                  <EarnedLinks key={item.id} item={item} />
                ))}
              </>
            </ResultCard>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

function ReactionRow({
  reaction,
  selected,
  freshIds,
  inventoryById,
  busy,
  onSelect,
}: {
  reaction: Reaction;
  selected: string[];
  freshIds: Set<string>;
  inventoryById: ReadonlyMap<string, InventoryItem>;
  busy: boolean;
  onSelect: (id: string) => void;
}) {
  return (
    <div
      className="row wrap"
      style={{
        gap: 8,
        alignItems: "center",
        overflowWrap: "anywhere",
      }}
    >
      <span className="muted" style={{ lineHeight: 1.45 }}>
        {reaction.parents[0].label} + {reaction.parents[1].label} →
      </span>
      <span className="row wrap" style={{ gap: 6 }}>
        {reaction.results.map((item) => {
          const isSelected = selected.includes(item.id);
          const isFresh = freshIds.has(item.id);
          const currentItem = inventoryById.get(item.id);
          const depleted = currentItem?.depleted ?? true;
          return (
            <button
              key={item.id}
              type="button"
              className="chip alchemy-reaction-result"
              disabled={busy || depleted}
              aria-pressed={isSelected}
              aria-label={depleted ? `${item.label}, pus deoparte` : `Alege ${item.label}`}
              title={depleted ? "Pus deoparte" : "Pune în alambic"}
              onClick={() => onSelect(item.id)}
              style={{
                cursor: busy || depleted ? "default" : "pointer",
                minHeight: 44,
                maxWidth: "100%",
                overflowWrap: "anywhere",
                borderColor: isSelected ? DEF.accent : isFresh ? GOLD : undefined,
                color: isSelected || isFresh ? "var(--text)" : undefined,
                fontWeight: 700,
                opacity: depleted ? 0.5 : 1,
              }}
            >
              {isFresh ? "NOU · " : ""}
              {item.label}
            </button>
          );
        })}
      </span>
      {reaction.results.map((item) => <EarnedLinks key={item.id} item={item} />)}
    </div>
  );
}

function EarnedLinks({ item }: { item: InventoryItem }) {
  if (!item.links?.length) return null;
  return (
    <div className="alchemy-earned-links">
      <strong>Legături descoperite: {item.label}</strong>
      <ul>
        {item.links.map((link, index) => (
          <li key={`${link.source.id}:${link.target.id}:${index}`}>
            {link.source.label} — {link.label} → {link.target.label}
          </li>
        ))}
      </ul>
    </div>
  );
}

function Slot({
  item,
  onRemove,
  disabled,
}: {
  item: InventoryItem | undefined;
  onRemove: (id: string) => void;
  disabled: boolean;
}) {
  if (!item) {
    return (
      <span
        className="chip faint alchemy-slot"
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
    <button
      type="button"
      className="chip alchemy-slot"
      style={{ borderColor: DEF.accent, color: "var(--text)", minHeight: 44 }}
      onClick={() => onRemove(item.id)}
      disabled={disabled}
      title={`Scoate ${item.label} din alambic`}
      aria-label={`Scoate ${item.label} din alambic`}
    >
      {item.parents ? <span aria-hidden>✦</span> : null}
      <span className="alchemy-slot-label">{item.label}</span>
      <span aria-hidden>×</span>
    </button>
  );
}
