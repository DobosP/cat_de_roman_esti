import { test, expect } from "@playwright/test";
import { games, deterministicStarts, start, solve, solution, tabTo } from "./games.mjs";

async function settle(page) {
  await page.evaluate(async () => {
    await globalThis.document.fonts.ready;
    await Promise.all(globalThis.document.getAnimations().filter((animation) =>
      Number.isFinite(animation.effect?.getComputedTiming().endTime),
    ).map((animation) => animation.finished.catch(() => {})));
  });
}

async function layout(page, testInfo, state) {
  await settle(page);
  const metrics = await page.evaluate(() => {
    const rect = (element) => {
      if (!element) return null;
      const box = element.getBoundingClientRect();
      return { left: box.left, top: box.top, right: box.right, bottom: box.bottom,
        width: box.width, height: box.height };
    };
    const header = globalThis.document.querySelector(".game-shell-header");
    const hud = header.querySelector(".hud");
    const scroller = globalThis.document.querySelector(".screen-pad");
    return {
      width: globalThis.innerWidth,
      pageWidth: globalThis.document.documentElement.scrollWidth,
      scrollWidth: scroller.scrollWidth,
      clientWidth: scroller.clientWidth,
      header: rect(header),
      title: rect(header.querySelector(".game-shell-title")),
      hud: rect(hud),
      hudScrollWidth: hud?.scrollWidth,
      badges: hud ? [...hud.children].map((child) => ({ text: child.textContent, ...rect(child) })) : [],
      notices: [...globalThis.document.querySelectorAll(".roedu-toast")].map(rect),
      content: rect(globalThis.document.querySelector(".app-content")),
    };
  });
  await testInfo.attach(`${state}-geometry`, {
    body: JSON.stringify(metrics, null, 2), contentType: "application/json",
  });
  expect(metrics.pageWidth, `${state}: page width`).toBeLessThanOrEqual(metrics.width);
  expect(metrics.scrollWidth, `${state}: screen width`).toBeLessThanOrEqual(metrics.clientWidth);
  if (metrics.hud) {
    expect(metrics.title.width, `${state}: visible game title`).toBeGreaterThan(2);
    expect(metrics.title.right).toBeLessThanOrEqual(metrics.width);
    expect(metrics.hudScrollWidth, `${state}: all counters fit without scrolling`)
      .toBeLessThanOrEqual(Math.ceil(metrics.hud.width));
    for (const badge of metrics.badges) {
      expect(badge.left, `${state}: ${badge.text}`).toBeGreaterThanOrEqual(metrics.header.left);
      expect(badge.right, `${state}: ${badge.text}`).toBeLessThanOrEqual(metrics.header.right);
      expect(badge.bottom, `${state}: ${badge.text}`).toBeLessThanOrEqual(metrics.header.bottom);
    }
  }
  for (const notice of metrics.notices) {
    expect(notice.bottom, `${state}: notice leaves the screen unobstructed`)
      .toBeLessThanOrEqual(metrics.content.top);
  }
}

for (const game of games) {
  test(`${game.key} keeps its status and notices visible through resume and result`, async ({ page }, testInfo) => {
    test.setTimeout(120_000);
    const widths = testInfo.project.name === "mobile" ? [320, 390] : [1280];
    await deterministicStarts(page, game);
    for (const width of widths) {
      await page.setViewportSize({ width, height: 850 });
      await page.goto(game.path);
      await page.evaluate(() => localStorage.clear());
      await page.reload();
      await expect(page.getByRole("button", { name: /^Joacă(?: →)?$/ })).toBeEnabled();
      await layout(page, testInfo, `${width}-intro`);
      await start(page, game);
      await layout(page, testInfo, `${width}-live`);
      await page.reload();
      await expect(page.locator(game.board)).toBeVisible();
      await expect(page.getByText(/^Joc reluat\./)).toBeVisible();
      await layout(page, testInfo, `${width}-resume`);
      await testInfo.attach(`${width}-resume`, { body: await page.screenshot(), contentType: "image/png" });
      const exit = page.getByRole("button", { name: "Ieși la lista de jocuri" });
      await tabTo(page, exit);
      await expect(exit).toBeFocused();
      await page.locator(".screen-pad").evaluate((element) => { element.scrollTop = element.scrollHeight; });
      await layout(page, testInfo, `${width}-scrolled`);
      if (width <= 640) {
        const sticky = page.locator(".connections-coach-stack, .contexto-sticky-controls, .alchemy-bench, .word-hop-input");
        for (const control of await sticky.all()) {
          const top = (await control.boundingBox()).y;
          const header = await page.locator(".game-shell-header").boundingBox();
          expect(top, "secondary sticky controls stay below the wrapped header")
            .toBeGreaterThanOrEqual(header.y + header.height);
        }
      }
      await solve(page, game, solution(game).steps);
      await layout(page, testInfo, `${width}-finished`);
      // Exercise the real copy failure feedback without relying on host clipboard permissions.
      await page.evaluate(() => {
        Object.defineProperty(globalThis.navigator, "clipboard", {
          configurable: true, value: { writeText: async () => { throw new Error("Clipboard unavailable in test"); } },
        });
        globalThis.document.execCommand = () => false;
      });
      await page.getByRole("button", { name: "Copiază rezultatul" }).click();
      const failure = page.getByRole("button", { name: /Nu am putut copia\./ });
      await expect(failure).toBeVisible();
      await layout(page, testInfo, `${width}-copy-failed`);
      await failure.focus();
      await page.keyboard.press("Space");
      await expect(failure).toHaveCount(0);
      await expect(page.getByRole("button", { name: /^Încă (?:unul|un lanț) →$/ })).toBeEnabled();
    }
  });
}

test("long Romanian status stays readable with text zoom and a short viewport", async ({ page }, testInfo) => {
  const game = games[0];
  await page.setViewportSize({ width: 320, height: 850 });
  await deterministicStarts(page, game);
  await start(page, game);
  // Presentation stress only: no game state or network response is changed.
  await page.evaluate(() => {
    globalThis.document.documentElement.style.fontSize = "200%";
    globalThis.document.querySelector(".stat-badge-value").textContent = "Personalități și viața de zi cu zi în România";
    globalThis.document.querySelector(".game-shell-title").textContent = "Lanțul Cuvintelor Românești";
  });
  await layout(page, testInfo, "long-labels-200-percent");
  await testInfo.attach("long-labels-200-percent", { body: await page.screenshot(), contentType: "image/png" });
  await page.setViewportSize({ width: 320, height: 480 });
  await page.getByRole("searchbox", { name: "Caută în toate conceptele descoperite" }).focus();
  await expect(page.getByRole("searchbox", { name: "Caută în toate conceptele descoperite" })).toBeInViewport();
  await layout(page, testInfo, "short-viewport-focused-input");
  await testInfo.attach("short-viewport-focused-input", { body: await page.screenshot(), contentType: "image/png" });
});
