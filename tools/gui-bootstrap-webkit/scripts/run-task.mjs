import * as fs from 'node:fs';
import path from 'node:path';
import { createHash, randomUUID } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { readKitConfig, kitScript, regularPath } from './locate-kit.mjs';
import { collectAstArtifacts } from './ast-artifacts.mjs';
import { validateUiAdoptionEvidence } from '../schemas/validate.mjs';
import { inspectUiAdoption, loadKit, uiAdoptionPending, validateUiAdoption } from './kit-sync.mjs';

const sha256 = data => createHash('sha256').update(data).digest('hex');
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
const CHECK = /^[A-Za-z][A-Za-z0-9:._-]*$/;
const CORE_UNIT = ['precompression','budgets','schemas','template-identity','lint-scope','kit:check','npm-distribution','go-distribution','npm-lock', 'versions-check', 'toolchain-versions', 'tsc', 'oxlint', 'v11-lint', 'vitest-browser', 'go-vet', 'go-test-race', 'docs-gate', 'go-mod-tidy', 'gen-check', 'templ-check', 'css-measurements', 'runtime-measurements', 'pg-live'];
const CORE_FULL = ['axe','vitals','app-healthy', 'pw-islands', 'pw-behaviors', 'pw-motion', 'pw-journeys', 'screenshots', 'csp-trap'];
export function readGateEnvironment(root) {
  const env = {};
  for (const line of fs.readFileSync(path.join(root, '.gate.env'), 'utf8').split('\n')) {
    if (!line || line.startsWith('#')) continue;
    const match = /^([A-Z_]+)=([^\r\n]*)$/.exec(line);
    if (!match || Object.hasOwn(env, match[1])) throw Error('Malformed gate environment');
    env[match[1]] = match[2];
  }
  return env;
}
export function createContext(target, invocation = randomUUID()) {
  const root = fs.realpathSync(process.cwd()), env = readGateEnvironment(root);
  if (!UUID.test(invocation)) throw Error('A fresh invocation UUID is required');
  if (!/^[a-f0-9]{40}([a-f0-9]{24})?$/.test(process.env.GATE_SHA ?? '') || !/^[a-f0-9]{64}$/.test(process.env.GATE_TREE_SHA256 ?? '') || !['true', 'false'].includes(process.env.GATE_DIRTY)) throw Error('Native wrapper SHA/tree/dirty binding required');
  const digest = process.env.TOOLCHAIN_DIGEST ?? env.TOOLCHAIN_DIGEST;
  const stage = process.env.CSP_STAGE ?? env.CSP_STAGE;
  const parallel = Number(process.env.GOMAXPROCS), cap = Number(process.env.GATE_PARALLEL_MAX ?? env.GATE_PARALLEL_MAX);
  if (!/^sha256:[a-f0-9]{64}$/.test(digest) || !Number.isInteger(parallel) || !Number.isInteger(cap) || cap < 1 || parallel < 1 || parallel > cap || !['report-only', 'enforced'].includes(stage)) throw Error('Executed toolchain/resources/CSP binding required');
  return { root, target, invocation, sha: process.env.GATE_SHA, tree_sha256: process.env.GATE_TREE_SHA256, dirty: process.env.GATE_DIRTY === 'true', toolchain_digest: digest, parallel, stage, started: new Date().toISOString() };
}
function retainLogs(context, label, ordinal, child, artifacts) {
  if (!CHECK.test(label) || !Number.isInteger(ordinal) || ordinal < 0) throw Error('Unsafe log identity');
  const prefix = `.gate/${context.target.replaceAll(':','-')}/logs/${context.invocation}-${label}-${ordinal}`;
  const logs = {};
  for (const stream of ['stdout','stderr']) {
    const relative = `${prefix}.${stream}.log`, bytes = Buffer.from(child[stream] ?? '');
    const filename = path.join(context.root,relative); fs.mkdirSync(path.dirname(filename),{recursive:true});
    fs.writeFileSync(filename,bytes); artifacts.push(`${relative} sha256:${sha256(bytes)}`); logs[`${stream}_log`] = relative;
  }
  return logs;
}
export function createHook(target, invocation) {
  const context = createContext(target, invocation), checks = [], actions = [], artifacts = [], budgets = {}, legacy_pending = [], reasons = new Map();
  let current;
  const api = {
    context, checks, actions, artifacts, budgets, legacy_pending,
    check(name, operation) {
      if (!CHECK.test(name) || checks.some(check => check.name === name)) throw Error(`Invalid/duplicate check name: ${name}`);
      const start = Date.now(), before = actions.length; current = name;
      try {
        operation();
        if (actions.length === before) throw Error('Check executed no command or assertion');
        checks.push({ name, status: 'pass', ...(reasons.has(name)?{reason:reasons.get(name)}:{}), duration_ms: Date.now() - start });
      } catch (error) { checks.push({ name, status: 'fail', reason: reasons.get(name)??error.message, duration_ms: Date.now() - start }); }
      finally { current = undefined; }
    },
    run(command, args = [], cwd = context.root, extraEnvironment = {}) {
      if (!current || typeof command !== 'string' || !Array.isArray(args)) throw Error('Commands require an active named check');
      const start = Date.now(); process.stderr.write(`+ ${command} (${args.length} arguments)\n`);
      const child = spawnSync(command, args, { cwd, env: { ...process.env, ...extraEnvironment }, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 });
      const logs = retainLogs(context,current,actions.length,child,artifacts);
      const action = { check: current, kind: 'command', command, argument_count: args.length, args_sha256: sha256(JSON.stringify(args)), cwd: path.relative(context.root, cwd) || '.', exit_code: child.status ?? -1, duration_ms: Date.now() - start, stdout_sha256: sha256(child.stdout ?? ''), stderr_sha256: sha256(child.stderr ?? ''), ...logs };
      actions.push(action); if (child.stdout) {
        if (args.includes('-json')) { const events = child.stdout.split('\n').filter(line => line.startsWith('{')).map(line => JSON.parse(line)); process.stderr.write(`Go JSON: ${events.filter(item => item.Test && item.Action === 'pass').length} pass; ${events.filter(item => item.Action === 'fail').length} fail; ${events.filter(item => item.Action === 'skip').length} skip\n`); if (child.status !== 0) process.stderr.write(child.stdout); }
        else process.stderr.write(child.stdout);
      } if (child.stderr) process.stderr.write(child.stderr);
      if (child.error || child.status !== 0) { const error=Error(`${command} failed (${child.status ?? 'unavailable'})`);error.stdout=child.stdout;throw error; }
      return child.stdout;
    },
    legacy(report) {
      if(!current||report?.schema!==1||!['pass','fail'].includes(report.status)||!Array.isArray(report.legacy_pending))throw Error('Malformed actual legacy validation report');
      for(const finding of report.legacy_pending){
        if(!['banned-imports','banned-packages','compat-paths'].includes(finding.rule)||typeof finding.tool_or_import!=='string'||!finding.tool_or_import||!Array.isArray(finding.paths)||!finding.paths.length||finding.paths.some(p=>typeof p!=='string'||!p)||typeof finding.expires!=='string'||!finding.expires.trim()||finding.source!=='lint/scope.json'||Object.keys(finding).some(k=>!['rule','tool_or_import','paths','expires','source'].includes(k)))throw Error('Malformed legacy finding');
        if(!legacy_pending.some(previous=>JSON.stringify(previous)===JSON.stringify(finding)))legacy_pending.push(finding);
      }
      if(report.legacy_pending.length)reasons.set(current,'legacy-pending');
    },
    uiAdoption(value) {
      if(value===undefined)return;
      if(!current)throw Error('UI adoption evidence requires an active named check');
      validateUiAdoptionEvidence(value);
      if(api.ui_adoption&&JSON.stringify(api.ui_adoption)!==JSON.stringify(value))throw Error('UI adoption evidence changed during execution');
      api.ui_adoption=structuredClone(value);
      reasons.set(current,reasons.get(current)==='legacy-pending'?'legacy-pending;ui-staged-pending':'ui-staged-pending');
    },
    assert(label, condition) {
      if (!current || typeof condition !== 'function') throw Error('Assertions require a named check and an executed predicate');
      const start = Date.now(); let passed = false;
      try { passed = condition() === true; } finally { actions.push({ check: current, kind: 'assertion', label, passed, duration_ms: Date.now() - start }); }
      if (!passed) throw Error(label);
    },
    skip(name, reason, condition) {
      if (target !== 'unit' || !['no-dsn', 'no-device'].includes(reason) || checks.some(check => check.name === name) || condition() !== true) throw Error('Unproven or disallowed skip');
      checks.push({ name, status: 'skipped', reason, duration_ms: 0 }); actions.push({ check: name, kind: 'skip', reason, condition_observed: true });
    },
    artifact(relative) {
      const file = regularPath(context.root, relative); if (!fs.lstatSync(file).isFile()) throw Error('Artifact must be an actual file');
      artifacts.push(`${relative} sha256:${sha256(fs.readFileSync(file))}`);
    },
    finish() { return { schema: 1, target, invocation, sha: context.sha, tree_sha256: context.tree_sha256, started: context.started, finished: new Date().toISOString(), checks, actions, artifacts, budgets, ...(legacy_pending.length?{legacy_pending}:{}), ...(api.ui_adoption?{ui_adoption:api.ui_adoption}:{}), ...(api.browser ? { browser: api.browser } : {}) }; },
  };
  return api;
}
export function validateHookReport(report, context, target) {
  if (!report || report.schema !== 1 || report.target !== target || report.invocation !== context.invocation || report.sha !== context.sha || report.tree_sha256 !== context.tree_sha256 || !Array.isArray(report.checks) || !report.checks.length || !Array.isArray(report.actions)) throw Error('Missing, empty or unbound repo hook report');
  const names = new Set();
  for (const check of report.checks) {
    if (!CHECK.test(check.name) || names.has(check.name) || !['pass', 'fail', 'skipped'].includes(check.status) || !Number.isInteger(check.duration_ms) || check.duration_ms < 0) throw Error('Invalid/duplicate hook check');
    names.add(check.name);
    const actions = report.actions.filter(action => action.check === check.name);
    if (!actions.length && check.status !== 'fail') throw Error(`Hook check lacks executed evidence: ${check.name}`);
    for (const action of actions) {
      if (action.kind === 'command' && (!Number.isInteger(action.exit_code) || !/^[a-f0-9]{64}$/.test(action.stdout_sha256) || !/^[a-f0-9]{64}$/.test(action.stderr_sha256) || typeof action.command !== 'string')) throw Error('Invalid command evidence');
      if (!['command', 'assertion', 'skip'].includes(action.kind)) throw Error('Unknown hook evidence');
    }
    if (check.status === 'pass' && actions.some(action => (action.kind === 'command' && action.exit_code !== 0) || (action.kind === 'assertion' && action.passed !== true) || action.kind === 'skip')) throw Error(`False pass in repo hook: ${check.name}`);
    if (check.status === 'skipped' && (context.target !== 'unit' || !['no-dsn', 'no-device'].includes(check.reason) || actions.some(action => action.kind !== 'skip' || action.condition_observed !== true))) throw Error('Disallowed hook skip');
  }
  if (report.actions.some(action => !names.has(action.check))) throw Error('Orphan hook action');
  if(report.ui_adoption)validateUiAdoptionEvidence(report.ui_adoption);
  if (context.target === 'full' && report.checks.some(check => check.status === 'skipped')) throw Error('Full hook skipped a check');
  return report;
}
export function validateDependencyActions(actions) {
  for (const [name, command, args] of [['npm-lock', 'npm', ['install', '--package-lock-only', '--ignore-scripts']], ['go-mod-tidy', 'go', ['mod', 'tidy']]]) {
    const relevant = actions.filter(action => action.check === name && action.kind === 'command');
    if (!relevant.length || relevant.some(action => path.basename(action.command) !== command || action.args_sha256 !== sha256(JSON.stringify(args)) || action.exit_code !== 0)) throw Error(`Actual sanctioned dependency command missing: ${name}`);
  }
}
function appendReport(harness, report) {
  for (const check of report.checks) {
    if (harness.checks.some(previous => previous.name === check.name)) throw Error(`Duplicate aggregate check: ${check.name}`);
    harness.checks.push(check);
  }
  harness.legacy_pending.push(...(report.legacy_pending??[]).filter(finding=>!harness.legacy_pending.some(previous=>JSON.stringify(previous)===JSON.stringify(finding))));
  if(report.ui_adoption){validateUiAdoptionEvidence(report.ui_adoption);if(harness.ui_adoption&&JSON.stringify(harness.ui_adoption)!==JSON.stringify(report.ui_adoption))throw Error('Hook UI adoption evidence differs from actual common checks');harness.ui_adoption=structuredClone(report.ui_adoption);}
  const relocated = new Map();
  for (const artifact of report.artifacts ?? []) {
    const match = /^(.+) sha256:([a-f0-9]{64})$/.exec(artifact);
    if (!match) throw Error('Malformed hook artifact');
    const source = regularPath(harness.context.root,match[1]), bytes = fs.readFileSync(source);
    if (sha256(bytes) !== match[2]) throw Error('Hook artifact bytes differ from receipt');
    let relative = match[1];
    if (/^\.gate\/[^/]+\/logs\//.test(relative) && !relative.startsWith(`.gate/${harness.context.target.replaceAll(':','-')}/`)) {
      relative = `.gate/${harness.context.target.replaceAll(':','-')}/logs/${report.target.replaceAll(':','-')}-${path.basename(relative)}`;
      const destination = path.join(harness.context.root,relative); fs.mkdirSync(path.dirname(destination),{recursive:true}); fs.writeFileSync(destination,bytes);
      relocated.set(match[1],relative);
    }
    harness.artifacts.push(`${relative} sha256:${match[2]}`);
  }
  harness.actions.push(...report.actions.map(action=>({...action,...(action.stdout_log?{stdout_log:relocated.get(action.stdout_log)??action.stdout_log}:{}),...(action.stderr_log?{stderr_log:relocated.get(action.stderr_log)??action.stderr_log}:{})})));
  Object.assign(harness.budgets, report.budgets ?? {});
  if (report.browser) harness.browser = report.browser;
}
function executeHook(harness, name) {
  const started = Date.now();
  const child = spawnSync('task', ['--silent', `repo:${name}`, `INVOCATION=${harness.context.invocation}`], { cwd: harness.context.root, env: process.env, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 });
  retainLogs(harness.context,`repo-${name}`,harness.actions.length,child,harness.artifacts);
  if (child.stderr) process.stderr.write(child.stderr);
  let report;
  try { report = JSON.parse(child.stdout); validateHookReport(report, harness.context, name); }
  catch (error) { harness.checks.push({ name: `repo-${name}`, status: 'fail', reason: `${error.message}; hook exit=${child.status ?? 'unavailable'}`, duration_ms: Date.now() - started }); return; }
  appendReport(harness, report);
  if (child.error || child.status !== 0) harness.checks.push({ name: `repo-${name}-exit`, status: 'fail', reason: `Actual hook process exited ${child.status ?? 'unavailable'}`, duration_ms: Date.now() - started });
}
export function validateSetupWitness(witness, context) {
  if (!witness || witness.command !== 'task' || witness.target !== 'repo:setup' || witness.exit_code !== 0 || !Number.isInteger(witness.duration_ms) || witness.duration_ms < 0) throw Error('Missing actual setup process witness');
  return validateHookReport(witness.report, context, 'setup');
}
export function validation(harness,config,name,command,args) {
  harness.check(name,()=>{
    let stdout,error;try{stdout=harness.run(command,args);}catch(failure){error=failure;stdout=failure.stdout;}
    const report=JSON.parse(stdout);harness.legacy(report);harness.uiAdoption(report.ui_adoption);collectAstArtifacts(harness,report);
    const relative=`.gate/${harness.context.target.replaceAll(':','-')}/validation-${name}.json`;fs.mkdirSync(path.dirname(path.join(harness.context.root,relative)),{recursive:true});fs.writeFileSync(path.join(harness.context.root,relative),JSON.stringify(report,null,2)+'\n');harness.artifact(relative);
    if(error)throw error;harness.assert('Actual validation must pass',()=>report.status==='pass');
  });
}
function common(harness, config) {
  validation(harness,config,'versions-check',process.execPath,[kitScript(config,'versions-check.mjs')]);
  if(config.role==='core')harness.check('resolver-fixtures',()=>harness.run(process.execPath,[kitScript(config,'resolver-test.mjs')]));
  validation(harness,config,'toolchain-versions',process.execPath,[kitScript(config,'versions-check.mjs'),'--toolchain']);
  validation(harness,config,'lint-scope',process.execPath,[path.join(config.packageRoot,'lint/lint-scope.mjs')]);
  harness.check('kit:check',()=>{const stdout=harness.run(process.execPath,[kitScript(config,'kit-sync.mjs'),config.role==='core'?'--self-test':'--check']);if(config.role==='consumer'){const report=JSON.parse(stdout);harness.assert('Actual consumer kit check must pass',()=>report.mode==='check'&&report.status==='pass');harness.uiAdoption(report.ui_adoption);}});
}
function browserDescriptor(harness,config) {
  const descriptor=config.role==='core'?{inventory:'web-kit/sample/e2e/inventory.json',asset_root:'web-kit/sample/embedfs/dist',entry:'src/sample/main.ts',asset_prefix:'/static/'}:harness.browser;
  if(!descriptor||typeof descriptor.inventory!=='string'||typeof descriptor.asset_root!=='string'||typeof descriptor.entry!=='string'||/^(?:\.gate|node_modules|dist)(?:\/|$)/.test(descriptor.inventory))throw Error('Full requires committed inventory and actual independent manifest/entry/root');
  const manifestFile=`${descriptor.asset_root}/.vite/manifest.json`,manifestBytes=fs.readFileSync(regularPath(harness.context.root,manifestFile)),manifest=JSON.parse(manifestBytes),entries=new Set(),files=new Set(),eagerCss=new Set(),eagerPreloads=new Set(),allowedCss=new Set(),allowedJs=new Set();
  const visit=(key,eager)=>{const entry=manifest[key];if(!entry||typeof entry.file!=='string')throw Error('Missing manifest closure entry');const seen=eager?new Set():entries;if(!eager&&seen.has(key))return;if(!eager)entries.add(key);files.add(entry.file);if(entry.file.endsWith('.js'))allowedJs.add(entry.file);for(const file of [...entry.css??[],...entry.assets??[]])files.add(file);for(const file of entry.css??[]){allowedCss.add(file);if(eager)eagerCss.add(file);}for(const dep of entry.imports??[]){if(eager)eagerPreloads.add(manifest[dep]?.file);visit(dep,eager);}if(!eager)for(const dep of entry.dynamicImports??[])visit(dep,false);};
  visit(descriptor.entry,false);
  const eagerVisited=new Set();const eager=(key)=>{if(eagerVisited.has(key))return;eagerVisited.add(key);const entry=manifest[key];if(!entry)throw Error('Missing eager entry');for(const file of entry.css??[])eagerCss.add(file);for(const dep of entry.imports??[]){if(!manifest[dep])throw Error('Missing eager import');eagerPreloads.add(manifest[dep].file);eager(dep);}};eager(descriptor.entry);
  const prefix=descriptor.asset_prefix??'/static/';if(!prefix.startsWith('/')||prefix.startsWith('//')||!prefix.endsWith('/')||prefix.includes('..'))throw Error('Invalid actual asset prefix');
  const url=file=>new URL(prefix+file,process.env.GATE_APP_URL).href;
  return {...descriptor,manifestBytes,manifest,entries,files,eagerCss,eagerPreloads,allowedCss,allowedJs,url};
}
function verifyInventory(harness, config) {
  harness.check('browser-evidence', () => {
    const ctx=harness.context,descriptor=browserDescriptor(harness,config),bytes=fs.readFileSync(regularPath(ctx.root,descriptor.inventory)),expected=JSON.parse(bytes).cases,inventoryHash=sha256(bytes);
    harness.assert('Committed browser inventory required',()=>Array.isArray(expected)&&expected.length>0&&new Set(expected.map(item=>`${item.project}:${item.file}:${item.title}`)).size===expected.length);
    const key=item=>`${item.project}:${item.file}:${item.title}`;
    for(const lane of [...new Set(expected.map(item=>item.lane))]){
      if(!CHECK.test(lane))throw Error('Unsafe browser lane');const file=`.gate/full/browser-${lane}.json`,receipt=JSON.parse(fs.readFileSync(regularPath(ctx.root,file))),wanted=expected.filter(item=>item.lane===lane);
      harness.assert(`Fresh complete browser lane ${lane}`,()=>fs.statSync(path.join(ctx.root,file)).mtimeMs>=Date.parse(ctx.started)&&receipt.schema===1&&receipt.lane===lane&&receipt.sha===ctx.sha&&receipt.tree_sha256===ctx.tree_sha256&&receipt.app_image_id===process.env.GATE_APP_IMAGE_ID&&receipt.inventory_sha256===inventoryHash&&wanted.length>0&&receipt.expected_count===wanted.length&&Array.isArray(receipt.cases)&&receipt.cases.length===wanted.length&&JSON.stringify(receipt.cases.map(key).sort())===JSON.stringify(wanted.map(key).sort())&&new Set(receipt.cases.map(item=>item.id)).size===wanted.length&&receipt.cases.every(item=>typeof item.id==='string'&&item.id&&item.expectedStatus==='passed'&&item.status==='expected'&&item.ok===true&&item.results?.length===1&&item.results[0].retry===0&&item.results[0].status==='passed'));
      harness.artifact(file);
    }
    const witness=JSON.parse(fs.readFileSync(regularPath(ctx.root,'.gate/full/app-witness.json')));
    harness.assert('Actual fetched exact manifest closure required',()=>fs.statSync(path.join(ctx.root,'.gate/full/app-witness.json')).mtimeMs>=Date.parse(ctx.started)&&witness.schema===1&&witness.sha===ctx.sha&&witness.tree_sha256===ctx.tree_sha256&&witness.app_image_id===process.env.GATE_APP_IMAGE_ID&&witness.identity?.sha===ctx.sha&&witness.identity?.tree_sha256===ctx.tree_sha256&&witness.identity?.manifest_sha256===sha256(descriptor.manifestBytes)&&witness.identity?.versions_lock_sha256===sha256(fs.readFileSync(path.join(ctx.root,'versions.lock.json')))&&witness.entry===descriptor.entry&&Array.isArray(witness.assets)&&new Set(witness.assets.map(item=>item.file)).size===descriptor.files.size&&JSON.stringify(witness.assets.map(item=>item.file).sort())===JSON.stringify([...descriptor.files].sort())&&witness.assets.some(item=>item.file.endsWith('.js'))&&witness.assets.some(item=>item.file.endsWith('.css')));
    for(const asset of witness.assets){const actual=fs.readFileSync(regularPath(ctx.root,`${descriptor.asset_root}/${asset.file}`));harness.assert(`Independent fetched asset bytes/origin: ${asset.file}`,()=>asset.url===descriptor.url(asset.file)&&asset.bytes===actual.length&&asset.sha256===sha256(actual));}
    harness.artifact('.gate/full/app-witness.json');
    if(config.role==='core'){
      const file='.gate/full/screenshots.json',receipt=JSON.parse(fs.readFileSync(regularPath(ctx.root,file))),baseline=fs.readFileSync(regularPath(ctx.root,'baselines/core/chromium/capture.json'));
      const exported=JSON.parse(fs.readFileSync(regularPath(ctx.root,'.gate/full/budget-routes.json'))).filter(route=>route.template).map(route=>route.path==='/{$}'?'/':route.path).sort();
      harness.assert('Fresh image-bound screenshots must cover every actual registered page exactly',()=>fs.statSync(path.join(ctx.root,file)).mtimeMs>=Date.parse(ctx.started)&&receipt.schema===1&&receipt.mode==='verify'&&receipt.status==='pass'&&receipt.sha===ctx.sha&&receipt.tree_sha256===ctx.tree_sha256&&receipt.app_image_id===process.env.GATE_APP_IMAGE_ID&&receipt.manifest_sha256===sha256(descriptor.manifestBytes)&&receipt.baseline_sha256===sha256(baseline)&&receipt.stage===ctx.stage&&receipt.reducedMotion==='reduce'&&receipt.viewport?.width===1000&&receipt.viewport?.height===800&&Array.isArray(receipt.pages)&&receipt.pages.length===exported.length&&new Set(receipt.pages.map(item=>item.route)).size===exported.length&&JSON.stringify(receipt.pages.map(item=>item.route).sort())===JSON.stringify(exported)&&new Set(receipt.pages.map(item=>item.nonce?.sha256)).size===exported.length&&receipt.server_after?.violations===0&&receipt.pages.every(item=>item.diagnostics_available===true&&!item.diagnostics_error&&!item.server_error&&item.nonce?.json===7&&/^[a-f0-9]{64}$/.test(item.nonce?.sha256??'')&&item.console?.length===0&&item.errors?.length===0&&item.network?.length===0&&item.csp?.length===0&&item.islands?.length===0));
      const capture=JSON.parse(baseline);harness.assert('Exact committed screenshot set and browser required',()=>capture.status==='pass'&&capture.mode==='capture'&&capture.browser===receipt.browser&&JSON.stringify(capture.pages.map(item=>item.route).sort())===JSON.stringify(exported));
      for(const item of receipt.pages){
        const committed=capture.pages.find(record=>record.route===item.route),actual=fs.readFileSync(regularPath(ctx.root,item.actual_file)),expectedPNG=fs.readFileSync(regularPath(ctx.root,item.file));
        harness.assert(`Actual PNG bytes equal committed baseline: ${item.route}`,()=>item.file===committed?.file&&item.actual_file===`.gate/full/screenshots/${path.basename(item.file)}`&&item.bytes===actual.length&&item.sha256===sha256(actual)&&committed.bytes===expectedPNG.length&&committed.sha256===sha256(expectedPNG)&&actual.equals(expectedPNG));
        harness.artifact(item.actual_file);
      }
      harness.artifact(file);
    }

  });
}
async function writeResult(harness, config) {
  const context = harness.context; let csp = { stage: context.stage, violations: 0, legacy_violations: 0 };
  if(harness.ui_adoption)harness.check('ui-adoption-binding',()=>harness.assert('UI pending evidence binds the complete actual captured Cat configuration',()=>{
    const phase=validateUiAdoption(config),publicConfig={role:config.role,app:config.app,npm_dir:config.npm_dir,vendor_dir:config.vendor_dir,go_dirs:config.go_dirs,...(phase?{ui_adoption:phase}:{})};
    return config.role==='consumer'&&config.app==='cat_de_roman_esti'&&phase!==undefined&&harness.ui_adoption.config_sha256===sha256(JSON.stringify(publicConfig))&&JSON.stringify(harness.ui_adoption.legacy)===JSON.stringify(phase.legacy);
  }));
  if (context.target === 'full') {
    harness.check('csp-measurement', () => {
      const measured = JSON.parse(fs.readFileSync(path.join(context.root, '.gate/full/csp-measurement.json')));
      const descriptor=browserDescriptor(harness,config),appOrigin=new URL(process.env.GATE_APP_URL).origin;
      const pathFor=file=>new URL(descriptor.url(file)).pathname;
      const exactURL=(value,pathname)=>{try{const url=new URL(value);return url.origin===appOrigin&&url.href===new URL(pathname,process.env.GATE_APP_URL).href;}catch{return false;}};
      harness.assert('Fresh source/image/policy-bound CSP measurement required',()=>measured.schema===1&&measured.sha===context.sha&&measured.tree_sha256===context.tree_sha256&&measured.app_image_id===process.env.GATE_APP_IMAGE_ID&&measured.stage===context.stage&&Number.isInteger(measured.violations)&&measured.violations>=0&&Number.isInteger(measured.legacy_violations)&&measured.legacy_violations>=0&&Number.isInteger(measured.pages)&&measured.pages>0&&Array.isArray(measured.nonceObservations)&&measured.nonceObservations.length===measured.pages&&new Set(measured.nonceObservations.map(item=>item.page)).size===measured.pages&&new Set(measured.nonceObservations.map(item=>item.nonce_sha256)).size===measured.pages&&measured.nonceObservations.every(item=>/^[a-f0-9]{64}$/.test(item.nonce_sha256)&&Number.isInteger(item.scripts)&&item.scripts>0&&Number.isInteger(item.json)&&item.json>=0&&item.json<=item.scripts&&Number.isInteger(item.assetLinks)&&item.assetLinks>0&&item.module===pathFor(descriptor.manifest[descriptor.entry].file)&&exactURL(item.module_url,item.module)&&Array.isArray(item.css)&&Array.isArray(item.preloads)&&Array.isArray(item.css_urls)&&Array.isArray(item.preload_urls)&&item.css_urls.length===item.css.length&&item.preload_urls.length===item.preloads.length&&item.assetLinks===item.css.length+item.preloads.length&&item.css.every((file,i)=>[...descriptor.allowedCss].some(allowed=>pathFor(allowed)===file)&&exactURL(item.css_urls[i],file))&&item.preloads.every((file,i)=>[...descriptor.allowedJs].some(allowed=>pathFor(allowed)===file)&&exactURL(item.preload_urls[i],file))&&[...descriptor.eagerCss].every(file=>item.css.includes(pathFor(file)))&&[...descriptor.eagerPreloads].every(file=>item.preloads.includes(pathFor(file))))&&fs.statSync(path.join(context.root,'.gate/full/csp-measurement.json')).mtimeMs>=Date.parse(context.started));
      if(config.role==='core'){
        const exported=JSON.parse(fs.readFileSync(path.join(context.root,'.gate/full/budget-routes.json'))).filter(route=>route.template).map(route=>route.path==='/{$}'?'/':route.path).sort();
        harness.assert('CSP must cover every actual exported sample page',()=>JSON.stringify(measured.nonceObservations.map(item=>item.page).sort())===JSON.stringify(exported));
      }
      csp = { stage: measured.stage, violations: measured.violations, legacy_violations: measured.legacy_violations };
      harness.artifact('.gate/full/csp-measurement.json');
    });
    harness.check('app-image-evidence', () => {
      harness.assert('Built/executed app image ID missing', () => /^sha256:[a-f0-9]{64}$/.test(process.env.GATE_APP_IMAGE_ID ?? '') && typeof process.env.GATE_APP_IMAGE === 'string' && !!process.env.GATE_APP_IMAGE);
      harness.artifacts.push(`app-image ${process.env.GATE_APP_IMAGE} ${process.env.GATE_APP_IMAGE_ID}`);
    });
    verifyInventory(harness, config);
  }
  if (config.role === 'core' && ['unit', 'full'].includes(context.target)) for (const required of [...CORE_UNIT, ...(context.target === 'full' ? CORE_FULL : [])]) if (!harness.checks.some(check => check.name === required)) harness.checks.push({ name: `missing-${required}`, status: 'fail', reason: `Preserved core check is missing: ${required}`, duration_ms: 0 });
  if (!harness.checks.length || new Set(harness.checks.map(check => check.name)).size !== harness.checks.length) throw Error('Empty or duplicate final check set');
  const directory = path.join(context.root, '.gate', context.target.replaceAll(':', '-')); fs.mkdirSync(directory, { recursive: true });
  fs.writeFileSync(path.join(directory, 'execution.json'), JSON.stringify({ schema: 1, invocation: context.invocation, sha: context.sha, tree_sha256: context.tree_sha256, actions: harness.actions }, null, 2) + '\n');
  harness.artifact(`${path.relative(context.root, directory)}/execution.json`);
  const result = {
    schema: 1, target: context.target, status: 'fail', sha: context.sha, dirty: context.dirty, tree_sha256: context.tree_sha256,
    toolchain_digest: context.toolchain_digest, versions_lock_sha256: sha256(fs.readFileSync(path.join(context.root, 'versions.lock.json'))), parallel: context.parallel,
    started: context.started, finished: new Date().toISOString(), checks: harness.checks, csp, budgets: harness.budgets, artifacts: harness.artifacts, ...(harness.legacy_pending.length?{legacy_pending:harness.legacy_pending}:{}), ...(harness.ui_adoption?{ui_adoption:harness.ui_adoption}:{}),
  };
  const failed = () => result.checks.some(check => check.status === 'fail') || (context.target === 'full' && result.checks.some(check => check.status === 'skipped')) || csp.violations > 0 || Object.values(result.budgets).some(item => item.status === 'fail');
  result.status = failed() ? 'fail' : 'pass';
  try {
    const validator = await import(pathToFileURL(path.join(config.packageRoot, 'schemas/validate.mjs')).href);
    const schema = JSON.parse(fs.readFileSync(path.join(config.packageRoot, 'schemas/result.schema.json')));
    if (validator.validate(schema, result) === false || validator.assertGateResult(result) === false) throw Error('Gate result schema rejected');
  } catch (error) {
    result.checks.push({ name: 'result-schema', status: 'fail', reason: error.message, duration_ms: 0 }); result.status = 'fail';
  }
  fs.writeFileSync(path.join(directory, 'result.json'), JSON.stringify(result, null, 2) + '\n');
  process.exitCode = result.status === 'pass' ? 0 : 1;
  return result;
}

function removeFreshEvidence(ctx) {
  if (ctx.target !== 'full') return;
  for (const file of ['csp-measurement.json', 'app-witness.json', 'screenshots.json', ...['pw-islands', 'pw-behaviors', 'pw-motion', 'pw-journeys', 'axe', 'vitals', 'csp-trap'].map(lane => `browser-${lane}.json`)]) fs.rmSync(path.join(ctx.root, '.gate/full', file), { force: true });
}
function appendBootstrapEvidence(harness, reference) {
  harness.check('bootstrap-evidence', () => {
    const ctx=harness.context,prefix=`.gate/${ctx.target.replaceAll(':','-')}/`;
    harness.assert('Bootstrap reference is source/toolchain/invocation bound',()=>reference?.schema===1&&reference.target===ctx.target&&reference.invocation===ctx.invocation&&reference.sha===ctx.sha&&reference.tree_sha256===ctx.tree_sha256&&reference.toolchain_digest===ctx.toolchain_digest&&typeof reference.path==='string'&&reference.path===prefix+'bootstrap-execution.json'&&/^[a-f0-9]{64}$/.test(reference.sha256??''));
    const bytes=fs.readFileSync(regularPath(ctx.root,reference.path)),report=JSON.parse(bytes);
    harness.assert('Bootstrap receipt hash/identity matches actual bytes',()=>sha256(bytes)===reference.sha256&&report.schema===1&&report.target===ctx.target&&report.invocation===ctx.invocation&&report.sha===ctx.sha&&report.tree_sha256===ctx.tree_sha256&&report.toolchain_digest===ctx.toolchain_digest&&report.started===reference.started&&Number.isFinite(Date.parse(report.started))&&Number.isFinite(Date.parse(report.finished))&&Date.parse(report.finished)>=Date.parse(report.started)&&Array.isArray(report.actions)&&report.actions.length>0&&Array.isArray(report.artifacts));
    const listed=new Map();
    for(const artifact of report.artifacts){const match=/^(.+) sha256:([a-f0-9]{64})$/.exec(artifact);if(!match||!match[1].startsWith(prefix+'logs/'+ctx.invocation+'-bootstrap-')||listed.has(match[1]))throw Error('Invalid bootstrap log artifact');const actual=fs.readFileSync(regularPath(ctx.root,match[1]));harness.assert('Bootstrap log hash matches saved stream',()=>sha256(actual)===match[2]);listed.set(match[1],match[2]);harness.artifact(match[1]);}
    for(const action of report.actions)harness.assert('Bootstrap command has actual successful bound streams',()=>action.kind==='command'&&typeof action.phase==='string'&&CHECK.test(action.phase)&&typeof action.command==='string'&&!!action.command&&action.exit_code===0&&Number.isInteger(action.duration_ms)&&action.duration_ms>=0&&Number.isInteger(action.argument_count)&&action.argument_count>=0&&/^[a-f0-9]{64}$/.test(action.args_sha256??'')&&listed.get(action.stdout_log)===action.stdout_sha256&&listed.get(action.stderr_log)===action.stderr_sha256);
    harness.assert('Every bootstrap log belongs to exactly one actual command',()=>listed.size===report.actions.length*2&&new Set(report.actions.flatMap(action=>[action.stdout_log,action.stderr_log])).size===listed.size);
    harness.artifact(reference.path);
  });
}
/** Imported by the trusted bootstrap launcher; setupWitness is executed-process evidence, not a CLI skip flag. */
export async function main(target, options = {}) {
  const invocation = options.bootstrapEvidence?.invocation ?? options.setupWitness?.report?.invocation ?? randomUUID(), harness = createHook(target, invocation);
  const config = readKitConfig(harness.context.root,true,target);
  if (options.bootstrapEvidence?.started && Number.isFinite(Date.parse(options.bootstrapEvidence.started))) harness.context.started = options.bootstrapEvidence.started;
  else if (options.setupWitness?.report?.started && Number.isFinite(Date.parse(options.setupWitness.report.started))) harness.context.started = options.setupWitness.report.started;
  removeFreshEvidence(harness.context);
  try {
    if(options.bootstrapEvidence)appendBootstrapEvidence(harness,options.bootstrapEvidence);
    if(config.ui_adoption)harness.check('ui-adoption',()=>{
      let plan;
      harness.assert('Actual staged original SDK and receipt bind current configuration',()=>{plan=inspectUiAdoption(harness.context.root,config,loadKit(harness.context.root));return plan.mode==='staged-react'&&plan.pending===true;});
      harness.uiAdoption(uiAdoptionPending(plan));
      const relative=`.gate/${target.replaceAll(':','-')}/ui-adoption-evidence.json`,file=path.join(harness.context.root,relative);
      fs.mkdirSync(path.dirname(file),{recursive:true});fs.writeFileSync(file,JSON.stringify({schema:1,sha:harness.context.sha,tree_sha256:harness.context.tree_sha256,ui_adoption:harness.ui_adoption,original_receipt:plan.receipt},null,2)+'\n');harness.artifact(relative);
    });
    if(harness.checks.some(check=>check.status==='fail'))return await writeResult(harness,config);
    if (['unit', 'full', 'build', 'baseline', 'e2e', 'perf'].includes(target)) {
      if (options.setupWitness) appendReport(harness, validateSetupWitness(options.setupWitness, harness.context));
      else executeHook(harness, 'setup');
      if (harness.checks.some(check => check.status === 'fail')) return await writeResult(harness, config);
    }
    switch (target) {
      case 'unit': case 'full': common(harness, config); executeHook(harness, target); break;
      case 'deps': executeHook(harness, 'deps');
        for (const required of ['npm-lock', 'go-mod-tidy']) if (!harness.checks.some(check => check.name === required)) throw Error(`Actual dependency check absent: ${required}`);
        validateDependencyActions(harness.actions);
        break;
      case 'gen':
        if (process.env.GATE_VERSIONS_RESOLVE === '1') {
          harness.check('versions-resolve', () => harness.run('bash', [kitScript(config, 'resolve-versions.sh')]));
          harness.check('deps', () => {
            fs.rmSync(path.join(harness.context.root, '.gate/deps/result.json'), { force: true });
            harness.run('task', ['--silent', 'deps']);
            const result = JSON.parse(fs.readFileSync(path.join(harness.context.root, '.gate/deps/result.json')));
            harness.assert('Actual dependency result must pass current SHA/tree', () => result.status === 'pass' && result.sha === harness.context.sha && result.tree_sha256 === harness.context.tree_sha256 && result.checks.some(check => check.name === 'npm-lock' && check.status === 'pass') && result.checks.some(check => check.name === 'go-mod-tidy' && check.status === 'pass'));
          });
        }
        executeHook(harness, 'gen'); break;
      case 'assets:sync': executeHook(harness, 'assets-sync'); break;
      case 'build': executeHook(harness, 'build');
        if (!harness.artifacts.length) throw Error('Build hook produced no actual artifacts');
        break;
      case 'image':
        harness.check('app-image', () => { harness.assert('Immutable executed app image ID required', () => /^sha256:[a-f0-9]{64}$/.test(process.env.GATE_APP_IMAGE_ID ?? '')); harness.artifacts.push(`app-image ${process.env.GATE_APP_IMAGE} ${process.env.GATE_APP_IMAGE_ID}`); }); break;
      case 'baseline': executeHook(harness, 'baseline');
        if (!harness.artifacts.some(item => item.startsWith('baselines/'))) throw Error('Baseline hook captured no actual screenshots'); break;
      case 'legacy:freeze': executeHook(harness, 'legacy-freeze'); break;
      case 'versions:check': validation(harness,config,'versions-check',process.execPath,[kitScript(config,'versions-check.mjs')]); break;
      case 'versions:resolve': throw Error('Resolution trigger is gen --resolve-versions only');
      case 'golden:capture': case 'golden:verify': case 'contract:refresh': throw Error(`${target} lands in S0b/app session; no passing stub`);
      case 'e2e': case 'perf': executeHook(harness, target); break;
      default: throw Error(`Unknown substantive gate target: ${target}`);
    }
  } catch (error) { harness.checks.push({ name: 'runner', status: 'fail', reason: error.message, duration_ms: 0 }); }
  return writeResult(harness, config);
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  if (process.argv.length !== 3) { process.stderr.write('Usage: run-task.mjs <target>\n'); process.exitCode = 1; }
  else main(process.argv[2]).catch(error => { process.stderr.write(error.message + '\n'); process.exitCode = 1; });
}
