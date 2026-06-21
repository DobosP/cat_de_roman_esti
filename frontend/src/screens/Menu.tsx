import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import type { CatalogCategory, GameState, Mode } from "../api/types";
import { api, ApiError } from "../api/client";
import { categoryStyle } from "../theme/tokens";
import { sound } from "../sound";
import { SoundToggle } from "../components/SoundToggle";
import { bestFor, bestRun } from "../leaderboard";

// Menu: animated category cards (from /api/catalog) + an easy/hard toggle with
// descriptions, and a Start button. The toggle exposes the contract's "4 levers"
// difference (hints + visible labels in easy; decoys + hidden labels in hard).

const MODE_INFO: Record<Mode, { title: string; blurb: string }> = {
  easy: {
    title: "Usor",
    blurb:
      "Etichete pe muchii, indiciu spre urmatorul salt, fara capcane. Reteaua te ghideaza.",
  },
  hard: {
    title: "Greu",
    blurb:
      "Muchii fara etichete, fara indicii si cu momeli care par reale. Doar instinctul tau.",
  },
};

export function Menu({
  onStart,
  onError,
}: {
  onStart: (game: GameState) => void;
  onError: (message: string) => void;
}) {
  const [catalog, setCatalog] = useState<CatalogCategory[] | null>(null);
  const [source, setSource] = useState<string>("");
  const [selected, setSelected] = useState<string | null>(null);
  const [mode, setMode] = useState<Mode>("easy");
  const [loading, setLoading] = useState(false);
  const [fetchErr, setFetchErr] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    api
      .getCatalog()
      .then((res) => {
        if (!alive) return;
        setCatalog(res.categories);
        setSource(res.source);
        // default-select the first category that has a puzzle for some mode
        const first = res.categories.find((c) => c.easy + c.hard > 0);
        if (first) setSelected(first.category);
      })
      .catch((err: unknown) => {
        if (!alive) return;
        const msg =
          err instanceof ApiError
            ? `Catalogul nu a putut fi incarcat (${err.status}).`
            : "Catalogul nu a putut fi incarcat. Porneste serverul BFF.";
        setFetchErr(msg);
      });
    return () => {
      alive = false;
    };
  }, []);

  const selectedRow = catalog?.find((c) => c.category === selected) ?? null;
  const availableForMode = selectedRow ? selectedRow[mode] : 0;
  const canStart = !!selected && availableForMode > 0 && !loading;

  // Offline personal bests (localStorage): best for the current selection + best run.
  const best = selected ? bestFor(selected, mode) : null;
  const run = bestRun();

  async function handleStart() {
    if (!selected) return;
    // The Start click is a user gesture — ensure the audio context is unlocked so the
    // hop/win blips can play once we're in the game.
    sound.unlockAudio();
    setLoading(true);
    try {
      const game = await api.createGame(selected, mode);
      sound.playSelect();
      onStart(game);
    } catch (err) {
      const msg =
        err instanceof ApiError
          ? err.status === 404
            ? "Nu exista nicio enigma pentru aceasta alegere."
            : `Nu am putut porni jocul (${err.status}).`
          : "Nu am putut porni jocul. Verifica serverul.";
      onError(msg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="screen-pad fill" style={{ overflowY: "auto" }}>
      <div className="container col" style={{ gap: 28, paddingBlock: 12 }}>
        <header className="col" style={{ gap: 10 }}>
          <div className="row spread" style={{ gap: 12, alignItems: "flex-start" }}>
            <motion.h1
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
            style={{ fontSize: "clamp(2rem, 5vw, 3.4rem)", lineHeight: 1.02 }}
          >
            cat de roman{" "}
            <span
              style={{
                background: "linear-gradient(120deg, var(--accent), var(--accent-2))",
                WebkitBackgroundClip: "text",
                backgroundClip: "text",
                color: "transparent",
              }}
            >
              esti
            </span>
            ?
            </motion.h1>
            <SoundToggle />
          </div>
          <motion.p
            className="muted"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.15, duration: 0.5 }}
            style={{ maxWidth: 640, fontSize: "1.05rem", margin: 0 }}
          >
            Navigheaza reteaua semantica a culturii romanesti. Sari din concept
            in concept, de la START la TINTA, in cat mai putine salturi.
            {source && (
              <span className="faint">
                {"  "}· sursa: {source === "live" ? "server live" : "offline"}
              </span>
            )}
          </motion.p>
        </header>

        {/* mode toggle */}
        <div className="col" style={{ gap: 10 }}>
          <span className="muted" style={{ fontSize: "0.85rem" }}>
            Dificultate
          </span>
          <div className="row wrap" style={{ gap: 14 }}>
            {(["easy", "hard"] as Mode[]).map((m) => {
              const active = mode === m;
              return (
                <motion.button
                  key={m}
                  type="button"
                  onClick={() => {
                    if (m !== mode) sound.playSelect();
                    setMode(m);
                  }}
                  whileTap={{ scale: 0.98 }}
                  aria-pressed={active}
                  className="card"
                  style={{
                    flex: "1 1 200px",
                    minWidth: 0,
                    textAlign: "left",
                    padding: 16,
                    cursor: "pointer",
                    borderColor: active
                      ? m === "hard"
                        ? "var(--bad)"
                        : "var(--good)"
                      : "var(--surface-border)",
                    boxShadow: active
                      ? `0 0 26px -10px ${m === "hard" ? "#ff5d6c" : "#5fd99b"}`
                      : "var(--shadow-card)",
                  }}
                >
                  <div className="row spread">
                    <strong style={{ fontFamily: "var(--font-display)" }}>
                      {MODE_INFO[m].title}
                    </strong>
                    <span
                      aria-hidden
                      style={{
                        width: 16,
                        height: 16,
                        borderRadius: "50%",
                        border: `2px solid ${
                          active
                            ? m === "hard"
                              ? "var(--bad)"
                              : "var(--good)"
                            : "var(--text-faint)"
                        }`,
                        background: active
                          ? m === "hard"
                            ? "var(--bad)"
                            : "var(--good)"
                          : "transparent",
                      }}
                    />
                  </div>
                  <p
                    className="muted"
                    style={{ margin: "8px 0 0", fontSize: "0.88rem" }}
                  >
                    {MODE_INFO[m].blurb}
                  </p>
                </motion.button>
              );
            })}
          </div>
        </div>

        {/* category cards */}
        <div className="col" style={{ gap: 10 }}>
          <span className="muted" style={{ fontSize: "0.85rem" }}>
            Categorie
          </span>

          {fetchErr && (
            <div
              className="card"
              style={{ padding: 18, borderColor: "var(--bad)" }}
            >
              <strong>{fetchErr}</strong>
            </div>
          )}

          {!catalog && !fetchErr && (
            <div className="muted" style={{ padding: 18 }}>
              Se incarca categoriile…
            </div>
          )}

          <div
            style={{
              display: "grid",
              gridTemplateColumns:
                "repeat(auto-fill, minmax(min(100%, 200px), 1fr))",
              gap: 14,
            }}
          >
            {catalog?.map((cat, i) => {
              const style = categoryStyle(cat.category);
              const active = selected === cat.category;
              const count = cat[mode];
              const empty = count === 0;
              return (
                <motion.button
                  key={cat.category}
                  type="button"
                  disabled={empty}
                  onClick={() => {
                    if (cat.category !== selected) sound.playSelect();
                    setSelected(cat.category);
                  }}
                  initial={{ opacity: 0, y: 18 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.05 * i, duration: 0.4 }}
                  whileHover={empty ? undefined : { y: -4 }}
                  whileTap={empty ? undefined : { scale: 0.98 }}
                  aria-pressed={active}
                  className="card"
                  style={{
                    textAlign: "left",
                    padding: 18,
                    cursor: empty ? "not-allowed" : "pointer",
                    opacity: empty ? 0.4 : 1,
                    position: "relative",
                    overflow: "hidden",
                    borderColor: active ? style.color : "var(--surface-border)",
                    boxShadow: active
                      ? `0 0 30px -8px ${style.color}, var(--shadow-card)`
                      : "var(--shadow-card)",
                  }}
                >
                  <div
                    aria-hidden
                    style={{
                      position: "absolute",
                      inset: 0,
                      background: `radial-gradient(120px 80px at 100% 0%, ${style.glow}22, transparent 70%)`,
                      opacity: active ? 1 : 0.5,
                      pointerEvents: "none",
                    }}
                  />
                  <div className="row spread" style={{ position: "relative" }}>
                    <span
                      style={{
                        fontFamily: "var(--font-display)",
                        fontWeight: 700,
                        fontSize: "1.12rem",
                        color: style.color,
                      }}
                    >
                      {cat.label || style.label}
                    </span>
                    <span
                      aria-hidden
                      style={{
                        width: 12,
                        height: 12,
                        borderRadius: "50%",
                        background: style.color,
                        boxShadow: `0 0 12px ${style.color}`,
                      }}
                    />
                  </div>
                  <p
                    className="muted"
                    style={{
                      margin: "8px 0 12px",
                      fontSize: "0.86rem",
                      position: "relative",
                    }}
                  >
                    {style.blurb}
                  </p>
                  <div
                    className="row"
                    style={{ gap: 8, position: "relative", alignItems: "center" }}
                  >
                    {/* Per-difficulty counts (strict, from /api/catalog). The chip for
                        the ACTIVE difficulty is emphasised; the inactive one is dimmed. */}
                    <span
                      className="chip"
                      style={{
                        fontSize: "0.76rem",
                        opacity: mode === "easy" ? 1 : 0.45,
                        borderColor:
                          mode === "easy" ? "var(--good)" : "var(--surface-border)",
                        fontWeight: mode === "easy" ? 600 : 400,
                      }}
                    >
                      {cat.easy} usor
                    </span>
                    <span
                      className="chip"
                      style={{
                        fontSize: "0.76rem",
                        opacity: mode === "hard" ? 1 : 0.45,
                        borderColor:
                          mode === "hard" ? "var(--bad)" : "var(--surface-border)",
                        fontWeight: mode === "hard" ? 600 : 400,
                      }}
                    >
                      {cat.hard} greu
                    </span>
                    {empty && (
                      <span
                        className="faint"
                        style={{ fontSize: "0.74rem", marginLeft: 2 }}
                      >
                        fără puzzle-uri
                      </span>
                    )}
                  </div>
                </motion.button>
              );
            })}
          </div>
        </div>

        {/* personal records (offline, localStorage) */}
        {(best || run.total > 0) && (
          <div className="row wrap" style={{ gap: 10, alignItems: "center" }}>
            <span className="muted" style={{ fontSize: "0.82rem" }}>
              Recorduri
            </span>
            {best && (
              <span
                className="badge"
                title="Cel mai bun rezultat al tau pentru aceasta categorie si dificultate"
                style={{ borderColor: "var(--warn)", color: "var(--warn)" }}
              >
                ★ {best.score} pct · {best.hops}/par {best.par}
              </span>
            )}
            {run.total > 0 && (
              <span className="badge" title="Cea mai buna sesiune (enigme rezolvate la rand)">
                ✓ sesiune: {run.solved} enigme · {run.total} pct
              </span>
            )}
          </div>
        )}

        {/* start */}
        <div className="row" style={{ gap: 14, paddingBottom: 24 }}>
          <motion.button
            type="button"
            className="btn btn-primary"
            disabled={!canStart}
            onClick={handleStart}
            whileTap={canStart ? { scale: 0.97 } : undefined}
            style={{ fontSize: "1.05rem", padding: "14px 28px" }}
          >
            {loading ? "Se porneste…" : "Incepe jocul"}
          </motion.button>
          {selected && availableForMode === 0 && (
            <span className="muted" style={{ fontSize: "0.88rem" }}>
              fără puzzle-uri {mode === "hard" ? "grele" : "usoare"} aici — alege
              alta categorie sau dificultate.
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
