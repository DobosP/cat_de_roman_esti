// scores/record.ts — mechanical module boundary; declarations copied from scores.ts.

import type { Board, GameRecord, ScoreEntry } from "./core";
import { browserStorage, loadRaw, normalizeBoard, normalizeEntry, normalizeStreak, advanceStreak, isDailyKey, capPuzzles, save, isRecord, GAME_CAP, RECENT_CAP, DERIVED_STARTER_COMPLETIONS, STREAK_KEY, RECEIPTS_KEY } from "./core";

export interface RecordOutcome {
  isBest: boolean;
  isPuzzleBest: boolean;
  prev: ScoreEntry | null;
  prevPuzzle: ScoreEntry | null;
}

export interface RecordScoreOptions {
  /** Stable, deterministic key for this exact completed puzzle/run shape. */
  puzzleKey?: string | null;
  /** Difficulty tier for history filtering. */
  difficulty?: string | null;
  /** YYYY-MM-DD for daily history filtering. */
  daily?: string | null;
  /** Category/theme key for category-scoped runs. */
  category?: string | null;
}

interface ScoreReceipt {
  id: string;
  at: number;
}

type ScoreReceiptLedger = Record<string, ScoreReceipt[]>;

interface ScoreLockManager {
  request<T>(name: string, callback: () => T | PromiseLike<T>): Promise<T>;
}

interface CompletionRuntime {
  /** Test seam; production resolves the same-origin browser storage. */
  storage?: Pick<Storage, "getItem" | "setItem" | "removeItem"> | null;
  /** Test seam; production uses `navigator.locks` when supported. */
  locks?: ScoreLockManager | null;
  /** Test seam for deterministic expiry checks. */
  now?: number;
}

const SCORE_STORE_LOCK = "cat_wordgame_scores_v1_transaction";

const RECEIPT_CAP_PER_GAME = 1_000;

const RECEIPT_TTL_MS = 24 * 60 * 60 * 1_000;

export async function recordScoreCompletionOnce(
  game: string,
  gameId: string,
  score: number,
  detail: string,
  options: RecordScoreOptions = {},
  runtime: CompletionRuntime = {},
): Promise<RecordOutcome | null> {
  const storage = runtime.storage === undefined ? browserStorage() : runtime.storage;
  const locks = runtime.locks === undefined ? browserLocks() : runtime.locks;
  const receiptGame = normalizeReceiptGame(game);
  const receiptId = normalizeReceiptId(gameId);

  const transaction = () => {
    // Another tab can acquire first while this claim waits; compare its receipt
    // against the commit-time clock rather than this invocation's older time.
    const now = Number.isFinite(runtime.now) ? Math.max(0, runtime.now ?? 0) : Date.now();
    if (!storage || !receiptGame || !receiptId) {
      return recordScore(game, score, detail, options);
    }
    const raw = loadRaw(storage);
    const ledger = normalizeReceiptLedger(raw[RECEIPTS_KEY], now);
    if (ledger[receiptGame]?.some((receipt) => receipt.id === receiptId)) return null;

    const update = buildScoreUpdate(raw, game, score, detail, options);
    ledger[receiptGame] = [{ id: receiptId, at: now }, ...(ledger[receiptGame] ?? [])]
      .slice(0, RECEIPT_CAP_PER_GAME);
    save(update.board, update.streak, { version: 1, games: ledger }, storage);
    return update.outcome;
  };

  if (!locks) return transaction();
  try {
    return await locks.request(SCORE_STORE_LOCK, transaction);
  } catch {
    // Lock acquisition can be unavailable despite an exposed API. Preserve local play with
    // the same receipt check; concurrent tabs are best-effort on this path.
    return transaction();
  }
}

export function recordScore(
  game: string,
  score: number,
  detail: string,
  options: RecordScoreOptions = {},
): RecordOutcome {
  const raw = loadRaw();
  const update = buildScoreUpdate(raw, game, score, detail, options);
  save(update.board, update.streak, raw[RECEIPTS_KEY]);
  return update.outcome;
}

function buildScoreUpdate(
  raw: Record<string, unknown>,
  game: string,
  score: number,
  detail: string,
  options: RecordScoreOptions,
): { board: Board; streak: unknown; outcome: RecordOutcome } {
  const board = normalizeBoard(raw);
  const rec: GameRecord = board[game] ?? {
    best: null,
    played: 0,
    recent: [],
    completedNonDaily: false,
    nonDailyCompletions: 0,
    nonDailyWon: false,
  };
  const prev = rec.best;
  const puzzleKey = options.puzzleKey?.trim() || null;
  const entry = normalizeEntry({
    score,
    detail,
    at: Date.now(),
    puzzleKey: puzzleKey ?? undefined,
    difficulty: options.difficulty?.trim() || undefined,
    daily: options.daily?.trim() || undefined,
    category: options.category?.trim() || undefined,
  });
  if (!entry) {
    return {
      board,
      streak: raw[STREAK_KEY],
      outcome: { isBest: false, isPuzzleBest: false, prev, prevPuzzle: null },
    };
  }
  // A 0-point finish is a loss (or a win with every penalty spent): history, never a record.
  const isBest = score > 0 && (prev === null || score > prev.score);
  const prevPuzzle = puzzleKey ? (rec.puzzles?.[puzzleKey] ?? null) : null;
  const isPuzzleBest =
    score > 0 && puzzleKey !== null && (prevPuzzle === null || score > prevPuzzle.score);
  rec.played += 1;
  rec.recent = [entry, ...rec.recent].slice(0, RECENT_CAP);
  if (!entry.daily) {
    rec.completedNonDaily = true;
    rec.nonDailyCompletions = Math.min(
      DERIVED_STARTER_COMPLETIONS,
      rec.nonDailyCompletions + 1,
    );
    if (entry.score > 0) rec.nonDailyWon = true;
  }
  if (isBest) rec.best = entry;
  // A first daily attempt keeps its puzzle row even at 0 points, so the daily circuit
  // still counts it after later plays push it out of `recent`; it is never a record.
  if (puzzleKey && (isPuzzleBest || (entry.daily && prevPuzzle === null))) {
    rec.puzzles = { ...(rec.puzzles ?? {}), [puzzleKey]: entry };
    rec.puzzles = capPuzzles(rec.puzzles);
  }
  board[game] = rec;
  // Local daily streak: advance only on a valid daily completion (any game counts).
  const dailyDay = entry.daily && isDailyKey(entry.daily) ? entry.daily : null;
  const streak = dailyDay
    ? advanceStreak(normalizeStreak(raw[STREAK_KEY], board), dailyDay)
    : raw[STREAK_KEY];
  return { board, streak, outcome: { isBest, isPuzzleBest, prev, prevPuzzle } };
}

function browserLocks(): ScoreLockManager | null {
  try {
    if (typeof navigator === "undefined" || !navigator.locks) return null;
    return navigator.locks as unknown as ScoreLockManager;
  } catch {
    return null;
  }
}

function normalizeReceiptLedger(value: unknown, now: number): ScoreReceiptLedger {
  try {
    const source = isRecord(value) && isRecord(value.games) ? value.games : {};
    const ledger: ScoreReceiptLedger = {};
    for (const [rawGame, rawReceipts] of Object.entries(source).slice(0, GAME_CAP)) {
      const game = normalizeReceiptGame(rawGame);
      if (!game || !Array.isArray(rawReceipts)) continue;
      const byId = new Map<string, ScoreReceipt>();
      for (const rawReceipt of rawReceipts) {
        if (!isRecord(rawReceipt)) continue;
        const id = normalizeReceiptId(rawReceipt.id);
        const at = typeof rawReceipt.at === "number" ? rawReceipt.at : Number.NaN;
        if (!id || !Number.isFinite(at) || at <= now - RECEIPT_TTL_MS || at > now) continue;
        const previous = byId.get(id);
        if (!previous || at > previous.at) byId.set(id, { id, at });
      }
      const receipts = [...byId.values()]
        .sort((left, right) => right.at - left.at || left.id.localeCompare(right.id))
        .slice(0, RECEIPT_CAP_PER_GAME);
      if (receipts.length) ledger[game] = receipts;
    }
    return ledger;
  } catch {
    return {};
  }
}

function normalizeReceiptGame(value: unknown): string | null {
  if (typeof value !== "string" || !/^[a-z0-9_-]{1,64}$/.test(value)) return null;
  return value;
}

function normalizeReceiptId(value: unknown): string | null {
  if (typeof value !== "string" || !/^[A-Za-z0-9-]{1,128}$/.test(value)) return null;
  return value;
}
