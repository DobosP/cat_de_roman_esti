import { h, type Ref } from "preact";
import type * as preact from "preact";
import { Button, useCspSafeStyle, type ButtonProps } from "@roedu/ui";
import { normalizeExplicitCss, type UnitlessProperty } from "./cssUnits";

// Dimensional declarations must carry explicit units: Preact 11 writes numbers
// verbatim (no auto-px), so only reviewed unitless and custom properties admit numbers.
// Keys come from the DOM declaration set only (not Preact's open string index),
// so a numeric value is admitted exactly for the reviewed unitless properties.
type CssKey = Exclude<keyof preact.DOMCSSProperties, number | symbol>;
export type ExplicitCss = {
  [K in CssKey]?: K extends UnitlessProperty ? string | number | undefined : string | undefined;
} & { [K: `--${string}`]: string | number | undefined };

// Tags whose Preact attribute type is a plain interface (no accessibility
// discriminated union), so Omit keeps the complete attribute set.
type TagAttributes = {
  div: preact.HTMLAttributes<HTMLDivElement>;
  span: preact.HTMLAttributes<HTMLSpanElement>;
  strong: preact.HTMLAttributes<HTMLElement>;
  p: preact.HTMLAttributes<HTMLParagraphElement>;
  h1: preact.HTMLAttributes<HTMLHeadingElement>;
  h2: preact.HTMLAttributes<HTMLHeadingElement>;
  header: preact.HTMLAttributes<HTMLElement>;
  section: preact.HTMLAttributes<HTMLElement>;
  summary: preact.HTMLAttributes<HTMLElement>;
  ol: preact.HTMLAttributes<HTMLOListElement>;
  ul: preact.HTMLAttributes<HTMLUListElement>;
  li: preact.HTMLAttributes<HTMLLIElement>;
  footer: preact.HTMLAttributes<HTMLElement>;
  small: preact.HTMLAttributes<HTMLElement>;
  button: preact.ButtonHTMLAttributes<HTMLButtonElement>;
  input: preact.InputHTMLAttributes<HTMLInputElement>;
  form: preact.HTMLAttributes<HTMLFormElement>;
};
type NativeTag = keyof TagAttributes;
type NativeProps<K extends NativeTag> = Omit<TagAttributes[K], "style" | "ref"> & {
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
function native<K extends NativeTag>(tag: K) {
  return function CspElement({ css, ref, style, ...props }: NativeProps<K>) {
    const cssRef = useStyle<HTMLElementTagNameMap[K]>(css, ref, style);
    return h(tag, { ...props, ref: cssRef });
  };
}
const CspDiv = native("div");
const CspSpan = native("span");
const CspStrong = native("strong");
const CspP = native("p");
const CspH1 = native("h1");
const CspHeader = native("header");
const CspSection = native("section");
const CspNativeButton = native("button");
const CspSummary = native("summary");
const CspH2 = native("h2");
const CspOl = native("ol");
const CspUl = native("ul");
const CspLi = native("li");
const CspFooter = native("footer");
const CspSmall = native("small");
const CspInput = native("input");
const CspForm = native("form");
function CspButton({ css, ref, style, ...props }: Omit<ButtonProps, "style" | "ref"> & {
  css?: ExplicitCss; style?: never; ref?: Ref<HTMLButtonElement>;
}) {
  const cssRef = useStyle<HTMLButtonElement>(css, ref, style);
  return <Button {...props} ref={cssRef} />;
}
export {
  CspDiv, CspSpan, CspStrong, CspP, CspH1, CspHeader, CspSection, CspNativeButton, CspSummary,
  CspH2, CspOl, CspUl, CspLi, CspFooter, CspSmall, CspInput, CspForm, CspButton,
};
