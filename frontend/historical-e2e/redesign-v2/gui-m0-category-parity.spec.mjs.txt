// Authored M0 replacements; NOT RUN. Native metadata cases use the actual local
// /api/categories response. Stale-selection cases explicitly project only public
// availability metadata onto the real application UI, not a backend qualification.
import { test, expect } from "@playwright/test";
import { games, deterministicStarts, openGameOptions } from "./games.mjs";

const GAME_KEYS = ["alchimie", "conexiuni", "contexto", "lant"];
const LEVELS = ["usor", "normal", "greu"];
const DIFFICULTY_NAMES = { usor: /^Ușor\b/, normal: /^Normal\b/, greu: /^Greu\b/ };
const LABELS = {
  istorie: "Istorie", literatura: "Literatură", geografie: "Geografie",
  personalitati: "Personalități", arta_cultura: "Artă și cultură", stiinta: "Știință",
  societate: "Societate", limba: "Limbă", mixed: "Toate temele", muzica: "Muzică",
  film_tv: "Film și seriale", meme_net: "Internet și meme", sport: "Sport",
  viata_de_roman: "Viața în România", gastronomie: "Gastronomie",
};
const categoryGroup = (page) => page.getByRole("group", { name: "CATEGORIE", exact: true });
const difficultyGroup = (page) => page.getByRole("group", { name: "DIFICULTATE", exact: true });
const labelFor = (category) => LABELS[category.key] ?? "Necunoscut";

async function nativeCategories(request) {
  const response = await request.get("/api/categories");
  expect(response.status()).toBe(200);
  const body = await response.json();
  expect(Array.isArray(body.categories)).toBe(true);
  expect(body.categories.length).toBeGreaterThan(0);
  expect(new Set(body.categories.map(({ key }) => key)).size).toBe(body.categories.length);
  for (const category of body.categories) {
    expect(typeof category.key).toBe("string");
    expect(["pop", "serious"]).toContain(category.kind);
    for (const game of GAME_KEYS) {
      for (const level of LEVELS) expect(typeof category.available_by_difficulty[game][level]).toBe("boolean");
    }
  }
  return body;
}

async function chooseDifficulty(page, level) {
  const choice = difficultyGroup(page).getByRole("button", { name: DIFFICULTY_NAMES[level] });
  await choice.click();
  await expect(choice).toHaveAttribute("aria-pressed", "true");
}

async function assertShelves(page, categories, game, level) {
  const group = categoryGroup(page);
  await expect(group).toBeVisible();
  const expected = categories.filter((category) => category.available_by_difficulty[game][level])
    .map(labelFor).sort();
  const buttons = group.getByRole("button");
  await expect(buttons).toHaveCount(expected.length + 1);
  await expect(buttons.first()).toHaveText("Toate temele");
  const actual = await buttons.allTextContents();
  expect(actual.slice(1).map((label) => label.trim()).sort()).toEqual(expected);
  for (const button of await buttons.all()) await expect(button).toBeEnabled();
  await expect(group.getByText("Indisponibil la această dificultate", { exact: true })).toHaveCount(0);
}

function presentationMatrix(native) {
  const keys = ["sport", "geografie", "arta_cultura", "film_tv"];
  const categories = keys.map((key, index) => {
    const row = native.categories.find((category) => category.key === key);
    expect(row).toBeDefined();
    const available_by_difficulty = Object.fromEntries(GAME_KEYS.map((game, gameIndex) => [game,
      Object.fromEntries(LEVELS.map((level, levelIndex) => [level, index === (gameIndex + levelIndex) % keys.length]))]));
    return { ...row, available_by_difficulty,
      available: Object.fromEntries(GAME_KEYS.map((game) => [game, Object.values(available_by_difficulty[game]).some(Boolean)])),
    };
  });
  return { ...native, categories };
}

for (const key of GAME_KEYS) {
  const game = games.find((entry) => entry.key === key);

  test(`${key} renders exactly the real native playable category shelf for each difficulty`, async ({ page, request }) => {
    const native = await nativeCategories(request);
    const metadata = page.waitForResponse((response) => response.request().method() === "GET"
      && new URL(response.url()).pathname === "/api/categories");
    await page.goto(game.path);
    await metadata;
    await openGameOptions(page, game, { setup: true });
    for (const level of LEVELS) {
      await chooseDifficulty(page, level);
      await assertShelves(page, native.categories, key, level);
      await expect(categoryGroup(page).getByRole("button", { name: "Toate temele", exact: true }))
        .toHaveAttribute("aria-pressed", "true");
    }
  });

  test(`${key} clears a category invalidated by difficulty and creates a real unfiltered round`, async ({ page, request }, testInfo) => {
    const native = await nativeCategories(request), projected = presentationMatrix(native);
    await testInfo.attach("category-availability-presentation-scope", {
      body: JSON.stringify({ scope: "NON-NATIVE public availability metadata presentation",
        game: key, category_keys: projected.categories.map(({ key }) => key),
        available_by_difficulty: projected.categories.map(({ key, available_by_difficulty }) => ({ key, available_by_difficulty })),
        validates_native_category_availability: false }, null, 2), contentType: "application/json",
    });
    const metadataRequests = [];
    await page.route("**/api/categories", async (route) => {
      metadataRequests.push(route.request().method());
      expect(route.request().method()).toBe("GET");
      await route.fulfill({ json: projected });
    });
    await deterministicStarts(page, game);
    await page.goto(game.path);
    await openGameOptions(page, game, { setup: true });
    // Every game has a different projected shelf, detecting a wrong game binding.
    for (const level of LEVELS) {
      await chooseDifficulty(page, level);
      await assertShelves(page, projected.categories, key, level);
    }
    await chooseDifficulty(page, "usor");
    await assertShelves(page, projected.categories, key, "usor");
    const selected = projected.categories.find((category) => category.available_by_difficulty[key].usor);
    expect(selected.available_by_difficulty[key].normal).toBe(false);
    const group = categoryGroup(page);
    await group.getByRole("button", { name: labelFor(selected), exact: true }).click();
    await expect(group.getByRole("button", { name: labelFor(selected), exact: true }))
      .toHaveAttribute("aria-pressed", "true");
    await expect(group.getByRole("button", { name: "Toate temele", exact: true }))
      .toHaveAttribute("aria-pressed", "false");
    await chooseDifficulty(page, "normal");
    await assertShelves(page, projected.categories, key, "normal");
    await expect(group.getByRole("button", { name: labelFor(selected), exact: true })).toHaveCount(0);
    await expect(group.getByRole("button", { name: "Toate temele", exact: true }))
      .toHaveAttribute("aria-pressed", "true");
    const created = page.waitForResponse((response) => response.request().method() === "POST"
      && new URL(response.url()).pathname === `/api/wordgames/${key}/games`);
    await page.getByRole("button", { name: /^Joacă(?: →)?$/, exact: true }).click();
    const response = await created;
    expect(response.status()).toBe(200);
    const query = new URL(response.url()).searchParams;
    expect(query.get("difficulty")).toBe("normal");
    expect(query.get("category")).toBeNull();
    expect(query.get("daily")).toBeNull();
    const state = await response.json();
    expect(state.difficulty).toBe("normal");
    if (key === "alchimie") {
      // Unfiltered Alchimie still chooses a real themed board on the server.
      // Query omission proves clearing; it does not imply a theme-free response.
      expect(typeof state.board_category).toBe("string");
      expect(state.board_category.length).toBeGreaterThan(0);
      const chosen = native.categories.find((category) => category.key === state.board_category);
      expect(chosen).toBeDefined();
      expect(chosen.available_by_difficulty.alchimie.normal).toBe(true);
    } else {
      expect(state.board_category).toBeFalsy();
    }
    await expect(page.locator(game.board)).toBeVisible();
    expect(metadataRequests.length).toBeGreaterThan(0);
    expect(metadataRequests.every((method) => method === "GET")).toBe(true);
  });
}
