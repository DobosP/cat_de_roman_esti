// Original ReactDOM19.2.7 unitless list; the pinned codemod verifies this list
// against the actual installed renderer and records its source SHA256.
export const UNITLESS_PROPERTIES = [
  "animationIterationCount", "aspectRatio", "borderImageOutset", "borderImageSlice", "borderImageWidth", "boxFlex", "boxFlexGroup", "boxOrdinalGroup", "columnCount", "columns", "flex", "flexGrow", "flexPositive", "flexShrink", "flexNegative", "flexOrder", "gridArea", "gridRow", "gridRowEnd", "gridRowSpan", "gridRowStart", "gridColumn", "gridColumnEnd", "gridColumnSpan", "gridColumnStart", "fontWeight", "lineClamp", "lineHeight", "opacity", "order", "orphans", "scale", "tabSize", "widows", "zIndex", "zoom", "fillOpacity", "floodOpacity", "stopOpacity", "strokeDasharray", "strokeDashoffset", "strokeMiterlimit", "strokeOpacity", "strokeWidth", "MozAnimationIterationCount", "MozBoxFlex", "MozBoxFlexGroup", "MozLineClamp", "msAnimationIterationCount", "msFlex", "msZoom", "msFlexGrow", "msFlexNegative", "msFlexOrder", "msFlexPositive", "msFlexShrink", "msGridColumn", "msGridColumnSpan", "msGridRow", "msGridRowSpan", "WebkitAnimationIterationCount", "WebkitBoxFlex", "WebKitBoxFlexGroup", "WebkitBoxOrdinalGroup", "WebkitColumnCount", "WebkitColumns", "WebkitFlex", "WebkitFlexGrow", "WebkitFlexPositive", "WebkitFlexShrink", "WebkitLineClamp",
] as const;
export type UnitlessProperty = typeof UNITLESS_PROPERTIES[number];
const unitless = new Set<string>(UNITLESS_PROPERTIES);

export function assertExplicitCss(css: object | undefined): void {
  if (css === undefined) return;
  if (css === null || Array.isArray(css)) throw new Error("CSS declarations must be a plain bag");
  for (const [property, value] of Object.entries(css)) {
    if (value === undefined) continue;
    if (typeof value !== "string" && typeof value !== "number") throw new Error(`Unsupported CSS value: ${property}`);
    if (typeof value === "number") {
      if (!Number.isFinite(value)) throw new Error(`Nonfinite CSS value: ${property}`);
      if (!property.startsWith("--") && !unitless.has(property)) throw new Error(`CSS length requires explicit units: ${property}`);
    }
  }
}

export function cssLength(value: string | number | undefined): string | undefined {
  if (typeof value !== "number") return value;
  if (!Number.isFinite(value)) throw new Error("CSS length must be finite");
  return `${value}px`;
}
