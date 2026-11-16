// Authored DOM contracts for source-test retirement; NOT RUN or qualification.
// Uses the real app with explicit synthetic API/local-history presentation data.
// Adult fixture identities are fictional; this does not activate production accounts.
// Keep old source tests and sealed original16/78 unchanged until actual equivalent
// browser execution passes. Discovery and the reviewed inventory delta are pending.
import { test, expect } from "@playwright/test";
import { tabTo } from "./games.mjs";

const SCORE_KEY = "cat_wordgame_scores_v1";
const DAY = "2026-10-07";
const FIXED_TIME = "2026-10-07T12:00:00.000Z";
const DISABLED_ME = { accounts_enabled: false, authenticated: false, user: null };

async function anonymous(page) {
  await page.route("**/api/me", (route) => route.fulfill({ json: DISABLED_ME }));
}

async function chooseRankingGame(page, key, title) {
  const select = page.getByRole("combobox", { name: "Alege jocul", exact: true });
  if (await select.isVisible()) await select.selectOption(key);
  else await page.getByRole("group", { name: "Alege jocul", exact: true })
    .getByRole("button", { name: title, exact: true }).click();
}

function heldReply() {
  let arrive, release;
  const requested = new Promise((resolve) => { arrive = resolve; });
  const waiting = new Promise((resolve) => { release = resolve; });
  return {
    requested, release,
    handler: async (route, response) => {
      arrive();
      await waiting;
      await route.fulfill(response);
    },
  };
}

const rankingBody = (game, entries = [], me = null) => ({ game, entries, me });

test("ranking clears old rows, announces a held failure and retries the selected game once", async ({ page }) => {
  await anonymous(page);
  const requests = [], failure = heldReply(), retry = heldReply();
  let intrusulReads = 0;
  await page.route("**/api/ranking?*", async (route) => {
    const url = new URL(route.request().url());
    requests.push({ method: route.request().method(), game: url.searchParams.get("game"), limit: url.searchParams.get("limit") });
    if (url.searchParams.get("game") === "alchimie") {
      await route.fulfill({ json: rankingBody("alchimie", [{ rank: 1, name: "Earlier public row", score: 600, is_me: false }]) });
    } else if (++intrusulReads === 1) {
      await failure.handler(route, { status: 503, json: { detail: "Unavailable presentation fixture" } });
    } else {
      await retry.handler(route, { json: rankingBody("intrusul", [{ rank: 1, name: "Recovered public row", score: 800, is_me: false }]) });
    }
  });
  try {
    await page.goto("/clasament");
    await expect(page.getByText("Earlier public row", { exact: true })).toBeVisible();
    await chooseRankingGame(page, "intrusul", "Intrusul");
    await failure.requested;
    const loading = page.getByRole("status").filter({ hasText: "Se încarcă…" });
    await expect(loading).toHaveAttribute("aria-busy", "true");
    await expect(loading).toHaveAttribute("aria-live", "polite");
    await expect(page.getByText("Earlier public row", { exact: true })).toHaveCount(0);
    failure.release();
    await expect(page.getByRole("alert")).toHaveText("Nu am putut încărca clasamentul.");
    const again = page.getByRole("button", { name: "Reîncearcă", exact: true });
    await expect(again).toBeEnabled();
    expect((await again.boundingBox()).height).toBeGreaterThanOrEqual(44);
    await tabTo(page, again);
    await page.keyboard.press("Space");
    await retry.requested;
    await expect(loading).toHaveAttribute("aria-busy", "true");
    await expect(page.getByRole("alert")).toHaveCount(0);
    await expect(again).toHaveCount(0);
    retry.release();
    await expect(page.getByText("Recovered public row", { exact: true })).toBeVisible();
    await expect(loading).toHaveCount(0);
    expect(requests).toEqual([
      { method: "GET", game: "alchimie", limit: "50" },
      { method: "GET", game: "intrusul", limit: "50" },
      { method: "GET", game: "intrusul", limit: "50" },
    ]);
  } finally { failure.release(); retry.release(); }
});

test("an unavailable ranking offers Home instead of an ineffective retry", async ({ page }) => {
  await anonymous(page);
  const reads = [];
  await page.route("**/api/ranking?*", async (route) => {
    reads.push(route.request().url());
    await route.fulfill({ status: 404, json: { detail: "Accounts disabled in this fixture" } });
  });
  await page.goto("/clasament");
  await expect(page.getByRole("alert")).toHaveText("Clasamentul nu este activ aici.");
  await expect(page.getByRole("button", { name: "Reîncearcă", exact: true })).toHaveCount(0);
  const home = page.getByRole("button", { name: "Acasă →", exact: true });
  await expect(home).toBeEnabled();
  expect((await home.boundingBox()).height).toBeGreaterThanOrEqual(44);
  await home.click();
  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByRole("heading", { name: "Cât de român ești?", exact: true })).toBeVisible();
  expect(reads).toHaveLength(1);
});

test("ranking identifies the viewer by is_me and retains an off-list self card despite tied ranks", async ({ page }) => {
  await anonymous(page);
  await page.route("**/api/ranking?*", async (route) => {
    const game = new URL(route.request().url()).searchParams.get("game");
    const entries = [
      { rank: 1, name: "Other tied player", score: 900, is_me: false },
      { rank: 1, name: game === "alchimie" ? "Viewer public nickname" : "Another tied player", score: 900, is_me: game === "alchimie" },
    ];
    await route.fulfill({ json: rankingBody(game, entries, { rank: 1, score: 900 }) });
  });
  await page.goto("/clasament");
  await expect(page.getByText("Recorduri verificate de joc · maximum 1000 de puncte.", { exact: true })).toBeVisible();
  const highlighted = page.locator(".rank-row--me");
  await expect(highlighted).toHaveCount(1);
  await expect(highlighted).toContainText("Viewer public nickname");
  await expect(highlighted).not.toContainText("Other tied player");
  await expect(page.getByText("Locul tău: #1", { exact: true })).toHaveCount(0);
  await chooseRankingGame(page, "intrusul", "Intrusul");
  await expect(page.getByText("Another tied player", { exact: true })).toBeVisible();
  await expect(highlighted).toHaveCount(1);
  await expect(highlighted).toContainText("Locul tău: #1");
  await expect(highlighted).toContainText("900 pct");
  await expect(highlighted).not.toContainText("Other tied player");
  await expect(page.getByText("Viewer public nickname", { exact: true })).toHaveCount(0);
});

async function answerRankingPrompt(page, answer) {
  const pendingDialog = page.waitForEvent("dialog");
  const clicked = page.getByRole("menuitem", { name: "Arată-mă în clasament", exact: true }).click();
  const dialog = await pendingDialog;
  let answered = false;
  try {
    expect(dialog.type()).toBe("prompt");
    expect(dialog.message()).toBe("Alege o poreclă pentru clasament:");
    if (answer === null) await dialog.dismiss(); else await dialog.accept(answer);
    answered = true;
  } finally { if (!answered) await dialog.dismiss(); }
  await clicked;
}

test("a private account name cannot enable public ranking without explicit nonblank nickname consent", async ({ page }) => {
  let user = {
    id: 901, email: "adult-fixture@example.invalid", name: "Private fixture name", avatar: "",
    ranking_name: "", display_name: "", show_on_ranking: false, consent_completed: true,
    can_save_progress: false, is_minor: false, parental_consent_required: false,
  };
  const updates = [], scoreTraffic = [];
  page.on("request", (request) => {
    if (new URL(request.url()).pathname === "/api/me/scores") scoreTraffic.push(request.method());
  });
  await page.route("**/api/me", (route) => route.fulfill({ json: { accounts_enabled: true, authenticated: true, user } }));
  await page.route("**/api/me/profile", async (route) => {
    updates.push({ method: route.request().method(), body: route.request().postDataJSON() });
    user = { ...user, ...route.request().postDataJSON() };
    await route.fulfill({ json: { status: "ok", user } });
  });
  await page.goto("/");
  const chip = page.locator(".account-chip");
  await expect(chip).toContainText("Private fixture name");
  await chip.click();
  await expect(page.getByRole("menu")).toBeVisible();
  await answerRankingPrompt(page, null);
  expect(updates).toEqual([]);
  await answerRankingPrompt(page, "   ");
  expect(updates).toEqual([]);
  const updated = page.waitForResponse((response) => response.request().method() === "POST"
    && new URL(response.url()).pathname === "/api/me/profile");
  await answerRankingPrompt(page, "  Public fixture nickname  ");
  expect((await updated).status()).toBe(200);
  await expect(page.getByRole("menuitem", { name: "Ascunde-mă din clasament", exact: true })).toBeVisible();
  await expect(chip).toContainText("Public fixture nickname");
  expect(updates).toEqual([{ method: "POST", body: { display_name: "Public fixture nickname", show_on_ranking: true } }]);
  expect(scoreTraffic).toEqual([]);
});

async function localHistory(page, value) {
  await anonymous(page);
  await page.clock.setFixedTime(new Date(FIXED_TIME));
  await page.addInitScript(({ key, value }) => localStorage.setItem(key, JSON.stringify(value)), { key: SCORE_KEY, value });
}

for (const [length, text] of [[0, null], [1, "🔥 Serie: o zi"], [3, "🔥 Serie: 3 zile"]]) {
  test(`Home renders a local ${length}-day streak with Romanian copy and no history write`, async ({ page }) => {
    const history = { _streak: { lastDate: length ? DAY : "", length } };
    await localHistory(page, history);
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Circuitul de azi", exact: true })).toBeVisible();
    const streak = page.getByText(/^🔥 Serie:/);
    if (text === null) await expect(streak).toHaveCount(0);
    else { await expect(streak).toHaveCount(1); await expect(streak).toHaveText(text); }
    expect(await page.evaluate((key) => localStorage.getItem(key), SCORE_KEY)).toBe(JSON.stringify(history));
  });
}

const DAILY_FIXTURE = [
  ["alchimie", 900], ["intrusul", 800], ["perechi", 700],
  ["conexiuni", 600], ["contexto", 500], ["lant", 0],
];
function completedHistory(count) {
  const history = { _streak: { lastDate: DAY, length: 1 } };
  for (const [game, score] of DAILY_FIXTURE.slice(0, count)) {
    const entry = { score, detail: "Rezultat local de test", at: Date.parse(FIXED_TIME), daily: DAY };
    history[game] = { best: score > 0 ? entry : null, played: 1, recent: [entry],
      completedNonDaily: false, nonDailyCompletions: 0, nonDailyWon: false };
  }
  return history;
}

for (const completed of [5, 6]) {
  const title = completed === 5
    ? "Home with five completed games keeps one daily playable and hides the diploma"
    : "Home grants its local diploma for six completions including a zero-point game";
  test(title, async ({ page, isMobile }) => {
    const history = completedHistory(completed), mutations = [], clipboard = [];
    await localHistory(page, history);
    page.on("request", (request) => {
      if (request.method() === "POST" && new URL(request.url()).pathname.startsWith("/api/")) mutations.push(request.url());
    });
    await page.addInitScript(() => {
      window.__replacementClipboard = [];
      Object.defineProperty(navigator, "clipboard", { configurable: true,
        value: { writeText: async (text) => { window.__replacementClipboard.push(text); } } });
    });
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Circuitul de azi", exact: true })).toBeVisible();
    const progress = page.getByRole("status", { name: `${completed} din 6 jocuri terminate azi, 3500 din 6000 de puncte`, exact: true });
    await expect(progress).toBeVisible();
    await expect(progress).toHaveAttribute("aria-live", "polite");
    const games = page.getByRole("list", { name: "Progresul jocurilor de azi", exact: true });
    await expect(games.getByRole("listitem")).toHaveCount(6);
    await expect(games.getByRole("button")).toHaveCount(completed === 5 ? 1 : 0);
    if (completed === 5) {
      await expect(page.getByText(/^🏆 Diplomă de român/)).toHaveCount(0);
      await expect(page.getByRole("button", { name: "Distribuie", exact: true })).toHaveCount(0);
      const remaining = games.getByRole("button", { name: "Deschide Lanțul Cuvintelor — neterminat azi", exact: true });
      await expect(remaining).toBeEnabled();
      await remaining.click();
      await expect(page).toHaveURL(/\/lant\?challenge=daily$/);
      await expect(page.getByRole("button", { name: "Joacă provocarea zilei", exact: true })).toBeEnabled();
    } else {
      await expect(games.getByRole("listitem", { name: "Lanțul Cuvintelor: terminat azi, 0 puncte", exact: true })).toBeVisible();
      await expect(page.getByText("🏆 Diplomă de român — 07.10.2026", { exact: true })).toBeVisible();
      await expect(page.getByText("Ai închis circuitul de azi: 3500 puncte.", { exact: true })).toBeVisible();
      const share = page.getByRole("button", { name: "Distribuie", exact: true });
      await expect(share).toBeEnabled();
      const coarsePointer = await page.evaluate(() => matchMedia("(pointer: coarse)").matches);
      if (isMobile) expect(coarsePointer).toBe(true);
      if (coarsePointer) expect((await share.boundingBox()).height).toBeGreaterThanOrEqual(44);
      await share.click();
      await expect(page.getByText("Copiat!", { exact: true })).toBeVisible();
      clipboard.push(...await page.evaluate(() => window.__replacementClipboard));
      const origin = new URL(page.url()).origin;
      expect(clipboard).toEqual([`Cât de român ești? Circuit 6/6 azi · 3500 pct · Joacă: ${origin}/`]);
    }
    expect(mutations).toEqual([]);
    expect(await page.evaluate((key) => localStorage.getItem(key), SCORE_KEY)).toBe(JSON.stringify(history));
  });
}
