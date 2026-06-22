import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  type Difficulty,
  type HintResult,
  type LantState,
  type PathStep,
  createLant,
  hintLant,
  moveLant,
  undoLant,
} from "../api/lant";
import { ApiError } from "../api/client";
import type { ToastKind } from "../components/Toast";
import { sound } from "../sound";
import { bestScore, recordScore } from "../scores";
import { copyResult, todayLocal } from "../share";

const GAME_KEY = "lant";

const DIFFICULTIES: { key: Difficulty; label: string; hint: string }[] = [
  { key: "usor", label: "Usor", hint: "2-3 salturi" },
  { key: "normal", label: "Normal", hint: "3-4 salturi" },
  { key: "greu", label: "Greu", hint: "4-6 salturi" },
];

// Lantul Cuvintelor — a text-only word-ladder. The player types a concept directly
// linked to the CURRENT one, hopping toward the TARGET in as few moves as possible.
// All logic is server-authoritative; this screen only renders state + sends actions.

const ACCENT = "#56d4dd"; // teal "chain" accent
const TARGET_COLOR = "#f178b6";

function Breadcrumb({ path }: { path: PathStep[] }) {
  return (
    <div className="row wrap" style={{ gap: 6, alignItems: "center" }}>
      <AnimatePresence initial={false}>
        {path.map((step, i) => (
          <motion.span
            key={`${step.id}-${i}`}
            layout
            initial={{ opacity: 0, scale: 0.8, y: -6 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ type: "spring", stiffness: 420, damping: 26 }}
            className="row"
            style={{ gap: 6, alignItems: "center" }}
          >
            {i > 0 && (
              <span
                className="faint"
                style={{ fontSize: "0.7rem", whiteSpace: "nowrap" }}
                title={step.relation}
              >
                ―{step.relation ? ` ${step.relation} →` : " →"}
              </span>
            )}
            <span
              className="chip"
              style={
                i === path.length - 1
                  ? {
                      borderColor: ACCENT,
                      color: ACCENT,
                      fontWeight: 700,
                    }
                  : undefined
              }
            >
              {step.label}
            </span>
          </motion.span>
        ))}
      </AnimatePresence>
    </div>
  );
}

export default function Lant({
  onExit,
  onToast,
}: {
  onExit: () => void;
  onToast: (message: string, kind?: ToastKind) => void;
}) {
  const [state, setState] = useState<LantState | null>(null);
  const [loading, setLoading] = useState(false);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [shake, setShake] = useState(0);
  const [hint, setHint] = useState<HintResult | null>(null);
  const [difficulty, setDifficulty] = useState<Difficulty>("normal");
  const [scored, setScored] = useState<{ score: number; isBest: boolean } | null>(
    null,
  );
  const inputRef = useRef<HTMLInputElement>(null);

  const best = useMemo(() => bestScore(GAME_KEY), []);

  const start = useCallback(
    async (opts?: { difficulty?: Difficulty; daily?: string }) => {
      setLoading(true);
      setHint(null);
      setScored(null);
      try {
        const fresh = await createLant({
          difficulty: opts?.difficulty ?? difficulty,
          daily: opts?.daily,
        });
        setState(fresh);
        setText("");
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
    [onToast, difficulty],
  );

  // Record the score exactly once when the game is won.
  useEffect(() => {
    if (!state?.won || state.score === undefined || scored) return;
    const detail = `${state.moves}/${state.optimal} mutari${
      state.daily ? ` · ${state.daily}` : ""
    }`;
    const { isBest } = recordScore(GAME_KEY, state.score, detail);
    setScored({ score: state.score, isBest });
    if (isBest) sound.playRecord();
  }, [state, scored]);

  useEffect(() => {
    if (state && !state.won) inputRef.current?.focus();
  }, [state]);

  const won = state?.won ?? false;
  const remaining = useMemo(() => {
    if (!state) return 0;
    return Math.max(0, state.optimal - state.moves);
  }, [state]);

  async function submit() {
    if (!state || busy || won) return;
    const value = text.trim();
    if (!value) return;
    setBusy(true);
    setHint(null);
    try {
      const res = await moveLant(state.game_id, value);
      if (!res.ok) {
        sound.playError();
        setShake((s) => s + 1);
        onToast(res.last_error ?? "Mutare invalida", "error");
        return;
      }
      // Successful hop: server returns the partial state — fold it into our full state.
      setState((prev) =>
        prev
          ? {
              ...prev,
              current: res.current ?? prev.current,
              path: res.path ?? prev.path,
              moves: res.moves ?? prev.moves,
              won: res.won ?? prev.won,
              score: res.score ?? prev.score,
              share: res.share ?? prev.share,
            }
          : prev,
      );
      setText("");
      if (res.won) {
        sound.playWin();
        onToast("Ai ajuns la tinta!", "success");
      } else {
        sound.playHop();
      }
    } catch (err) {
      onToast(
        err instanceof ApiError
          ? `Eroare server (${err.status}).`
          : "Eroare de retea.",
        "error",
      );
    } finally {
      setBusy(false);
    }
  }

  async function handleUndo() {
    if (!state || busy || state.moves === 0) return;
    setBusy(true);
    setHint(null);
    try {
      const fresh = await undoLant(state.game_id);
      setState(fresh);
      sound.playUndo();
      inputRef.current?.focus();
    } catch {
      onToast("Nu am putut anula.", "error");
    } finally {
      setBusy(false);
    }
  }

  async function handleHint() {
    if (!state || busy || won) return;
    setBusy(true);
    try {
      const res = await hintLant(state.game_id);
      setHint(res);
      if (res.hint) {
        sound.playSelect();
      } else {
        onToast(res.message ?? "Niciun indiciu.", "info");
      }
    } catch {
      onToast("Nu am putut obtine un indiciu.", "error");
    } finally {
      setBusy(false);
    }
  }

  async function handleCopy() {
    if (!state?.share) return;
    const ok = await copyResult(state.share);
    if (ok) onToast("Copiat!", "info");
    else onToast("Nu am putut copia.", "error");
  }

  if (loading) {
    return (
      <div className="screen-pad fill center">
        <p className="muted">Se pregateste lantul…</p>
      </div>
    );
  }

  // Intro: difficulty picker + daily challenge.
  if (!state) {
    return (
      <div className="screen-pad fill">
        <div className="container col" style={{ gap: 18 }}>
          <div className="spread row" style={{ alignItems: "center" }}>
            <button type="button" className="btn btn-ghost" onClick={onExit}>
              ← Meniu
            </button>
            {best && (
              <span className="badge" title="Cel mai bun scor">
                Record: {best.score}
              </span>
            )}
          </div>

          <motion.div
            className="card col"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            style={{ gap: 16, padding: 22 }}
          >
            <div className="col" style={{ gap: 4 }}>
              <h1
                style={{
                  margin: 0,
                  fontFamily: "var(--font-display)",
                  color: ACCENT,
                }}
              >
                Lantul Cuvintelor
              </h1>
              <p className="muted" style={{ margin: 0 }}>
                Sari de la un concept la altul prin legaturi reale, pana la tinta.
                Cu cat mai putine salturi, cu atat scor mai mare.
              </p>
            </div>

            <div className="col" style={{ gap: 8 }}>
              <span className="faint" style={{ fontSize: "0.72rem" }}>
                DIFICULTATE
              </span>
              <div className="row wrap" style={{ gap: 8 }}>
                {DIFFICULTIES.map((d) => (
                  <button
                    key={d.key}
                    type="button"
                    className={`btn ${
                      difficulty === d.key ? "btn-primary" : "btn-ghost"
                    }`}
                    onClick={() => setDifficulty(d.key)}
                  >
                    {d.label}
                    <span className="faint" style={{ marginLeft: 6, fontSize: "0.7rem" }}>
                      {d.hint}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            <div className="row wrap" style={{ gap: 12, marginTop: 4 }}>
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => void start({ difficulty })}
              >
                Joaca →
              </button>
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => void start({ difficulty, daily: todayLocal() })}
                title="Acelasi lant pentru toata lumea, azi"
              >
                ⭐ Provocarea zilei
              </button>
            </div>
          </motion.div>
        </div>
      </div>
    );
  }

  return (
    <div className="screen-pad fill">
      <div className="container col" style={{ gap: 18 }}>
        {/* header */}
        <div className="spread row" style={{ alignItems: "center" }}>
          <button type="button" className="btn btn-ghost" onClick={onExit}>
            ← Meniu
          </button>
          <div className="row" style={{ gap: 8 }}>
            {state.daily && (
              <span className="badge" title="Provocarea zilei">
                ⭐ {state.daily}
              </span>
            )}
            <span className="badge" title="Mutari facute">
              {state.moves} mutari
            </span>
            <span
              className="badge"
              style={{ borderColor: ACCENT, color: ACCENT }}
              title="Numarul minim de salturi"
            >
              optim {state.optimal}
            </span>
          </div>
        </div>

        {/* start -> target */}
        <div className="card col" style={{ gap: 12, padding: 18 }}>
          <div className="spread row wrap" style={{ gap: 12, alignItems: "center" }}>
            <div className="col" style={{ gap: 2 }}>
              <span className="faint" style={{ fontSize: "0.7rem" }}>
                START
              </span>
              <strong>{state.start.label}</strong>
            </div>
            <span className="muted" aria-hidden style={{ fontSize: "1.2rem" }}>
              ⟶
            </span>
            <div className="col" style={{ gap: 2, textAlign: "right" }}>
              <span className="faint" style={{ fontSize: "0.7rem" }}>
                TINTA
              </span>
              <strong style={{ color: TARGET_COLOR }}>
                {state.target.label}
              </strong>
            </div>
          </div>
          {state.target.description && (
            <p className="muted" style={{ margin: 0, fontSize: "0.85rem" }}>
              {state.target.description}
            </p>
          )}
        </div>

        {/* current concept — big */}
        <div className="col center" style={{ gap: 6 }}>
          <span className="faint" style={{ fontSize: "0.72rem" }}>
            EsTI ACUM LA
          </span>
          <AnimatePresence mode="wait">
            <motion.div
              key={state.current.id}
              initial={{ opacity: 0, y: 14, scale: 0.92 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ type: "spring", stiffness: 260, damping: 22 }}
              style={{
                fontFamily: "var(--font-display)",
                fontWeight: 800,
                fontSize: "clamp(1.8rem, 6vw, 3rem)",
                color: won ? TARGET_COLOR : ACCENT,
                textShadow: `0 0 30px ${won ? TARGET_COLOR : ACCENT}55`,
                lineHeight: 1.1,
                textAlign: "center",
              }}
            >
              {state.current.label}
            </motion.div>
          </AnimatePresence>
        </div>

        {/* input + actions OR win */}
        {won ? (
          <motion.div
            className="card center col"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ type: "spring", stiffness: 240, damping: 18 }}
            style={{
              gap: 12,
              padding: 24,
              borderColor: TARGET_COLOR,
              boxShadow: `0 0 50px -16px ${TARGET_COLOR}`,
            }}
          >
            <div style={{ fontSize: "2.4rem" }} aria-hidden>
              {state.moves <= state.optimal ? "★" : "✦"}
            </div>
            <h2 style={{ margin: 0 }}>
              {state.moves <= state.optimal ? "Lant perfect!" : "Ai reusit!"}
            </h2>
            <p className="muted" style={{ margin: 0 }}>
              Ai ajuns la <strong>{state.target.label}</strong> in{" "}
              <strong style={{ color: "var(--text)" }}>{state.moves}</strong>{" "}
              salturi (optim {state.optimal}).
            </p>

            {state.score !== undefined && (
              <div className="col center" style={{ gap: 4 }}>
                <span className="faint" style={{ fontSize: "0.72rem" }}>
                  SCOR
                </span>
                <div
                  style={{
                    fontFamily: "var(--font-display)",
                    fontWeight: 800,
                    fontSize: "2rem",
                    color: TARGET_COLOR,
                  }}
                >
                  {state.score}
                </div>
                {scored?.isBest && (
                  <motion.span
                    className="badge"
                    initial={{ scale: 0.6, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    style={{ borderColor: TARGET_COLOR, color: TARGET_COLOR }}
                  >
                    🏆 Record!
                  </motion.span>
                )}
              </div>
            )}

            <div className="row wrap center" style={{ gap: 12, marginTop: 4 }}>
              {state.share && (
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => void handleCopy()}
                >
                  Copiaza rezultatul
                </button>
              )}
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => setState(null)}
              >
                Lant nou →
              </button>
              <button type="button" className="btn btn-ghost" onClick={onExit}>
                Meniu
              </button>
            </div>
          </motion.div>
        ) : (
          <motion.div
            key={shake}
            animate={shake ? { x: [0, -8, 8, -6, 6, 0] } : {}}
            transition={{ duration: 0.32 }}
            className="col"
            style={{ gap: 10 }}
          >
            <div className="row" style={{ gap: 8 }}>
              <input
                ref={inputRef}
                className="fill"
                placeholder="scrie urmatorul concept…"
                value={text}
                disabled={busy}
                onChange={(e) => setText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") void submit();
                }}
                style={{
                  flex: 1,
                  padding: "12px 14px",
                  borderRadius: 12,
                  border: "1px solid var(--border)",
                  background: "var(--surface)",
                  color: "var(--text)",
                  fontSize: "1rem",
                }}
              />
              <button
                type="button"
                className="btn btn-primary"
                disabled={busy || !text.trim()}
                onClick={() => void submit()}
              >
                {busy ? "…" : "Salt"}
              </button>
            </div>

            <div className="row wrap" style={{ gap: 8 }}>
              <button
                type="button"
                className="btn btn-ghost"
                disabled={busy || state.moves === 0}
                onClick={() => void handleUndo()}
              >
                ↶ Inapoi
              </button>
              <button
                type="button"
                className="btn btn-ghost"
                disabled={busy}
                onClick={() => void handleHint()}
              >
                💡 Indiciu
              </button>
              <span className="muted" style={{ alignSelf: "center" }}>
                {remaining > 0
                  ? `~${remaining} salturi pe drumul cel scurt`
                  : "esti la un pas!"}
              </span>
            </div>

            <AnimatePresence>
              {hint?.hint && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="card"
                  style={{ padding: 12, borderColor: "var(--warn)" }}
                >
                  <span className="muted" style={{ fontSize: "0.85rem" }}>
                    Incearca:{" "}
                    <strong
                      style={{ color: "var(--warn)", cursor: "pointer" }}
                      onClick={() => {
                        if (hint.hint) setText(hint.hint.label);
                        inputRef.current?.focus();
                      }}
                    >
                      {hint.hint.label}
                    </strong>
                    {hint.relation ? (
                      <span className="faint"> ({hint.relation})</span>
                    ) : null}
                  </span>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}

        {/* path breadcrumb */}
        <div className="col" style={{ gap: 6 }}>
          <span className="faint" style={{ fontSize: "0.72rem" }}>
            DRUMUL TAU
          </span>
          <Breadcrumb path={state.path} />
        </div>
      </div>
    </div>
  );
}
