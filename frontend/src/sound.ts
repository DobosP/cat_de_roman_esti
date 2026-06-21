// sound.ts — tiny synthesized sound effects via the Web Audio API.
//
// NO binary assets: every effect is generated from oscillators + an exponential gain
// envelope, so the bundle stays asset-free and offline-friendly. A single AudioContext
// is created lazily and resumed on the FIRST user gesture (browsers block autoplay until
// then), so nothing ever plays before the player interacts. All output is gated behind a
// persisted mute flag (localStorage `cat_sound_muted`); prefers-reduced-motion is honoured
// as a default-mute HINT only when the user has never expressed a preference.

const STORAGE_KEY = "cat_sound_muted";

/** Event fired (on `window`) whenever the mute flag changes, so UI toggles can sync. */
export const SOUND_MUTED_EVENT = "cat-sound-muted-change";

type SfxName = "hop" | "error" | "win" | "select" | "undo" | "record";

let ctx: AudioContext | null = null;
let master: GainNode | null = null;
let muted = readInitialMuted();

// ------------------------------------------------------------------ preference state

function prefersReducedMotion(): boolean {
  return (
    typeof window !== "undefined" &&
    typeof window.matchMedia === "function" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches
  );
}

/**
 * Initial mute: an explicit stored choice always wins. With no stored choice, default to
 * UNMUTED — unless the user prefers reduced motion, in which case we start muted as a
 * gentle hint (they can still flip it on; the flip is then persisted).
 */
function readInitialMuted(): boolean {
  if (typeof localStorage === "undefined") return false;
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === "1") return true;
    if (stored === "0") return false;
  } catch {
    /* storage may be unavailable (private mode); fall through to default */
  }
  return prefersReducedMotion();
}

export function isMuted(): boolean {
  return muted;
}

export function setMuted(next: boolean): void {
  muted = next;
  try {
    localStorage.setItem(STORAGE_KEY, next ? "1" : "0");
  } catch {
    /* ignore persistence failures */
  }
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent(SOUND_MUTED_EVENT, { detail: muted }));
  }
}

export function toggleMuted(): boolean {
  setMuted(!muted);
  return muted;
}

// ------------------------------------------------------------------ audio context

type AudioCtor = typeof AudioContext;

function getAudioContextCtor(): AudioCtor | null {
  if (typeof window === "undefined") return null;
  const w = window as unknown as {
    AudioContext?: AudioCtor;
    webkitAudioContext?: AudioCtor;
  };
  return w.AudioContext ?? w.webkitAudioContext ?? null;
}

/** Create (once) the shared AudioContext + master gain. Returns null if unsupported. */
function ensureContext(): AudioContext | null {
  if (ctx) return ctx;
  const Ctor = getAudioContextCtor();
  if (!Ctor) return null;
  try {
    ctx = new Ctor();
    master = ctx.createGain();
    master.gain.value = 0.5;
    master.connect(ctx.destination);
  } catch {
    ctx = null;
    master = null;
  }
  return ctx;
}

/**
 * Resume/unlock the AudioContext. MUST be called from within a user-gesture handler the
 * first time (click / keydown / touch), or the context stays suspended on most browsers.
 * Safe to call repeatedly — it no-ops once unlocked.
 */
export function unlockAudio(): void {
  const c = ensureContext();
  if (!c) return;
  if (c.state === "suspended") {
    void c.resume().catch(() => {
      /* resume can reject if not in a gesture; we'll retry on the next gesture */
    });
  }
}

// Install a one-time set of gesture listeners that unlock audio on the very first
// interaction. Registered at module load; self-removing once the context is running.
function installUnlockListeners(): void {
  if (typeof window === "undefined") return;
  const events: (keyof WindowEventMap)[] = [
    "pointerdown",
    "touchstart",
    "keydown",
  ];
  const handler = () => {
    unlockAudio();
    if (ctx && ctx.state === "running") {
      for (const ev of events) window.removeEventListener(ev, handler);
    }
  };
  for (const ev of events) {
    window.addEventListener(ev, handler, { passive: true });
  }
}

installUnlockListeners();

// ------------------------------------------------------------------ synth helpers

interface ToneSpec {
  freq: number;
  /** start time offset (s) relative to "now". */
  at: number;
  /** note duration (s). */
  dur: number;
  type?: OscillatorType;
  /** peak gain for this tone (0..1, scaled by master). */
  gain?: number;
  /** optional linear glide to this frequency over the note. */
  glideTo?: number;
}

/** Schedule one enveloped oscillator tone on the shared context. */
function playTone(c: AudioContext, dest: AudioNode, spec: ToneSpec): void {
  const now = c.currentTime;
  const start = now + spec.at;
  const end = start + spec.dur;
  const peak = spec.gain ?? 0.3;

  const osc = c.createOscillator();
  osc.type = spec.type ?? "sine";
  osc.frequency.setValueAtTime(spec.freq, start);
  if (spec.glideTo != null) {
    osc.frequency.exponentialRampToValueAtTime(
      Math.max(1, spec.glideTo),
      end,
    );
  }

  const env = c.createGain();
  env.gain.setValueAtTime(0.0001, start);
  env.gain.exponentialRampToValueAtTime(Math.max(0.0002, peak), start + 0.012);
  env.gain.exponentialRampToValueAtTime(0.0001, end);

  osc.connect(env);
  env.connect(dest);
  osc.start(start);
  osc.stop(end + 0.02);
}

/** A short band-limited noise burst (used for the error buzz). */
function playNoise(
  c: AudioContext,
  dest: AudioNode,
  at: number,
  dur: number,
  gain: number,
): void {
  const now = c.currentTime;
  const start = now + at;
  const frames = Math.max(1, Math.floor(c.sampleRate * dur));
  const buffer = c.createBuffer(1, frames, c.sampleRate);
  const data = buffer.getChannelData(0);
  for (let i = 0; i < frames; i++) {
    data[i] = (Math.random() * 2 - 1) * (1 - i / frames);
  }
  const src = c.createBufferSource();
  src.buffer = buffer;

  const filter = c.createBiquadFilter();
  filter.type = "bandpass";
  filter.frequency.value = 380;
  filter.Q.value = 0.8;

  const env = c.createGain();
  env.gain.setValueAtTime(0.0001, start);
  env.gain.exponentialRampToValueAtTime(Math.max(0.0002, gain), start + 0.008);
  env.gain.exponentialRampToValueAtTime(0.0001, start + dur);

  src.connect(filter);
  filter.connect(env);
  env.connect(dest);
  src.start(start);
  src.stop(start + dur + 0.02);
}

// ------------------------------------------------------------------ effect bank

function renderHop(c: AudioContext, dest: AudioNode): void {
  // Soft, friendly upward blip.
  playTone(c, dest, {
    freq: 440,
    glideTo: 660,
    at: 0,
    dur: 0.13,
    type: "sine",
    gain: 0.28,
  });
  playTone(c, dest, {
    freq: 880,
    at: 0.01,
    dur: 0.08,
    type: "triangle",
    gain: 0.08,
  });
}

function renderError(c: AudioContext, dest: AudioNode): void {
  // Distinct low descending buzz + a touch of noise — clearly "no".
  playTone(c, dest, {
    freq: 200,
    glideTo: 110,
    at: 0,
    dur: 0.26,
    type: "sawtooth",
    gain: 0.22,
  });
  playTone(c, dest, {
    freq: 150,
    glideTo: 90,
    at: 0.03,
    dur: 0.22,
    type: "square",
    gain: 0.1,
  });
  playNoise(c, dest, 0, 0.18, 0.12);
}

function renderWin(c: AudioContext, dest: AudioNode): void {
  // Rising major arpeggio (C5 E5 G5 C6) — triumphant little run.
  const notes = [523.25, 659.25, 783.99, 1046.5];
  notes.forEach((f, i) => {
    playTone(c, dest, {
      freq: f,
      at: i * 0.09,
      dur: 0.22,
      type: "triangle",
      gain: 0.26,
    });
    // a soft sine doubling an octave up for sparkle
    playTone(c, dest, {
      freq: f * 2,
      at: i * 0.09,
      dur: 0.16,
      type: "sine",
      gain: 0.06,
    });
  });
}

function renderSelect(c: AudioContext, dest: AudioNode): void {
  // Subtle, quiet click/tick for menu navigation.
  playTone(c, dest, {
    freq: 660,
    at: 0,
    dur: 0.05,
    type: "sine",
    gain: 0.12,
  });
}

function renderUndo(c: AudioContext, dest: AudioNode): void {
  // Soft DOWNWARD blip — the mirror image of the hop (which glides up). Clearly a
  // "step back" without the harshness of the error buzz.
  playTone(c, dest, {
    freq: 540,
    glideTo: 360,
    at: 0,
    dur: 0.12,
    type: "sine",
    gain: 0.24,
  });
}

function renderRecord(c: AudioContext, dest: AudioNode): void {
  // Bright sparkle for a NEW personal best — a quick rising 5th + an octave shimmer
  // on top, distinct from (and a touch brighter than) the win arpeggio.
  const notes = [659.25, 987.77, 1318.51]; // E5 B5 E6
  notes.forEach((f, i) => {
    playTone(c, dest, { freq: f, at: i * 0.07, dur: 0.2, type: "triangle", gain: 0.24 });
    playTone(c, dest, { freq: f * 2, at: i * 0.07, dur: 0.12, type: "sine", gain: 0.07 });
  });
}

const BANK: Record<SfxName, (c: AudioContext, dest: AudioNode) => void> = {
  hop: renderHop,
  error: renderError,
  win: renderWin,
  select: renderSelect,
  undo: renderUndo,
  record: renderRecord,
};

// ------------------------------------------------------------------ public play API

/**
 * Play a named effect. No-ops when muted, before the first gesture (context suspended),
 * or when Web Audio is unavailable. Never throws.
 */
export function playSfx(name: SfxName): void {
  if (muted) return;
  const c = ctx;
  if (!c || !master) return;
  if (c.state !== "running") {
    // Not unlocked yet (no gesture). Try a resume; if it lands we still skip THIS sound
    // to avoid a late blip after the gesture that requested it.
    if (c.state === "suspended") void c.resume().catch(() => {});
    return;
  }
  try {
    BANK[name](c, master);
  } catch {
    /* never let an audio glitch break the game */
  }
}

export const sound = {
  playHop: () => playSfx("hop"),
  playError: () => playSfx("error"),
  playWin: () => playSfx("win"),
  playSelect: () => playSfx("select"),
  playUndo: () => playSfx("undo"),
  playRecord: () => playSfx("record"),
  isMuted,
  setMuted,
  toggleMuted,
  unlockAudio,
};
