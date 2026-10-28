import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "preact/hooks";
import { useIsPresent } from "@roedu/ui/motion";
import { Button, Spinner, type ToastKind } from "@roedu/ui";
import { ApiError } from "../api/client";
import { explorationApi, type ExplorationResult, type ExplorationState } from "../api/alchimieExplore";
import type { Concept } from "../api/alchimie";
import { GameShell } from "../components/GameShell";
import { AlchimieModes } from "../components/AlchimieModes";
import { EXPLORATION_SAVE_KEY, readExplorationSave, saveExplorationState } from "../explorationSave";
import { sound } from "../sound";

const ACCENT = "#c5a0f0";
const EMPTY_PAIR_FRESH_MS = 30_000;
const normalize = (value: string) => value.normalize("NFD").replace(/\p{M}/gu, "").toLocaleLowerCase("ro-RO").trim();
type Recovery = "changed" | "failed" | "invalid" | null;
type LastReaction = { ingredients: [string, string]; results: Concept[]; supplied: Concept[]; known: boolean };

export default function AlchimieExplore({ onExit }: {
  onExit: () => void;
  onToast: (message: string, kind?: ToastKind) => void;
}) {
  const isPresent = useIsPresent();
  const liveRef = useRef(true);
  const initialSave = useMemo(() => readExplorationSave(), []);
  const savedRawRef = useRef(initialSave.raw);
  const stateConfirmedAtRef = useRef(0);
  const generationRef = useRef(0);
  const flightRef = useRef(false);
  const [state, setState] = useState<ExplorationState | null>(null);
  const localStateRef = useRef(state);
  useLayoutEffect(() => { localStateRef.current = state; }, [state]);
  const [busy, setBusy] = useState(initialSave.kind === "saved");
  const [recovery, setRecovery] = useState<Recovery>(initialSave.kind === "invalid" ? "invalid" : null);
  const [storageUnavailable, setStorageUnavailable] = useState(initialSave.kind === "unavailable");
  const [selected, setSelected] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [journalQuery, setJournalQuery] = useState("");
  const journalSearchRef = useRef<HTMLInputElement>(null);
  const [recipesOpen, setRecipesOpen] = useState(false);
  const [lastReaction, setLastReaction] = useState<LastReaction | null>(null);
  const [message, setMessage] = useState("");
  const [dropId, setDropId] = useState<string | null>(null);
  const dragSourceRef = useRef<{ gameId: string; id: string } | null>(null);
  const buttonsRef = useRef(new Map<string, HTMLButtonElement>());
  const libraryRef = useRef<HTMLElement>(null);
  const benchRef = useRef<HTMLDivElement>(null);
  const [benchPinned, setBenchPinned] = useState(false);
  const pendingFocusRef = useRef<{ origin: HTMLElement; id: string | null; keyboard: boolean } | null>(null);
  const locked = !isPresent || busy || recovery !== null;
  useLayoutEffect(() => {
    liveRef.current = isPresent;
    if (!isPresent) { generationRef.current += 1; flightRef.current = false; dragSourceRef.current = null; pendingFocusRef.current = null; }
    return () => { liveRef.current = false; generationRef.current += 1; flightRef.current = false; };
  }, [isPresent]);

  useEffect(() => {
    const element = benchRef.current;
    if (!element) return;
    const resize = () => {
      const height = element.getBoundingClientRect().height;
      const viewport = window.visualViewport?.height ?? window.innerHeight;
      const pinned = viewport >= 480 && height <= viewport * 0.35;
      setBenchPinned(pinned);
      element.parentElement?.style.setProperty("--alchemy-bench-clearance", `${pinned ? height + 16 : 12}px`);
    };
    const observer = new ResizeObserver(resize);
    observer.observe(element);
    window.visualViewport?.addEventListener("resize", resize);
    window.addEventListener("resize", resize);
    resize();
    return () => {
      observer.disconnect();
      window.visualViewport?.removeEventListener("resize", resize);
      window.removeEventListener("resize", resize);
    };
  }, [state?.game_id]);

  const adopt = useCallback(async (fresh: ExplorationState) => {
    if (!liveRef.current) return false;
    const epoch = generationRef.current;
    const saved = await saveExplorationState(fresh, savedRawRef.current, undefined, undefined, () => liveRef.current && generationRef.current === epoch);
    if (!liveRef.current || generationRef.current !== epoch) return false;
    if (saved.kind === "merged") {
      savedRawRef.current = saved.raw;
      setRecovery("changed");
      return false;
    }
    if (saved.kind === "changed") {
      setRecovery("changed");
      return false;
    }
    if (saved.kind === "saved") savedRawRef.current = saved.raw;
    setStorageUnavailable(saved.kind === "unavailable");
    stateConfirmedAtRef.current = performance.now();
    setState(fresh);
    setRecovery(null);
    return true;
  }, []);

  const loadCollection = useCallback(async () => {
    if (!liveRef.current || flightRef.current) return;
    const save = readExplorationSave();
    if (save.kind === "invalid") { setRecovery("invalid"); setBusy(false); return; }
    const epoch = ++generationRef.current;
    flightRef.current = true;
    setBusy(true);
    savedRawRef.current = save.raw;
    try {
      let fresh: ExplorationState;
      if (save.kind === "saved") {
        try {
          fresh = save.value.needs_restore
            ? await explorationApi.create({ progress: save.value.progress, goal_id: save.value.goal_id })
            : await explorationApi.get(save.value.game_id);
        }
        catch (error) {
          if (!(error instanceof ApiError) || error.status !== 404) throw error;
          fresh = await explorationApi.create({ progress: save.value.progress, goal_id: save.value.goal_id });
        }
      } else if (save.kind === "unavailable" && localStateRef.current) {
        // Storage failure must not replace a live local collection on re-entry.
        fresh = await explorationApi.get(localStateRef.current.game_id);
      } else fresh = await explorationApi.create();
      if (generationRef.current !== epoch) return;
      if (await adopt(fresh)) {
        setSelected(fresh.hint?.pair?.[0].id ?? null);
        setLastReaction(null);
        setMessage(save.kind === "saved" && !fresh.complete ? "Colecția ta este pregătită. Continuă să descoperi." : "");
      }
    } catch (error) {
      if (generationRef.current === epoch) {
        setRecovery(error instanceof ApiError && [400, 409].includes(error.status) ? "invalid" : "failed");
      }
    } finally {
      if (generationRef.current === epoch) { flightRef.current = false; setBusy(false); }
    }
  }, [adopt]);

  const departedRef = useRef(false);
  useLayoutEffect(() => {
    if (!isPresent) departedRef.current = true;
    else if (departedRef.current) {
      departedRef.current = false;
      if (localStateRef.current || readExplorationSave().kind === "saved") void loadCollection();
      else setBusy(false);
    }
  }, [isPresent, loadCollection]);

  useEffect(() => {
    if (initialSave.kind === "saved") void loadCollection();
    return () => { generationRef.current += 1; flightRef.current = false; };
  }, [initialSave.kind, loadCollection]);

  useEffect(() => {
    const changed = (event: StorageEvent) => {
      if ((event.key === EXPLORATION_SAVE_KEY || event.key === null) &&
        readExplorationSave().raw !== savedRawRef.current) setRecovery("changed");
    };
    window.addEventListener("storage", changed);
    return () => window.removeEventListener("storage", changed);
  }, []);

  const act = useCallback(async (
    operation: (gameId: string) => Promise<ExplorationState>,
    onSuccess?: (fresh: ExplorationState) => void,
    onRecovered?: (fresh: ExplorationState) => void,
  ) => {
    if (!liveRef.current || !state || flightRef.current || locked) return;
    const save = readExplorationSave();
    if (save.kind !== "unavailable" && save.raw !== savedRawRef.current) { setRecovery("changed"); return; }
    const epoch = generationRef.current;
    const gameId = state.game_id;
    flightRef.current = true;
    setBusy(true);
    try {
      const fresh = await operation(gameId);
      if (generationRef.current !== epoch) return;
      if (fresh.game_id !== gameId) throw new Error("Unexpected exploration session");
      if (await adopt(fresh)) onSuccess?.(fresh);
    } catch {
      if (generationRef.current !== epoch) return;
      // An action may have reached the server. Read once; never replay the mutation.
      try {
        const fresh = await explorationApi.get(gameId);
        if (generationRef.current !== epoch) return;
        if (fresh.game_id !== gameId) throw new Error("Unexpected exploration session");
        if (await adopt(fresh)) {
          setSelected(fresh.hint?.pair?.[0].id ?? null);
          setLastReaction(null);
          setMessage("Colecție sincronizată. Poți continua.");
          onRecovered?.(fresh);
        }
      } catch {
        if (generationRef.current === epoch) setRecovery("failed");
      }
    } finally {
      if (generationRef.current === epoch) { flightRef.current = false; setBusy(false); }
    }
  }, [state, locked, adopt]);

  const combine = useCallback((a: string, b: string, keyboard = false) => {
    if (a === b || !state || locked || flightRef.current || [a, b].some((id) => !state.inventory.some((item) => item.id === id && item.status === "active"))) return;
    const origin = document.activeElement;
    // Local acknowledgments obey the same saved-collection ownership guard as requests.
    const save = readExplorationSave();
    if (save.kind !== "unavailable" && save.raw !== savedRawRef.current) { setRecovery("changed"); return; }
    const ingredients: [string, string] = [
      state.inventory.find((item) => item.id === a)!.label,
      state.inventory.find((item) => item.id === b)!.label,
    ];
    const pairLabel = ingredients.join(" + ");
    const tried = state.empty_pairs?.some(([left, right]) =>
      (left === a && right === b) || (left === b && right === a));
    // Revalidate older observations so a newly published recipe can be discovered.
    if (tried && performance.now() - stateConfirmedAtRef.current < EMPTY_PAIR_FRESH_MS) {
      setLastReaction({ ingredients, results: [], supplied: [], known: false });
      setMessage(`${pairLabel}: ai încercat deja această pereche fără rezultat. Alege alt ingredient.`);
      // No request disables this button; keep its existing focus without a deferred ref.
      if (keyboard && origin instanceof HTMLElement) origin.scrollIntoView({ block: "center" });
      return;
    }
    void act((gameId) => explorationApi.combine(gameId, a, b), (fresh) => {
      const result = fresh as ExplorationResult;
      const carry = fresh.inventory.find((item) => result.discovered.some((entry) => entry.id === item.id) && item.status === "active");
      const next = carry?.id ?? (fresh.inventory.some((item) => item.id === a && item.status === "active") ? a : null);
      setSelected(next);
      const outputs = [...(result.result ? [result.result] : []), ...result.discovered];
      setLastReaction({
        ingredients,
        results: outputs.filter((item, index) => outputs.findIndex((entry) => entry.id === item.id) === index),
        supplied: result.supplied ?? [],
        known: result.already_known,
      });
      setMessage((result.result === null ? `${pairLabel}: ` : "") + result.message + (carry ? ` ${carry.label} rămâne ales.` : ""));
      if (result.discovered.length) sound.playHop();
      if (origin instanceof HTMLElement && origin.matches(".alchemy-word")) pendingFocusRef.current = { origin, id: next, keyboard };
    }, (fresh) => {
      if (origin instanceof HTMLElement && origin.matches(".alchemy-word")) {
        const next = fresh.inventory.some((item) => item.id === a && item.status === "active") ? a : null;
        pendingFocusRef.current = { origin, id: next, keyboard };
      }
    });
  }, [state, locked, act]);

  const choose = useCallback((id: string, keyboard: boolean) => {
    if (locked || flightRef.current) return;
    if (selected === id) setSelected(null);
    else if (selected) combine(selected, id, keyboard);
    else { setSelected(id); setMessage(""); sound.playSelect(); }
  }, [locked, selected, combine]);

  useLayoutEffect(() => {
    const pending = pendingFocusRef.current;
    if (!pending || busy || locked || !liveRef.current) return;
    pendingFocusRef.current = null;
    if (document.activeElement !== document.body && document.activeElement !== pending.origin) return;
    const target = pending.origin.isConnected && !(pending.origin as HTMLButtonElement).disabled
      ? pending.origin : pending.id ? buttonsRef.current.get(pending.id) : null;
    if (target && !(target as HTMLButtonElement).disabled) target.focus({ preventScroll: true });
    else libraryRef.current?.focus({ preventScroll: true });
    // Keyboard activation must leave its focus visible. Centering clears the bench,
    // whose pinned height is bounded; pointer crafting keeps its browsing position.
    if (pending.keyboard) (target ?? libraryRef.current?.querySelector(".alchemy-library-toolbar"))?.scrollIntoView({ block: "center" });
  }, [state, busy, locked, message]);

  useEffect(() => {
    const escape = (event: KeyboardEvent) => {
      if (liveRef.current && event.key === "Escape" && !event.defaultPrevented && !flightRef.current) setSelected(null);
    };
    window.addEventListener("keydown", escape);
    return () => window.removeEventListener("keydown", escape);
  }, []);

  const selectResult = (id: string) => {
    if (locked || flightRef.current || !state?.inventory.some((item) => item.id === id && item.status === "active")) return;
    setSelected(id);
    sound.playSelect();
  };

  const normalizedQuery = normalize(query);
  const items = state?.inventory.slice().reverse().filter((item) => !normalizedQuery || normalize(item.label).includes(normalizedQuery)) ?? [];
  const selectedItem = state?.inventory.find((item) => item.id === selected);
  const emptyPartners = new Set((state?.empty_pairs ?? []).flatMap(([a, b]) =>
    a === selected ? [b] : b === selected ? [a] : []));
  const goal = state?.goals.find((item) => item.id === state.goal_id);
  const journal = state?.inventory.filter((item) => item.parents !== null).slice().reverse() ?? [];
  const normalizedJournalQuery = normalize(journalQuery);
  const journalResults = journal.filter((item) => !normalizedJournalQuery ||
    [item.label, ...(item.parents?.map((parent) => parent.label) ?? [])]
      .some((label) => normalize(label).includes(normalizedJournalQuery)));

  const recoveryNotice = recovery && (
    <div className="alchemy-explore-recovery" role="alert">
      <strong>{recovery === "changed" ? "Colecția s-a schimbat în altă filă." :
        recovery === "invalid" ? "Colecția salvată nu poate fi încărcată." : "Nu am putut verifica colecția."}</strong>
      <p>{recovery === "invalid"
        ? "Salvarea a rămas pe acest dispozitiv. Reîncearcă după actualizarea jocului."
        : "Descoperirile salvate sunt păstrate. Încarcă starea curentă pentru a continua."}</p>
      <Button variant="secondary" disabled={busy} onClick={() => void loadCollection()}>
        {busy ? "Se încarcă…" : "Încarcă colecția"}
      </Button>
    </div>
  );

  return (
    <div className={`screen-pad fill alchemy-screen alchemy-explore-screen${state ? " alchemy-simple" : " alchemy-intro"}`} aria-busy={busy}>
      <div className="container col game-container alchemy-game">
        <GameShell onExit={() => { generationRef.current += 1; liveRef.current = false; flightRef.current = false; onExit(); }} title="Alchimie" accent={ACCENT} busy={busy} />
        <AlchimieModes mode="explore" busy={busy} />
        {storageUnavailable && <p className="alchemy-save-note" role="status">Browserul nu poate păstra colecția. Descoperirile rămân disponibile cât timp ții jocul deschis.</p>}
        {recoveryNotice}
        {!state ? (
          busy ? <div className="center alchemy-explore-loading"><Spinner label="Se pregătește colecția…" /></div> : (
            <section className="alchemy-explore-intro">
              <span className="alchemy-eyebrow">UN CUVÂNT DUCE LA ALTUL</span>
              <h1>O lume de descoperit.</h1>
              <p>Atinge două cuvinte și vezi ce creezi. Păstrezi fiecare descoperire și alegi singur ce explorezi mai departe.</p>
              <div className="alchemy-intro-example" aria-label="Două cuvinte se combină într-o descoperire"><span>Cuvânt</span><b>+</b><span>Cuvânt</span><b>→</b><span>✦ Descoperire</span></div>
              <Button disabled={locked} onClick={() => void loadCollection()}>Începe explorarea →</Button>
              <p className="alchemy-inventory-note">Fără scor sau penalizări. Colecția se salvează pe acest dispozitiv. Obiectivele sunt opționale.</p>
            </section>
          )
        ) : (
          <>
            <section className="alchemy-world-heading" aria-label="Lumea de explorat">
              <h1>{state.world.title}</h1>
            </section>
            {state.complete && <p className="alchemy-explore-complete" role="status">Ai descoperit toate cuvintele din această lume! Colecția și rețetele tale rămân aici.</p>}
            <div className="alchemy-workspace">
              <div ref={benchRef} className={`alchemy-bench${benchPinned ? " alchemy-bench--pinned" : ""}`} aria-label="Alambic">
                <div className="alchemy-craft-cue">
                  {state.complete ? <p className="alchemy-craft-prompt">Răsfoiește cuvintele sau deschide „Rețete”.</p> : selectedItem ? <><button type="button" className="alchemy-slot" disabled={locked} aria-label={`Scoate ${selectedItem.label} din alambic`} onClick={() => setSelected(null)}><span className="alchemy-slot-label">{selectedItem.label}</span></button><span className="alchemy-craft-plus" aria-hidden>+</span><span className="alchemy-craft-prompt">Atinge un alt cuvânt</span></> : <p className="alchemy-craft-prompt">Alege două cuvinte pentru a le combina.</p>}
                </div>
                {busy && <span className="alchemy-working" role="status">Se verifică…</span>}
                {lastReaction && <div className="alchemy-last-reaction" role="status" aria-live="polite" aria-atomic="true">
                  <div className="alchemy-result-line"><span>{lastReaction.ingredients.join(" + ")} →</span>
                    {lastReaction.results.length ? lastReaction.results.map((item, index) => <span key={item.id}>{index > 0 && ", "}<button type="button" className="alchemy-result-word" disabled={locked || !state.inventory.some((entry) => entry.id === item.id && entry.status === "active")} aria-label={`Alege ${item.label}`} onClick={() => selectResult(item.id)}>{item.label}</button></span>) : <span>fără rezultat</span>}
                  </div>
                  {lastReaction.known && <p className="alchemy-result-note">Deja în colecție.</p>}
                  {lastReaction.supplied.length > 0 && <p className="alchemy-result-note">Provizii primite: {lastReaction.supplied.map((item) => item.label).join(", ")}.</p>}
                </div>}
                {message && <p className={`alchemy-feedback${lastReaction?.results.length ? " visually-hidden" : ""}`} role="status">{message}</p>}
                {state.hint && <p className="alchemy-feedback alchemy-explore-hint" role="status">{state.hint.message}</p>}
              </div>
              <section ref={libraryRef} tabIndex={-1} className="col alchemy-inventory-panel" aria-label="Colecția ta">
                <h2 className="visually-hidden">Cuvintele tale</h2>
                <div className="alchemy-library-tools alchemy-library-toolbar">
                  <input ref={recipesOpen ? journalSearchRef : undefined} id={recipesOpen ? "alchemy-journal-search" : "alchemy-collection-search"} type="search" className="field alchemy-inventory-search" value={recipesOpen ? journalQuery : query}
                    onInput={(event) => { if (recipesOpen) setJournalQuery(event.currentTarget.value); else setQuery(event.currentTarget.value); }}
                    onKeyDown={(event) => {
                      if (event.key !== "Escape") return;
                      if (recipesOpen ? journalQuery : query) { event.preventDefault(); if (recipesOpen) setJournalQuery(""); else setQuery(""); }
                      else if (recipesOpen) { event.preventDefault(); setRecipesOpen(false); }
                    }}
                    placeholder={recipesOpen ? "Caută o rețetă…" : "Caută un cuvânt…"} aria-label={recipesOpen ? "Caută în rețetele mele" : "Caută în colecție"}
                    aria-describedby={recipesOpen && journal.length > 0 ? "alchemy-journal-count" : undefined} autoComplete="off" spellcheck={false} />
                  <button type="button" className="alchemy-recipes-toggle" aria-expanded={recipesOpen} aria-controls="alchemy-earned-recipes" onClick={() => setRecipesOpen(!recipesOpen)}>{recipesOpen ? "Cuvinte" : "Rețete"}</button>
                </div>
                {(recipesOpen ? journalQuery : query) && <Button variant="secondary" className="alchemy-clear-search" onClick={(event) => {
                  if (recipesOpen) { setJournalQuery(""); journalSearchRef.current?.focus({ preventScroll: true }); }
                  else { setQuery(""); libraryRef.current?.querySelector<HTMLInputElement>(".alchemy-inventory-search")?.focus({ preventScroll: true }); }
                  if (event.detail === 0) libraryRef.current?.querySelector(".alchemy-library-toolbar")?.scrollIntoView({ block: "center" });
                }}>{recipesOpen ? "Șterge căutarea din rețete" : "Șterge căutarea"}</Button>}
                <div className="alchemy-inventory-grid" hidden={recipesOpen}>
                  {items.map((item) => {
                    const inactive = item.status !== "active";
                    const hinted = state.hint?.pair?.some((entry) => entry.id === item.id) ?? false;
                    const isSelected = selected === item.id;
                    const triedEmpty = !inactive && emptyPartners.has(item.id);
                    return <button key={item.id} ref={(node) => { if (node) buttonsRef.current.set(item.id, node); else buttonsRef.current.delete(item.id); }} type="button"
                      className={`chip alchemy-word${isSelected ? " alchemy-word--selected" : ""}${hinted ? " alchemy-word--hint" : ""}${triedEmpty ? " alchemy-word--tried" : ""}${dropId === item.id ? " alchemy-word--drop" : ""}`}
                      disabled={locked || inactive} aria-pressed={isSelected} aria-label={`${item.label}${inactive ? ", colecționat" : triedEmpty ? `, încercat fără rezultat cu ${selectedItem?.label}` : ""}`}
                      title={inactive ? item.status === "final" ? "Colecționat: nu intră în alte rețete." : "Toate descoperirile cu acest cuvânt sunt deja în colecție." : triedEmpty ? `Încercat fără rezultat cu ${selectedItem?.label}. Alege altă pereche.` : item.description}
                      onClick={(event) => choose(item.id, event.detail === 0)} draggable={!locked && !inactive}
                      onDragStart={(event) => { if (!event.dataTransfer || locked || inactive || flightRef.current) { event.preventDefault(); return; } dragSourceRef.current = { gameId: state.game_id, id: item.id }; event.dataTransfer.setData("text/plain", item.id); event.dataTransfer.effectAllowed = "copy"; }}
                      onDragOver={(event) => { if (event.dataTransfer && !locked && !inactive && dragSourceRef.current?.gameId === state.game_id && dragSourceRef.current.id !== item.id) { event.preventDefault(); setDropId(item.id); event.dataTransfer.dropEffect = "copy"; } }}
                      onDragLeave={() => setDropId(null)} onDragEnd={() => { dragSourceRef.current = null; setDropId(null); }}
                      onDrop={(event) => { event.preventDefault(); const source = dragSourceRef.current; dragSourceRef.current = null; setDropId(null); if (event.dataTransfer && source?.gameId === state.game_id && source.id === event.dataTransfer.getData("text/plain")) combine(source.id, item.id); }}>
                      <span className="alchemy-word-label">{item.label}</span>
                    </button>;
                  })}
                  {items.length === 0 && <p className="alchemy-empty-inventory">Niciun cuvânt găsit.</p>}
                </div>
                <section id="alchemy-earned-recipes" className="alchemy-explore-journal" hidden={!recipesOpen} aria-label="Rețetele mele">
                  {journal.length > 0 && <div className="alchemy-journal-tools"><p id="alchemy-journal-count" role="status">{journalQuery ? `${journalResults.length} din ${journal.length} rețete găsite` : "Doar rețetele pe care le-ai descoperit."}</p></div>}
                  {journal.length === 0 ? <p className="alchemy-inventory-note">Prima rețetă apare aici când creezi un cuvânt nou.</p>
                    : journalResults.length === 0 ? <p className="alchemy-inventory-note">Nicio rețetă găsită. Încearcă alt cuvânt sau șterge căutarea.</p>
                      : journalResults.map((item) => <article key={item.id} className="alchemy-journal-entry"><h3>{item.parents?.[0].label} + {item.parents?.[1].label} → <button type="button" className="alchemy-result-word" disabled={locked || item.status !== "active"} aria-label={`Alege ${item.label}`} onClick={() => selectResult(item.id)}>{item.label}</button></h3><p>{item.explanation}</p>{item.sources.length > 0 && <details><summary>Surse</summary><ul>{item.sources.map((source, index) => <li key={source}><a href={source} target="_blank" rel="noreferrer">Sursa {index + 1}</a></li>)}</ul></details>}</article>)}
                </section>
              </section>
            </div>
            <details className="alchemy-explore-goal">
              <summary><span>Obiectiv opțional</span><strong>{goal ? `${goal.completed ? "✓ " : ""}${goal.label}` : "Explorez liber"}</strong></summary>
              <div className="alchemy-goal-content">
              <label htmlFor="alchemy-optional-goal">Obiectiv opțional</label>
              <select id="alchemy-optional-goal" className="field" value={state.goal_id ?? ""} disabled={locked}
                onChange={(event) => { const value = event.currentTarget.value || null; void act((id) => explorationApi.goal(id, value), () => { setSelected(null); setMessage(""); }); }}>
                <option value="">Explorez liber</option>
                {state.goals.map((item) => <option key={item.id} value={item.id}>{item.completed ? "✓ " : ""}{item.title}</option>)}
              </select>
              {goal && <p role="status">{goal.completed ? `✓ ${goal.label} descoperit! Poți continua sau alege alt obiectiv.` : `Descoperă: ${goal.label}. Poți crea și orice altceva pe drum.`}</p>}
              </div>
            </details>
            <details className="alchemy-menu"><summary>Ajutor pentru explorare</summary><div className="alchemy-menu-content">
              {!state.complete && <div className="alchemy-assistance"><Button variant="secondary" disabled={locked || state.hint?.stage === "pair"} onClick={() => void act(explorationApi.hint, (fresh) => { setSelected(fresh.hint?.pair?.[0].id ?? null); setQuery(""); setRecipesOpen(false); setMessage(""); })}>{state.hint?.stage === "output" ? "Arată-mi perechea" : "O idee?"}</Button><span>{state.hint?.stage === "pair" ? "Atinge al doilea cuvânt marcat." : "Gratuit"}</span></div>}
              <p>{state.world.description}</p><p>Atinge două cuvinte sau trage unul peste altul. O pereche are aceeași rețetă indiferent de obiectivul ales.</p><p>Nu toate perechile au o rețetă. Încercările nu te costă nimic. Cere o idee pentru un rezultat apropiat, apoi perechea exactă dacă ai nevoie.</p><p>Colecția păstrează toate cuvintele. Cele fără descoperiri noi rămân vizibile, dar nu se mai combină. În „Rețete” găsești doar rețetele descoperite. Proviziile noi se deschid automat pe măsură ce descoperi.</p><p>Colecția se salvează în acest browser. Ștergerea datelor browserului șterge și salvarea locală.</p>
            </div></details>
          </>
        )}
      </div>
    </div>
  );
}
