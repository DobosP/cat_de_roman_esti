import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const intrusul = read("../src/screens/Intrusul.tsx");
const perechi = read("../src/screens/Perechi.tsx");
const resultCard = read("../src/components/ResultCard.tsx");

test("valid terminal resume states are adopted instead of discarded", () => {
  assert.match(
    intrusul,
    /const fresh = await intrusulApi\.get\(gameId\);\s*setState\(fresh\)/,
  );
  assert.match(
    perechi,
    /const fresh = await perechiApi\.get\(gameId\);\s*setState\(fresh\)/,
  );
  for (const screen of [intrusul, perechi]) {
    assert.doesNotMatch(
      screen,
      /if \(fresh\.won \|\| fresh\.lost\) \{\s*active\.forget\(\);\s*return/,
    );
  }
});

test("every V38 mutation failure reconciles authoritative state", () => {
  assert.match(intrusul, /catch \{\s*const fresh = await reconcile\(state, "guess"\)/);
  assert.match(intrusul, /catch \{\s*const fresh = await reconcile\(state, "hint"\)/);
  assert.match(perechi, /catch \{\s*const fresh = await reconcile\(state, "match"\)/);
  assert.match(perechi, /catch \{\s*const fresh = await reconcile\(state, "hint"\)/);
  for (const screen of [intrusul, perechi]) {
    assert.match(screen, /recoverAuthoritative\(\(\) => [a-z]+Api\.get\(previous\.game_id\)\)/);
    assert.match(screen, /if \(fresh\.won \|\| fresh\.lost\) \{\s*setFeedback\(null\)/);
    assert.match(screen, /Jocul rămâne salvat; încearcă din nou/);
  }
});

test("tile mutations and hints share one synchronous flight lock", () => {
  for (const screen of [intrusul, perechi]) {
    assert.equal((screen.match(/acquireFlight\(actionInFlight\)/g) ?? []).length, 2);
    assert.equal((screen.match(/releaseFlight\(actionInFlight\)/g) ?? []).length, 2);
  }
});

test("create and replay are single-flight with visible result busy state", () => {
  for (const screen of [intrusul, perechi]) {
    assert.match(screen, /const startInFlight = useRef\(false\)/);
    assert.match(screen, /if \(!acquireFlight\(startInFlight\)\) return/);
    assert.match(screen, /releaseFlight\(startInFlight\)/);
    assert.match(screen, /actionsBusy=\{loading\}/);
    assert.match(screen, /const exitSafely = useCallback/);
  }
  assert.match(resultCard, /actionsBusy = false/);
  assert.match(resultCard, /disabled=\{actionsBusy\}/);
  assert.match(resultCard, /actionsBusy \? "Se pregătește…" : replayLabel/);
});

test("Intrusul exposes the hint unlock rule to touch users", () => {
  assert.match(intrusul, /💡 Indiciu după 1 greșeală/);
});
