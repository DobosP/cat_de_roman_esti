import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { readFileSync } from "node:fs";
import { expect } from "@playwright/test";

export const games = [
  { key: "alchimie", path: "/alchimie", board: ".alchemy-inventory-grid" },
  { key: "intrusul", path: "/intrusul", board: ".intrusul-grid", derived: true },
  { key: "perechi", path: "/perechi", board: ".perechi-grid", derived: true },
  { key: "conexiuni", path: "/conexiuni", board: ".connections-grid" },
  { key: "contexto", path: "/cald-rece", board: '[aria-label="Concept de ghicit"]' },
  { key: "lant", path: "/lant", board: '[aria-label="Următorul concept"]' },
];
const fixtures = new Map();
export const seededStarts = JSON.parse(readFileSync(new URL("./seeded-starts.json", import.meta.url), "utf8"));
const root = fileURLToPath(new URL("../../", import.meta.url));
const script = fileURLToPath(new URL("./solutions.py", import.meta.url));
const escapeRegex = (value) => value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

export function solution(game) {
  if (!fixtures.has(game.key)) {
    fixtures.set(game.key, JSON.parse(execFileSync("python3", [script, game.key], {
      cwd: root, env: { ...process.env, PYTHONPATH: root }, encoding: "utf8",
    })));
  }
  return fixtures.get(game.key);
}

export const activeKey = (game) => `cat_active_game_v1_${game.key}`;
export const gameURL = (game, id) => `/api/wordgames/${game.key}/games/${id}`;

export async function deterministicStarts(page, game) {
  await page.route(`**/api/wordgames/${game.key}/games?*`, async (route) => {
    const url = new URL(route.request().url());
    url.searchParams.set("seed", "38");
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

export async function start(page, game, { keyboard = false } = {}) {
  await page.goto(game.path);
  const response = page.waitForResponse((r) =>
    r.request().method() === "POST" &&
    new URL(r.url()).pathname === `/api/wordgames/${game.key}/games`);
  await activate(page, page.getByRole("button", { name: /^Joacă(?: →)?$/ }), keyboard);
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
      await activate(page, page.getByRole("button", { name: /^Toate / }), keyboard);
    }
    for (const label of step.labels) {
      await activate(page, page.locator(game.board).getByRole("button", {
        name: new RegExp(`^${escapeRegex(label)}(?:,|$)`),
      }), keyboard);
    }
    if (game.key === "alchimie") {
      await activate(page, page.getByRole("button", { name: "Combină cele două concepte selectate" }), keyboard);
    } else if (game.key === "conexiuni") {
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
        await expect(page.getByRole("button", { name: "Copiază rezultatul" })).toBeFocused();
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
  await expect(page.getByRole("button", { name: /^Încă (?:unul|un lanț) →$/ })).toBeEnabled();
  return result;
}
