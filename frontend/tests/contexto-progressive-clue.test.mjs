import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const screen = readFileSync(
  new URL("../src/screens/CaldRece.tsx", import.meta.url),
  "utf8",
);
const css = readFileSync(
  new URL("../src/styles/arcade.css", import.meta.url),
  "utf8",
);

test("Cald sau Rece labels the next server-authored clue stage", () => {
  assert.match(screen, /const clueActionLabel = state\?\.clue_available/);
  assert.match(screen, /state\.next_clue_kind === "warmer"/);
  assert.match(screen, /\? "Mai cald"\s*: "Indiciu"/);
  assert.match(screen, /`Indiciu în \$\{clueCountdown\}`/);
  assert.match(screen, /Arată un cuvânt sigur mai cald/);
  assert.match(screen, /Nu mai există un indiciu sigur/);
  assert.match(screen, /const res = await contextoApi\.requestClue\(state\.game_id\)/);
  assert.match(screen, /setState\(res\)/);
});

test("compact clue cards keep category and warmer word visible on mobile", () => {
  assert.match(screen, /\(state\?\.clue \|\| state\?\.warm_clue\) && !finished/);
  assert.match(screen, /🧭 Categorie/);
  assert.match(screen, /🔥 Încearcă/);
  assert.match(screen, /\{state\.warm_clue\.label\}/);
  assert.match(screen, /#\{state\.warm_clue\.rank\}/);
  assert.match(screen, /aria-label="Indicii folosite"/);
});

test("the warmer word is a phone-safe fill action", () => {
  assert.match(screen, /className="contexto-warm-clue-button"/);
  assert.match(screen, /aria-label=\{`Pune \$\{state\.warm_clue\.label\} în câmpul de răspuns`\}/);
  assert.match(screen, /setText\(word\)/);
  assert.match(screen, /matchMedia\("\(pointer: fine\)"\)\.matches/);
  assert.match(css, /\.contexto-warm-clue-button \{[\s\S]*?min-height: 44px/);
});

test("guess responses retain progressive clue state from the server", () => {
  const nextKindUpdates = screen.match(/next_clue_kind: res\.next_clue_kind/g) ?? [];
  const warmUpdates = screen.match(/warm_clue: res\.warm_clue \?\? prev\.warm_clue/g) ?? [];
  assert.equal(nextKindUpdates.length, 2);
  assert.equal(warmUpdates.length, 2);
});

test("a rejected stale clue refreshes authoritative availability", () => {
  const start = screen.indexOf("const handleClue = useCallback");
  const end = screen.indexOf("const handleGiveUp = useCallback", start);
  assert.ok(start >= 0 && end > start);
  const clue = screen.slice(start, end);
  // HTTP400 remains covered; every failed action now follows the same owned GET.
  assert.match(clue, /catch \{\s*await reconcileAction\(ticket, state\);/);
  const recoveryStart = screen.indexOf("const reconcileAction = useCallback");
  const recoveryEnd = screen.indexOf("const retryActionSync = useCallback", recoveryStart);
  assert.ok(recoveryStart >= 0 && recoveryEnd > recoveryStart);
  const recovery = screen.slice(recoveryStart, recoveryEnd);
  assert.match(recovery, /recoverOwnedContextoAction\(\s*actionOwner, ticket, contextoApi\.getGame,/);
  assert.match(recovery, /if \(!mayAdoptAction\(ticket\)\) return;/);
  assert.match(recovery, /const fresh = outcome\.state;[\s\S]*?setState\(fresh\);/);
});
