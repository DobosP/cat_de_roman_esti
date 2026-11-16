// M0 replacements for challenge lineage and successful creation-option parity.
// Authored NOT RUN. The lineage-cap case is explicitly a DOM presentation
// projection, not qualification of server recipes, challenge scoring or exploration.
import { test, expect } from "@playwright/test";
import {
  games, gameURL, solution, deterministicStarts, start, act, solve,
  openGameOptions, openAlchemyDisclosure,
} from "./games.mjs";

const game = games.find(({ key }) => key === "alchimie");
const football = { ...game, packId: "al_sport_083" };
const themed = { ...game, packId: "al_arta_cultura_008" };
const CREATE = "/api/wordgames/alchimie/games";
const createdReply = (page) => page.waitForResponse((response) =>
  response.request().method() === "POST" && new URL(response.url()).pathname === CREATE);
const dialog = (page) => page.getByRole("dialog", { name: "Cum se joacă Alchimie", exact: true });

async function applyThemedFreeOptions(page) {
  await openGameOptions(page, game);
  const difficulty = dialog(page).getByLabel("Dificultate");
  await difficulty.selectOption("normal");
  await expect(difficulty).toHaveValue("normal");
  const theme = dialog(page).getByLabel("Temă");
  await expect(theme.locator('option[value="arta_cultura"]')).toHaveCount(1);
  await theme.selectOption("arta_cultura");
  await expect(theme).toHaveValue("arta_cultura");
}

async function nextGame(page, name) {
  const response = createdReply(page);
  await page.getByRole("button", { name, exact: true }).click();
  const reply = await response;
  expect(reply.status()).toBe(200);
  return reply.json();
}

async function themedStart(page) {
  const plan = solution(themed);
  expect(plan.query.category).toBe("arta_cultura");
  expect(plan.query.difficulty).toBe("normal");
  await deterministicStarts(page, game);
  const originalRequests = [];
  await page.route((url) => url.pathname === CREATE, async (route) => {
    if (route.request().method() !== "POST") return route.continue();
    const original = new URL(route.request().url());
    originalRequests.push(Object.fromEntries(original.searchParams));
    // Stabilize the reviewed board without replacing the actual UI options.
    original.searchParams.set("seed", original.searchParams.has("category") ? plan.query.seed : "38");
    await route.continue({ url: original.toString() });
  });
  await start(page, game);
  await applyThemedFreeOptions(page);
  const state = await nextGame(page, "Alt joc");
  expect(state.difficulty).toBe("normal");
  expect(state.board_category).toBe("arta_cultura");
  expect(state.target.label).toBe(plan.initial.target.label);
  await expect(page.locator(game.board)).toBeVisible();
  expect(originalRequests).toHaveLength(2);
  expect(originalRequests[1]).toMatchObject({ difficulty: "normal", category: "arta_cultura" });
  expect(originalRequests[1].daily).toBeUndefined();
  return { state, originalRequests, plan };
}

test("challenge lineage DOM presentation caps at12, orders newest first and groups only consecutive parent sets", async ({ page }, testInfo) => {
  await deterministicStarts(page, football);
  const initial = await start(page, football);
  // This existing challenge has nine recipe pairs, so it cannot prove a native
  // >12 reaction history. Ground the presentation fixture in a real earned item.
  expect(initial.recipe_summary.pairs).toBe(9);
  const discovery = await act(page, football, solution(football).steps[0]);
  expect(discovery.status()).toBe(200);
  const earned = await discovery.json();
  expect(earned.won).toBe(false);
  expect(earned.discovered.length).toBeGreaterThan(0);
  const discoveredIds = new Set(earned.discovered.map((item) => item.id));
  const template = earned.inventory.find((item) => discoveredIds.has(item.id)
    && Array.isArray(item.parents) && item.parents.length === 2);
  expect(template).toBeDefined();
  const starters = initial.inventory.filter((item) => item.parents === null);
  expect(starters.length).toBeGreaterThanOrEqual(6);
  const pairs = [];
  for (let left = 0; left < starters.length; left += 1) {
    for (let right = left + 1; right < starters.length; right += 1) {
      pairs.push([starters[left], starters[right]].map(({ id, label }) => ({ id, label })));
    }
  }
  expect(pairs.length).toBeGreaterThanOrEqual(13);
  const crafted = [], labels = [];
  const append = (index, parents, suffix = "") => {
    const label = `Lineage projection result ${index}${suffix}`;
    const item = { ...template, id: `lineage-projection-${index}${suffix}`, label,
      parents, links: [], depleted: true, useful: false, ready: false };
    crafted.push(item); labels.push(label);
  };
  for (let index = 0; index < 13; index += 1) append(index, pairs[index]);
  // Reversed consecutive parents still form one reaction with two results.
  append(12, [...pairs[12]].reverse(), "-second");
  // The first parent set reappears later: grouping it globally would be wrong.
  append(13, pairs[0]);
  const presentation = { ...earned, inventory: [...initial.inventory, ...crafted] };
  await testInfo.attach("challenge-lineage-presentation-scope", {
    body: JSON.stringify({ scope: "NON-NATIVE DOM presentation projection",
      native_game_id: initial.game_id, native_recipe_pairs: initial.recipe_summary.pairs,
      native_earned_item_id: template.id, projected_results: crafted.length,
      projected_reaction_groups: 14, validates_server_recipe_or_score_semantics: false }, null, 2),
    contentType: "application/json",
  });
  await page.route(`**${gameURL(game, initial.game_id)}`, async (route) => {
    expect(route.request().method()).toBe("GET");
    await route.fulfill({ json: presentation });
  });
  await page.reload();
  await expect(page.locator(game.board)).toBeVisible();
  await expect(dialog(page)).toBeHidden();
  await expect(page.locator(".alchemy-reaction-history")).toBeHidden();
  await openAlchemyDisclosure(page, ".alchemy-discoveries");
  // The same bounded, consecutive-grouped history now opens in one flat switch.
  const discoveries = page.locator(".alchemy-reaction-history");
  expect((await page.getByRole("button", { name: "Cuvinte", exact: true }).boundingBox()).height).toBeGreaterThanOrEqual(44);
  const rows = discoveries.locator(".alchemy-reaction-row");
  await expect(rows).toHaveCount(12);
  const latest = rows.first();
  const earlier = discoveries.locator(".alchemy-reaction-row:nth-child(n+2)");
  await expect(earlier).toHaveCount(11);
  await expect(latest.locator(".alchemy-reaction-result")).toHaveText([labels.at(-1)]);
  await expect(earlier.nth(0).locator(".alchemy-reaction-result")).toHaveText(["Lineage projection result 12", "Lineage projection result 12-second"]);
  const ordered = await earlier.locator(".alchemy-reaction-result").allTextContents();
  expect(ordered.map((label) => label.trim())).toEqual([
    "Lineage projection result 12", "Lineage projection result 12-second",
    ...Array.from({ length: 10 }, (_, index) => `Lineage projection result ${11 - index}`),
  ]);
  await expect(discoveries.getByText("Lineage projection result 0", { exact: true })).toHaveCount(0);
  await expect(discoveries.getByText("Lineage projection result 1", { exact: true })).toHaveCount(0);
  for (const result of await discoveries.locator(".alchemy-reaction-result").all()) {
    await expect(result).toBeDisabled();
    expect((await result.boundingBox()).height).toBeGreaterThanOrEqual(44);
  }
});

test("successful Alt joc keeps the nondefault challenge category and difficulty in the real create request", async ({ page }) => {
  const { state, originalRequests } = await themedStart(page);
  await openGameOptions(page, game);
  const next = await nextGame(page, "Alt joc");
  expect(next.game_id).not.toBe(state.game_id);
  expect(next.difficulty).toBe("normal");
  expect(next.board_category).toBe("arta_cultura");
  expect(next.daily).toBeFalsy();
  expect(originalRequests).toHaveLength(3);
  expect(originalRequests[2]).toMatchObject({ difficulty: "normal", category: "arta_cultura" });
  expect(originalRequests[2].daily).toBeUndefined();
  await expect(page.locator(game.board)).toBeVisible();
  await expect.poll(() => page.evaluate(() => localStorage.getItem("cat_active_game_v1_alchimie"))).toBe(next.game_id);
});

test("successful solved-challenge replay keeps the nondefault category and difficulty", async ({ page }) => {
  const { state, originalRequests, plan } = await themedStart(page);
  const won = await solve(page, themed, plan.steps);
  expect(won.won).toBe(true);
  await expect(page.getByRole("heading", { name: "Ai făurit ținta!", exact: true })).toBeVisible();
  const next = await nextGame(page, "Încă o rundă");
  expect(next.game_id).not.toBe(state.game_id);
  expect(next.difficulty).toBe("normal");
  expect(next.board_category).toBe("arta_cultura");
  expect(next.won).toBe(false);
  expect(next.daily).toBeFalsy();
  expect(originalRequests).toHaveLength(3);
  expect(originalRequests[2]).toMatchObject({ difficulty: "normal", category: "arta_cultura" });
  expect(originalRequests[2].daily).toBeUndefined();
  await expect(page.locator(game.board)).toBeVisible();
  await expect(page.getByRole("heading", { name: "Ai făurit ținta!", exact: true })).toHaveCount(0);
});

test("the real daily starts at Ușor and ignores the stored free-round theme", async ({ page }) => {
  const day = "2026-10-08";
  await page.clock.setFixedTime(new Date(day + "T12:00:00.000Z"));
  await page.addInitScript(() => {
    localStorage.setItem("cat_free_v2_alchimie", JSON.stringify({ difficulty: "normal", category: "arta_cultura" }));
  });
  const originalRequests = [];
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (request.method() === "POST" && url.pathname === CREATE) originalRequests.push(Object.fromEntries(url.searchParams));
  });
  const state = await start(page, { ...game, daily: day });
  expect(originalRequests).toHaveLength(1);
  expect(originalRequests[0]).toMatchObject({ daily: day, difficulty: "usor" });
  expect(originalRequests[0].category).toBeUndefined();
  expect(state.daily).toBe(day);
  expect(state.difficulty).toBe("usor");
  await openGameOptions(page, game);
  await expect(dialog(page).getByLabel("Dificultate")).toHaveValue("normal");
  await expect(dialog(page).getByLabel("Temă")).toHaveValue("arta_cultura");
});
