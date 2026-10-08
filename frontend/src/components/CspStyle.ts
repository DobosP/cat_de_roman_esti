import {
  CspDiv, CspSpan, CspStrong, CspP, CspForm, CspH1, CspHeader, CspSection, CspLabel, CspSelect,
  CspInput, CspNativeButton, CspSummary, CspH2, CspA, CspOl, CspUl, CspLi, CspFooter, CspSmall,
  MotionDiv, MotionButton, MotionSpan, MotionP,
} from "./CspElements";

export { cssLength } from "./cssUnits";
export { CspButton } from "./CspElements";
export type { ExplicitCss } from "./CspElements";

export const Csp = {
  div: CspDiv, span: CspSpan, strong: CspStrong, p: CspP, form: CspForm,
  h1: CspH1, header: CspHeader, section: CspSection, label: CspLabel, select: CspSelect,
  input: CspInput, button: CspNativeButton, summary: CspSummary, h2: CspH2, a: CspA,
  ol: CspOl, ul: CspUl, li: CspLi, footer: CspFooter, small: CspSmall,
};
export const CspMotion = { div: MotionDiv, button: MotionButton, span: MotionSpan, p: MotionP };
