import { useMemo } from "preact/hooks";
import type { ToastKind } from "@roedu/ui";
import { lazyScreen } from "../lazyScreen";
import { legacyAlchimieResume } from "../alchimieSavedMode";
import { alchimieMode } from "../alchimieMode";
// Preserve the exact original stylesheet precedence for both modes. Splitting
// JavaScript must not make shared controls depend on visiting exploration first.

const AlchimieChallenge = lazyScreen(() => import("./AlchimieChallenge"));
const AlchimieExplore = lazyScreen(() => import("./AlchimieExplore"));

export default function Alchimie({ url, onExit, onToast }: {
  url: string;
  onExit: () => void;
  onToast: (message: string, kind?: ToastKind) => void;
}) {
  // The App frame captures this URL; an exiting frame cannot switch mode when
  // the live location advances. The saved-round fallback is sampled once.
  const legacyResume = useMemo(() => legacyAlchimieResume(), []);
  const mode = alchimieMode(url, legacyResume);
  return mode === "challenges"
    ? <AlchimieChallenge onExit={onExit} onToast={onToast} />
    : <AlchimieExplore onExit={onExit} onToast={onToast} />;
}
