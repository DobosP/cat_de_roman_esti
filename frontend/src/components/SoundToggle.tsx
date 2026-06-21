// SoundToggle — a small accessible on/off button for the synthesized SFX.
//
// Reflects the persisted mute flag from src/sound.ts, flips it on click, and stays in
// sync with changes made elsewhere via the SOUND_MUTED_EVENT. Clicking also counts as a
// user gesture, so it unlocks the AudioContext and previews a soft click when enabling.

import { useEffect, useState } from "react";
import { isMuted, toggleMuted, unlockAudio, playSfx, SOUND_MUTED_EVENT } from "../sound";

export function SoundToggle({ compact = false }: { compact?: boolean }) {
  const [muted, setMutedState] = useState<boolean>(() => isMuted());

  // Keep in sync if the flag changes from another instance / tab.
  useEffect(() => {
    const onChange = () => setMutedState(isMuted());
    window.addEventListener(SOUND_MUTED_EVENT, onChange);
    return () => window.removeEventListener(SOUND_MUTED_EVENT, onChange);
  }, []);

  function handleClick() {
    // The click itself is a user gesture — unlock the context here.
    unlockAudio();
    const next = toggleMuted();
    setMutedState(next);
    // Audible confirmation when turning sound ON.
    if (!next) playSfx("select");
  }

  const label = muted ? "Activeaza sunetul" : "Dezactiveaza sunetul";

  return (
    <button
      type="button"
      className="btn btn-ghost sound-toggle"
      onClick={handleClick}
      aria-pressed={!muted}
      aria-label={label}
      title={label}
      style={{
        padding: compact ? "8px 10px" : "10px 12px",
        minWidth: 44,
        minHeight: 44,
        justifyContent: "center",
        lineHeight: 1,
      }}
    >
      <span aria-hidden style={{ fontSize: "1.1rem" }}>
        {muted ? "🔇" : "🔊"}
      </span>
    </button>
  );
}
