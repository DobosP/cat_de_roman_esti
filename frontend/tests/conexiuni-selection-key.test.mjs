import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import vm from "node:vm";
import test from "node:test";
import ts from "typescript";

// Authored NOT RUN. This executes the actual local utility, independently of
// React and public retry UI; it does not qualify a native server/session.
function actualSelectionKey() {
  const lock = JSON.parse(readFileSync(new URL("../package-lock.json", import.meta.url), "utf8"));
  assert.equal(ts.version, lock.packages["node_modules/typescript"].version);
  const configFile = fileURLToPath(new URL("../tsconfig.json", import.meta.url));
  const config = ts.readConfigFile(configFile, ts.sys.readFile);
  assert.equal(config.error, undefined);
  const parsed = ts.parseJsonConfigFileContent(config.config, ts.sys,
    fileURLToPath(new URL("../", import.meta.url)), undefined, configFile);
  assert.equal(parsed.errors.length, 0, JSON.stringify(parsed.errors));
  assert.equal(parsed.options.strict, true);
  const filename = fileURLToPath(new URL("../src/conexiuniSelectionKey.ts", import.meta.url));
  const source = readFileSync(filename, "utf8");
  // CommonJS is only the VM container adaptation. The actual target/useDefine
  // options are retained; bundler module resolution is not a runtime dependency.
  const transformed = ts.transpileModule(source, {
    fileName: filename,
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: parsed.options.target,
      useDefineForClassFields: parsed.options.useDefineForClassFields,
      alwaysStrict: true,
    },
    reportDiagnostics: true,
  });
  const errors = (transformed.diagnostics ?? []).filter(({ category }) => category === ts.DiagnosticCategory.Error);
  assert.equal(errors.length, 0, ts.formatDiagnosticsWithColorAndContext(errors, {
    getCanonicalFileName: (name) => name,
    getCurrentDirectory: () => fileURLToPath(new URL("../", import.meta.url)),
    getNewLine: () => "\n",
  }));
  const exported = {};
  vm.runInNewContext(transformed.outputText, {
    exports: exported,
    require(name) { throw new Error(`Pure selection-key module has an unexpected dependency: ${name}`); },
  }, { filename });
  assert.deepEqual(Object.keys(exported), ["selectionKey"]);
  assert.equal(typeof exported.selectionKey, "function");
  return exported.selectionKey;
}

function* permutations(values) {
  if (values.length === 0) { yield []; return; }
  for (const [index, value] of values.entries()) {
    for (const rest of permutations(values.filter((_, candidate) => candidate !== index))) {
      yield [value, ...rest];
    }
  }
}

test("retained selection identity is permutation-equivalent without mutating caller arrays", () => {
  const selectionKey = actualSelectionKey();
  const retained = Object.freeze(["tile-c", "tile-a", "tile-d", "tile-b"]);
  const retainedKey = selectionKey(retained);
  assert.deepEqual(retained, ["tile-c", "tile-a", "tile-d", "tile-b"]);
  let checked = 0;
  for (const candidate of permutations(retained)) {
    const before = [...candidate];
    assert.equal(selectionKey(candidate), retainedKey);
    assert.deepEqual(candidate, before);
    checked += 1;
  }
  assert.equal(checked, 24);
});

test("different opaque selections and multiplicities keep distinct identities", () => {
  const selectionKey = actualSelectionKey();
  assert.notEqual(selectionKey(["a", "bc"]), selectionKey(["ab", "c"]));
  assert.notEqual(selectionKey(["a,b", "c"]), selectionKey(["a", "b,c"]));
  assert.notEqual(selectionKey(["tile-a", "tile-b", "tile-c", "tile-d"]),
    selectionKey(["tile-a", "tile-b", "tile-c", "tile-e"]));
  assert.notEqual(selectionKey(["opaque"]), selectionKey(["opaque", "opaque"]));
  assert.notEqual(selectionKey([]), selectionKey([""]));
});

test("selection keys preserve lossless JSON encoding of complete opaque IDs", () => {
  const selectionKey = actualSelectionKey();
  const ids = ["[brackets]", "Șir / ? # %", "back\\slash", "line\nbreak", "nul\u0000inside", "quote\"inside"];
  const before = [...ids];
  const key = selectionKey(ids);
  // Literal expected encoding is independent of the utility's sorting body.
  assert.equal(key, '["[brackets]","back\\\\slash","line\\nbreak","nul\\u0000inside","quote\\"inside","Șir / ? # %"]');
  assert.deepEqual(JSON.parse(key), ["[brackets]", "back\\slash", "line\nbreak", "nul\u0000inside", "quote\"inside", "Șir / ? # %"]);
  assert.deepEqual(ids, before);
});
