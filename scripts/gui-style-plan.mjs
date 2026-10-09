import * as fs from "node:fs";
import path from "node:path";
import assert from "node:assert/strict";
import { createHash, randomUUID } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";
import { createRequire } from "node:module";
import { spawnSync } from "node:child_process";
import { nativeCompiler, parserBinding } from "../frontend/scripts/compiler-runtime.mjs";
import { readNormalizedFrozenRenderer } from "./gui-style-operation.mjs";

const frontend = fileURLToPath(new URL("../frontend/", import.meta.url));
const require = createRequire(path.join(frontend, "package.json"));
const compilerVersion = JSON.parse(fs.readFileSync(path.join(frontend, "package.json"))).devDependencies.typescript;
const parserEntry = require.resolve(compilerVersion === "7.0.2" ? "@typescript/typescript6" : "typescript");
const loadedParser = await import(pathToFileURL(parserEntry).href);
const ts = loadedParser.default ?? loadedParser;

const hash = (data) => createHash("sha256").update(data).digest("hex");
export function bindSourceInput(inputs, file, data) {
  const record = { sha256: hash(data), bytes: data.length };
  if (Object.hasOwn(inputs, file)) assert.deepEqual(inputs[file], record, `Repeated source input changed: ${file}`);
  else Object.defineProperty(inputs, file, { value: record, enumerable: true, writable: false, configurable: false });
  return data;
}
const nativeTags = new Set("div span strong p form h1 header section label select input button summary h2 a ol ul li footer small".split(" "));
const motionTags = new Set(["m.div", "m.button", "m.span", "m.p"]);
export const ORIGINAL_OWNERS = Object.freeze({
  "frontend/src/screens/Alchimie.tsx": { opacity: 0.5, className: "csp-motion-opacity-50", source_sha256: "d5f299fc3189e887147779c19d39218dc9bd60b717d3f598cdfbbb62760fa53b" },
  "frontend/src/screens/Conexiuni.tsx": { opacity: 0.55, className: "csp-motion-opacity-55", source_sha256: "7c5d85dda928a7f385be2a31edc8ea217cf381e0d48fa6ddbd5888c1b02e9338" },
});
export const NORMALIZED_INPUTS = Object.freeze({
  "frontend/package.json": "d2fe548af9b8c097f2e067852332bdaed0daf319826892a6cb1c4e5bf92aa121",
  "frontend/package-lock.json": "fa9800b9a39cf7d30f60bd5b85e1a2bd1edcc662e20b851f4b85b56e09749915",
  "frontend/tsconfig.json": "c71b02d67f1b304ffd49edbcc5a5dc4a57719176c9d1f83aabef9c5d36d17617",
  "frontend/tsconfig.tools.json": "3604ec127a7a5fbadbb007409f949230b57cd0ac937fd0e4b1aa7a1cd9ad7754",
  "frontend/scripts/compiler-runtime.mjs": "16a7c8213c5835541c73906e02761e05f9378e067fd6f0f41a3a2fdfbf620d12",
});

export function absolutePath(value) {
  assert.equal(typeof value, "string", "Absolute path required");
  assert.ok(value && !value.includes("\0"), "Literal nonempty path required");
  const slashes = value.replaceAll("\\", "/"), windows = /^[A-Za-z]:\//.test(slashes), api = windows ? path.win32 : path.posix;
  assert.ok(windows || slashes.startsWith("/") && !slashes.startsWith("//"), "Absolute drive or POSIX path required");
  return api.normalize(slashes).replaceAll("\\", "/");
}
export function repoRelative(root, file) {
  const base = absolutePath(root), api = /^[A-Za-z]:\//.test(base) ? path.win32 : path.posix;
  assert.equal(typeof file, "string", "Literal file path required");
  const slashes = file.replaceAll("\\", "/");
  assert.ok(slashes && !slashes.includes("\0") && !slashes.startsWith("//"), "Literal file path required");
  const absolute = /^[A-Za-z]:\//.test(slashes) || slashes.startsWith("/");
  assert.ok(absolute || !slashes.includes(":"), "Drive-relative or stream path refused");
  const target = absolutePath(absolute ? slashes : api.resolve(base, slashes));
  assert.equal(/^[A-Za-z]:\//.test(target), api === path.win32, "Path platforms differ");
  const relative = api.relative(base, target).replaceAll("\\", "/");
  assert.ok(!api.isAbsolute(relative) && !relative.split("/").includes(".."), "Path escapes repo segments");
  return relative;
}
export function applyEdits(text, edits) {
  const sorted = [...edits].sort((a, b) => a.start - b.start || a.end - b.end); let previous;
  for (const edit of sorted) {
    assert.ok(Number.isInteger(edit.start) && Number.isInteger(edit.end) && edit.start >= 0 && edit.end >= edit.start && edit.end <= text.length, "Invalid edit bounds");
    assert.equal(typeof edit.value, "string", "Literal edit text required");
    if (previous) assert.ok(edit.start >= previous.end && !(edit.start === previous.start && edit.end === previous.end), "Overlapping or duplicate edits");
    previous = edit;
  }
  let result = text;
  for (const edit of sorted.reverse()) result = result.slice(0, edit.start) + edit.value + result.slice(edit.end);
  return result;
}

const diagnostics = (items) => items.map((item) => ({ code: item.code, category: ts.DiagnosticCategory[item.category], file: item.file?.fileName.replaceAll("\\", "/") ?? null, start: item.start ?? null, message: ts.flattenDiagnosticMessageText(item.messageText, "\n") }));
function parseSource(file, bytes, kind) {
  const source = ts.createSourceFile(file, bytes.toString(), ts.ScriptTarget.Latest, true, kind);
  assert.equal(source.parseDiagnostics.length, 0, `Invalid parser input: ${file}`); return source;
}
function uniqueList(list) {
  assert.ok(list.length === 71 && new Set(list).size === list.length && list.every((name) => /^[A-Za-z][A-Za-z0-9]*$/.test(name)), "Exact original71 unique unitless names required"); return list;
}
export function extractRendererUnitless(bytes) {
  const source = parseSource("react-dom-client.development.js", bytes, ts.ScriptKind.JS), matches = [];
  function visit(node) {
    let value;
    if (ts.isVariableDeclaration(node) && ts.isIdentifier(node.name) && node.name.text === "unitlessNumbers") value = node.initializer;
    else if (ts.isBinaryExpression(node) && ts.isIdentifier(node.left) && node.left.text === "unitlessNumbers") { assert.equal(node.operatorToken.kind, ts.SyntaxKind.EqualsToken, "Closed renderer assignment required"); value = node.right; }
    else { ts.forEachChild(node, visit); return; }
    assert.ok(value && ts.isNewExpression(value) && ts.isIdentifier(value.expression) && value.expression.text === "Set" && !value.typeArguments?.length && value.arguments?.length === 1, "Closed renderer Set initializer required");
    const argument = value.arguments[0];
    assert.ok(ts.isCallExpression(argument) && ts.isPropertyAccessExpression(argument.expression) && argument.expression.name.text === "split" && ts.isStringLiteral(argument.expression.expression) && argument.arguments.length === 1 && ts.isStringLiteral(argument.arguments[0]) && argument.arguments[0].text === " ", "Literal renderer split required");
    matches.push(uniqueList(argument.expression.expression.text.split(" "))); ts.forEachChild(node, visit);
  }
  visit(source); assert.equal(matches.length, 1, "One unambiguous actual renderer unitless declaration required"); return matches[0];
}
export function extractUnitlessPolicy(bytes) {
  const source = parseSource("cssUnits.ts", bytes, ts.ScriptKind.TS), matches = [];
  function visit(node) {
    if (ts.isVariableDeclaration(node) && ts.isIdentifier(node.name) && node.name.text === "UNITLESS_PROPERTIES") {
      assert.ok(node.initializer && ts.isAsExpression(node.initializer) && node.initializer.type.getText(source) === "const" && ts.isArrayLiteralExpression(node.initializer.expression), "Closed readonly policy list required");
      assert.ok(node.initializer.expression.elements.every(ts.isStringLiteral), "Literal policy members required"); matches.push(uniqueList(node.initializer.expression.elements.map((item) => item.text)));
    }
    ts.forEachChild(node, visit);
  }
  visit(source); assert.equal(matches.length, 1, "One unitless policy declaration required"); return matches[0];
}
export function classifyCssValue(checker, value) {
  const type = checker.getTypeAtLocation(value), parts = type.isUnion() ? type.types : [type], kinds = new Set();
  for (const part of parts) {
    if (part.flags & (ts.TypeFlags.Any | ts.TypeFlags.Unknown | ts.TypeFlags.Never | ts.TypeFlags.TypeParameter)) return null;
    if (part.flags & ts.TypeFlags.NumberLike) kinds.add("number");
    else if (part.flags & ts.TypeFlags.StringLike) kinds.add("string");
    else if (part.flags & ts.TypeFlags.Undefined) kinds.add("undefined");
    else return null;
  }
  return [...kinds].sort();
}
export function signedNumericLiteral(value) {
  let sign = 1, node = value;
  if (ts.isPrefixUnaryExpression(node) && [ts.SyntaxKind.PlusToken, ts.SyntaxKind.MinusToken].includes(node.operator)) { sign = node.operator === ts.SyntaxKind.MinusToken ? -1 : 1; node = node.operand; }
  if (!ts.isNumericLiteral(node)) return null;
  const number = sign * Number(node.text); assert.ok(Number.isFinite(number), "Finite numeric literal required"); return number;
}
function importBinding(checker, node, imported, moduleName) {
  const declarations = checker.getSymbolAtLocation(node)?.declarations ?? [];
  return declarations.length === 1 && ts.isImportSpecifier(declarations[0]) && (declarations[0].propertyName ?? declarations[0].name).text === imported && declarations[0].parent.parent.parent.moduleSpecifier.text === moduleName;
}
function removeCssProperty(source, expression, property) {
  const text = source.text, objectStart = expression.getStart(source);
  let start = property.getStart(source), end = property.end + (text[property.end] === "," ? 1 : 0);
  const lineStart = text.lastIndexOf("\n", start - 1) + 1, lineEnd = text.indexOf("\n", end);
  // Remove indentation/newline only when this member owns the whole line.
  // Inline members and adjacent comments keep their original surrounding text.
  if (lineEnd !== -1 && /^[ \t]*$/.test(text.slice(lineStart, start))
    && /^[ \t\r]*$/.test(text.slice(end, lineEnd))) { start = lineStart; end = lineEnd + 1; }
  return { start: start - objectStart, end: end - objectStart, value: "" };
}
function matchesOwner(file, condition) {
  if (file.endsWith("/Alchimie.tsx")) return ts.isPropertyAccessExpression(condition) && ts.isIdentifier(condition.expression) && condition.expression.text === "item" && condition.name.text === "depleted";
  return ts.isBinaryExpression(condition) && condition.operatorToken.kind === ts.SyntaxKind.AmpersandAmpersandToken && ts.isIdentifier(condition.left) && condition.left.text === "actionsLocked" && ts.isPrefixUnaryExpression(condition.right) && condition.right.operator === ts.SyntaxKind.ExclamationToken && ts.isIdentifier(condition.right.operand) && condition.right.operand.text === "isSel";
}
function candidateDiagnostics(program, files, makeHost) {
  const options = program.getCompilerOptions(), host = makeHost(options), consumed = new Set();
  const canonical = (file) => host.getCanonicalFileName(absolutePath(file));
  const texts = new Map(files.map((file) => [canonical(file.absolute), file.text]));
  assert.equal(texts.size, files.length, "Ambiguous canonical candidate paths");
  const read = host.readFile.bind(host), get = host.getSourceFile.bind(host);
  host.readFile = (file) => texts.get(canonical(file)) ?? read(file);
  host.getSourceFile = (file, language, onError, fresh) => {
    const key = canonical(file);
    if (!texts.has(key)) return get(file, language, onError, fresh);
    consumed.add(key); return ts.createSourceFile(file, texts.get(key), language, true, ts.ScriptKind.TSX);
  };
  const result = diagnostics(ts.getPreEmitDiagnostics(ts.createProgram({ rootNames: program.getRootFileNames(), options, host, projectReferences: program.getProjectReferences() })));
  assert.equal(consumed.size, texts.size, "Every transformed candidate must be checked"); return result;
}
function assertOwnerPreserved(source, owner) {
  const matches = [];
  function visit(node) {
    if ((ts.isJsxOpeningElement(node) || ts.isJsxSelfClosingElement(node)) && node.tagName.getText(source) === "CspMotion.button") {
      const attrs = node.attributes.properties, className = attrs.find((attr) => ts.isJsxAttribute(attr) && attr.name.text === "className");
      if (className?.initializer?.getText(source).includes(owner.owner_class)) matches.push(node);
    }
    ts.forEachChild(node, visit);
  }
  visit(source); assert.equal(matches.length, 1, "One converted original owner required");
  for (const before of owner.preserved_attributes) {
    const attr = matches[0].attributes.properties.find((item) => ts.isJsxAttribute(item) && item.name.text === before.name);
    assert.ok(attr && hash(attr.getText(source)) === before.sha256, `Original owner attribute changed: ${before.name}`);
  }
}

export function analyzeStyles(program, { root, unitless, readBytes, makeHost = (options) => ts.createCompilerHost(options, true),
  authoritativeDiagnostics, diagnoseCandidate, owners = ORIGINAL_OWNERS }) {
  // The default is a parser/checker unit or original-profile check. Normalized
  // product diagnostics are supplied solely by the owning native7 CLI below.
  const result = { schema: 2, status: "fail", application_ready: false, diagnostics: authoritativeDiagnostics ?? diagnostics(ts.getPreEmitDiagnostics(program)), candidate_diagnostics: [], sites: [], manual: [], owners: [], proposals: [], files: [] };
  if (result.diagnostics.length) return result;
  const checker = program.getTypeChecker(), units = new Set(uniqueList(unitless)), ownerCounts = Object.fromEntries(Object.keys(owners).map((file) => [file, 0]));
  const sources = program.getSourceFiles().filter((source) => source.fileName.endsWith(".tsx")).map((source) => {
    try { return { source, relative: repoRelative(root, source.fileName) }; }
    catch { result.manual.push({ file: source.fileName, reason: "TSX path escapes repo" }); return null; }
  }).filter((item) => item && item.relative.split("/")[0] === "frontend" && item.relative.split("/")[1] === "src").sort((a, b) => a.relative.localeCompare(b.relative, "en"));
  for (const { source, relative } of sources) {
    const original = readBytes(source.fileName), text = source.text, edits = [], imports = new Set(), removedCasts = [];
    if (original.toString() !== text || text.startsWith("\uFEFF")) { result.manual.push({ file: relative, reason: "Raw/parser source text mismatch or BOM" }); continue; }
    const failuresBefore = result.manual.length, sitesBefore = result.sites.length;
    function visit(node) {
      if (!ts.isJsxAttribute(node) || node.name.text !== "style") { ts.forEachChild(node, visit); return; }
      const opening = node.parent.parent, position = source.getLineAndCharacterOfPosition(node.getStart(source));
      const site = { file: relative, line: position.line + 1, column: position.character + 1, tag: opening.tagName.getText(source), expression_sha256: node.initializer ? hash(node.initializer.getText(source)) : null, values: [] };
      result.sites.push(site); const fail = (reason) => result.manual.push({ file: relative, line: site.line, column: site.column, reason });
      const staged = [], attributes = opening.attributes.properties, names = attributes.filter(ts.isJsxAttribute).map((attr) => attr.name.getText(source));
      if (attributes.some(ts.isJsxSpreadAttribute) || new Set(names).size !== names.length || names.includes("css")) { fail("Spread, duplicate or pre-existing css attributes"); return; }
      let replacement, binding;
      if (ts.isIdentifier(opening.tagName) && nativeTags.has(site.tag)) { replacement = `Csp.${site.tag}`; binding = "Csp"; }
      else if (motionTags.has(site.tag) && ts.isPropertyAccessExpression(opening.tagName) && importBinding(checker, opening.tagName.expression, "m", "framer-motion")) { replacement = site.tag.replace("m.", "CspMotion."); binding = "CspMotion"; }
      else if (ts.isIdentifier(opening.tagName) && site.tag === "Button" && importBinding(checker, opening.tagName, "Button", "@roedu/ui")) { replacement = "CspButton"; binding = "CspButton"; }
      else { fail("Unsupported or ambiguously bound styled tag"); return; }
      if (!node.initializer || !ts.isJsxExpression(node.initializer) || !node.initializer.expression) { fail("Explicit JSX CSS expression required"); return; }
      let expression = node.initializer.expression, cast;
      if (ts.isAsExpression(expression)) {
        if (!ts.isTypeReferenceNode(expression.type) || !ts.isIdentifier(expression.type.typeName) || !importBinding(checker, expression.type.typeName, "CSSProperties", "react")) { fail("Unsupported CSS cast"); return; }
        cast = expression.type; expression = expression.expression;
      }
      if (!ts.isObjectLiteralExpression(expression)) { fail("Literal CSS bag required"); return; }
      const objectEdits = [], keys = new Set(), contextual = checker.getContextualType(expression);
      if (!contextual || contextual.flags & (ts.TypeFlags.Any | ts.TypeFlags.Unknown)) { fail("Resolved CSS property context required"); return; }
      const closedContext = checker.getNonNullableType(contextual);
      if (closedContext.isUnion() || closedContext.isIntersection() || closedContext.flags & (ts.TypeFlags.Any | ts.TypeFlags.Unknown | ts.TypeFlags.TypeParameter)) { fail("Unambiguous CSS property context required"); return; }
      for (const property of expression.properties) {
        if (!ts.isPropertyAssignment(property) || !(ts.isIdentifier(property.name) || ts.isStringLiteral(property.name))) { fail("Unsupported CSS member/spread/computed/accessor"); continue; }
        const key = property.name.text, value = property.initializer;
        if (keys.has(key) || key === "__proto__" || !key.startsWith("--") && !checker.getPropertyOfType(closedContext, key)) { fail(`Duplicate or unsupported CSS property: ${key}`); continue; }
        keys.add(key); const kinds = classifyCssValue(checker, value);
        if (!kinds) { fail(`Uncertain or unsupported CSS value type: ${key}`); continue; }
        if (site.tag === "m.button" && key === "opacity" && Object.hasOwn(owners, relative)) {
          const owner = owners[relative], classAttribute = attributes.find((attr) => ts.isJsxAttribute(attr) && attr.name.text === "className");
          if (!ts.isConditionalExpression(value) || !matchesOwner(relative, value.condition) || signedNumericLiteral(value.whenTrue) !== owner.opacity || signedNumericLiteral(value.whenFalse) !== 1 || !classAttribute?.initializer) { fail("Exact original Motion opacity owner required"); continue; }
          let oldClass;
          if (ts.isStringLiteral(classAttribute.initializer)) oldClass = JSON.stringify(classAttribute.initializer.text);
          else if (ts.isJsxExpression(classAttribute.initializer) && classAttribute.initializer.expression && classifyCssValue(checker, classAttribute.initializer.expression)?.join() === "string") oldClass = classAttribute.initializer.expression.getText(source);
          else { fail("Exact string Motion className required"); continue; }
          staged.push({ start: classAttribute.initializer.getStart(source), end: classAttribute.initializer.end, value: `{(${oldClass}) + (${value.condition.getText(source)} ? " ${owner.className}" : "")}` });
          objectEdits.push(removeCssProperty(source, expression, property));
          site.values.push({ key, decision: "original-class-below-motion-inline", predicate: value.condition.getText(source), className: owner.className });
          site.owner = relative; site.owner_class = owner.className;
          site.preserved_attributes = attributes.filter((attr) => ts.isJsxAttribute(attr) && !["style", "className"].includes(attr.name.text)).map((attr) => ({ name: attr.name.text, sha256: hash(attr.getText(source)) })); continue;
        }
        if (motionTags.has(site.tag) && ["opacity", "transform", "scale"].includes(key)) { fail(`Unreviewed Motion CSS ownership: ${key}`); continue; }
        const literal = kinds.includes("number") ? signedNumericLiteral(value) : null;
        let valueText = value.getText(source), decision = "string-or-undefined";
        if (units.has(key) || key.startsWith("--")) decision = "unitless-or-custom";
        else if (kinds.includes("number")) {
          valueText = literal === null ? `cssLength((${valueText}))` : JSON.stringify(`${literal}px`); decision = "explicit-length";
          if (literal === null) imports.add("cssLength"); objectEdits.push({ start: value.getStart(source) - expression.getStart(source), end: value.end - expression.getStart(source), value: valueText });
        }
        site.values.push({ key, decision, value: value.getText(source), replacement: valueText });
      }
      if (result.manual.some((failure) => failure.file === relative && failure.line === site.line && failure.column === site.column)) return;
      try {
        const object = applyEdits(expression.getText(source), objectEdits);
        staged.push({ start: node.name.getStart(source), end: node.name.end, value: "css" }, { start: node.initializer.getStart(source), end: node.initializer.end, value: `{${object}}` }, { start: opening.tagName.getStart(source), end: opening.tagName.end, value: replacement });
        if (ts.isJsxOpeningElement(opening)) staged.push({ start: opening.parent.closingElement.tagName.getStart(source), end: opening.parent.closingElement.tagName.end, value: replacement });
        applyEdits(text, [...edits, ...staged]); edits.push(...staged); imports.add(binding);
        if (cast) removedCasts.push({ start: cast.getStart(source), end: cast.end });
        if (site.owner) { ownerCounts[site.owner] += 1; result.owners.push(site); }
      } catch (error) { fail(`Invalid or overlapping site edits: ${error.message}`); }
    }
    try { visit(source); } catch (error) { result.manual.push({ file: relative, reason: `Unresolved source analysis: ${error.message}` }); }
    if (result.sites.length === sitesBefore || result.manual.length !== failuresBefore) continue;
    for (const statement of source.statements) {
      if (!ts.isImportDeclaration(statement) || statement.moduleSpecifier.text !== "react" || !statement.importClause?.namedBindings || !ts.isNamedImports(statement.importClause.namedBindings)) continue;
      const named = statement.importClause.namedBindings, removable = [];
      for (const element of named.elements) {
        if ((element.propertyName ?? element.name).text !== "CSSProperties") continue;
        const symbol = checker.getSymbolAtLocation(element.name); let retained = false;
        function uses(node) {
          if (ts.isIdentifier(node) && node !== element.name && checker.getSymbolAtLocation(node) === symbol && !removedCasts.some((range) => node.getStart(source) >= range.start && node.end <= range.end)) retained = true;
          ts.forEachChild(node, uses);
        }
        uses(source); if (!retained) removable.push(element);
      }
      if (!removable.length) continue;
      const elements = named.elements.filter((element) => !removable.includes(element));
      const clause = elements.length || statement.importClause.name ? ts.factory.updateImportClause(statement.importClause, statement.importClause.isTypeOnly, statement.importClause.name, elements.length ? ts.factory.updateNamedImports(named, elements) : undefined) : null;
      edits.push({ start: statement.getStart(source), end: statement.end, value: clause ? ts.createPrinter().printNode(ts.EmitHint.Unspecified, ts.factory.updateImportDeclaration(statement, statement.modifiers, clause, statement.moduleSpecifier, statement.attributes), source) : "" });
    }
    const inScope = new Set(checker.getSymbolsInScope(source, ts.SymbolFlags.Value | ts.SymbolFlags.Type | ts.SymbolFlags.Alias).map((symbol) => symbol.name));
    if ([...imports].some((name) => inScope.has(name))) { result.manual.push({ file: relative, reason: "Generated import binding collision" }); continue; }
    if (source.statements.some((statement) => ts.isExpressionStatement(statement) && ts.isStringLiteral(statement.expression))) { result.manual.push({ file: relative, reason: "Source directive requires explicit import placement review" }); continue; }
    let module = path.posix.relative(path.posix.dirname(relative), "frontend/src/components/CspStyle"); if (!module.startsWith(".")) module = "./" + module;
    edits.push({ start: 0, end: 0, value: `import { ${[...imports].sort().join(", ")} } from ${JSON.stringify(module)};\n` });
    try {
      const converted = applyEdits(text, edits), parsed = parseSource(relative, Buffer.from(converted), ts.ScriptKind.TSX);
      for (const owner of result.owners.filter((item) => item.file === relative)) assertOwnerPreserved(parsed, owner);
      result.files.push({ file: relative, absolute: absolutePath(source.fileName), before_sha256: hash(original), after_sha256: hash(Buffer.from(converted)), text: converted });
    } catch (error) { result.manual.push({ file: relative, reason: `Candidate edit/syntax/owner failure: ${error.message}` }); }
  }
  for (const [file, count] of Object.entries(ownerCounts)) if (count !== 1) result.manual.push({ file, reason: `Exactly one original Motion owner required, observed${count}` });
  if (!result.sites.length) result.manual.push({ reason: "No original style sites discovered" });
  if (!result.manual.length) {
    try { result.candidate_diagnostics = diagnoseCandidate ? diagnoseCandidate(result.files) : candidateDiagnostics(program, result.files, makeHost); }
    catch (error) { result.manual.push({ reason: `Candidate semantic check unresolved: ${error.message}` }); }
  }
  result.proposals = result.files.map(({ text: _text, absolute: _absolute, ...file }) => file);
  if (result.manual.length || result.candidate_diagnostics.length) { result.files = []; return result; }
  result.status = "pass"; result.application_ready = true; return result;
}

function safePath(root, relative) {
  assert.equal(absolutePath(fs.realpathSync(root)), absolutePath(root), "Canonical output root required");
  assert.ok(relative && !relative.includes("\\") && !relative.split("/").some((part) => !part || part === "." || part === ".."), "Literal confined path required");
  assert.ok(!/[\x00-\x1f<>:"|?*]/.test(relative) && !relative.split("/").some((part) => /[. ]$/.test(part) || /^(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)/i.test(part)), "Portable literal path components required");
  const target = path.resolve(root, relative); assert.equal(repoRelative(root, target), relative, "Confined path differs");
  let cursor = root;
  for (const segment of relative.split("/")) {
    cursor = path.join(cursor, segment);
    try { assert.ok(!fs.lstatSync(cursor).isSymbolicLink(), "Symlinked source/output ancestor refused"); }
    catch (error) { if (error.code !== "ENOENT") throw error; }
  }
  return target;
}
function readSafe(root, relative) {
  const file = safePath(root, relative); assert.ok(fs.lstatSync(file).isFile(), "Regular source file required"); return fs.readFileSync(file);
}
function ownStyleRun(root) {
  const id = randomUUID(), relative = `.gate/gen/styles/runs/style-plan-${id}`;
  const parent = safePath(root, ".gate/gen/styles/runs"); fs.mkdirSync(parent, { recursive: true });
  const directory = safePath(root, relative); fs.mkdirSync(directory);
  return { id, relative, directory };
}
function retainedNativeFiles(root, relative) {
  const rows = [], directory = safePath(root, `${relative}/native`);
  if (!fs.existsSync(directory)) return rows;
  function walk(file) {
    const full = safePath(root, file), stat = fs.lstatSync(full);
    if (stat.isDirectory()) for (const child of fs.readdirSync(full).sort()) walk(`${file}/${child}`);
    else { assert.ok(stat.isFile()); const bytes = fs.readFileSync(full); rows.push({ file, bytes: bytes.length, sha256: hash(bytes) }); }
  }
  walk(`${relative}/native`); return rows;
}
function publishOwnedStylePlan(root, plan, bindings, owned) {
  const { id, relative, directory } = owned ?? ownStyleRun(root);
  const report = { ...plan, files: plan.files.map(({ text: _text, absolute: _absolute, ...file }) => file), bindings, plan_id: id, output: relative, converted: null, report_json: `${relative}/report.json`, mode: "source-plan-only-product-files-unmodified" };
  if (bindings.profile === "normalized") report.retained_native_files = retainedNativeFiles(root, relative);
  // Each attempt owns a newly and exclusively created directory. Earlier reports
  // and trees remain immutable history; only this returned run can publish a path.
  fs.writeFileSync(safePath(root, `${relative}/analysis.json`), JSON.stringify({ ...report, application_ready: false }, null, 2) + "\n", { flag: "wx" });
  if (plan.status !== "pass" || !plan.application_ready || plan.manual.length || plan.diagnostics.length || plan.candidate_diagnostics.length) {
    report.status = "fail"; report.application_ready = false; report.files = [];
    fs.writeFileSync(safePath(root, report.report_json), JSON.stringify(report, null, 2) + "\n", { flag: "wx" }); return report;
  }
  try {
    const candidateRelative = `${relative}/candidate`; fs.mkdirSync(safePath(root, candidateRelative));
    for (const file of plan.files) {
      assert.ok(file.file.split("/")[0] === "frontend" && file.file.split("/")[1] === "src" && file.file.endsWith(".tsx"), "Closed candidate source path required");
      const destination = safePath(root, `${candidateRelative}/${file.file}`); assert.ok(repoRelative(directory, destination).split("/")[0] === "candidate", "Exact private run confinement required");
      fs.mkdirSync(path.dirname(destination), { recursive: true }); fs.writeFileSync(destination, file.text, { flag: "wx" });
      assert.equal(hash(fs.readFileSync(destination)), file.after_sha256, "Written candidate bytes differ");
    }
    report.converted = candidateRelative;
    fs.writeFileSync(safePath(root, report.report_json), JSON.stringify(report, null, 2) + "\n", { flag: "wx" }); return report;
  } catch (error) {
    // Partial files and analysis remain failure evidence, without a published path.
    report.status = "fail"; report.application_ready = false; report.files = []; report.converted = null; report.report_json = `${relative}/publication-failure.json`;
    report.manual = [...report.manual, { reason: `Publication failed: ${error.message}` }];
    fs.writeFileSync(safePath(root, report.report_json), JSON.stringify(report, null, 2) + "\n", { flag: "wx" }); return report;
  }
}
export function publishStylePlan(root, plan, bindings = {}, owned) {
  try { return publishOwnedStylePlan(root, plan, bindings, owned); }
  catch (error) {
    // If even a safe report cannot be written, return failure to stdout. Do not
    // retry the unsafe/unwritable path or remove any prior/partial evidence.
    return { ...plan, status: "fail", application_ready: false, files: [], bindings,
      plan_id: null, output: null, converted: null, report_json: null,
      mode: "source-plan-only-product-files-unmodified",
      manual: [...plan.manual, { reason: `Safe report publication unavailable: ${error.message}` }] };
  }
}

export function nativeDiagnosticResult(child) {
  assert.ok(Number.isInteger(child.status), "Native compiler must return an actual exit status");
  assert.ok(!child.error && !child.signal, "Native compiler launch or signal failure");
  const output = `${child.stdout ?? ""}${child.stderr ?? ""}`;
  if (child.status === 0) { assert.equal(output.trim(), "", "Successful native typecheck emitted unexplained output"); return []; }
  assert.ok(output.trim(), "Native compiler refusal must retain diagnostics");
  return [{ code: "native-tsc-exit", category: "Error", compiler: "typescript@7.0.2 native CLI", exit_code: child.status, message: output }];
}
function normalizedBindings(root, bytes, manifest, lock, bindings) {
  for (const [file, expected] of Object.entries(NORMALIZED_INPUTS)) assert.equal(hash(bytes(file)), expected, `Current reviewed normalized input required: ${file}`);
  const selected = JSON.parse(bytes("versions.lock.json")).tools;
  for (const [name, version] of [["react", "19.2.7"], ["react-dom", "19.2.7"], ["motion", "14.0.0"], ["framer-motion", "14.0.0"], ["motion-dom", "14.0.0"], ["typescript", "7.0.2"], ["@typescript/typescript6", "6.0.2"]]) {
    const installed = JSON.parse(bytes(`frontend/node_modules/${name}/package.json`)), locked = lock.packages[`node_modules/${name}`];
    assert.equal(installed.name, name); assert.equal(installed.version, version); assert.equal(locked.version, version);
    if (!["react", "react-dom", "motion-dom"].includes(name)) assert.equal(selected.find((item) => item.tool === name)?.version, version);
    bindings[name] = { version, resolved: locked.resolved, integrity: locked.integrity };
  }
  assert.equal(manifest.dependencies.motion, "14.0.0"); assert.ok(!Object.hasOwn(manifest.dependencies, "framer-motion"));
  assert.equal(manifest.devDependencies.typescript, "7.0.2"); assert.equal(manifest.devDependencies["@typescript/typescript6"], "6.0.2");
  assert.equal(lock.packages["node_modules/motion"].dependencies["framer-motion"], "14.0.0");
  const approval = selected.find((item) => item.tool === "@typescript/typescript6"); assert.equal(approval.status, "optional"); assert.ok(approval.exception && approval.approved_by);
  bindings.parser = parserBinding(path.join(root, "frontend"), ts);
  assert.equal(bindings.parser.package.version, "6.0.2"); assert.equal(bindings.parser.implementation.version, "6.0.3");
  assert.equal(lock.packages["node_modules/@typescript/old"].name, "typescript"); assert.equal(lock.packages["node_modules/@typescript/old"].version, "6.0.3");
  bytes(repoRelative(root, bindings.parser.package.path)); bytes(repoRelative(root, parserEntry));
  bytes(repoRelative(root, bindings.parser.implementation.path)); bytes("frontend/node_modules/@typescript/old/package.json");
  assert.equal(bindings.parser.implementation.entry_sha256, "569177652966bd528c319171c7dd22860dbf72bde116cbc4f644f1d02bb12e39", "Exact approved6.0.3 parser payload required");
  assert.equal(hash(bytes(repoRelative(root, parserEntry))), "d3f3cd2b04b7f466f4484df921b744223f7bd1f3e353ec9110bdf52695b983d5", "Exact published6.0.2 wrapper payload required");
  bindings.parser.locked_implementation = { ...lock.packages["node_modules/@typescript/old"] };
  bindings.native_compiler = nativeCompiler(path.join(root, "frontend"));
  bytes(repoRelative(root, bindings.native_compiler.package.path)); bytes(repoRelative(root, bindings.native_compiler.executable));
  for (const file of ["frontend/node_modules/typescript/lib/tsc.js", "frontend/node_modules/typescript/lib/getExePath.js"]) bytes(file);
  const nativeName = `@typescript/typescript-${process.platform}-${process.arch}`, nativeManifest = `frontend/node_modules/${nativeName}/package.json`;
  const installedNative = JSON.parse(bytes(nativeManifest)); assert.equal(installedNative.name, nativeName); assert.equal(installedNative.version, "7.0.2"); assert.equal(lock.packages[`node_modules/${nativeName}`].version, "7.0.2");
  const nativeExecutable = `frontend/node_modules/${nativeName}/lib/tsc${process.platform === "win32" ? ".exe" : ""}`, nativeBytes = bytes(nativeExecutable);
  bindings.native_payload = { name: nativeName, version: "7.0.2", manifest: nativeManifest, executable: nativeExecutable, executable_sha256: hash(nativeBytes) };
  bindings.native_checks = [];
}
function nativeCheck(root, owned, bindings, role, project) {
  const relative = `${owned.relative}/native/${role}`, cwd = path.join(root, "frontend");
  fs.mkdirSync(safePath(root, relative), { recursive: true });
  const args = ["--project", project, "--noEmit", "--pretty", "false"], started = new Date().toISOString();
  const child = spawnSync(bindings.native_compiler.executable, args, { cwd, encoding: "utf8", maxBuffer: 32 * 1024 * 1024 });
  const record = { role, compiler: "typescript@7.0.2 native CLI", command: bindings.native_compiler.executable, args, cwd: "frontend", started, finished: new Date().toISOString(), exit_code: child.status,
    ...(child.error ? { error: child.error.message } : {}), ...(child.signal ? { signal: child.signal } : {}) };
  for (const stream of ["stdout", "stderr"]) {
    const data = Buffer.from(child[stream] ?? ""), file = `${relative}/${stream}.log`;
    fs.writeFileSync(safePath(root, file), data, { flag: "wx" }); record[stream] = { file, bytes: data.length, sha256: hash(data) };
  }
  fs.writeFileSync(safePath(root, `${relative}/command.json`), JSON.stringify(record, null, 2) + "\n", { flag: "wx" });
  bindings.native_checks.push(record); return nativeDiagnosticResult(child);
}
function candidateProject(root, owned, files, bytes) {
  const graph = `${owned.relative}/native/candidate-graph`, replacements = new Map(files.map((file) => [file.file, file]));
  const copied = new Set();
  function copy(relative) {
    const data = bytes(relative), replacement = replacements.get(relative), output = replacement ? Buffer.from(replacement.text) : data;
    if (replacement) { assert.equal(hash(data), replacement.before_sha256); assert.equal(hash(output), replacement.after_sha256); }
    const destination = safePath(root, `${graph}/${relative}`); fs.mkdirSync(path.dirname(destination), { recursive: true }); fs.writeFileSync(destination, output, { flag: "wx" }); copied.add(relative);
  }
  function walk(relative, declarationsOnly = false) {
    const file = safePath(root, relative), stat = fs.lstatSync(file);
    if (stat.isDirectory()) for (const name of fs.readdirSync(file).sort()) { if (declarationsOnly && name === ".bin") continue; walk(`${relative}/${name}`, declarationsOnly); }
    else { assert.ok(stat.isFile(), "Private compiler graph cannot contain aliases or nonregular files"); if (!declarationsOnly || /\.(?:json|[cm]?tsx?)$/.test(relative)) copy(relative); }
  }
  walk("frontend/src"); walk("frontend/node_modules", true);
  for (const file of ["frontend/package.json", "frontend/package-lock.json", "frontend/tsconfig.json", "frontend/vite.config.ts", "frontend/tsconfig.tools.json", "frontend/scripts/gui-sdk-allocation-plugin.mts", "frontend/scripts/native-tsc.mjs"]) copy(file);
  assert.ok(files.every((file) => copied.has(file.file)), "All candidate sources must enter the native compiler graph");
  return safePath(root, `${graph}/frontend/tsconfig.json`);
}
function bindNativeProjectInputs(root, bytes) {
  function walk(relative, declarationsOnly = false) {
    const file = safePath(root, relative), stat = fs.lstatSync(file);
    if (stat.isDirectory()) for (const name of fs.readdirSync(file).sort()) { if (declarationsOnly && name === ".bin") continue; walk(`${relative}/${name}`, declarationsOnly); }
    else { assert.ok(stat.isFile(), "Native source/declaration/package input must be regular"); if (!declarationsOnly || /\.(?:json|[cm]?tsx?)$/.test(relative)) bytes(relative); }
  }
  walk("frontend/src"); walk("frontend/node_modules", true);
  for (const file of ["frontend/vite.config.ts", "frontend/tsconfig.tools.json", "frontend/scripts/gui-sdk-allocation-plugin.mts", "frontend/scripts/native-tsc.mjs"]) bytes(file);
}

export function main(profile = "original") {
  const root = fs.realpathSync(process.cwd()), bindings = {}, empty = { schema: 2, status: "fail", application_ready: false, diagnostics: [], candidate_diagnostics: [], sites: [], manual: [], owners: [], proposals: [], files: [] };
  let owned;
  try {
    assert.ok(["original", "normalized"].includes(profile), "Explicit known style profile required");
    if (profile === "normalized") { bindings.profile = profile; owned = ownStyleRun(root); }
    assert.match(process.env.GATE_SHA ?? "", /^(?:[a-f0-9]{40}|[a-f0-9]{64})$/, "Actual wrapper source identity required");
    assert.match(process.env.GATE_TREE_SHA256 ?? "", /^[a-f0-9]{64}$/, "Actual wrapper tree identity required");
    assert.match(process.env.TOOLCHAIN_DIGEST ?? "", /^sha256:[a-f0-9]{64}$/, "Actual toolchain identity required");
    bindings.sha = process.env.GATE_SHA; bindings.tree_sha256 = process.env.GATE_TREE_SHA256; bindings.toolchain_digest = process.env.TOOLCHAIN_DIGEST; bindings.inputs = {};
    const bytes = (file) => bindSourceInput(bindings.inputs, file, readSafe(root, file));
    if (profile === "normalized") {
      const request = JSON.parse(bytes("scripts/gui-gen-request.json"));
      assert.deepEqual(request, { schema: 1, operation: "plan-normalized-styles", fixtures: "frontend/e2e/original/runtime.spec.mjs" });
      const descriptorBytes = bytes(".gate/wrapper-current.json"), descriptor = JSON.parse(descriptorBytes);
      assert.equal(descriptor.target, "gen"); assert.equal(descriptor.sha, bindings.sha); assert.equal(descriptor.tree_sha256, bindings.tree_sha256); assert.equal(descriptor.toolchain_digest, bindings.toolchain_digest);
      assert.deepEqual(bytes(".gate/gen/wrapper-current.json"), descriptorBytes); assert.equal(descriptor.config_path, ".gate/gen/wrapper-kit-config.json");
      const configBytes = bytes(descriptor.config_path), frozenConfig = JSON.parse(configBytes); assert.equal(hash(configBytes), descriptor.config_file_sha256);
      assert.equal(hash(JSON.stringify(frozenConfig.config)), descriptor.config_sha256);
      const phase = frozenConfig.config.ui_adoption; assert.equal(phase?.mode, "staged-react"); assert.equal(phase.until, "S1-M2"); assert.equal(phase.legacy.version, "0.3.0");
      assert.equal(phase.legacy.archive_sha256, "1934a81cdfd737a051f591ebcae072f5028943b715456dbb2899b483d399c244"); assert.equal(hash(bytes(phase.legacy.receipt)), phase.legacy.receipt_sha256);
    }
    assert.equal(hash(bytes("frontend/src/components/CspStyle.ts")), "2ea61764325b4cb9ecd036d106466594d0f32f2f6d83b09a547981c0317fa320", "Exact reviewed CSP facade source required");
    assert.equal(hash(bytes("frontend/src/components/CspElements.tsx")), profile === "normalized" ? "f1c5478b8d243223d16baedb9fc6f0ced38f073377e0d7393e252b5a598b32c3" : "27cf738b5af8a4e4eefab89b513d941261b61d0d41813eca09618ea8a8ef881d", "Exact reviewed CSP component source required");
    const manifestBytes = bytes("frontend/package.json"), lockBytes = bytes("frontend/package-lock.json"), manifest = JSON.parse(manifestBytes), lock = JSON.parse(lockBytes);
    if (profile === "original") {
      assert.equal(hash(manifestBytes), "efde2d3fbdebc5899dc63ca6b518cab0d60370ef36a7301477da720f4978e2e9", "Original frontend manifest bytes required");
      assert.equal(hash(lockBytes), "f72661b4bd7ad129a6771037bf900a616a0fdf84bbb41f70c6d118b69fb1b62c", "Original frontend lock bytes required");
    }
    assert.equal(manifest.dependencies["@roedu/ui"], "file:vendor/roedu-ui-0.3.0.tgz");
    assert.equal(hash(bytes("frontend/vendor/roedu-ui-0.3.0.tgz")), "1934a81cdfd737a051f591ebcae072f5028943b715456dbb2899b483d399c244", "Original SDK bytes required");
    if (profile === "normalized") normalizedBindings(root, bytes, manifest, lock, bindings);
    else for (const [name, version] of [["react-dom", "19.2.7"], ["typescript", "5.9.3"]]) {
      const installed = JSON.parse(bytes(`frontend/node_modules/${name}/package.json`));
      assert.equal(installed.name, name); assert.equal(installed.version, version); assert.equal(lock.packages[`node_modules/${name}`].version, version);
      bindings[name] = { version: installed.version, resolved: lock.packages[`node_modules/${name}`].resolved, integrity: lock.packages[`node_modules/${name}`].integrity };
    }
    if (profile === "original") { assert.equal(ts.version, bindings.typescript.version); bytes("frontend/node_modules/typescript/lib/typescript.js"); }
    assert.equal(absolutePath(fs.realpathSync(fileURLToPath(import.meta.url))), absolutePath(fs.realpathSync(safePath(root, "scripts/gui-style-plan.mjs"))), "Executing planner must be the bound repository script");
    const scriptBytes = bytes("scripts/gui-style-plan.mjs"); assert.equal(hash(scriptBytes), hash(fs.readFileSync(fileURLToPath(import.meta.url))), "Executing planner bytes differ");
    const renderer = extractRendererUnitless(bytes("frontend/node_modules/react-dom/cjs/react-dom-client.development.js"));
    const policy = extractUnitlessPolicy(bytes("frontend/src/components/cssUnits.ts")); assert.deepEqual(policy, renderer, "Policy must equal actual pinned renderer");
    let frozen;
    if (profile === "normalized") {
      bytes("scripts/gui-style-operation.mjs");
      const archived = readNormalizedFrozenRenderer(bytes); frozen = archived.bytes; bindings.frozen_renderer = archived.binding;
    } else { frozen = bytes("cat_de_roman_esti/web/static/assets/index-qYTSE3Vo.js"); assert.equal(hash(frozen), "3aeceaed54e6d8614fa85e68bcf2a5c6ab1a7619bf20f7184624d475259be93a"); }
    const frozenList = frozen.toString().match(/animationIterationCount.{0,1800}WebkitLineClamp/g); assert.equal(frozenList?.length, 1); assert.deepEqual(policy, frozenList[0].split(" "), "Exact original frozen renderer policy required");
    const owners = Object.fromEntries(Object.entries(ORIGINAL_OWNERS).map(([file, owner]) => {
      const actual = hash(bytes(file));
      if (profile === "original") assert.equal(actual, owner.source_sha256, "Exact original Motion owner source bytes required");
      return [file, { ...owner, source_sha256: actual }];
    }));
    if (profile === "normalized") bindings.current_owners = owners;
    const configBytes = bytes("frontend/tsconfig.json");
    assert.equal(hash(configBytes), profile === "normalized" ? NORMALIZED_INPUTS["frontend/tsconfig.json"] : "81dbe0e79cad7363ee3e83e4683cb5f382560608a592b91b5f0f903f2385b963", "Exact owning semantic config bytes required");
    const configFile = path.join(root, "frontend/tsconfig.json"), read = ts.readConfigFile(configFile, () => configBytes.toString());
    const parsed = read.error ? null : ts.parseJsonConfigFileContent(read.config, ts.sys, path.join(root, "frontend"));
    if (read.error || parsed.errors.length) return publishStylePlan(root, { ...empty, ...(profile === "normalized" ? { manual: [{ reason: "AST parser cannot resolve the owning config", parser_diagnostics: diagnostics(read.error ? [read.error] : parsed.errors) }] } : { diagnostics: diagnostics(read.error ? [read.error] : parsed.errors) }) }, bindings, owned);
    assert.equal(parsed.options.strict, true); assert.equal(parsed.options.noUnusedLocals, true); assert.equal(parsed.options.noUnusedParameters, true); assert.ok(!parsed.options.noCheck, "Semantic diagnostics cannot be disabled");
    if (profile === "normalized") bindNativeProjectInputs(root, bytes);
    const authoritativeDiagnostics = profile === "normalized" ? nativeCheck(root, owned, bindings, "before", safePath(root, "frontend/tsconfig.json")) : undefined;
    const program = ts.createProgram(parsed.fileNames, parsed.options), plan = analyzeStyles(program, { root, unitless: policy, owners, authoritativeDiagnostics,
      readBytes: (file) => bytes(repoRelative(root, file)), ...(profile === "normalized" ? { diagnoseCandidate: (files) => nativeCheck(root, owned, bindings, "candidate", candidateProject(root, owned, files, bytes)) } : {}) });
    return publishStylePlan(root, plan, bindings, owned);
  } catch (error) { return publishStylePlan(root, { ...empty, manual: [{ reason: error.message }] }, bindings, owned); }
}

if (process.argv[1] && absolutePath(path.resolve(process.argv[1])) === absolutePath(fileURLToPath(import.meta.url))) {
  const report = main(process.argv[2] ?? "original"); process.stdout.write(JSON.stringify({ ...report, sites: undefined, files: undefined, owners: undefined }, null, 2) + "\n"); process.exitCode = report.status === "pass" && report.application_ready ? 0 : 1;
}
