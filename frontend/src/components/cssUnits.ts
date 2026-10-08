// Original ReactDOM19.2.7 unitless list; the pinned codemod verifies this list
// against the actual installed renderer and records its source SHA256.
export const UNITLESS_PROPERTIES = [
  "animationIterationCount", "aspectRatio", "borderImageOutset", "borderImageSlice", "borderImageWidth", "boxFlex", "boxFlexGroup", "boxOrdinalGroup", "columnCount", "columns", "flex", "flexGrow", "flexPositive", "flexShrink", "flexNegative", "flexOrder", "gridArea", "gridRow", "gridRowEnd", "gridRowSpan", "gridRowStart", "gridColumn", "gridColumnEnd", "gridColumnSpan", "gridColumnStart", "fontWeight", "lineClamp", "lineHeight", "opacity", "order", "orphans", "scale", "tabSize", "widows", "zIndex", "zoom", "fillOpacity", "floodOpacity", "stopOpacity", "strokeDasharray", "strokeDashoffset", "strokeMiterlimit", "strokeOpacity", "strokeWidth", "MozAnimationIterationCount", "MozBoxFlex", "MozBoxFlexGroup", "MozLineClamp", "msAnimationIterationCount", "msFlex", "msZoom", "msFlexGrow", "msFlexNegative", "msFlexOrder", "msFlexPositive", "msFlexShrink", "msGridColumn", "msGridColumnSpan", "msGridRow", "msGridRowSpan", "WebkitAnimationIterationCount", "WebkitBoxFlex", "WebKitBoxFlexGroup", "WebkitBoxOrdinalGroup", "WebkitColumnCount", "WebkitColumns", "WebkitFlex", "WebkitFlexGrow", "WebkitFlexPositive", "WebkitFlexShrink", "WebkitLineClamp",
] as const;
export type UnitlessProperty = typeof UNITLESS_PROPERTIES[number];
const unitless = new Set<string>(UNITLESS_PROPERTIES);

type CssDeclarationValue = string | number | undefined;

function explicitCssEntries(css: unknown): [string, CssDeclarationValue][] | undefined {
  if (css === undefined) return;
  if (css === null || typeof css !== "object" || Array.isArray(css)) throw new Error("CSS declarations must be a plain bag");
  const prototype = Object.getPrototypeOf(css);
  if (prototype !== Object.prototype && prototype !== null) throw new Error("CSS declarations must be a plain bag");
  const entries: [string, CssDeclarationValue][] = [];
  for (const [property, descriptor] of Object.entries(Object.getOwnPropertyDescriptors(css))) {
    if (!descriptor.enumerable) continue;
    if (!Object.prototype.hasOwnProperty.call(descriptor, "value")) throw new Error(`CSS declarations must use own data properties: ${property}`);
    const value: unknown = descriptor.value;
    if (value === undefined) { entries.push([property, value]); continue; }
    if (typeof value !== "string" && typeof value !== "number") throw new Error(`Unsupported CSS value: ${property}`);
    if (typeof value === "number") {
      if (!Number.isFinite(value)) throw new Error(`Nonfinite CSS value: ${property}`);
      if (!property.startsWith("--") && !unitless.has(property)) throw new Error(`CSS length requires explicit units: ${property}`);
    }
    entries.push([property, value]);
  }
  return entries;
}

export function assertExplicitCss(css: unknown): void {
  explicitCssEntries(css);
}

export function normalizeExplicitCss(css: unknown): Record<string, string | undefined> | undefined {
  const entries = explicitCssEntries(css);
  if (entries === undefined) return;
  // Admitted numbers are unitless or custom properties. Explicit serialization
  // prevents the preserved SDK's narrower unitless list from adding px.
  return Object.fromEntries(entries.map(([property, value]): [string, string | undefined] => [
    property, typeof value === "number" ? String(value) : value,
  ]));
}

export function cssLength(value: string | number | undefined): string | undefined {
  if (typeof value !== "number") return value;
  if (!Number.isFinite(value)) throw new Error("CSS length must be finite");
  return `${value}px`;
}
