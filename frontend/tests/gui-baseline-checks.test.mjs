import test from "node:test";
import assert from "node:assert/strict";
import * as fs from "node:fs";
import { createHash } from "node:crypto";
import { assertHomeData, assertHomeAliasData, assertAxePages, comparisonOutcomes, captureHomeWitness,
  ORIGINAL_BASELINE_SHA256 } from "../../scripts/gui-baseline-checks.mjs";

// Synthetic DATA controls only. No browser/context capability or passing receipt is manufactured.
const raw = fs.readFileSync(new URL("../../baselines/cat/capture.json", import.meta.url));
assert.equal(createHash("sha256").update(raw).digest("hex"), ORIGINAL_BASELINE_SHA256);
const baseline = JSON.parse(raw), originalHome = baseline.pages[0].axe;
const aliases = [".home-game--alchimie.game-card.card", ".game-card--featured", ".home-game--perechi.game-card.card",
  ".home-game--conexiuni.game-card.card", ".home-game--contexto.game-card.card", ".home-game--lant.game-card.card"];
const names = ["Joacă Alchimie — Combină și descoperă", "Joacă Intrusul — Începe aici", "Joacă Perechi — Potrivește câte două",
  "Joacă Conexiuni — Găsește grupurile", "Joacă Cald sau Rece — Mai cald, mai rece", "Joacă Lanțul Cuvintelor — Leagă conceptele"];
const keys = ["alchimie", "intrusul", "perechi", "conexiuni", "contexto", "lant"];
function aliased() {
  const result = structuredClone(originalHome);
  result[0].targets = aliases.map((value) => [value]); result[1].targets = [[".home-footer"]]; return result;
}
function declaredData() {
  return { cards: names.map((name, index) => ({ key: keys[index], order: index,
    original: originalHome[0].targets[index][0], current: aliases[index], tag: "button", type: "button",
    role_attribute: null, aria_label: name, aria_labelledby: null, aria_hidden: null, disabled: false,
    visible: true, enabled: true, old_current_same: true, order_same: true, computed_name_same: true,
    aria_snapshot: "NON-RELEASE synthetic declaration; not browser evidence" })),
  footer: { tag: "p", text: "Toate cele șase jocuri folosesc aceeași hartă de legături culturale românești.",
    role_attribute: null, aria_label: null, aria_labelledby: null, aria_hidden: null,
    old_current_same: true, text_same: true, aria_snapshot: "NON-RELEASE synthetic footer declaration" } };
}
void test("known Home alias DATA preserves immutable ordered original fields and does not mutate either caller", () => {
  const before = structuredClone(originalHome), next = aliased(), kept = structuredClone(next);
  assert.equal(assertHomeAliasData(before, next), undefined);
  assert.deepEqual(before, originalHome); assert.deepEqual(next, kept);
});
for (const [name, mutate] of [
  ["unknown card selector", (value) => { value[0].targets[0] = [".unreviewed"]; }],
  ["swapped semantic owners", (value) => { [value[0].targets[0], value[0].targets[2]] = [value[0].targets[2], value[0].targets[0]]; }],
  ["additional target", (value) => { value[0].targets.push([".extra"]); }],
  ["missing target", (value) => { value[0].targets.pop(); }],
  ["multi-part shadow target", (value) => { value[0].targets[0].push(".other"); }],
  ["new rule ID", (value) => { value[0].id = "different"; }],
  ["new impact", (value) => { value[0].impact = "critical"; }],
  ["rule order", (value) => { value.reverse(); }],
  ["extra rule", (value) => { value.push({ id: "new", impact: "serious", targets: [] }); }],
  ["unknown footer", (value) => { value[1].targets = [[".other-footer"]]; }],
  ["additional fingerprint field", (value) => { value[0].accepted = true; }],
]) void test("Home alias DATA refuses " + name, () => {
  const value = aliased(); mutate(value); assert.throws(() => assertHomeAliasData(originalHome, value));
});
void test("exact raw route/Axe comparison remains strict and needs no selector reinterpretation", () => {
  const current = structuredClone(baseline.pages);
  assert.equal(assertAxePages(baseline.pages, current, null, null), undefined);
  current[1].axe.push({ id: "new", impact: "critical", targets: [["button"]] });
  assert.throws(() => assertAxePages(baseline.pages, current, null, null));
});
void test("valid declared Home DATA and serialized historical claims cannot authorize live alias comparison", () => {
  const declaration = declaredData(); assert.equal(assertHomeData(declaration), undefined);
  const current = structuredClone(baseline.pages); current[0].axe = aliased();
  for (const value of [declaration, structuredClone(declaration), { passed: true }, null]) {
    assert.throws(() => assertAxePages(baseline.pages, current, value, {}), /Live Home node\/name witness/);
  }
});
for (const [name, mutate] of [
  ["non-native tag", (value) => { value.cards[0].tag = "div"; }],
  ["different role", (value) => { value.cards[0].role_attribute = "link"; }],
  ["different exact name", (value) => { value.cards[0].aria_label += " changed"; }],
  ["external labelledby", (value) => { value.cards[0].aria_labelledby = "other"; }],
  ["hidden card", (value) => { value.cards[0].aria_hidden = "true"; }],
  ["disabled card", (value) => { value.cards[0].disabled = true; }],
  ["invisible card", (value) => { value.cards[0].visible = false; }],
  ["wrong native element join", (value) => { value.cards[0].old_current_same = false; }],
  ["wrong order", (value) => { value.cards[0].order_same = false; }],
  ["name resolver mismatch", (value) => { value.cards[0].computed_name_same = false; }],
  ["missing snapshot", (value) => { value.cards[0].aria_snapshot = ""; }],
  ["missing card", (value) => { value.cards.pop(); }],
  ["different footer text", (value) => { value.footer.text = "different"; }],
  ["different footer node", (value) => { value.footer.old_current_same = false; }],
  ["different footer role", (value) => { value.footer.role_attribute = "status"; }],
]) void test("declared Home DATA refuses " + name + " without granting runtime authority", () => {
  const value = declaredData(); mutate(value); assert.throws(() => assertHomeData(value));
});
void test("forged live context refuses before any browser method or observer runs", async () => {
  let touched = false;
  await assert.rejects(captureHomeWitness({ locator() { touched = true; throw Error("must not run"); } }, {}), /Live identified source\/image context/);
  assert.equal(touched, false);
});
void test("Axe refusal does not hide any of nine exact PNG and four unchanged vitals predicates", () => {
  const current = structuredClone(baseline); current.pages[0].axe = aliased();
  current.vitals[0].median.lcp += Math.max(baseline.vitals[0].median.lcp * .1, 50) + 1;
  current.vitals[1].median.lcp -= Math.max(baseline.vitals[1].median.lcp * .1, 50) + 1;
  const pngs = current.pages.map(() => ({ original: Buffer.from("original"), current: Buffer.from("original") }));
  pngs[2].current = Buffer.from("different");
  const results = comparisonOutcomes(baseline, current, declaredData(), {}, pngs);
  assert.deepEqual(results.map((value) => value.name), ["home-live-semantic-witness", "axe-route-fingerprints",
    ...baseline.pages.map((value) => "png:" + value.route),
    "vitals:/conexiuni:lcp", "vitals:/conexiuni:inp", "vitals:/alchimie?mode=challenges:lcp", "vitals:/alchimie?mode=challenges:inp"]);
  assert.deepEqual(results.filter((value) => value.status === "fail").map((value) => value.name),
    ["home-live-semantic-witness", "axe-route-fingerprints", "png:/perechi", "vitals:/conexiuni:lcp", "vitals:/alchimie?mode=challenges:lcp"]);
  assert.deepEqual(baseline.pages[0].axe, originalHome);
});
for (const [expected, actual, pass] of [[1000, 1100, true], [1000, 1100.01, false], [100, 150, true],
  [100, 150.01, false], [100, 50, true], [100, 49.99, false], [100, null, false], [100, NaN, false], [100, Infinity, false]]) {
  void test("vitals retain absolute max(10%,50ms) predicate for " + String(actual), () => {
    const before = { pages: [], vitals: [{ median: { lcp: expected, inp: 100 } }] };
    const current = { pages: [], vitals: [{ route: "/fixture", median: { lcp: actual, inp: 100 } }] };
    const rows = comparisonOutcomes(before, current, null, null, []);
    assert.equal(rows.find((row) => row.name === "vitals:/fixture:lcp").status, pass ? "pass" : "fail");
  });
}
