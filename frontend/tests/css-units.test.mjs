import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import ts from "typescript";

const source = readFileSync(new URL("../src/components/cssUnits.ts", import.meta.url), "utf8");
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2021 },
}).outputText;
const { assertExplicitCss, normalizeExplicitCss, cssLength } = await import(
  `data:text/javascript;base64,${Buffer.from(compiled).toString("base64")}`
);

test("an absent CSS bag stays absent and an empty bag stays empty", () => {
  assert.equal(assertExplicitCss(undefined), undefined);
  assert.equal(normalizeExplicitCss(undefined), undefined);
  assert.deepEqual(normalizeExplicitCss({}), {});
});

test("React unitless columnCount uses a string before the preserved SDK hook", () => {
  assert.equal(assertExplicitCss({ columnCount: 2 }), undefined);
  assert.deepEqual(normalizeExplicitCss({ columnCount: 2 }), { columnCount: "2" });
});

test("finite unitless and custom numbers serialize without implicit px", () => {
  assert.deepEqual(normalizeExplicitCss({
    opacity: 0.55, fontWeight: 600, zIndex: 0, lineHeight: 1.15,
    WebKitBoxFlexGroup: 2, "--cue-count": 2, "--cue-offset": -2,
  }), {
    opacity: "0.55", fontWeight: "600", zIndex: "0", lineHeight: "1.15",
    WebKitBoxFlexGroup: "2", "--cue-count": "2", "--cue-offset": "-2",
  });
});

test("dimensional numbers require explicit units, including zero and negatives", () => {
  for (const value of [0, -0, 12, -2]) {
    for (const validate of [assertExplicitCss, normalizeExplicitCss]) {
      assert.throws(() => validate({ marginTop: value }), /CSS length requires explicit units: marginTop/);
    }
  }
  assert.deepEqual(normalizeExplicitCss({ marginTop: cssLength(-2), padding: cssLength(0) }), {
    marginTop: "-2px", padding: "0px",
  });
});

test("strings retain their exact declarations without source mutation", () => {
  const input = Object.freeze({ width: "12px", gap: "0.5rem", gridColumn: "1 / -1", "--cue-accent": "#ffd166" });
  const declarations = normalizeExplicitCss(input);
  assert.deepEqual(declarations, input);
  assert.notEqual(declarations, input);
});

test("undefined declarations and omitted keys retain the hook input shape", () => {
  const input = { color: "red", background: undefined, opacity: 0 };
  const declarations = normalizeExplicitCss(input);
  assert.deepEqual(declarations, { color: "red", background: undefined, opacity: "0" });
  assert.equal(Object.hasOwn(declarations, "background"), true);
  assert.equal(Object.hasOwn(declarations, "width"), false);
  assert.deepEqual(input, { color: "red", background: undefined, opacity: 0 });
  assert.deepEqual(normalizeExplicitCss({ color: undefined }), { color: undefined });
});

test("cssLength preserves strings and absence and serializes finite lengths", () => {
  assert.equal(cssLength(undefined), undefined);
  assert.equal(cssLength("auto"), "auto");
  assert.equal(cssLength("0.5rem"), "0.5rem");
  assert.equal(cssLength(0), "0px");
  assert.equal(cssLength(-0), "0px");
  assert.equal(cssLength(-2), "-2px");
  assert.equal(cssLength(2.5), "2.5px");
  for (const value of [NaN, Infinity, -Infinity]) {
    assert.throws(() => cssLength(value), /CSS length must be finite/);
  }
});

test("nonfinite numbers are refused for unitless, custom and dimensional declarations", () => {
  for (const property of ["opacity", "--cue-count", "width"]) {
    for (const value of [NaN, Infinity, -Infinity]) {
      for (const validate of [assertExplicitCss, normalizeExplicitCss]) {
        assert.throws(() => validate({ [property]: value }), new RegExp(`Nonfinite CSS value: ${property}`));
      }
    }
  }
});

test("CSS bags reject primitives, arrays and nonplain prototypes", () => {
  class CssBag { opacity = 1; }
  for (const input of [null, 0, "opacity", true, Symbol("css"), 1n, () => {}, [], new Date(0), new CssBag(), Object.create({ opacity: 1 })]) {
    for (const validate of [assertExplicitCss, normalizeExplicitCss]) {
      assert.throws(() => validate(input), /CSS declarations must be a plain bag/);
    }
  }
});

test("plain bags may have a null prototype and frozen own data entries", () => {
  const input = Object.create(null);
  input.opacity = 0.5;
  input["--cue-accent"] = "gold";
  Object.freeze(input);
  assert.equal(assertExplicitCss(input), undefined);
  assert.deepEqual(normalizeExplicitCss(input), { opacity: "0.5", "--cue-accent": "gold" });
});

test("unsupported values are refused even for custom declarations", () => {
  for (const value of [null, true, {}, [], () => {}, Symbol("value"), 1n]) {
    for (const validate of [assertExplicitCss, normalizeExplicitCss]) {
      assert.throws(() => validate({ "--cue-count": value }), /Unsupported CSS value: --cue-count/);
    }
  }
});

test("enumerable accessor declarations are refused without invoking them", () => {
  let reads = 0, writes = 0;
  const getter = Object.defineProperty({}, "opacity", { enumerable: true, get() { reads += 1; return 1; } });
  const setter = Object.defineProperty({}, "opacity", { enumerable: true, set() { writes += 1; } });
  for (const input of [getter, setter]) {
    for (const validate of [assertExplicitCss, normalizeExplicitCss]) {
      assert.throws(() => validate(input), /CSS declarations must use own data properties: opacity/);
    }
  }
  assert.equal(reads, 0);
  assert.equal(writes, 0);
});

test("nonenumerable and symbol properties remain outside CSS declaration entries", () => {
  let reads = 0;
  const input = { opacity: 0.5 };
  Object.defineProperty(input, "width", { get() { reads += 1; return 12; } });
  Object.defineProperty(input, Symbol("private"), { enumerable: true, get() { reads += 1; return {}; } });
  assert.equal(assertExplicitCss(input), undefined);
  assert.deepEqual(normalizeExplicitCss(input), { opacity: "0.5" });
  assert.equal(reads, 0);
});
