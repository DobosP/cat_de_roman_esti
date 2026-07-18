import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const guide = read("../src/components/PlayGuide.tsx");
const intro = read("../src/components/GameIntro.tsx");
const css = read("../src/styles/arcade.css");
const alchimie = read("../src/screens/Alchimie.tsx");
const caldRece = read("../src/screens/CaldRece.tsx");
const lant = read("../src/screens/Lant.tsx");
const conexiuni = read("../src/screens/Conexiuni.tsx");

test("all games teach the loop with a semantic three-step guide and start on easy", () => {
  assert.match(guide, /<ol className="play-guide"/);
  assert.match(guide, /<li className="play-guide-step"/);
  assert.match(intro, /steps\?: PlayGuideStep\[\]/);
  assert.match(intro, /<PlayGuide steps=\{steps\}/);

  for (const screen of [alchimie, caldRece, lant, conexiuni]) {
    assert.match(screen, /steps=\{\[/);
    assert.match(screen, /useState<Difficulty>\("usor"\)/);
    assert.match(screen, /<NextMove/);
  }
});

test("mobile layout keeps status and category rails compact with 44px targets", () => {
  assert.match(css, /@media \(pointer: coarse\)[\s\S]*?\.roedu-btn,[\s\S]*?min-height: 44px/);
  assert.match(css, /@media \(pointer: coarse\)[\s\S]*?\.chip \{[\s\S]*?min-height: 44px/);
  assert.match(css, /\.hud \{[\s\S]*?overflow-x: auto/);
  assert.match(css, /\.category-picker-options \{[\s\S]*?flex-wrap: nowrap;[\s\S]*?overflow-x: auto/);
  assert.match(css, /\.alchemy-bench \{[\s\S]*?position: sticky/);
  assert.match(alchimie, /className="alchemy-slot-label"/);
  assert.match(css, /\.alchemy-slot-label \{[\s\S]*?text-overflow: ellipsis/);
  assert.match(
    css,
    /\.alchemy-bench > \.row:first-child \{[\s\S]*?grid-template-columns: minmax\(0, 1fr\) auto minmax\(0, 1fr\)/,
  );
  assert.match(css, /\.connections-coach-stack \{[\s\S]*?position: sticky/);
  assert.match(conexiuni, /className="connections-coach-stack"[\s\S]*?className="card connections-feedback col"/);
});

test("Romanian labels wrap on a responsive Connections board and long paths scroll", () => {
  assert.doesNotMatch(conexiuni, /gridTemplateColumns/);
  assert.match(css, /\.connections-grid \{\s*grid-template-columns: repeat\(4, minmax\(0, 1fr\)\)/);
  assert.match(css, /@media \(max-width: 480px\)[\s\S]*?repeat\(2, minmax\(0, 1fr\)\)/);
  assert.match(css, /\.connection-tile \{[\s\S]*?overflow-wrap: anywhere/);
  assert.match(lant, /className="row wrap breadcrumb-trail"/);
  assert.match(css, /\.breadcrumb-trail \{[\s\S]*?overflow-x: auto/);
  assert.match(css, /\.lant-choice-grid \{[\s\S]*?repeat\(3, minmax\(0, 1fr\)\)/);
  assert.match(
    css,
    /@media \(max-width: 480px\)[\s\S]*?\.lant-choice-grid \{[\s\S]*?repeat\(2, minmax\(0, 1fr\)\)/,
  );
  assert.match(
    css,
    /@media \(max-width: 480px\)[\s\S]*?\.lant-choice-grid > \.lant-choice:last-child:nth-child\(odd\)[\s\S]*?grid-column: 1 \/ -1/,
  );
  assert.match(css, /\.lant-choice \{[\s\S]*?min-height: 58px/);
  assert.match(css, /\.lant-choice span \{[\s\S]*?font-size: 0\.75rem/);
});

test("global shortcuts ignore focused controls instead of double-submitting", () => {
  const selector = /target\?\.closest\(\s*'button, a, input, textarea, select, \[role="button"\], \[contenteditable="true"\]'/;
  for (const screen of [alchimie, lant, conexiuni]) {
    assert.match(screen, /e\.defaultPrevented/);
    assert.match(screen, selector);
  }
  for (const screen of [alchimie, conexiuni]) {
    assert.match(screen, /e\.key === "Enter" &&\s*target\?\.closest/);
  }
});

test("touch users get visible rank meaning and important feedback is announced", () => {
  assert.match(caldRece, /Număr mai mic = mai aproape · #1 = răspunsul/);
  assert.match(alchimie, /lastMessage[\s\S]*?role="status"[\s\S]*?aria-live="polite"/);
  assert.match(
    lant,
    /hint && \(hint\.stage \|\| hint\.hint\)[\s\S]*?role="status"[\s\S]*?aria-live="polite"/,
  );
  assert.match(conexiuni, /state\?\.clues\.map\(\(clue\) => clue\.message\)/);
  assert.match(conexiuni, /className="card connections-feedback col"/);
  assert.match(conexiuni, /role="status"\s*aria-live="polite"/);
});
