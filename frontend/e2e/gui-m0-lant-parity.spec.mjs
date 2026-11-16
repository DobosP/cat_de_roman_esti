// Authored M0 parity replacements; NOT RUN during authoring. Every game state,
// correction, progress cue and hint below comes from the ordinary local server.
// The clipboard sink observes presentation output only; it is not native proof.
import { test, expect } from "@playwright/test";
import {
  games, gameURL, deterministicStarts, solution, start, tabTo,
} from "./games.mjs";

const game = games.find(({ key }) => key === "lant");
const easyJourney = { ...game, packId: "lt_geografie_239" };
const normalJourney = { ...game, packId: "lt_istorie_001" };
const field = (page) => page.getByRole("textbox", { name: "Următorul concept" });
const result = (page) => page.locator(".game-result");

const responseFor = (page, id, action) => page.waitForResponse((response) =>
  response.request().method() === "POST" &&
  new URL(response.url()).pathname === `${gameURL(game, id)}/${action}`);

async function begin(page, fixture = game) {
  const plan = solution(fixture);
  await deterministicStarts(page, fixture);
  const initial = await start(page, fixture);
  expect(initial.start).toEqual(plan.initial.start);
  expect(initial.target).toEqual(plan.initial.target);
  expect(initial.difficulty).toBe(plan.initial.difficulty);
  expect(initial.optimal).toBe(plan.initial.optimal);
  expect(initial.moves).toBe(0);
  expect(initial.won).toBe(false);
  return { initial, plan };
}

async function move(page, id, text) {
  await expect(field(page)).toBeEnabled();
  const pending = responseFor(page, id, "move");
  await field(page).fill(text);
  await field(page).press("Enter");
  const response = await pending;
  expect(response.status()).toBe(200);
  const moved = await response.json();
  expect(moved.ok).toBe(true);
  await expect(page.locator(".lant-current .lant-route-word"))
    .toHaveText(moved.current.label);
  if (!moved.won) await expect(field(page)).toBeEnabled();
  return moved;
}

async function saved(request, id) {
  const response = await request.get(gameURL(game, id));
  expect(response.status()).toBe(200);
  return response.json();
}

async function assertProgress(page, moved, kind) {
  expect(moved.progress.kind).toBe(kind);
  expect(moved.progress.message.length).toBeGreaterThan(0);
  if (moved.won) {
    await expect(result(page).getByRole("heading")).toBeFocused();
    return;
  }
  const cue = page.locator(".coach-line");
  await expect(cue).toHaveAttribute("role", "status");
  await expect(cue).toHaveAttribute("aria-atomic", "true");
  await expect(cue).toHaveText(moved.progress.message);
}

async function undo(page, id) {
  const pending = responseFor(page, id, "undo");
  await page.locator(".lant-undo").click();
  const response = await pending;
  expect(response.status()).toBe(200);
  const undone = await response.json();
  await expect(page.locator(".lant-current .lant-route-word"))
    .toHaveText(undone.current.label);
  await expect(field(page)).toBeEnabled();
  return undone;
}

test("Lanț help is keyboard operated and states input, free undo, move cap and step rules", async ({ page }) => {
  await begin(page);
  const toggle = page.getByRole("button", { name: "Cum se joacă", exact: true });
  const dialog = page.getByRole("dialog", { name: /Cum se joacă Lanțul Cuvintelor/ });
  await expect(dialog).toHaveCount(0);
  await tabTo(page, toggle);
  await page.keyboard.press("Space");
  await expect(dialog.getByRole("heading", { level: 2 })).toBeFocused();
  await expect(dialog).toContainText("Alege o legătură din listă sau scrie tu alt cuvânt legat de cel curent.");
  await expect(dialog).toContainText("Poți da înapoi gratuit. Un lanț poate avea până la 64 de salturi.");
  await expect(dialog).toContainText("Salturile anulate rămân numărate.");
  await page.keyboard.press("Escape");
  await expect(dialog).toHaveCount(0);
  await expect(toggle).toBeFocused();
});

test("a genuinely corrected winning hop retains the server's spelling message in the result", async ({ page, request }) => {
  const { initial, plan } = await begin(page);
  for (const step of plan.steps.slice(0, -1)) {
    expect((await move(page, initial.game_id, step.payload.text)).won).toBe(false);
  }
  // A one-character typo in the actual native planner's target, not a forged
  // MoveResult. Failure to resolve/correct this input fails the test outright.
  const typo = `${plan.steps.at(-1).payload.text}x`;
  expect(typo).not.toBe(initial.target.label);
  const won = await move(page, initial.game_id, typo);
  expect(won.won).toBe(true);
  expect(won.current.id).toBe(initial.target.id);
  expect(won.message).toBe(`Am înțeles: ${initial.target.label}.`);
  await expect(result(page)).toBeVisible();
  const correction = result(page).getByText(won.message, { exact: true });
  await expect(correction).toHaveCount(1);
  await expect(correction).toBeVisible();
  await assertProgress(page, won, "won");
  const persisted = await saved(request, initial.game_id);
  expect(persisted.won).toBe(true);
  expect(persisted.current).toEqual(won.current);
  expect(persisted.path).toEqual(won.path);
});

test("two real farther hops recommend the existing free undo and undo clears the cue", async ({ page, request }) => {
  const { initial } = await begin(page, easyJourney);
  expect(initial.start.label).toBe("Cluj-Napoca");
  expect(initial.target.label).toBe("Munții Apuseni");
  expect(initial.optimal).toBe(3);
  // These two bidirectional links are original graph content. Each public move
  // must actually succeed and supply the expected progress; no reverse is faked.
  for (const text of ["Transilvania", "Avram Iancu"]) {
    const closer = await move(page, initial.game_id, text);
    expect(closer.won).toBe(false);
    await assertProgress(page, closer, "closer");
    expect(closer.backtrack_recommended).toBe(false);
  }
  const undoButton = page.locator(".lant-undo");
  const first = await move(page, initial.game_id, "Transilvania");
  await assertProgress(page, first, "farther");
  expect(first.backtrack_recommended).toBe(false);
  await expect(undoButton).not.toHaveClass(/lant-undo--recommended/);
  const second = await move(page, initial.game_id, initial.start.label);
  await assertProgress(page, second, "farther");
  expect(second.backtrack_recommended).toBe(true);
  await expect(undoButton).toHaveClass(/lant-undo--recommended/);
  await expect(undoButton).toHaveAccessibleName("Înapoi, recomandat după două salturi fără progres");
  await expect(undoButton).toContainText("Înapoi · recomandat");
  const undone = await undo(page, initial.game_id);
  expect(undone.moves).toBe(second.moves - 1);
  expect(undone.path).toEqual(second.path.slice(0, -1));
  expect(undone.backtrack_recommended).toBe(false);
  await expect(undoButton).not.toHaveClass(/lant-undo--recommended/);
  await expect(undoButton).toHaveAccessibleName("Înapoi");
  await expect(page.locator(".coach-line")).toHaveText("Alege următorul cuvânt.");
  const persisted = await saved(request, initial.game_id);
  expect(persisted.path).toEqual(undone.path);
  expect(persisted.moves).toBe(undone.moves);
});

test("normal difficulty renders real server progress without inventing an easy-only recommendation", async ({ page, request }) => {
  const { initial, plan } = await begin(page, normalJourney);
  expect(initial.difficulty).toBe("normal");
  expect(initial.optimal).toBeGreaterThan(1);
  const moved = await move(page, initial.game_id, plan.steps[0].payload.text);
  expect(moved.won).toBe(false);
  await assertProgress(page, moved, "closer");
  expect(moved.backtrack_recommended).toBe(false);
  await expect(page.locator(".lant-undo")).not.toHaveClass(/lant-undo--recommended/);
  await expect(page.locator(".lant-undo")).toHaveAccessibleName("Înapoi");
  const undone = await undo(page, initial.game_id);
  expect(undone.moves).toBe(0);
  expect(undone.current).toEqual(initial.current);
  expect(undone.path).toEqual(initial.path);
  await expect(page.locator(".coach-line")).toHaveText("Alege următorul cuvânt.");
  expect((await saved(request, initial.game_id)).path).toEqual(initial.path);
});

test("a server-earned backtrack hint highlights free undo and clears when a real hop is undone", async ({ page, request }) => {
  const { initial } = await begin(page, easyJourney);
  let last;
  // Reach the actual 64-hop boundary with real API mutations on the browser's
  // own session. Do not inject a state/earned hint or assume an offline route
  // proves that either direction is legal on the selected running server.
  for (let index = 0; index < 64; index += 1) {
    const text = index % 2 === 0 ? "Transilvania" : initial.start.label;
    const response = await request.post(`${gameURL(game, initial.game_id)}/move`, { data: { text } });
    expect(response.status()).toBe(200);
    last = await response.json();
    expect(last.ok).toBe(true);
    expect(last.won).toBe(false);
    expect(last.current.label).toBe(text);
    expect(last.moves).toBe(index + 1);
  }
  const persisted = await saved(request, initial.game_id);
  expect(persisted.moves).toBe(64);
  expect(persisted.path).toEqual(last.path);
  expect(persisted.backtrack_recommended).toBe(false);
  await page.reload();
  await expect(field(page)).toBeEnabled();
  await expect(page.locator(".game-frame-status")).toContainText("64 de salturi");
  const undoButton = page.locator(".lant-undo");
  await expect(undoButton).not.toHaveClass(/lant-undo--recommended/);
  await expect(undoButton).toHaveAccessibleName("Înapoi");
  await expect(undoButton).toBeEnabled();
  await expect(page.getByRole("button", { name: "Fără indicii", exact: true })).toBeDisabled();
  expect((await request.post(`${gameURL(game, initial.game_id)}/hint`)).status()).toBe(400);
  const pending = responseFor(page, initial.game_id, "move");
  await field(page).fill("Transilvania");
  await field(page).press("Enter");
  const response = await pending;
  expect(response.status()).toBe(200);
  const capped = await response.json();
  expect(capped.ok).toBe(false);
  const guidance = "Limită atinsă — folosește Înapoi.";
  expect(capped.last_error).toBe(guidance);
  await expect(page.locator(".lant-screen .card").getByText(guidance, { exact: true })).toBeVisible();
  await expect(page.getByRole("status").filter({ hasText: guidance })).toHaveCount(1);
  expect(await saved(request, initial.game_id)).toEqual(persisted);
  const undone = await undo(page, initial.game_id);
  expect(undone.moves).toBe(63);
  expect(undone.path).toEqual(persisted.path.slice(0, -1));
  expect(undone.earned_hint).toBeUndefined();
  expect(undone.steps).toBe(persisted.steps);
  expect(undone.hints_left).toBeGreaterThan(0);
  await expect(page.getByRole("button", { name: "Indiciu", exact: true })).toBeEnabled();
  await expect(page.getByRole("status").filter({ hasText: guidance })).toHaveCount(0);
  await expect(undoButton).not.toHaveClass(/lant-undo--recommended/);
  expect((await saved(request, initial.game_id)).path).toEqual(undone.path);
});

for (const detour of [false, true]) {
  test(`${detour ? "detour" : "optimal"} win uses authoritative hop counts, steps and point-free copied result`, async ({ page, request }) => {
    // Observe the real app's write at the external clipboard boundary. This
    // explicit browser-only sink does not manufacture a game or native receipt.
    await page.addInitScript(() => {
      globalThis.__guiM0LantClipboard = [];
      Object.defineProperty(globalThis.navigator, "clipboard", {
        configurable: true,
        value: { writeText: async (text) => { globalThis.__guiM0LantClipboard.push(text); } },
      });
    });
    const { initial, plan } = await begin(page);
    if (detour) {
      const first = await move(page, initial.game_id, plan.steps[0].payload.text);
      expect(first.won).toBe(false);
      const back = await move(page, initial.game_id, initial.start.label);
      expect(back.won).toBe(false);
      expect(back.current.id).toBe(initial.start.id);
      expect(back.moves).toBe(2);
    }
    let won;
    for (const step of plan.steps) won = await move(page, initial.game_id, step.payload.text);
    expect(won.won).toBe(true);
    expect(won.moves).toBe(initial.optimal + (detour ? 2 : 0));
    const card = result(page);
    await expect(card.getByRole("heading", { name: "Ai reușit!", exact: true })).toBeFocused();
    await expect(card).toContainText(`Ai ajuns la ${initial.target.label}. Drumul cel mai scurt: ${initial.optimal} salturi.`);
    await expect(card).toContainText(`Pașii tăi: ${detour ? 2 : 0} pași`);
    await expect(card.getByText("Perfect", { exact: true })).toHaveCount(detour ? 0 : 1);
    await expect(page.locator(".game-frame-status")).toContainText(`${won.moves} salturi`);
    await expect(page.getByRole("group", { name: "Traseul parcurs" })).toContainText(initial.start.label);
    const persisted = await saved(request, initial.game_id);
    expect(persisted.path).toEqual(won.path);
    expect(persisted.moves).toBe(won.moves);
    expect(persisted.share).toBe(won.share);
    await card.getByRole("button", { name: "Copiază rezultatul", exact: true }).click();
    await expect.poll(() => page.evaluate(() => globalThis.__guiM0LantClipboard.length)).toBe(1);
    const copied = await page.evaluate(() => globalThis.__guiM0LantClipboard[0]);
    const url = new URL(page.url());
    const publicShare = won.share.trim().replace(/^cat_de_roman_esti/u, "Cât de român ești?");
    expect(copied).toBe(`${publicShare}\n\nJoacă: ${url.origin}${url.pathname}`);
    expect(copied).toContain(`${won.moves}/${initial.optimal} salturi`);
    expect(copied).not.toMatch(/mutări|MUTĂRI|Scor:/);
  });
}
