import { AnimatePresence, motion } from "framer-motion";
import type { GameState, GraphNode } from "../api/types";
import { categoryColor, categoryLabel } from "../theme/tokens";

// The HUD is the product's "explicit hop tracker": start -> target chips, a hops/par
// meter, the live (server) score, mode + category badges, and the ordered HOP-TRAIL
// breadcrumb of every node hopped, in order.

function labelOf(nodes: Map<string, GraphNode>, id: string): string {
  return nodes.get(id)?.label ?? id;
}

function NodeChip({
  node,
  tone,
}: {
  node: GraphNode | undefined;
  tone: "start" | "target";
}) {
  const color =
    tone === "target" ? "var(--target, #ff5d8f)" : "var(--accent)";
  return (
    <span
      className="chip"
      title={node?.description ?? ""}
      style={{
        borderColor: color,
        boxShadow: `0 0 16px -6px ${tone === "target" ? "#ff5d8f" : "#7c8bff"}`,
      }}
    >
      <span
        aria-hidden
        style={{
          width: 9,
          height: 9,
          borderRadius: "50%",
          background: node ? categoryColor(node.category) : color,
          boxShadow: `0 0 8px ${node ? categoryColor(node.category) : color}`,
        }}
      />
      {node?.label ?? "?"}
    </span>
  );
}

export function Hud({ game }: { game: GameState }) {
  const nodes = new Map(game.nodes.map((n) => [n.id, n]));
  const start = nodes.get(game.start_id);
  const target = nodes.get(game.target_id);

  const par = game.puzzle.par;
  const meterMax = Math.max(par, game.hops, 1);
  const overPar = game.hops > par;
  const catColor = categoryColor(game.category);

  return (
    <div className="card" style={{ padding: 18, display: "grid", gap: 16 }}>
      {/* badges row */}
      <div className="row spread wrap" style={{ gap: 10 }}>
        <div className="row wrap" style={{ gap: 8 }}>
          <span
            className="badge"
            style={{ borderColor: catColor, color: catColor }}
          >
            {categoryLabel(game.category)}
          </span>
          <span
            className="badge"
            style={{
              borderColor:
                game.mode === "hard" ? "var(--bad)" : "var(--good)",
              color: game.mode === "hard" ? "var(--bad)" : "var(--good)",
            }}
          >
            {game.mode === "hard" ? "Greu" : "Usor"}
          </span>
        </div>
        <motion.div
          key={game.score}
          initial={{ scale: 1.18 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", stiffness: 400, damping: 18 }}
          className="badge"
          style={{
            fontVariantNumeric: "tabular-nums",
            borderColor: "var(--warn)",
            color: "var(--warn)",
          }}
        >
          {game.score} pct
        </motion.div>
      </div>

      {/* start -> target */}
      <div className="row wrap" style={{ gap: 10 }}>
        <NodeChip node={start} tone="start" />
        <span aria-hidden className="faint" style={{ fontWeight: 700 }}>
          →
        </span>
        <NodeChip node={target} tone="target" />
      </div>

      {/* hops / par meter */}
      <div className="col" style={{ gap: 6 }}>
        <div className="row spread">
          <span className="muted" style={{ fontSize: "0.82rem" }}>
            Salturi
          </span>
          <span
            style={{
              fontVariantNumeric: "tabular-nums",
              fontWeight: 700,
              color: overPar ? "var(--warn)" : "var(--text)",
            }}
          >
            {game.hops} / par {par}
          </span>
        </div>
        <div
          style={{
            height: 8,
            borderRadius: 999,
            background: "rgba(140,152,196,0.16)",
            overflow: "hidden",
          }}
        >
          <motion.div
            initial={false}
            animate={{ width: `${Math.min(100, (game.hops / meterMax) * 100)}%` }}
            transition={{ type: "spring", stiffness: 260, damping: 28 }}
            style={{
              height: "100%",
              borderRadius: 999,
              background: overPar
                ? "linear-gradient(90deg, var(--warn), var(--bad))"
                : "linear-gradient(90deg, var(--accent), var(--good))",
            }}
          />
        </div>
      </div>

      {/* explicit HOP-TRAIL breadcrumb */}
      <div className="col" style={{ gap: 8 }}>
        <span className="muted" style={{ fontSize: "0.82rem" }}>
          Traseul salturilor
        </span>
        <div className="row wrap" style={{ gap: 6 }}>
          <AnimatePresence initial={false}>
            {game.path.map((id, i) => {
              const node = nodes.get(id);
              const isCurrent = id === game.current_id;
              const isTarget = id === game.target_id;
              const color = node
                ? categoryColor(node.category)
                : "var(--text-dim)";
              return (
                <motion.div
                  key={`${id}-${i}`}
                  layout
                  initial={{ opacity: 0, scale: 0.7, y: 6 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  transition={{
                    type: "spring",
                    stiffness: 480,
                    damping: 26,
                  }}
                  className="row"
                  style={{ gap: 6 }}
                >
                  {i > 0 && (
                    <span aria-hidden className="faint">
                      ›
                    </span>
                  )}
                  <span
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: 6,
                      padding: "4px 10px",
                      borderRadius: 10,
                      fontSize: "0.82rem",
                      fontWeight: 600,
                      background: isCurrent
                        ? "var(--surface-strong)"
                        : "var(--surface)",
                      border: `1px solid ${
                        isCurrent
                          ? color
                          : isTarget
                            ? "var(--target, #ff5d8f)"
                            : "var(--surface-border)"
                      }`,
                      boxShadow: isCurrent ? `0 0 14px -4px ${color}` : "none",
                    }}
                  >
                    <span
                      aria-hidden
                      style={{
                        width: 8,
                        height: 8,
                        borderRadius: "50%",
                        background: color,
                        boxShadow: `0 0 6px ${color}`,
                      }}
                    />
                    {labelOf(nodes, id)}
                  </span>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
