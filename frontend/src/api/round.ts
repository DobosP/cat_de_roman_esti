/** Additive round counters shared by the six word games. */
export interface RoundCounters {
  steps?: number;
  hints_left?: number;
  hint_level?: number;
}

export interface PerfectRoundCounters extends RoundCounters {
  perfect?: boolean;
}
