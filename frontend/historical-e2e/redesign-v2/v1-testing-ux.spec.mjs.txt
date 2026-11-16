// Historical witness extracts from 8186210a, frontend/e2e/v1-testing-ux.spec.mjs.
// Removed Home progress, setup and history surfaces superseded by ADR-0233.

for (const game of games) {
  test(`${game.key} circuit offers the daily round without creating one on navigation`, async ({ page }) => {
    await deterministicStarts(page, game);
    await page.goto("/");
    const creates = [];
    page.on("request", (request) => {
      if (request.method() === "POST" && new URL(request.url()).pathname === createPath(game)) creates.push(request.url());
    });
    await page.getByRole("button", { name: `Deschide ${titles[game.key]} — neterminat azi`, exact: true }).click();
    await expect(page).toHaveURL(/challenge=daily/);
    const daily = page.getByRole("button", { name: "Joacă provocarea zilei", exact: true });
    await expect(daily).toBeEnabled();
    await expect(page.getByRole("button", { name: "Joacă liber", exact: true })).toBeEnabled();
    expect(creates).toHaveLength(0);
    const expectedDay = await dayInBrowser(page);
    const created = page.waitForResponse((response) => response.request().method() === "POST" && new URL(response.url()).pathname === createPath(game));
    await daily.click();
    const response = await created;
    expect(response.status()).toBe(200);
    expect(new URL(response.url()).searchParams.get("daily")).toBe(expectedDay);
    expect((await response.json()).daily).toBe(expectedDay);
    await expect(page.locator(game.board)).toBeVisible();
    expect(creates).toHaveLength(1);
    await expect(page).not.toHaveURL(/challenge=/);
    if (game.key === "alchimie") await expect(page).toHaveURL(/[?&]mode=challenges(?:&|$)/);
  });

  test(`${game.key} circuit free start creates a free round and uses up the daily intent`, async ({ page }) => {
    await deterministicStarts(page, game);
    await page.goto("/");
    await page.getByRole("button", { name: `Deschide ${titles[game.key]} — neterminat azi`, exact: true }).click();
    await expect(page).toHaveURL(/challenge=daily/);
    const created = page.waitForResponse(isCreate(game));
    await page.getByRole("button", { name: "Joacă liber", exact: true }).click();
    const response = await created;
    expect(response.status()).toBe(200);
    expect(new URL(response.url()).searchParams.get("daily")).toBeNull();
    expect((await response.json()).daily).toBeFalsy();
    await expect(page.locator(game.board)).toBeVisible();
    await expect(page).not.toHaveURL(/challenge=/);
    if (game.key === "alchimie") await expect(page).toHaveURL(/[?&]mode=challenges(?:&|$)/);
  });
}

test("a finished circuit daily returns to an intro that leads with free play", async ({ page }) => {
  const game = games.find(({ key }) => key === "lant");
  await deterministicStarts(page, game);
  await page.goto("/");
  await page.getByRole("button", { name: "Deschide Lanțul Cuvintelor — neterminat azi", exact: true }).click();
  const expectedDay = await dayInBrowser(page);
  const created = page.waitForResponse(isCreate(game));
  await page.getByRole("button", { name: "Joacă provocarea zilei", exact: true }).click();
  expect((await (await created).json()).daily).toBe(expectedDay);
  await solve(page, game, solution({ ...game, daily: expectedDay }).steps);
  await page.getByRole("button", { name: "Schimbă opțiunile", exact: true }).click();
  const actions = page.locator(".game-intro-actions").getByRole("button");
  await expect(actions.first()).toHaveText("Joacă →");
  await expect(actions.nth(1)).toHaveAccessibleName("Provocarea zilei");
  await expect(page.getByRole("button", { name: "Joacă provocarea zilei", exact: true })).toHaveCount(0);
  await expect(page).not.toHaveURL(/challenge=/);
});

test("first visit presents descriptive game choices before daily progress", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator(".games-grid .game-card")).toHaveCount(6);
  expect(await page.locator(".games-grid").evaluate((cards) => {
    const progress = globalThis.document.querySelector(".daily-circuit");
    return Boolean(cards.compareDocumentPosition(progress) & globalThis.Node.DOCUMENT_POSITION_FOLLOWING);
  })).toBe(true);
  await expect(page.locator(".game-card--featured")).toContainText("Începe aici");
});

test("a circuit visit preserves an unfinished saved round", async ({ page, request }) => {
  const game = games.find(({ key }) => key === "intrusul");
  await deterministicStarts(page, game);
  const initial = await start(page, game);
  await page.getByRole("button", { name: "Ieși la lista de jocuri" }).click();
  const creates = [];
  page.on("request", (request) => {
    if (request.method() === "POST" && new URL(request.url()).pathname === createPath(game)) creates.push(request.url());
  });
  await page.getByRole("button", { name: "Deschide Intrusul — neterminat azi", exact: true }).click();
  await expect(page.locator(game.board)).toBeVisible();
  await expect(page.getByText(bypassNotice, { exact: true })).toBeVisible();
  expect(creates).toHaveLength(0);
  expect(await page.evaluate((key) => localStorage.getItem(key), activeKey(game))).toBe(initial.game_id);
  expect(await (await request.get(gameURL(game, initial.game_id))).json()).toEqual(initial);

  expect((await (await act(page, game, solution(game).steps[0])).json()).won).toBe(true);
  const replay = page.getByRole("button", { name: "Joacă provocarea zilei →", exact: true });
  await expect(replay.locator("..").getByRole("button").first()).toHaveText("Joacă provocarea zilei →");
  const expectedDay = await dayInBrowser(page);
  const created = page.waitForResponse(isCreate(game));
  await replay.click();
  const response = await created;
  expect(response.status()).toBe(200);
  expect(new URL(response.url()).searchParams.get("daily")).toBe(expectedDay);
  expect((await response.json()).daily).toBe(expectedDay);
  await expect(page.locator(game.board)).toBeVisible();
  await expect(page).not.toHaveURL(/challenge=/);
  expect(creates).toHaveLength(1);
});
