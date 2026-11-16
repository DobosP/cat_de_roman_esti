// Preserved assertions for the retired introduction and in-board disclosures at 8186210a.
// The replacement journeys live in the current e2e suite.

// start-failure.spec.mjs
// await expect(page.locator(".game-intro")).toHaveAttribute("inert", "");
// await expect(page.locator(".game-intro")).toHaveAttribute("aria-busy", "true");
// await expect(page.locator(".game-shell-header button")).toBeDisabled();
// await expect(page.getByRole("button", { name: /^Joacă(?: →)?$/ })).toBeEnabled();
// await expect(page.locator(".alchemy-menu")).not.toHaveAttribute("open");

// resume-recovery.spec.mjs
// await expect(player.getByRole("button", { name: "Schimbă opțiunile" })).toHaveCount(0);
// await player.getByRole("button", { name: "Schimbă opțiunile" }).click();

// quick-games-simpler-ui.spec.mjs
// await expect(page.locator(".game-options")).toHaveCount(0);
// await expect(page.locator(".game-help")).not.toHaveAttribute("open");
// await expect(page.locator(".game-help")).toHaveAttribute("open", "");

// mobile-status-notices.spec.mjs
// await expect(page.getByRole("button", { name: /^Joacă(?: →)?$/ })).toBeEnabled();
// await layout(page, testInfo, `${width}-intro`);
