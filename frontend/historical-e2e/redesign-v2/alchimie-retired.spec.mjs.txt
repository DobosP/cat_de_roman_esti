// Historical assertion extracts from 8186210a. Excluded from Playwright discovery.
// Source gui-m0-alchimie-parity.spec.mjs. Setup and menus moved into the shared help dialog.
async function oldThemedStart(page) {
  await openGameOptions(page, game, { setup: true });
  const normal = page.getByRole("group", { name: "DIFICULTATE", exact: true }).getByRole("button", { name: /^Normal\b/ });
  await normal.click();
  await expect(normal).toHaveAttribute("aria-pressed", "true");
  const theme = page.getByRole("group", { name: "CATEGORIE", exact: true })
    .getByRole("button", { name: "Artă și cultură", exact: true });
  await theme.click();
  await expect(theme).toHaveAttribute("aria-pressed", "true");
  await page.getByRole("button", { name: /^Joacă(?: →)?$/ }).click();
}
async function oldNextBoard(page) {
  await openAlchemyDisclosure(page, ".alchemy-menu");
  await page.getByRole("button", { name: "Alt joc", exact: true }).click();
  await page.getByRole("button", { name: "Încă unul →", exact: true }).click();
}
async function oldDaily(page, originalRequests, state, day) {
  await page.getByRole("button", { name: "Provocarea zilei", exact: true }).click();
  expect(originalRequests[0]).toMatchObject({ daily: day, difficulty: "normal" });
  expect(state.difficulty).toBe("normal");
}

// Source alchimie-content-freedom.spec.mjs. New pair steps and the Perfect badge replace the point result.
async function oldExperimentFeedback(page, won) {
  await expect(page.locator(".alchemy-feedback")).toContainText("Fără penalizare.");
  expect(won.score).toBe(1000);
}

// Source alchimie-workbench.spec.mjs. The shared band carries the move count; the Help dialog holds reset.
async function oldWorkbenchControls(page) {
  await expect(page.locator(".alchemy-bench .alchemy-round-count")).toHaveText("0 combinații");
  await expect(page.locator(".alchemy-bench .alchemy-round-count")).toHaveText("1 combinație");
  await expect(page.locator(".alchemy-menu")).not.toHaveAttribute("open");
  await expect(page.locator(".alchemy-menu > summary")).toContainText("Opțiuni de joc");
}
