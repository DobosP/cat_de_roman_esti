import { createElement, type ComponentPropsWithRef, type CSSProperties, type Ref } from "react";
import { m, type HTMLMotionProps } from "motion/react";
import { Button, useCspSafeStyle, type ButtonProps } from "@roedu/ui";
import { normalizeExplicitCss, type UnitlessProperty } from "./cssUnits";
import "../styles/csp-style.css";

export type ExplicitCss = {
  [K in keyof CSSProperties]: K extends UnitlessProperty ? CSSProperties[K] : Exclude<CSSProperties[K], number>;
} & { [K: `--${string}`]: string | number | undefined };

type NativeTag = "div" | "span" | "strong" | "p" | "form" | "h1" | "header" | "section" | "label" | "select" | "input" | "button" | "summary" | "h2" | "a" | "ol" | "ul" | "li" | "footer" | "small";
type NativeProps<K extends NativeTag> = Omit<ComponentPropsWithRef<K>, "style" | "ref"> & {
  style?: never; css?: ExplicitCss; ref?: Ref<HTMLElementTagNameMap[K]>;
};
function guardedDeclarations(css: ExplicitCss | undefined, unsafeStyle: unknown) {
  if (unsafeStyle !== undefined) throw new Error("Use explicit CSSOM declarations");
  return normalizeExplicitCss(css);
}
function useStyle<T extends HTMLElement>(css: ExplicitCss | undefined, ref: Ref<T> | undefined, unsafeStyle: unknown) {
  // The SDK owns application of declarations and ref forwarding. This boundary
  // validates units; it does not implement a second styling or motion engine.
  return useCspSafeStyle<T>(guardedDeclarations(css, unsafeStyle), ref);
}
function useMotionStyle<T extends HTMLElement>(css: ExplicitCss | undefined, ref: Ref<T> | undefined,
  unsafeStyle: unknown, layout: Pick<HTMLMotionProps<"div">, "layout" | "layoutId">) {
  // Validate the complete own-data bag before reading any ownership field.
  const declarations = guardedDeclarations(css, unsafeStyle);
  let layoutShadow: { boxShadow: string | undefined } | undefined;
  if ((layout.layout || layout.layoutId !== undefined) && declarations) {
    for (const key of ["borderRadius", "borderTopLeftRadius", "borderTopRightRadius",
      "borderBottomLeftRadius", "borderBottomRightRadius"]) {
      if (Object.prototype.hasOwnProperty.call(declarations, key)) throw new Error(`Unreviewed Motion layout CSS ownership: ${key}`);
    }
    if (Object.prototype.hasOwnProperty.call(declarations, "boxShadow")) {
      // Pinned Motion scrapes this exact field for layout scale correction.
      // Keep present-undefined/removal semantics and a single Motion writer.
      layoutShadow = { boxShadow: declarations.boxShadow };
      delete declarations.boxShadow;
    }
  }
  const cssRef = useCspSafeStyle<T>(declarations, ref);
  return { cssRef, layoutShadow };
}
function native<K extends NativeTag>(tag: K) {
  return function CspElement({ css, ref, style, ...props }: NativeProps<K>) {
    const cssRef = useStyle(css, ref, style);
    return createElement(tag, { ...props, ref: cssRef });
  };
}
const CspDiv = native("div");
const CspSpan = native("span");
const CspStrong = native("strong");
const CspP = native("p");
const CspForm = native("form");
const CspH1 = native("h1");
const CspHeader = native("header");
const CspSection = native("section");
const CspLabel = native("label");
const CspSelect = native("select");
const CspInput = native("input");
const CspNativeButton = native("button");
const CspSummary = native("summary");
const CspH2 = native("h2");
const CspA = native("a");
const CspOl = native("ol");
const CspUl = native("ul");
const CspLi = native("li");
const CspFooter = native("footer");
const CspSmall = native("small");
function CspButton({ css, ref, style, ...props }: Omit<ButtonProps, "style"> & {
  css?: ExplicitCss; style?: never; ref?: Ref<HTMLButtonElement>;
}) {
  const cssRef = useStyle(css, ref, style);
  return <Button {...props} ref={cssRef} />;
}
type MotionProps<K extends "div" | "button" | "span" | "p"> = Omit<HTMLMotionProps<K>, "style" | "ref"> & {
  css?: ExplicitCss; style?: never; ref?: Ref<HTMLElementTagNameMap[K]>;
};
function MotionDiv({ css, ref, style, ...props }: MotionProps<"div">) {
  const { cssRef, layoutShadow } = useMotionStyle(css, ref, style, props);
  // Closed internal Motion channel; caller style bags remain forbidden.
  return createElement(m.div, { ...props, ref: cssRef, style: layoutShadow });
}
function MotionButton({ css, ref, style, ...props }: MotionProps<"button">) {
  const { cssRef, layoutShadow } = useMotionStyle(css, ref, style, props);
  // Closed internal Motion channel; caller style bags remain forbidden.
  return createElement(m.button, { ...props, ref: cssRef, style: layoutShadow });
}
function MotionSpan({ css, ref, style, ...props }: MotionProps<"span">) {
  const { cssRef, layoutShadow } = useMotionStyle(css, ref, style, props);
  // Closed internal Motion channel; caller style bags remain forbidden.
  return createElement(m.span, { ...props, ref: cssRef, style: layoutShadow });
}
function MotionP({ css, ref, style, ...props }: MotionProps<"p">) {
  const { cssRef, layoutShadow } = useMotionStyle(css, ref, style, props);
  // Closed internal Motion channel; caller style bags remain forbidden.
  return createElement(m.p, { ...props, ref: cssRef, style: layoutShadow });
}
export {
  CspDiv, CspSpan, CspStrong, CspP, CspForm, CspH1, CspHeader, CspSection, CspLabel, CspSelect,
  CspInput, CspNativeButton, CspSummary, CspH2, CspA, CspOl, CspUl, CspLi, CspFooter, CspSmall,
  CspButton, MotionDiv, MotionButton, MotionSpan, MotionP,
};
