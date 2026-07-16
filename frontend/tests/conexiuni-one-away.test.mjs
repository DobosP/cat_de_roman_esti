import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const screen = readFileSync(
  new URL("../src/screens/Conexiuni.tsx", import.meta.url),
  "utf8",
);

test("Conexiuni treats a retained one-away selection as an order-independent set", () => {
  assert.match(
    screen,
    /selectionKey = \(ids: readonly string\[\]\) => JSON\.stringify\(\[\.\.\.ids\]\.sort\(\)\)/,
  );
  assert.match(screen, /selectionKey\(selected\) === blockedGuess\.key/);
});

test("Conexiuni snapshots and retains only a recoverable one-away guess", () => {
  assert.match(screen, /const guess = \[\.\.\.selected\];/);
  assert.match(screen, /recoverableOneAway = Boolean\(res\.one_away && !res\.lost\)/);
  assert.match(
    screen,
    /if \(recoverableOneAway\) \{\s*setSelected\(guess\);\s*setBlockedGuess\(\{ key: guessKey, oneAway: true \}\);\s*\} else \{\s*setSelected\(\[\]\);\s*setBlockedGuess\(null\);/,
  );
  assert.match(screen, /Schimbă cel puțin o piesă și verifică din nou/);
  assert.match(
    screen,
    /feedback = blockedGuess\?\.oneAway \? ONE_AWAY_GUIDANCE : hint/,
  );
});

test("Conexiuni blocks unchanged retries in submit, keyboard, and button paths", () => {
  assert.match(
    screen,
    /selected\.length !== GROUP_SIZE \|\| busy \|\| exactBlockedRetry/,
  );
  assert.match(
    screen,
    /e\.key === "Enter" && selected\.length === GROUP_SIZE && !exactBlockedRetry/,
  );
  assert.match(
    screen,
    /disabled=\{busy \|\| selected\.length !== GROUP_SIZE \|\| exactBlockedRetry\}/,
  );
  assert.match(screen, /exactBlockedRetry \? "Schimbă o piesă" : "Verifică"/);
});

test("Conexiuni remembers a server-rejected duplicate and preserves terminal resets", () => {
  assert.match(
    screen,
    /err\.status === 409\) \{\s*setSelected\(guess\);\s*setBlockedGuess\(\{ key: guessKey, oneAway: false \}\);/,
  );
  assert.match(
    screen,
    /if \(res\.correct\) \{[\s\S]{0,180}setSelected\(\[\]\);\s*setBlockedGuess\(null\);/,
  );
  assert.doesNotMatch(
    screen,
    /const clearSelection = useCallback\([\s\S]{0,180}setBlockedGuess\(null\)/,
  );
});

test("Conexiuni never turns a generic duplicate rejection into one-away feedback", () => {
  assert.match(screen, /setBlockedGuess\(\{ key: guessKey, oneAway: false \}\)/);
  assert.match(screen, /feedback = blockedGuess\?\.oneAway \? ONE_AWAY_GUIDANCE : hint/);
  assert.doesNotMatch(screen, /blockedGuess !== null \? ONE_AWAY_GUIDANCE/);
});
