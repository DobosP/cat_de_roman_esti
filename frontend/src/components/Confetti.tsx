// Confetti — a one-shot celebration burst for wins/records. Pieces are seeded
// deterministically (stable across StrictMode double-renders); honours reduced
// motion by rendering nothing. Parent must be position:relative + overflow:hidden
// (the .confetti-layer is absolutely positioned and clipped to it).

import { m, useReducedMotion } from "framer-motion";

const PALETTE = ["#ffd166", "#ff5470", "#4ea8ff", "#54e39d", "#c689ff"];

/** Deterministic 0..1 from (index, salt). */
function seeded(i: number, salt: number): number {
  const x = Math.sin(i * 127.1 + salt * 311.7) * 43758.5453;
  return x - Math.floor(x);
}

export function Confetti({ accent, count = 26 }: { accent?: string; count?: number }) {
  const reduced = useReducedMotion();
  if (reduced) return null;
  const colors = accent ? [accent, ...PALETTE] : PALETTE;
  return (
    <div className="confetti-layer" aria-hidden>
      {Array.from({ length: count }, (_, i) => {
        const left = seeded(i, 1) * 100;
        const spin = (seeded(i, 2) > 0.5 ? 1 : -1) * (180 + seeded(i, 3) * 300);
        const fall = 2 + seeded(i, 4) * 1.4;
        const delay = seeded(i, 5) * 0.6;
        const scale = 0.7 + seeded(i, 6) * 0.7;
        return (
          <m.span
            key={i}
            className="confetti-piece"
            style={{ left: `${left}%`, background: colors[i % colors.length] }}
            initial={{ y: -20, opacity: 0, rotate: 0, scale }}
            animate={{ y: 480, opacity: [0, 1, 1, 0], rotate: spin }}
            transition={{ duration: fall, delay, ease: "linear" }}
          />
        );
      })}
    </div>
  );
}
