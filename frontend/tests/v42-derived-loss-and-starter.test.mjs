import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const intrusul = read("../src/screens/Intrusul.tsx");
const perechi = read("../src/screens/Perechi.tsx");

const STARTER_LINE =
  "Primele runde sunt mai blânde. Câștigă una și deblochezi tot catalogul.";

test("Intrusul and Perechi show the starter-shelf hint only pre-graduation", () => {
  for (const source of [intrusul, perechi]) {
    assert.match(
      source,
      /const starterVisible = useMemo\(\(\) => needsDerivedStarter\(GAME_KEY\), \[state\]\)/,
    );
    assert.match(source, /\{starterVisible && \(/);
    assert.match(source, new RegExp(STARTER_LINE.replace(/[.]/g, "\\.")));
    // The hint lives inside the pre-game GameIntro description, not the finished state.
    const introBlock = source.slice(
      source.indexOf("if (!state) {"),
      source.indexOf("const wrong = new Set") > -1
        ? source.indexOf("const wrong = new Set")
        : source.indexOf("const hintIds = new Set"),
    );
    assert.match(introBlock, new RegExp(STARTER_LINE.replace(/[.]/g, "\\.")));
  }
});

test("Intrusul loss reveal names the intruder and the group without leaking pre-terminal", () => {
  assert.match(
    intrusul,
    /Intrusul era: \{state\.solution\.intruder\.label\}\.\s*<\/strong>/,
  );
  assert.match(
    intrusul,
    /Grupul: <strong>\{state\.solution\.group\.label\}<\/strong>\./,
  );
  // Guarded behind the same finished && state.solution gate as the win reveal.
  assert.match(intrusul, /finished && state\.solution && \(/);
  assert.match(intrusul, /\{state\.won \? \(/);
});

test("Perechi loss reveal states earned progress out of four using session-known solved_count", () => {
  assert.match(
    perechi,
    /\{!state\.won && \(\s*<p style=\{\{ margin: "0 0 2px" \}\}>\s*Ai găsit \{state\.solved_count\} din 4 perechi\.\s*<\/p>\s*\)\}/,
  );
  assert.match(perechi, /finished && state\.solution && \(/);
});
