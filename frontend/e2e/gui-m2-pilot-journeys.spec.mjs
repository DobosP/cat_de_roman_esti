// Stable M2 inventory identities, extended for M3: every game document now
// uses Preact. Historical test titles stay fixed; assertions qualify the new
// current-route behavior and add both lazy Alchimie modes without new case keys.
// The motion-on project runs this file with real motion so the kit Presence
// retention/exit variant is exercised instead of finishing at duration 0.
import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";
import { games, activeKey, gameURL, deterministicStarts, expectUi, solution, start, solve, act } from "./games.mjs";

const ported = games.filter(({ key }) => ["intrusul", "perechi", "conexiuni"].includes(key));
const legacy = ["/alchimie", "/cald-rece", "/lant", "/clasament"];
const motionOn = () => test.info().project.name === "motion-on";

function documentRequests(page) {
  const requests = [];
  page.on("request", (request) => {
    if (request.isNavigationRequest() && request.frame() === page.mainFrame()) requests.push(request.url());
  });
  return requests;
}

async function heldDailyResumeDuringExit(page, request) {
  const game = games.find(({ key }) => key === "lant");
  await page.goto("/");
  const daily = await page.evaluate(() => {
    const date = new Date();
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
  });
  const created = await request.post(`/api/wordgames/lant/games?daily=${daily}&difficulty=usor`);
  expect(created.status()).toBe(200);
  const state = await created.json();
  expect(state.daily).toBe(daily);
  await page.evaluate(([key, id]) => localStorage.setItem(key, id), [activeKey(game), state.game_id]);
  const beforeScores = await page.evaluate(() => localStorage.getItem("cat_wordgame_scores_v1"));
  const posts = [];
  page.on("request", (item) => { if (item.method() === "POST") posts.push(item.url()); });
  let entered, release;
  const requested = new Promise((resolve) => { entered = resolve; });
  const held = new Promise((resolve) => { release = resolve; });
  await page.route(`**${gameURL(game, state.game_id)}`, async (route) => {
    const response = await route.fetch();
    entered(); await held; await route.fulfill({ response });
  }, { times: 1 });
  await page.getByRole("button", { name: "Deschide Lanțul Cuvintelor — neterminat azi", exact: true }).click();
  await requested;
  const exit = await page.evaluate(async () => {
    const changed = new Promise((resolve) => globalThis.addEventListener("popstate", resolve, { once: true }));
    globalThis.history.back(); await changed;
    await new Promise(requestAnimationFrame);
    const frame = document.querySelector('.app-content > .roedu-presence[data-state="exiting"]');
    const animations = document.getAnimations().filter((item) => item.effect?.target === frame);
    // Keep this real outer exit alive while its actual GET reply arrives.
    animations.forEach((item) => item.pause());
    globalThis.__m3HeldExit = animations;
    return { exiting: Boolean(frame), inert: Boolean(frame?.querySelector(".screen")?.inert), animations: animations.length };
  });
  try {
    if (motionOn()) { expect(exit.exiting).toBe(true); expect(exit.inert).toBe(true); expect(exit.animations).toBeGreaterThan(0); }
    const reply = page.waitForResponse((item) => item.request().method() === "GET" && new URL(item.url()).pathname === gameURL(game, state.game_id));
    release(); await (await reply).finished();
    await page.evaluate(async () => { await new Promise(requestAnimationFrame); await new Promise(requestAnimationFrame); });
    await expect(page).toHaveURL(/\/$/);
    if (motionOn()) await expect(page.locator('.app-content > .roedu-presence[data-state="exiting"] .screen')).toHaveCount(1);
    await expect(page.getByText("Ai continuat jocul liber început. Provocarea zilei te așteaptă după ce îl termini.", { exact: true })).toHaveCount(0);
    expect(await page.evaluate((key) => localStorage.getItem(key), activeKey(game))).toBe(state.game_id);
    expect(await page.evaluate(() => localStorage.getItem("cat_wordgame_scores_v1"))).toBe(beforeScores);
    expect(posts).toEqual([]);
  } finally {
    release();
    await page.evaluate(() => { globalThis.__m3HeldExit?.forEach((item) => item.play()); delete globalThis.__m3HeldExit; });
  }
  await expect(page.getByRole("heading", { name: "Cât de român ești?", exact: true })).toBeVisible();
}

async function heldMoveAcrossReentry(page, request) {
  const game = games.find(({ key }) => key === "lant");
  await page.goto("/");
  await page.evaluate((key) => localStorage.removeItem(key), activeKey(game));
  await deterministicStarts(page, game);
  const navigations = documentRequests(page);
  await page.getByRole("button", { name: /^Joacă Lanțul Cuvintelor —/ }).click();
  const creation = page.waitForResponse((item) => item.request().method() === "POST" && new URL(item.url()).pathname === "/api/wordgames/lant/games");
  await page.getByRole("button", { name: /^Joacă(?: →)?$/ }).click();
  const initial = await (await creation).json();
  await expect(page.locator(game.board)).toBeEnabled();
  const step = solution(game).steps[0];
  let entered, release;
  const requested = new Promise((resolve) => { entered = resolve; });
  const held = new Promise((resolve) => { release = resolve; });
  const counts = { moves: 0, reads: 0 };
  page.on("request", (item) => {
    const path = new URL(item.url()).pathname;
    if (item.method() === "POST" && path === `${gameURL(game, initial.game_id)}/${step.action}`) counts.moves += 1;
    if (item.method() === "GET" && path === gameURL(game, initial.game_id)) counts.reads += 1;
  });
  await page.route(`**${gameURL(game, initial.game_id)}/${step.action}`, async (route) => {
    const response = await route.fetch();
    expect((await response.json()).won).toBe(false);
    entered(); await held; await route.fulfill({ response });
  }, { times: 1 });
  const performed = act(page, game, step);
  await requested;
  const authoritative = await (await request.get(gameURL(game, initial.game_id))).json();
  expect(authoritative.moves).toBeGreaterThan(initial.moves);
  // A failed fresh read must expose normal resume retry without losing the id.
  await page.route(`**${gameURL(game, initial.game_id)}`, (route) => route.fulfill({
    status: 503, contentType: "application/json", body: JSON.stringify({ detail: "Temporar indisponibil." }),
  }), { times: 1 });
  const returned = await page.evaluate(async () => {
    const original = document.querySelector(".app-content > .roedu-presence > .screen");
    const traverse = async (direction) => {
      const changed = new Promise((resolve) => globalThis.addEventListener("popstate", resolve, { once: true }));
      globalThis.history[direction](); await changed; await new Promise(requestAnimationFrame);
    };
    await traverse("back");
    const frame = original?.parentElement;
    const exiting = frame?.dataset.state === "exiting";
    const animations = document.getAnimations().filter((item) => item.effect?.target === frame);
    animations.forEach((item) => item.pause());
    try {
      await traverse("forward");
      return { exiting, same: original?.isConnected && original === document.querySelector(".app-content > .roedu-presence > .screen"), inert: original?.inert };
    } finally { animations.forEach((item) => item.play()); }
  });
  try {
    if (motionOn()) { expect(returned.exiting).toBe(true); expect(returned.same).toBe(true); expect(returned.inert).toBe(false); }
    await expect.poll(() => counts.reads).toBe(1);
    release(); await performed;
    await expect(page).toHaveURL(/\/lant$/);
    await expect(page.getByRole("alert")).toContainText("Nu am putut relua jocul salvat. Nu l-am șters.");
    expect(await page.evaluate((key) => localStorage.getItem(key), activeKey(game))).toBe(initial.game_id);
    const read = page.waitForResponse((item) => item.request().method() === "GET" && new URL(item.url()).pathname === gameURL(game, initial.game_id));
    await page.getByRole("button", { name: "Reîncearcă reluarea", exact: true }).click();
    expect(await (await read).json()).toEqual(authoritative);
    await expect(page.locator(".lant-current .lant-route-word")).toHaveText(authoritative.current.label);
    await expect(page.locator(game.board)).toBeEnabled();
    expect(counts).toEqual({ moves: 1, reads: 2 });
    expect(navigations).toEqual([]);
    // A subsequent real move proves the recovered frame can act again.
    const next = solution(game).steps[1];
    expect(next).toBeDefined();
    expect((await act(page, game, next)).status()).toBe(200);
  } finally { release(); }
}

async function heldCreateAcrossHistory(page, context, request, game) {
  const title = { intrusul: "Intrusul", perechi: "Perechi", conexiuni: "Conexiuni" }[game.key];
  const createPath = `/api/wordgames/${game.key}/games`;
  const documents = documentRequests(page);
  await page.evaluate((key) => localStorage.removeItem(key), activeKey(game));
  const scoresBefore = await page.evaluate(() => localStorage.getItem("cat_wordgame_scores_v1"));
  let releaseOld, releaseFresh, enteredOld, enteredFresh, oldRound, other;
  const oldHeld = new Promise((resolve) => { releaseOld = resolve; });
  const freshHeld = new Promise((resolve) => { releaseFresh = resolve; });
  const oldRequested = new Promise((resolve) => { enteredOld = resolve; });
  const freshRequested = new Promise((resolve) => { enteredFresh = resolve; });
  await page.route(`**${createPath}?*`, async (route) => {
    const url = new URL(route.request().url());
    url.searchParams.set("seed", "38");
    const response = await route.fetch({ url: url.toString() });
    expect(response.status()).toBe(200);
    oldRound = await response.json();
    enteredOld(); await oldHeld; await route.fulfill({ response });
  }, { times: 1 });
  try {
    await page.getByRole("button", { name: new RegExp(`^Joacă ${title} —`) }).click();
    const oldDelivered = page.waitForResponse((item) => item.request().method() === "POST"
      && new URL(item.url()).pathname === createPath);
    await page.getByRole("button", { name: /^Joacă(?: →)?$/ }).click();
    await oldRequested;
    const newerResponse = await request.post(`${createPath}?seed=38&difficulty=usor`);
    expect(newerResponse.status()).toBe(200);
    const newer = await newerResponse.json();
    expect(newer.game_id).not.toBe(oldRound.game_id);
    const newerPath = gameURL(game, newer.game_id);
    let freshReads = 0;
    page.on("request", (item) => {
      if (item.method() === "GET" && new URL(item.url()).pathname === newerPath) freshReads += 1;
    });
    await page.route(`**${newerPath}`, async (route) => {
      expect(route.request().method()).toBe("GET");
      const response = await route.fetch();
      expect(response.status()).toBe(200);
      enteredFresh(); await freshHeld; await route.fulfill({ response });
    }, { times: 1 });
    other = await context.newPage();
    await other.goto("/");
    await other.evaluate(([key, id]) => localStorage.setItem(key, id), [activeKey(game), newer.game_id]);
    const newerDelivered = page.waitForResponse((item) => item.request().method() === "GET"
      && new URL(item.url()).pathname === newerPath);
    const returned = await page.evaluate(async () => {
      const original = document.querySelector(".app-content > .roedu-presence > .screen");
      const traverse = async (direction) => {
        const changed = new Promise((resolve) => globalThis.addEventListener("popstate", resolve, { once: true }));
        globalThis.history[direction](); await changed; await new Promise(requestAnimationFrame);
      };
      await traverse("back");
      const frame = original?.parentElement;
      const exiting = frame?.dataset.state === "exiting";
      const animations = document.getAnimations().filter((item) => item.effect?.target === frame);
      animations.forEach((item) => item.pause());
      try {
        await traverse("forward");
        return { exiting, same: original?.isConnected
          && original === document.querySelector(".app-content > .roedu-presence > .screen"), inert: original?.inert };
      } finally { animations.forEach((item) => item.play()); }
    });
    if (motionOn()) {
      expect(returned.exiting).toBe(true); expect(returned.same).toBe(true); expect(returned.inert).toBe(false);
    }
    await freshRequested;
    await expect(page.locator(".game-intro")).toHaveAttribute("aria-busy", "true");
    expect(await page.evaluate((key) => localStorage.getItem(key), activeKey(game))).toBe(newer.game_id);
    releaseOld();
    expect((await oldDelivered).status()).toBe(200);
    expect(await (await oldDelivered).finished()).toBeNull();
    await page.evaluate(() => new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    // The old create resolves while the frame is present again. It must neither
    // adopt its obsolete id nor unlock the fresh authoritative resume attempt.
    expect(await page.evaluate((key) => localStorage.getItem(key), activeKey(game))).toBe(newer.game_id);
    await expect(page.locator(".game-intro")).toHaveAttribute("aria-busy", "true");
    expect(await page.evaluate(() => localStorage.getItem("cat_wordgame_scores_v1"))).toBe(scoresBefore);
    releaseFresh();
    expect((await (await newerDelivered).json()).game_id).toBe(newer.game_id);
    await expect(page.locator(game.board)).toBeVisible();
    expect(await page.evaluate((key) => localStorage.getItem(key), activeKey(game))).toBe(newer.game_id);
    expect(freshReads).toBe(1);
    expect(documents).toEqual([]);
  } finally { releaseOld(); releaseFresh(); if (other) await other.close(); }
}

test("home deep link is the Preact shell and an unported card is a document navigation to legacy", async ({ page }) => {
  const navigations = documentRequests(page);
  await page.goto("/");
  await expectUi(page, "/");
  await expect(page.getByRole("heading", { name: "Cât de român ești?", exact: true })).toBeVisible();
  await expect(page.locator(".games-grid .game-card")).toHaveCount(6);
  await expect(page.locator(".roedu-root")).toHaveCount(1);
  expect(navigations).toHaveLength(1);
  const arrived = page.waitForURL(/\/cald-rece$/);
  await page.getByRole("button", { name: /^Joacă Cald sau Rece —/ }).click();
  await arrived;
  await expectUi(page, "/cald-rece");
  await expect(page.locator(".game-intro")).toBeVisible();
  expect(navigations).toHaveLength(1);
});

for (const game of ported) {
  test(`${game.key} deep link is served by the Preact shell and plays a seeded round`, async ({ page }) => {
    const manifest = JSON.parse(readFileSync(new URL("../dist/.vite/manifest.json", import.meta.url)));
    const home = manifest["src/screens/Home.tsx"];
    expect(home?.isDynamicEntry).toBe(true);
    const fetched = [];
    page.on("request", (item) => fetched.push(new URL(item.url()).pathname));
    await deterministicStarts(page, game);
    const state = await start(page, game);
    expect(state.game_id.length).toBeGreaterThan(0);
    await solve(page, game, solution(game).steps);
    await expectUi(page, game.path);
    await expect.poll(() => page.evaluate((key) => localStorage.getItem(key), activeKey(game))).toBeNull();
    expect(fetched).not.toContain("/" + home.file);
  });

  test(`${game.key} exit returns to Home client-side without a new document`, async ({ page, context, request }) => {
    const manifest = JSON.parse(readFileSync(new URL("../dist/.vite/manifest.json", import.meta.url)));
    const home = manifest["src/screens/Home.tsx"];
    const fetched = [];
    page.on("request", (item) => fetched.push(new URL(item.url()).pathname));
    await deterministicStarts(page, game);
    const navigations = documentRequests(page);
    await start(page, game);
    expect(navigations).toHaveLength(1);
    expect(fetched).not.toContain("/" + home.file);
    await page.getByRole("button", { name: "Ieși la lista de jocuri", exact: true }).click();
    await expect(page).toHaveURL(/\/$/);
    await expect(page.getByRole("heading", { name: "Cât de român ești?", exact: true })).toBeVisible();
    await expectUi(page, "/");
    expect(navigations).toHaveLength(1);
    await expect(page.locator(".app-content .roedu-presence[data-state=\"exiting\"]")).toHaveCount(0);
    expect(fetched).toContain("/" + home.file);
    await heldCreateAcrossHistory(page, context, request, game);
  });
}

test("every unported route is the frozen legacy bundle", async ({ page }) => {
  for (const route of legacy) {
    await page.goto(route);
    await expectUi(page, route);
    await expect(page.locator(".screen").first()).toBeVisible();
  }
  const manifest = JSON.parse(readFileSync(new URL("../dist/.vite/manifest.json", import.meta.url)));
  const challenge = manifest["src/screens/AlchimieChallenge.tsx"], explore = manifest["src/screens/AlchimieExplore.tsx"];
  expect(challenge?.isDynamicEntry).toBe(true); expect(explore?.isDynamicEntry).toBe(true);
  const fetched = [], navigations = documentRequests(page);
  page.on("request", (request) => fetched.push(new URL(request.url()).pathname));
  await page.goto("/alchimie?mode=explore");
  await expect(page.getByRole("heading", { name: "O lume de descoperit.", exact: true })).toBeVisible();
  expect(fetched).toContain("/" + explore.file); expect(fetched).not.toContain("/" + challenge.file);
  await page.getByRole("link", { name: "Provocări", exact: true }).click();
  await expect(page).toHaveURL(/\/alchimie\?mode=challenges$/);
  await expect(page.locator(".game-intro")).toBeVisible();
  expect(fetched).toContain("/" + challenge.file); expect(navigations).toHaveLength(1);
  await page.getByRole("link", { name: "Explorează", exact: true }).click();
  await expect(page.getByRole("heading", { name: "O lume de descoperit.", exact: true })).toBeVisible();
  expect(fetched.filter((file) => file === "/" + explore.file)).toHaveLength(1);
  expect(navigations).toHaveLength(1);
  await page.goto("/not-a-route");
  await expect(page).toHaveURL(/\/$/); await expectUi(page, "/");
  await page.goto("/lant/?challenge=daily");
  await expect(page).toHaveURL(/\/lant\?challenge=daily$/);
  await expectUi(page, "/lant");
  await expect(page.getByRole("button", { name: "Joacă provocarea zilei", exact: true })).toBeEnabled();
});

test("Home circuit opens a ported daily client-side and an unported daily as a legacy document", async ({ page, request }) => {
  const navigations = documentRequests(page);
  await page.goto("/");
  await page.getByRole("button", { name: "Deschide Intrusul — neterminat azi", exact: true }).click();
  await expect(page).toHaveURL(/\/intrusul\?challenge=daily$/);
  await expectUi(page, "/intrusul");
  await expect(page.getByRole("button", { name: "Joacă provocarea zilei", exact: true })).toBeFocused();
  expect(navigations).toHaveLength(1);
  await page.goBack();
  await expect(page).toHaveURL(/\/$/);
  const arrived = page.waitForURL(/\/lant\?challenge=daily$/);
  await page.getByRole("button", { name: "Deschide Lanțul Cuvintelor — neterminat azi", exact: true }).click();
  await arrived;
  await expectUi(page, "/lant");
  await expect(page.getByRole("button", { name: "Joacă provocarea zilei", exact: true })).toBeEnabled();
  expect(navigations).toHaveLength(1);
  await heldDailyResumeDuringExit(page, request);
});

test("leaving Intrusul keeps the retained screen inert while a winning reply is held", async ({ page, request }) => {
  const game = games.find(({ key }) => key === "intrusul");
  await deterministicStarts(page, game);
  const initial = await start(page, game);
  const step = solution(game).steps[0];
  let entered, release;
  const requested = new Promise((resolve) => { entered = resolve; });
  const held = new Promise((resolve) => { release = resolve; });
  await page.route(`**${gameURL(game, initial.game_id)}/${step.action}`, async (route) => {
    const response = await route.fetch();
    entered();
    await held;
    await route.fulfill({ response });
  }, { times: 1 });
  const counts = { reads: 0 };
  page.on("request", (item) => {
    if (item.method() === "GET" && new URL(item.url()).pathname === gameURL(game, initial.game_id)) counts.reads += 1;
  });
  const performed = act(page, game, step);
  await requested;
  // Leave inside one evaluation so the retained frame is observed within the
  // Presence exit (180 ms with real motion), like the original Presence fixture.
  const snapshot = await page.evaluate(async ([board]) => {
    globalThis.document.querySelector('button[aria-label="Ieși la lista de jocuri"]').click();
    await new Promise((resolve) => globalThis.requestAnimationFrame(resolve));
    const exiting = globalThis.document.querySelector('.app-content .roedu-presence[data-state="exiting"]');
    const buttons = exiting ? [...exiting.querySelectorAll(`${board} button`)] : [];
    return { exiting: Boolean(exiting), buttons: buttons.length, disabled: buttons.every((button) => button.disabled) };
  }, [game.board]);
  if (motionOn()) {
    // Real motion: the kit Presence retains the exiting screen for its animation;
    // `useIsPresent()` is false there, so every retained control is disabled.
    expect(snapshot.exiting).toBe(true);
    expect(snapshot.buttons).toBeGreaterThan(0);
    expect(snapshot.disabled).toBe(true);
  }
  release();
  await performed;
  await expect(page.locator(game.board)).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "Cât de român ești?", exact: true })).toBeVisible();
  await expect(page.locator(".app-content .roedu-presence[data-state=\"exiting\"]")).toHaveCount(0);
  expect(await page.evaluate((key) => localStorage.getItem(key), activeKey(game))).toBe(initial.game_id);
  expect(await page.evaluate(() => JSON.parse(localStorage.getItem("cat_wordgame_scores_v1") || "{}").intrusul?.played ?? 0)).toBe(0);
  expect(counts.reads).toBe(0);
  expect((await (await request.get(gameURL(game, initial.game_id))).json()).won).toBe(true);
  await heldMoveAcrossReentry(page, request);
});

test("Conexiuni solved tiles leave through the Presence scale variant and the board keeps four columns", async ({ page }) => {
  const game = games.find(({ key }) => key === "conexiuni");
  await deterministicStarts(page, game);
  const initial = await start(page, game);
  const grid = page.locator(game.board);
  expect(await grid.evaluate((element) => getComputedStyle(element).gridTemplateColumns.split(/\s+/).filter(Boolean).length)).toBe(4);
  await expect(grid.locator(":scope > .roedu-presence > .connection-tile")).toHaveCount(16);
  const step = solution(game).steps[0];
  const response = page.waitForResponse((item) => item.request().method() === "POST" && new URL(item.url()).pathname === `${gameURL(game, initial.game_id)}/guess`);
  for (const label of step.labels) await grid.getByRole("button", { name: label, exact: true }).click();
  await page.getByRole("button", { name: "Verifică", exact: true }).click();
  const observed = page.waitForFunction(() => globalThis.document.getAnimations().some((animation) => {
    const target = animation.effect?.target;
    return target instanceof globalThis.Element && target.matches(".connections-grid > .roedu-presence[data-state=\"exiting\"]")
      && JSON.stringify(animation.effect.getKeyframes()).includes("scale(0.4)");
  }), undefined, { timeout: 4000 }).then(() => true, () => false);
  expect((await (await response).json()).correct).toBe(true);
  if (motionOn()) expect(await observed, "the exit keyframes must be Presence-owned scale 1 -> 0.4").toBe(true);
  await expect(grid.locator(":scope > .roedu-presence > .connection-tile")).toHaveCount(12);
  await expect(page.locator(".connections-grid > .roedu-presence[data-state=\"exiting\"]")).toHaveCount(0);
  expect(await grid.evaluate((element) => getComputedStyle(element).gridTemplateColumns.split(/\s+/).filter(Boolean).length)).toBe(4);
});
