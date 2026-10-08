// Original ReactDOM19.2.7 unitless list; the pinned codemod verifies this list
// against the actual installed renderer and records its source SHA256.
export const UNITLESS_PROPERTIES = [
  "animationIterationCount", "aspectRatio", "borderImageOutset", "borderImageSlice", "borderImageWidth", "boxFlex", "boxFlexGroup", "boxOrdinalGroup", "columnCount", "columns", "flex", "flexGrow", "flexPositive", "flexShrink", "flexNegative", "flexOrder", "gridArea", "gridRow", "gridRowEnd", "gridRowSpan", "gridRowStart", "gridColumn", "gridColumnEnd", "gridColumnSpan", "gridColumnStart", "fontWeight", "lineClamp", "lineHeight", "opacity", "order", "orphans", "scale", "tabSize", "widows", "zIndex", "zoom", "fillOpacity", "floodOpacity", "stopOpacity", "strokeDasharray", "strokeDashoffset", "strokeMiterlimit", "strokeOpacity", "strokeWidth", "MozAnimationIterationCount", "MozBoxFlex", "MozBoxFlexGroup", "MozLineClamp", "msAnimationIterationCount", "msFlex", "msZoom", "msFlexGrow", "msFlexNegative", "msFlexOrder", "msFlexPositive", "msFlexShrink", "msGridColumn", "msGridColumnSpan", "msGridRow", "msGridRowSpan", "WebkitAnimationIterationCount", "WebkitBoxFlex", "WebKitBoxFlexGroup", "WebkitBoxOrdinalGroup", "WebkitColumnCount", "WebkitColumns", "WebkitFlex", "WebkitFlexGrow", "WebkitFlexPositive", "WebkitFlexShrink", "WebkitLineClamp",
] as const;
export type UnitlessProperty = typeof UNITLESS_PROPERTIES[number];
const unitless = new Set<string>(UNITLESS_PROPERTIES);

export function assertExplicitCss(css: unknown): asserts css is Record<string, string | number | undefined> | undefined {
  if (css === undefined) return;
  if (css === null || typeof css !== "object" || Array.isArray(css) ||
      ![Object.prototype, null].includes(Object.getPrototypeOf(css))) throw new Error("CSS declarations must be a plain bag");
  for (const [property, value] of Object.entries(css)) {
    if (value === undefined) continue;
    if (typeof value !== "string" && typeof value !== "number") throw new Error(`Unsupported CSS value: ${property}`);
    if (typeof value === "number") {
      if (!Number.isFinite(value)) throw new Error(`Nonfinite CSS value: ${property}`);
      if (!property.startsWith("--") && !unitless.has(property)) throw new Error(`CSS length requires explicit units: ${property}`);
    }
  }
}

/** Preserve React's unitless numbers through the old SDK's narrower numeric list. */
export function normalizeExplicitCss(css: unknown): Record<string, string | undefined> | undefined {
  assertExplicitCss(css);
  if (css === undefined) return undefined;
  return Object.fromEntries(Object.entries(css).map(([key, value]) => [key, typeof value === "number" ? String(value) : value]));
}

export function cssLength(value: string | number | undefined): string | undefined {
  if (typeof value !== "number") return value;
  if (!Number.isFinite(value)) throw new Error("CSS length must be finite");
  return `${value}px`;
}
