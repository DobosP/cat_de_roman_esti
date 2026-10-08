// Authored NOT RUN. Fictional adult account/history presentation fixtures only;
// mocked account transports never qualify consent, deletion, child eligibility,
// production accounts or an owner's privacy approval. Existing tests stay intact.
import { test, expect } from "@playwright/test";

const SCORE_KEY = "cat_wordgame_scores_v1";
const RECEIPT = "99999999-9999-4999-8999-999999999999";
const NOW = "2026-10-08T12:00:00.000Z";
const ENTRY = { score: 500, detail: "Istoric local fictiv", at: Date.parse(NOW) };
const HISTORY = {
  alchimie: { best: ENTRY, played: 1, recent: [ENTRY], completedNonDaily: true,
    nonDailyCompletions: 1, nonDailyWon: true },
  _completionReceipts: { version: 1, games: { alchimie: [{ id: RECEIPT, at: Date.parse(NOW) }] } },
};
const ADULT = {
  id: 902, email: "adult-privacy-parity@example.invalid", name: "Adult privacy fixture", avatar: "",
  ranking_name: "", display_name: "", show_on_ranking: false, consent_completed: true,
  can_save_progress: false, is_minor: false, parental_consent_required: false,
};
const ANONYMOUS = { accounts_enabled: true, authenticated: false, user: null };
const local = (page) => page.evaluate((key) => localStorage.getItem(key), SCORE_KEY);

async function accountFixture(page, user) {
  let me = { accounts_enabled: true, authenticated: true, user };
  const posts = [];
  await page.clock.setFixedTime(new Date(NOW));
  await page.addInitScript(({ key, history }) => {
    if (localStorage.getItem(key) === null) localStorage.setItem(key, JSON.stringify(history));
  }, { key: SCORE_KEY, history: HISTORY });
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (request.method() === "POST" && url.pathname.startsWith("/api/")) posts.push(url.pathname);
  });
  await page.route("**/api/me", (route) => route.fulfill({ json: me }));
  for (const path of ["/api/auth/logout", "/api/me/delete"]) {
    await page.route(`**${path}`, async (route) => {
      expect(route.request().method()).toBe("POST");
      me = ANONYMOUS;
      await route.fulfill({ json: { ok: true } });
    });
  }
  // Even an unexpected client regression cannot send this fixture's score rows
  // into a real account backend. The negative transport assertion still fails.
  await page.route("**/api/me/scores", (route) => route.fulfill({ status: 503,
    json: { detail: "Private score transport is forbidden in this presentation fixture." } }));
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Cât de român ești?", exact: true })).toBeVisible();
  return posts;
}

test("fictional adult consent copy promises a private copy while declining keeps local play and receipts", async ({ page }) => {
  const posts = await accountFixture(page, { ...ADULT, consent_completed: false });
  const gate = page.locator(".account-card").filter({ has: page.getByRole("heading", { name: "Un pas rapid", exact: true }) });
  await expect(gate).toBeVisible();
  await expect(gate.getByText("Progresul rămâne aici. Pentru o copie privată a rezultatelor, confirmă vârsta și acceptă regulile.", { exact: true })).toBeVisible();
  await expect(gate.getByLabel("Poreclă (opțională; necesară doar pentru clasament)", { exact: true })).toBeEditable();
  await expect(gate.getByRole("link", { name: "Politica de confidențialitate", exact: true })).toHaveAttribute("href", "/legal/privacy");
  await expect(gate.getByRole("link", { name: "Termenii", exact: true })).toHaveAttribute("href", "/legal/terms");
  expect(posts).toEqual([]);
  expect(await local(page)).toBe(JSON.stringify(HISTORY));
  await gate.getByRole("button", { name: "Renunță", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Un pas rapid", exact: true })).toHaveCount(0);
  await expect(page.getByRole("link", { name: "Intră în cont", exact: true })).toBeVisible();
  await expect(page.locator(".games-grid .game-card")).toHaveCount(6);
  expect(posts).toEqual(["/api/auth/logout"]);
  expect(await local(page)).toBe(JSON.stringify(HISTORY));
});

async function deletePrompt(page, confirm) {
  const prompted = page.waitForEvent("dialog");
  const clicked = page.getByRole("menuitem", { name: "Șterge contul și datele", exact: true }).click();
  const dialog = await prompted;
  let answered = false;
  try {
    expect(dialog.type()).toBe("confirm");
    expect(dialog.message()).toBe("Ștergi contul și copia privată de pe server? Progresul de pe acest dispozitiv rămâne.");
    if (confirm) await dialog.accept(); else await dialog.dismiss();
    answered = true;
  } finally { if (!answered) await dialog.dismiss(); }
  await clicked;
}

test("fictional adult delete confirmation distinguishes its private account copy from retained local history", async ({ page }) => {
  const posts = await accountFixture(page, ADULT);
  const chip = page.locator(".account-chip");
  await expect(chip).toContainText(ADULT.name);
  await chip.click();
  await expect(page.getByRole("menu")).toBeVisible();
  await deletePrompt(page, false);
  expect(posts).toEqual([]);
  expect(await local(page)).toBe(JSON.stringify(HISTORY));
  await expect(chip).toContainText(ADULT.name);
  await deletePrompt(page, true);
  await expect(page.getByRole("link", { name: "Intră în cont", exact: true })).toBeVisible();
  await expect(chip).toHaveCount(0);
  expect(posts).toEqual(["/api/me/delete"]);
  expect(await local(page)).toBe(JSON.stringify(HISTORY));
  await expect(page.getByRole("heading", { name: "Cât de român ești?", exact: true })).toBeVisible();
});

test("an explicit fictional-adult restriction-flag projection preserves anonymous continuation copy and local history", async ({ page }, testInfo) => {
  // This inconsistent adult/policy flag is intentional public-field presentation
  // input for RestrictedNotice. It is not a real minor, policy decision, parental
  // consent fact or proof that an actual adult backend produces this state.
  await testInfo.attach("account-restriction-presentation-scope", {
    body: JSON.stringify({ scope: "NON-NATIVE fictional-adult public policy-flag DOM projection",
      is_minor: false, projected_parental_consent_required: true,
      validates_backend_age_or_parental_consent: false, real_child_data: false }, null, 2), contentType: "application/json",
  });
  const posts = await accountFixture(page, { ...ADULT, consent_completed: false, parental_consent_required: true });
  const notice = page.locator(".account-card").filter({ has: page.getByRole("heading", { name: "Cont restricționat", exact: true }) });
  await expect(notice).toBeVisible();
  await expect(notice.getByText("Contul există, dar rămâne restricționat. Poți juca local; nu încărcăm copia privată, nu memorăm jocurile terminate și nu te afișăm în clasament.", { exact: true })).toBeVisible();
  const action = notice.getByRole("button", { name: "Continuă fără cont", exact: true });
  await expect(action).toBeEnabled();
  expect(posts).toEqual([]);
  await action.click();
  await expect(page.getByRole("heading", { name: "Cont restricționat", exact: true })).toHaveCount(0);
  await expect(page.getByRole("link", { name: "Intră în cont", exact: true })).toBeVisible();
  await expect(page.locator(".games-grid .game-card")).toHaveCount(6);
  expect(posts).toEqual(["/api/auth/logout"]);
  expect(await local(page)).toBe(JSON.stringify(HISTORY));
});
