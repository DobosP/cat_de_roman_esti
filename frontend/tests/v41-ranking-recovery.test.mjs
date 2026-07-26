import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const ranking = read("../src/screens/Ranking.tsx");
const css = read("../src/styles/arcade.css");

test("ranking retries the selected game from a clean request state", () => {
  assert.match(ranking, /const \[attempt, setAttempt\] = useState\(0\)/);
  assert.match(ranking, /setLoading\(true\);\s+setError\(null\);\s+setData\(null\);/);
  assert.match(ranking, /getRanking\(game, 50\)/);
  assert.match(ranking, /\}, \[game, attempt\]\);/);
  assert.match(ranking, /onClick=\{\(\) => setAttempt\(\(value\) => value \+ 1\)\}/);
  assert.match(ranking, />\s*Reîncearcă\s*<\/button>/);
});

test("accounts-off and transient failures have distinct next actions", () => {
  assert.match(ranking, /reason instanceof AuthError && reason\.status === 404/);
  assert.match(ranking, /Clasamentul nu este activ aici\./);
  assert.match(ranking, /error === "unavailable"/);
  assert.match(ranking, /onClick=\{\(\) => navigate\("\/"\)\}/);
  assert.match(ranking, />\s*Acasă →\s*<\/button>/);
  assert.match(ranking, /Nu am putut încărca clasamentul\./);
});

test("loading and errors are announced in a centered touch-safe state card", () => {
  assert.match(
    ranking,
    /className="card ranking-state muted"\s+role="status"\s+aria-live="polite"\s+aria-busy="true"/,
  );
  assert.match(ranking, /\{!loading && error && \(/);
  assert.match(ranking, /<p className="account-error" role="alert">/);
  assert.match(
    css,
    /\.ranking-state\s*\{[^}]*display: grid;[^}]*align-content: center;[^}]*justify-items: center;/s,
  );
  assert.match(css, /\.ranking-state\s*\{[^}]*min-height: 100px;[^}]*padding: 18px;/s);
  assert.match(css, /\.ranking-state \.account-btn\s*\{[^}]*min-height: 44px;/s);
});
