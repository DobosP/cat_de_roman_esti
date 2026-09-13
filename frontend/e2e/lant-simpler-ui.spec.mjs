import { test, expect } from "@playwright/test";
import { games, deterministicStarts, gameURL, start } from "./games.mjs";

const game = games.find(({ key }) => key === "lant");
const hints = (page) => page.getByRole("button", { name: /💡 (?:Indiciu|Mai clar)/ });
const tapOrClick = (button) => test.info().project.name === "mobile" ? button.tap() : button.click();
const responseFor = (page, id, action) => page.waitForResponse((response) =>
  response.request().method() === "POST" &&
  new URL(response.url()).pathname === `${gameURL(game, id)}/${action}`);

async function requestHint(page, id) {
  const response = responseFor(page, id, "hint");
  await hints(page).click();
  return (await response).json();
}

test.beforeEach(async ({ page }) => {
  await deterministicStarts(page, game);
});

test("current word, target and all local choices fit before the optional controls", async ({ page }) => {
  const initial = await start(page, game);
  await expect(page.locator(".lant-current")).toContainText(initial.current.label);
  await expect(page.locator(".lant-target")).toContainText(initial.target.label);
  const options = page.locator(".game-options");
  await expect(options).not.toHaveAttribute("open", "");
  await expect(page.locator(".breadcrumb-trail")).toBeHidden();
  const choices = page.locator(".lant-choice-grid button");
  await expect(choices).toHaveCount(initial.choices.length);
  const measurements = await choices.evaluateAll((buttons) => ({
    viewportHeight: globalThis.innerHeight,
    firstTop: buttons[0].getBoundingClientRect().top,
    lastBottom: buttons.at(-1).getBoundingClientRect().bottom,
    visibleChoices: buttons.filter((button) => {
      const rect = button.getBoundingClientRect();
      return rect.top >= 0 && rect.bottom <= globalThis.innerHeight;
    }).length,
  }));
  expect(measurements.visibleChoices).toBe(initial.choices.length);
  await test.info().attach("choice-layout", {
    body: JSON.stringify(measurements, null, 2), contentType: "application/json",
  });
  await page.screenshot({ path: test.info().outputPath("lant-compact-play.png"), fullPage: true });
});

test("one local-choice tap makes one hop without typing or confirmation", async ({ page, request }) => {
  const initial = await start(page, game);
  let mutations = 0;
  page.on("request", (request) => {
    if (request.method() === "POST" && new URL(request.url()).pathname.endsWith("/move")) mutations += 1;
  });
  const response = responseFor(page, initial.game_id, "move");
  await tapOrClick(page.locator(".lant-choice-grid button").first());
  const moved = await (await response).json();
  expect(moved.ok).toBe(true);
  expect(moved.moves).toBe(1);
  expect(mutations).toBe(1);
  const server = await (await request.get(gameURL(game, initial.game_id))).json();
  expect(server.current.label).toBe(initial.choices[0].label);
  await expect(page.getByRole("textbox", { name: "Următorul concept" })).toHaveValue("");
});

for (const stage of ["alternatives", "hop"]) {
  test(`an exact ${stage} hint takes one tap and resume never makes the hop`, async ({ page, request }) => {
    const initial = await start(page, game);
    expect((await requestHint(page, initial.game_id)).stage).toBe("direction");
    let earned = await requestHint(page, initial.game_id);
    expect(earned.stage).toBe("alternatives");
    if (stage === "hop") earned = await requestHint(page, initial.game_id);
    expect(earned.stage).toBe(stage);
    let mutations = 0;
    page.on("request", (request) => {
      if (request.method() === "POST" && new URL(request.url()).pathname.startsWith(`${gameURL(game, initial.game_id)}/`)) mutations += 1;
    });
    await page.reload();
    const panel = page.locator(".lant-hint-panel");
    const choice = stage === "alternatives" ? earned.alternatives_choices[0] : earned.hint;
    await expect(panel).toBeVisible();
    await expect(panel).toContainText(choice.label);
    expect(mutations).toBe(0);
    expect((await (await request.get(gameURL(game, initial.game_id))).json()).moves).toBe(0);
    const response = responseFor(page, initial.game_id, "move");
    const button = panel.getByRole("button").first();
    if (test.info().project.name === "mobile") await button.tap();
    else {
      await button.focus();
      await page.keyboard.press("Space");
    }
    const moved = await (await response).json();
    expect(moved.ok).toBe(true);
    expect(moved.current.label).toBe(choice.label);
    expect(moved.moves).toBe(1);
    expect(mutations).toBe(1);
    await expect(panel).toHaveCount(0);
  });
}

async function earnExactHint(page, id) {
  for (const stage of ["direction", "alternatives", "hop"]) {
    expect((await requestHint(page, id)).stage).toBe(stage);
  }
  const choice = page.locator(".lant-hint-panel .hint-fill-button");
  await expect(choice).toBeEnabled();
  return choice;
}

test("a delayed exact-hint hop preserves focus moved deliberately to game options", async ({ page }) => {
  const initial = await start(page, game);
  const choice = await earnExactHint(page, initial.game_id);
  let release;
  let signalRequest;
  const held = new Promise((resolve) => { release = resolve; });
  const requested = new Promise((resolve) => { signalRequest = resolve; });
  await page.route(`**${gameURL(game, initial.game_id)}/move`, async (route) => {
    const response = await route.fetch();
    signalRequest();
    await held;
    await route.fulfill({ response });
  }, { times: 1 });
  await choice.focus();
  await page.keyboard.press("Space");
  await requested;
  await expect(choice).toBeDisabled();
  const options = page.locator(".game-options > summary");
  await options.focus();
  await expect(options).toBeFocused();
  release();
  await expect(page.locator(".lant-hint-panel")).toHaveCount(0);
  await expect(page.getByRole("textbox", { name: "Următorul concept" })).toBeEnabled();
  await expect(options).toBeFocused();
});

test("keyboard focus follows a consumed hint to a usable next word on either pointer type", async ({ page }) => {
  const initial = await start(page, game);
  const choice = await earnExactHint(page, initial.game_id);
  await choice.focus();
  await expect(choice).toBeFocused();
  const response = responseFor(page, initial.game_id, "move");
  await page.keyboard.press("Space");
  expect((await (await response).json()).moves).toBe(1);
  await expect(page.locator(".lant-hint-panel")).toHaveCount(0);
  const nextWord = page.locator(".lant-choice-grid button").first();
  await expect(nextWord).toBeFocused();
  await expect(nextWord).toBeEnabled();
  const nextResponse = responseFor(page, initial.game_id, "move");
  await page.keyboard.press("Space");
  const moved = await (await nextResponse).json();
  expect(moved.ok).toBe(true);
  expect(moved.moves).toBe(2);
});
