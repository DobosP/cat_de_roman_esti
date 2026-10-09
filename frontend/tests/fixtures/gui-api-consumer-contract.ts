// Type-only replacements for the mapped API source assertions. Authored NOT RUN.
// The owning node test must check this file with the real TypeScript program;
// transpilation alone cannot prove these constraints. Native response parity
// separately checks public payloads; this fixture does not validate JSON at runtime.
import type {
  CategoryClue, ClueResult, ContextoState, Difficulty as ContextoDifficulty,
  Guess, GuessAccepted, GuessFeedback, GuessFeedbackKind, GuessRejected, NextClueKind, RevealedTarget, Temperature, WarmClue,
} from "../../src/api/contexto";
import type {
  AlchimieState, CombineResult, Difficulty as AlchimieDifficulty, EarnedHint,
  HintResult as AlchimieHintResult, InventoryItem,
} from "../../src/api/alchimie";
import type {
  Difficulty as LantDifficulty, HintResult as LantHintResult, LantChoice,
  LantProgress, LantProgressKind, LantState, MoveResult,
} from "../../src/api/lant";
import type {
  CategoryInfo, Difficulty as MetaDifficulty, GameKey as CategoryGameKey,
} from "../../src/api/meta";
import type { RankingRow } from "../../src/api/auth";

type Equal<A, B> =
  (<T>() => T extends A ? 1 : 2) extends (<T>() => T extends B ? 1 : 2)
    ? (<T>() => T extends B ? 1 : 2) extends (<T>() => T extends A ? 1 : 2)
      ? true : false
    : false;
type Assert<T extends true> = T;
type AssertAll<T extends readonly true[]> = T;
type OptionalKeys<T> = {
  [K in keyof T]-?: Record<never, never> extends Pick<T, K> ? K : never;
}[keyof T];
type Required<T, K extends keyof T> = Equal<Extract<K, OptionalKeys<T>>, never>;
type Optional<T, K extends keyof T> = Equal<Extract<K, OptionalKeys<T>>, K>;

type DifficultyTokens = "usor" | "normal" | "greu";
type TemperatureTokens = "Gasit" | "Fierbinte" | "Cald" | "Caldut"
  | "Rece" | "Foarte rece" | "Inghetat";

// v41-category-availability:15–20 and the typed configurable game options.
export type DifficultyContract = AssertAll<[
  Equal<MetaDifficulty, DifficultyTokens>, Equal<ContextoDifficulty, DifficultyTokens>,
  Equal<AlchimieDifficulty, DifficultyTokens>, Equal<LantDifficulty, DifficultyTokens>,
]>;
export type CategoryAvailabilityContract = AssertAll<[
  Equal<CategoryGameKey, "alchimie" | "conexiuni" | "contexto" | "lant">,
  Equal<CategoryInfo["available_by_difficulty"],
    Record<CategoryGameKey, Record<DifficultyTokens, boolean>>>,
  Required<CategoryInfo, "available_by_difficulty">,
]>;

// v39-verified-ranking:16: the requester marker remains required boolean.
export type RankingViewerIdentityContract = AssertAll<[
  Equal<RankingRow["is_me"], boolean>, Required<RankingRow, "is_me">,
]>;

// contexto-api:7–30 and v42-caldrece-legend-confirm:10–15,45–53.
export type TemperatureContract = Assert<Equal<Temperature, TemperatureTokens>>;
export type ContextoClueKindsContract = Assert<Equal<NextClueKind, "category" | "warmer">>;
export type ContextoClueFieldsContract = AssertAll<[
  Equal<CategoryClue["category"], { key: string; label: string }>,
  Equal<CategoryClue["message"], string>, Required<CategoryClue, "category" | "message">,
  Equal<WarmClue["label"], string>, Equal<WarmClue["rank"], number>,
  Required<WarmClue, "label" | "rank">,
  Equal<Guess["rank"], number>, Required<Guess, "rank">,
  Equal<Guess["temperature"], TemperatureTokens>,
  Equal<ContextoState["clue_available"], boolean>, Required<ContextoState, "clue_available">,
  Equal<ContextoState["next_clue_kind"], NextClueKind | undefined>,
  Equal<ContextoState["warm_clue"], WarmClue | undefined>,
  Optional<ContextoState, "next_clue_kind" | "warm_clue">,
  Equal<ClueResult["clue_kind"], NextClueKind>, Required<ClueResult, "clue_kind">,
  Equal<ClueResult["word"], WarmClue | undefined>, Optional<ClueResult, "word">,
]>;
// These field and optionality checks replace the remaining Contexto type
// spelling assertions; known token presence does not claim a closed union.
export type ContextoGuessFeedbackContract = AssertAll<[
  Equal<Guess["attempt_number"], number>, Required<Guess, "attempt_number">,
  Equal<GuessFeedback["rank_delta"], number | undefined>, Optional<GuessFeedback, "rank_delta">,
  Equal<GuessAccepted["feedback"], GuessFeedback>, Required<GuessAccepted, "feedback">,
  Equal<GuessRejected["suggestions"], string[]>, Required<GuessRejected, "suggestions">,
  Equal<GuessAccepted["message"], string | undefined>, Optional<GuessAccepted, "message">,
]>;
export type ContextoKnownGuessFeedbackKindsContract = AssertAll<[
  Equal<Extract<"first", GuessFeedbackKind>, "first">,
  Equal<Extract<"new-best", GuessFeedbackKind>, "new-best">,
  Equal<Extract<"warmer", GuessFeedbackKind>, "warmer">,
  Equal<Extract<"colder", GuessFeedbackKind>, "colder">,
  Equal<Extract<"same", GuessFeedbackKind>, "same">,
  Equal<Extract<"repeat", GuessFeedbackKind>, "repeat">,
  Equal<Extract<"found", GuessFeedbackKind>, "found">,
]>;
export type ContextoConfirmationContract = AssertAll<[
  Equal<GuessRejected["needs_confirmation"], true | undefined>,
  Equal<GuessRejected["resolved_label"], string | undefined>,
  Equal<GuessRejected["resolved_token"], string | undefined>,
  Optional<GuessRejected, "needs_confirmation" | "resolved_label" | "resolved_token">,
]>;
// The former own-interface-body regex did not check inherited fields.
// ClueResult really extends ContextoState, including its optional target;
// target absence on a live clue response is an actual native API assertion.
export type ClueInheritedTargetContract = AssertAll<[
  Equal<ClueResult["target"], RevealedTarget | undefined>, Optional<ClueResult, "target">,
]>;

// alchimie-projection:10–14,77–80,94–96. Counts/verdicts are public;
// attempted pair memory and recipe identifiers remain outside these API types.
type PrivateAlchemyKeys = "attempted_pairs" | "attempted_partner" | "recipe_ids";
export type AlchimieInventoryFlagsContract = AssertAll<[
  Equal<InventoryItem["recent"], boolean>, Equal<InventoryItem["useful"], boolean>,
  Equal<InventoryItem["ready"], boolean>, Equal<InventoryItem["depleted"], boolean>,
  Required<InventoryItem, "recent" | "useful" | "ready" | "depleted">,
]>;
export type AlchimieMemoryContract = AssertAll<[
  Equal<AlchimieState["attempted_count"], number>, Required<AlchimieState, "attempted_count">,
  Equal<CombineResult["already_tried"], boolean>, Required<CombineResult, "already_tried">,
  Equal<Extract<PrivateAlchemyKeys, keyof CombineResult | keyof AlchimieHintResult>, never>,
]>;
export type AlchimieHintContract = AssertAll<[
  Equal<EarnedHint["hint_kind"], "output" | "category" | "pair" | "none">,
  Equal<EarnedHint["hint_output"], { label: string } | null>,
  Required<EarnedHint, "hint_kind" | "hint_output">,
  Equal<AlchimieHintResult["hint_kind"], EarnedHint["hint_kind"]>,
  Equal<AlchimieHintResult["hint_output"], EarnedHint["hint_output"]>,
]>;

// lant-recovery-feedback:9–39: labels/relations, coarse progress, optional
// recovery results and voluntary hint stages; no private choice identifier.
export type LantChoiceContract = AssertAll<[
  Equal<LantChoice["label"], string>, Equal<LantChoice["relation"], string>,
  Required<LantChoice, "label" | "relation">, Equal<Extract<"id", keyof LantChoice>, never>,
]>;
export type LantProgressContract = AssertAll<[
  Equal<LantProgressKind, "closer" | "lateral" | "farther" | "dead_end" | "won">,
  Equal<LantProgress["kind"], LantProgressKind>, Equal<LantProgress["message"], string>,
  Required<LantProgress, "kind" | "message">,
  Equal<LantState["choices"], LantChoice[]>, Equal<LantState["backtrack_recommended"], boolean>,
  Required<LantState, "choices" | "backtrack_recommended">,
]>;
export type LantMoveRecoveryContract = AssertAll<[
  Equal<MoveResult["message"], string | undefined>, Equal<MoveResult["dead_end"], boolean | undefined>,
  Equal<MoveResult["suggestions"], string[] | undefined>, Equal<MoveResult["choices"], LantChoice[] | undefined>,
  Equal<MoveResult["progress"], LantProgress | undefined>,
  Equal<MoveResult["backtrack_recommended"], boolean | undefined>,
  Optional<MoveResult, "message" | "dead_end" | "suggestions" | "choices" | "progress" | "backtrack_recommended">,
]>;
export type LantHintRecoveryContract = AssertAll<[
  Equal<LantHintResult["stage"], "direction" | "alternatives" | "hop" | "backtrack" | undefined>,
  Equal<LantHintResult["alternatives_labels"], string[] | undefined>,
  Equal<LantHintResult["alternatives_choices"], LantChoice[] | undefined>,
  Optional<LantHintResult, "stage" | "alternatives_labels" | "alternatives_choices">,
]>;
