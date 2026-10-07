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
const difficultyGroup = (page) => page.getByRole("group", { name: "DIFICULTATE", exact: true });
const categoryGroup = (page) => page.getByRole("group", { name: "CATEGORIE", exact: true });

async function chooseNormal(page) {
  await openGameOptions(page, game, { setup: true });
  const normal = difficultyGroup(page).getByRole("button", { name: /^Normal\b/ });
  await normal.click();
  await expect(normal).toHaveAttribute("aria-pressed", "true");
}

async function themedStart(page) {
  const plan = solution(themed);
  expect(plan.query.category).toBe("arta_cultura");
  expect(plan.query.difficulty).toBe("normal");
  const originalRequests = [];
  await page.route(`**${CREATE}?*`, async (route) => {
    const original = new URL(route.request().url());
    originalRequests.push(Object.fromEntries(original.searchParams));
    // Stabilize the approved real board by its native selected seed. Never
    // replace category/difficulty: that would hide a product option regression.
    original.searchParams.set("seed", plan.query.seed);
    await route.continue({ url: original.toString() });
  });
  await page.goto(game.path);
  await chooseNormal(page);
  const theme = categoryGroup(page).getByRole("button", { name: "Artă și cultură", exact: true });
  await theme.click();
  await expect(theme).toHaveAttribute("aria-pressed", "true");
  const response = createdReply(page);
  await page.getByRole("button", { name: /^Joacă(?: →)?$/ }).click();
  const reply = await response;
  expect(reply.status()).toBe(200);
  const state = await reply.json();
  expect(state.difficulty).toBe("normal");
  expect(state.board_category).toBe("arta_cultura");
  expect(state.target.label).toBe(plan.initial.target.label);
  await expect(page.locator(game.board)).toBeVisible();
  expect(originalRequests).toHaveLength(1);
  expect(originalRequests[0]).toMatchObject({ difficulty: "normal", category: "arta_cultura" });
  expect(originalRequests[0].daily).toBeUndefined();
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
  await expect(page.locator(".alchemy-menu")).not.toHaveAttribute("open");
  await expect(page.locator(".alchemy-discoveries")).not.toHaveAttribute("open");
  await openAlchemyDisclosure(page, ".alchemy-discoveries");
  const discoveries = page.locator(".alchemy-discoveries");
  await expect(discoveries).toContainText("12 reacții păstrate");
  const history = page.locator(".alchemy-reaction-log");
  await expect(history).not.toHaveAttribute("open");
  await expect(history.locator(":scope > summary")).toHaveText("Vezi jurnalul (12)");
  expect((await history.locator(":scope > summary").boundingBox()).height).toBeGreaterThanOrEqual(44);
  await history.locator(":scope > summary").click();
  const latest = discoveries.locator(":scope > .row.wrap").filter({ has: page.locator(".alchemy-reaction-result") });
  const earlier = history.locator(".col > .row.wrap");
  await expect(latest).toHaveCount(1);
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
  await openAlchemyDisclosure(page, ".alchemy-menu");
  const response = createdReply(page);
  await page.getByRole("button", { name: "⚗ Alt joc", exact: true }).click();
  const reply = await response;
  expect(reply.status()).toBe(200);
  const next = await reply.json();
  expect(next.game_id).not.toBe(state.game_id);
  expect(next.difficulty).toBe("normal");
  expect(next.board_category).toBe("arta_cultura");
  expect(next.daily).toBeFalsy();
  expect(originalRequests).toHaveLength(2);
  expect(originalRequests[1]).toMatchObject({ difficulty: "normal", category: "arta_cultura" });
  expect(originalRequests[1].daily).toBeUndefined();
  await expect(page.locator(game.board)).toBeVisible();
  expect(await page.evaluate(() => localStorage.getItem("cat_active_game_v1_alchimie"))).toBe(next.game_id);
});

test("successful solved-challenge replay keeps the nondefault category and difficulty", async ({ page }) => {
  const { state, originalRequests, plan } = await themedStart(page);
  const won = await solve(page, themed, plan.steps);
  expect(won.won).toBe(true);
  await expect(page.getByRole("heading", { name: "Ai făurit ținta!", exact: true })).toBeVisible();
  const response = createdReply(page);
  await page.getByRole("button", { name: "Încă unul →", exact: true }).click();
  const reply = await response;
  expect(reply.status()).toBe(200);
  const next = await reply.json();
  expect(next.game_id).not.toBe(state.game_id);
  expect(next.difficulty).toBe("normal");
  expect(next.board_category).toBe("arta_cultura");
  expect(next.won).toBe(false);
  expect(next.daily).toBeFalsy();
  expect(originalRequests).toHaveLength(2);
  expect(originalRequests[1]).toMatchObject({ difficulty: "normal", category: "arta_cultura" });
  expect(originalRequests[1].daily).toBeUndefined();
  await expect(page.locator(game.board)).toBeVisible();
  await expect(page.getByRole("heading", { name: "Ai făurit ținta!", exact: true })).toHaveCount(0);
});

test("the real daily challenge create request uses the selected nondefault difficulty", async ({ page }) => {
  const day = "2026-10-08";
  await page.clock.setFixedTime(new Date("2026-10-08T12:00:00.000Z"));
  const originalRequests = [];
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (request.method() === "POST" && url.pathname === CREATE) originalRequests.push(Object.fromEntries(url.searchParams));
  });
  await page.goto(game.path);
  await chooseNormal(page);
  const response = createdReply(page);
  await page.getByRole("button", { name: "Provocarea zilei", exact: true }).click();
  const reply = await response;
  expect(reply.status()).toBe(200);
  const state = await reply.json();
  expect(originalRequests).toHaveLength(1);
  expect(originalRequests[0]).toMatchObject({ daily: day, difficulty: "normal" });
  expect(originalRequests[0].category).toBeUndefined();
  expect(state.daily).toBe(day);
  expect(state.difficulty).toBe("normal");
  await expect(page.locator(game.board)).toBeVisible();
});
