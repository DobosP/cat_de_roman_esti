type Theme = "light" | "dark";
const key = "cat_theme";

export function installTheme(): void {
  try {
    const stored = localStorage.getItem(key);
    if (stored === "light" || stored === "dark") document.documentElement.dataset.theme = stored;
  } catch { /* The device setting applies. */ }
}

export function currentTheme(): Theme {
  const theme = document.documentElement.dataset.theme;
  return theme === "light" || theme === "dark" ? theme :
    matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function toggleTheme(): Theme {
  const theme = currentTheme() === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = theme;
  try { localStorage.setItem(key, theme); } catch { /* Apply for this visit. */ }
  return theme;
}
