import {
  CspDiv, CspSpan, CspStrong, CspP, CspH1, CspHeader, CspSection, CspNativeButton, CspSummary,
  CspH2, CspOl, CspUl, CspLi, CspFooter, CspSmall, CspInput, CspForm,
} from "./CspElements";

export { cssLength } from "./cssUnits";
export { CspButton } from "./CspElements";
export type { ExplicitCss } from "./CspElements";

export const Csp = {
  div: CspDiv, span: CspSpan, strong: CspStrong, p: CspP, h1: CspH1, header: CspHeader,
  section: CspSection, button: CspNativeButton, summary: CspSummary, h2: CspH2,
  ol: CspOl, ul: CspUl, li: CspLi, footer: CspFooter, small: CspSmall,
  input: CspInput, form: CspForm,
};
