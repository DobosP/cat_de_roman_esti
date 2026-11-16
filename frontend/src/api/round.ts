export type BoardPlaceTier = "perfect" | "top_10" | "top_half" | "completed";

export interface BoardPlace {
  better_than_pct: number;
  tier: BoardPlaceTier;
  rounds: number;
}

/** Additive round counters shared by the six word games. */
export interface RoundCounters {
  steps?: number;
  hints_left?: number;
  hint_level?: number;
  /** Present on eligible finished daily wins only. */
  place?: BoardPlace;
}

export interface PerfectRoundCounters extends RoundCounters {
  perfect?: boolean;
}
