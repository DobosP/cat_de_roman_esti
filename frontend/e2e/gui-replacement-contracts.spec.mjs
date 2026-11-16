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

test("results sheet shows steps, hides legacy points and preserves the stored history", async ({ page }) => {
  const entry = { score: 900, detail: "Rezultat local de test", at: Date.parse(FIXED_TIME), daily: DAY, steps: 2 };
  const legacy = { ...entry, score: 511, steps: undefined, at: entry.at - 1000 };
  const history = { intrusul: { best: entry, recent: [entry, legacy], played: 2 } };
  await localHistory(page, history);
  await page.goto("/");
  await expect(page.locator("dialog.results-history")).toHaveCount(0);
  const trigger = page.getByRole("button", { name: "Rezultatele mele" });
  await trigger.click();
  const dialog = page.getByRole("dialog", { name: "Rezultatele mele" });
  await expect(dialog.getByRole("listitem")).toHaveCount(1);
  await expect(dialog.getByRole("listitem")).toContainText("Intrusul");
  await expect(dialog.getByRole("listitem")).toContainText("2 pași");
  await expect(dialog).not.toContainText(/900|511|puncte/i);
  await expect(dialog.getByRole("button", { name: "Exportă istoricul" })).toBeEnabled();
  await expect(dialog.getByRole("button", { name: "Importă istoricul" })).toBeEnabled();
  await page.keyboard.press("Escape");
  await expect(dialog).toHaveCount(0);
  await expect(trigger).toBeFocused();
  expect(await page.evaluate((key) => localStorage.getItem(key), SCORE_KEY)).toBe(JSON.stringify(history));
});
