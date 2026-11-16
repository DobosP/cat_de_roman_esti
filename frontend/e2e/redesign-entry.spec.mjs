import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { games, solve, solution, tabTo } from "./games.mjs";

const day = "2026-10-08";
const now = new Date(day + "T12:00:00Z");
const ultimo = games.find(({ key }) => key === "intrusul");
const title = "Cât de român ești?";
const cards = {
  alchimie: "Alchimie",
  intrusul: "Intrusul",
  perechi: "Perechi",
  conexiuni: "Conexiuni",
  contexto: "Cald sau Rece",
  lant: "Lanțul Cuvintelor",
};
const created = (page, game) => page.waitForResponse((response) =>
  response.request().method() === "POST" &&
  new URL(response.url()).pathname === `/api/wordgames/${game.key}/games`);

for (const width of [320, 390]) {
  test(`six illustrated links fit ${width}px at enlarged text with visible focus`, async ({ page }) => {
    await page.setViewportSize({ width, height: 844 });
    await page.goto("/");
    await expect(page.getByRole("heading", { name: title })).toBeVisible();
    await page.evaluate(() => { document.documentElement.style.fontSize = "200%"; });
    const links = page.locator(".games-grid").getByRole("link");
    await expect(links).toHaveCount(6);
    for (const link of await links.all()) {
      const box = await link.boundingBox();
      expect(box.width).toBeGreaterThanOrEqual(44);
      expect(box.height).toBeGreaterThanOrEqual(44);
      expect(box.x + box.width).toBeLessThanOrEqual(width + 1);
      const image = link.locator("img");
      await expect(image).toHaveAttribute("alt", "");
      await expect(image).toHaveAttribute("src", /\/assets\/[\w-]+\.svg$/);
      const response = await page.request.get(await image.getAttribute("src"));
      expect(response.ok()).toBe(true);
      expect(response.headers()["content-type"]).toContain("image/svg+xml");
      expect(response.headers()["cache-control"]).toContain("immutable");
      expect(await response.text()).not.toMatch(/<script|\sstyle=/i);
    }
    const alchimie = links.filter({ hasText: "Alchimie" });
    await tabTo(page, alchimie);
    await expect(alchimie).toBeInViewport();
    expect(await alchimie.evaluate((element) => element.matches(":focus-visible"))).toBe(true);
  });
}

test("one tap starts the day's game, reload resumes it and the next tap opens free play", async ({ page }) => {
  await page.clock.setFixedTime(now);
  await page.goto("/");
  const card = page.locator(`.games-grid a[href="${ultimo.path}"]`);
  let response = created(page, ultimo);
  await card.click();
  const daily = await (await response).json();
  expect(daily.daily).toBe(day);
  await expect(page.getByText("Jocul zilei", { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.locator(ultimo.board)).toBeVisible();
  expect(await page.evaluate(() => localStorage.getItem("cat_active_game_v1_intrusul"))).toBe(daily.game_id);
  await solve(page, ultimo, solution({ ...ultimo, daily: day }).steps);
  await expect(page.locator(".game-result h2")).toBeFocused();
  await expect(page.locator(".game-result")).toContainText("Pașii tăi");
  await expect(page.locator(".game-result")).not.toContainText(/scor|puncte/i);
  await page.locator(".game-result").getByRole("button", { name: "Înapoi la jocuri" }).click();
  await expect(card).toContainText("Gata azi");
  response = created(page, ultimo);
  await card.click();
  expect((await (await response).json()).daily).toBeUndefined();
  await expect(page.getByText("Rundă liberă", { exact: true })).toBeVisible();
});

for (const colorScheme of ["light", "dark"]) {
  test(`device ${colorScheme} theme, persistent toggle and labelled help focus`, async ({ page }) => {
    await page.emulateMedia({ colorScheme, reducedMotion: "reduce" });
    await page.goto("/");
    await expect(page.getByRole("heading", { name: title })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.dataset.theme)).toBeUndefined();
    const opposite = colorScheme === "dark" ? "light" : "dark";
    const toggle = page.getByRole("button", { name: opposite === "dark"
      ? "Trece pe modul întunecat" : "Trece pe modul luminos" });
    await toggle.click();
    await expect(page.locator("html")).toHaveAttribute("data-theme", opposite);
    await page.reload();
    await expect(page.locator("html")).toHaveAttribute("data-theme", opposite);
    const first = created(page, ultimo);
    await page.locator(`.games-grid a[href="${ultimo.path}"]`).click();
    await first;
    const help = page.getByRole("button", { name: "Cum se joacă" });
    await tabTo(page, help);
    await page.keyboard.press("Enter");
    const dialog = page.getByRole("dialog", { name: "Cum se joacă Intrusul" });
    await expect(dialog).toBeVisible();
    await expect(dialog.getByRole("heading", { name: "Cum se joacă Intrusul" })).toBeFocused();
    for (let index = 0; index < 8; index += 1) {
      await page.keyboard.press("Tab");
      expect(await dialog.evaluate((element) => element.contains(document.activeElement))).toBe(true);
    }
    const axe = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
    expect(axe.violations.map(({ id }) => id)).toEqual([]);
    await page.keyboard.press("Escape");
    await expect(dialog).toHaveCount(0);
    await expect(help).toBeFocused();
  });
}

for (const game of games) {
  test(`${game.key} one-tap link brings the keyboard to the game heading`, async ({ page }) => {
    await page.goto("/");
    const card = page.locator(`.games-grid a[href="${game.path}"]`);
    await tabTo(page, card);
    const response = created(page, game);
    await page.keyboard.press("Enter");
    expect((await response).status()).toBe(200);
    await expect(page.getByRole("heading", { level: 1, name: cards[game.key] })).toBeFocused();
    await expect(page.locator(game.board)).toBeVisible();
  });
}
