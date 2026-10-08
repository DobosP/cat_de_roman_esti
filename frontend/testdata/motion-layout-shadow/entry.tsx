// Test-only projected-layout capability; production App remains domAnimation.
// Focused original Motion-owned style.boxShadow control, frozen CSSOM-only
// negative control, and actual corrected helper. This is not full-game parity.
import { Component, createElement, useRef, useState, type ComponentType, type ReactNode, type Ref } from "react";
import { createRoot } from "react-dom/client";
import { LazyMotion, MotionConfig, domMax, m, visualElementStore, type HTMLMotionProps } from "framer-motion";
import { ThemeProvider, useCspSafeStyle } from "@roedu/ui";
import { CspMotion } from "../../src/components/CspStyle";
import { normalizeExplicitCss } from "../../src/components/cssUnits";
import { gameByKey } from "../../src/games";
import { catTheme } from "../../src/theme";
import "@roedu/ui/styles.css";
import "../../src/styles/arcade.css";
import "../../src/styles/conexiuni.css";
import "../../src/styles/contexto.css";
import "./fixture.css";

type Owner = "conexiuni" | "caldrece";
type Variant = "original" | "broken-cssom" | "corrected";
const variants: Variant[] = ["original", "broken-cssom", "corrected"];
const DEF = gameByKey("conexiuni");
// Source-derived CaldRece TEMP_COLOR.Cald; the driver binds the owning source.
const color = "#f4a259";
type CssBag = Record<string, string | number | undefined>;
type BrokenProps<K extends "button" | "div"> = Omit<HTMLMotionProps<K>, "style" | "ref"> & {
  css: CssBag; ref?: Ref<HTMLElementTagNameMap[K]>;
};

// Frozen negative-control mechanism, not a substitute styling engine. These use
// the real preserved SDK hook and deliberately omit Motion's style-value input.
function FrozenCssomButton({ css, ref, ...props }: BrokenProps<"button">) {
  const cssRef = useCspSafeStyle<HTMLButtonElement>(normalizeExplicitCss(css), ref);
  return <m.button {...props} ref={cssRef} />;
}
function FrozenCssomDiv({ css, ref, ...props }: BrokenProps<"div">) {
  const cssRef = useCspSafeStyle<HTMLDivElement>(normalizeExplicitCss(css), ref);
  return <m.div {...props} ref={cssRef} />;
}

// The positive control admits only the original narrow Motion shadow channel.
// All remaining CSS uses the exact same actual SDK boundary as the other arms.
function OriginalShadowButton({ css, ref, ...props }: BrokenProps<"button">) {
  const declarations = normalizeExplicitCss(css);
  const motionStyle: { boxShadow: string | undefined } = { boxShadow: declarations?.boxShadow };
  if (declarations) delete declarations.boxShadow;
  const cssRef = useCspSafeStyle<HTMLButtonElement>(declarations, ref);
  return createElement(m.button, { ...props, ref: cssRef, style: motionStyle });
}
function OriginalShadowDiv({ css, ref, ...props }: BrokenProps<"div">) {
  const declarations = normalizeExplicitCss(css);
  const motionStyle: { boxShadow: string | undefined } = { boxShadow: declarations?.boxShadow };
  if (declarations) delete declarations.boxShadow;
  const cssRef = useCspSafeStyle<HTMLDivElement>(declarations, ref);
  return createElement(m.div, { ...props, ref: cssRef, style: motionStyle });
}

type ObservedVisual = {
  latestValues?: Record<string, unknown>;
  projection?: {
    id?: number; projectionDelta?: { x: { scale: number }; y: { scale: number } };
    treeScale?: { x: number; y: number };
  };
};
const events: { owner: Owner; variant: Variant; event: string; time: number }[] = [];
const lens = {
  feature: "domMax", scope: "focused-original-shadow-ownership-model-not-full-game-parity", events, guardReads: 0,
  inspect(element: HTMLElement) {
    // Read-only observation of the actual pinned Motion visual/projection node.
    const visual = visualElementStore.get(element) as unknown as ObservedVisual | undefined;
    const projection = visual?.projection;
    return {
      projection: Boolean(projection), id: projection?.id ?? null,
      latestShadow: typeof visual?.latestValues?.boxShadow === "string" ? visual.latestValues.boxShadow : null,
      latestScale: typeof visual?.latestValues?.scale === "number" ? visual.latestValues.scale : null,
      projectionScaleX: projection?.projectionDelta?.x.scale ?? null,
      projectionScaleY: projection?.projectionDelta?.y.scale ?? null,
      treeScaleX: projection?.treeScale?.x ?? null, treeScaleY: projection?.treeScale?.y ?? null,
    };
  },
};
declare global { interface Window { __motionLayoutShadow: typeof lens } }
Object.defineProperty(window, "__motionLayoutShadow", { value: lens, writable: false });

function Card({ owner, variant, active, large }: { owner: Owner; variant: Variant; active: boolean; large: boolean }) {
  const isSel = active, isLatest = active;
  const ref = useRef<HTMLElement | null>(null);
  const observe = (event: string) => () => events.push({ owner, variant, event, time: performance.now() });
  const common = {
    layout: true as const,
    "data-owner": owner, "data-variant": variant, "data-active": String(active), "data-large": String(large),
    className: (owner === "conexiuni" ? "card center connection-tile" : "card contexto-guess-row")
      + " fixture-card" + (large ? " fixture-card--large" : ""),
    onLayoutAnimationStart: observe("layout-start"), onLayoutAnimationComplete: observe("layout-complete"),
    onAnimationComplete: observe("animation-complete"),
  };
  if (owner === "conexiuni") {
    const css = {
      padding: "12px 6px", minHeight: "64px", cursor: "pointer", textAlign: "center" as const,
      // actionsLocked=false; animate.opacity=1 covers the original steady value.
      // Candidate CSS removes the opacity owner; none of these arms writes it twice.
      fontSize: "0.82rem", lineHeight: 1.15,
      borderColor: isSel ? DEF.accent : "var(--surface-border)",
      background: isSel ? `color-mix(in srgb, var(--surface) 65%, ${DEF.accent})` : undefined,
      color: isSel ? "var(--text)" : undefined, fontWeight: isSel ? 700 : 500,
      boxShadow: isSel ? `0 0 18px -6px ${DEF.accent}` : undefined,
    };
    const motion = {
      ...common, type: "button" as const, title: "Cuvânt de test", "aria-pressed": isSel,
      initial: { scale: 0.6, opacity: 0 }, animate: { scale: 1, opacity: 1 },
      exit: { scale: 0.4, opacity: 0 }, transition: { type: "spring" as const, stiffness: 320, damping: 20 },
    };
    if (variant === "original") return <OriginalShadowButton {...motion} ref={ref as Ref<HTMLButtonElement>} css={css}>Cuvânt de test</OriginalShadowButton>;
    if (variant === "broken-cssom") return <FrozenCssomButton {...motion} ref={ref as Ref<HTMLButtonElement>} css={css}>Cuvânt de test</FrozenCssomButton>;
    return <CspMotion.button {...motion} ref={ref as Ref<HTMLButtonElement>} css={css}>Cuvânt de test</CspMotion.button>;
  }
  const css = {
    position: "relative" as const, overflow: "hidden" as const, padding: "10px 14px", display: "grid", gap: "8px",
    borderColor: isLatest ? color : "var(--surface-border)",
    boxShadow: isLatest ? `0 0 22px -10px ${color}` : undefined,
  };
  const motion = {
    ...common, initial: isLatest ? { opacity: 0, y: -10, scale: 0.97 } : false as const,
    animate: { opacity: 1, y: 0, scale: 1 }, transition: { type: "spring" as const, stiffness: 380, damping: 28 },
  };
  if (variant === "original") return <OriginalShadowDiv {...motion} ref={ref as Ref<HTMLDivElement>} css={css}>Idee de test</OriginalShadowDiv>;
  if (variant === "broken-cssom") return <FrozenCssomDiv {...motion} ref={ref as Ref<HTMLDivElement>} css={css}>Idee de test</FrozenCssomDiv>;
  return <CspMotion.div {...motion} ref={ref as Ref<HTMLDivElement>} css={css}>Idee de test</CspMotion.div>;
}

function Scene({ owner }: { owner: Owner }) {
  const [large, setLarge] = useState(false), [active, setActive] = useState(true);
  return <main className="fixture-root">
    <h1>Private {owner} layout-shadow capability</h1>
    <p>Focused original shadow-ownership control; domMax is test-only. No full-game, device, budget or production qualification.</p>
    <div className="fixture-controls">
      <button id="toggle-size" type="button" onClick={() => setLarge((value) => !value)}>Schimbă dimensiunea</button>
      <button id="toggle-active" type="button" onClick={() => setActive((value) => !value)}>Schimbă selecția / cel mai recent</button>
    </div>
    <section className={"fixture-stage " + (owner === "conexiuni" ? "connections-screen" : "contexto-screen")}>
      {variants.map((variant) => <section className="fixture-slot" key={variant}>
        <h2>{variant}</h2><Card owner={owner} variant={variant} active={active} large={large} />
      </section>)}
    </section>
  </main>;
}


type GuardKind = "raw-style" | "getter" | "numeric-shadow" | "layout-radius";
function GuardProbe({ kind }: { kind: GuardKind }) {
  let css: unknown = { boxShadow: "0 0 18px -6px #54e39d" };
  const extra: Record<string, unknown> = {};
  if (kind === "raw-style") extra.style = { color: "red" };
  if (kind === "getter") css = Object.defineProperty({}, "boxShadow", {
    enumerable: true, get() { lens.guardReads++; return "0 0 18px -6px #54e39d"; },
  });
  if (kind === "numeric-shadow") css = { boxShadow: 18 };
  if (kind === "layout-radius") css = { borderRadius: "12px" };
  // Deliberately invalid runtime payload; this does not weaken the public types.
  const Actual = CspMotion.div as unknown as ComponentType<Record<string, unknown>>;
  return createElement(Actual, { layout: true, css, "data-guard-probe": kind, ...extra }, "Guard must reject this payload");
}
class GuardBoundary extends Component<{ children: ReactNode }, { error: string | null }> {
  state = { error: null as string | null };
  static getDerivedStateFromError(error: Error) { return { error: error.message }; }
  render() {
    return this.state.error === null ? this.props.children
      : <p id="guard-outcome" data-error={this.state.error} data-reads={lens.guardReads}>{this.state.error}</p>;
  }
}
const owner = new URLSearchParams(window.location.search).get("owner");
if (owner !== "conexiuni" && owner !== "caldrece") throw new Error("Explicit private owner required");
const guard = new URLSearchParams(window.location.search).get("guard");
if (guard !== null && !["raw-style", "getter", "numeric-shadow", "layout-radius"].includes(guard)) throw new Error("Explicit private guard required");
createRoot(document.getElementById("root")!).render(
  <ThemeProvider theme={catTheme}><MotionConfig reducedMotion="user"><LazyMotion features={domMax} strict>
    {guard === null ? <Scene owner={owner} /> : <GuardBoundary><GuardProbe kind={guard as GuardKind} /></GuardBoundary>}
  </LazyMotion></MotionConfig></ThemeProvider>,
);
