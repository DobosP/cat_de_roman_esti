// Authored M0 replacements; NOT RUN. Native metadata cases use the actual local
// /api/categories response. Stale-selection cases explicitly project only public
// availability metadata onto the real application UI, not a backend qualification.
import { test, expect } from "@playwright/test";
import { games, deterministicStarts, openGameOptions } from "./games.mjs";

const GAME_KEYS = ["alchimie", "conexiuni", "contexto", "lant"];
const LEVELS = ["usor", "normal", "greu"];
const LABELS = {
  istorie: "Istorie", literatura: "Literatură", geografie: "Geografie",
  personalitati: "Personalități", arta_cultura: "Artă și cultură", stiinta: "Știință",
  societate: "Societate", limba: "Limbă", mixed: "Toate temele", muzica: "Muzică",
  film_tv: "Film și seriale", meme_net: "Internet și meme", sport: "Sport",
  viata_de_roman: "Viața în România", gastronomie: "Gastronomie",
};
const categoryGroup = (page) => page.getByRole("combobox", { name: "Temă", exact: true });
const difficultyGroup = (page) => page.getByRole("combobox", { name: "Dificultate", exact: true });
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
  const choice = difficultyGroup(page);
  await choice.selectOption(level);
  await expect(choice).toHaveValue(level);
}

async function assertShelves(page, categories, game, level) {
  const theme = categoryGroup(page);
  await expect(theme).toBeVisible();
  const expected = categories.filter((category) => category.key !== "mixed" && category.available_by_difficulty[game][level])
    .map(labelFor).sort();
  const options = theme.locator("option");
  await expect(options).toHaveCount(expected.length + 1);
  await expect(options.first()).toHaveText("Toate temele");
  const actual = await options.allTextContents();
  expect(actual.slice(1).map((label) => label.trim()).sort()).toEqual(expected);
  for (const option of await options.all()) await expect(option).toBeEnabled();
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
    await openGameOptions(page, game);
    await metadata;
    for (const level of LEVELS) {
      await chooseDifficulty(page, level);
      await assertShelves(page, native.categories, key, level);
      await expect(categoryGroup(page)).toHaveValue("");
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
    await openGameOptions(page, game);
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
    await group.selectOption(selected.key);
    await expect(group).toHaveValue(selected.key);
    await chooseDifficulty(page, "normal");
    await assertShelves(page, projected.categories, key, "normal");
    await expect(group.locator(`option[value="${selected.key}"]`)).toHaveCount(0);
    await expect(group).toHaveValue("");
    await page.keyboard.press("Escape");
    await page.evaluate((gameKey) => localStorage.removeItem(`cat_active_game_v1_${gameKey}`), key);
    const created = page.waitForResponse((response) => response.request().method() === "POST"
      && new URL(response.url()).pathname === `/api/wordgames/${key}/games`);
    await page.reload();
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
