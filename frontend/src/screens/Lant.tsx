import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Button, Spinner, type ToastKind } from "@roedu/ui";
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
import { GameShell } from "../components/GameShell";
import { GameIntro } from "../components/GameIntro";
import { Hud, StatBadge } from "../components/Hud";
import { ResultCard } from "../components/ResultCard";
import { DifficultyPicker } from "../components/DifficultyPicker";
import { useRecordScore } from "../hooks/useRecordScore";
import { sound } from "../sound";
import { bestScore } from "../scores";
import { gameByKey } from "../games";
import { buildSharePayload, copyResult, stableKey, todayLocal } from "../share";

const GAME_KEY = "lant";
const DEF = gameByKey("lant");

const DIFFICULTIES: { key: Difficulty; label: string; hint: string }[] = [
  { key: "usor", label: "Usor", hint: "2-3 salturi" },
  { key: "normal", label: "Normal", hint: "3-4 salturi" },
  { key: "greu", label: "Greu", hint: "4-6 salturi" },
];

// Lantul Cuvintelor — a text-only word-ladder. The player types a concept directly
// linked to the CURRENT one, hopping toward the TARGET in as few moves as possible.
// All logic is server-authoritative; this screen only renders state + sends actions.

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
                      borderColor: DEF.accent,
                      color: DEF.accent,
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
  const [scored, setScored] = useState<{
    score: number;
    isBest: boolean;
    isPuzzleBest: boolean;
  } | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const best = useMemo(() => bestScore(GAME_KEY), []);
  const recordOnce = useRecordScore("lant");

  const puzzleKey = useMemo(() => {
    if (!state?.won) return null;
    return stableKey([
      GAME_KEY,
      state.daily ? `daily-${state.daily}` : state.difficulty,
      state.start.id,
      state.target.id,
      state.optimal,
    ]);
  }, [state]);

  const sharePayload = useMemo(() => {
    if (!state?.won || !state.share) return null;
    return buildSharePayload({
      gameTitle: "Lantul Cuvintelor",
      serverShare: state.share,
      score: state.score,
      puzzleKey,
    });
  }, [state, puzzleKey]);

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
    if (!state?.won || state.score === undefined) return;
    const detail = `${state.moves}/${state.optimal} mutari${
      state.daily ? ` · ${state.daily}` : ""
    }`;
    const outcome = recordOnce(state.game_id, state.score, detail, {
      puzzleKey,
      difficulty: state.difficulty,
      daily: state.daily,
    });
    if (!outcome) return;
    const { isBest, isPuzzleBest } = outcome;
    setScored({ score: state.score, isBest, isPuzzleBest });
    if (isBest || isPuzzleBest) sound.playRecord();
  }, [state, puzzleKey, recordOnce]);

  useEffect(() => {
    if (state && !state.won) inputRef.current?.focus();
  }, [state]);

  // On the win screen, Enter starts a fresh chain (keeps the keyboard flow going).
  useEffect(() => {
    if (!state?.won) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Enter") {
        e.preventDefault();
        setState(null);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [state?.won]);

  const won = state?.won ?? false;
  // Moves relative to par. Positive => still within/at optimal budget; negative => over par.
  const overPar = useMemo(() => {
    if (!state) return 0;
    return state.moves - state.optimal;
  }, [state]);
  // True distance left, learned from the most recent hint for THIS current node.
  const hintRemaining = hint?.hint && hint.remaining !== undefined ? hint.remaining : null;

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
    if (!sharePayload) return;
    const ok = await copyResult(sharePayload);
    if (ok) onToast("Copiat!", "info");
    else onToast("Nu am putut copia.", "error");
  }

  if (loading) {
    return (
      <div className="screen-pad fill center">
        <Spinner size="lg" label="Se incarca..." />
      </div>
    );
  }

  // Intro: difficulty picker + daily challenge.
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
            description={
              <p style={{ margin: 0 }}>
                Sari de la un concept la altul prin legaturi reale, pana la tinta.
                Cu cat mai putine salturi, cu atat scor mai mare.
              </p>
            }
            best={best}
            startLabel="Joaca →"
            onStart={() => void start({ difficulty })}
            onDaily={() => void start({ difficulty, daily: todayLocal() })}
            dailyLabel="Provocarea zilei"
            starting={loading}
          >
            <DifficultyPicker
              options={DIFFICULTIES.map((d) => ({ id: d.key, label: d.label, hint: d.hint }))}
              value={difficulty}
              onChange={(id) => {
                sound.playSelect();
                setDifficulty(id);
              }}
            />
          </GameIntro>
        </div>
      </div>
    );
  }

  return (
    <div className="screen-pad fill">
      <div className="container col" style={{ gap: 18 }}>
        {/* header */}
        <GameShell onExit={onExit} accent={DEF.accent} title={DEF.title}>
          <Hud>
            {state.daily && (
              <StatBadge
                label="ZI"
                value={state.daily}
                accent={DEF.accent}
                title="Provocarea zilei"
              />
            )}
            <StatBadge
              label="MUTARI"
              value={`${state.moves} ${state.moves === 1 ? "mutare" : "mutari"}`}
              accent={DEF.accent}
              title="Mutari facute"
            />
            <StatBadge
              label="OPTIM"
              value={<>{state.optimal}{overPar > 0 ? ` (+${overPar})` : ""}</>}
              accent={DEF.accent}
              title="Numarul minim de salturi"
            />
          </Hud>
        </GameShell>

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
                color: won ? TARGET_COLOR : DEF.accent,
                textShadow: `0 0 30px ${won ? TARGET_COLOR : DEF.accent}55`,
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
          <ResultCard
            icon={state.moves <= state.optimal ? "★" : "✦"}
            title={state.moves <= state.optimal ? "Lant perfect!" : "Ai reusit!"}
            accent={TARGET_COLOR}
            score={state.score}
            isRecord={scored?.isBest ?? false}
            isPuzzleRecord={scored?.isPuzzleBest ?? false}
            shareText={sharePayload}
            onCopy={() => void handleCopy()}
            onReplay={() => setState(null)}
            onExit={onExit}
            replayLabel="Lant nou →"
          >
            Ai ajuns la <strong style={{ color: "var(--text)" }}>{state.target.label}</strong>{" "}
            in <strong style={{ color: "var(--text)" }}>{state.moves}</strong> salturi (optim{" "}
            {state.optimal}).
          </ResultCard>
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
                className="field fill"
                placeholder="scrie urmatorul concept…"
                value={text}
                disabled={busy}
                onChange={(e) => setText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") void submit();
                  else if (e.key === "Escape") setText("");
                }}
                autoComplete="off"
                autoCapitalize="off"
                autoCorrect="off"
                spellCheck={false}
                enterKeyHint="send"
                aria-label="Urmatorul concept"
                style={{ flex: 1 }}
              />
              <Button
                type="button"
                disabled={busy || !text.trim()}
                onClick={() => void submit()}
              >
                {busy ? "…" : "Salt"}
              </Button>
            </div>

            <div className="row wrap" style={{ gap: 8 }}>
              <Button
                type="button"
                variant="secondary"
                disabled={busy || state.moves === 0}
                onClick={() => void handleUndo()}
              >
                ↶ Inapoi
              </Button>
              <Button
                type="button"
                variant="secondary"
                disabled={busy}
                onClick={() => void handleHint()}
              >
                💡 Indiciu
              </Button>
              <span className="muted" style={{ alignSelf: "center" }}>
                {hintRemaining !== null
                  ? hintRemaining <= 1
                    ? "esti la un pas de tinta!"
                    : `${hintRemaining} salturi pana la tinta`
                  : overPar > 0
                    ? `peste par cu ${overPar} — incearca ↶ Inapoi`
                    : `tinta la ~${state.optimal - state.moves} salturi`}
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
                  <div className="col" style={{ gap: 4 }}>
                    <span className="muted" style={{ fontSize: "0.85rem" }}>
                      Incearca:{" "}
                      <button
                        type="button"
                        title="Pune in casuta"
                        onClick={() => {
                          if (hint.hint) setText(hint.hint.label);
                          inputRef.current?.focus();
                        }}
                        style={{
                          background: "none",
                          border: "none",
                          padding: 0,
                          font: "inherit",
                          fontWeight: 700,
                          color: "var(--warn)",
                          cursor: "pointer",
                          textDecoration: "underline",
                        }}
                      >
                        {hint.hint.label}
                      </button>
                      {hint.relation ? (
                        <span className="faint"> ({hint.relation})</span>
                      ) : null}
                    </span>
                    {hint.alternatives && hint.alternatives > 1 ? (
                      <span className="faint" style={{ fontSize: "0.72rem" }}>
                        {hint.alternatives} variante bune de aici — exista mai multe
                        drumuri.
                      </span>
                    ) : null}
                  </div>
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
