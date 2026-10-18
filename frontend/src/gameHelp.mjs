// Compatibility aggregate for help consumers and content assertions.
// Screens import their own record so another game's copy is not an eager dependency.
import { ALCHIMIE_HELP } from "./gameHelp/alchimie.mjs";
import { INTRUSUL_HELP } from "./gameHelp/intrusul.mjs";
import { PERECHI_HELP } from "./gameHelp/perechi.mjs";
import { CONEXIUNI_HELP } from "./gameHelp/conexiuni.mjs";
import { CONTEXTO_HELP } from "./gameHelp/contexto.mjs";
import { LANT_HELP } from "./gameHelp/lant.mjs";

export const GAME_HELP = {
  alchimie: ALCHIMIE_HELP,
  intrusul: INTRUSUL_HELP,
  perechi: PERECHI_HELP,
  conexiuni: CONEXIUNI_HELP,
  contexto: CONTEXTO_HELP,
  lant: LANT_HELP,
};
