// Confetti — a one-shot celebration burst for wins/records, owned by the kit's
// motion API (@roedu/ui/motion): deterministic particles, finished through WAAPI,
// hidden under reduced motion or data-motion="off|reduced". The absolute
// .confetti-layer keeps the burst inside the card (position:relative +
// overflow:hidden) without taking space in the card's column layout.

import { Confetti as KitConfetti } from "@roedu/ui/motion";

export function Confetti({ count = 26 }: { count?: number }) {
  return (
    <div className="confetti-layer" aria-hidden>
      <KitConfetti count={count} durationMs={1400} />
    </div>
  );
}
