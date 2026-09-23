import { test, expect } from "@playwright/test";
import { games, gameURL, deterministicStarts, solution, start, tabTo, openAlchemyDisclosure } from "./games.mjs";

const game = games.find(({ key }) => key === "alchimie");
// These focus/empty-pair scenarios require the original football-board topology.
const footballGame = { ...game, packId: "al_sport_083" };
const escapeRegex = (value) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const inventory = (page) => page.locator(game.board);
const ingredient = (page, label) => inventory(page).getByRole("button", {
  name: new RegExp(`^${escapeRegex(label)}(?:,|$)`),
});
const slot = (page, label) => page.getByRole("button", {
  name: `Scoate ${label} din alambic`, exact: true,
});
const slots = (page) => page.getByRole("button", { name: /^Scoate .* din alambic$/ });
const filter = (page, name) => page.getByRole("button", { name: new RegExp(`^${name} `) });
const search = (page) => page.getByRole("searchbox", { name: "Caută în toate conceptele descoperite" });
const responseFor = (page, id) => page.waitForResponse((reply) => reply.request().method() === "POST"
  && new URL(reply.url()).pathname === `${gameURL(game, id)}/combine`);

function combineTraffic(page, id) {
  const posts = [];
  page.on("request", (request) => {
    if (request.method() === "POST" && new URL(request.url()).pathname === `${gameURL(game, id)}/combine`) {
      posts.push(request.postDataJSON());
    }
  });
  return posts;
}

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

test("the initial game puts words above 500px and collapses secondary controls", async ({ page }, testInfo) => {
  const mobile = testInfo.project.name === "mobile";
  await page.setViewportSize({ width: mobile ? 390 : 1280, height: mobile ? 844 : 850 });
  const initial = await start(page, game);
  await expect(page.locator(".alchemy-workspace > .alchemy-bench")).toHaveCount(1);
  await expect(page.locator(".alchemy-workspace > .alchemy-inventory-panel")).toHaveCount(1);
  await expect(inventory(page).getByRole("button")).toHaveCount(initial.inventory.filter((item) =>
    item.useful && !item.depleted).length);
  await expect(page.getByRole("button", { name: "Combină cele două concepte selectate" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Golește", exact: true })).toHaveCount(0);
  await expect(slots(page)).toHaveCount(0);
  await expect(page.locator(".alchemy-quick-results")).toHaveCount(0);
  await expect(search(page)).toBeHidden();
  await expect(page.getByRole("button", { name: /Reia același joc/ })).toBeHidden();
  for (const [selector, name] of [
    [".alchemy-library-tools", "Caută și filtrează"],
    [".alchemy-menu", "Opțiuni de joc"],
  ]) {
    await expect(page.locator(selector)).not.toHaveAttribute("open");
    await expect(page.locator(selector).locator(":scope > summary")).toContainText(name);
  }
  const metrics = await measure(page, testInfo, "initial-direct-craft");
  for (const control of [page.locator(".alchemy-target"), inventory(page).getByRole("button").first()]) {
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
    expect(Math.max(...firstRow.map((box) => box.bottom)), "first ingredient row fits above 500px")
      .toBeLessThanOrEqual(500);
  }
  await testInfo.attach("initial-direct-craft", { body: await page.screenshot(), contentType: "image/png" });
});

for (const keyboard of [false, true]) {
  test(`${keyboard ? "keyboard" : "tap"}: two word activations discover, then one activation continues to the target`, async ({ page }, testInfo) => {
    const initial = await start(page, game);
    const posts = combineTraffic(page, initial.game_id);
    const steps = solution(game).steps;
    const choose = async (label) => {
      if (keyboard) {
        await tabTo(page, ingredient(page, label));
        await page.keyboard.press("Enter");
      } else if (testInfo.project.name === "mobile") await ingredient(page, label).tap();
      else await ingredient(page, label).click();
    };
    await choose(steps[0].labels[0]);
    await expect(slot(page, steps[0].labels[0])).toBeVisible();
    expect(posts).toEqual([]);
    const discoveryResponse = responseFor(page, initial.game_id);
    await choose(steps[0].labels[1]);
    const discovery = await (await discoveryResponse).json();
    expect(discovery.discovered).toHaveLength(1);
    expect(discovery.won).toBe(false);
    const earned = discovery.discovered[0];
    await expect(slots(page)).toHaveCount(1);
    await expect(slot(page, earned.label)).toBeVisible();
    await expect(ingredient(page, earned.label)).toHaveAttribute("aria-pressed", "true");
    await expect(page.locator(".alchemy-discoveries")).not.toHaveAttribute("open");
    await expect(page.locator(".alchemy-reaction-result").first()).toBeHidden();
    await expect(page.locator(".alchemy-feedback")).toContainText(earned.label);
    expect(posts).toEqual([steps[0].payload]);
    const partner = steps[1].labels.find((label) => label !== earned.label);
    expect(partner).toBeDefined();
    const winningResponse = responseFor(page, initial.game_id);
    await choose(partner);
    expect((await (await winningResponse).json()).won).toBe(true);
    await expect(page.getByRole("button", { name: "Copiază rezultatul" })).toBeVisible();
    expect(posts).toHaveLength(2);
    expect(new Set(Object.values(posts[1]))).toEqual(new Set(Object.values(steps[1].payload)));
  });
}

test("keyboard discovery moves focus from a removed ingredient to the carried word", async ({ page }) => {
  await deterministicStarts(page, footballGame);
  const initial = await start(page, footballGame);
  const [first, second] = solution(footballGame).steps[0].labels;
  await tabTo(page, ingredient(page, first));
  await page.keyboard.press("Enter");
  await tabTo(page, ingredient(page, second));
  await expect(ingredient(page, second)).toBeFocused();
  const response = responseFor(page, initial.game_id);
  await page.keyboard.press("Enter");
  const discovered = await (await response).json();
  const earned = discovered.discovered[0];
  expect(discovered.inventory.find((item) => item.label === second).depleted).toBe(true);
  await expect(ingredient(page, second)).toHaveCount(0);
  await expect(slot(page, earned.label)).toBeVisible();
  await expect(ingredient(page, earned.label)).toBeFocused();
  await expect(page.locator(".alchemy-feedback")).toContainText(`${earned.label} rămâne ales.`);
});

test("a delayed discovery preserves focus moved to another control while the combine is pending", async ({ page }) => {
  await deterministicStarts(page, footballGame);
  const initial = await start(page, footballGame);
  const [first, second] = solution(footballGame).steps[0].labels;
  let release;
  let entered;
  const held = new Promise((resolve) => { release = resolve; });
  const requested = new Promise((resolve) => { entered = resolve; });
  await page.route(`**${gameURL(game, initial.game_id)}/combine`, async (route) => {
    const response = await route.fetch();
    entered();
    await held;
    await route.fulfill({ response });
  }, { times: 1 });
  await tabTo(page, ingredient(page, first));
  await page.keyboard.press("Enter");
  await tabTo(page, ingredient(page, second));
  const response = responseFor(page, initial.game_id);
  await page.keyboard.press("Enter");
  await requested;
  const otherControl = page.locator(".alchemy-menu > summary");
  try {
    await tabTo(page, otherControl);
    await expect(otherControl).toBeFocused();
  } finally {
    release();
  }
  const discovered = await (await response).json();
  await expect(ingredient(page, second)).toHaveCount(0);
  await expect(slot(page, discovered.discovered[0].label)).toBeVisible();
  await expect(otherControl).toBeFocused();
});

test("an empty reaction keeps the anchor, blocks the same partner and retries another in one tap", async ({ page, request }) => {
  await deterministicStarts(page, footballGame);
  const initial = await start(page, footballGame);
  const posts = combineTraffic(page, initial.game_id);
  const [failed, changed] = solution(footballGame).hint_setup;
  expect(changed.a).toBe(failed.a);
  const label = (id) => initial.inventory.find((item) => item.id === id).label;
  await ingredient(page, label(failed.a)).click();
  const firstResponse = responseFor(page, initial.game_id);
  await ingredient(page, label(failed.b)).click();
  const first = await (await firstResponse).json();
  expect(first.discovered).toEqual([]);
  await expect(slots(page)).toHaveCount(1);
  await expect(slot(page, label(failed.a))).toBeVisible();
  // Synthetic activation also exercises the local guard if a browser delivers a queued click.
  await ingredient(page, label(failed.b)).dispatchEvent("click");
  await tabTo(page, ingredient(page, label(failed.b)));
  await page.keyboard.press("Enter");
  await settle(page);
  expect(posts).toEqual([failed]);
  expect((await (await request.get(gameURL(game, initial.game_id))).json()).moves).toBe(first.moves);
  const changedResponse = responseFor(page, initial.game_id);
  await ingredient(page, label(changed.b)).click();
  const retried = await (await changedResponse).json();
  expect(retried.discovered).toEqual([]);
  expect(retried.moves).toBe(first.moves + 1);
  expect(posts).toEqual([failed, changed]);
  await expect(slot(page, label(failed.a))).toBeVisible();
});

test("rapid partner taps send one combine while the response is pending", async ({ page }) => {
  await deterministicStarts(page, footballGame);
  const initial = await start(page, footballGame);
  const posts = combineTraffic(page, initial.game_id);
  const [first, second] = solution(footballGame).steps[0].labels;
  const third = initial.inventory.find((item) => ![first, second].includes(item.label));
  let release;
  let entered;
  const held = new Promise((resolve) => { release = resolve; });
  const requested = new Promise((resolve) => { entered = resolve; });
  await page.route(`**${gameURL(game, initial.game_id)}/combine`, async (route) => {
    const response = await route.fetch();
    entered();
    await held;
    await route.fulfill({ response });
  }, { times: 1 });
  await ingredient(page, first).click();
  const response = responseFor(page, initial.game_id);
  await ingredient(page, second).click();
  await requested;
  try {
    await expect(ingredient(page, third.label)).toBeDisabled();
    await ingredient(page, second).dispatchEvent("click");
    await ingredient(page, third.label).dispatchEvent("click");
    await page.keyboard.press("Enter");
    expect(posts).toEqual([solution(footballGame).steps[0].payload]);
  } finally {
    release();
  }
  expect((await response).status()).toBe(200);
  await expect(slots(page)).toHaveCount(1);
  expect(posts).toHaveLength(1);
});

test("dragging one word onto another combines without separate selection or confirmation", async ({ page }) => {
  const initial = await start(page, game);
  const posts = combineTraffic(page, initial.game_id);
  const [first, second] = solution(game).steps[0].labels;
  await expect(ingredient(page, first)).toHaveAttribute("draggable", "true");
  const response = responseFor(page, initial.game_id);
  await ingredient(page, first).dragTo(ingredient(page, second));
  const discovered = await (await response).json();
  expect(discovered.discovered).toHaveLength(1);
  expect(posts).toEqual([solution(game).steps[0].payload]);
  await expect(slot(page, discovered.discovered[0].label)).toBeVisible();
});

test("the anchor cancels by tapping it or Escape and removal preserves keyboard focus", async ({ page }) => {
  const initial = await start(page, game);
  const posts = combineTraffic(page, initial.game_id);
  const first = initial.inventory.find((item) => item.useful && !item.depleted);
  await ingredient(page, first.label).click();
  await ingredient(page, first.label).click();
  await expect(slots(page)).toHaveCount(0);
  await ingredient(page, first.label).click();
  await page.keyboard.press("Escape");
  await expect(slots(page)).toHaveCount(0);
  await ingredient(page, first.label).click();
  await slot(page, first.label).focus();
  await page.keyboard.press("Enter");
  await expect(ingredient(page, first.label)).toBeFocused();
  await expect(slots(page)).toHaveCount(0);
  await ingredient(page, first.label).click();
  await openAlchemyDisclosure(page, ".alchemy-library-tools");
  await search(page).fill("zzzz-hidden-ingredient");
  await slot(page, first.label).focus();
  await page.keyboard.press("Enter");
  await expect(page.locator(".alchemy-inventory-panel")).toBeFocused();
  await expect(slots(page)).toHaveCount(0);
  expect(posts).toEqual([]);
});

for (const view of ["Utile", "Toate"]) {
  test(`a discovery preserves the ${view} view and can be reused from the collapsed journal`, async ({ page }) => {
    const initial = await start(page, game);
    const posts = combineTraffic(page, initial.game_id);
    await openAlchemyDisclosure(page, ".alchemy-library-tools");
    await filter(page, view).click();
    const response = responseFor(page, initial.game_id);
    for (const label of solution(game).steps[0].labels) await ingredient(page, label).click();
    const state = await (await response).json();
    await expect(filter(page, view)).toHaveAttribute("aria-pressed", "true");
    await expect(filter(page, "Recente")).toHaveAttribute("aria-pressed", "false");
    const earned = state.discovered[0];
    await expect(slot(page, earned.label)).toBeVisible();
    await slot(page, earned.label).click();
    await expect(page.locator(".alchemy-discoveries")).not.toHaveAttribute("open");
    await expect(page.locator(".alchemy-discoveries > summary")).toContainText("Descoperiri");
    await openAlchemyDisclosure(page, ".alchemy-discoveries");
    const result = page.locator(".alchemy-reaction-result").filter({
      hasText: new RegExp(`${escapeRegex(earned.label)}$`),
    }).first();
    await result.click();
    await expect(result).toHaveAttribute("aria-pressed", "true");
    await expect(slot(page, earned.label)).toBeVisible();
    expect(posts).toHaveLength(1);
    await result.click();
    await expect(slots(page)).toHaveCount(0);
    const partner = solution(game).steps[1].labels.find((label) => label !== earned.label);
    await ingredient(page, partner).click();
    const next = responseFor(page, initial.game_id);
    await result.click();
    expect((await (await next).json()).won).toBe(true);
    expect(posts).toHaveLength(2);
  });
}

test("optional search and filters provide a direct way back from an empty result", async ({ page }) => {
  const initial = await start(page, game);
  const first = initial.inventory.find((item) => item.useful && !item.depleted);
  await openAlchemyDisclosure(page, ".alchemy-library-tools");
  await search(page).fill(first.label.normalize("NFD").replace(/\p{M}/gu, "").toLocaleLowerCase("ro-RO"));
  await expect(ingredient(page, first.label)).toBeVisible();
  await filter(page, "Toate").click();
  await expect(search(page)).toHaveValue("");
  await expect(inventory(page).getByRole("button")).toHaveCount(initial.inventory.length);
  await search(page).fill("zzzz-fără-rezultat-v92-zzzz");
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
  const first = initial.inventory.find((item) => item.useful && !item.depleted);
  await ingredient(page, first.label).click();
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
  await openAlchemyDisclosure(page, ".alchemy-library-tools");
  await search(page).focus();
  await expect(search(page)).toBeInViewport({ ratio: 1 });
  await measure(page, testInfo, "320-short-viewport-search");
});
