import * as fs from "node:fs";
import path from "node:path";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import ts from "../frontend/node_modules/typescript/lib/typescript.js";

const hash = (data) => createHash("sha256").update(data).digest("hex");
const root = process.cwd(), output = ".gate/gen/styles";
fs.mkdirSync(output, { recursive: true });
const rendererPath = "frontend/node_modules/react-dom/cjs/react-dom-client.development.js";
const rendererBytes = fs.readFileSync(rendererPath), renderer = ts.createSourceFile(rendererPath, rendererBytes.toString(), ts.ScriptTarget.Latest, true, ts.ScriptKind.JS);
let unitless;
function inspect(node) {
  if (ts.isBinaryExpression(node) && node.left.getText(renderer) === "unitlessNumbers" && ts.isNewExpression(node.right)) {
    const value = node.right.arguments?.[0];
    if (value && ts.isCallExpression(value) && ts.isPropertyAccessExpression(value.expression) && value.expression.name.text === "split" && ts.isStringLiteral(value.expression.expression)) unitless = value.expression.expression.text.split(" ");
  }
  ts.forEachChild(node, inspect);
}
inspect(renderer);
assert.ok(unitless?.length > 50, "Actual original renderer unitless list required");
const set = new Set(unitless);
const policyBytes = fs.readFileSync("frontend/src/components/cssUnits.ts"), policySource = ts.createSourceFile("cssUnits.ts", policyBytes.toString(), ts.ScriptTarget.Latest, true);
let declared;
function policy(node) {
  if (ts.isVariableDeclaration(node) && node.name.getText(policySource) === "UNITLESS_PROPERTIES") {
    const value = ts.isAsExpression(node.initializer) ? node.initializer.expression : node.initializer;
    if (ts.isArrayLiteralExpression(value)) declared = value.elements.map((item) => item.text);
  }
  ts.forEachChild(node, policy);
}
policy(policySource); assert.deepEqual(declared, unitless, "App unitless policy must equal the pinned original renderer");
const tsconfig = ts.readConfigFile("frontend/tsconfig.json", ts.sys.readFile).config;
const parsed = ts.parseJsonConfigFileContent(tsconfig, ts.sys, path.resolve("frontend"));
const program = ts.createProgram(parsed.fileNames, parsed.options), checker = program.getTypeChecker();
const sites = [], manual = [], transformed = [];
function numeric(value) {
  const type = checker.getTypeAtLocation(value);
  return type.flags & ts.TypeFlags.NumberLike || type.isUnion?.() && type.types.some((part) => part.flags & ts.TypeFlags.NumberLike);
}
for (const source of program.getSourceFiles().filter((file) => file.fileName.startsWith(path.join(root, "frontend/src")) && file.fileName.endsWith(".tsx"))) {
  const relative = path.relative(root, source.fileName), text = source.text, edits = [], imports = new Set();
  function edit(start, end, value) { edits.push({ start, end, value }); }
  function visit(node) {
    if (!ts.isJsxAttribute(node) || node.name.text !== "style") { ts.forEachChild(node, visit); return; }
    const opening = node.parent.parent, tag = opening.tagName.getText(source), position = source.getLineAndCharacterOfPosition(node.getStart(source));
    const site = { file: relative, line: position.line + 1, column: position.character + 1, tag, expression_sha256: hash(node.initializer.getText(source)), ref: opening.attributes.properties.find((attr) => ts.isJsxAttribute(attr) && attr.name.text === "ref")?.initializer?.getText(source) ?? null, values: [] };
    sites.push(site);
    let expression = node.initializer.expression;
    if (ts.isAsExpression(expression) && expression.type.getText(source) === "CSSProperties") expression = expression.expression;
    if (!expression || !ts.isObjectLiteralExpression(expression)) { manual.push({ ...site, reason: "nonliteral or unsupported cast CSS bag" }); return; }
    const properties = [], removals = [];
    for (const prop of expression.properties) {
      if (!ts.isPropertyAssignment(prop) || ![ts.SyntaxKind.Identifier, ts.SyntaxKind.StringLiteral].includes(prop.name.kind)) { manual.push({ ...site, reason: "spread/computed/unsupported CSS member" }); continue; }
      const key = prop.name.text, value = prop.initializer;
      if (key === "opacity" && tag === "m.button" && ["frontend/src/screens/Alchimie.tsx", "frontend/src/screens/Conexiuni.tsx"].includes(relative)) {
        assert.ok(ts.isConditionalExpression(value) && ts.isNumericLiteral(value.whenTrue) && Number(value.whenFalse.getText(source)) === 1);
        const opacity = Number(value.whenTrue.text), className = opacity === .5 ? "csp-motion-opacity-50" : opacity === .55 ? "csp-motion-opacity-55" : null;
        assert.ok(className, "Known original Motion opacity predicate required");
        const attr = opening.attributes.properties.find((item) => ts.isJsxAttribute(item) && item.name.text === "className");
        assert.ok(attr?.initializer);
        const old = ts.isStringLiteral(attr.initializer) ? JSON.stringify(attr.initializer.text) : attr.initializer.expression.getText(source);
        edit(attr.initializer.getStart(source), attr.initializer.end, `{(${old}) + (${value.condition.getText(source)} ? " ${className}" : "")}`);
        removals.push({ start: prop.getStart(source), end: text[prop.end] === "," ? prop.end + 1 : prop.end });
        site.values.push({ key, decision: "retain-original-static-class-below-motion-inline", value: value.getText(source), className }); continue;
      }
      const allow = set.has(key) || key.startsWith("--");
      if (!allow && numeric(value)) {
        const replacement = ts.isNumericLiteral(value) || ts.isPrefixUnaryExpression(value) ? JSON.stringify(`${Number(value.getText(source))}px`) : `cssLength(${value.getText(source)})`;
        properties.push({ start: value.getStart(source), end: value.end, value: replacement });
        if (replacement.startsWith("cssLength")) imports.add("cssLength");
        site.values.push({ key, decision: "explicit-length", value: value.getText(source), replacement });
      } else site.values.push({ key, decision: allow ? "unitless-or-custom" : "string-or-undefined", value: value.getText(source) });
    }
    if (manual.some((item) => item.file === site.file && item.line === site.line)) return;
    let object = expression.getText(source);
    for (const item of [...properties, ...removals.map((item) => ({ ...item, value: "" }))].sort((a, b) => b.start - a.start)) object = object.slice(0, item.start - expression.getStart(source)) + item.value + object.slice(item.end - expression.getStart(source));
    edit(node.name.getStart(source), node.name.end, "css"); edit(node.initializer.getStart(source), node.initializer.end, `{${object}}`);
    let replacement;
    if (/^[a-z]+$/.test(tag)) { replacement = `Csp.${tag}`; imports.add("Csp"); }
    else if (["m.div", "m.button", "m.span", "m.p"].includes(tag)) { replacement = tag.replace("m.", "CspMotion."); imports.add("CspMotion"); }
    else if (tag === "Button") { replacement = "CspButton"; imports.add("CspButton"); }
    else { manual.push({ ...site, reason: "unsupported styled component" }); return; }
    edit(opening.tagName.getStart(source), opening.tagName.end, replacement);
    if (ts.isJsxOpeningElement(opening)) edit(opening.parent.closingElement.tagName.getStart(source), opening.parent.closingElement.tagName.end, replacement);
  }
  visit(source);
  if (!sites.some((site) => site.file === relative)) continue;
  let converted = text;
  for (const item of edits.sort((a, b) => b.start - a.start)) converted = converted.slice(0, item.start) + item.value + converted.slice(item.end);
  if (relative.endsWith("/PlayGuide.tsx")) converted = converted.replace("CSSProperties, ReactNode", "ReactNode");
  let module = path.relative(path.dirname(source.fileName), path.join(root, "frontend/src/components/CspStyle")).split(path.sep).join("/");
  if (!module.startsWith(".")) module = "./" + module;
  converted = `import { ${[...imports].sort().join(", ")} } from ${JSON.stringify(module)};\n` + converted;
  const destination = path.join(output, "converted", relative); fs.mkdirSync(path.dirname(destination), { recursive: true }); fs.writeFileSync(destination, converted);
  transformed.push({ file: relative, before_sha256: hash(text), after_sha256: hash(converted) });
}
const report = { schema: 1, sha: process.env.GATE_SHA, tree_sha256: process.env.GATE_TREE_SHA256, toolchain_digest: process.env.TOOLCHAIN_DIGEST, parser: ts.version, renderer: { file: rendererPath, sha256: hash(rendererBytes), version: "19.2.7" }, policy_sha256: hash(policyBytes), unitless, site_count: sites.length, sites, manual, files: transformed, mode: "planned-edits-only-product-files-unmodified" };
fs.writeFileSync(`${output}/report.json`, JSON.stringify(report, null, 2) + "\n");
process.stdout.write(JSON.stringify({ ...report, sites: undefined, unitless: undefined, files: undefined }, null, 2) + "\n");
assert.equal(manual.length, 0, "Unsupported style sites require source review before application");
