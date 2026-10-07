import { createElement, type ComponentPropsWithRef, type CSSProperties, type Ref } from "react";
import { m, type HTMLMotionProps } from "framer-motion";
import { Button, useCspSafeStyle, type ButtonProps } from "@roedu/ui";
import { assertExplicitCss, type UnitlessProperty } from "./cssUnits";
import "../styles/csp-style.css";
export { cssLength } from "./cssUnits";

export type ExplicitCss = {
  [K in keyof CSSProperties]: K extends UnitlessProperty ? CSSProperties[K] : Exclude<CSSProperties[K], number>;
} & { [K: `--${string}`]: string | number | undefined };

type NativeTag = "div" | "span" | "strong" | "p" | "form" | "h1" | "header" | "section" | "label" | "select" | "input" | "button" | "summary" | "h2" | "a" | "ol" | "ul" | "li" | "footer" | "small";
type NativeProps<K extends NativeTag> = Omit<ComponentPropsWithRef<K>, "style" | "ref"> & {
  style?: never; css?: ExplicitCss; ref?: Ref<HTMLElementTagNameMap[K]>;
};
function useStyle<T extends HTMLElement>(css: ExplicitCss | undefined, ref: Ref<T> | undefined, unsafeStyle: unknown) {
  if (unsafeStyle !== undefined) throw new Error("Use explicit CSSOM declarations");
  assertExplicitCss(css);
  // The SDK owns application of declarations and ref forwarding. This boundary
  // validates units; it does not implement a second styling or motion engine.
  return useCspSafeStyle<T>(css, ref);
}
function native<K extends NativeTag>(tag: K) {
  return function CspElement({ css, ref, style, ...props }: NativeProps<K>) {
    const cssRef = useStyle(css, ref, style);
    return createElement(tag, { ...props, ref: cssRef });
  };
}
export const Csp = {
  div: native("div"), span: native("span"), strong: native("strong"), p: native("p"), form: native("form"),
  h1: native("h1"), header: native("header"), section: native("section"), label: native("label"), select: native("select"),
  input: native("input"), button: native("button"), summary: native("summary"), h2: native("h2"), a: native("a"),
  ol: native("ol"), ul: native("ul"), li: native("li"), footer: native("footer"), small: native("small"),
};
export function CspButton({ css, ref, style, ...props }: Omit<ButtonProps, "style"> & {
  css?: ExplicitCss; style?: never; ref?: Ref<HTMLButtonElement>;
}) {
  const cssRef = useStyle(css, ref, style);
  return <Button {...props} ref={cssRef} />;
}
type MotionProps<K extends "div" | "button" | "span" | "p"> = Omit<HTMLMotionProps<K>, "style" | "ref"> & {
  css?: ExplicitCss; style?: never; ref?: Ref<HTMLElementTagNameMap[K]>;
};
function MotionDiv({ css, ref, style, ...props }: MotionProps<"div">) {
  const cssRef = useStyle(css, ref, style); return <m.div {...props} ref={cssRef} />;
}
function MotionButton({ css, ref, style, ...props }: MotionProps<"button">) {
  const cssRef = useStyle(css, ref, style); return <m.button {...props} ref={cssRef} />;
}
function MotionSpan({ css, ref, style, ...props }: MotionProps<"span">) {
  const cssRef = useStyle(css, ref, style); return <m.span {...props} ref={cssRef} />;
}
function MotionP({ css, ref, style, ...props }: MotionProps<"p">) {
  const cssRef = useStyle(css, ref, style); return <m.p {...props} ref={cssRef} />;
}
export const CspMotion = { div: MotionDiv, button: MotionButton, span: MotionSpan, p: MotionP };
