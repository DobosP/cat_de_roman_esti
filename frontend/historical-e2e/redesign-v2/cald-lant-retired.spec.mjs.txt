// Historical witness extracts from 8186210a. Excluded from current Playwright discovery.

// frontend/e2e/contexto-simpler-ui.spec.mjs
test("one start reaches the guess field with setup and secondary tools tucked away", async ({ page }) => {
  await page.goto(game.path);
  await expect(page.locator(".game-setup-options")).not.toHaveAttribute("open", "");
  await expect(page.getByRole("button", { name: "Normal", exact: true })).not.toBeVisible();
  await start(page, game);
  await expect(field(page)).toBeInViewport();
  expect((await field(page).boundingBox()).y).toBeLessThan(280);
  await expect(page.locator(".game-options")).not.toHaveAttribute("open", "");
  await expect(page.getByRole("button", { name: "Arată răspunsul", exact: true })).not.toBeVisible();
  await expect(page.getByRole("button", { name: "Recente", exact: true })).not.toBeVisible();
  await expect(page.locator("#contexto-rank-guide")).toHaveText("Un număr mai mic = mai aproape. #1 este ținta.");
  await expect(page.getByRole("button", { name: "Cum citesc #?", exact: true })).toHaveCount(0);
  await expect(page.locator("#contexto-clue-cost")).toBeVisible();
  await expect(page.getByRole("button", { name: "Indiciu după 3 încercări", exact: true }))
    .toHaveAccessibleDescription("−120 puncte / indiciu");
});

// frontend/e2e/contexto-simpler-ui.spec.mjs
test("rules open full width below the clue button and 'Opțiuni de joc' stays beside it", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await start(page, game);
  const clue = page.locator(".contexto-action-row");
  const summary = options(page);
  const help = page.locator(".contexto-screen details.game-help");
  await help.locator("summary").click();
  await expect(help).toHaveAttribute("open", "");
  const [clueBox, optionsBox, helpBox, toolsBox] = await Promise.all([
    clue.boundingBox(), summary.boundingBox(), help.boundingBox(), page.locator(".contexto-tools").boundingBox(),
  ]);
  await test.info().attach("help-layout", {
    body: JSON.stringify({ clueBox, optionsBox, helpBox, toolsBox }, null, 2), contentType: "application/json",
  });
  expect(Math.abs(optionsBox.y - clueBox.y)).toBeLessThan(2);
  expect(optionsBox.x).toBeGreaterThan(clueBox.x + clueBox.width);
  expect(helpBox.y).toBeGreaterThanOrEqual(Math.max(clueBox.y + clueBox.height, optionsBox.y + optionsBox.height));
  expect(Math.abs(helpBox.width - toolsBox.width)).toBeLessThan(2);
});

// frontend/e2e/contexto-simpler-ui.spec.mjs
test("the clue countdown label fits its half of the row at 320px", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 640 });
  await start(page, game);
  const clue = page.getByRole("button", { name: "Indiciu după 3 încercări", exact: true });
  await expect(clue).toBeVisible();
  const fit = await clue.evaluate((element) => {
    const range = globalThis.document.createRange();
    range.selectNodeContents(element);
    const box = element.getBoundingClientRect();
    const text = range.getBoundingClientRect();
    return {
      scroll: element.scrollWidth, client: element.clientWidth, height: box.height,
      textInside: text.left >= box.left && text.right <= box.right && text.top >= box.top && text.bottom <= box.bottom,
    };
  });
  await test.info().attach("clue-fit", { body: JSON.stringify(fit, null, 2), contentType: "application/json" });
  // The longer label may wrap to two lines, but it stays inside the unchanged 44px target.
  expect(fit.scroll).toBeLessThanOrEqual(fit.client + 1);
  expect(fit.textInside).toBe(true);
  expect(fit.height).toBeLessThanOrEqual(45);
});

// frontend/e2e/gui-m0-contexto-parity.spec.mjs
test("typing and actual new-game/exit lifecycles dismiss reveal without giving up either round", async ({ page }) => {
  const initial = await start(page, game), mutations = traffic(page);
  await armReveal(page); await field(page).fill("curiozitate");
  await expect(confirmation(page)).toHaveCount(0); expect(mutations).toEqual([]);
  await armReveal(page);
  await page.getByRole("button", { name: "Începe alt joc", exact: true }).click();
  await expect(confirmation(page)).toHaveCount(0);
  await expect(page.getByRole("button", { name: /^Joacă(?: →)?$/ })).toBeVisible();
  const response = page.waitForResponse((result) => result.request().method() === "POST"
    && new URL(result.url()).pathname === "/api/wordgames/contexto/games");
  await page.getByRole("button", { name: /^Joacă(?: →)?$/ }).click();
  const received = await response; expect(received.status()).toBe(200);
  const next = await received.json(); expect(next.game_id).not.toBe(initial.game_id);
  await expect(field(page)).toHaveValue("");
  await armReveal(page);
  await page.getByRole("button", { name: "Ieși la lista de jocuri", exact: true }).click();
  await expect(page).toHaveURL(/\/$/); await expect(confirmation(page)).toHaveCount(0);
  expect(mutations.filter(({ pathname }) => pathname.endsWith("/giveup"))).toEqual([]);
});

// frontend/e2e/gui-m0-lant-parity.spec.mjs
test("Lanț intro disclosure is optional, keyboard operated and states all four rules", async ({ page }) => {
  let creates = 0;
  page.on("request", (request) => {
    if (request.method() === "POST" &&
        new URL(request.url()).pathname === "/api/wordgames/lant/games") creates += 1;
  });
  await page.goto(game.path);
  const toggle = page.getByRole("button", { name: "Cum funcționează", exact: true });
  const disclosure = page.locator("#lant-intro-disclosure");
  await expect(toggle).toHaveAttribute("aria-expanded", "false");
  await expect(toggle).toHaveAttribute("aria-controls", "lant-intro-disclosure");
  await expect(disclosure).toBeHidden();
  await tabTo(page, toggle);
  await page.keyboard.press("Space");
  await expect(toggle).toBeFocused();
  await expect(toggle).toHaveAttribute("aria-expanded", "true");
  await expect(disclosure).toBeVisible();
  await expect(disclosure.locator("li")).toHaveText([
    "Salturile afișate amestecă drumul cel mai scurt cu ocoluri sigure.",
    "Înapoi e gratuit și nelimitat.",
    "Poți scrie orice concept legat — nu doar din listă.",
    "Limită: 64 de salturi pe lanț.",
  ]);
  await page.keyboard.press("Space");
  await expect(toggle).toHaveAttribute("aria-expanded", "false");
  await expect(disclosure).toBeHidden();
  await expect(toggle).toBeFocused();
  expect(creates).toBe(0);
});

// frontend/e2e/lant-simpler-ui.spec.mjs
test("'Începe alt lanț' abandons the board and re-entering opens the intro, not the old board", async ({ page }) => {
  const initial = await start(page, game);
  await expect(page.getByRole("button", { name: "Începe alt lanț", exact: true })).toBeHidden();
  await page.locator(".game-options > summary").click();
  const giveUp = page.getByRole("button", { name: "Începe alt lanț", exact: true });
  await expect(giveUp).toHaveAttribute("title", "Renunță la acest lanț și alege altul");
  await tapOrClick(giveUp);
  const play = page.getByRole("button", { name: /^Joacă(?: →)?$/ });
  await expect(play).toBeEnabled();
  expect(await page.evaluate((key) => localStorage.getItem(key), activeKey(game))).toBeNull();
  let reads = 0;
  page.on("request", (request) => {
    if (request.method() === "GET" && new URL(request.url()).pathname === gameURL(game, initial.game_id)) reads += 1;
  });
  await page.goto("/");
  await page.getByRole("button", { name: /^Joacă Lanțul Cuvintelor —/ }).click();
  await expect(play).toBeEnabled();
  await expect(page.locator(game.board)).toHaveCount(0);
  expect(reads).toBe(0);
});

// Retired from the Lanț result clipboard assertion in gui-m0-lant-parity.spec.mjs:
// The surviving witness compares the same share body and suffix without visible score.
expect(copied).toBe(`${publicShare}\n\nJoacă: ${url.origin}${url.pathname}\nScor: ${won.score}`);
