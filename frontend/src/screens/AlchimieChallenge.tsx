// Alchimie — Infinite-Craft over the Romanian KG. Text-only: the inventory is a grid of
// clickable concepts: a first tap selects, a second tap crafts their shared neighbour(s).
// Server-authoritative: we render whatever the backend returns and never know the target
// id until the server reveals it on a win.

import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "preact/hooks";
import { useIsPresent } from "@roedu/ui/motion";
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
import { GameIntro } from "../components/GameIntro";
import { StartFailureNotice } from "../components/StartFailureNotice";
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

const REACTION_LOG_LIMIT = 12;

const isTerminalResume = (state: AlchimieState) => state.won === true;

type ActionSync = { gameId: string; kind: "failed" | "changed" };

type CraftedItem = InventoryItem & { parents: [Concept, Concept] };

interface Reaction {
  ingredientKey: string;
  parents: [Concept, Concept];
  results: CraftedItem[];
}

interface LatestReaction {
  gameId: string;
  parents: [Concept, Concept];
  results: Concept[];
  discoveryMessage?: string;
}

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
  const [lastReaction, setLastReaction] = useState<LatestReaction | null>(null);
  // Only an earned hint may mark a suggested pair.
  const [hintIds, setHintIds] = useState<Set<string>>(new Set());
  const [recipesOpen, setRecipesOpen] = useState(false);
  const [recipeQuery, setRecipeQuery] = useState("");
  const [inventoryQuery, setInventoryQuery] = useState("");
  const [lastMessage, setLastMessage] = useState<string | null>(null);
  const [difficulty, setDifficulty] = useState<Difficulty>("usor");
  const [category, setCategory] = useState<string | null>(null);
  const [isRecord, setIsRecord] = useState(false);
  const [isPuzzleRecord, setIsPuzzleRecord] = useState(false);
  const inventoryButtonsRef = useRef(new Map<string, HTMLButtonElement>());
  const inventoryPanelRef = useRef<HTMLElement>(null);
  const completionHeadingRef = useRef<HTMLHeadingElement>(null);
  const completionFocusedGameRef = useRef<string | null>(null);
  const pendingCraftFocusRef = useRef<{ gameId: string; origin: HTMLElement; targetId: string | null } | null>(null);
  const dragSourceRef = useRef<{ id: string; gameId: string } | null>(null);
  const [dragOverId, setDragOverId] = useState<string | null>(null);
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

  const applyAuthoritativeState = useCallback((fresh: AlchimieState, options: { preserveLibrary?: boolean; preserveReaction?: boolean } = {}) => {
    pendingCraftFocusRef.current = null;
    setState(fresh);
    setSelected(fresh.earned_hint?.hint?.slice(0, 1).map((item) => item.id) ?? []);
    setEmptyPairKey(null);
    setHintIds(new Set(fresh.earned_hint?.hint?.map((item) => item.id) ?? []));
    if (!options.preserveLibrary) {
      setInventoryQuery("");
      setRecipeQuery("");
      setRecipesOpen(false);
    }
    if (!options.preserveReaction) {
      const latest = buildReactionLog(fresh.inventory)[0];
      setLastReaction(latest ? { gameId: fresh.game_id, parents: latest.parents, results: latest.results } : null);
    }
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
        setRecipesOpen(false);
        setRecipeQuery("");
        setLastReaction(null);
        setMenuOpen(false);
        dragSourceRef.current = null;
        setDragOverId(null);
        setActionSync(null);
        setBusy(false);
        active.remember(s.game_id);
        dismissRecovery();
        setSelected([]);
        setEmptyPairKey(null);
        setHintIds(new Set());
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
  const currentGameId = state?.game_id;
  useLayoutEffect(() => {
    if (!liveRef.current || !isPresent || !won || !currentGameId || completionFocusedGameRef.current === currentGameId) return;
    const heading = completionHeadingRef.current;
    if (!heading) return;
    completionFocusedGameRef.current = currentGameId;
    heading.focus();
  }, [won, currentGameId, isPresent]);


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
    applyAuthoritativeState(outcome.state, { preserveLibrary: true });
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
    const parents = pair.map((id) => state.inventory.find((item) => item.id === id)) as [InventoryItem, InventoryItem];
    if (pairKey(pair) === emptyPairKey) {
      setLastReaction({ gameId: state.game_id, parents, results: [] });
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
      const earnedResults = res.inventory.filter((item) => item.parents !== null && pairKey(item.parents.map((parent) => parent.id)) === pairKey(pair));
      const publicResults = new Map<string, Concept>(earnedResults.map((item) => [item.id, item]));
      for (const item of res.discovered) publicResults.set(item.id, item);
      setLastReaction({ gameId: res.game_id, parents, results: [...publicResults.values()], ...(res.discovered.length > 0 ? { discoveryMessage: res.message } : {}) });
      const recoverableEmpty = res.discovered.length === 0 && !res.won;
      let focusTargetId: string | null = null;
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
        }
        setEmptyPairKey(null);
      }
      if (!res.won && focusOrigin instanceof HTMLElement && focusOrigin.matches(".alchemy-word, .alchemy-reaction-result")) {
        pendingCraftFocusRef.current = { gameId: res.game_id, origin: focusOrigin, targetId: focusTargetId };
      }
      setHintIds(new Set());
      let feedback = res.message;
      if (recoverableEmpty && !res.already_tried) {
        feedback += " Primul cuvânt rămâne ales. Atinge alt partener.";
      }
      if (recoverableEmpty && res.hint_available) {
        feedback += " Apasă „Indiciu” dacă te-ai blocat.";
      }
      setLastMessage(feedback);
      if (res.discovered.length > 0) {
        if (!res.won) sound.playHop();
        // win sound handled by the won effect
      } else {
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
    }
  }, [state, selected, actionsLocked, won, actionOwner, clearSelection, doCombine]);

  const selectResult = useCallback((id: string) => {
    if (startInFlightRef.current || actionsLocked || won || actionOwner.hasPending()) return;
    const item = state?.inventory.find((owned) => owned.id === id);
    if (!item || item.depleted) return;
    setSelected([id]);
    setEmptyPairKey(null);
    sound.playSelect();
  }, [state, actionsLocked, won, actionOwner]);

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
    setInventoryQuery("");
    setRecipeQuery("");
    setRecipesOpen(false);
    setLastReaction(null);
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
      applyAuthoritativeState(fresh, { preserveLibrary: true, preserveReaction: true });
      setInventoryQuery("");
      setRecipesOpen(false);
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
    // while the request was pending; the terminal summary stays in the main flow.
    if (focused !== document.body && focused !== pending.origin) return;
    if (focused === pending.origin && pending.origin.isConnected &&
      !(pending.origin instanceof HTMLButtonElement && pending.origin.disabled)) return;
    const target = pending.targetId ? inventoryButtonsRef.current.get(pending.targetId) : null;
    if (target && !target.disabled) target.focus({ preventScroll: true });
    else inventoryPanelRef.current?.focus({ preventScroll: true });
  }, [state, busy, won, actionsLocked]);
  const normalizedInventoryQuery = useMemo(
    () => normalizeInventorySearch(inventoryQuery),
    [inventoryQuery],
  );
  const visibleInventory = useMemo(
    () => inventory.filter((item) => !normalizedInventoryQuery || normalizeInventorySearch(item.label).includes(normalizedInventoryQuery)).slice().reverse(),
    [inventory, normalizedInventoryQuery],
  );
  const selectedItems = useMemo(
    () =>
      selected
        .map((id) => inventory.find((i) => i.id === id))
        .filter(Boolean) as InventoryItem[],
    [selected, inventory],
  );
  const reactionLog = useMemo(() => buildReactionLog(inventory), [inventory]);
  const normalizedRecipeQuery = normalizeInventorySearch(recipeQuery);
  const visibleRecipes = reactionLog.filter((reaction) =>
    !normalizedRecipeQuery || [...reaction.parents, ...reaction.results].some((item) => normalizeInventorySearch(item.label).includes(normalizedRecipeQuery)),
  );
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
        <GameShell onExit={exitSafely} accent={DEF.accent} title={DEF.title} busy={creating}>
          <span className="alchemy-round-count">{state.moves} {state.moves === 1 ? "combinație" : "combinații"}</span>
        </GameShell>
        <AlchimieModes mode="challenges" busy={creating || busy || loading} />

        <section className={`alchemy-target${won ? " alchemy-target--won" : ""}`} aria-label="Ținta de făurit">
          <div className="alchemy-target-copy">
            <div className="alchemy-target-meta">
              <span className="alchemy-eyebrow">{won ? "ȚINTA FĂURITĂ" : "CREEAZĂ"}</span>
              <span className="alchemy-theme">
                {state.board_category && `${categoryLabel(state.board_category)} · `}{DIFFICULTY_LABEL[state.difficulty]}
                {state.daily && ` · ${formatDayKey(state.daily)}`}
              </span>
            </div>
            <h2>{state.target.label}</h2>
            {state.target.description && <p>{state.target.description}</p>}
            {won && <div className="alchemy-challenge-complete">
              <h2 ref={completionHeadingRef} tabIndex={-1} className="alchemy-completion-heading">Ai făurit ținta!</h2>
              <p>{state.score} puncte.{isRecord ? " Record personal." : isPuzzleRecord ? " Recordul acestei provocări." : ""}</p>
              <StartFailureNotice failed={startFailed} reserveSpace />
              <div className="row wrap alchemy-completion-actions">
                <Button type="button" disabled={creating} onClick={() => void start({ difficulty: state.difficulty, category: state.board_category ?? undefined })}>{creating ? "Se pregătește…" : "Încă unul →"}</Button>
                {sharePayload && <Button type="button" variant="secondary" disabled={creating} onClick={() => void handleCopy()}>Copiază rezultatul</Button>}
                <Button type="button" variant="secondary" disabled={creating} onClick={newGame}>Schimbă opțiunile</Button>
                <Button type="button" variant="secondary" disabled={creating} onClick={exitSafely}>Meniu</Button>
              </div>
            </div>}
          </div>
        </section>

        <div className="alchemy-workspace">
          <div className="alchemy-bench" aria-label="Alambic">
            <div className="alchemy-craft-cue" id="alchemy-instructions">
              {won ? <p className="alchemy-craft-prompt">Poți răsfoi cuvintele și rețetele rundei.</p> : selectedItems[0] ? <>
                <Slot item={selectedItems[0]} onRemove={removeFromBench} disabled={actionsLocked} />
                <span className="alchemy-craft-plus" aria-hidden>+</span>
                <span className="alchemy-craft-prompt">Alege un alt cuvânt</span>
              </> : <p className="alchemy-craft-prompt">Alege două cuvinte. Se combină imediat.</p>}
            </div>
            {busy && <span role="status" className="alchemy-working">Se verifică…</span>}
            {lastReaction?.gameId === state.game_id && <div className="alchemy-last-reaction" aria-label="Ultima combinație">
              <span>{lastReaction.parents[0].label} + {lastReaction.parents[1].label} → </span>
              {lastReaction.results.length ? lastReaction.results.map((item, index) => <span key={item.id}>
                {index > 0 && ", "}<button type="button" className="alchemy-result-word alchemy-reaction-result"
                  disabled={actionsLocked || won || inventoryById.get(item.id)?.depleted !== false}
                  aria-pressed={selected.includes(item.id)} aria-label={`Alege ${item.label}`} onClick={() => selectResult(item.id)}>{item.label}</button>
              </span>) : <span>fără descoperiri noi</span>}
            </div>}
            {lastMessage && <p className={`alchemy-feedback${emptyPairKey ? " alchemy-feedback--empty" : ""}${lastReaction?.gameId === state.game_id && lastReaction.discoveryMessage === lastMessage ? " visually-hidden" : ""}`} role="status" aria-live="polite" aria-atomic="true">{lastMessage}</p>}
            {actionSync && <div className="col alchemy-sync-recovery" role="alert">
              <strong>{actionSync.kind === "changed" ? "Jocul salvat s-a schimbat." : "Verificarea jocului nu a reușit."}</strong>
              <span>{actionSync.kind === "changed" ? "Încarcă jocul curent pentru a continua." : "Acțiunea poate fi deja salvată. Verifică jocul înainte de o nouă combinație, un indiciu sau o reluare."}</span>
              <Button type="button" onClick={() => void retryActionSync()} disabled={busy}>{busy ? "Se verifică…" : actionSync.kind === "changed" ? "Încarcă jocul curent" : "Verifică jocul"}</Button>
            </div>}
            {!won && state.earned_hint && <p className="alchemy-earned-hint" role="status">{state.earned_hint.message}</p>}
            {state.hint_available && !won && <div className="alchemy-assistance">
              <Button type="button" variant="secondary" className="alchemy-challenge-hint" disabled={actionsLocked}
                onClick={() => void doHint()} aria-describedby="alchemy-hint-cost">Indiciu</Button>
              <span id="alchemy-hint-cost">Penalizare de 150 puncte.</span>
            </div>}
          </div>

          <section ref={inventoryPanelRef} tabIndex={-1} className="col alchemy-inventory-panel" aria-label="Inventarul acestei runde">
            <div className="alchemy-library-tools">
              <div className="alchemy-library-toolbar">
                <input type="search" className="field alchemy-inventory-search" value={recipesOpen ? recipeQuery : inventoryQuery}
                  onInput={(event) => { if (recipesOpen) setRecipeQuery(event.currentTarget.value); else setInventoryQuery(event.currentTarget.value); }}
                  onKeyDown={(event) => { if (event.key === "Escape" && (recipesOpen ? recipeQuery : inventoryQuery)) { event.preventDefault(); event.stopPropagation(); if (recipesOpen) setRecipeQuery(""); else setInventoryQuery(""); } }}
                  placeholder={recipesOpen ? "Caută o rețetă…" : "Caută un cuvânt…"}
                  aria-label={recipesOpen ? "Caută în rețetele descoperite" : "Caută în toate conceptele descoperite"}
                  autoComplete="off" spellcheck={false} />
                <button type="button" className="alchemy-recipes-toggle" aria-expanded={recipesOpen} aria-controls="alchemy-challenge-library"
                  onClick={() => setRecipesOpen((open) => !open)}>{recipesOpen ? "Cuvinte" : "Rețete"}</button>
              </div>
            </div>
            <div id="alchemy-challenge-library">
              {recipesOpen ? <div className="alchemy-reaction-history" role="region" aria-label="Rețetele acestei runde">
                {visibleRecipes.map((reaction) => <ReactionRow key={`${reaction.ingredientKey}:${reaction.results.map((item) => item.id).join(",")}`}
                  reaction={reaction} selected={selected} inventoryById={inventoryById} busy={actionsLocked || won} onSelect={selectResult} />)}
                {!visibleRecipes.length && <p className="alchemy-empty-inventory">{reactionLog.length ? "Nicio rețetă găsită." : "Rețetele apar aici după primele descoperiri."}</p>}
              </div> : <div className="alchemy-inventory-grid">
                {visibleInventory.map((item) => {
                  const isSel = selected.includes(item.id);
                  const isHint = hintIds.has(item.id);
                  const isTried = selected.length === 1 && pairKey([selected[0], item.id]) === emptyPairKey;
                  return <button key={item.id} ref={(node) => { if (node) inventoryButtonsRef.current.set(item.id, node); else inventoryButtonsRef.current.delete(item.id); }}
                    type="button" onClick={() => toggle(item.id)} draggable={!actionsLocked && !won && !item.depleted}
                    onDragStartCapture={(event) => {
                      if (!event.dataTransfer || actionsLocked || won || item.depleted || actionOwner.hasPending()) { event.preventDefault(); return; }
                      dragSourceRef.current = { id: item.id, gameId: state.game_id };
                      event.dataTransfer.setData("text/plain", item.id); event.dataTransfer.effectAllowed = "copy";
                    }}
                    onDragOver={(event) => { if (event.dataTransfer && !actionsLocked && !won && !item.depleted && dragSourceRef.current?.gameId === state.game_id && dragSourceRef.current.id !== item.id) { event.preventDefault(); event.dataTransfer.dropEffect = "copy"; setDragOverId(item.id); } }}
                    onDragLeave={() => setDragOverId(null)} onDragEndCapture={() => { dragSourceRef.current = null; setDragOverId(null); }}
                    onDrop={(event) => { event.preventDefault(); const source = dragSourceRef.current; dragSourceRef.current = null; setDragOverId(null); if (event.dataTransfer && source?.gameId === state.game_id && source.id === event.dataTransfer.getData("text/plain")) void doCombine([source.id, item.id]); }}
                    disabled={actionsLocked || won || item.depleted} aria-pressed={isSel}
                    aria-label={item.depleted ? `${item.label}, pus deoparte` : item.label}
                    title={item.depleted ? "Nu mai produce descoperiri noi. Rețetele rămân disponibile." : parentsOf(item) ?? "Concept de start"}
                    className={`chip alchemy-word${isSel ? " alchemy-word--selected" : ""}${isHint ? " alchemy-word--hint" : ""}${isTried ? " alchemy-word--tried" : ""}${dragOverId === item.id ? " alchemy-word--drop" : ""}`}>
                    <span className="alchemy-word-label">{item.label}</span>
                  </button>;
                })}
                {!visibleInventory.length && <p className="alchemy-empty-inventory">Niciun concept găsit.</p>}
              </div>}
            </div>
          </section>
        </div>

        <GameHelp help={ALCHIMIE_HELP} />
        <details className="alchemy-menu" open={menuOpen} onToggle={(event) => setMenuOpen(event.currentTarget.open)}>
          <summary>Opțiuni de joc</summary>
          <div className="alchemy-menu-content">
            {!won && <div className="row wrap alchemy-challenge-actions">
              <Button type="button" variant="secondary" disabled={actionsLocked} onClick={doReset}>Reia același joc</Button>
              <Button type="button" variant="secondary" className="alchimie-other-board" disabled={!isPresent || creating || busy || loading}
                onClick={() => void start({ difficulty: state.difficulty, category: state.board_category ?? undefined })}>Alt joc</Button>
              <Button type="button" variant="secondary" disabled={actionsLocked} onClick={newGame}>Schimbă opțiunile</Button>
            </div>}
          </div>
        </details>
        {!won && <StartFailureNotice failed={startFailed} />}
      </div>
    </div>
  );
}

function ReactionRow({
  reaction,
  selected,
  inventoryById,
  busy,
  onSelect,
}: {
  reaction: Reaction;
  selected: string[];
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
          const currentItem = inventoryById.get(item.id);
          const depleted = currentItem?.depleted ?? true;
          return (
            <button
              key={item.id}
              type="button"
              className="alchemy-result-word alchemy-reaction-result"
              disabled={busy || depleted}
              aria-pressed={isSelected}
              aria-label={depleted ? `${item.label}, pus deoparte` : `Alege ${item.label}`}
              title={depleted ? "Pus deoparte" : "Pune în alambic"}
              onClick={() => onSelect(item.id)}
            >
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
    </button>
  );
}
