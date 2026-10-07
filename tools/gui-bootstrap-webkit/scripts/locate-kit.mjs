import * as fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';
import { createHash } from 'node:crypto';
import { validateUiAdoption } from './ui-adoption-config.mjs';
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
/** Read only the wrapper-owned current invocation; matching historical receipts are never selectors. */
function frozenBootstrapConfig(ctx) {
  const known = new Set(['unit','full','gen','deps','kit:sync','build','image','baseline','golden:capture','golden:verify','contract:refresh','legacy:freeze','e2e','perf','qualify','shell']);
  const input = relative => {
    let current = ctx.root;
    for (const part of relative.split('/')) { current = path.join(current,part); const stat = fs.lstatSync(current); if (stat.isSymbolicLink() || (!stat.isFile() && !stat.isDirectory())) throw Error('Nonregular current configuration ancestor'); }
    if (!fs.lstatSync(current).isFile()) throw Error('Current configuration must be a regular file'); return current;
  };
  const descriptorPath='.gate/wrapper-current.json', descriptorBytes=fs.readFileSync(input(descriptorPath)), current=JSON.parse(descriptorBytes);
  const fields=['schema','invocation','target','sha','tree_sha256','toolchain_digest','config_sha256','config_path','config_file_sha256'];
  if (!current || typeof current!=='object' || Array.isArray(current) || Object.keys(current).length!==fields.length || !fields.every(key=>Object.hasOwn(current,key)) || current.schema!==1 || typeof current.invocation!=='string' || !/^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/.test(current.invocation??'') || typeof current.target!=='string' || !known.has(current.target) || current.sha!==ctx.sha || current.tree_sha256!==ctx.tree_sha256 || current.toolchain_digest!==ctx.toolchain_digest || !/^[a-f0-9]{64}$/.test(current.config_sha256??'') || !/^[a-f0-9]{64}$/.test(current.config_file_sha256??'')) throw Error('Closed current wrapper invocation identity required');
  const relative=`.gate/${current.target.replaceAll(':','-')}/wrapper-kit-config.json`;
  if (current.config_path!==relative) throw Error('Current configuration reference differs from exact primary target');
  if (ctx.target && ctx.target!==current.target) {
    const parents={setup:['unit','full','build','baseline','e2e','perf','kit:sync'],deps:['gen','kit:sync'], 'assets:sync':['build','kit:sync']};
    if (!parents[ctx.target]?.includes(current.target)) throw Error('Requested primary target differs from current wrapper invocation');
  }
  const bytes=fs.readFileSync(input(relative)), captured=JSON.parse(bytes), config=captured.config;
  if (hash(bytes)!==current.config_file_sha256 || captured.schema!==1 || captured.target!==current.target || captured.sha!==current.sha || captured.tree_sha256!==current.tree_sha256 || captured.toolchain_digest!==current.toolchain_digest || captured.config_sha256!==current.config_sha256 || !config || typeof config!=='object' || Array.isArray(config) || Object.keys(config).some(key=>!['role','app','npm_dir','vendor_dir','go_dirs','ui_adoption'].includes(key)) || !['role','app','npm_dir','vendor_dir','go_dirs'].every(key=>Object.hasOwn(config,key)) || !['core','consumer'].includes(config.role) || typeof config.app!=='string' || !/^[A-Za-z][A-Za-z0-9_-]*$/.test(config.app)) throw Error('Current frozen configuration bytes/identity differ');
  const literal=(value,dot=false)=>{if(dot&&value==='.')return value;if(typeof value!=='string'||!value||value.startsWith('/')||value.split('/').some(part=>!/^[A-Za-z0-9_@.-]+$/.test(part)||part==='.'||part==='..'))throw Error('Nonliteral current configured path');return value;};
  literal(config.npm_dir);literal(config.vendor_dir);
  if(!Array.isArray(config.go_dirs)||!config.go_dirs.length||new Set(config.go_dirs).size!==config.go_dirs.length)throw Error('Explicit current Go paths required');config.go_dirs.forEach(directory=>literal(directory,true));
  const phase=validateUiAdoption(config),canonical={role:config.role,app:config.app,npm_dir:config.npm_dir,vendor_dir:config.vendor_dir,go_dirs:[...config.go_dirs],...(phase?{ui_adoption:phase}:{})};
  if(current.config_sha256!==hash(JSON.stringify(canonical))||JSON.stringify(config)!==JSON.stringify(canonical))throw Error('Current complete phase projection checksum mismatch');
  return {config:canonical,config_sha256:captured.config_sha256,wrapper_target:captured.target,wrapper_config:relative,wrapper_config_sha256:hash(bytes),wrapper_invocation:current.invocation,wrapper_descriptor:descriptorPath,wrapper_descriptor_sha256:hash(descriptorBytes)};
}


export function relativePath(value, allowDot = false) {
  if (allowDot && value === '.') return value;
  if (typeof value !== 'string' || !value || value.startsWith('/') || /[\\:\x00-\x1f\x7f]/.test(value) || value.split('/').some(part => !part || part === '.' || part === '..')) throw Error('Unsafe configured kit path');
  return value;
}
export function regularPath(root, relative, missing = false) {
  let current = root;
  for (const part of relativePath(relative).split('/')) {
    current = path.join(current, part);
    try { if (fs.lstatSync(current).isSymbolicLink()) throw Error(`Symlink kit path: ${relative}`); }
    catch (error) { if (error.code !== 'ENOENT' || !missing) throw error; }
  }
  return current;
}
export function validateKitConfig(root, config, requirePackage = true) {
  if (!config || typeof config !== 'object' || Array.isArray(config) || Object.keys(config).some(key => !['role', 'app', 'npm_dir', 'vendor_dir', 'go_dirs', 'ui_adoption'].includes(key))) throw Error('Unknown repo:kit-config fields');
  if (!['core', 'consumer'].includes(config.role) || typeof config.app !== 'string' || !/^[A-Za-z][A-Za-z0-9_-]*$/.test(config.app)) throw Error('Explicit kit role/app required');
  const phase = validateUiAdoption(config);
  const npmDir = relativePath(config.npm_dir ?? (config.role === 'core' ? 'web-kit' : 'frontend/node_modules/@roedu/web-kit'));
  const vendorDir = relativePath(config.vendor_dir ?? 'frontend/vendor');
  if (config.go_dirs !== undefined && (!Array.isArray(config.go_dirs) || new Set(config.go_dirs).size !== config.go_dirs.length)) throw Error('Malformed configured Go directories');
  for (const directory of config.go_dirs ?? []) relativePath(directory, true);
  const packageRoot = regularPath(root, npmDir, !requirePackage);
  if (requirePackage) {
    const manifestPath = regularPath(root, `${npmDir}/package.json`);
    if (!fs.lstatSync(manifestPath).isFile() || JSON.parse(fs.readFileSync(manifestPath)).name !== '@roedu/web-kit') throw Error('Located package is not @roedu/web-kit');
  }
  return { role: config.role, app: config.app, npm_dir: npmDir, vendor_dir: vendorDir, ...(config.go_dirs === undefined ? {} : { go_dirs: [...config.go_dirs] }), ...(phase ? { ui_adoption: phase } : {}), packageRoot };
}
export function readKitConfig(root = process.cwd(), requirePackage = true, requestedTarget) {
  const child = spawnSync('task', ['--silent', 'repo:kit-config'], { cwd: root, env: process.env, encoding: 'utf8', maxBuffer: 1024 * 1024 });
  if (child.error || child.status !== 0) throw Error(`repo:kit-config failed (${child.status ?? 'unavailable'})`);
  let parsed; try { parsed = JSON.parse(child.stdout); } catch { throw Error('repo:kit-config must emit only JSON'); }
  const config = validateKitConfig(root, parsed, requirePackage);
  // This is a native entrypoint. Pure structural fixtures use validateKitConfig.
  const frozen = frozenBootstrapConfig({root,target:requestedTarget,sha:process.env.GATE_SHA,tree_sha256:process.env.GATE_TREE_SHA256,toolchain_digest:process.env.TOOLCHAIN_DIGEST});
  const canonical = {role:config.role,app:config.app,npm_dir:config.npm_dir,vendor_dir:config.vendor_dir,go_dirs:config.go_dirs??frozen.config.go_dirs,...(config.ui_adoption?{ui_adoption:config.ui_adoption}:{})};
  if(hash(JSON.stringify(canonical))!==frozen.config_sha256)throw Error('Actual package configuration differs from the current complete UI phase');
  config.go_dirs=[...canonical.go_dirs];
  return config;
}
export function publicConfig(config) {
  const { packageRoot: _private, ...result } = config; return result;
}
export function kitScript(config, name) {
  relativePath(name); return path.join(config.packageRoot, 'scripts', name);
}
export function kitModule(config, relative) { return pathToFileURL(regularPath(path.dirname(config.packageRoot), `${path.basename(config.packageRoot)}/${relativePath(relative)}`)).href; }
/** Trusted Taskfile inline equivalent: config is available before npm dependencies. */
export async function launchConfigured(target) {
  const { randomUUID } = await import('node:crypto');
  const root = fs.realpathSync(process.cwd()), before = readKitConfig(root, false, target);
  let witness;
  const install = ['unit', 'full', 'build', 'baseline', 'e2e', 'perf'].includes(target) || !fs.existsSync(path.join(before.packageRoot, 'scripts/run-task.mjs'));
  if (target === 'deps' && !fs.existsSync(path.join(before.packageRoot, 'scripts/run-task.mjs'))) throw Error('Dependency bootstrap must dispatch self-contained repo:deps before npm ci; use trusted inline bootstrapDeps');
  if (install) {
    const invocation = randomUUID(), start = Date.now();
    const child = spawnSync('task', ['--silent', 'repo:setup', `INVOCATION=${invocation}`], { cwd: root, env: process.env, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 });
    if (child.stderr) process.stderr.write(child.stderr);
    if (child.error || child.status !== 0) throw Error(`Actual repo:setup failed (${child.status ?? 'unavailable'})`);
    witness = { command: 'task', target: 'repo:setup', exit_code: child.status, duration_ms: Date.now() - start, report: JSON.parse(child.stdout) };
  }
  const config = readKitConfig(root, true, target);
  const runner = await import(pathToFileURL(path.join(config.packageRoot, 'scripts/run-task.mjs')).href);
  return runner.main(target, witness ? { setupWitness: witness } : {});
}
