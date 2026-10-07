import { lstatSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { isDeepStrictEqual } from 'node:util';
import { localPath, posix, readJSON, validateConfig, walkRepository } from '../lint/validation-files.mjs';
import { bannedName, finish, loadScope, sourceFindings, taskConfig, tokens } from '../lint/lint-scope.mjs';
import { checkVersions } from './versions-check.mjs';

const check = (value, message) => { if (!value) throw new Error(message); };
const hash = value => createHash('sha256').update(value).digest('hex');
const languages = new Set(['JavaScript', 'TypeScript', 'Tsx', 'Html', 'Go']);
const types = ['hidden', 'dot', 'exclude', 'global', 'parent', 'vcs'];
const languageOf = path => /\.[cm]?jsx?$/.test(path) ? 'JavaScript' : /\.[cm]?ts$/.test(path) ? 'TypeScript' : /\.tsx$/.test(path) ? 'Tsx' : /\.(?:html|htm|xhtml)$/.test(path) ? 'Html' : /\.go$/.test(path) ? 'Go' : null;
const packageOf = name => name.split('/').slice(0, name.startsWith('@') ? 2 : 1).join('/');
const imports = new Set(['import-source', 'import-call']);
const unique = values => [...new Map(values.map(value => [JSON.stringify(value), value])).values()];

function trustedRules() {
  const directory = resolve(dirname(fileURLToPath(import.meta.url)), '../lint/ast');
  check(lstatSync(directory).isDirectory() && !lstatSync(directory).isSymbolicLink(), 'AST rules must be a real directory');
  const manifestPath = join(directory, 'manifest.json');
  check(lstatSync(manifestPath).isFile() && !lstatSync(manifestPath).isSymbolicLink(), 'AST manifest must be a regular file');
  const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
  check(manifest.schema === 1 && Array.isArray(manifest.rules) && manifest.rules.length, 'nonempty AST manifest required');
  const rulesDirectory = join(directory, 'rules');
  check(lstatSync(rulesDirectory).isDirectory() && !lstatSync(rulesDirectory).isSymbolicLink(), 'AST rule directory must be real');
  const ids = new Map(), documents = [], names = new Set();
  for (const item of manifest.rules) {
    check(item && Object.keys(item).sort().join(',') === 'check,file,id,language' && /^[a-zA-Z][a-zA-Z0-9-]*\.yml$/.test(item.file) && languages.has(item.language) && !ids.has(item.id), 'invalid or duplicate trusted AST rule');
    const path = join(directory, 'rules', item.file), stat = lstatSync(path);
    check(stat.isFile() && !stat.isSymbolicLink(), 'AST rule must be a regular file');
    const document = JSON.parse(readFileSync(path, 'utf8'));
    check(document.id === item.id && document.language === item.language && document.severity === 'error' && document.rule && !('fix' in document) && !('files' in document) && !('ignores' in document), 'AST rule identity or severity differs');
    ids.set(item.id, item); names.add(item.file); documents.push(document);
  }
  check(isDeepStrictEqual([...names].sort(), readdirSync(join(directory, 'rules')).sort()), 'unknown AST rule file');
  for (const language of languages) check([...ids.values()].some(item => item.language === language && item.check === 'coverage'), `AST coverage rule missing: ${language}`);
  return { ids, text: documents.map(document => JSON.stringify(document)).join('\n---\n'), sha256: hash(JSON.stringify(documents)) };
}

function temporary(root, name) {
  const directory = localPath(root, `.gate/${name}`, false);
  mkdirSync(directory, { recursive: true });
  check(lstatSync(directory).isDirectory() && !lstatSync(directory).isSymbolicLink(), 'AST scratch must be a real directory');
  return mkdtempSync(join(directory, 'run-'));
}

// A native suppression comment must not hide the AST finding. Substituting
// ASCII characters of equal length preserves byte offsets and syntax. Original
// source slices, rather than the substituted copy, supply every diagnostic.
function scanCopy(text) { return text.replace(/ast-grep-ignore/g, 'ast_grep_ignore'); }

const SHIM_WARNING = '[warn] postinstall script did not run; falling back to runtime binary resolution.\nEnable postinstall to avoid the per-invocation overhead.\n';
const SUMMARY_HELP = 'Help: Scan succeeded and found error level diagnostics in the codebase.';
/** Pinned CLI protocol, not a blanket stderr exemption. Coverage/comment/import
 * probes are error-severity rows too. Native count, JSON rows and exit must agree.
 * The exact optional notice was confirmed in the installed 0.45.3 npm shim.
 * Primary semantics: https://ast-grep.github.io/reference/cli/scan.html and
 * https://github.com/ast-grep/ast-grep/blob/main/crates/cli/src/utils/error_context.rs
 */
export function parseScanOutput(result) {
  check(!result.error && result.signal === null && [0, 1].includes(result.status), `ast-grep execution failed: ${result.error?.message ?? result.signal ?? result.status}; ${result.stderr?.trim() ?? ''}`);
  check(typeof result.stdout === 'string' && typeof result.stderr === 'string', 'ast-grep output streams must be text');
  let rows;
  try { rows = JSON.parse(result.stdout); } catch { throw new Error('ast-grep stdout is not a JSON array'); }
  check(Array.isArray(rows) && rows.every(row => row && typeof row === 'object' && !Array.isArray(row) && row.severity === 'error'), 'ast-grep stdout must contain only error-severity match objects');
  check(result.status === (rows.length ? 1 : 0), 'ast-grep exit status disagrees with error-severity matches');
  // Pinned ErrorFormat uses writeln! plus eprintln!: exactly two final LF.
  // Only the exact optional npm notice is removed; no boundary trimming.
  let diagnostic = result.stderr, shimWarning = false, summaryCount = 0;
  if (diagnostic.startsWith(SHIM_WARNING)) { diagnostic = diagnostic.slice(SHIM_WARNING.length); shimWarning = true; }
  if (rows.length) {
    const lines = diagnostic.split('\n');
    const count = lines.length === 4 && /^Error: ([1-9][0-9]*) error\(s\) found in code\.$/.exec(lines[0]);
    check(count && lines[1] === SUMMARY_HELP && lines[2] === '' && lines[3] === '', `ast-grep emitted unexpected diagnostics: ${JSON.stringify(result.stderr)}`);
    summaryCount = Number(count[1]);
    check(Number.isSafeInteger(summaryCount) && summaryCount === rows.length, 'ast-grep diagnostic summary count disagrees with JSON error rows');
  } else check(diagnostic === '', `ast-grep emitted unexpected diagnostics: ${JSON.stringify(result.stderr)}`);
  return { rows, diagnostics: { shim_warning: shimWarning, error_summary_count: summaryCount } };
}
function nativeCapture(root) {
  // Existing wrapper-owned app URL identifies full; no new CLI/env contract.
  const target = process.env.GATE_APP_URL ? 'full' : 'unit';
  const base = localPath(root, `.gate/${target}/ast-native`, false);
  mkdirSync(base, { recursive: true });
  check(lstatSync(base).isDirectory() && !lstatSync(base).isSymbolicLink(), 'AST evidence must be a real directory');
  return { root, directory: mkdtempSync(join(base, 'scan-')), artifacts: [] };
}
function invocation(args, cwd, capture) {
  const started = Date.now();
  const result = spawnSync('ast-grep', args, { cwd, maxBuffer: 32 * 1024 * 1024, timeout: 120000 });
  const stdout = result.stdout ?? Buffer.alloc(0), stderr = result.stderr ?? Buffer.alloc(0);
  const number = String(capture.artifacts.length / 3).padStart(4, '0');
  const receipt = { command: 'ast-grep', args_sha256: hash(JSON.stringify(args)), exit_code: result.status, signal: result.signal, duration_ms: Date.now() - started, stdout_sha256: hash(stdout), stderr_sha256: hash(stderr), ...(result.error ? { launch_error: { code: result.error.code ?? null, message: result.error.message } } : {}) };
  // Save actual bytes and native outcome before ANY parser/row validation.
  for (const [name, bytes] of [[`${number}.stdout.json`, stdout], [`${number}.stderr.log`, stderr], [`${number}.receipt.json`, Buffer.from(JSON.stringify({ schema: 1, sha: process.env.GATE_SHA, tree_sha256: process.env.GATE_TREE_SHA256, ...(process.env.GATE_APP_IMAGE_ID ? { app_image_id: process.env.GATE_APP_IMAGE_ID } : {}), ...receipt }, null, 2) + '\n')]]) {
    const file = join(capture.directory, name); writeFileSync(file, bytes, { flag: 'wx', mode: 0o600 });
    capture.artifacts.push(`${posix(relative(capture.root, file))} sha256:${hash(bytes)}`);
  }
  const text = { ...result, stdout: stdout.toString('utf8'), stderr: stderr.toString('utf8') };
  check(stdout.equals(Buffer.from(text.stdout)) && stderr.equals(Buffer.from(text.stderr)), 'AST native output is not valid UTF-8');
  const { rows, diagnostics } = parseScanOutput(text);
  return { rows, receipt: { ...receipt, matches: rows.length, diagnostics, stdout_path: posix(relative(capture.root, join(capture.directory, `${number}.stdout.json`))), stderr_path: posix(relative(capture.root, join(capture.directory, `${number}.stderr.log`))), native_receipt_path: posix(relative(capture.root, join(capture.directory, `${number}.receipt.json`))) } };
}

function finding(rule, tool, path, match, scopable = false) {
  return { rule, tool_or_import: tool, paths: [path], scopable, ast: { rule_id: match.ruleId, line: match.range.start.line + 1, column: match.range.start.column + 1 } };
}

function importedName(kind, text) {
  const ts = tokens(text);
  if (kind === 'import-source') return ts.length === 1 && ts[0].kind === 'string' ? ts[0].value : null;
  return ['import', 'require'].includes(ts[0]?.value) && ts[1]?.value === '(' && ts[2]?.kind === 'string' ? ts[2].value : null;
}

export function scanAst({ root, config, files, entries, capture }) {
  root = resolve(root); validateConfig(root, config);
  const rules = trustedRules(), selected = files.filter(path => languageOf(path));
  check(selected.length, 'no source files qualified for AST checking');
  capture ??= nativeCapture(root);
  const scratch = temporary(root, 'ast'), mirror = join(scratch, 'mirror'), originals = new Map(), findings = [], commands = [], covered = new Map(), scriptRegions = new Map(), injectedCoverage = [];
  try {
    for (const path of selected) {
      const bytes = readFileSync(localPath(root, path)), text = bytes.toString('utf8'), destination = join(mirror, path);
      check(bytes.equals(Buffer.from(text)), `AST source is not valid UTF-8: ${path}`);
      mkdirSync(dirname(destination), { recursive: true });
      writeFileSync(destination, scanCopy(text)); originals.set(path, bytes);
    }
    // Explicit paths and every documented --no-ignore class prohibit repository,
    // parent, global, hidden and VCS ignore configuration from changing coverage.
    for (let start = 0; start < selected.length; start += 64) {
      const batch = selected.slice(start, start + 64);
      const args = ['scan', '--inline-rules', rules.text, '--json=compact', '--color=never', '--threads', '1', '--error', ...types.flatMap(type => ['--no-ignore', type]), '--', ...batch];
      const result = invocation(args, mirror, capture); commands.push(result.receipt);
      for (const match of result.rows) {
        const path = typeof match.file === 'string' ? posix(relative(mirror, resolve(mirror, match.file))) : '';
        const item = rules.ids.get(match.ruleId), bytes = originals.get(path), offset = match.range?.byteOffset;
        check(item && bytes && batch.includes(path) && match.language === item.language && match.severity === 'error' && typeof match.message === 'string' && typeof match.text === 'string', 'unknown AST match, source, language or severity');
        check(offset && Number.isSafeInteger(offset.start) && Number.isSafeInteger(offset.end) && offset.start >= 0 && offset.end >= offset.start && offset.end <= bytes.length, 'invalid AST byte range');
        check(['start', 'end'].every(key => Number.isSafeInteger(match.range?.[key]?.line) && match.range[key].line >= 0 && Number.isSafeInteger(match.range[key].column) && match.range[key].column >= 0), 'invalid AST source position');
        const text = bytes.subarray(offset.start, offset.end).toString('utf8');
        check(scanCopy(text) === match.text, 'AST match text differs from the actual source slice');
        if (item.check === 'script-region') {
          check(languageOf(path) === 'Html' && item.language === 'Html', 'HTML script probe has an unexpected host language');
          const regions = scriptRegions.get(path) ?? [];
          check(!regions.some(region => region.start === offset.start && region.end === offset.end), 'duplicate trusted HTML script region');
          regions.push({ start: offset.start, end: offset.end }); scriptRegions.set(path, regions); continue;
        }
        if (item.check === 'coverage') {
          if (languageOf(path) === item.language) {
            check(offset.start === 0, 'outer AST parser root does not start at the actual file boundary');
            if (item.language === 'Html') check(offset.end === bytes.length, 'outer HTML document does not cover the complete actual source');
            covered.set(path, (covered.get(path) ?? 0) + 1);
          } else injectedCoverage.push({ path, language: item.language, start: offset.start, end: offset.end });
          continue;
        }
        if (item.check === 'comments') {
          if (/\b(?:ast-grep|sg)-(?:ignore|disable)\b/.test(text)) findings.push(finding('inline-disable', 'AST suppression comment', path, match));
          continue;
        }
        if (imports.has(item.check)) {
          const name = importedName(item.check, text), entry = name && entries.get(packageOf(name));
          if (name && (bannedName(name) || ['banned', 'transitive-only'].includes(entry?.status))) findings.push(finding('banned-imports', name, path, match, bannedName(name)));
          continue;
        }
        if (item.check === 'v11-identifiers') { findings.push(finding(text, text, path, match)); continue; }
        if (item.check === 'v11-computed') {
          const name = tokens(text).find(token => token.kind === 'string' && ['forwardRef', 'defaultProps'].includes(token.value))?.value;
          check(name, 'unknown computed v11 match'); findings.push(finding(name, name, path, match)); continue;
        }
        const tool = { 'useRef-initial': 'useRef()', 'JSX-types': 'JSX.HTMLAttributes', 'Component-base': text, 'inline-style': 'style=', 'inline-handler': 'on*=', 'templ-SafeURL': 'templ.SafeURL(' }[item.check];
        check(tool, `unknown AST check ${item.check}`); findings.push(finding(item.check, tool, path, match));
      }
    }
    // Native HTML injection creates program roots with host-file byte offsets.
    // Validate them against actual raw_text-in-script AST probes, independently
    // of the exactly-once outer document/program/source_file coverage inventory.
    const injectedSeen = new Set();
    for (const injected of injectedCoverage) {
      check(languageOf(injected.path) === 'Html' && ['JavaScript', 'TypeScript', 'Tsx'].includes(injected.language) && injected.start > 0, 'unexpected injected coverage language or host');
      const regions = (scriptRegions.get(injected.path) ?? []).filter(region => injected.start >= region.start && injected.end <= region.end);
      check(regions.length === 1, 'injected parser root is outside a unique trusted HTML script region');
      const key = `${injected.path}:${injected.language}:${injected.start}:${injected.end}`;
      check(!injectedSeen.has(key), 'duplicate injected parser root'); injectedSeen.add(key);
      injected.script_start = regions[0].start; injected.script_end = regions[0].end;
    }
    check(selected.every(path => covered.get(path) === 1), 'ast-grep did not parse every explicit source file exactly once');
    return { findings: unique(findings), receipt: { rules_sha256: rules.sha256, source_files: selected.length, files: selected.map(path => ({ path, language: languageOf(path), sha256: hash(originals.get(path)), coverage: covered.get(path) })), commands, injected_coverage: injectedCoverage, script_regions: [...scriptRegions].flatMap(([path, regions]) => regions.map(region => ({ path, ...region }))), artifacts: capture.artifacts } };
  } catch (error) { error.astArtifacts = capture.artifacts; throw error; }
  finally { rmSync(scratch, { recursive: true, force: true }); }
}

export async function checkAst({ root = process.cwd(), config }) {
  root = resolve(root); config ??= taskConfig(root);
  const { files } = walkRepository(root, config), lock = readJSON(root, 'versions.lock.json');
  check(Array.isArray(lock.tools), 'AST check needs the actual versions lock');
  const ast = scanAst({ root, config, files, entries: new Map(lock.tools.map(entry => [entry.tool, entry])) });
  // The full lexical/package/compat collection and the AST findings enter the
  // same finish() call. A second scope evaluation would falsely stale entries.
  const result = await checkVersions({ root, config, lintOnly: true, additionalFindings: ast.findings });
  check(result.schema === 1 && ['pass', 'fail'].includes(result.status) && Array.isArray(result.errors) && Array.isArray(result.legacy_pending), 'invalid shared lint result');
  return { ...result, check: 'v11-lint', ast: ast.receipt, artifacts: ast.receipt.artifacts };
}

export function astSelfTest(root = process.cwd()) {
  root = resolve(root); const directory = temporary(root, 'ast-fixtures');
  const assertions = [], commands = [], capture = nativeCapture(root);
  const assert = (name, ok) => { check(ok, `AST fixture failed: ${name}`); assertions.push({ name, status: 'pass' }); };
  const write = (path, text) => { const target = join(directory, path); mkdirSync(dirname(target), { recursive: true }); writeFileSync(target, text); };
  const config = { role: 'consumer', app: 'ast-fixture', npm_dir: 'kit-package', vendor_dir: 'frontend/vendor', go_dirs: ['server'] };
  const entries = new Map([['motion-utils', { status: 'transitive-only' }], ['legacy-banned', { status: 'banned' }]]);
  try {
    const probe = { severity: 'error', ruleId: 'probe' };
    const summary = count => `Error: ${count} error(s) found in code.\n${SUMMARY_HELP}\n\n`;
    const native = (rows, stderr, status = rows.length ? 1 : 0) => ({ stdout: JSON.stringify(rows), stderr, status, signal: null });
    assert('native diagnostic count includes coverage probes without claiming policy failure', parseScanOutput(native([probe], summary(1))).diagnostics.error_summary_count === 1);
    assert('pinned npm fallback notice is retained explicitly', parseScanOutput(native([probe], SHIM_WARNING + summary(1))).diagnostics.shim_warning === true);
    assert('exact writeln plus eprintln native boundary is accepted', parseScanOutput(native([probe], SHIM_WARNING + summary(1))).diagnostics.error_summary_count === 1);
    assert('empty native result accepts only zero exit and no diagnostic summary', parseScanOutput(native([], '')).diagnostics.error_summary_count === 0 && parseScanOutput(native([], SHIM_WARNING)).diagnostics.shim_warning === true);
    for (const [name, result] of [
      ['wrong native count', native([probe], summary(2))],
      ['extra final LF', native([probe], summary(1) + '\n')],
      ['missing final LF', native([probe], summary(1).slice(0,-1))],
      ['leading LF', native([probe], '\n' + SHIM_WARNING + summary(1))],
      ['blank between notice and summary', native([probe], SHIM_WARNING + '\n' + summary(1))],
      ['unknown warning', native([probe], '[warn] arbitrary warning\n' + summary(1))],
      ['CRLF boundary', native([probe], summary(1).replaceAll('\n', '\r\n'))],
      ['space boundary', native([probe], ' ' + summary(1))],
      ['internal blank line', native([probe], summary(1).replace('\nHelp:', '\n\nHelp:'))],
      ['Rust chained diagnostic', native([probe], summary(1) + '\nCaused by missing source\n')],
      ['duplicated fallback notice', native([probe], SHIM_WARNING + SHIM_WARNING + summary(1))],
      ['extra diagnostic after valid summary', native([probe], summary(1) + 'Error: failed to read a source file\n')],
      ['missing summary', native([probe], '')],
      ['empty rows with nonzero exit', native([], summary(1), 1)],
      ['nonempty rows with zero exit', native([probe], summary(1), 0)],
      ['unexpected native exit', native([probe], summary(1), 8)],
      ['unexpected match severity', native([{ ...probe, severity: 'warning' }], summary(1))],
      ['malformed JSON', { ...native([probe], summary(1)), stdout: '[' }],
      ['native signal', { ...native([probe], summary(1)), signal: 'SIGTERM' }],
      ['native launch error', { ...native([probe], summary(1)), error: Error('ENOENT') }],
    ]) {
      let refused = false; try { parseScanOutput(result); } catch { refused = true; }
      assert(`strict native output refuses ${name}`, refused);
    }
    write('kit-package/package.json', '{}\n'); write('frontend/package.json', '{}\n'); write('server/go.mod', 'module example.test/ast\n');
    write('src/good.tsx', "import {useRef} from 'preact/hooks';\nimport type * as preact from 'preact';\nconst message=\"import React from 'react'; ast-grep-ignore\";\n// import React from 'react'; useRef(); forwardRef; defaultProps;\nexport function Valid(props: preact.ButtonHTMLAttributes<HTMLButtonElement>){const ref=useRef<HTMLButtonElement>(null);return <button ref={ref} onClick={() => {}} aria-label='valid'/>;}\nexport const Bridge=()=> <Button style={{color:'red'}}/>;\n");
    write('src/good.js', "import {h} from 'preact'; export const element=<button onClick={() => {}}/>;\n");
    write('src/good.html', '<button id="ok">Valid</button>\n');
    write('server/good.go', 'package ast\nfunc valid() {}\n');
    const scan = paths => { const result = scanAst({ root: directory, config, files: paths, entries, capture }); commands.push(...result.receipt.commands); return result.findings; };
    assert('preact callbacks, initialized refs, bridge style props and comment/string data are valid', scan(['src/good.tsx', 'src/good.js', 'src/good.html', 'server/good.go']).length === 0);
    write('src/mixed.html', `<div>Host document</div>
<script type="application/json">{"value":45,"snippet":"import React from 'react';"}</script>
<script>
const safe = 1;
</script>
`);
    const mixedDocument = scanAst({ root: directory, config, files: ['src/mixed.html'], entries, capture }); commands.push(...mixedDocument.receipt.commands);
    assert('HTML outer document remains exactly once alongside JSON and JS injected roots', mixedDocument.findings.length === 0 && mixedDocument.receipt.files.length === 1 && mixedDocument.receipt.files[0].coverage === 1 && mixedDocument.receipt.injected_coverage.length === 2 && mixedDocument.receipt.script_regions.length === 2);
    assert('every injected root is backed by a unique source-verified script region', mixedDocument.receipt.injected_coverage.every(row => row.language === 'JavaScript' && row.start >= row.script_start && row.end <= row.script_end));
    write('src/mixed-bad.html', `<div>Host document</div>
<script>import React from 'react'; Component.defaultProps={}; const bad=<div style={{color:'red'}}/>;</script>
`);
    const mixedBad = scanAst({ root: directory, config, files: ['src/mixed-bad.html'], entries, capture }); commands.push(...mixedBad.receipt.commands);
    assert('injected banned imports and v11/CSP findings remain failures', mixedBad.receipt.files[0].coverage === 1 && ['banned-imports', 'defaultProps', 'inline-style'].every(rule => mixedBad.findings.some(finding => finding.rule === rule)));
    const exportData = `export function inspect(value) { return value.includes('preact/compat') ? 'react' : 'framer-motion'; }
export const reference = {source:'react-dom'};
export default 'react/jsx-runtime';
export {reference as "preact/compat"};
`;
    const exportDataPaths = ['src/export-data.js', 'src/export-data.ts', 'src/export-data.tsx'];
    for (const path of exportDataPaths) write(path, exportData);
    const dataScan = scanAst({ root: directory, config, files: exportDataPaths, entries, capture }); commands.push(...dataScan.receipt.commands);
    assert('exported function comparisons, declaration strings, default values and alias names are data', dataScan.findings.length === 0 && dataScan.receipt.files.length === 3 && dataScan.receipt.files.every(file => file.coverage === 1));
    const actualSources = `import 'react';
import React from 'react/jsx-runtime';
export * from 'preact/compat';
export {createRoot} from 'react-dom/client';
`;
    const actualSourcePaths = ['src/actual-source.js', 'src/actual-source.ts', 'src/actual-source.tsx'];
    for (const path of actualSourcePaths) write(path, actualSources);
    const sourceScan = scanAst({ root: directory, config, files: actualSourcePaths, entries, capture }); commands.push(...sourceScan.receipt.commands);
    assert('side-effect imports, imports and both re-export forms remain module sources in every language', actualSourcePaths.every(path => sourceScan.findings.filter(finding => finding.rule === 'banned-imports' && finding.paths[0] === path).length === 4));
    write('src/imports.ts', "import React from 'react/jsx-runtime';\nexport {useState} from 'preact/compat/client';\nconst first=require('react-dom/client');\nconst second=import('framer-motion/mini');\nimport x from 're\\u0061ct';\nimport hidden from 'motion-utils';\nimport blocked from 'legacy-banned/subpath';\n");
    const imported = scan(['src/imports.ts']);
    assert('import/export/require/dynamic/subpaths/escaped literals use the banned lock', imported.filter(item => item.rule === 'banned-imports').length === 7);
    write('src/v11.tsx', "import {forwardRef} from 'preact';\nconst ref=useRef<HTMLDivElement>();\nconst defaults=Component.defaultProps;\nComponent['defaultProps']={};\ntype Props=JSX.HTMLAttributes<HTMLElement>;\nconst first=Component.base;const second=this.base;\nconst bad=<div style={{color:'red'}} onclick='doBad()'/>;\n");
    const v11 = scan(['src/v11.tsx']);
    for (const name of ['forwardRef', 'defaultProps', 'useRef-initial', 'JSX-types', 'Component-base', 'inline-style', 'inline-handler']) assert(`actual AST identifies ${name}`, v11.some(item => item.rule === name));
    write('src/.hidden/ignored.tsx', "// ast-grep-ignore: roedu-tsx-import-source\nimport React from 'react';\n// ast-grep-ignore: roedu-tsx-inline-style\nconst hidden=<div style={{color:'red'}}/>;\n");
    write('.gitignore', 'src/.hidden/\n'); write('.ignore', 'src/.hidden/\n'); write('.ast-grepignore', 'src/.hidden/\n');
    const { files } = walkRepository(directory, config), ignored = scan(files.filter(path => path.endsWith('ignored.tsx')));
    assert('hidden and ignored files are scanned explicitly', ignored.some(item => item.rule === 'banned-imports'));
    assert('native suppression is a failing finding and cannot remove style finding', ignored.some(item => item.rule === 'inline-disable') && ignored.some(item => item.rule === 'inline-style'));
    write('src/bad.html', '<button STYLE="color:red" OnClick="bad()">Invalid</button>\n');
    write('server/bad.go', 'package ast\nfunc invalid() { templ.SafeURL("bad") }\n');
    const others = scan(['src/bad.html', 'server/bad.go']);
    assert('HTML case variants are AST attributes', ['inline-style', 'inline-handler'].every(rule => others.some(item => item.rule === rule)));
    assert('Go templ.SafeURL is an AST call', others.some(item => item.rule === 'templ-SafeURL'));
    write('lint/scope.json', JSON.stringify({ schema: 1, entries: [{ paths: ['src/imports.ts'], rules: ['banned-imports'], reason: 'temporary migration', expires: 'last-screen' }] }) + '\n');
    const scopeFiles = walkRepository(directory, config).files, packages = new Set(['frontend', 'kit-package']);
    const scope = loadScope(directory, config, scopeFiles, packages);
    const scoped = finish(imported, scope, packages);
    assert('legacy scope reports import findings as pending', scoped.reason === 'legacy-pending' && scoped.legacy_pending.length === 5 && scoped.errors.length === 2 && scoped.errors.every(item => item.rule === 'banned-imports' && !item.scopable));
    const mixed = finish([...imported, ...v11], scope, packages);
    assert('scope never exempts v11 or CSP findings', mixed.errors.some(item => item.rule === 'inline-style') && mixed.errors.some(item => item.rule === 'forwardRef'));
    const lex = sourceFindings(directory, scopeFiles, entries);
    assert('ignore configuration still reaches the shared lexical policy', lex.some(item => item.rule === 'ignore-bypass'));
    assert('stale scope remains a failure', finish([], scope, packages).errors.some(item => item.rule === 'lint-scope'));
    let coreRefused = false; try { loadScope(directory, { ...config, role: 'core' }, scopeFiles, packages); } catch { coreRefused = true; }
    assert('core cannot acquire a legacy scope', coreRefused);
    return { schema: 1, check: 'ast-self-test', status: 'pass', assertions, commands, artifacts: capture.artifacts };
  } catch (error) { error.astArtifacts = capture.artifacts; throw error; }
  finally { rmSync(directory, { recursive: true, force: true }); }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  (async () => {
    const args = process.argv.slice(2);
    check(args.length === 0 || args.length === 1 && args[0] === '--self-test', 'ast-check accepts only --self-test');
    const result = args.length ? astSelfTest() : await checkAst({});
    process.stdout.write(JSON.stringify(result) + '\n');
    if (result.status !== 'pass') { for (const error of result.errors) process.stderr.write(`${error.rule}: ${error.tool_or_import} ${error.paths.join(', ')}\n`); process.exitCode = 1; }
  })().catch(error => {
    process.stderr.write(error.message + '\n');
    process.stdout.write(JSON.stringify({ schema: 1, check: 'v11-lint', status: 'fail', reason: 'validation-failed', errors: [{ rule: 'ast-check', tool_or_import: error.message, paths: [] }], legacy_pending: [], artifacts: error.astArtifacts ?? [] }) + '\n'); process.exitCode = 1;
  });
}
