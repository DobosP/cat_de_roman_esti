import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const screen = read("../src/screens/Alchimie.tsx");
const guide = read("../src/components/PlayGuide.tsx");

test("Alchimie derives a bounded newest-first journal from server inventory", () => {
  assert.match(screen, /const REACTION_LOG_LIMIT = 12/);
  assert.match(screen, /item\.parents !== null/);
  assert.match(screen, /previous\?\.ingredientKey === ingredientKey/);
  assert.match(screen, /chronological\.slice\(-REACTION_LOG_LIMIT\)\.reverse\(\)/);
  assert.match(screen, /useMemo\(\(\) => buildReactionLog\(inventory\), \[inventory\]\)/);
  assert.doesNotMatch(screen, /useState<Reaction/);
});

test("latest reaction stays visible while older reactions use collapsed disclosure", () => {
  assert.match(screen, /ULTIMA DESCOPERIRE/);
  assert.match(screen, /<details className="alchemy-reaction-log">/);
  assert.match(screen, /Vezi jurnalul \(\{reactionLog\.length\}\)/);
  assert.match(screen, /reactionLog\.slice\(1\)\.map/);
  assert.doesNotMatch(screen, /<details[^>]*\sopen(?:=|\s|>)/);
  assert.match(
    screen,
    /className="chip alchemy-reaction-log-toggle"[\s\S]{0,180}minHeight: 44/,
  );
});

test("journal result controls only fill the bench and keep 44px targets", () => {
  const start = screen.indexOf("function ReactionRow");
  const end = screen.indexOf("function Slot", start);
  assert.notEqual(start, -1);
  assert.notEqual(end, -1);
  const row = screen.slice(start, end);

  assert.match(row, /type="button"/);
  assert.match(row, /const currentItem = inventoryById\.get\(item\.id\)/);
  assert.match(row, /const depleted = currentItem\?\.depleted \?\? true/);
  assert.match(row, /disabled=\{busy \|\| depleted\}/);
  assert.match(row, /aria-label=\{depleted \? `\$\{item\.label\}, pus deoparte` : `Alege \$\{item\.label\}`\}/);
  assert.match(row, /title=\{depleted \? "Pus deoparte" : "Pune în alambic"\}/);
  assert.match(row, /onClick=\{\(\) => onSelect\(item\.id\)\}/);
  assert.match(row, /minHeight: 44/);
  assert.doesNotMatch(row, /doCombine|alchimieApi\.combine/);
  assert.match(screen, /inventoryById=\{inventoryById\}/);
  assert.match(screen, /onSelect=\{toggle\}/);
});

test("accepted empty combines use one persistent feedback path", () => {
  assert.match(
    screen,
    /let feedback = res\.message;[\s\S]*?recoverableEmpty && !res\.already_tried[\s\S]*?feedback \+= " Perechea rămâne în alambic — schimbă un ingredient\.";[\s\S]*?recoverableEmpty && res\.hint_available[\s\S]*?feedback \+= " Apasă „Indiciu” dacă te-ai blocat\.";[\s\S]*?setLastMessage\(feedback\)/,
  );
  const discovered = screen.indexOf("if (res.discovered.length > 0)");
  const empty = screen.indexOf("} else {", discovered);
  const rejected = screen.indexOf("} catch (err)", empty);
  assert.notEqual(discovered, -1);
  assert.notEqual(empty, -1);
  assert.notEqual(rejected, -1);
  const emptyBranch = screen.slice(empty, rejected);
  assert.doesNotMatch(emptyBranch, /onToast/);
});

test("combine feedback has one nonterminal and one terminal announcement owner", () => {
  const nextMove = screen.slice(
    screen.indexOf("<NextMove"),
    screen.indexOf("/>", screen.indexOf("<NextMove")),
  );
  assert.match(nextMove, /announce=\{false\}/);
  assert.match(guide, /role=\{announce \? "status" : undefined\}/);
  assert.match(screen, /\{lastMessage && !won && \(/);
  assert.match(
    screen,
    /role="status"\s+aria-live="polite"\s+aria-atomic="true"/,
  );

  const result = screen.match(/<ResultCard[\s\S]*?<\/ResultCard>/);
  assert.ok(result);
  assert.match(result[0], /winningReaction\.parents\[0\]\.label/);
  assert.match(result[0], /winningReaction\.parents\[1\]\.label/);
  assert.match(result[0], /winningReaction\.results\.map/);
});
