import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const screen = readFileSync(
  new URL("../src/screens/Alchimie.tsx", import.meta.url),
  "utf8",
);
function callback(name) {
  const start = screen.indexOf(`  const ${name} = useCallback`);
  assert.notEqual(start, -1, `${name} exists`);
  const end = screen.indexOf("\n  const ", start + 1);
  assert.ok(end > start, `${name} has a following declaration`);
  return screen.slice(start, end);
}

const combine = callback("doCombine");
const toggle = callback("toggle");

test("empty reaction recovery uses an unordered pair key", () => {
  assert.match(
    screen,
    /function pairKey[\s\S]*?ids\.length === 2[\s\S]*?JSON\.stringify\(\[\.\.\.ids\]\.sort\(\)\)/,
  );
  assert.match(
    combine,
    /pairKey\(pair\) === emptyPairKey[\s\S]*?return;/,
  );
});

test("an authoritative empty response retains one ingredient for the next tap", () => {
  assert.match(
    combine,
    /const recoverableEmpty = res\.discovered\.length === 0 && !res\.won/,
  );
  assert.match(
    combine,
    /if \(recoverableEmpty\) \{[\s\S]*?setSelected\(\[a\]\);[\s\S]*?setEmptyPairKey\(pairKey\(\[a, b\]\)\);/,
  );
  assert.match(
    combine,
    /recoverableEmpty && !res\.already_tried[\s\S]*?Primul cuvânt rămâne ales\. Atinge alt partener\./,
  );
  assert.match(
    combine,
    /recoverableEmpty && res\.hint_available[\s\S]*?Apasă „Indiciu” dacă te-ai blocat\./,
  );

  const rejected = combine.slice(combine.indexOf("} catch {"));
  assert.match(rejected, /await reconcileAction\(ticket\)/);
  assert.doesNotMatch(rejected, /setSelected|setEmptyPairKey/);
});

test("a second distinct ingredient submits through the single owned action path", () => {
  assert.match(toggle, /startInFlight\.current \|\| actionsLocked \|\| won \|\| actionOwner\.hasPending\(\)/);
  assert.match(toggle, /void doCombine\(\[selected\[0\], id\]\)/);
  assert.doesNotMatch(toggle, /alchimieApi\.combine/);
  assert.match(combine, /startInFlight\.current \|\|/);
  assert.match(combine, /actionsLocked \|\|[\s\S]*?pair\.length !== 2[\s\S]*?pair\[0\] === pair\[1\]/);
  assert.match(combine, /pair\.some\(\(id\) => !state\.inventory\.some\(\(item\) => item\.id === id && !item\.depleted\)\)/);
  assert.ok(
    combine.indexOf("const ticket = beginAction(state)") <
      combine.indexOf("alchimieApi.combine"),
  );
  assert.match(combine, /const \[a, b\] = pair/);
  assert.match(combine, /if \(!ticket\) return/);
  assert.match(combine, /if \(!mayAdoptAction\(ticket\)\) return/);
  assert.match(combine, /res\.game_id !== ticket\.gameId[\s\S]*?await reconcileAction\(ticket\)/);
  assert.match(
    combine,
    /finally \{[\s\S]*?if \(actionOwner\.finish\(ticket\)\) setBusy\(false\)/,
  );
});

test("a sole useful discovery becomes the next anchor without another selection", () => {
  assert.match(combine, /const usableDiscoveries = res\.inventory\.filter\(\(item\) =>\s*item\.useful && !item\.depleted && res\.discovered\.some\(\(fresh\) => fresh\.id === item\.id\)/);
  assert.match(combine, /setSelected\(!res\.won && usableDiscoveries\.length === 1 \? \[usableDiscoveries\[0\]\.id\] : \[\]\)/);
  assert.match(combine, /setEmptyPairKey\(null\)/);
});

test("cancelling the anchor or changing games clears the immediate retry block", () => {
  assert.match(toggle, /selected\[0\] === id[\s\S]*?clearSelection\(\)/);
  const clear = callback("clearSelection");
  assert.match(clear, /startInFlight\.current \|\| actionsLocked \|\| actionOwner\.hasPending\(\)/);
  assert.match(clear, /setSelected\(\[\]\)/);
  assert.match(clear, /setEmptyPairKey\(null\)/);

  for (const name of ["start", "newGame", "applyAuthoritativeState"]) {
    assert.match(callback(name), /setEmptyPairKey\(null\)/);
  }
  for (const name of ["doReset", "doHint"]) {
    assert.match(callback(name), /applyAuthoritativeState\(fresh\)/);
  }
});

test("Escape cancels without a global Enter submit or a separate combine button", () => {
  const keyboardStart = screen.indexOf("const onKey = (event: KeyboardEvent)");
  const keyboardEnd = screen.indexOf('window.addEventListener("keydown", onKey)', keyboardStart);
  assert.ok(keyboardStart >= 0 && keyboardEnd > keyboardStart);
  const keyboard = screen.slice(keyboardStart, keyboardEnd);
  assert.match(keyboard, /startInFlight\.current/);
  assert.match(keyboard, /event\.defaultPrevented/);
  assert.match(keyboard, /event\.key === "Escape"/);
  assert.match(keyboard, /clearSelection\(\)/);
  assert.doesNotMatch(keyboard, /doCombine|"Enter"/);
  assert.doesNotMatch(screen, /onClick=\{doCombine\}|aria-label="Combină cele două concepte selectate"|>\s*Golește\s*</);
});

test("removing the anchor preserves keyboard focus and a 44px touch target", () => {
  assert.match(
    screen,
    /<Slot[\s\S]{0,160}item=\{selectedItems\[0\]\}[\s\S]{0,160}onRemove=\{removeFromBench\}/,
  );
  assert.match(
    callback("removeFromBench"),
    /requestAnimationFrame\(\(\) => \{[\s\S]*?const button = inventoryButtons\.current\.get\(id\);[\s\S]*?if \(button && !button\.disabled\) button\.focus\(\);[\s\S]*?else inventoryPanel\.current\?\.focus\(\);/,
  );
  assert.match(screen, /<section ref=\{inventoryPanel\} tabIndex=\{-1\}[^>]*aria-label="Inventar"/);
  assert.match(
    screen,
    /ref=\{\(node\) => \{[\s\S]{0,180}inventoryButtons\.current\.set\(item\.id, node\)/,
  );

  const slot = screen.slice(screen.indexOf("function Slot"));
  assert.match(slot, /if \(!item\) return null/);
  assert.match(slot, /<button[\s\S]*?type="button"/);
  assert.match(slot, /onClick=\{\(\) => onRemove\(item\.id\)\}/);
  assert.match(slot, /aria-label=\{`Scoate \$\{item\.label\} din alambic`\}/);
  assert.match(slot, /minHeight: 44/);
  assert.match(slot, /<span aria-hidden>×<\/span>/);
});
