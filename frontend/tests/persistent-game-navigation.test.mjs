import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const app = read("../src/App.tsx");
const shell = read("../src/components/GameShell.tsx");
const conexiuni = read("../src/screens/Conexiuni.tsx");
const activeGame = read("../src/hooks/useActiveGame.ts");
const css = read("../src/styles/arcade.css");

test("a live Conexiuni exit forgets its pointer while a terminal score owns cleanup", () => {
  assert.match(app, /navigate\("\/", \{ replace: true \}\)/);

  const exit = conexiuni.match(
    /const handleExit = useCallback\(\(\) => \{[\s\S]*?\n {2}\}, \[active, finished, onExit\]\);/,
  );
  assert.ok(exit);
  assert.match(exit[0], /if \(!finished\) active\.forget\(\);[\s\S]*?onExit\(\);/);
  assert.doesNotMatch(exit[0], /localStorage\.(?:clear|removeItem)/);
  assert.equal((conexiuni.match(/onExit=\{handleExit\}/g) ?? []).length, 3);
  assert.match(activeGame, /const key = `\$\{PREFIX\}\$\{game\}`/);
  assert.match(activeGame, /forget: \(\) => \{[\s\S]*?localStorage\.removeItem\(key\)/);
  assert.doesNotMatch(activeGame, /localStorage\.clear\(\)/);
});

test("Escape still clears a Conexiuni selection", () => {
  assert.match(
    conexiuni,
    /e\.key === "Escape" \|\| e\.key === "Backspace"[\s\S]*?clearSelection\(\)/,
  );
});

test("narrow screens keep exit visible and offset every second sticky game surface", () => {
  assert.match(shell, /aria-label=\{busy \? "Se pregătește jocul" : "Ieși la lista de jocuri"\}/);
  assert.match(shell, /\{busy \? "Se pregătește…" : "Ieși"\}/);
  assert.match(
    css,
    /@media \(max-width: 640px\)[\s\S]*?--game-shell-sticky-top: env\(safe-area-inset-top\);[\s\S]*?--game-shell-sticky-offset: calc\(env\(safe-area-inset-top\) \+ 60px\);[\s\S]*?\.game-shell-header \{[\s\S]*?position: sticky;[\s\S]*?top: var\(--game-shell-sticky-top\);[\s\S]*?z-index: 12;/,
  );
  for (const selector of [
    "connections-coach-stack",
    "contexto-sticky-controls",
    "alchemy-bench",
    "word-hop-input",
  ]) {
    assert.match(
      css,
      new RegExp(
        "\\." + selector + " \\{[\\s\\S]*?top: var\\(--game-shell-sticky-offset\\);",
      ),
    );
  }
  assert.doesNotMatch(css, /\.game-shell-title \{\s*display: none/);
  assert.match(
    css,
    /@media \(max-width: 360px\) \{[\s\S]*?\.game-shell-title \{[\s\S]*?clip: rect\(0 0 0 0\)/,
  );
});

test("only the compact Conexiuni coach sticks; feedback remains before the board", () => {
  const coach = conexiuni.indexOf('className="connections-coach-stack"');
  const coachEnd = conexiuni.indexOf("\n          </div>\n        )}", coach);
  const feedback = conexiuni.indexOf('className="card connections-feedback col"');
  const board = conexiuni.indexOf('className="connections-grid"');
  assert.ok(coach > 0 && coachEnd > coach && feedback > coachEnd && board > feedback);
});

test("Conexiuni explains every difficulty with visible plain-language copy", () => {
  assert.match(
    conexiuni,
    /\{ id: "usor", label: DIFF_LABEL\.usor, hint: "grupuri clare" \}/,
  );
  assert.match(
    conexiuni,
    /\{ id: "normal", label: DIFF_LABEL\.normal, hint: "mix echilibrat" \}/,
  );
  assert.match(
    conexiuni,
    /\{ id: "greu", label: DIFF_LABEL\.greu, hint: "legături subtile" \}/,
  );
  assert.match(conexiuni, /<DifficultyPicker\s+options=\{DIFFICULTY_OPTIONS\}/);
});
