import { test, expect } from "@playwright/test";
import { games, deterministicStarts, solution, start } from "./games.mjs";

const game = games.find(({ key }) => key === "alchimie");
const escapeRegex = (value) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const inventory = (page) => page.locator(game.board);
const ingredient = (page, label) => inventory(page).getByRole("button", {
  name: new RegExp(`^${escapeRegex(label)}(?:,|$)`),
});
const slot = (page, label) => page.getByRole("button", {
  name: `Scoate ${label} din alambic`, exact: true,
});
const filter = (page, name) => page.getByRole("button", { name: new RegExp(`^${name} `) });
const search = (page) => page.getByRole("searchbox", { name: "Caută în toate conceptele descoperite" });
const combine = (page) => page.getByRole("button", { name: "Combină cele două concepte selectate" });
const fullSelectionMessage = "Ai ales deja două cuvinte. Scoate unul din alambic pentru a-l înlocui.";

async function settle(page) {
  await page.evaluate(async () => {
    await globalThis.document.fonts.ready;
    await Promise.all(globalThis.document.getAnimations().filter((animation) =>
      Number.isFinite(animation.effect?.getComputedTiming().endTime),
    ).map((animation) => animation.finished.catch(() => {})));
  });
}

async function measure(page, testInfo, phase) {
  await settle(page);
  const metrics = await page.evaluate(() => {
    const selectors = [
      ".alchemy-target", ".alchemy-workspace", ".alchemy-bench",
      ".alchemy-inventory-panel", ".alchemy-inventory-grid", ".alchemy-slot",
    ];
    const box = (element) => {
      const rect = element.getBoundingClientRect();
      return { left: rect.left, top: rect.top, right: rect.right, bottom: rect.bottom,
        width: rect.width, height: rect.height };
    };
    const screen = globalThis.document.querySelector(".screen-pad");
    return {
      viewport: { width: globalThis.innerWidth, height: globalThis.innerHeight },
      pageWidth: globalThis.document.documentElement.scrollWidth,
      screen: { ...box(screen), width: screen.clientWidth, scrollWidth: screen.scrollWidth },
      header: box(globalThis.document.querySelector(".game-shell-header")),
      components: selectors.flatMap((selector) =>
        [...globalThis.document.querySelectorAll(selector)].map((element, index) => ({
          selector, index, ...box(element), clientWidth: element.clientWidth,
          scrollWidth: element.scrollWidth,
        }))),
    };
  });
  await testInfo.attach(`${phase}-geometry`, {
    body: JSON.stringify(metrics, null, 2), contentType: "application/json",
  });
  expect(metrics.pageWidth, `${phase}: page has no horizontal scroll`).toBeLessThanOrEqual(metrics.viewport.width);
  expect(metrics.screen.scrollWidth, `${phase}: game has no horizontal scroll`).toBeLessThanOrEqual(metrics.screen.width);
  for (const item of metrics.components) {
    expect(item.scrollWidth, `${phase}: ${item.selector}[${item.index}] text fits its container`)
      .toBeLessThanOrEqual(item.clientWidth + 1);
    expect(item.left, `${phase}: ${item.selector} stays inside the screen`).toBeGreaterThanOrEqual(0);
    expect(item.right, `${phase}: ${item.selector} stays inside the screen`).toBeLessThanOrEqual(metrics.viewport.width);
  }
  return metrics;
}

test.beforeEach(async ({ page }) => deterministicStarts(page, game));

test("the initial workbench shows the target, mixing controls and ingredients together", async ({ page }, testInfo) => {
  const mobile = testInfo.project.name === "mobile";
  await page.setViewportSize({ width: mobile ? 390 : 1280, height: mobile ? 844 : 850 });
  await start(page, game);
  await expect(page.locator(".alchemy-workspace > .alchemy-bench")).toHaveCount(1);
  await expect(page.locator(".alchemy-workspace > .alchemy-inventory-panel")).toHaveCount(1);
  const metrics = await measure(page, testInfo, "initial-workbench");
  const controls = [page.locator(".alchemy-target"), ...await page.locator(".alchemy-slot").all(),
    combine(page), inventory(page).getByRole("button").first()];
  expect(await page.locator(".alchemy-slot").count()).toBe(2);
  for (const control of controls) {
    await expect(control).toBeInViewport({ ratio: 1 });
    const bounds = await control.boundingBox();
    expect(bounds.y, "play controls are below the header").toBeGreaterThanOrEqual(metrics.header.bottom);
    expect(bounds.y + bounds.height, "play controls are visible before scrolling").toBeLessThanOrEqual(metrics.screen.bottom);
  }
  if (mobile) {
    const firstRow = await inventory(page).getByRole("button").evaluateAll((buttons) => {
      const boxes = buttons.map((button) => button.getBoundingClientRect());
      return boxes.filter((box) => Math.abs(box.top - boxes[0].top) < 1)
        .map((box) => ({ top: box.top, bottom: box.bottom }));
    });
    expect(firstRow.length).toBeGreaterThan(0);
    expect(Math.max(...firstRow.map((box) => box.bottom)),
      "at 390×844 the first ingredient row leaves room to continue without scrolling")
      .toBeLessThanOrEqual(700);
  }
  await expect(combine(page)).toBeDisabled();
  await testInfo.attach("initial-workbench", { body: await page.screenshot(), contentType: "image/png" });
});

test("a third ingredient preserves both picks until the player removes one explicitly", async ({ page }) => {
  const initial = await start(page, game);
  const [first, second, third] = initial.inventory.filter((item) => item.useful && !item.depleted);
  expect(third, "seeded board supplies three usable ingredients").toBeDefined();
  await ingredient(page, first.label).click();
  await ingredient(page, second.label).click();
  await ingredient(page, third.label).click();
  await expect(page.locator(".alchemy-feedback")).toContainText(fullSelectionMessage);
  await expect(slot(page, first.label)).toBeVisible();
  await expect(slot(page, second.label)).toBeVisible();
  await expect(slot(page, third.label)).toHaveCount(0);
  await expect(ingredient(page, first.label)).toHaveAttribute("aria-pressed", "true");
  await expect(ingredient(page, second.label)).toHaveAttribute("aria-pressed", "true");
  await expect(ingredient(page, third.label)).toHaveAttribute("aria-pressed", "false");
  await expect(combine(page)).toBeEnabled();

  await slot(page, first.label).focus();
  await page.keyboard.press("Enter");
  await expect(ingredient(page, first.label)).toBeFocused();
  await expect(slot(page, first.label)).toHaveCount(0);
  await expect(page.getByText(fullSelectionMessage, { exact: true })).toHaveCount(0);
  await expect(combine(page)).toBeDisabled();
  await ingredient(page, third.label).click();
  await expect(slot(page, second.label)).toBeVisible();
  await expect(slot(page, third.label)).toBeVisible();
  await expect(combine(page)).toBeEnabled();

  // A search can hide the selected ingredient; removing it still leaves focus in the game.
  await search(page).fill("zzzz-hidden-ingredient");
  await slot(page, second.label).focus();
  await page.keyboard.press("Enter");
  await expect(page.locator(".alchemy-inventory-panel")).toBeFocused();
  await expect(slot(page, second.label)).toHaveCount(0);
  await expect(slot(page, third.label)).toBeVisible();
});

test("emptying a full bench dismisses the old selection warning and allows a fresh pair", async ({ page }) => {
  const initial = await start(page, game);
  const [first, second, third] = initial.inventory.filter((item) => item.useful && !item.depleted);
  expect(third, "seeded board supplies three usable ingredients").toBeDefined();
  for (const item of [first, second, third]) await ingredient(page, item.label).click();
  await expect(page.locator(".alchemy-feedback")).toContainText(fullSelectionMessage);
  await page.getByRole("button", { name: "Golește", exact: true }).click();
  await expect(page.getByText(fullSelectionMessage, { exact: true })).toHaveCount(0);
  await expect(page.getByRole("button", { name: /^Scoate .* din alambic$/ })).toHaveCount(0);
  await expect(combine(page)).toBeDisabled();
  await ingredient(page, third.label).click();
  await ingredient(page, first.label).click();
  await expect(slot(page, third.label)).toBeVisible();
  await expect(slot(page, first.label)).toBeVisible();
  await expect(combine(page)).toBeEnabled();
  await expect(page.getByText(fullSelectionMessage, { exact: true })).toHaveCount(0);
});

for (const view of ["Utile", "Toate"]) {
  test(`a productive combine keeps the ${view} filter and offers its earned result immediately`, async ({ page }) => {
    const initial = await start(page, game);
    const posts = [];
    page.on("request", (request) => {
      if (request.method() === "POST") posts.push(new URL(request.url()).pathname);
    });
    const steps = solution(game).steps;
    expect(steps.length, "this journey has a nonterminal discovery").toBeGreaterThan(1);
    await filter(page, view).click();
    for (const label of steps[0].labels) await ingredient(page, label).click();
    const response = page.waitForResponse((reply) => reply.request().method() === "POST"
      && new URL(reply.url()).pathname === `/api/wordgames/alchimie/games/${initial.game_id}/combine`);
    await combine(page).click();
    const reply = await response;
    expect(reply.status()).toBe(200);
    const state = await reply.json();
    expect(state.won).toBe(false);
    expect(state.discovered.length).toBeGreaterThan(0);
    await expect(filter(page, view)).toHaveAttribute("aria-pressed", "true");
    await expect(filter(page, "Recente")).toHaveAttribute("aria-pressed", "false");
    await expect(page.getByRole("button", { name: /^Scoate .* din alambic$/ })).toHaveCount(0);

    const earned = state.discovered.find((item) => state.inventory.some((owned) =>
      owned.id === item.id && !owned.depleted));
    expect(earned, "the real recipe earns an ingredient that can still be used").toBeDefined();
    const quickResult = page.locator(".alchemy-bench").getByRole("button", {
      name: `Folosește ${earned.label}`, exact: true,
    });
    await expect(quickResult).toBeEnabled();
    await quickResult.click();
    await expect(quickResult).toHaveAttribute("aria-pressed", "true");
    await expect(slot(page, earned.label)).toBeVisible();
    expect(posts, "using an earned ingredient selects locally without repeating its recipe")
      .toEqual([`/api/wordgames/alchimie/games/${initial.game_id}/combine`]);
    await slot(page, earned.label).click();
    await expect(slot(page, earned.label)).toHaveCount(0);
    await expect(quickResult).toHaveAttribute("aria-pressed", "false");

    const result = page.locator(".alchemy-reaction-result").filter({
      hasText: new RegExp(`${escapeRegex(earned.label)}$`),
    }).first();
    await expect(result).toBeEnabled();
    await result.click();
    await expect(result).toHaveAttribute("aria-pressed", "true");
    await expect(slot(page, earned.label)).toBeVisible();
    await expect(filter(page, view)).toHaveAttribute("aria-pressed", "true");
    expect(posts, "the discovery journal also selects locally")
      .toEqual([`/api/wordgames/alchimie/games/${initial.game_id}/combine`]);
  });
}

test("filters leave search mode and an empty search offers a direct way back", async ({ page }) => {
  const initial = await start(page, game);
  const first = initial.inventory.find((item) => item.useful && !item.depleted);
  await search(page).fill(first.label.normalize("NFD").replace(/\p{M}/gu, "").toLocaleLowerCase("ro-RO"));
  await expect(ingredient(page, first.label)).toBeVisible();
  await filter(page, "Toate").click();
  await expect(search(page)).toHaveValue("");
  await expect(inventory(page).getByRole("button")).toHaveCount(initial.inventory.length);

  await search(page).fill("zzzz-fără-rezultat-v92-zzzz");
  await expect(page.getByRole("button", { name: "Șterge căutarea" })).toBeVisible();
  await expect(page.getByText("Niciun concept găsit.", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Șterge căutarea", exact: true }).click();
  await expect(search(page)).toHaveValue("");
  await expect(inventory(page).getByRole("button")).toHaveCount(initial.inventory.length);
  await expect(filter(page, "Toate")).toHaveAttribute("aria-pressed", "true");

  await search(page).fill("zzzz-fără-rezultat-v92-zzzz");
  await filter(page, "Utile").click();
  await expect(search(page)).toHaveValue("");
  await expect(page.getByText("Niciun concept găsit.", { exact: true })).toHaveCount(0);
  await expect(inventory(page).getByRole("button")).toHaveCount(
    initial.inventory.filter((item) => item.useful && !item.depleted).length,
  );
});

test("the workbench wraps long Romanian labels at 320px and 200 percent text", async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 320, height: 850 });
  const initial = await start(page, game);
  for (const item of initial.inventory.filter((item) => item.useful && !item.depleted).slice(0, 2)) {
    await ingredient(page, item.label).click();
  }
  // Presentation stress only: the real session, IDs, recipe and responses stay intact.
  await page.evaluate(() => {
    const longLabel = "Comunitatea românească și tradițiile din viața de zi cu zi";
    globalThis.document.querySelector(".alchemy-target h2").textContent = longLabel;
    globalThis.document.querySelectorAll(".alchemy-slot-label").forEach((element) => {
      element.textContent = longLabel;
    });
    globalThis.document.querySelector(".alchemy-inventory-grid button").textContent = longLabel;
  });
  await measure(page, testInfo, "320-long-labels");
  await page.evaluate(() => { globalThis.document.documentElement.style.fontSize = "200%"; });
  await measure(page, testInfo, "320-long-labels-200-percent");
  await testInfo.attach("320-long-labels-200-percent", { body: await page.screenshot(), contentType: "image/png" });
  await page.setViewportSize({ width: 320, height: 480 });
  await search(page).focus();
  await expect(search(page)).toBeInViewport({ ratio: 1 });
  await measure(page, testInfo, "320-short-viewport-search");
});
