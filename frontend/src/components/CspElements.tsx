import { createElement, memo, type ComponentPropsWithRef, type CSSProperties, type Ref } from "react";
import { m, type HTMLMotionProps } from "framer-motion";
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
function useStyle<T extends HTMLElement>(css: ExplicitCss | undefined, ref: Ref<T> | undefined, unsafeStyle: unknown) {
  if (unsafeStyle !== undefined) throw new Error("Use explicit CSSOM declarations");
  // Validation/normalization only. The unchanged SDK applies declarations and
  // forwards refs. Unitless numbers become strings to avoid its smaller px list.
  return useCspSafeStyle<T>(normalizeExplicitCss(css), ref);
}
function native<K extends NativeTag>(tag: K) {
  return function CspElement({ css, ref, style, ...props }: NativeProps<K>) {
    const cssRef = useStyle(css, ref, style);
    return createElement(tag, { ...props, ref: cssRef });
  };
}
export const CspDiv = memo(native("div"));
export const CspSpan = memo(native("span"));
export const CspStrong = memo(native("strong"));
export const CspP = memo(native("p"));
export const CspForm = memo(native("form"));
export const CspH1 = memo(native("h1"));
export const CspHeader = memo(native("header"));
export const CspSection = memo(native("section"));
export const CspLabel = memo(native("label"));
export const CspSelect = memo(native("select"));
export const CspInput = memo(native("input"));
export const CspNativeButton = memo(native("button"));
export const CspSummary = memo(native("summary"));
export const CspH2 = memo(native("h2"));
export const CspA = memo(native("a"));
export const CspOl = memo(native("ol"));
export const CspUl = memo(native("ul"));
export const CspLi = memo(native("li"));
export const CspFooter = memo(native("footer"));
export const CspSmall = memo(native("small"));
export function CspButton({ css, ref, style, ...props }: Omit<ButtonProps, "style"> & {
  css?: ExplicitCss; style?: never; ref?: Ref<HTMLButtonElement>;
}) {
  const cssRef = useStyle(css, ref, style);
  return <Button {...props} ref={cssRef} />;
}
type MotionProps<K extends "div" | "button" | "span" | "p"> = Omit<HTMLMotionProps<K>, "style" | "ref"> & {
  css?: ExplicitCss; style?: never; ref?: Ref<HTMLElementTagNameMap[K]>;
};
export function CspMotionDiv({ css, ref, style, ...props }: MotionProps<"div">) {
  const cssRef = useStyle(css, ref, style); return <m.div {...props} ref={cssRef} />;
}
export function CspMotionButton({ css, ref, style, ...props }: MotionProps<"button">) {
  const cssRef = useStyle(css, ref, style); return <m.button {...props} ref={cssRef} />;
}
export function CspMotionSpan({ css, ref, style, ...props }: MotionProps<"span">) {
  const cssRef = useStyle(css, ref, style); return <m.span {...props} ref={cssRef} />;
}
export function CspMotionP({ css, ref, style, ...props }: MotionProps<"p">) {
  const cssRef = useStyle(css, ref, style); return <m.p {...props} ref={cssRef} />;
}
