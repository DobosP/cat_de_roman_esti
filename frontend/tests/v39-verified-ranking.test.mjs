import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const read = (path) => readFileSync(new URL(path, import.meta.url), "utf8");
const authApi = read("../src/api/auth.ts");
const ranking = read("../src/screens/Ranking.tsx");
const account = read("../src/components/AccountBar.tsx");
const sync = read("../src/scoreSync.ts");

test("tied rows identify the requester explicitly and keep an off-list self card", () => {
  assert.match(authApi, /is_me: boolean/);
  assert.match(ranking, /row\.is_me \? " rank-row--me"/);
  assert.doesNotMatch(ranking, /meRank === row\.rank/);
  assert.match(ranking, /data\?\.me && !loading && !error && !meIsVisible/);
  assert.match(ranking, /Locul tău: #\{data\.me\.rank\}/);
});

test("ranking copy describes verified records rather than knowledge or fun", () => {
  assert.match(ranking, /Recorduri verificate de joc · maximum 1000 de puncte/);
  assert.doesNotMatch(ranking, /scor de (?:cunoaștere|distracție)/i);
  assert.match(ranking, /activează clasamentul din meniul profilului/);
});

test("public visibility needs an explicit nickname and private sync stays private", () => {
  assert.match(account, /const privateLabel = user\.display_name \|\| user\.name \|\| "Cont"/);
  assert.match(account, /className="account-name">\{privateLabel\}/);
  assert.match(account, /Numele afișat în clasament:", privateLabel/);
  assert.match(account, /!user\.show_on_ranking && !user\.display_name\.trim\(\)/);
  assert.match(account, /Alege o poreclă pentru clasament/);
  assert.match(account, /display_name: next\.trim\(\), show_on_ranking: true/);
  assert.match(sync, /NEVER feed the public ranking/);
});
