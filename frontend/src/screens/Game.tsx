// Game — the playing screen that wraps GraphMap + Hud.
//
// api.hop(game_id, to) is the ONLY source of truth: we render whatever the server
// returns (it sets last_error on a rejected hop and DOES NOT advance). On last_error
// we toast + shake the board; when the returned state has won=true we bubble it up via
// onSync and App routes to the Win screen. Keyboard 1..9 hops to the listed neighbours;
// reset / exit are handled via the header buttons.

import { useCallback, useEffect, useRef, useState } from "react";
import { motion, useAnimationControls } from "framer-motion";
import type { GameState } from "../api/types";
import type { RunState } from "../App";
import { api, ApiError } from "../api/client";
import { GraphMap } from "../components/GraphMap";
import { Hud } from "../components/Hud";
import type { ToastKind } from "../components/Toast";
import { sound } from "../sound";
import { SoundToggle } from "../components/SoundToggle";

export function Game({
  game,
  run,
  onSync,
  onExit,
  onToast,
}: {
  game: GameState;
  run: RunState;
  onSync: (game: GameState) => void;
  onExit: () => void;
  onToast: (message: string, kind?: ToastKind) => void;
}) {
  const [busy, setBusy] = useState(false);
  const shake = useAnimationControls();
  // Track the last error we surfaced so we don't re-toast the same rejection.
  const lastErrShown = useRef<string | null>(null);

  const doHop = useCallback(
    async (to: string) => {
      if (busy || game.won) return;
      if (!game.neighbors.includes(to)) return;
      setBusy(true);
      try {
        const next = await api.hop(game.game_id, to);
        if (next.last_error) {
          // Server rejected the hop (state unchanged). Surface + shake + buzz.
          if (lastErrShown.current !== next.last_error) {
            onToast(next.last_error, "error");
            lastErrShown.current = next.last_error;
          }
          sound.playError();
          // Rejected hop: the whole board shakes red and we DON'T advance (the server
          // left state unchanged; onSync re-renders the same current node + trail).
          shake.start({
            x: [0, -10, 10, -7, 7, 0],
            transition: { duration: 0.4 },
          });
        } else {
          lastErrShown.current = null;
          // Valid hop. Win arpeggio is played on the Win screen mount; here a soft hop
          // blip for every accepted (non-winning) move.
          if (!next.won) sound.playHop();
        }
        onSync(next);
      } catch (err) {
        onToast(
          err instanceof ApiError
            ? `Saltul a esuat (${err.status}).`
            : "Saltul a esuat. Verifica serverul.",
          "error",
        );
      } finally {
        setBusy(false);
      }
    },
    [busy, game.won, game.neighbors, game.game_id, onSync, onToast, shake],
  );

  const canUndo = !busy && !game.won && game.hops > 0;

  const doUndo = useCallback(async () => {
    if (busy || game.won || game.hops === 0) return;
    setBusy(true);
    try {
      const next = await api.undoHop(game.game_id);
      if (!next.last_error) {
        lastErrShown.current = null;
        sound.playUndo();
      }
      onSync(next);
    } catch (err) {
      onToast(
        err instanceof ApiError
          ? `Pasul inapoi a esuat (${err.status}).`
          : "Pasul inapoi a esuat.",
        "error",
      );
    } finally {
      setBusy(false);
    }
  }, [busy, game.won, game.hops, game.game_id, onSync, onToast]);

  // Keyboard: number keys 1..9 hop to the listed neighbours; Backspace steps back.
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key >= "1" && e.key <= "9") {
        const idx = Number(e.key) - 1;
        const target = game.neighbors[idx];
        if (target) {
          e.preventDefault();
          void doHop(target);
        }
      } else if (e.key === "Backspace") {
        e.preventDefault();
        void doUndo();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [game.neighbors, doHop, doUndo]);

  async function handleReset() {
    if (busy) return;
    setBusy(true);
    try {
      const fresh = await api.resetGame(game.game_id);
      lastErrShown.current = null;
      onSync(fresh);
    } catch (err) {
      onToast(
        err instanceof ApiError
          ? `Resetarea a esuat (${err.status}).`
          : "Resetarea a esuat.",
        "error",
      );
    } finally {
      setBusy(false);
    }
  }

  const currentLabel =
    game.nodes.find((n) => n.id === game.current_id)?.label ?? game.current_id;

  return (
    <motion.div
      animate={shake}
      className="screen-pad fill"
      style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}
    >
      <div
        className="container col fill game-layout"
        style={{ gap: 16, minHeight: 0, paddingBlock: 8 }}
      >
        <div className="row spread wrap" style={{ gap: 10 }}>
          <button
            type="button"
            className="btn btn-ghost"
            onClick={onExit}
            disabled={busy}
          >
            ← Meniu
          </button>
          <div className="row" style={{ gap: 10 }}>
            {run.solved > 0 && (
              <span
                className="badge"
                title="Enigme rezolvate · scor total in aceasta sesiune"
                style={{ fontVariantNumeric: "tabular-nums" }}
              >
                ✓ {run.solved} · {run.total} pct
              </span>
            )}
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => void doUndo()}
              disabled={!canUndo}
              title="Pas inapoi (Backspace)"
            >
              ↶ Inapoi
            </button>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={handleReset}
              disabled={busy}
            >
              ↻ Reseteaza
            </button>
            <SoundToggle />
          </div>
        </div>

        <Hud game={game} />

        <div className="row spread wrap" style={{ gap: 10 }}>
          <span className="muted" style={{ fontSize: "0.85rem" }}>
            Esti la{" "}
            <strong style={{ color: "var(--text)" }}>{currentLabel}</strong> ·{" "}
            <span style={{ color: "var(--text)" }}>{game.neighbors.length}</span>{" "}
            {game.neighbors.length === 1 ? "vecin" : "vecini"}
          </span>
          <span className="faint fine-only" style={{ fontSize: "0.8rem" }}>
            apasa 1–9 ca sa sari la al N-lea vecin
          </span>
          <span className="faint coarse-only" style={{ fontSize: "0.8rem" }}>
            atinge un vecin ca sa sari
          </span>
        </div>

        <GraphMap game={game} onHop={doHop} busy={busy} />
      </div>
    </motion.div>
  );
}
