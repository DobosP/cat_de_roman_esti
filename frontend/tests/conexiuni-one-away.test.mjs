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
  assert.match(screen, /Aproape: 3 din 4\. Schimbă o piesă\./);
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
    /err\.status === 409\) \{\s*if \(!fresh\?\.won && !fresh\?\.lost\) \{\s*setSelected\(guess\);\s*setBlockedGuess\(\{ key: guessKey, oneAway: false \}\);/,
  );
  assert.match(
    screen,
    /if \(res\.correct\) \{[\s\S]{0,180}setSelected\(\[\]\);\s*setBlockedGuess\(null\);/,
  );
  assert.match(
    screen,
    /const clearSelection = useCallback\([\s\S]{0,180}setBlockedGuess\(null\)/,
  );
  assert.match(
    screen,
    /if \(changed\) \{\s*sound\.playSelect\(\);\s*setBlockedGuess\(null\);\s*setHint\(null\);/,
  );
});

test("Conexiuni never turns a generic duplicate rejection into one-away feedback", () => {
  assert.match(screen, /setBlockedGuess\(\{ key: guessKey, oneAway: false \}\)/);
  assert.match(screen, /feedback = blockedGuess\?\.oneAway \? ONE_AWAY_GUIDANCE : hint/);
  assert.doesNotMatch(screen, /blockedGuess !== null \? ONE_AWAY_GUIDANCE/);
});

test("mobile recovery and clues stay in the sticky action channel above the board", () => {
  const coach = screen.indexOf('className="connections-coach-stack"');
  const guidance = screen.indexOf('className="card connections-feedback col"');
  const board = screen.indexOf('className="connections-grid"');
  assert.ok(coach > 0 && guidance > coach && board > guidance);
  assert.match(screen, /state\?\.clues\.map\(\(clue\) => clue\.message\)/);
  assert.match(
    screen,
    /const res = await conexiuniApi\.clue\(state\.game_id\);[\s\S]{0,180}applyAuthoritativeState\(res\)/,
  );
  assert.doesNotMatch(screen, /setHint\(res\.clue\.message\)/);
  assert.doesNotMatch(screen, /onToast\("Indiciu deblocat\./);
  assert.doesNotMatch(screen, /onToast\("Aproape! 3 din 4\.|onToast\("Nu e grupul/);
  assert.match(screen, /refreshAuthoritativeState\(state\.game_id\)/);
  assert.match(screen, /err\.status === 400 \|\| err\.status === 409/);
});

test("authoritative refresh retires invisible selections without duplicating terminal errors", () => {
  assert.match(screen, /fresh\.solved\.flatMap\(\(group\) => group\.tiles\.map/);
  assert.match(screen, /current\.filter\(\(id\) => available\.has\(id\)\)/);
  assert.match(
    screen,
    /setState\(fresh\);[\s\S]{0,240}setBlockedGuess\(null\);\s*setHint\(null\);/,
  );
  assert.match(
    screen,
    /else if \(!fresh\?\.won && !fresh\?\.lost\) \{\s*onToast\(message, "error"\);/,
  );
  assert.match(screen, /if \(!fresh\?\.won && !fresh\?\.lost\) \{\s*onToast\(/);
});

test("the sticky coach keeps the bounded mistake budget visible without membership", () => {
  assert.match(screen, /className="connections-lives"/);
  assert.match(screen, /role="img"/);
  assert.match(
    screen,
    /aria-label=\{`\$\{state\.lives\} \$\{state\.lives === 1 \? "greșeală disponibilă" : "greșeli disponibile"\}`\}/,
  );
  assert.match(screen, /Array\.from\(\{ length: 4 \}/);
  const clues = screen.match(/const clueMessages = useMemo\([\s\S]*?\n {2}\);/);
  assert.ok(clues);
  assert.doesNotMatch(clues[0], /tiles|solution|\.id/);
  assert.match(screen, /key="connections-feedback"/);
  assert.match(screen, /\{feedback && \([\s\S]*?role="status"/);
  assert.match(screen, /clueMessages\.map\(\(message\) => \([\s\S]*?role="status"/);
});
