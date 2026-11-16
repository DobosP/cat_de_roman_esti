import { readFileSync } from "node:fs";
import { expect } from "@playwright/test";
import { nativePlan } from "./native-plan.mjs";

export const games = [
  { key: "alchimie", path: "/alchimie", board: ".alchemy-inventory-grid" },
  { key: "intrusul", path: "/intrusul", board: ".intrusul-grid", derived: true },
  { key: "perechi", path: "/perechi", board: ".perechi-grid", derived: true },
  { key: "conexiuni", path: "/conexiuni", board: ".connections-grid" },
  { key: "contexto", path: "/cald-rece", board: '[aria-label="Concept de ghicit"]' },
  { key: "lant", path: "/lant", board: '[aria-label="Următorul concept"]' },
];
const fixtures = new Map();
export const seededStarts = JSON.parse(readFileSync(new URL("./seeded-starts-rules-v2.json", import.meta.url), "utf8"));
const escapeRegex = (value) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

export function solution(game) {
  // Named semantic journeys and the general seed-38 journey must never share a cache entry.
  const fixtureKey = `${game.key}:${game.packId ?? "seed-38"}${game.daily ? `:daily-${game.daily}` : ""}`;
  if (!fixtures.has(fixtureKey)) {
    const args = [game.key, ...(game.packId ? [game.packId] : []), ...(game.daily ? [`--daily=${game.daily}`] : [])];
    fixtures.set(fixtureKey, nativePlan(args));
  }
  return fixtures.get(fixtureKey);
}

export const activeKey = (game) => `cat_active_game_v1_${game.key}`;
export const gameURL = (game, id) => `/api/wordgames/${game.key}/games/${id}`;

export async function deterministicStarts(page, game) {
  const query = game.packId ? solution(game).query : { seed: "38" };
  // Historical seeded mechanics witnesses use a free round. Daily-specific
  // journeys pass a day and exercise the daily entry against their own clock.
  if (!game.daily) {
    const completeDaily = (key) => {
      const now = new Date();
      const day = [now.getFullYear(), now.getMonth() + 1, now.getDate()]
        .map((value) => String(value).padStart(2, "0")).join("-");
      const storageKey = `cat_daily_v2_${key}`;
      if (!localStorage.getItem(storageKey)) localStorage.setItem(storageKey, JSON.stringify({ [day]: 2 }));
    };
    await page.addInitScript(completeDaily, game.key);
    if (page.url() !== "about:blank") await page.evaluate(completeDaily, game.key);
  }
  await page.route((url) => url.pathname === `/api/wordgames/${game.key}/games`, async (route) => {
    if (route.request().method() !== "POST") return route.continue();
    const url = new URL(route.request().url());
    for (const [name, value] of Object.entries(query)) url.searchParams.set(name, String(value));
    await route.continue({ url: url.toString() });
  });
}

export async function tabTo(page, target) {
  await expect(target).toBeVisible();
  await expect(target).toBeEnabled();
  for (let steps = 0; steps < 80; steps += 1) {
    if (await target.evaluate((element) => element === globalThis.document.activeElement)) return;
    await page.keyboard.press("Tab");
  }
  await expect(target, "essential control must be reachable with Tab").toBeFocused();
}

async function activate(page, target, keyboard) {
  if (!keyboard) return target.click();
  await tabTo(page, target);
  await page.keyboard.press("Space");
}

export async function openAlchemyDisclosure(page, selector, { keyboard = false } = {}) {
  // The approved flat Alchimie collection replaces nested library/journal details.
  // Keep callers focused on the same visible controls and earned content.
  if (selector === ".alchemy-discoveries" || selector === ".alchemy-explore-journal") {
    const toggle = page.locator("button.alchemy-recipes-toggle");
    if (await toggle.textContent() === "Rețete") await activate(page, toggle, keyboard);
    await expect(toggle).toHaveText("Cuvinte");
    await expect(page.locator(selector === ".alchemy-discoveries"
      ? ".alchemy-reaction-history" : selector)).toBeVisible();
    return;
  }
  if (selector === ".alchemy-library-tools") {
    const toggle = page.locator("button.alchemy-recipes-toggle");
    if (await toggle.textContent() === "Cuvinte") await activate(page, toggle, keyboard);
    await expect(page.locator(".alchemy-inventory-search")).toBeVisible();
    await expect(page.locator(".alchemy-inventory-grid")).toBeVisible();
    return;
  }
  const details = page.locator(selector);
  if (await details.getAttribute("open") === null) {
    await activate(page, details.locator(":scope > summary"), keyboard);
  }
  await expect(details).toHaveAttribute("open", "");
}

export async function openGameOptions(page, _game, { keyboard = false } = {}) {
  const dialog = page.getByRole("dialog", { name: /Cum se joacă/ });
  if (!(await dialog.isVisible())) {
    await activate(page, page.getByRole("button", { name: "Cum se joacă", exact: true }), keyboard);
  }
  await expect(dialog).toBeVisible();
}

// ADR-0197 per-route delivery: the Preact shell serves exactly these document
// paths. M3 observes every game through the current Preact bundle; explicit
// CAT_UI=legacy rollback is qualified independently by its owning journey.
export const portedRoutes = Object.freeze(["/", "/intrusul", "/perechi", "/conexiuni", "/alchimie", "/cald-rece", "/lant", "/clasament"]);
export const expectedUi = (url) => (portedRoutes.includes(new URL(url, "http://local.invalid").pathname) ? "preact" : "legacy");

/** Every journey states which bundle the server answered with for the current document. */
export async function expectUi(page, url = page.url()) {
  await expect(page.locator("html")).toHaveAttribute("data-ui", expectedUi(url));
}

export async function start(page, game, { keyboard = false } = {}) {
  if (keyboard) await page.goto("/");
  const response = page.waitForResponse((r) =>
    r.request().method() === "POST" &&
    new URL(r.url()).pathname === `/api/wordgames/${game.key}/games`);
  if (keyboard) {
    const link = page.locator(`.games-grid a[href="${game.path}"]`);
    await tabTo(page, link);
    await page.keyboard.press("Enter");
  } else {
    await page.goto(game.path);
  }
  await expectUi(page, game.path);
  const created = await response;
  expect(created.status()).toBe(200);
  const state = await created.json();
  await expect(page.locator(game.board)).toBeVisible();
  return state;
}

export async function act(page, game, step, { keyboard = false } = {}) {
  const response = page.waitForResponse((r) =>
    r.request().method() === "POST" && new URL(r.url()).pathname.endsWith(`/${step.action}`));
  if (game.key === "contexto" || game.key === "lant") {
    const input = page.getByRole("textbox", {
      name: game.key === "contexto" ? "Concept de ghicit" : "Următorul concept",
    });
    if (keyboard) await tabTo(page, input);
    await input.fill(step.payload.text);
    await input.press("Enter");
  } else {
    if (game.key === "alchimie") {
      for (const slot of await page.getByRole("button", { name: /^Scoate .* din alambic$/ }).all()) {
        await activate(page, slot, keyboard);
      }
      await openAlchemyDisclosure(page, ".alchemy-library-tools", { keyboard });
      await expect(page.locator(".alchemy-inventory-search")).toHaveValue("");
    }
    for (const label of step.labels) {
      await activate(page, page.locator(game.board).getByRole("button", {
        name: new RegExp(`^${escapeRegex(label)}(?:,|$)`),
      }), keyboard);
    }
    if (game.key === "conexiuni") {
      await activate(page, page.getByRole("button", { name: "Verifică", exact: true }), keyboard);
    }
  }
  return response;
}

export async function solve(page, game, steps, options = {}) {
  let result;
  for (const step of steps) {
    const response = await act(page, game, step, options);
    expect(response.status()).toBe(200);
    result = await response.json();
    if (game.key === "conexiuni") {
      await expect(page.locator(`${game.board} button`)).toHaveCount(16 - result.solved_count * 4);
    }
    if (game.key === "perechi" && options.keyboard) {
      if (result.won) {
        const heading = page.getByRole("heading", { name: "Toate se potrivesc!" });
        await expect(heading).toBeFocused();
        // One extra Enter on the focused result must not start a new round.
        let creates = 0;
        const countCreate = (request) => {
          if (request.method() === "POST" &&
            new URL(request.url()).pathname === `/api/wordgames/${game.key}/games`) creates += 1;
        };
        page.on("request", countCreate);
        await page.keyboard.press("Enter");
        await page.waitForTimeout(500);
        page.off("request", countCreate);
        expect(creates).toBe(0);
        await expect(heading).toBeVisible();
      } else {
        const split = result.tiles.findIndex((tile) => tile.id === step.payload.ids[1]) + 1;
        const next = [...result.tiles.slice(split), ...result.tiles.slice(0, split)]
          .find((tile) => !tile.solved);
        await expect(page.locator(game.board).getByRole("button", { name: next.label, exact: true }))
          .toBeFocused();
      }
    }
  }
  expect(result.won).toBe(true);
  await expect(page.getByRole("button", { name: "Copiază rezultatul" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Încă o rundă", exact: true })).toBeEnabled();
  return result;
}
