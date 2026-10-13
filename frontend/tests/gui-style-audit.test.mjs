import assert from "node:assert/strict";
import test from "node:test";
import ts from "@typescript/typescript6";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { EXPECTED_CSS_BAGS, auditProgram, readUnitlessPolicy } from "../../scripts/gui-style-audit.mjs";

// This lane exercises the read-only M2 explicit-unit audit with narrow virtual
// JSX declarations plus one run over the current owning source. It does not
// render Preact/React, prove DOM/CSSOM output, screenshots or M2 acceptance.
const unitless = readUnitlessPolicy(ts, readFileSync(new URL("../src/components/cssUnits.ts", import.meta.url), "utf8"));
const root = "/fixture";

function audit(body, ownedDeclaration, policy = unitless) {
  const filename = root + "/frontend/src/fixture.tsx";
  const text = `
type Css = {width?: string | number; fontSize?: string | number; margin?: string | number; gap?: string | number;
  borderRadius?: string | number; top?: string | number; letterSpacing?: string | number; opacity?: number;
  zIndex?: number; flexGrow?: number; lineHeight?: string | number; fontWeight?: number; aspectRatio?: string | number;
  color?: string; [key: \`--\${string}\`]: string | number | undefined};
declare const Csp: {div: (props: {css?: Css; style?: Css; children?: unknown}) => null; span: (props: {css?: Css; style?: Css}) => null};
declare const Slot: (props: {title?: unknown; render?: (count: number) => unknown; slots?: {header?: unknown}; children?: unknown}) => null;
declare const uncertain: unknown;
declare const unsafe: any;
declare const numeric: number;
declare const flag: boolean;
declare const NaN: number;
declare const Infinity: number;
declare function stringify(value: unknown): string;
${body}`;
  const source = ts.createSourceFile(filename, text, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  assert.equal(source.parseDiagnostics.length, 0, "Mutation fixture must parse");
  const sources = new Map([[filename, source]]);
  if (ownedDeclaration !== undefined) {
    const declaredFilename = root + "/frontend/src/owned-types.d.mts";
    const declaredSource = ts.createSourceFile(declaredFilename, ownedDeclaration, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS);
    assert.equal(declaredSource.parseDiagnostics.length, 0, "Owned declaration mutation must parse");
    sources.set(declaredFilename, declaredSource);
  }
  const options = { noLib: true, strict: true, jsx: ts.JsxEmit.Preserve, target: ts.ScriptTarget.ES2021 };
  const host = ts.createCompilerHost(options);
  host.getSourceFile = (name) => sources.get(name);
  host.fileExists = (name) => sources.has(name);
  host.readFile = (name) => sources.get(name)?.text;
  return auditProgram(ts, ts.createProgram([...sources.keys()], options, host), root, policy);
}
const reasons = (result) => result.findings.map((item) => item.reason);
const missingUnit = (result, key) => reasons(result).includes("Dimensional numeric declaration requires explicit units: " + key);

void test("all explicit lengths and reviewed unitless/custom numbers pass without edits", () => {
  const result = audit('export const example = <Csp.div css={{width: "12px", opacity: 0, fontWeight: numeric, "--count": 2}} />;');
  assert.deepEqual(result.findings, []);
  assert.deepEqual(result.counters, { css_bags: 1, nested_css_bags: 0, declarations: 4, numeric_declarations: 3,
    unitless_numeric: 2, custom_numeric: 1, raw_style_attributes: 0 });
  assert.equal(result.sites.length, 1);
  assert.match(result.sites_sha256, /^[a-f0-9]{64}$/);
});

void test("missing units: zero, negative, conditional and dynamic dimensional numbers all refuse", () => {
  for (const [key, value] of [["width", "0"], ["width", "-2"], ["width", "numeric"], ["width", 'numeric ? "12px" : 4'],
    ["fontSize", "12"], ["margin", "0"], ["gap", "4"], ["borderRadius", "8"], ["top", "-1"], ["letterSpacing", "1"]]) {
    const result = audit(`export const example = <Csp.div css={{${key}: ${value}}} />;`);
    assert.ok(missingUnit(result, key), `${key}: ${value}`);
    assert.equal(result.findings.length, 1, `${key}: ${value}`);
    assert.equal(audit(`export const example = <Csp.div css={{${key}: "${value === "0" ? "0px" : "1px"}"}} />;`).findings.length, 0, key);
  }
});

void test("nested attribute bags: element-valued, props-object, render-prop and child bags are all audited", () => {
  const nested = [
    'export const example = <Slot title={<Csp.span css={{width: 4}} />} />;',
    'export const example = <Slot title={<><Csp.span css={{width: 4}} /></>} />;',
    'export const example = <Slot title={flag ? <Csp.span css={{width: 4}} /> : null} />;',
    'export const example = <Slot slots={{header: <Csp.span css={{width: 4}} />}} />;',
    'export const example = <Slot render={(count) => <Csp.span css={{width: count}} />} />;',
    'export const example = <Slot title={<Csp.div><Csp.span css={{width: 4}} /></Csp.div>} />;',
    'export const example = <Slot title={<Slot render={() => <Csp.span css={{width: 4}} />} />} />;',
  ];
  for (const body of nested) {
    const result = audit(body);
    assert.ok(missingUnit(result, "width"), body);
    assert.equal(result.counters.css_bags, 1, body);
    assert.equal(result.counters.nested_css_bags, 1, body);
    assert.equal(result.sites[0].nested, true, body);
  }
  const child = audit('export const example = <Csp.div><Slot>{<Csp.span css={{width: 4}} />}</Slot></Csp.div>;');
  assert.ok(missingUnit(child, "width"));
  assert.equal(child.counters.nested_css_bags, 0, "JSX children are not attribute-nested");
  const raw = audit('export const example = <Slot title={<Csp.span style={{width: "4px"}} />} />;');
  assert.equal(raw.counters.raw_style_attributes, 1);
  assert.ok(reasons(raw).includes("Raw JSX style attribute refused"));
  const mixed = audit('export const example = <Csp.div css={{opacity: 1}}><Slot title={<Csp.span css={{width: "4px"}} />} '
    + 'slots={{header: <Csp.span css={{"--n": 1}} />}} render={() => <Csp.span css={{zIndex: 2}} />} /></Csp.div>;');
  assert.deepEqual(mixed.findings, []);
  assert.equal(mixed.counters.css_bags, 4);
  assert.equal(mixed.counters.nested_css_bags, 3);
  assert.deepEqual(mixed.sites.map((site) => site.nested), [false, true, true, true]);
});

void test("unitless allow-list follows the reviewed Preact 11 policy: verbatim numbers only where CSS accepts them", () => {
  for (const key of ["opacity", "zIndex", "flexGrow", "lineHeight", "fontWeight", "aspectRatio", "flex", "order", "scale"])
    assert.ok(unitless.has(key), key);
  for (const key of ["width", "fontSize", "margin", "gap", "borderRadius", "top", "letterSpacing", "padding", "height"])
    assert.ok(!unitless.has(key), key);
  for (const key of ["opacity", "zIndex", "flexGrow", "lineHeight", "fontWeight", "aspectRatio"]) {
    const result = audit(`export const example = <Csp.div css={{${key}: 1}} />;`);
    assert.deepEqual(result.findings, [], key);
    assert.equal(result.counters.unitless_numeric, 1, key);
    assert.equal(result.sites[0].declarations[0].decision, "reviewed-unitless-number", key);
  }
  // The decision is policy-bound: a property absent from the reviewed list loses its unitless admission.
  const narrowed = new Set([...unitless].filter((key) => key !== "opacity"));
  assert.ok(missingUnit(audit("export const example = <Csp.div css={{opacity: 1}} />;", undefined, narrowed), "opacity"));
  assert.throws(() => readUnitlessPolicy(ts, 'export const UNITLESS_PROPERTIES = ["opacity"] as const;'), /71-property/);
});

void test("unknown, any, null and callable declaration values all refuse", () => {
  for (const value of ["uncertain", "unsafe", "null", "() => 1"]) {
    const result = audit(`export const example = <Csp.div css={{opacity: ${value}}} />;`);
    assert.ok(result.findings.some((item) => item.reason.includes("Unresolved or unsupported")), value);
  }
});

void test("assertions, non-null, satisfies and unsafe call inputs cannot launder CSS values", () => {
  for (const [key, value] of [
    ["width", "numeric as unknown as string"],
    ["opacity", "unsafe as number"],
    ["opacity", "numeric!"],
    ["opacity", "numeric satisfies number"],
  ]) {
    const result = audit(`export const example = <Csp.div css={{${key}: ${value}}} />;`);
    assert.ok(result.findings.some((item) => item.reason.includes("Assertions, non-null and satisfies")), value);
  }
  for (const value of ["unsafe", "uncertain"]) {
    const result = audit(`export const example = <Csp.div css={{width: stringify(${value})}} />;`);
    assert.ok(result.findings.some((item) => item.reason.includes("Unresolved or unsupported CSS value source")), value);
  }
  assert.deepEqual(audit('export const example = <Csp.div css={{width: stringify(numeric)}} />;').findings, []);
});

void test("computed keys, accessors, aliases, duplicate keys and spreads refuse", () => {
  for (const body of [
    'export const example = <Csp.div css={{["opacity"]: 1}} />;',
    'export const example = <Csp.div css={{get opacity() {return 1}}} />;',
    'const bag = {opacity: 1}; export const example = <Csp.div css={bag} />;',
    'export const example = <Csp.div css={{opacity: 1, opacity: 0}} />;',
    'const bag = {opacity: 1}; export const example = <Csp.div css={{...bag}} />;',
  ]) assert.ok(audit(body).findings.length > 0, body);
});

void test("raw JSX styles and unknown properties refuse", () => {
  assert.ok(audit('export const example = <Csp.div style={{width: 2}} />;').findings.some((item) => item.reason.includes("Raw JSX")));
  assert.ok(audit('export const example = <Csp.div css={{unsupported: 2}} />;').findings.some((item) => item.reason.includes("unknown CSS property")));
});

void test("obvious nonfinite values refuse even for unitless properties", () => {
  for (const value of ["NaN", "Infinity", "-Infinity", "1e999"]) {
    assert.ok(audit(`export const example = <Csp.div css={{opacity: ${value}}} />;`).findings.some((item) => item.reason.includes("Nonfinite CSS value")), value);
  }
});

void test("owned declaration changes bind provenance and the inferred numeric decision", () => {
  const body = 'export const example = <Csp.div css={{width: declaredDimension}} />;';
  const explicit = audit(body, 'declare global {const declaredDimension: "12px";} export {};');
  const dimensional = audit(body, 'declare global {const declaredDimension: 12;} export {};');
  assert.deepEqual(explicit.findings, []);
  assert.ok(missingUnit(dimensional, "width"));
  assert.equal(explicit.audited_tsx_files, 1);
  assert.equal(explicit.owned_program_source_files, 2);
  assert.equal(explicit.audited_tsx_sha256, dimensional.audited_tsx_sha256);
  assert.notEqual(explicit.owned_program_source_sha256, dimensional.owned_program_source_sha256);
});

void test("the current owning source audits every bag, including nested ones, with a stable report", (t) => {
  const repository = fileURLToPath(new URL("../../", import.meta.url));
  const script = fileURLToPath(new URL("../../scripts/gui-style-audit.mjs", import.meta.url));
  const run = () => spawnSync(process.execPath, [script, "--root", repository], { encoding: "utf8", maxBuffer: 16 << 20 });
  const child = run();
  assert.ok(!child.error, child.error?.message);
  assert.equal(child.status, 0, child.stdout + child.stderr);
  assert.equal(child.stderr, "");
  const again = run();
  assert.equal(again.status, 0);
  assert.equal(again.stdout, child.stdout, "Report bytes must be stable across runs");
  assert.ok(!child.stdout.includes(repository), "Report must not embed the checkout location");
  const result = JSON.parse(child.stdout);
  assert.equal(result.status, "pass");
  assert.equal(EXPECTED_CSS_BAGS, 59);
  assert.equal(result.counters.css_bags, 59);
  assert.equal(result.sites.length, 59);
  assert.equal(result.counters.nested_css_bags, 5, "Bags nested in other JSX attributes must be counted");
  assert.equal(result.sites.filter((site) => site.nested).length, result.counters.nested_css_bags);
  assert.equal(result.counters.raw_style_attributes, 0);
  assert.equal(result.counters.numeric_declarations, result.counters.unitless_numeric + result.counters.custom_numeric);
  assert.ok(result.sites.every((site) => site.path.startsWith("frontend/src/") && site.path.endsWith(".tsx")));
  assert.ok(result.sites.flatMap((site) => site.declarations).every((item) =>
    ["explicit-string-or-undefined", "reviewed-unitless-number", "custom-number"].includes(item.decision)));
  assert.equal(result.source_changes, 0);
  assert.deepEqual(result.codemod_delta, []);
  assert.deepEqual(result.findings, []);
  assert.ok(result.owned_program_source_files > result.audited_tsx_files);
  assert.deepEqual(result.semantic_config_inputs.map((item) => item.path), ["frontend/package.json", "frontend/package-lock.json", "frontend/tsconfig.json"]);
  assert.ok(result.semantic_config_inputs.every((item) => /^[a-f0-9]{64}$/.test(item.sha256)));
  assert.equal(result.parser_provenance.package.name, "@typescript/typescript6");
  assert.equal(result.parser_provenance.package.version, "6.0.2");
  assert.equal(result.parser_provenance.package.path, "frontend/node_modules/@typescript/typescript6/package.json");
  assert.equal(result.parser_provenance.implementation.name, "typescript");
  assert.equal(result.parser_provenance.implementation.version, ts.version);
  assert.match(result.parser_provenance.implementation.path, /^frontend\/node_modules\//);
  assert.match(result.parser_provenance.implementation.entry_sha256, /^[a-f0-9]{64}$/);
  assert.match(result.parser_provenance.implementation.manifest_sha256, /^[a-f0-9]{64}$/);
  t.diagnostic("gui-style-audit " + JSON.stringify({ status: result.status, counters: result.counters, findings: result.findings.length,
    audited_tsx_files: result.audited_tsx_files, sites_sha256: result.sites_sha256, report_sha256: createHash("sha256").update(child.stdout).digest("hex") }));
});
