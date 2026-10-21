// Alchimie — Infinite-Craft over the Romanian KG. Text-only: the inventory is a grid of
// clickable concepts: a first tap selects, a second tap crafts their shared neighbour(s).
// Server-authoritative: we render whatever the backend returns and never know the target
// id until the server reveals it on a win.

import type { ComponentProps } from "preact";
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "preact/hooks";
import { Presence, useIsPresent } from "@roedu/ui/motion";
import { useElementMotion } from "../hooks/useElementMotion";
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
import { ALCHIMIE_HELP } from "../gameHelp/alchimie.mjs";
import { GameHelp } from "../components/GameHelp";
import { ResultCard } from "../components/ResultCard";
import { GameIntro } from "../components/GameIntro";
import { StartFailureNotice } from "../components/StartFailureNotice";
import { Hud, StatBadge } from "../components/Hud";
import { DifficultyPicker } from "../components/DifficultyPicker";
import { useActiveGame } from "../hooks/useActiveGame";
import { useRecordScore } from "../hooks/useRecordScore";
import { useSavedGameResume } from "../hooks/useSavedGameResume";
import { gameByKey } from "../games";
import { sound } from "../sound";
import { bestScore } from "../scores/read";
import { categoryLabel } from "../categories";
import { CategoryPicker } from "../components/CategoryPicker";
import { AlchimieModes } from "../components/AlchimieModes";
import { buildSharePayload, copyResult, formatDayKey, stableKey, todayLocal } from "../share";

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

export default function AlchimieChallenge({
  onExit,
  onToast,
}: {
  onExit: () => void;
  onToast: (m: string, k?: ToastKind) => void;
}) {
  const active = useActiveGame("alchimie");
  const isPresent = useIsPresent();
  const liveRef = useRef(true);
  const lifetimeRef = useRef(0);
  const [state, setState] = useState<AlchimieState | null>(null);
  const [startFailed, setStartFailed] = useState(false);
  const startInFlightRef = useRef(false);
  const [loading, setLoading] = useState(() => active.peek() !== null);
  const [creating, setCreating] = useState(false);
  const [busy, setBusy] = useState(false);
  const [selected, setSelected] = useState<string[]>([]);
  const [emptyPairKey, setEmptyPairKey] = useState<string | null>(null);
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
  const inventoryButtonsRef = useRef(new Map<string, HTMLButtonElement>());
  const inventoryPanelRef = useRef<HTMLElement>(null);
  const pendingCraftFocusRef = useRef<{ gameId: string; origin: HTMLElement; targetId: string | null } | null>(null);
  const dragSourceRef = useRef<{ id: string; gameId: string } | null>(null);
  const [dragOverId, setDragOverId] = useState<string | null>(null);
  const [toolsOpen, setToolsOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [actionSync, setActionSync] = useState<ActionSync | null>(null);
  const actionOwner = useMemo(() => createGameActionOwner(active), [active]);
  useLayoutEffect(() => {
    liveRef.current = isPresent;
    if (!isPresent) { actionOwner.invalidate(); pendingCraftFocusRef.current = null; dragSourceRef.current = null; }
    return () => { liveRef.current = false; lifetimeRef.current += 1; actionOwner.invalidate(); };
  }, [actionOwner, isPresent]);
  const actionsLocked = !isPresent || creating || busy || loading || actionSync !== null;
  const recordOnce = useRecordScore("alchimie");

  const best = useMemo(() => bestScore(GAME_KEY), []);

  const applyAuthoritativeState = useCallback((fresh: AlchimieState) => {
    pendingCraftFocusRef.current = null;
    setState(fresh);
    setSelected(fresh.earned_hint?.hint?.slice(0, 1).map((item) => item.id) ?? []);
    setEmptyPairKey(null);
    setFreshIds(new Set());
    setHintIds(new Set(fresh.earned_hint?.hint?.map((item) => item.id) ?? []));
    setInventoryView("useful");
    setInventoryQuery("");
    setLastMessage(null);
  }, []);

  const applyResumedGame = useCallback(
    (s: AlchimieState, { terminal, bypassed }: { terminal: boolean; bypassed: boolean }) => {
      if (!liveRef.current) return;
      actionOwner.invalidate();
      setActionSync(null);
      setBusy(false);
      setStartFailed(false);
      applyAuthoritativeState(s);
      setDifficulty(s.difficulty);
      setCategory(s.board_category ?? null);
      setIsRecord(false);
      setIsPuzzleRecord(false);
      // The daily-bypass notice already says the round was resumed.
      if (!terminal && !bypassed) onToast("Joc reluat.", "info");
    },
    [actionOwner, applyAuthoritativeState, onToast],
  );

  const { recovery: resumeRecovery, retryResume, cancelResume, dismissRecovery } = useSavedGameResume({
    active,
    load: alchimieApi.get,
    isTerminal: isTerminalResume,
    setPending: setLoading,
    onResume: applyResumedGame,
    onReentry: () => {
      startInFlightRef.current = false;
      setBusy(false); setCreating(false); setStartFailed(false);
      if (!active.peek() && state) {
        // A locally owned round may have no persistent storage. Keep its id and
        // existing read-only recovery path instead of silently discarding it.
        if (!state.won) setActionSync({ gameId: state.game_id, kind: "failed" });
      } else { setState(null); setActionSync(null); }
    },
    onDailyBypassed: () => onToast("Ai continuat jocul liber început. Provocarea zilei te așteaptă după ce îl termini.", "info"),
  });

  const exitSafely = useCallback(() => {
    if (startInFlightRef.current) return;
    actionOwner.invalidate();
    liveRef.current = false;
    cancelResume();
    onExit();
  }, [actionOwner, cancelResume, onExit]);

  const start = useCallback(
    async (opts: CreateOpts = {}) => {
      if (!liveRef.current || startInFlightRef.current) return;
      startInFlightRef.current = true;
      const epoch = lifetimeRef.current;
      actionOwner.invalidate();
      cancelResume();
      setStartFailed(false);
      setCreating(true);
      try {
        const s = await alchimieApi.create(opts);
        if (!liveRef.current || epoch !== lifetimeRef.current) return;
        setState(s);
        setToolsOpen(false);
        setMenuOpen(false);
        dragSourceRef.current = null;
        setDragOverId(null);
        setActionSync(null);
        setBusy(false);
        active.remember(s.game_id);
        dismissRecovery();
        setSelected([]);
        setEmptyPairKey(null);
        setFreshIds(new Set());
        setHintIds(new Set());
        setInventoryView("useful");
        setInventoryQuery("");
        setLastMessage(null);
        setIsRecord(false);
        setIsPuzzleRecord(false);
      } catch {
        if (liveRef.current && epoch === lifetimeRef.current) setStartFailed(true);
      } finally {
        if (epoch === lifetimeRef.current) {
          startInFlightRef.current = false;
          if (liveRef.current) setCreating(false);
        }
      }
    },
    [active, actionOwner, cancelResume, dismissRecovery],
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
      "productive-crafts-v92",
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
    if (liveRef.current && won) sound.playWin();
  }, [won]);

  // Record the score exactly once when a game is won.
  useEffect(() => {
    if (!liveRef.current || !state || !state.won || state.score === undefined) return;
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
      if (!current || !liveRef.current || !outcome) return;
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
  }, [state, puzzleKey, recordOnce, active, isPresent]);

  const beginAction = useCallback((previous: AlchimieState) => {
    if (!liveRef.current || startInFlightRef.current) return null;
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
    if (!liveRef.current || !actionOwner.isCurrent(ticket)) return false;
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
      await reconcileAction(ticket);
    } finally {
      if (actionOwner.finish(ticket)) setBusy(false);
    }
  }, [state, busy, actionSync, actionOwner, beginAction, reconcileAction, retryResume]);

  const doCombine = useCallback(async (pair: readonly string[]) => {
    if (
      !state ||
      startInFlightRef.current ||
      state.won ||
      actionsLocked ||
      pair.length !== 2 ||
      pair[0] === pair[1] ||
      pair.some((id) => !state.inventory.some((item) => item.id === id && !item.depleted))
    ) {
      return;
    }
    if (pairKey(pair) === emptyPairKey) {
      setLastMessage("Ai încercat deja această pereche. Atinge un alt partener.");
      return;
    }
    const ticket = beginAction(state);
    if (!ticket) return;
    const [a, b] = pair;
    const focusOrigin = document.activeElement;
    setBusy(true);
    setSelected([a]);
    setLastMessage(null);
    try {
      const res = await alchimieApi.combine(state.game_id, a, b);
      if (!mayAdoptAction(ticket)) return;
      if (res.game_id !== ticket.gameId) {
        await reconcileAction(ticket);
        return;
      }
      setState(res);
      const recoverableEmpty = res.discovered.length === 0 && !res.won;
      let focusTargetId: string | null = null;
      let carriedLabel: string | null = null;
      if (recoverableEmpty) {
        setSelected([a]);
        setEmptyPairKey(pairKey([a, b]));
        focusTargetId = a;
      } else {
        const usableDiscoveries = res.inventory.filter((item) =>
          item.useful && !item.depleted && res.discovered.some((fresh) => fresh.id === item.id),
        );
        setSelected(!res.won && usableDiscoveries.length === 1 ? [usableDiscoveries[0].id] : []);
        if (!res.won && usableDiscoveries.length === 1) {
          focusTargetId = usableDiscoveries[0].id;
          carriedLabel = usableDiscoveries[0].label;
        }
        setEmptyPairKey(null);
      }
      if (!res.won && focusOrigin instanceof HTMLElement && focusOrigin.matches(".alchemy-word, .alchemy-reaction-result")) {
        pendingCraftFocusRef.current = { gameId: res.game_id, origin: focusOrigin, targetId: focusTargetId };
      }
      setHintIds(new Set());
      let feedback = res.message;
      if (carriedLabel) feedback += ` ${carriedLabel} rămâne ales.`;
      if (recoverableEmpty && !res.already_tried) {
        feedback += " Primul cuvânt rămâne ales. Atinge alt partener.";
      }
      if (recoverableEmpty && res.hint_available) {
        feedback += " Apasă „Indiciu” dacă te-ai blocat.";
      }
      setLastMessage(feedback);
      if (res.discovered.length > 0) {
        setFreshIds(new Set(res.discovered.map((d: Concept) => d.id)));
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
  }, [state, actionsLocked, emptyPairKey, beginAction, mayAdoptAction,
    reconcileAction, actionOwner]);

  const clearSelection = useCallback(() => {
    if (startInFlightRef.current || actionsLocked || actionOwner.hasPending()) return;
    setSelected([]);
    setEmptyPairKey(null);
    setHintIds(new Set());
    setLastMessage(null);
  }, [actionsLocked, actionOwner]);

  const toggle = useCallback((id: string) => {
    if (startInFlightRef.current || actionsLocked || won || actionOwner.hasPending()) return;
    const item = state?.inventory.find((owned) => owned.id === id);
    if (!item || item.depleted) return;
    if (selected[0] === id) {
      clearSelection();
    } else if (selected[0]) {
      void doCombine([selected[0], id]);
    } else {
      sound.playSelect();
      setSelected([id]);
      setEmptyPairKey(null);
      setLastMessage(null);
    }
  }, [state, selected, actionsLocked, won, actionOwner, clearSelection, doCombine]);

  const removeFromBench = useCallback((id: string) => {
    if (startInFlightRef.current || actionsLocked || actionOwner.hasPending()) return;
    clearSelection();
    requestAnimationFrame(() => {
      const button = inventoryButtonsRef.current.get(id);
      if (button && !button.disabled) button.focus();
      else inventoryPanelRef.current?.focus();
    });
  }, [actionsLocked, actionOwner, clearSelection]);

  const doReset = useCallback(async () => {
    if (startInFlightRef.current || !state || actionsLocked) return;
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
    if (startInFlightRef.current) return;
    if (state && !state.won && !busy && !actionSync && !actionOwner.hasPending()) {
      active.forgetIfCurrent(state.game_id);
    }
    actionOwner.invalidate();
    setActionSync(null);
    setBusy(false);
    setSelected([]);
    setEmptyPairKey(null);
    setInventoryView("useful");
    setInventoryQuery("");
    setState(null);
  }, [active, state, busy, actionSync, actionOwner]);

  // Ask for a gentle nudge: the server points at a useful pair (it costs some score).
  const doHint = useCallback(async () => {
    if (startInFlightRef.current || !state || actionsLocked || won || !state.hint_available) return;
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
  useLayoutEffect(() => {
    const pending = pendingCraftFocusRef.current;
    if (!pending || busy || actionsLocked) return;
    pendingCraftFocusRef.current = null;
    if (!liveRef.current || !state || state.game_id !== pending.gameId || won) return;
    const focused = document.activeElement;
    // A removed/depleted word can lose focus. Respect navigation to another control
    // while the request was pending, and leave terminal focus to ResultCard.
    if (focused !== document.body && focused !== pending.origin) return;
    if (focused === pending.origin && pending.origin.isConnected &&
      !(pending.origin instanceof HTMLButtonElement && pending.origin.disabled)) return;
    const target = pending.targetId ? inventoryButtonsRef.current.get(pending.targetId) : null;
    if (target && !target.disabled) target.focus({ preventScroll: true });
    else inventoryPanelRef.current?.focus({ preventScroll: true });
  }, [state, busy, won, actionsLocked]);
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

  // Native button activation handles both taps and keyboard crafting. Escape only cancels.
  useLayoutEffect(() => {
    if (!state || won) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.defaultPrevented || startInFlightRef.current) return;
      if (event.key === "Escape" && selected.length > 0) {
        event.preventDefault();
        clearSelection();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [state, won, selected, clearSelection]);

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
      <div className="screen-pad fill alchemy-screen alchemy-intro alchemy-challenge" aria-busy={creating}>
        {creating && <span className="visually-hidden" role="status">Se pregătește jocul…</span>}
        <div inert={creating} className="container col game-container alchemy-challenge-intro-content">
          <GameShell onExit={exitSafely} accent={DEF.accent} busy={creating} />
          <AlchimieModes mode="challenges" busy={creating || loading} />

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
              <p className="alchemy-intro-description">
                Atinge un cuvânt, apoi altul: se combină imediat. Descoperă cuvinte noi până creezi ținta.
                {" "}Perechile fără rezultat nu scad scorul.
              </p>
            }
            steps={[
              { icon: "👆", label: "Atinge un cuvânt" },
              { icon: "👆", label: "Atinge altul" },
              { icon: "✨", label: "Descoperă automat" },
            ]}
            startLabel="Joacă →"
            onStart={() => void start({ difficulty, category: category ?? undefined })}
            onDaily={() => void start({ difficulty, daily: todayLocal() })}
            dailyLabel="Provocarea zilei"
            starting={!isPresent || creating || loading}
          >
            <details className="alchemy-setup-options">
              <summary>{DIFFICULTY_LABEL[difficulty]} · {category ? categoryLabel(category) : "Toate temele"} · Personalizează</summary>
              <div className="alchemy-setup-content">
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
              </div>
            </details>
          </GameIntro>
        </div>
      </div>
    );
  }

  return (
    <div className="screen-pad fill alchemy-screen alchemy-challenge" aria-busy={creating}>
      {creating && <span className="visually-hidden" role="status">Se pregătește jocul…</span>}
      <div inert={creating} className="container col game-container alchemy-game">
        {/* Header */}
        <GameShell onExit={exitSafely} accent={DEF.accent} title={DEF.title} busy={creating}>
          <Hud>
            <StatBadge label="Combinații" value={state.moves} accent={DEF.accent} />
          </Hud>
        </GameShell>
        <AlchimieModes mode="challenges" busy={creating || busy || loading} />

        <section className={`alchemy-target${won ? " alchemy-target--won" : ""}`} aria-label="Ținta de făurit">
          <span className="alchemy-target-icon" aria-hidden>{won ? "★" : "◎"}</span>
          <div className="alchemy-target-copy">
            <div className="alchemy-target-meta">
              <span className="alchemy-eyebrow">{won ? "ȚINTA FĂURITĂ" : "SCOPUL TĂU · CREEAZĂ"}</span>
              <span className="alchemy-theme">
                {state.board_category && `${categoryLabel(state.board_category)} · `}{DIFFICULTY_LABEL[state.difficulty]}
                {state.daily && ` · ${formatDayKey(state.daily)}`}
              </span>
            </div>
            <h2>{state.target.label}</h2>
            {state.target.description && <p>{state.target.description}</p>}
          </div>
        </section>

        <div className="alchemy-workspace">
          {/* Combine bench */}
          {!won && (
            <div
              className="card alchemy-bench"
              aria-label="Alambic"
            >
              <div className="alchemy-craft-cue" id="alchemy-instructions">
                {selectedItems[0] ? (
                  <>
                    <Slot item={selectedItems[0]} onRemove={removeFromBench} disabled={actionsLocked} />
                    <span className="alchemy-craft-plus" aria-hidden>+</span>
                    <span className="alchemy-craft-prompt">Atinge un alt cuvânt</span>
                  </>
                ) : (
                  <p className="alchemy-craft-prompt">Atinge un cuvânt, apoi altul. Se combină imediat.</p>
                )}
              </div>
              {busy && <span role="status" className="alchemy-working">Se verifică…</span>}
              {/* Last combine feedback */}
              <Presence mode="wait" variant={{ enter: { opacity: [0, 1], transform: ["translateY(4px)", "translateY(0px)"] }, exit: { opacity: [1, 0] } }}>
                {lastMessage && !won && (
                  <p
                    key={lastMessage + state.moves}
                    className={`alchemy-feedback${emptyPairKey ? " alchemy-feedback--empty" : ""}`}
                    role="status"
                    aria-live="polite"
                    aria-atomic="true"
                  >
                    {lastMessage}
                  </p>
                )}
              </Presence>

              {!won && actionSync ? (
                <div className="card col alchemy-sync-recovery" role="alert">
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
                <div className="card alchemy-earned-hint" role="status">
                  {state.earned_hint.message}
                </div>
              ) : null}

              {state.hint_available && (
                <div className="alchemy-assistance">
                  <Button
                    type="button"
                    variant="secondary"
                    className="alchemy-challenge-hint"
                    disabled={actionsLocked}
                    onClick={() => void doHint()}
                    title={
                      state.hint_stage === "output"
                        ? "Îți arată un rezultat apropiat"
                        : "Îți arată o pereche utilă"
                    }
                    aria-describedby="alchemy-hint-cost"
                  >
                    💡 Indiciu
                  </Button>
                  <span id="alchemy-hint-cost">Folosește un indiciu · penalizare de 150 puncte.</span>
                </div>
              )}
            </div>
          )}

          {/* Inventory */}
          <section ref={inventoryPanelRef} tabIndex={-1} className="card col alchemy-inventory-panel" aria-label="Inventar">
            <div className="alchemy-panel-heading">
              <span className="alchemy-step" aria-hidden>Aa</span>
              <h3>Cuvintele tale</h3>
              <span className="alchemy-selection-count">{state.inventory_summary.active} utile</span>
            </div>
            <details className="alchemy-library-tools" open={toolsOpen} onToggle={(event) => setToolsOpen(event.currentTarget.open)}>
              <summary>Caută și filtrează</summary>
              <div className="alchemy-library-content">
                <p className="alchemy-inventory-note">
                  Utile arată cuvintele care mai pot produce descoperiri. În Toate găsești și cuvintele puse deoparte.
                  {state.inventory_summary.depleted > 0 && ` Puse deoparte: ${state.inventory_summary.depleted}.`}
                </p>

                <div
                  className="alchemy-inventory-tabs"
                  role="group"
                  aria-label="Filtrează inventarul"
                >
                  {(["useful", "recent", "all"] as InventoryView[]).map((view) => (
                    <button
                      key={view}
                      type="button"
                      aria-pressed={inventoryView === view}
                      className="chip alchemy-inventory-tab"
                      onClick={() => {
                        sound.playSelect();
                        setInventoryView(view);
                        setInventoryQuery("");
                      }}
                    >
                      {INVENTORY_VIEW_LABEL[view]} {inventoryCounts[view]}
                    </button>
                  ))}
                </div>
                <div className="alchemy-search-row">
                  <input
                    type="search"
                    className="field alchemy-inventory-search"
                    value={inventoryQuery}
                    onInput={(event) => setInventoryQuery(event.currentTarget.value)}
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
                    spellcheck={false}
                  />
                  {inventoryQuery && (
                    <button className="alchemy-clear-search" type="button" onClick={() => setInventoryQuery("")}>
                      Șterge căutarea
                    </button>
                  )}
                </div>
              </div>
            </details>
            <div className="alchemy-inventory-grid">
              <>
                {visibleInventory.map((item) => {
                  const isSel = selected.includes(item.id);
                  const isFresh = freshIds.has(item.id);
                  const isHint = hintIds.has(item.id);
                  const isCrafted = item.parents !== null;
                  const isTried = selected.length === 1 && pairKey([selected[0], item.id]) === emptyPairKey;
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
                    <AlchemyWord
                      key={item.id}
                      buttonRef={(node) => {
                        if (node) inventoryButtonsRef.current.set(item.id, node);
                        else inventoryButtonsRef.current.delete(item.id);
                      }}
                      type="button"
                      fresh={isFresh}
                      pulsing={isHint && !isSel}
                      onClick={() => toggle(item.id)}
                      draggable={!actionsLocked && !won && !item.depleted}
                      onDragStartCapture={(event) => {
                        if (!event.dataTransfer || actionsLocked || won || item.depleted || actionOwner.hasPending()) {
                          event.preventDefault();
                          return;
                        }
                        dragSourceRef.current = { id: item.id, gameId: state.game_id };
                        event.dataTransfer.setData("text/plain", item.id);
                        event.dataTransfer.effectAllowed = "copy";
                      }}
                      onDragOver={(event) => {
                        if (event.dataTransfer && !actionsLocked && !won && !item.depleted && dragSourceRef.current?.gameId === state.game_id && dragSourceRef.current.id !== item.id) {
                          event.preventDefault();
                          event.dataTransfer.dropEffect = "copy";
                          setDragOverId(item.id);
                        }
                      }}
                      onDragLeave={() => setDragOverId(null)}
                      onDragEndCapture={() => { dragSourceRef.current = null; setDragOverId(null); }}
                      onDrop={(event) => {
                        event.preventDefault();
                        const source = dragSourceRef.current;
                        dragSourceRef.current = null;
                        setDragOverId(null);
                        if (event.dataTransfer && source?.gameId === state.game_id && source.id === event.dataTransfer.getData("text/plain")) {
                          void doCombine([source.id, item.id]);
                        }
                      }}
                      disabled={actionsLocked || won || item.depleted}
                      aria-pressed={isSel}
                      aria-label={accessibleLabel}
                      title={title}
                      className={(`chip alchemy-word${isSel ? " alchemy-word--selected" : ""}${isFresh ? " alchemy-word--fresh" : ""}${isHint ? " alchemy-word--hint" : ""}${isTried ? " alchemy-word--tried" : ""}${dragOverId === item.id ? " alchemy-word--drop" : ""}${isCrafted ? " alchemy-word--crafted" : ""}`) + (item.depleted ? " csp-motion-opacity-50" : "")}
                    >
                      <span className="alchemy-word-label">{item.label}</span>
                      {(isSel || isFresh || isTried || item.depleted) && (
                        <span className="alchemy-word-meta" aria-hidden="true">
                          {isSel ? "✓ Ales" : item.depleted ? "Pus deoparte" : isTried ? "Încercat" : "✦ Nou"}
                        </span>
                      )}
                    </AlchemyWord>
                  );
                })}
              </>
              {!normalizedInventoryQuery && visibleInventory.length === 0 && (
                <p className="alchemy-empty-inventory">
                  Niciun cuvânt în acest filtru. <button type="button" onClick={() => setInventoryView("useful")}>Vezi cuvintele utile</button>
                </p>
              )}
              {normalizedInventoryQuery && visibleInventory.length === 0 && (
                <p className="faint center alchemy-empty-search">
                  Niciun concept găsit.
                </p>
              )}
            </div>
          </section>

        </div>

        <GameHelp help={ALCHIMIE_HELP} />
        <details className="alchemy-menu" open={menuOpen} onToggle={(event) => setMenuOpen(event.currentTarget.open)}>
          <summary>Opțiuni de joc</summary>
          <div className="alchemy-menu-content">
            {/* Server-authored lineage is available on request. */}
            {!won && reactionLog.length > 0 && (
              <details className="alchemy-discoveries">
                <summary>Descoperiri</summary>
                <div className="row spread wrap alchemy-reaction-heading">
                  <span
                    id="alchemy-reaction-log-title"
                    className="faint"
                  >
                    ULTIMA DESCOPERIRE
                  </span>
                  <span className="muted alchemy-reaction-count">
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
                    >
                      Vezi jurnalul ({reactionLog.length})
                    </summary>
                    <div className="col alchemy-reaction-history">
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
              </details>
            )}

            {/* Footer actions stay in-play only; ResultCard owns the terminal actions. */}
            {!won && (
              <>
                <div className="row center wrap alchemy-challenge-actions">
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
                    disabled={!isPresent || creating || busy || loading}
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
                    disabled={actionsLocked}
                    onClick={newGame}
                  >
                    ⚙ Schimbă opțiunile
                  </Button>
                </div>
              </>
            )}

          </div>
        </details>
        {!won && <StartFailureNotice failed={startFailed} />}

        {/* Win banner */}
        <Presence>
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
                <strong className="alchemy-result-emphasis">{state.target.label}</strong> în{" "}
                {state.moves} {state.moves === 1 ? "combinație" : "combinații"} ·{" "}
                {state.discovered_count} concepte descoperite.
                {winningReaction && (
                  <span className="alchemy-winning-reaction">
                    <span
                      className="faint alchemy-winning-caption"
                    >
                      CUM AI FĂURIT-O
                    </span>
                    {winningReaction.parents[0].label} +{" "}
                    {winningReaction.parents[1].label} →{" "}
                    <strong className="alchemy-result-emphasis">
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
        </Presence>
      </div>
    </div>
  );
}

function AlchemyWord({ fresh, pulsing, buttonRef, ...props }: ComponentProps<"button"> & {
  fresh: boolean; pulsing: boolean; buttonRef: (node: HTMLButtonElement | null) => void;
}) {
  const elementRef = useRef<HTMLButtonElement>(null);
  useElementMotion(elementRef, pulsing ? { scale: [1, 1.08, 1] }
    : fresh ? { opacity: [0, 1], scale: [0.4, 1] } : false,
  { spring: { stiffness: 320, damping: 18 } }, [fresh, pulsing]);
  return <button {...props} ref={(node) => { elementRef.current = node; buttonRef(node); }} />;
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
      className="row wrap alchemy-reaction-row"
    >
      <span className="muted alchemy-reaction-parents">
        {reaction.parents[0].label} + {reaction.parents[1].label} →
      </span>
      <span className="row wrap alchemy-reaction-results">
        {reaction.results.map((item) => {
          const isSelected = selected.includes(item.id);
          const isFresh = freshIds.has(item.id);
          const currentItem = inventoryById.get(item.id);
          const depleted = currentItem?.depleted ?? true;
          return (
            <button
              key={item.id}
              type="button"
              className={`chip alchemy-reaction-result${isFresh ? " alchemy-reaction-result--fresh" : ""}${depleted ? " alchemy-reaction-result--depleted" : ""}`}
              disabled={busy || depleted}
              aria-pressed={isSelected}
              aria-label={depleted ? `${item.label}, pus deoparte` : `Alege ${item.label}`}
              title={depleted ? "Pus deoparte" : "Pune în alambic"}
              onClick={() => onSelect(item.id)}
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
  if (!item) return null;
  return (
    <button
      type="button"
      className="chip alchemy-slot"
      onClick={() => onRemove(item.id)}
      disabled={disabled}
      title={`Scoate ${item.label} din alambic`}
      aria-label={`Scoate ${item.label} din alambic`}
    >
      <span className="alchemy-slot-label">{item.label}</span>
      <span aria-hidden>×</span>
    </button>
  );
}
