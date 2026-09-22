import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { test, expect } from "@playwright/test";
import { games, gameURL, start, tabTo } from "./games.mjs";

const game = games.find(({ key }) => key === "lant");
const root = fileURLToPath(new URL("../../", import.meta.url));
const helper = fileURLToPath(new URL("./lant_caption_seeds.py", import.meta.url));
const cases = [
  { id: "lt_geografie_239", nouns: /oraș|regiune|salină|chei|revoluționar|răscoală|munți|Turda/ },
  { id: "lt_literatura_240", nouns: /poet|scriitor|revistă|societate|academie|fondator|postum/ },
  { id: "lt_gastronomie_241", nouns: /ciorbă|perișoare|sarmale|orez|carne|umplutură/ },
  { id: "lt_gastronomie_243", nouns: /cuptor|pâine|biscuit|bucățele/, via: ["Pâine", "Biscuit"], hints: false },
  { id: "lt_gastronomie_244", nouns: /frișcă|îndulcitor|tort|pișcot|zahăr/, via: ["Frișcă", "Pișcot"], hints: false },
  { id: "lt_gastronomie_245", nouns: /plăcintă|pască|vanilie|brânză/, via: ["Poale-n brâu", "Pască"], hints: false },
].map((item) => ({
  ...item,
  journey: JSON.parse(execFileSync("python3", [helper, item.id], {
    cwd: root, env: { ...process.env, PYTHONPATH: root }, encoding: "utf8",
  })),
}));

const responseFor = (page, id, action) => page.waitForResponse((response) =>
  response.request().method() === "POST" &&
  new URL(response.url()).pathname === `${gameURL(game, id)}/${action}`);

async function begin(page, item) {
  if (test.info().project.name === "mobile") {
    await page.setViewportSize({ width: 320, height: 900 });
    await page.addInitScript(() => {
      globalThis.document.addEventListener("DOMContentLoaded", () => {
        globalThis.document.documentElement.style.fontSize = "200%";
      });
    });
  }
  await page.route("**/api/wordgames/lant/games?*", async (route) => {
    const url = new URL(route.request().url());
    for (const [name, value] of Object.entries(item.journey.query)) {
      url.searchParams.set(name, String(value));
    }
    await route.continue({ url: url.toString() });
  });
  const state = await start(page, game, { keyboard: true });
  if (test.info().project.name === "mobile") {
    await expect(page.locator("html")).toHaveCSS("font-size", "32px");
  }
  expect(state.start.id).toBe(item.journey.start.id);
  expect(state.target.id).toBe(item.journey.target.id);
  return state;
}

function meaningful(caption, nouns) {
  expect(caption).toMatch(nouns);
  expect(caption).not.toMatch(/^legătură(?: directă)?$/i);
}

async function fits(page) {
  const layout = await page.locator(".lant-choice-grid button, .lant-hint-panel, .breadcrumb-trail, .lant-trail-step, .lant-trail-relation, .lant-trail-step .chip")
    .evaluateAll((elements) => ({
      width: globalThis.document.documentElement.clientWidth,
      scroll: globalThis.document.documentElement.scrollWidth,
      visible: elements.filter((element) => element.getClientRects().length).map((element) => ({
        left: element.getBoundingClientRect().left,
        right: element.getBoundingClientRect().right,
        width: element.clientWidth,
        scroll: element.scrollWidth,
      })),
    }));
  expect(layout.scroll).toBeLessThanOrEqual(layout.width + 1);
  for (const element of layout.visible) {
    expect(element.left).toBeGreaterThanOrEqual(-1);
    expect(element.right).toBeLessThanOrEqual(layout.width + 1);
    expect(element.scroll).toBeLessThanOrEqual(element.width + 1);
  }
}

for (const item of cases) {
  if (item.via) {
    item.journey.routes = item.journey.routes.filter((route) => item.via.includes(route[1].label));
    if (item.journey.routes.length !== 2) throw new Error(`Missing reviewed food routes for ${item.id}`);
  }
  for (const [index, route] of item.journey.routes.entries()) {
    test(`${item.id} route ${index + 1}: meaningful choices survive earned path and reload`, async ({ page, request }) => {
      let state = await begin(page, item);
      const id = state.game_id;
      let mutations = 0;
      page.on("request", (request) => {
        if (request.method() === "POST" && new URL(request.url()).pathname.startsWith(`${gameURL(game, id)}/`)) mutations += 1;
      });
      const firstHops = new Set(item.journey.routes.map((path) => path[1].label));
      const usefulChoices = state.choices.filter((choice) => firstHops.has(choice.label));
      expect(usefulChoices.length).toBeGreaterThanOrEqual(2);
      for (const choice of usefulChoices) {
        meaningful(choice.relation, item.nouns);
        await expect(page.getByRole("button", { name: `Salt la ${choice.label}: ${choice.relation}`, exact: true }))
          .toContainText(choice.relation);
      }
      await fits(page);
      if (index === 0) await page.screenshot({ path: test.info().outputPath("choices.png"), fullPage: true });
      for (const next of route.slice(1)) {
        const response = responseFor(page, id, "move");
        const choice = page.locator(".lant-choice-grid button").filter({
          has: page.locator("strong", { hasText: new RegExp(`^${next.label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}$`) }),
        });
        if (await choice.count()) {
          await tabTo(page, choice);
          await page.keyboard.press("Space");
        } else {
          const input = page.getByRole("textbox", { name: "Următorul concept" });
          await tabTo(page, input);
          await input.fill(next.label);
          await input.press("Enter");
        }
        state = await (await response).json();
        expect(state.ok).toBe(true);
        expect(state.current.id).toBe(next.id);
        meaningful(state.path.at(-1).relation, item.nouns);
        if (state.moves === 1) {
          const saved = await (await request.get(gameURL(game, id))).json();
          expect(saved.path).toEqual(state.path);
          const beforeReload = mutations;
          await page.reload();
          await expect(page.locator(".lant-current")).toContainText(next.label);
          expect(mutations).toBe(beforeReload);
          const options = page.locator(".game-options > summary");
          await tabTo(page, options);
          await page.keyboard.press("Space");
          await expect(page.getByRole("group", { name: "Traseul parcurs" }))
            .toContainText(saved.path.at(-1).relation);
          await fits(page);
          await options.press("Space");
        }
      }
      expect(state.won).toBe(true);
      const saved = await (await request.get(gameURL(game, id))).json();
      expect(saved.path).toEqual(state.path);
      await expect(page.getByRole("button", { name: "Copiază rezultatul" })).toBeVisible();
      const options = page.locator(".game-options > summary");
      await tabTo(page, options);
      await page.keyboard.press("Space");
      const path = page.getByRole("group", { name: "Traseul parcurs" });
      for (const step of saved.path.slice(1)) await expect(path).toContainText(step.relation);
      expect(mutations).toBe(route.length - 1);
      await fits(page);
      await tabTo(page, path);
      await expect(path).toBeFocused();
      await path.scrollIntoViewIfNeeded();
      if (index === 0) await page.screenshot({ path: test.info().outputPath("earned-path.png"), fullPage: true });
      await test.info().attach("earned-captions", {
        body: JSON.stringify({ seed: item.journey.query, path: saved.path }, null, 2), contentType: "application/json",
      });
    });
  }

  if (item.hints !== false) test(`${item.id}: noun-bearing hints persist without taking a hop`, async ({ page, request }) => {
    const initial = await begin(page, item);
    const id = initial.game_id;
    async function ask() {
      const response = responseFor(page, id, "hint");
      const button = page.getByRole("button", { name: /💡 (?:Indiciu|Mai clar)/ });
      await tabTo(page, button);
      await page.keyboard.press("Space");
      return (await response).json();
    }
    const direction = await ask();
    expect(direction.stage).toBe("direction");
    meaningful(direction.relation, item.nouns);
    await expect(page.locator(".lant-hint-panel")).toContainText(direction.relation);
    await page.reload();
    await expect(page.locator(".lant-hint-panel")).toContainText(direction.relation);
    const saved = await (await request.get(gameURL(game, id))).json();
    expect(saved.moves).toBe(0);
    expect(saved.earned_hint).toEqual(direction);
    const alternatives = await ask();
    expect(alternatives.stage).toBe("alternatives");
    for (const choice of alternatives.alternatives_choices) {
      meaningful(choice.relation, item.nouns);
      await expect(page.locator(".lant-hint-panel").getByRole("button", {
        name: `Salt la ${choice.label}: ${choice.relation}`, exact: true,
      })).toBeVisible();
    }
    const exact = await ask();
    expect(exact.stage).toBe("hop");
    meaningful(exact.relation, item.nouns);
    await expect(page.locator(".lant-hint-panel")).toContainText(exact.relation);
    await fits(page);
    await page.screenshot({ path: test.info().outputPath("exact-hint.png"), fullPage: true });
    const move = responseFor(page, id, "move");
    await tabTo(page, page.locator(".hint-fill-button"));
    await page.keyboard.press("Space");
    const moved = await (await move).json();
    expect(moved.moves).toBe(1);
    expect(moved.current.id).toBe(exact.hint.id);
    expect(moved.path.at(-1).relation).toBe(exact.relation);
    await expect(page.locator(".lant-hint-panel")).toHaveCount(0);
    await expect(page.locator(".lant-choice-grid button").first()).toBeFocused();
  });
}
