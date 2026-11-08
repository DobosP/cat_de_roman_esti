import { test, expect } from "@playwright/test";

const response = (p, path, method = "POST") => p.waitForResponse(r => r.request().method() === method && new URL(r.url()).pathname === path);

test("unsupported Cald sau Rece words are explicitly free and do not suggest unrelated spelling", async ({ page }) => {
  await page.goto("/cald-rece");
  const created = response(page, "/api/wordgames/contexto/games");
  await page.getByRole("button", { name: /^Joacă(?: →)?$/ }).click();
  const state = await (await created).json();
  const field = page.getByRole("textbox", { name: "Concept de ghicit" });
  for (const text of ["fier", "reparație", "scule", "rechizite"]) {
    await field.fill(text);
    const guessed = response(page, `/api/wordgames/contexto/games/${state.game_id}/guess`);
    await field.press("Enter");
    const result = await (await guessed).json();
    expect(result.ok).toBe(false);
    expect(result.attempts).toBe(0);
    expect(result.suggestions).not.toContain("fluier");
    expect(result.suggestions).not.toContain("pârâu");
    await expect(page.locator(".card").getByText(/Nu ai pierdut nicio încercare/)).toBeVisible();
    await expect(field).toHaveValue(text);
    await expect(field).toBeFocused();
  }
});
