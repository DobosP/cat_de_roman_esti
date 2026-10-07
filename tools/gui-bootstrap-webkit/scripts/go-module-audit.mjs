import { existsSync, lstatSync, readFileSync, realpathSync } from 'node:fs';
import { dirname, isAbsolute, join, relative, resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { inside, localPath, posix } from '../lint/validation-files.mjs';

const KIT = 'github.com/DobosP/roedu-ui/web-kit';
const reserved = new Set(['node_modules', '.git', '.gate', '.vitest', 'dist', 'test-results', 'testdata', 'fixtures', 'third_party', 'vendor', 'kit', 'legacy', 'cache', 'caches', '_temp', '_worktrees', '__pycache__']);
const check = (value, message) => { if (!value) throw Error(message); };
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const modFile = dir => dir === '.' ? 'go.mod' : `${dir}/go.mod`;
const sumFile = dir => dir === '.' ? 'go.sum' : `${dir}/go.sum`;

// Native JSON sorts/deduplicates replace selectors. Count only source arrows
// outside Go strings/comments so an earlier declared row cannot disappear.
function declaredReplacements(bytes) {
  const text = bytes.toString('utf8'); check(bytes.equals(Buffer.from(text)), 'Go module source must be valid UTF-8');
  let count = 0, quote = '', escaped = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quote) {
      if (quote === '"' && escaped) { escaped = false; continue; }
      if (quote === '"' && c === '\\') { escaped = true; continue; }
      if (c === quote) quote = '';
      continue;
    }
    if (c === '"' || c === '`') { quote = c; continue; }
    if (c === '/' && text[i + 1] === '/') { while (i < text.length && text[i] !== '\n') i++; continue; }
    if (c === '=' && text[i + 1] === '>') { count++; i++; }
  }
  return count;
}

/** Go1.27 omits Indirect:false. Absence means a direct requirement, not an exemption. */
export function normalizeGoRequirements(rows, filename) {
  check(Array.isArray(rows), `${filename}: native requirements must be an array`);
  const names=new Set();
  return rows.map(item=>{
    check(item&&typeof item==='object'&&!Array.isArray(item)&&Object.keys(item).every(key=>['Path','Version','Indirect'].includes(key))&&typeof item.Path==='string'&&item.Path&&typeof item.Version==='string'&&item.Version.startsWith('v')&&(!Object.hasOwn(item,'Indirect')||typeof item.Indirect==='boolean')&&!names.has(item.Path), `${filename}: malformed or duplicate requirement`);
    names.add(item.Path);
    return {Path:item.Path,Version:item.Version,Indirect:Object.hasOwn(item,'Indirect')?item.Indirect:false};
  });
}

/** The native Go parser reads one selected file; -json prints rather than writes.
 * No dependency resolution, external mount, synthetic parser or product build.
 * Primary protocol: https://go.dev/ref/mod#go-mod-edit
 */
function parseModule(root, dir, commands) {
  const filename = modFile(dir), file = localPath(root, filename), before = readFileSync(file), mode = lstatSync(file).mode;
  const result = spawnSync('go', ['mod', 'edit', '-json', file], {
    cwd: dirname(file), env: { ...process.env, GOTOOLCHAIN: 'local', GOWORK: 'off', GOENV: 'off' },
    encoding: 'utf8', maxBuffer: 4 * 1024 * 1024, timeout: 30000,
  });
  const after = readFileSync(file);
  // Retain complete actual parser streams before any source/JSON/row assertion.
  commands.push({ command: 'go', args: ['mod', 'edit', '-json', filename], cwd: dir, exit_code: result.status ?? -1, source_sha256: sha(before), stdout: result.stdout ?? '', stderr: result.stderr ?? '', stdout_sha256: sha(result.stdout ?? ''), stderr_sha256: sha(result.stderr ?? '') });
  check(before.equals(after) && lstatSync(file).mode === mode, `${filename}: native parser changed source bytes or mode`);
  check(!result.error && result.signal === null && result.status === 0, `${filename}: native Go parser refused: ${result.stderr?.trim() || result.error?.message || result.signal || result.status}`);
  const data = JSON.parse(result.stdout);
  check(typeof data.Module?.Path === 'string' && data.Module.Path, `${filename}: declared module identity missing`);
  check(typeof data.Go === 'string' && /^\d+\.\d+(?:\.\d+)?$/.test(data.Go), `${filename}: Go directive missing`);
  check((data.Require === null || data.Require === undefined || Array.isArray(data.Require)) && (data.Replace === null || data.Replace === undefined || Array.isArray(data.Replace)), `${filename}: unexpected native Go metadata`);
  const requirements = normalizeGoRequirements(data.Require ?? [], filename), replacements = data.Replace ?? [];
  check(declaredReplacements(before) === replacements.length, `${filename}: native Go parser dropped declared replacement rows`);
  const selectors = new Set();
  for (const item of replacements) {
    check(item.Old && item.New && typeof item.Old.Path === 'string' && item.Old.Path && typeof item.New.Path === 'string' && item.New.Path, `${filename}: malformed replacement`);
    const selector = `${item.Old.Path}@${item.Old.Version ?? ''}`;
    check(!selectors.has(selector), `${filename}: duplicate replacement selector`); selectors.add(selector);
  }
  return { data, requirements, replacements, sha256: sha(before) };
}

function literalTarget(root, dir, literal, frozenKit = false) {
  const filename = modFile(dir);
  check(typeof literal === 'string' && literal && !isAbsolute(literal) && !/^[A-Za-z]:/.test(literal) && !literal.includes('\\') && !literal.includes('\0') && !/[\r\n]/.test(literal) && (literal === '.' || literal === '..' || literal.startsWith('./') || literal.startsWith('../')), `${filename}: replacement must be a literal relative directory`);
  let current = localPath(root, dir);
  // Validate every literal path hop before normalization, including ancestors.
  for (const part of literal.split('/')) {
    if (!part || part === '.') continue;
    current = part === '..' ? dirname(current) : join(current, part);
    check(inside(root, current), `${filename}: replacement escapes repository`);
    const parts = posix(relative(root, current)).split('/').filter(Boolean);
    check(frozenKit || !parts.some(name => name.startsWith('.') || reserved.has(name)), `${filename}: replacement enters ignored or cache source`);
    check(existsSync(current) && lstatSync(current).isDirectory() && !lstatSync(current).isSymbolicLink(), `${filename}: replacement ancestor is missing, non-directory or a symlink`);
  }
  const target = posix(relative(root, current)) || '.';
  localPath(root, modFile(target));
  return target;
}

/** Audit actual discovered module roots, retaining go_dirs solely as receivers.
 * Generic same-repo edges must be source-discovered. The frozen kit edge keeps
 * its existing distinct tag/path proof; checkKit owns its vendored byte proof.
 */
export function auditGoModules({ root, config, files, entries, lock, onObserved = () => {}, onBanned = () => {} }) {
  root = resolve(root);
  check(lstatSync(root).isDirectory() && !lstatSync(root).isSymbolicLink() && realpathSync(root) === root, 'Go audit repository root must be real');
  check(Array.isArray(files) && entries instanceof Map && Array.isArray(config.go_dirs) && config.go_dirs.length, 'Go audit needs actual source discovery, lock entries and receiver roots');
  const discovered = new Set(files), receivers = config.go_dirs.map(dir => posix(relative(root, localPath(root, dir))) || '.');
  const parsed = new Map(), audited = new Set();
  const report = { receivers: [...receivers], modules: [], local_edges: [], kit_edges: [], commands: [] };
  const load = dir => { if (!parsed.has(dir)) parsed.set(dir, parseModule(root, dir, report.commands)); return parsed.get(dir); };
  const sourceModule = dir => {
    check(!dir.split('/').some(name => name.startsWith('.') && name !== '.' || reserved.has(name)), `${modFile(dir)}: ignored or cache module is unaudited`);
    check(discovered.has(modFile(dir)), `${modFile(dir)}: replacement target is not an audited source module`);
    return load(dir);
  };
  const visit = dir => {
    if (audited.has(dir)) return;
    const module = sourceModule(dir); audited.add(dir);
    const filename = modFile(dir), sumPath = sumFile(dir), sumAbsolute = localPath(root, sumPath, false);
    const sum = existsSync(sumAbsolute) ? readFileSync(localPath(root, sumPath), 'utf8') : '';
    if (existsSync(sumAbsolute)) check(discovered.has(sumPath), `${sumPath}: checksum file is outside audited source discovery`);
    const sums = sum.split('\n').filter(line => line.trim());
    for (const line of sums) check(/^\S+ v\S+ h1:[A-Za-z0-9+/]{43}=$/.test(line), `${sumPath}: malformed Go checksum row`);
    if (receivers.includes(dir)) check(module.requirements.length, `${filename}: no actual requirements parsed`);
    const row = { dir, module: module.data.Module.Path, go: module.data.Go, mod_sha256: module.sha256, sum_sha256: existsSync(sumAbsolute) ? sha(readFileSync(sumAbsolute)) : null, requirements: [] };
    report.modules.push(row);
    const edges = new Map();
    // Even a replacement that Go would not select must match an actual require.
    for (const replacement of module.replacements) {
      const requirement = module.requirements.find(item => item.Path === replacement.Old.Path && (!replacement.Old.Version || item.Version === replacement.Old.Version));
      check(requirement, `${filename}: replacement has no matching actual requirement ${replacement.Old.Path}`);
      check(!replacement.New.Version, `${filename}: remote module/version replacements remain refused`);
      let target, kind;
      if (requirement.Path === KIT) {
        check(!replacement.Old.Version, `${filename}: frozen kit replacement must be unqualified`);
        if (config.role === 'consumer') {
          check(requirement.Version === `v0.0.0-${lock.core_tag}` && replacement.New.Path === './third_party/webkit', `${filename}: kit Go tag/path mismatch`);
          target = literalTarget(root, dir, replacement.New.Path, true);
          check(target === (dir === '.' ? '' : `${dir}/`) + 'third_party/webkit', `${filename}: kit Go tag/path mismatch`);
        } else {
          target = literalTarget(root, dir, replacement.New.Path);
          check(requirement.Version === 'v0.0.0' && receivers.includes(target), `${filename}: core sample kit replacement mismatch`);
        }
        check(load(target).data.Module.Path === KIT, `${filename}: local kit module identity differs`);
        kind = 'frozen-kit'; report.kit_edges.push({ from: dir, module: requirement.Path, version: requirement.Version, literal: replacement.New.Path, target });
      } else {
        target = literalTarget(root, dir, replacement.New.Path);
        check(sourceModule(target).data.Module.Path === requirement.Path, `${filename}: replacement target declared module identity differs ${requirement.Path}`);
        kind = 'same-repo'; report.local_edges.push({ from: dir, module: requirement.Path, version: requirement.Version, old_version: replacement.Old.Version ?? '', literal: replacement.New.Path, target });
      }
      edges.set(`${replacement.Old.Path}@${replacement.Old.Version ?? ''}`, { target, kind });
    }
    for (const requirement of module.requirements) {
      const { Path: tool, Version: value, Indirect: indirect } = requirement;
      const entry = entries.get(tool), edge = edges.get(`${tool}@${value}`) ?? edges.get(`${tool}@`);
      onObserved(tool);
      if (entry?.status === 'banned') onBanned(tool, filename);
      if (tool === KIT) check(edge?.kind === 'frozen-kit', `${filename}: local kit replacement missing`);
      else if (entry?.version) check(value === entry.version, `${filename}: exact Go version differs ${tool}`);
      else if (!edge) check(indirect, `${filename}: unregistered direct Go requirement ${tool}`);
      if (!edge) check(sums.some(line => line.startsWith(`${tool} ${value} `)), `${sumPath}: requirement has no actual content hash ${tool}`);
      row.requirements.push({ module: tool, version: value, indirect, resolution: edge?.kind ?? 'remote', ...(edge ? { target: edge.target } : {}) });
    }
    for (const replacement of module.replacements) {
      const edge = edges.get(`${replacement.Old.Path}@${replacement.Old.Version ?? ''}`);
      if (edge.kind === 'same-repo') visit(edge.target);
    }
  };
  try { for (const dir of receivers) visit(dir); return report; }
  catch (error) { error.goAudit = report; throw error; }
}
