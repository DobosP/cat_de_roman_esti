import { CATEGORY_STYLES } from "./categories";
import type { GameKey } from "./games";
import type { Difficulty } from "./api/meta";

interface DailyStatus { started: boolean; done: boolean }
interface SavedRound { game_id: string; daily?: string; terminal: boolean }
export interface FreeOptions { difficulty: Difficulty; category: string | null }

type Entry =
  | { kind: "resume"; gameId: string; daily?: string }
  | { kind: "daily"; daily: string }
  | { kind: "free" };

const dayPattern = /^\d{4}-\d{2}-\d{2}$/u;
const emptyStatus: DailyStatus = { started: false, done: false };

export function localDay(date = new Date()): string {
  return [date.getFullYear(), date.getMonth() + 1, date.getDate()]
    .map((part, index) => String(part).padStart(index ? 2 : 4, "0"))
    .join("-");
}

function read(key: string): string | null {
  try { return localStorage.getItem(key); } catch { return null; }
}

function write(key: string, value: string): void {
  try { localStorage.setItem(key, value); } catch { /* storage is optional */ }
}

const dailyKey = (game: GameKey) => `cat_daily_v2_${game}`;

function dailyRecords(game: GameKey): Record<string, 1 | 2> {
  try {
    const value: unknown = JSON.parse(read(dailyKey(game)) ?? "{}");
    if (!value || typeof value !== "object" || Array.isArray(value)) return {};
    return Object.fromEntries(Object.entries(value)
      .filter(([day, state]) => dayPattern.test(day) && (state === 1 || state === 2))
      .sort(([a], [b]) => b.localeCompare(a)).slice(0, 31));
  } catch {
    return {};
  }
}

export function dailyStatus(game: GameKey, day: string): DailyStatus {
  const value = dailyRecords(game)[day];
  return value ? { started: true, done: value === 2 } : emptyStatus;
}

function updateDaily(game: GameKey, day: string, state: 1 | 2): void {
  if (!dayPattern.test(day)) return;
  const records = dailyRecords(game);
  if ((records[day] ?? 0) >= state) return;
  records[day] = state;
  const recent = Object.entries(records).sort(([a], [b]) => b.localeCompare(a)).slice(0, 31);
  write(dailyKey(game), JSON.stringify(Object.fromEntries(recent)));
}

export function markDailyStarted(game: GameKey, day: string): void {
  updateDaily(game, day, 1);
}

export function markDailyDone(game: GameKey, day: string): void {
  updateDaily(game, day, 2);
}

export function roundEntry(game: GameKey, day: string, saved?: SavedRound): Entry {
  const unfinished = saved && !saved.terminal ? saved : undefined;
  if (unfinished?.daily) {
    return { kind: "resume", gameId: unfinished.game_id, daily: unfinished.daily };
  }
  if (!dailyStatus(game, day).done) return { kind: "daily", daily: day };
  return unfinished ? { kind: "resume", gameId: unfinished.game_id } : { kind: "free" };
}

function freeOptions(value: Partial<FreeOptions>): FreeOptions {
  const difficulty = value.difficulty === "normal" || value.difficulty === "greu"
    ? value.difficulty : "usor";
  const category = typeof value.category === "string" && Object.prototype.hasOwnProperty.call(CATEGORY_STYLES, value.category)
    && value.category !== "mixed" ? value.category : null;
  return { difficulty, category };
}

export function readFreeOptions(game: GameKey): FreeOptions {
  try {
    return freeOptions(JSON.parse(read(`cat_free_v2_${game}`) ?? "{}"));
  } catch {
    return freeOptions({});
  }
}

export function writeFreeOptions(game: GameKey, options: FreeOptions): void {
  write(`cat_free_v2_${game}`, JSON.stringify(freeOptions(options)));
}
