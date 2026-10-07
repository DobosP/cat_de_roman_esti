// Authored final M0 replacements, NOT RUN. History is explicit fictional local
// presentation data. Static-closure assertions compare genuine build artifacts
// with served bytes; lazy startup requests are permitted, not mistaken for imports.
import { test, expect } from "@playwright/test";
import { createHash } from "node:crypto";
import { existsSync, lstatSync, readFileSync, realpathSync } from "node:fs";
import { resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";
import { tabTo } from "./games.mjs";
import { collectInitialBundleFiles } from "../scripts/check-bundle-budget.mjs";

const SCORE_KEY = "cat_wordgame_scores_v1";
const DAY = "2026-10-08";
const NOW = "2026-10-08T12:00:00.000Z";
const KEYS = ["alchimie", "intrusul", "perechi", "conexiuni", "contexto", "lant"];
const TITLES = ["Alchimie", "Intrusul", "Perechi", "Conexiuni", "Cald sau Rece", "Lanțul Cuvintelor"];
const root = fileURLToPath(new URL("../../", import.meta.url));
const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");

function historyFixture() {
  const history = {};
  for (const [index, score] of [900, 0, 400].entries()) {
    const entry = { score, detail: "Rezultat local de paritate", at: Date.parse(NOW), daily: DAY };
    history[KEYS[index]] = { best: score > 0 ? entry : null, played: 1, recent: [entry],
      completedNonDaily: false, nonDailyCompletions: 0, nonDailyWon: false };
  }
  return history;
}

async function openHome(page, history = historyFixture()) {
  await page.clock.setFixedTime(new Date(NOW));
  await page.route("**/api/me", (route) => route.fulfill({
    json: { accounts_enabled: false, authenticated: false, user: null },
  }));
  await page.addInitScript(({ key, history }) => {
    if (localStorage.getItem(key) === null) localStorage.setItem(key, JSON.stringify(history));
  }, { key: SCORE_KEY, history });
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Circuitul de azi", exact: true })).toBeVisible();
  return history;
}

test("Home presents exactly six local daily rows and completed rows remain read-only", async ({ page }) => {
  const posts = [];
  page.on("request", (request) => {
    if (request.method() === "POST") posts.push(request.url());
  });
  const history = await openHome(page);
  const circuit = page.getByRole("region", { name: "Circuitul de azi", exact: true });
  await expect(circuit.getByText("Doar pe acest dispozitiv.", { exact: true })).toBeVisible();
  const status = circuit.getByRole("status", { name: "3 din 6 jocuri terminate azi, 1300 din 6000 de puncte", exact: true });
  await expect(status).toHaveAttribute("aria-live", "polite");
  await expect(status).toContainText("3/6");
  await expect(status).toContainText("1300/6000 pct");
  const list = circuit.getByRole("list", { name: "Progresul jocurilor de azi", exact: true });
  const rows = list.getByRole("listitem");
  await expect(rows).toHaveCount(6);
  await expect(rows.locator(".daily-circuit-game-name")).toHaveText(TITLES);
  for (const [index, score] of [900, 0, 400].entries()) {
    const row = rows.nth(index);
    await expect(row).toHaveAccessibleName(`${TITLES[index]}: terminat azi, ${score} puncte`);
    await expect(row.getByRole("button")).toHaveCount(0);
    await expect(row).toContainText(`${score} ✓`);
    await row.click();
    await expect(page).toHaveURL(/\/$/);
    await expect(page.locator(".games-grid .game-card").nth(index))
      .toHaveAccessibleName(`Joacă ${TITLES[index]} — terminat azi`);
    await expect(page.locator(".games-grid .game-card").nth(index)).toContainText("Azi ✓");
  }
  for (let index = 3; index < 6; index += 1) {
    const action = rows.nth(index).getByRole("button", { name: `Deschide ${TITLES[index]} — neterminat azi`, exact: true });
    await expect(action).toBeEnabled();
    await expect(action).toContainText("Joacă →");
  }
  expect(posts).toEqual([]);
  expect(await page.evaluate((key) => localStorage.getItem(key), SCORE_KEY)).toBe(JSON.stringify(history));
});

for (const [width, columns] of [[320, 2], [699, 2], [700, 3], [979, 3], [980, 6], [1280, 6]]) {
  test(`daily circuit has ${columns} complete columns at ${width}px with visible keyboard focus and no overflow`, async ({ page }) => {
    await page.setViewportSize({ width, height: 1000 });
    await openHome(page);
    const list = page.getByRole("list", { name: "Progresul jocurilor de azi", exact: true });
    await expect(list.getByRole("listitem")).toHaveCount(6);
    expect(await list.evaluate((element) => getComputedStyle(element).gridTemplateColumns.split(/\s+/).filter(Boolean).length))
      .toBe(columns);
    const dimensions = await list.getByRole("listitem").evaluateAll((rows) => rows.map((row) => ({
      left: row.getBoundingClientRect().left, right: row.getBoundingClientRect().right,
      width: row.clientWidth, scroll: row.scrollWidth,
    })));
    for (const bounds of dimensions) {
      expect(bounds.left).toBeGreaterThanOrEqual(-1);
      expect(bounds.right).toBeLessThanOrEqual(width + 1);
      expect(bounds.scroll).toBeLessThanOrEqual(bounds.width + 1);
    }
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    const action = list.getByRole("button", { name: "Deschide Conexiuni — neterminat azi", exact: true });
    const bounds = await action.boundingBox();
    expect(bounds.height).toBeGreaterThanOrEqual(44);
    expect(bounds.width).toBeGreaterThanOrEqual(44);
    await tabTo(page, action);
    await expect(action).toBeFocused();
    await expect(action).toBeInViewport();
    const focus = await action.evaluate((element) => {
      const style = getComputedStyle(element);
      return { visible: element.matches(":focus-visible"), width: parseFloat(style.outlineWidth),
        style: style.outlineStyle, color: style.outlineColor };
    });
    expect(focus.visible).toBe(true);
    expect(focus.width).toBeGreaterThanOrEqual(2);
    expect(focus.style).toBe("solid");
    expect(focus.color).not.toBe("rgba(0, 0, 0, 0)");
  });
}

test("Home's hero states its actual cultural range under the unchanged accessible brand", async ({ page }) => {
  await openHome(page, {});
  await expect(page.getByRole("heading", { name: "Cât de român ești?", exact: true })).toBeVisible();
  await expect(page.getByText("De la Ștefan cel Mare la Las Fierbinți: șase jocuri scurte din cultura și viața românească.", { exact: true })).toBeVisible();
  await expect(page.getByText("Șase jocuri românești. Alege unul și intri direct în ritm.", { exact: true })).toHaveCount(0);
});

for (const graduated of [false, true]) {
  test(`Home ${graduated ? "removes both derived starter chips for explicit local graduation history" : "shows starter chips only on the two unplayed derived cards"}`, async ({ page }) => {
    const history = {};
    if (graduated) {
      // Explicit local presentation history: three free losses graduate Intrusul;
      // one free win graduates Perechi. Module arithmetic is covered separately.
      const losses = [0, 1, 2].map((index) => ({ score: 0, detail: "Pierdere locală de test", at: Date.parse(NOW) - index }));
      const win = { score: 500, detail: "Câștig local de test", at: Date.parse(NOW) };
      history.intrusul = { best: null, played: 3, recent: losses, completedNonDaily: true,
        nonDailyCompletions: 3, nonDailyWon: false };
      history.perechi = { best: win, played: 1, recent: [win], completedNonDaily: true,
        nonDailyCompletions: 1, nonDailyWon: true };
    }
    await openHome(page, history);
    const cards = page.locator(".games-grid .game-card");
    await expect(cards.locator(".game-card-title")).toHaveText(TITLES);
    const chip = "🌱 Nivel de început";
    await expect(cards.getByText(chip, { exact: true })).toHaveCount(graduated ? 0 : 2);
    for (let index = 0; index < 6; index += 1) {
      await expect(cards.nth(index).getByText(chip, { exact: true }))
        .toHaveCount(!graduated && [1, 2].includes(index) ? 1 : 0);
    }
    expect(await page.evaluate((key) => localStorage.getItem(key), SCORE_KEY)).toBe(JSON.stringify(history));
  });
}

function artifactBytes(directory, relative) {
  expect(typeof relative).toBe("string");
  expect(relative.length).toBeGreaterThan(0);
  const parts = relative.split("/");
  expect(parts.every((part) => part && part !== "." && part !== ".." && !part.includes("\\"))).toBe(true);
  const absolute = resolve(directory, ...parts);
  expect(absolute.startsWith(resolve(directory) + sep)).toBe(true);
  let current = resolve(directory);
  expect(realpathSync(current)).toBe(current);
  for (const part of parts) {
    current = resolve(current, part);
    expect(lstatSync(current).isSymbolicLink()).toBe(false);
  }
  expect(lstatSync(absolute).isFile()).toBe(true);
  return readFileSync(absolute);
}

test("the actual served build keeps optional account/game chunks outside static imports while binding emitted bytes", async ({ page, request }, testInfo) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Cât de român ești?", exact: true })).toBeVisible();
  const origin = new URL(page.url()).origin;
  const modules = await page.locator("script[type=module][src]").evaluateAll((elements) => elements.map((element) => element.src));
  expect(modules.length).toBeGreaterThan(0);
  const candidates = ["frontend/dist", "cat_de_roman_esti/web/static", "go-backend/embedfs/dist"];
  const matches = [];
  for (const relative of candidates) {
    const directory = resolve(root, relative), manifestFile = resolve(directory, ".vite/manifest.json");
    if (!existsSync(manifestFile)) continue;
    const manifestBytes = artifactBytes(directory, ".vite/manifest.json"), manifest = JSON.parse(manifestBytes);
    const entries = Object.entries(manifest).filter(([, row]) => row.isEntry);
    for (const [entry, row] of entries) {
      const module = modules.find((url) => {
        const parsed = new URL(url); return parsed.origin === origin && parsed.pathname.endsWith("/" + row.file);
      });
      if (!module) continue;
      const prefix = new URL(module).pathname.slice(0, -row.file.length);
      const response = await request.get(module);
      expect(response.status()).toBe(200);
      if (!(await response.body()).equals(artifactBytes(directory, row.file))) continue;
      matches.push({ directory, relative, manifest, manifestBytes, entry, prefix });
    }
  }
  expect(matches.length, "A genuine local build manifest must bind the actually served module bytes").toBeGreaterThan(0);
  for (const match of matches) {
    const closure = collectInitialBundleFiles(match.manifest);
    expect(closure.length).toBeGreaterThan(0);
    const optional = ["src/components/AccountBar.tsx", "src/screens/Intrusul.tsx", "src/screens/Perechi.tsx"]
      .map((key) => {
        const row = match.manifest[key];
        expect(row).toBeDefined();
        expect(row.isDynamicEntry).toBe(true);
        expect(closure).not.toContain(row.file);
        expect(match.manifest[match.entry].dynamicImports).toContain(key);
        return { key, file: row.file };
      });
    const bound = [];
    for (const file of [...new Set([...closure, ...optional.map(({ file }) => file)])]) {
      const bytes = artifactBytes(match.directory, file), url = new URL(match.prefix + file, origin).href;
      const response = await request.get(url);
      expect(response.status()).toBe(200);
      expect(response.url()).toBe(url);
      expect((await response.body()).equals(bytes)).toBe(true);
      expect(bytes.length).toBeGreaterThan(0);
      bound.push({ file, bytes: bytes.length, sha256: hash(bytes) });
    }
    await testInfo.attach(`static-closure-${match.relative.replaceAll("/", "-")}`, {
      body: JSON.stringify({ scope: "Observed build artifact/HTTP byte integrity, not a no-startup-fetch claim",
        artifact_root: match.relative, manifest_sha256: hash(match.manifestBytes), entry: match.entry,
        initial_static_files: closure, optional_dynamic_files: optional, bound }, null, 2), contentType: "application/json",
    });
  }
});
