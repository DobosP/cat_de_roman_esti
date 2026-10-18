/** The original query precedence, including the saved challenge fallback. */
export function alchimieMode(url: string, legacyResume: boolean): "challenges" | "explore" {
  const params = new URL(url, "http://local.invalid").searchParams;
  const challenge = params.get("mode") !== "explore" && (params.get("mode") === "challenges" ||
    ["daily", "category", "seed", "difficulty"].some((key) => params.has(key)) || legacyResume);
  return challenge ? "challenges" : "explore";
}
