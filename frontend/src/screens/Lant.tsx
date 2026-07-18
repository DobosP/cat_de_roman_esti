import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, m } from "framer-motion";
import { Button, Spinner, type ToastKind } from "@roedu/ui";
import {
  type Difficulty,
  type HintResult,
  type LantChoice,
  type LantProgress,
  type LantState,
  type PathStep,
  createLant,
  getLant,
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
import { NextMove } from "../components/PlayGuide";
import { useActiveGame } from "../hooks/useActiveGame";
import { useRecordScore } from "../hooks/useRecordScore";
import { sound } from "../sound";
import { bestScore } from "../scores";
import { gameByKey } from "../games";
import { categoryColor, categoryLabel } from "../categories";
import { CategoryPicker } from "../components/CategoryPicker";
import { buildSharePayload, copyResult, stableKey, todayLocal } from "../share";

const GAME_KEY = "lant";
const DEF = gameByKey("lant");

const DIFFICULTIES: { key: Difficulty; label: string; hint: string }[] = [
  { key: "usor", label: "Ușor", hint: "recomandat" },
  { key: "normal", label: "Normal", hint: "3–4 salturi" },
  { key: "greu", label: "Greu", hint: "4–6 salturi" },
];

// Lanțul Cuvintelor — a text-only word-ladder. The player types a concept directly
// linked to the CURRENT one, hopping toward the TARGET in as few moves as possible.
// All logic is server-authoritative; this screen only renders state + sends actions.

const TARGET_COLOR = "#f178b6";

const PROGRESS_ICON: Record<LantProgress["kind"], string> = {
  closer: "↗",
  lateral: "↔",
  farther: "↘",
  dead_end: "↶",
  won: "✓",
};

type RecoveryFeedback = {
  message: string;
  choices: string[];
  tone: "info" | "warning";
};

function Breadcrumb({ path }: { path: PathStep[] }) {
  return (
    <div className="row wrap breadcrumb-trail" style={{ gap: 6, alignItems: "center" }}>
      <AnimatePresence initial={false}>
        {path.map((step, i) => (
          <m.span
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
          </m.span>
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
  const active = useActiveGame(GAME_KEY);
  const [state, setState] = useState<LantState | null>(null);
  const [loading, setLoading] = useState(() => active.peek() !== null);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [shake, setShake] = useState(0);
  const [hint, setHint] = useState<HintResult | null>(null);
  const [progress, setProgress] = useState<LantProgress | null>(null);
  const [recovery, setRecovery] = useState<RecoveryFeedback | null>(null);
  const [difficulty, setDifficulty] = useState<Difficulty>("usor");
  const [category, setCategory] = useState<string | null>(null);
  const [scored, setScored] = useState<{
    score: number;
    isBest: boolean;
    isPuzzleBest: boolean;
  } | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const resumeTried = useRef(false);

  const focusInputForFinePointer = useCallback(() => {
    if (window.matchMedia("(pointer: fine)").matches) {
      inputRef.current?.focus();
    }
  }, []);

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
      state.board_category,
    ]);
  }, [state]);

  const sharePayload = useMemo(() => {
    if (!state?.won || !state.share) return null;
    return buildSharePayload({
      gameTitle: "Lanțul Cuvintelor",
      serverShare: state.share,
      score: state.score,
      puzzleKey,
    });
  }, [state, puzzleKey]);

  const start = useCallback(
    async (opts?: { difficulty?: Difficulty; daily?: string }) => {
      setLoading(true);
      setHint(null);
      setProgress(null);
      setRecovery(null);
      setScored(null);
      try {
        const fresh = await createLant({
          difficulty: opts?.difficulty ?? difficulty,
          daily: opts?.daily,
          // The theme applies to picked games only; the daily stays the shared classic.
          category: opts?.daily ? undefined : (category ?? undefined),
        });
        active.remember(fresh.game_id);
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
    [onToast, difficulty, category, active],
  );

  useEffect(() => {
    if (resumeTried.current) return;
    resumeTried.current = true;
    const id = active.peek();
    if (!id) return;

    setLoading(true);
    void (async () => {
      try {
        const fresh = await getLant(id);
        if (fresh.won) {
          active.forget();
          return;
        }
        setHint(null);
        setProgress(null);
        setScored(null);
        setDifficulty(fresh.difficulty);
        setCategory(fresh.board_category ?? null);
        setState(fresh);
        setText("");
        onToast("Joc reluat.", "info");
      } catch {
        active.forget();
      } finally {
        setLoading(false);
      }
    })();
  }, [active, onToast]);

  // Record the score exactly once when the game is won.
  useEffect(() => {
    if (!state?.won || state.score === undefined) return;
    active.forget();
    const detail = `${state.moves}/${state.optimal} mutări${
      state.daily ? ` · ${state.daily}` : ""
    }`;
    const outcome = recordOnce(state.game_id, state.score, detail, {
      puzzleKey,
      difficulty: state.difficulty,
      daily: state.daily,
      category: state.board_category,
    });
    if (!outcome) return;
    const { isBest, isPuzzleBest } = outcome;
    setScored({ score: state.score, isBest, isPuzzleBest });
    if (isBest || isPuzzleBest) sound.playRecord();
  }, [state, puzzleKey, recordOnce, active]);

  useEffect(() => {
    // Do not summon the phone keyboard over the new tap-first local choices.
    if (state && !state.won) focusInputForFinePointer();
  }, [state, focusInputForFinePointer]);

  // On the win screen, Enter starts another chain with the same free-play filters.
  useEffect(() => {
    if (!state?.won) return;
    const onKey = (e: KeyboardEvent) => {
      const target = e.target instanceof Element ? e.target : null;
      if (
        e.defaultPrevented ||
        target?.closest('button, a, input, textarea, select, [role="button"], [contenteditable="true"]')
      ) {
        return;
      }
      if (e.key === "Enter") {
        e.preventDefault();
        void start({ difficulty: state.difficulty });
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [state?.won, state?.difficulty, start]);

  const won = state?.won ?? false;
  // Moves spent beyond the optimal path length from the original start.
  const overPar = useMemo(() => {
    if (!state) return 0;
    return state.moves - state.optimal;
  }, [state]);
  // True distance left, learned from the most recent hint for THIS current node.
  const hintRemaining = hint?.remaining ?? null;

  async function submit(choice?: LantChoice) {
    if (!state || busy || won) return;
    const value = (choice?.label ?? text).trim();
    if (!value) return;
    setBusy(true);
    setHint(null);
    setProgress(null);
    setRecovery(null);
    try {
      const res = await moveLant(state.game_id, value);
      if (!res.ok) {
        sound.playError();
        setShake((s) => s + 1);
        const message = res.last_error ?? "Mutare invalidă";
        setRecovery({
          message,
          choices: res.suggestions ?? [],
          tone: "warning",
        });
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
              choices: res.choices ?? prev.choices,
              backtrack_recommended:
                res.backtrack_recommended ?? prev.backtrack_recommended,
            }
          : prev,
      );
      setProgress(res.progress ?? null);
      setText("");
      if (res.message) {
        setRecovery({
          message: res.message,
          choices: [],
          tone: res.dead_end ? "warning" : "info",
        });
      }
      if (res.won) {
        sound.playWin();
        onToast("Ai ajuns la țintă!", "success");
      } else {
        sound.playHop();
      }
    } catch (err) {
      onToast(
        err instanceof ApiError
          ? `Eroare server (${err.status}).`
          : "Eroare de rețea.",
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
    setProgress(null);
    setRecovery(null);
    try {
      const fresh = await undoLant(state.game_id);
      setState(fresh);
      sound.playUndo();
      focusInputForFinePointer();
    } catch {
      onToast("Nu am putut anula.", "error");
    } finally {
      setBusy(false);
    }
  }

  async function handleHint() {
    if (!state || busy || won) return;
    setBusy(true);
    setRecovery(null);
    try {
      const res = await hintLant(state.game_id);
      setHint(res);
      if (res.hint || res.stage) {
        sound.playSelect();
      } else {
        const message = res.message ?? "Niciun indiciu.";
        setRecovery({ message, choices: [], tone: "warning" });
      }
    } catch {
      onToast("Nu am putut obține un indiciu.", "error");
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
        <Spinner size="lg" label="Se încarcă…" />
      </div>
    );
  }

  // Intro: difficulty picker + daily challenge.
  if (!state) {
    return (
      <div className="screen-pad fill">
        <div className="container col game-container" style={{ gap: 18 }}>
          <GameShell onExit={onExit} accent={DEF.accent} />

          <GameIntro
            icon={DEF.icon}
            title={DEF.title}
            tag={DEF.tag}
            accent={DEF.accent}
            glow={DEF.glow}
            description={
              <p style={{ margin: 0 }}>
                Ajungi la țintă prin concepte legate direct.
              </p>
            }
            steps={[
              { icon: "👆", label: "Alege o legătură" },
              { icon: "🔗", label: "Fă un salt" },
              { icon: "🎯", label: "Ajungi la țintă" },
            ]}
            best={best}
            startLabel="Joacă →"
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
            <CategoryPicker
              game="lant"
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
    <div className="screen-pad fill">
      <div className="container col game-container" style={{ gap: 18 }}>
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
            {state.board_category && (
              <StatBadge
                label="CATEGORIE"
                value={categoryLabel(state.board_category)}
                accent={categoryColor(state.board_category)}
              />
            )}
            <StatBadge
              label="MUTĂRI"
              value={`${state.moves} ${state.moves === 1 ? "mutare" : "mutări"}`}
              accent={DEF.accent}
              title="Mutări făcute"
            />
            <StatBadge
              label="REPER"
              value={<>{state.optimal} salturi{overPar > 0 ? ` (+${overPar})` : ""}</>}
              accent={DEF.accent}
              title="Numărul minim de salturi"
            />
          </Hud>
        </GameShell>

        {/* start -> target */}
        <div className="card col route-card" style={{ gap: 12, padding: 18 }}>
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
                ȚINTĂ
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
            EȘTI ACUM LA
          </span>
          <AnimatePresence mode="wait">
            <m.div
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
            </m.div>
          </AnimatePresence>
        </div>

        {!won && (
          <NextMove
            icon="🔗"
            title={`Leagă-te de ${state.current.label}`}
            detail="Alege o sugestie sau scrie alt vecin."
            progress={`→ ${state.target.label}`}
            accent={DEF.accent}
          />
        )}

        {!won && state.choices?.length > 0 ? (
          <section className="lant-choice-panel col" aria-labelledby="lant-choice-title">
            <div className="spread row" style={{ gap: 10, alignItems: "baseline" }}>
              <strong id="lant-choice-title">Salturi de aici</strong>
              <span className="faint">toate sunt legături valide</span>
            </div>
            <div className="lant-choice-grid">
              {state.choices.map((choice) => (
                <button
                  key={`${choice.label}-${choice.relation}`}
                  type="button"
                  className="lant-choice"
                  disabled={busy}
                  aria-label={`Salt la ${choice.label}: ${choice.relation}`}
                  onClick={() => void submit(choice)}
                >
                  <strong>{choice.label}</strong>
                  <span>{choice.relation}</span>
                </button>
              ))}
            </div>
          </section>
        ) : null}

        {progress ? (
          <m.div
            key={progress.kind + "-" + state.moves}
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            className={"lant-progress lant-progress--" + progress.kind}
            role="status"
            aria-live="polite"
          >
            <span aria-hidden="true">{PROGRESS_ICON[progress.kind]}</span>
            <strong>{progress.message}</strong>
          </m.div>
        ) : null}

        <span
          className="visually-hidden"
          role="status"
          aria-live="polite"
          aria-atomic="true"
        >
          {recovery?.message ?? ""}
        </span>

        {/* input + actions OR win */}
        {won ? (
          <ResultCard
            icon={state.moves <= state.optimal ? "★" : "✦"}
            title={state.moves <= state.optimal ? "Lanț perfect!" : "Ai reușit!"}
            accent={TARGET_COLOR}
            score={state.score}
            isRecord={scored?.isBest ?? false}
            isPuzzleRecord={scored?.isPuzzleBest ?? false}
            shareText={sharePayload}
            onCopy={() => void handleCopy()}
            onReplay={() => void start({ difficulty: state.difficulty })}
            onOptions={() => {
              active.forget();
              setState(null);
            }}
            onExit={onExit}
            replayLabel="Încă un lanț →"
          >
            Ai ajuns la <strong style={{ color: "var(--text)" }}>{state.target.label}</strong>{" "}
            în <strong style={{ color: "var(--text)" }}>{state.moves}</strong> salturi (optim{" "}
            {state.optimal}).
            {recovery?.message ? (
              <span className="muted" style={{ display: "block", marginTop: 8 }}>
                <span aria-hidden="true" style={{ marginRight: 6 }}>
                  ℹ
                </span>
                {recovery.message}
              </span>
            ) : null}
          </ResultCard>
        ) : (
          <m.div
            key={shake}
            animate={shake ? { x: [0, -8, 8, -6, 6, 0] } : {}}
            transition={{ duration: 0.32 }}
            className="col"
            style={{ gap: 10 }}
          >
            <div className="row word-hop-input" style={{ gap: 8 }}>
              <input
                ref={inputRef}
                className="field fill"
                placeholder="Sau scrie alt concept…"
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
                aria-label="Următorul concept"
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
                className={
                  state.backtrack_recommended
                    ? "lant-undo lant-undo--recommended"
                    : "lant-undo"
                }
                disabled={busy || state.moves === 0}
                onClick={() => void handleUndo()}
                aria-label={
                  state.backtrack_recommended
                    ? "Înapoi, recomandat după două salturi fără progres"
                    : "Înapoi"
                }
              >
                {state.backtrack_recommended ? "↶ Înapoi · recomandat" : "↶ Înapoi"}
              </Button>
              <Button
                type="button"
                variant="secondary"
                disabled={busy}
                onClick={() => void handleHint()}
              >
                {hint?.stage === "direction" || hint?.stage === "alternatives"
                  ? "💡 Mai clar"
                  : "💡 Indiciu"}
              </Button>
              <span className="muted" style={{ alignSelf: "center" }}>
                {hintRemaining !== null
                  ? hintRemaining <= 1
                    ? "ești la un pas de țintă!"
                    : `${hintRemaining} salturi până la țintă`
                  : overPar > 0
                    ? `cu ${overPar} peste optim — încearcă ↶ Înapoi`
                    : state.moves === state.optimal
                      ? "ai atins reperul optim; ținta este încă înainte"
                      : `drumul optim de la start: ${state.optimal} salturi`}
              </span>
            </div>

            <AnimatePresence>
              {recovery && (
                <m.div
                  key={`${recovery.tone}-${recovery.message}`}
                  initial={{ opacity: 0, y: -6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -6 }}
                  className="card"
                  style={{
                    padding: 12,
                    borderColor:
                      recovery.tone === "warning" ? "var(--bad)" : DEF.accent,
                  }}
                >
                  <div className="col" style={{ gap: 8 }}>
                    <span>
                      <span aria-hidden="true" style={{ marginRight: 6 }}>
                        {recovery.tone === "warning" ? "⚠" : "ℹ"}
                      </span>
                      {recovery.message}
                    </span>
                    {recovery.choices.length > 0 ? (
                      <div className="row wrap" style={{ gap: 8 }}>
                        <span className="faint">Ai vrut să scrii:</span>
                        {recovery.choices.map((choice) => (
                          <Button
                            key={choice}
                            type="button"
                            variant="secondary"
                            onClick={() => {
                              setText(choice);
                              focusInputForFinePointer();
                            }}
                          >
                            {choice}
                          </Button>
                        ))}
                      </div>
                    ) : null}
                  </div>
                </m.div>
              )}
            </AnimatePresence>

            <AnimatePresence>
              {hint && (hint.stage || hint.hint) && (
                <m.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="card"
                  style={{ padding: 12, borderColor: "var(--warn)" }}
                  role="status"
                  aria-live="polite"
                >
                  <div className="col" style={{ gap: 8 }}>
                    <strong style={{ color: "var(--warn)", fontSize: "0.8rem" }}>
                      {hint.stage === "direction"
                        ? "O DIRECȚIE"
                        : hint.stage === "alternatives"
                          ? "VARIANTE UTILE"
                          : hint.stage === "backtrack"
                            ? "UN PAS ÎNAPOI"
                            : "UN SALT"}
                    </strong>
                    {hint.message ? (
                      <span className="muted" style={{ fontSize: "0.85rem" }}>
                        {hint.message}
                      </span>
                    ) : null}
                    {hint.alternatives_choices?.length ? (
                      <div className="row wrap" style={{ gap: 8 }}>
                        {hint.alternatives_choices.map((choice) => (
                          <Button
                            key={`${choice.label}-${choice.relation}`}
                            type="button"
                            variant="secondary"
                            title={choice.relation}
                            onClick={() => {
                              setText(choice.label);
                              focusInputForFinePointer();
                            }}
                          >
                            {choice.label}
                          </Button>
                        ))}
                      </div>
                    ) : null}
                    {hint.hint ? (
                      <button
                        type="button"
                        className="hint-fill-button"
                        title="Pune în căsuță"
                        onClick={() => {
                          if (hint.hint) setText(hint.hint.label);
                          focusInputForFinePointer();
                        }}
                      >
                        Încearcă <strong>{hint.hint.label}</strong>
                        {hint.relation ? ` · ${hint.relation}` : ""}
                      </button>
                    ) : null}
                    {hint.stage === "backtrack" ? (
                      <Button
                        type="button"
                        variant="secondary"
                        disabled={busy || state.moves === 0}
                        onClick={() => void handleUndo()}
                      >
                        ↶ Anulează ultimul salt
                      </Button>
                    ) : null}
                  </div>
                </m.div>
              )}
            </AnimatePresence>
          </m.div>
        )}

        {/* path breadcrumb */}
        <div className="col" style={{ gap: 6 }}>
          <span className="faint" style={{ fontSize: "0.72rem" }}>
            DRUMUL TĂU
          </span>
          <Breadcrumb path={state.path} />
        </div>
      </div>
    </div>
  );
}
