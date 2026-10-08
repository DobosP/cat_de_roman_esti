import test from "node:test";
import assert from "node:assert/strict";
import { assertExplicitCss, cssLength, normalizeExplicitCss } from "../src/components/cssUnits.ts";

test("CSSOM declarations refuse numeric lengths including zero and negative offsets", () => {
  for (const [property, value] of [["width", 0], ["minHeight", 44], ["marginTop", -8], ["gap", 12], ["flexBasis", 0]]) {
    assert.throws(() => assertExplicitCss({ [property]: value }), /requires explicit units/);
  }
  assert.deepEqual(normalizeExplicitCss({ width: "0px", minHeight: "44px", marginTop: "-8px", gap: "12px" }),
    { width: "0px", minHeight: "44px", marginTop: "-8px", gap: "12px" });
});
test("all unitless numbers survive the original SDK without accidental px", () => {
  assert.deepEqual(normalizeExplicitCss({ columnCount: 2, gridRow: 2, WebkitLineClamp: 3, opacity: .5, fontWeight: 700, lineHeight: 1.4, "--ordinal": 2 }),
    { columnCount: "2", gridRow: "2", WebkitLineClamp: "3", opacity: "0.5", fontWeight: "700", lineHeight: "1.4", "--ordinal": "2" });
});
test("CSSOM bags refuse primitives, arrays, class instances and nonfinite values", () => {
  class Bag { color = "red"; }
  for (const value of [42, "abc", true, null, [], new Date(0), new Bag()]) assert.throws(() => assertExplicitCss(value), /plain bag/);
  for (const value of [NaN, Infinity, -Infinity]) assert.throws(() => assertExplicitCss({ opacity: value }), /Nonfinite/);
  for (const value of [{}, false, null]) assert.throws(() => assertExplicitCss({ color: value }), /Unsupported/);
});
test("explicit length conversion preserves valid strings and rejects nonfinite measurements", () => {
  assert.equal(cssLength(0), "0px"); assert.equal(cssLength(-2.5), "-2.5px");
  assert.equal(cssLength("50%"), "50%"); assert.equal(cssLength("var(--height)"), "var(--height)");
  assert.equal(cssLength(undefined), undefined); assert.throws(() => cssLength(Infinity), /finite/);
  assert.deepEqual(normalizeExplicitCss(Object.assign(Object.create(null), { padding: "12px" })), { padding: "12px" });
});
