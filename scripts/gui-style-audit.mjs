#!/usr/bin/env node
// Read-only M2 explicit-unit audit over the current owning source. It never
// applies or replays the historical codemod and writes no source or baseline.
// Preact 11 core sets numeric style values verbatim (no px suffix outside
// compat), so a number is only valid for a reviewed unitless property or a
// custom property; every other numeric declaration must carry explicit units.
import assert from "node:assert/strict";
import * as fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import { parserBinding } from "../frontend/scripts/compiler-runtime.mjs";

export const EXPECTED_CSS_BAGS = 162;
const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
const slash = (value) => value.split(path.sep).join("/");

export function readUnitlessPolicy(ts, text) {
  const source = ts.createSourceFile("cssUnits.ts", text, ts.ScriptTarget.Latest, true);
  assert.equal(source.parseDiagnostics.length, 0, "Unitless policy must parse");
  const matches = [];
  function visit(node) {
    if (ts.isVariableDeclaration(node) && ts.isIdentifier(node.name) && node.name.text === "UNITLESS_PROPERTIES") {
      let value = node.initializer;
      while (value && (ts.isAsExpression(value) || ts.isParenthesizedExpression(value))) value = value.expression;
      assert.ok(value && ts.isArrayLiteralExpression(value), "Literal unitless array required");
      assert.ok(value.elements.every(ts.isStringLiteral), "Literal unitless names required");
      matches.push(value.elements.map((item) => item.text));
    }
    ts.forEachChild(node, visit);
  }
  visit(source);
  assert.equal(matches.length, 1, "One actual source policy required");
  const values = matches[0];
  assert.equal(values.length, 71, "Current reviewed 71-property policy required");
  assert.equal(new Set(values).size, values.length, "Duplicate policy names refused");
  assert.ok(values.every((name) => /^[A-Za-z][A-Za-z0-9]*$/.test(name)));
  return new Set(values);
}

function valueKinds(ts, checker, expression) {
  let type = checker.getTypeAtLocation(expression);
  const types = type.isUnion() ? type.types : [type];
  const kinds = new Set();
  for (type of types) {
    if (type.flags & (ts.TypeFlags.Any | ts.TypeFlags.Unknown | ts.TypeFlags.TypeParameter | ts.TypeFlags.Never)) return null;
    if (type.flags & ts.TypeFlags.StringLike) kinds.add("string");
    else if (type.flags & ts.TypeFlags.NumberLike) kinds.add("number");
    else if (type.flags & ts.TypeFlags.Undefined) kinds.add("undefined");
    else return null;
  }
  return [...kinds].sort();
}

function valueSourceRefusal(ts, checker, expression) {
  let refusal = null;
  const unsafeType = (type) => Boolean(type.flags &
    (ts.TypeFlags.Any | ts.TypeFlags.Unknown | ts.TypeFlags.TypeParameter | ts.TypeFlags.Never))
    || type.isUnion() && type.types.some(unsafeType);
  function visit(node) {
    if (refusal) return;
    if (ts.isAsExpression(node) || ts.isTypeAssertionExpression(node)
      || ts.isNonNullExpression(node) || ts.isSatisfiesExpression(node)) {
      refusal = "Assertions, non-null and satisfies declarations refused";
      return;
    }
    // A safe outer return type must not launder an any/unknown input through a
    // call or property access. This inspects the expression tree only; it does
    // not purport to prove arbitrary called function implementations at runtime.
    if (ts.isExpression(node) && unsafeType(checker.getTypeAtLocation(node))) {
      refusal = "Unresolved or unsupported CSS value source";
      return;
    }
    ts.forEachChild(node, visit);
  }
  visit(expression);
  return refusal;
}

export function auditProgram(ts, program, root, unitless) {
  const checker = program.getTypeChecker(), findings = [], sites = [];
  const counters = { css_bags: 0, nested_css_bags: 0, declarations: 0, numeric_declarations: 0, unitless_numeric: 0,
    custom_numeric: 0, raw_style_attributes: 0 };
  // Initializer types can depend on owned .ts/.d.mts modules. Bind every owned
  // source/declaration in the actual program, not just the audited JSX owners.
  const ownedProgram = program.getSourceFiles().filter((source) =>
    slash(path.relative(root, source.fileName)).startsWith("frontend/src/")).sort((a, b) => a.fileName.localeCompare(b.fileName));
  const inputs = ownedProgram.map((source) => ({ path: slash(path.relative(root, source.fileName)), sha256: hash(source.text) }));
  const files = ownedProgram.filter((source) => !source.isDeclarationFile && source.fileName.endsWith(".tsx"));
  const tsxInputs = files.map((source) => ({ path: slash(path.relative(root, source.fileName)), sha256: hash(source.text) }));
  for (const source of files) {
    const relative = slash(path.relative(root, source.fileName));
    const where = (node) => {
      const position = source.getLineAndCharacterOfPosition(node.getStart(source));
      return { line: position.line + 1, column: position.character + 1 };
    };
    const fail = (node, reason) => findings.push({ path: relative, ...where(node), reason });
    function auditBag(node, nested) {
      counters.css_bags += 1;
      if (nested) counters.nested_css_bags += 1;
      const site = { path: relative, ...where(node), nested, expression_sha256: hash(node.getText(source)), declarations: [] };
      sites.push(site);
      const value = node.initializer;
      if (!value || !ts.isJsxExpression(value) || !value.expression || !ts.isObjectLiteralExpression(value.expression)) {
        fail(node, "Explicit literal CSS bag required; casts, aliases and spreads are not audited"); return;
      }
      const bag = value.expression, rawContext = checker.getContextualType(bag),
        contextual = rawContext && checker.getNonNullableType(rawContext), keys = new Set();
      if (!contextual || contextual.flags & (ts.TypeFlags.Any | ts.TypeFlags.Unknown)) {
        fail(bag, "Resolved CSS declaration context required"); return;
      }
      for (const member of bag.properties) {
        if (!ts.isPropertyAssignment(member) || !(ts.isIdentifier(member.name) || ts.isStringLiteral(member.name))) {
          fail(member, "Computed, spread, shorthand, method and accessor declarations refused"); continue;
        }
        const key = member.name.text;
        if (keys.has(key) || key === "__proto__" || !key.startsWith("--") && !checker.getPropertyOfType(contextual, key)) {
          fail(member, "Duplicate or unknown CSS property: " + key); continue;
        }
        keys.add(key); counters.declarations += 1;
        const sourceRefusal = valueSourceRefusal(ts, checker, member.initializer);
        if (sourceRefusal) { fail(member, sourceRefusal + ": " + key); continue; }
        const kinds = valueKinds(ts, checker, member.initializer);
        if (!kinds) { fail(member, "Unresolved or unsupported CSS value: " + key); continue; }
        let nonfinite = false;
        function inspect(valueNode) {
          if (ts.isNumericLiteral(valueNode) && !Number.isFinite(Number(valueNode.text))) nonfinite = true;
          if (ts.isIdentifier(valueNode) && ["NaN", "Infinity"].includes(valueNode.text)) nonfinite = true;
          ts.forEachChild(valueNode, inspect);
        }
        inspect(member.initializer);
        if (nonfinite) { fail(member, "Nonfinite CSS value: " + key); continue; }
        let decision = "explicit-string-or-undefined";
        if (kinds.includes("number")) {
          counters.numeric_declarations += 1;
          if (key.startsWith("--")) { decision = "custom-number"; counters.custom_numeric += 1; }
          else if (unitless.has(key)) { decision = "reviewed-unitless-number"; counters.unitless_numeric += 1; }
          else { fail(member, "Dimensional numeric declaration requires explicit units: " + key); continue; }
        }
        site.declarations.push({ key, kinds, decision, value_sha256: hash(member.initializer.getText(source)) });
      }
    }
    // The traversal is total: every node, including the initializers of other
    // JSX attributes (element-valued props, props objects, render props) and
    // the CSS bag itself, is visited, so no nested css/style site is skipped.
    function visit(node, depth) {
      let inner = depth;
      if (ts.isJsxAttribute(node)) {
        const name = node.name.getText(source);
        if (name === "style") { counters.raw_style_attributes += 1; fail(node, "Raw JSX style attribute refused"); }
        else if (name === "css") auditBag(node, depth > 0);
        if (node.initializer) inner = depth + 1;
      }
      ts.forEachChild(node, (child) => visit(child, inner));
    }
    visit(source, 0);
  }
  return { counters, findings, sites, sites_sha256: hash(JSON.stringify(sites)),
    audited_tsx_files: files.length, audited_tsx_sha256: hash(JSON.stringify(tsxInputs)),
    owned_program_source_files: ownedProgram.length, owned_program_source_sha256: hash(JSON.stringify(inputs)) };
}

function relativeRecord(root, record) {
  const relative = slash(path.relative(root, record.path));
  assert.ok(relative && !relative.startsWith("../") && !path.isAbsolute(relative), "Parser provenance must stay inside the owning repo");
  return { ...record, path: relative };
}

export function main(argv = process.argv.slice(2)) {
  assert.deepEqual(argv.slice(0, 1), ["--root"], "Usage: node scripts/gui-style-audit.mjs --root <owning repo>");
  assert.equal(argv.length, 2, "No source-edit or baseline-output option exists");
  const root = fs.realpathSync(argv[1]), frontend = path.join(root, "frontend");
  const require = createRequire(path.join(frontend, "package.json"));
  const ts = require("@typescript/typescript6");
  // Lock-bound: the 6.0.2 wrapper legitimately resolves its locked 6.0.3 implementation.
  const binding = parserBinding(frontend, ts);
  const parserProvenance = { ...binding, package: relativeRecord(root, binding.package),
    implementation: relativeRecord(root, binding.implementation) };
  const policy = fs.readFileSync(path.join(frontend, "src/components/cssUnits.ts"));
  const unitless = readUnitlessPolicy(ts, policy.toString());
  const configFile = path.join(frontend, "tsconfig.json"), config = ts.readConfigFile(configFile, ts.sys.readFile);
  assert.ok(!config.error, "Owning config must parse");
  assert.ok(!config.config.extends && !config.config.references, "Additional config dependencies need explicit provenance before this audit supports them");
  const parsed = ts.parseJsonConfigFileContent(config.config, ts.sys, frontend);
  assert.equal(parsed.errors.length, 0, "Owning config diagnostics refused");
  const program = ts.createProgram(parsed.fileNames, parsed.options);
  assert.equal(program.getSyntacticDiagnostics().length, 0, "Source parser diagnostics refused");
  const audit = auditProgram(ts, program, root, unitless);
  if (audit.counters.css_bags !== EXPECTED_CSS_BAGS) audit.findings.push({ reason:
    `Current ${EXPECTED_CSS_BAGS}-bag inventory changed to ${audit.counters.css_bags}; review the source delta before rebinding` });
  const report = { schema: 1, check: "cat-m2-explicit-style-audit", status: audit.findings.length ? "fail" : "pass",
    scope: "Read-only CSS-bag declaration, nested JSX attribute and direct style-attribute audit; JSX spreads of non-literal props/native style lint are separate; not native compiler, screenshot, browser, full or M2 acceptance",
    mode: "dry-run", source_changes: 0, codemod_delta: [], parser: ts.version,
    parser_provenance: parserProvenance,
    policy_sha256: hash(policy), unitless_properties: unitless.size,
    semantic_config_inputs: ["frontend/package.json", "frontend/package-lock.json", "frontend/tsconfig.json"].map((name) => ({
      path: name, sha256: hash(fs.readFileSync(path.join(root, name))),
    })),
    dependency_provenance_limit: "Installed dependency declaration bytes are supplied by managed npm ci and native typecheck; these lock/config hashes do not independently qualify them",
    expected_css_bags: EXPECTED_CSS_BAGS, ...audit };
  process.stdout.write(JSON.stringify(report, null, 2) + "\n");
  return report.status === "pass" ? 0 : 1;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try { process.exitCode = main(); }
  catch (error) {
    process.stdout.write(JSON.stringify({ schema: 1, check: "cat-m2-explicit-style-audit", status: "fail", source_changes: 0, reason: error.message }) + "\n");
    process.exitCode = 1;
  }
}
