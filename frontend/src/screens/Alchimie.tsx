// Alchimie — Infinite-Craft over the Romanian KG. Text-only: the inventory is a grid of
// clickable concept chips; pick two and "Combina" to discover their shared neighbour(s).
// Server-authoritative: we render whatever the backend returns and never know the target
// id until the server reveals it on a win.

import { useCallback, useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ApiError } from "../api/client";
import {
  alchimieApi,
  type AlchimieState,
  type Concept,
  type InventoryItem,
} from "../api/alchimie";
import type { ToastKind } from "../components/Toast";
import { sound } from "../sound";

const ACCENT = "#c08bff"; // arta_cultura purple — the "alchemy" accent.
const GOLD = "#ffd166";

interface SelfProps {
  onExit: () => void;
  onToast: (message: string, kind?: ToastKind) => void;
}

export default function Alchimie({ onExit, onToast }: SelfProps) {
  const [state, setState] = useState<AlchimieState | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [selected, setSelected] = useState<string[]>([]);
  // ids discovered by the most recent combine — used to animate them in.
  const [freshIds, setFreshIds] = useState<Set<string>>(new Set());
  const [lastMessage, setLastMessage] = useState<string | null>(null);

  const start = useCallback(async () => {
    setLoading(true);
    try {
      const s = await alchimieApi.create();
      setState(s);
      setSelected([]);
      setFreshIds(new Set());
      setLastMessage(null);
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
  }, [onToast]);

  // Create the game on mount.
  useEffect(() => {
    void start();
  }, [start]);

  // Win arpeggio fires once when we transition into the won state.
  const won = state?.won ?? false;
  useEffect(() => {
    if (won) sound.playWin();
  }, [won]);

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

  const doCombine = useCallback(async () => {
    if (!state || selected.length !== 2 || busy) return;
    setBusy(true);
    const [a, b] = selected;
    try {
      const res = await alchimieApi.combine(state.game_id, a, b);
      setState(res);
      setSelected([]);
      setLastMessage(res.message);
      if (res.discovered.length > 0) {
        setFreshIds(new Set(res.discovered.map((d: Concept) => d.id)));
        if (res.won) {
          // win sound handled by the won effect
        } else {
          sound.playHop();
        }
      } else {
        setFreshIds(new Set());
        sound.playUndo();
        onToast("Nicio combinatie noua din aceasta pereche.", "info");
      }
    } catch (err) {
      sound.playError();
      onToast(
        err instanceof ApiError
          ? err.message || `Combinatie respinsa (${err.status}).`
          : "Combinatie respinsa.",
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
      setSelected([]);
      setFreshIds(new Set());
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
  }, [state, busy, onToast]);

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
    () => selected.map((id) => inventory.find((i) => i.id === id)).filter(Boolean) as InventoryItem[],
    [selected, inventory],
  );

  if (loading || !state) {
    return (
      <div className="screen-pad fill center">
        <p className="muted">Se prepara alambicul…</p>
        <div className="row center" style={{ marginTop: 16 }}>
          <button type="button" className="btn btn-ghost" onClick={onExit}>
            ← Meniu
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="screen-pad fill" style={{ overflowY: "auto" }}>
      <div className="container col" style={{ gap: 18, paddingBottom: 32 }}>
        {/* Header */}
        <div className="row spread wrap" style={{ gap: 12 }}>
          <button type="button" className="btn btn-ghost" onClick={onExit}>
            ← Meniu
          </button>
          <div className="row wrap" style={{ gap: 8 }}>
            <span className="badge" style={{ borderColor: ACCENT, color: ACCENT }}>
              ⚗ Alchimie
            </span>
            <span className="badge">Combinari: {state.moves}</span>
            <span className="badge" style={{ borderColor: GOLD, color: GOLD }}>
              ✦ {state.discovered_count} descoperite
            </span>
          </div>
        </div>

        {/* Target */}
        <motion.div
          className="card"
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          style={{
            padding: 18,
            borderColor: won ? GOLD : ACCENT,
            boxShadow: won
              ? `0 0 50px -16px ${GOLD}`
              : `0 0 36px -20px ${ACCENT}`,
          }}
        >
          <div className="col" style={{ gap: 6 }}>
            <span className="faint" style={{ letterSpacing: "0.08em", fontSize: "0.72rem" }}>
              {won ? "TINTA CRAFTATA" : "TINTA DE CRAFTAT"}
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
        </motion.div>

        {/* Combine bench */}
        {!won && (
          <div
            className="card row spread wrap"
            style={{ padding: 14, gap: 12, alignItems: "center" }}
          >
            <div className="row wrap" style={{ gap: 8, alignItems: "center", minHeight: 38 }}>
              <Slot item={selectedItems[0]} />
              <span className="faint" style={{ fontSize: "1.4rem" }} aria-hidden>
                +
              </span>
              <Slot item={selectedItems[1]} />
            </div>
            <div className="row wrap" style={{ gap: 8 }}>
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
                disabled={busy || selected.length !== 2}
                onClick={doCombine}
                style={{ borderColor: ACCENT }}
              >
                {busy ? "…" : "⚗ Combina"}
              </button>
            </div>
          </div>
        )}

        {/* Last combine feedback */}
        <AnimatePresence mode="wait">
          {lastMessage && (
            <motion.p
              key={lastMessage + state.moves}
              className="muted center"
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              style={{ margin: 0, fontSize: "0.92rem" }}
            >
              {lastMessage}
            </motion.p>
          )}
        </AnimatePresence>

        {/* Inventory */}
        <div className="col" style={{ gap: 8 }}>
          <span className="faint" style={{ letterSpacing: "0.06em", fontSize: "0.72rem" }}>
            INVENTAR ({inventory.length})
          </span>
          <div className="wrap" style={{ display: "flex", gap: 8 }}>
            <AnimatePresence initial={false}>
              {inventory.map((item) => {
                const isSel = selected.includes(item.id);
                const isFresh = freshIds.has(item.id);
                const isCrafted = item.parents !== null;
                const title = parentsOf(item) ?? "Concept de start";
                return (
                  <motion.button
                    key={item.id}
                    type="button"
                    layout
                    initial={isFresh ? { scale: 0.4, opacity: 0 } : false}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ type: "spring", stiffness: 320, damping: 18 }}
                    onClick={() => toggle(item.id)}
                    disabled={won || busy}
                    title={title}
                    className="chip"
                    style={{
                      cursor: won ? "default" : "pointer",
                      borderColor: isSel
                        ? ACCENT
                        : isFresh
                          ? GOLD
                          : isCrafted
                            ? "var(--border)"
                            : "var(--border)",
                      background: isSel
                        ? "color-mix(in srgb, var(--panel) 70%, " + ACCENT + ")"
                        : isFresh
                          ? "color-mix(in srgb, var(--panel) 80%, " + GOLD + ")"
                          : undefined,
                      color: isSel || isFresh ? "var(--text)" : undefined,
                      fontWeight: isCrafted ? 600 : 500,
                      boxShadow: isFresh ? `0 0 16px -4px ${GOLD}` : undefined,
                    }}
                  >
                    {isCrafted ? "✦ " : ""}
                    {item.label}
                  </motion.button>
                );
              })}
            </AnimatePresence>
          </div>
        </div>

        {/* Footer actions */}
        <div className="row center wrap" style={{ gap: 12, marginTop: 8 }}>
          <button type="button" className="btn btn-ghost" disabled={busy} onClick={doReset}>
            ↻ Reia (acelasi joc)
          </button>
          <button type="button" className="btn btn-ghost" disabled={busy} onClick={() => void start()}>
            ⚂ Joc nou
          </button>
        </div>

        {/* Win banner */}
        <AnimatePresence>
          {won && (
            <motion.div
              className="card center"
              initial={{ scale: 0.85, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ type: "spring", stiffness: 240, damping: 18 }}
              style={{
                padding: 22,
                textAlign: "center",
                borderColor: GOLD,
                boxShadow: `0 0 60px -18px ${GOLD}`,
              }}
            >
              <div style={{ fontSize: "2.4rem" }} aria-hidden>
                ★
              </div>
              <h2 style={{ margin: "6px 0", color: GOLD }}>Ai craftat tinta!</h2>
              <p className="muted" style={{ margin: 0 }}>
                <strong style={{ color: "var(--text)" }}>{state.target.label}</strong> in{" "}
                {state.moves} combinari · {state.discovered_count} concepte descoperite.
              </p>
              <div className="row center wrap" style={{ gap: 12, marginTop: 16 }}>
                <button type="button" className="btn btn-primary" onClick={() => void start()}>
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

function Slot({ item }: { item: InventoryItem | undefined }) {
  if (!item) {
    return (
      <span
        className="chip faint"
        style={{ borderStyle: "dashed", minWidth: 90, justifyContent: "center" }}
      >
        alege…
      </span>
    );
  }
  return (
    <span className="chip" style={{ borderColor: ACCENT, color: "var(--text)" }}>
      {item.parents ? "✦ " : ""}
      {item.label}
    </span>
  );
}
