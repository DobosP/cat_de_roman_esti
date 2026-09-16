import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { Button, Spinner, type ToastKind } from "@roedu/ui";
import { ApiError } from "../api/client";
import { explorationApi, type ExplorationResult, type ExplorationState } from "../api/alchimieExplore";
import { GameShell } from "../components/GameShell";
import { AlchimieModes } from "../components/AlchimieModes";
import { EXPLORATION_SAVE_KEY, readExplorationSave, saveExplorationState } from "../explorationSave";
import { sound } from "../sound";
import "../styles/alchimie-explore.css";

const ACCENT = "#c5a0f0";
const EMPTY_PAIR_FRESH_MS = 30_000;
const normalize = (value: string) => value.normalize("NFD").replace(/\p{M}/gu, "").toLocaleLowerCase("ro-RO").trim();
type Recovery = "changed" | "failed" | "invalid" | null;

export default function AlchimieExplore({ onExit }: {
  onExit: () => void;
  onToast: (message: string, kind?: ToastKind) => void;
}) {
  const initialSave = useMemo(() => readExplorationSave(), []);
  const savedRaw = useRef(initialSave.raw);
  const stateConfirmedAt = useRef(0);
  const generation = useRef(0);
  const flight = useRef(false);
  const [state, setState] = useState<ExplorationState | null>(null);
  const [busy, setBusy] = useState(initialSave.kind === "saved");
  const [recovery, setRecovery] = useState<Recovery>(initialSave.kind === "invalid" ? "invalid" : null);
  const [storageUnavailable, setStorageUnavailable] = useState(initialSave.kind === "unavailable");
  const [selected, setSelected] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [journalQuery, setJournalQuery] = useState("");
  const journalSearch = useRef<HTMLInputElement>(null);
  const [showAll, setShowAll] = useState(false);
  const [freshIds, setFreshIds] = useState<string[]>([]);
  const [message, setMessage] = useState("");
  const [dropId, setDropId] = useState<string | null>(null);
  const dragSource = useRef<{ gameId: string; id: string } | null>(null);
  const buttons = useRef(new Map<string, HTMLButtonElement>());
  const library = useRef<HTMLElement>(null);
  const bench = useRef<HTMLDivElement>(null);
  const [benchPinned, setBenchPinned] = useState(false);
  const pendingFocus = useRef<{ origin: HTMLElement; id: string | null; keyboard: boolean } | null>(null);
  const locked = busy || recovery !== null;

  useEffect(() => {
    const element = bench.current;
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
    const epoch = generation.current;
    const saved = await saveExplorationState(fresh, savedRaw.current, undefined, undefined, () => generation.current === epoch);
    if (generation.current !== epoch) return false;
    if (saved.kind === "merged") {
      savedRaw.current = saved.raw;
      setRecovery("changed");
      return false;
    }
    if (saved.kind === "changed") {
      setRecovery("changed");
      return false;
    }
    if (saved.kind === "saved") savedRaw.current = saved.raw;
    setStorageUnavailable(saved.kind === "unavailable");
    stateConfirmedAt.current = performance.now();
    setState(fresh);
    setRecovery(null);
    return true;
  }, []);

  const loadCollection = useCallback(async () => {
    if (flight.current) return;
    const save = readExplorationSave();
    if (save.kind === "invalid") { setRecovery("invalid"); setBusy(false); return; }
    const epoch = ++generation.current;
    flight.current = true;
    setBusy(true);
    savedRaw.current = save.raw;
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
      } else fresh = await explorationApi.create();
      if (generation.current !== epoch) return;
      if (await adopt(fresh)) {
        setSelected(fresh.hint?.pair?.[0].id ?? null);
        setQuery("");
        setFreshIds([]);
        setMessage(save.kind === "saved" && !fresh.complete ? "Colecția ta este pregătită. Continuă să descoperi." : "");
      }
    } catch (error) {
      if (generation.current === epoch) {
        setRecovery(error instanceof ApiError && [400, 409].includes(error.status) ? "invalid" : "failed");
      }
    } finally {
      if (generation.current === epoch) { flight.current = false; setBusy(false); }
    }
  }, [adopt]);

  useEffect(() => {
    if (initialSave.kind === "saved") void loadCollection();
    return () => { generation.current += 1; flight.current = false; };
  }, [initialSave.kind, loadCollection]);

  useEffect(() => {
    const changed = (event: StorageEvent) => {
      if ((event.key === EXPLORATION_SAVE_KEY || event.key === null) &&
        readExplorationSave().raw !== savedRaw.current) setRecovery("changed");
    };
    window.addEventListener("storage", changed);
    return () => window.removeEventListener("storage", changed);
  }, []);

  const act = useCallback(async (
    operation: (gameId: string) => Promise<ExplorationState>,
    onSuccess?: (fresh: ExplorationState) => void,
    onRecovered?: (fresh: ExplorationState) => void,
  ) => {
    if (!state || flight.current || locked) return;
    const save = readExplorationSave();
    if (save.kind !== "unavailable" && save.raw !== savedRaw.current) { setRecovery("changed"); return; }
    const epoch = generation.current;
    const gameId = state.game_id;
    flight.current = true;
    setBusy(true);
    try {
      const fresh = await operation(gameId);
      if (generation.current !== epoch) return;
      if (fresh.game_id !== gameId) throw new Error("Unexpected exploration session");
      if (await adopt(fresh)) onSuccess?.(fresh);
    } catch {
      if (generation.current !== epoch) return;
      // An action may have reached the server. Read once; never replay the mutation.
      try {
        const fresh = await explorationApi.get(gameId);
        if (generation.current !== epoch) return;
        if (fresh.game_id !== gameId) throw new Error("Unexpected exploration session");
        if (await adopt(fresh)) {
          setSelected(fresh.hint?.pair?.[0].id ?? null);
          setFreshIds([]);
          setMessage("Colecție sincronizată. Poți continua.");
          onRecovered?.(fresh);
        }
      } catch {
        if (generation.current === epoch) setRecovery("failed");
      }
    } finally {
      if (generation.current === epoch) { flight.current = false; setBusy(false); }
    }
  }, [state, locked, adopt]);

  const combine = useCallback((a: string, b: string, keyboard = false) => {
    if (a === b || !state || locked || flight.current || [a, b].some((id) => !state.inventory.some((item) => item.id === id && item.status === "active"))) return;
    const origin = document.activeElement;
    // Local acknowledgments obey the same saved-collection ownership guard as requests.
    const save = readExplorationSave();
    if (save.kind !== "unavailable" && save.raw !== savedRaw.current) { setRecovery("changed"); return; }
    const pairLabel = [a, b].map((id) => state.inventory.find((item) => item.id === id)?.label).join(" + ");
    const tried = state.empty_pairs?.some(([left, right]) =>
      (left === a && right === b) || (left === b && right === a));
    // Revalidate older observations so a newly published recipe can be discovered.
    if (tried && performance.now() - stateConfirmedAt.current < EMPTY_PAIR_FRESH_MS) {
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
      setFreshIds([...result.discovered, ...(result.supplied ?? [])].map((item) => item.id));
      setMessage((result.result === null ? `${pairLabel}: ` : "") + result.message + (carry ? ` ${carry.label} rămâne ales.` : ""));
      if (result.discovered.length) { setQuery(""); sound.playHop(); }
      if (origin instanceof HTMLElement && origin.matches(".alchemy-word")) pendingFocus.current = { origin, id: next, keyboard };
    }, (fresh) => {
      if (origin instanceof HTMLElement && origin.matches(".alchemy-word")) {
        const next = fresh.inventory.some((item) => item.id === a && item.status === "active") ? a : null;
        pendingFocus.current = { origin, id: next, keyboard };
      }
    });
  }, [state, locked, act]);

  const choose = useCallback((id: string, keyboard: boolean) => {
    if (locked || flight.current) return;
    if (selected === id) setSelected(null);
    else if (selected) combine(selected, id, keyboard);
    else { setSelected(id); setMessage(""); sound.playSelect(); }
  }, [locked, selected, combine]);

  useLayoutEffect(() => {
    const pending = pendingFocus.current;
    if (!pending || busy) return;
    pendingFocus.current = null;
    if (document.activeElement !== document.body && document.activeElement !== pending.origin) return;
    const target = pending.origin.isConnected && !(pending.origin as HTMLButtonElement).disabled
      ? pending.origin : pending.id ? buttons.current.get(pending.id) : null;
    if (target && !(target as HTMLButtonElement).disabled) target.focus({ preventScroll: true });
    else library.current?.focus({ preventScroll: true });
    // Keyboard activation must leave its focus visible. Centering clears the bench,
    // whose pinned height is bounded; pointer crafting keeps its browsing position.
    if (pending.keyboard) (target ?? library.current?.querySelector("h2"))?.scrollIntoView({ block: "center" });
  }, [state, busy, message]);

  useEffect(() => {
    const escape = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !event.defaultPrevented && !flight.current) setSelected(null);
    };
    window.addEventListener("keydown", escape);
    return () => window.removeEventListener("keydown", escape);
  }, []);

  const activeCount = state?.inventory.filter((item) => item.status === "active").length ?? 0;
  const normalizedQuery = normalize(query);
  const items = state?.inventory.filter((item) => normalizedQuery
    ? normalize(item.label).includes(normalizedQuery)
    : state.complete || showAll || item.status === "active" || freshIds.includes(item.id)) ?? [];
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
    <div className="screen-pad fill alchemy-screen alchemy-explore-screen" aria-busy={busy}>
      <div className="container col game-container alchemy-game">
        <GameShell onExit={onExit} title="Alchimie" accent={ACCENT} busy={busy}>
          {state && <span className="alchemy-collection-count" aria-label="Progresul colecției">{state.inventory.length} / {state.world.total_concepts} cuvinte</span>}
        </GameShell>
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
              <div><span className="alchemy-eyebrow">EXPLOREAZĂ ÎN RITMUL TĂU</span><h1>{state.world.title}</h1></div>
              <progress aria-label="Colecție descoperită" value={state.inventory.length} max={state.world.total_concepts} />
              {state.next_unlock && <p className="alchemy-pantry-progress">După încă {state.next_unlock.remaining} {state.next_unlock.remaining === 1 ? "descoperire primești" : "descoperiri primești"} provizii noi.</p>}
            </section>
            <details className="alchemy-explore-goal">
              <summary><span>Obiectiv opțional</span><strong>{goal ? `${goal.completed ? "✓ " : ""}${goal.label}` : "Explorez liber"}</strong></summary>
              <div className="alchemy-goal-content">
              <label htmlFor="alchemy-optional-goal">Obiectiv opțional</label>
              <select id="alchemy-optional-goal" className="field" value={state.goal_id ?? ""} disabled={locked}
                onChange={(event) => { const value = event.target.value || null; void act((id) => explorationApi.goal(id, value), () => { setSelected(null); setMessage(""); }); }}>
                <option value="">Explorez liber</option>
                {state.goals.map((item) => <option key={item.id} value={item.id}>{item.completed ? "✓ " : ""}{item.title}</option>)}
              </select>
              {goal && <p role="status">{goal.completed ? `✓ ${goal.label} descoperit! Poți continua sau alege alt obiectiv.` : `Descoperă: ${goal.label}. Poți crea și orice altceva pe drum.`}</p>}
              </div>
            </details>
            {state.complete && <p className="alchemy-explore-complete" role="status">✦ Ai descoperit toate cuvintele din această lume! Colecția și rețetele tale rămân aici.</p>}
            <div className="alchemy-workspace">
              <div ref={bench} className={`card alchemy-bench${benchPinned ? " alchemy-bench--pinned" : ""}`} aria-label="Alambic">
                <div className="alchemy-craft-cue">
                  {state.complete ? <p className="alchemy-craft-prompt">Răsfoiește cuvintele sau deschide „Rețetele mele”.</p> : selectedItem ? <><button type="button" className="alchemy-slot" disabled={locked} aria-label={`Scoate ${selectedItem.label} din alambic`} onClick={() => setSelected(null)}><span className="alchemy-slot-label">{selectedItem.label}</span><span aria-hidden>×</span></button><span className="alchemy-craft-plus" aria-hidden>+</span><span className="alchemy-craft-prompt">Atinge un alt cuvânt</span></> : <p className="alchemy-craft-prompt">Atinge un cuvânt, apoi altul. Se combină imediat.</p>}
                </div>
                {busy && <span className="alchemy-working" role="status">Se verifică…</span>}
                {message && <p className="alchemy-feedback" role="status">{message}</p>}
                {state.hint && <p className="alchemy-feedback alchemy-explore-hint" role="status">{state.hint.message}</p>}
                {!state.complete && <div className="alchemy-assistance"><Button variant="secondary" disabled={locked || state.hint?.stage === "pair"} onClick={() => void act(explorationApi.hint, (fresh) => { setSelected(fresh.hint?.pair?.[0].id ?? null); setQuery(""); setShowAll(false); setMessage(""); })}>{state.hint?.stage === "output" ? "Arată-mi perechea" : "💡 O idee?"}</Button><span>{state.hint?.stage === "pair" ? "Atinge al doilea cuvânt marcat." : "Gratuit"}</span></div>}
              </div>
              <section ref={library} tabIndex={-1} className="card col alchemy-inventory-panel" aria-label="Colecția ta">
                <div className="alchemy-panel-heading"><h2>Cuvintele tale</h2><span className="alchemy-selection-count">{state.complete ? `${state.inventory.length} colecționate` : `${activeCount} de explorat`}</span></div>
                <details className="alchemy-library-tools"><summary>{query ? `Căutare: ${query}` : state.complete || showAll ? `Toate cuvintele · ${state.inventory.length}` : "Caută și filtrează"}</summary>
                <div className="alchemy-explore-library-tools"><input type="search" className="field alchemy-inventory-search" value={query} onChange={(event) => setQuery(event.target.value)} onKeyDown={(event) => { if (event.key === "Escape" && query) { event.preventDefault(); setQuery(""); } }} placeholder="Caută în colecție…" aria-label="Caută în colecție" autoComplete="off" spellCheck={false} />
                  {!state.complete && <label className="alchemy-show-collection"><input type="checkbox" checked={showAll} onChange={(event) => setShowAll(event.target.checked)} />Toate ({state.inventory.length})</label>}</div></details>
                {query && <Button variant="secondary" className="alchemy-clear-search" onClick={(event) => { setQuery(""); library.current?.focus({ preventScroll: true }); if (event.detail === 0) library.current?.querySelector("h2")?.scrollIntoView({ block: "center" }); }}>Șterge căutarea</Button>}
                <div className="alchemy-inventory-grid">
                  {items.map((item) => {
                    const inactive = item.status !== "active";
                    const hinted = state.hint?.pair?.some((entry) => entry.id === item.id) ?? false;
                    const isSelected = selected === item.id;
                    const fresh = freshIds.includes(item.id);
                    const triedEmpty = !inactive && emptyPartners.has(item.id);
                    return <button key={item.id} ref={(node) => { if (node) buttons.current.set(item.id, node); else buttons.current.delete(item.id); }} type="button"
                      className={`chip alchemy-word${isSelected ? " alchemy-word--selected" : ""}${fresh ? " alchemy-word--fresh" : ""}${hinted ? " alchemy-word--hint" : ""}${triedEmpty ? " alchemy-word--tried" : ""}${dropId === item.id ? " alchemy-word--drop" : ""}`}
                      disabled={locked || inactive} aria-pressed={isSelected} aria-label={`${item.label}${inactive ? ", colecționat" : triedEmpty ? `, încercat fără rezultat cu ${selectedItem?.label}` : ""}`}
                      title={inactive ? item.status === "final" ? "Colecționat: nu intră în alte rețete." : "Toate descoperirile cu acest cuvânt sunt deja în colecție." : triedEmpty ? `Încercat fără rezultat cu ${selectedItem?.label}. Alege altă pereche.` : item.description}
                      onClick={(event) => choose(item.id, event.detail === 0)} draggable={!locked && !inactive}
                      onDragStart={(event) => { if (locked || inactive || flight.current) { event.preventDefault(); return; } dragSource.current = { gameId: state.game_id, id: item.id }; event.dataTransfer.setData("text/plain", item.id); event.dataTransfer.effectAllowed = "copy"; }}
                      onDragOver={(event) => { if (!locked && !inactive && dragSource.current?.gameId === state.game_id && dragSource.current.id !== item.id) { event.preventDefault(); setDropId(item.id); event.dataTransfer.dropEffect = "copy"; } }}
                      onDragLeave={() => setDropId(null)} onDragEnd={() => { dragSource.current = null; setDropId(null); }}
                      onDrop={(event) => { event.preventDefault(); const source = dragSource.current; dragSource.current = null; setDropId(null); if (source?.gameId === state.game_id && source.id === event.dataTransfer.getData("text/plain")) combine(source.id, item.id); }}>
                      <span className="alchemy-word-label">{item.label}</span>{(isSelected || fresh || inactive || triedEmpty) && <span className="alchemy-word-meta" aria-hidden>{isSelected ? "✓ Ales" : triedEmpty ? "Încercat" : fresh ? "✦ Nou" : "Colecționat"}</span>}
                    </button>;
                  })}
                  {items.length === 0 && <p className="alchemy-empty-inventory">{query ? "Niciun cuvânt găsit." : "Toate cuvintele sunt colecționate. Bifează „Toate” pentru a le vedea."}</p>}
                </div>
              </section>
            </div>
            <details className="alchemy-menu alchemy-explore-journal"><summary>Rețetele mele · {journal.length}{journalQuery && <span className="alchemy-journal-query">Căutare: {journalQuery}</span>}</summary><div className="alchemy-menu-content">
              {journal.length > 0 && <div className="alchemy-journal-tools">
                <label htmlFor="alchemy-journal-search">Caută un rezultat sau un ingredient</label>
                <input ref={journalSearch} id="alchemy-journal-search" type="search" className="field"
                  value={journalQuery} onChange={(event) => setJournalQuery(event.target.value)}
                  onKeyDown={(event) => { if (event.key === "Escape" && journalQuery) { event.preventDefault(); setJournalQuery(""); } }}
                  placeholder="De exemplu: făină" aria-label="Caută în rețetele mele"
                  aria-describedby="alchemy-journal-count" autoComplete="off" spellCheck={false} />
                {journalQuery && <Button variant="secondary" className="alchemy-clear-search"
                  onClick={() => { setJournalQuery(""); journalSearch.current?.focus({ preventScroll: true }); }}>Șterge căutarea din rețete</Button>}
                <p id="alchemy-journal-count" role="status">{journalQuery ? `${journalResults.length} din ${journal.length} rețete găsite` : "Doar rețetele pe care le-ai descoperit."}</p>
              </div>}
              {journal.length === 0 ? <p className="alchemy-inventory-note">Prima rețetă apare aici când creezi un cuvânt nou.</p>
                : journalResults.length === 0 ? <p className="alchemy-inventory-note">Nicio rețetă găsită. Încearcă alt cuvânt sau șterge căutarea.</p>
                  : journalResults.map((item) => <article key={item.id} className="alchemy-journal-entry"><h3>{item.parents?.[0].label} + {item.parents?.[1].label} → {item.label}</h3><p>{item.explanation}</p>{item.sources.length > 0 && <details><summary>Surse</summary><ul>{item.sources.map((source, index) => <li key={source}><a href={source} target="_blank" rel="noreferrer">Sursa {index + 1}</a></li>)}</ul></details>}</article>)}
            </div></details>
            <details className="alchemy-menu"><summary>Cum explorezi</summary><div className="alchemy-menu-content"><p>{state.world.description}</p><p>Atinge două cuvinte sau trage unul peste altul. O pereche are aceeași rețetă indiferent de obiectivul ales.</p><p>Nu toate perechile au o rețetă. Încercările nu te costă nimic. Cere o idee pentru un rezultat apropiat, apoi perechea exactă dacă ai nevoie.</p><p>Cuvintele fără descoperiri noi sunt păstrate în „Toate”. Rețetele găsite apar în jurnal. Proviziile noi se deschid automat pe măsură ce descoperi.</p><p>Colecția se salvează în acest browser. Ștergerea datelor browserului șterge și salvarea locală.</p></div></details>
          </>
        )}
      </div>
    </div>
  );
}
