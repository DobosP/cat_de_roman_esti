import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const screen = readFileSync(
  new URL("../src/screens/Alchimie.tsx", import.meta.url),
  "utf8",
);
const combineStart = screen.indexOf("const doCombine = useCallback");
const combineEnd = screen.indexOf("const doReset = useCallback", combineStart);
const combine = screen.slice(combineStart, combineEnd);

test("empty reaction recovery uses an unordered pair key", () => {
  assert.match(
    screen,
    /function pairKey[\s\S]*?ids\.length === 2[\s\S]*?JSON\.stringify\(\[\.\.\.ids\]\.sort\(\)\)/,
  );
  assert.match(
    screen,
    /selectedPairKey !== null && selectedPairKey === emptyPairKey/,
  );
});

test("only authoritative nonterminal empty responses retain the submitted pair", () => {
  assert.match(
    combine,
    /const recoverableEmpty = res\.discovered\.length === 0 && !res\.won/,
  );
  assert.match(
    combine,
    /if \(recoverableEmpty\) \{[\s\S]*?setSelected\(\[a, b\]\);[\s\S]*?setEmptyPairKey\(pairKey\(\[a, b\]\)\);[\s\S]*?setEmptyRecoveryActive\(true\);[\s\S]*?\} else \{[\s\S]*?setSelected\(\[\]\);[\s\S]*?setEmptyPairKey\(null\);[\s\S]*?setEmptyRecoveryActive\(false\)/,
  );
  assert.match(
    combine,
    /recoverableEmpty && !res\.already_tried[\s\S]*?Perechea rămâne în alambic — schimbă un ingredient\./,
  );
  assert.match(
    combine,
    /recoverableEmpty && res\.hint_available[\s\S]*?Apasă „Indiciu” dacă te-ai blocat\./,
  );

  const rejected = combine.slice(combine.indexOf("} catch (err)"));
  assert.doesNotMatch(rejected, /setSelected|setEmptyPairKey/);
});

test("button, keyboard, and action guard block an unchanged or duplicate submit", () => {
  assert.match(combine, /isEmptyRetry \|\|[\s\S]*?combineInFlight\.current/);
  assert.ok(
    combine.indexOf("combineInFlight.current = true") <
      combine.indexOf("alchimieApi.combine"),
  );
  assert.match(
    combine,
    /finally \{[\s\S]*?combineInFlight\.current = false;[\s\S]*?setBusy\(false\)/,
  );
  assert.match(
    screen,
    /e\.key === "Enter" &&[\s\S]{0,180}!busy &&[\s\S]{0,80}!isEmptyRetry/,
  );
  assert.match(
    screen,
    /disabled=\{busy \|\| selected\.length !== 2 \|\| isEmptyRetry\}/,
  );
});

test("changing or clearing the bench dismisses only the immediate retry block", () => {
  const toggle = screen.slice(
    screen.indexOf("const toggle = useCallback"),
    screen.indexOf("const doCombine = useCallback"),
  );
  assert.match(toggle, /setEmptyPairKey\(null\)[\s\S]*?setSelected/);
  assert.match(
    toggle,
    /if \(emptyRecoveryActive\)[\s\S]*?const nextSelectionCount[\s\S]*?selected\.length - 1[\s\S]*?Math\.min\(selected\.length \+ 1, 2\)/,
  );
  assert.match(
    toggle,
    /nextSelectionCount === 0[\s\S]*?Alambicul este gol\.[\s\S]*?nextSelectionCount === 1[\s\S]*?Un concept este ales\.[\s\S]*?Perechea nouă este gata\. Apasă Combină\./,
  );
  assert.match(
    toggle,
    /const clearSelection[\s\S]*?Alambicul este gol\.[\s\S]*?setSelected\(\[\]\);[\s\S]*?setEmptyPairKey\(null\)/,
  );

  for (const anchor of [
    "const start = useCallback",
    "const doReset = useCallback",
    "const newGame = useCallback",
    "const doHint = useCallback",
  ]) {
    const start = screen.indexOf(anchor);
    assert.notEqual(start, -1, `${anchor} exists`);
    assert.match(screen.slice(start, start + 1200), /setEmptyPairKey\(null\)/);
    assert.match(
      screen.slice(start, start + 1200),
      /setEmptyRecoveryActive\(false\)/,
    );
  }
  assert.match(
    screen.slice(screen.indexOf("const s = await alchimieApi.get"), screen.indexOf("const start = useCallback")),
    /setEmptyPairKey\(null\)/,
  );
  assert.match(
    screen.slice(screen.indexOf("const s = await alchimieApi.get"), screen.indexOf("const start = useCallback")),
    /setEmptyRecoveryActive\(false\)/,
  );
});

test("the guide explains recovery and either occupied slot can be removed", () => {
  assert.match(screen, /isEmptyRetry[\s\S]{0,100}\? "Schimbă un ingredient"/);
  assert.match(screen, /Perechea aceasta nu a descoperit nimic\./);
  assert.match(screen, /ready=\{selected\.length === 2 && !isEmptyRetry\}/);
  assert.match(
    screen,
    /<Slot[\s\S]{0,160}item=\{selectedItems\[0\]\}[\s\S]{0,160}onRemove=\{removeFromBench\}/,
  );
  assert.match(
    screen,
    /<Slot[\s\S]{0,160}item=\{selectedItems\[1\]\}[\s\S]{0,160}onRemove=\{removeFromBench\}/,
  );
  assert.match(
    screen,
    /const removeFromBench[\s\S]*?requestAnimationFrame\(\(\) => inventoryButtons\.current\.get\(id\)\?\.focus\(\)\)/,
  );
  assert.match(
    screen,
    /ref=\{\(node\) => \{[\s\S]{0,180}inventoryButtons\.current\.set\(item\.id, node\)/,
  );

  const slot = screen.slice(screen.indexOf("function Slot"));
  assert.match(slot, /if \(!item\)[\s\S]*?<span/);
  assert.match(slot, /<button[\s\S]*?type="button"/);
  assert.match(slot, /onClick=\{\(\) => onRemove\(item\.id\)\}/);
  assert.match(slot, /aria-label=\{`Scoate \$\{item\.label\} din alambic`\}/);
  assert.match(slot, /minHeight: 44/);
  assert.match(slot, /<span aria-hidden>×<\/span>/);
});
