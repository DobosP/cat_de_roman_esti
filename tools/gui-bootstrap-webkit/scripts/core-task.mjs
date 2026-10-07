import * as fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { createRequire } from 'node:module';
import { regularPath } from './locate-kit.mjs';
import { createHook,validation } from './run-task.mjs';
import { collectAstArtifacts } from './ast-artifacts.mjs';
import { npmArchive, isPythonBytecodePath } from './kit-sync.mjs';

const digest = bytes => createHash('sha256').update(bytes).digest('hex');
export function walk(directory, filename) {
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap(entry => {
    if (isPythonBytecodePath(entry.name)) return [];
    if (['node_modules', '.git', '.gate', '.vitest', 'dist', 'test-results', 'testdata', 'templates', 'kit', 'third_party', 'vendor'].includes(entry.name)) return [];
    if (entry.isSymbolicLink()) throw Error('Symlink in source discovery');
    const file = path.join(directory, entry.name);
    return entry.isDirectory() ? walk(file, filename) : entry.name === filename ? [file] : [];
  });
}
function modules(hook) {
  const result = walk(hook.context.root, 'go.mod').map(file => path.dirname(file));
  if (!result.length) throw Error('No actual Go modules found'); return result;
}
function packages(hook) { return walk(hook.context.root, 'package.json').map(file => path.dirname(file)); }
function workspaceMembers(rootManifest) {
  const entries = Array.isArray(rootManifest.workspaces) ? rootManifest.workspaces : rootManifest.workspaces?.packages ?? [];
  return entries;
}
function dependencyPackages(hook) {
  const rootManifest = JSON.parse(fs.readFileSync(path.join(hook.context.root, 'package.json'))), members = workspaceMembers(rootManifest);
  return packages(hook).filter(directory => directory === hook.context.root || !members.some(pattern => pattern === path.relative(hook.context.root, directory) || (pattern.endsWith('/*') && path.relative(hook.context.root, directory).startsWith(pattern.slice(0, -1)))));
}
function events(output) { return output.split('\n').filter(line => line.startsWith('{')).map(line => JSON.parse(line)); }
function script(hook, name) { return path.join(hook.context.root, 'web-kit/scripts', name); }
function objectFields(value, fields) {
  return !!value && typeof value === 'object' && !Array.isArray(value) && Object.keys(value).length === fields.length && fields.every(field => Object.hasOwn(value, field));
}
function lockedQualitySource(hook, name, source) {
  const lock = JSON.parse(fs.readFileSync(path.join(hook.context.root, 'versions.lock.json'))), pin = lock.tools.find(tool => tool.tool === name);
  let directory = path.dirname(source), manifest;
  while (directory !== path.dirname(directory)) {
    const file = path.join(directory, 'package.json');
    if (fs.existsSync(file)) { const candidate = JSON.parse(fs.readFileSync(file)); if (candidate.name === name) { manifest = candidate; break; } }
    directory = path.dirname(directory);
  }
  hook.assert(`Actual installed ${name} source has the locked package version`, () => !!pin?.version && manifest?.version === pin.version);
  return digest(fs.readFileSync(source));
}
/** A passed browser lane also publishes freshly bound, inspectable actual quality measurements. */
function acceptQualityMeasurement(hook, lane, laneStarted) {
  const relative = `.gate/full/${lane}-measurement.json`, filename = regularPath(hook.context.root, relative), stat = fs.lstatSync(filename);
  // List the actual bytes before validation too, so an invalid measurement remains inspectable on failure.
  hook.artifact(relative);
  const report = JSON.parse(fs.readFileSync(filename));
  const fields = lane === 'axe' ? ['schema', 'sha', 'tree_sha256', 'app_image_id', 'pages'] : ['schema', 'sha', 'tree_sha256', 'app_image_id', 'route', 'source_sha256', 'throttle', 'interactions', 'metrics', 'actual', 'limits'];
  hook.assert(`Fresh complete source/image-bound ${lane} measurement`, () => stat.isFile() && stat.mtimeMs >= laneStarted && stat.mtimeMs >= Date.parse(hook.context.started) && objectFields(report, fields) && report.schema === 1 && report.sha === hook.context.sha && report.tree_sha256 === hook.context.tree_sha256 && /^sha256:[a-f0-9]{64}$/.test(process.env.GATE_APP_IMAGE_ID ?? '') && report.app_image_id === process.env.GATE_APP_IMAGE_ID);
  const routeFile = regularPath(hook.context.root, '.gate/full/budget-routes.json'), routeStat = fs.lstatSync(routeFile), routes = JSON.parse(fs.readFileSync(routeFile));
  hook.assert('Fresh actual exported page registrations required for browser quality', () => routeStat.isFile() && routeStat.mtimeMs >= Date.parse(hook.context.started) && Array.isArray(routes) && routes.length > 0);
  const pages = routes.filter(route => route.template).map(route => route.path === '/{$}' ? '/' : route.path).sort();
  hook.assert('Actual exported HTML page paths must be nonempty and distinct', () => pages.length > 0 && new Set(pages).size === pages.length && pages.every(route => typeof route === 'string' && route.startsWith('/') && !route.startsWith('//')));
  const require = createRequire(new URL('../playwright/index.mjs', import.meta.url));
  if (lane === 'axe') {
    const sourceHash = lockedQualitySource(hook, 'axe-core', require.resolve('axe-core'));
    hook.assert('Actual axe coverage equals every exported sample page', () => Array.isArray(report.pages) && report.pages.length === pages.length && JSON.stringify(report.pages.map(page => page.route).sort()) === JSON.stringify(pages));
    for (const page of report.pages) hook.assert(`Actual locked axe scan has zero violations: ${page.route}`, () => objectFields(page, ['route', 'fingerprint', 'axe_source_sha256', 'violations', 'passes', 'incomplete']) && page.axe_source_sha256 === sourceHash && Array.isArray(page.violations) && page.violations.length === 0 && page.fingerprint === digest('[]') && Number.isInteger(page.passes) && page.passes > 0 && Number.isInteger(page.incomplete) && page.incomplete >= 0);
  } else {
    const limits = JSON.parse(fs.readFileSync(path.join(hook.context.root, 'budgets.json'))).vitals;
    const source = path.join(path.dirname(require.resolve('web-vitals')), 'web-vitals.iife.js'), sourceHash = lockedQualitySource(hook, 'web-vitals', source);
    hook.assert('Actual vitals match committed route, source, throttle and interactions', () => report.route === '/islands' && pages.includes(report.route) && report.source_sha256 === sourceHash && report.interactions === 5 && objectFields(report.throttle, ['cpu', 'rtt_ms', 'down_kbps']) && Object.keys(report.throttle).every(key => report.throttle[key] === limits.throttle[key]) && objectFields(report.limits, ['lcp_ms', 'inp_ms']) && report.limits.lcp_ms === limits.lcp_ms && report.limits.inp_ms === limits.inp_ms && typeof limits.lcp_ms === 'number' && Number.isFinite(limits.lcp_ms) && limits.lcp_ms > 0 && typeof limits.inp_ms === 'number' && Number.isFinite(limits.inp_ms) && limits.inp_ms > 0);
    hook.assert('Actual nonempty web-vitals browser callback records required', () => Array.isArray(report.metrics) && report.metrics.length >= 2 && report.metrics.every(metric => objectFields(metric, ['name', 'id', 'value', 'rating', 'entries']) && ['LCP', 'INP'].includes(metric.name) && typeof metric.id === 'string' && metric.id.length > 0 && metric.id.length <= 128 && typeof metric.value === 'number' && Number.isFinite(metric.value) && metric.value >= 0 && ['good', 'needs-improvement', 'poor'].includes(metric.rating) && Number.isInteger(metric.entries) && metric.entries > 0));
    const lcp = report.metrics.filter(metric => metric.name === 'LCP').at(-1), inp = report.metrics.filter(metric => metric.name === 'INP').at(-1);
    hook.assert('Final actual vitals agree exactly with browser callbacks and strict committed limits', () => objectFields(report.actual, ['lcp_ms', 'inp_ms']) && !!lcp && !!inp && report.actual.lcp_ms === lcp.value && report.actual.inp_ms === inp.value && lcp.value > 0 && inp.value >= 0 && lcp.value < limits.lcp_ms && inp.value < limits.inp_ms);
    for (const key of ['lcp_ms', 'inp_ms']) {
      // Frozen gate schema uses integer actuals; retain exact callbacks and conservative upward rounding.
      // Fractional committed limits stay exact in the artifact; the frozen integer budget schema cannot represent them.
      if (!Number.isInteger(limits[key])) continue;
      const name = `vitals:${key}`;
      hook.assert(`Measured vital budget must not replace another row: ${name}`, () => !Object.hasOwn(hook.budgets, name));
      hook.budgets[name] = { limit: limits[key], actual: Math.ceil(report.actual[key]), status: 'pass', actual_ms: report.actual[key], comparison: '<', rounding: 'ceil', route: report.route, measurement: relative };
    }
  }
}
function unit(hook, full) {
  hook.check('budgets',()=>{
    hook.run(process.execPath,[script(hook,'budgets-test.mjs'),full?'full':'unit']);
    const file=`.gate/${full?'full':'unit'}/budget-measurements.json`,report=JSON.parse(fs.readFileSync(path.join(hook.context.root,file)));
    hook.assert('Actual fresh bound budget report',()=>report.sha===hook.context.sha&&report.tree_sha256===hook.context.tree_sha256&&report.budgets_sha256===digest(fs.readFileSync(path.join(hook.context.root,'budgets.json')))&&report.report.status==='pass'&&Object.keys(report.budgets).length>0);
    Object.assign(hook.budgets,report.budgets);hook.artifact(file);
    for(const name of ['budget-go.json','budget-routes.json','budget-bindings.json'])hook.artifact(`.gate/${full?'full':'unit'}/${name}`);
  });
  hook.check('schemas',()=>hook.run(process.execPath,[script(hook,'schema-test.mjs')]));
  hook.check('template-identity',()=>{hook.run(process.execPath,[script(hook,'template-identity.mjs')]);hook.run(process.execPath,[script(hook,'wrapper-config-test.mjs')]);hook.run(process.execPath,[script(hook,'bootstrap-current-test.mjs')]);});
  hook.check('validation-fixtures',()=>hook.run(process.execPath,['--test',script(hook,'validation-self-test.mjs')]));

  hook.check('tsc', () => { hook.run('npm', ['run', 'typecheck']); hook.run(process.execPath, [script(hook, 'declarations-check.mjs')]); });
  hook.check('oxlint', () => hook.run('npm', ['run', 'lint']));
  validation(hook,null,'v11-lint',process.execPath,[script(hook,'ast-check.mjs')]);
  hook.check('ast-fixtures',()=>{
    let stdout,failure;try{stdout=hook.run(process.execPath,[script(hook,'ast-check.mjs'),'--self-test']);}catch(error){failure=error;stdout=error.stdout;}
    const report=JSON.parse(stdout);collectAstArtifacts(hook,report);if(failure)throw failure;
    hook.assert('Actual AST fixtures must pass',()=>report.schema===1&&report.check==='ast-self-test'&&report.status==='pass');
  });
  hook.check('vitest-browser', () => hook.run('npm', ['test']));
  hook.check('go-vet', () => { for (const directory of modules(hook)) hook.run('go', ['vet', './...'], directory); });
  hook.check('go-test-race', () => {
    for (const directory of modules(hook)) {
      const actual = events(hook.run('go', ['test', '-race', '-json', '-count=1', './...'], directory, { CGO_ENABLED: '1' }));
      hook.assert(`Actual Go tests required: ${path.relative(hook.context.root, directory)}`, () => actual.some(event => event.Test && event.Action === 'pass') && !actual.some(event => event.Action === 'fail') && (full ? !actual.some(event => event.Action === 'skip') : actual.filter(event => event.Action === 'skip').every(event => event.Test === 'TestPostgresLive' && !process.env.GATE_DB_DSN)));
    }
  });
  hook.check('docs-gate', () => hook.run('python3', ['-B', path.join(hook.context.root, 'web-kit/lint/docs_gate.py'), '.']));
  hook.check('go-mod-tidy', () => { for (const directory of modules(hook)) hook.run('go', ['mod', 'tidy', '-diff'], directory); });
  hook.check('gen-check', () => hook.run(process.execPath, [script(hook, 'gen-check.mjs')]));
  hook.check('templ-check', () => {
    const report=JSON.parse(hook.run(process.execPath,[script(hook,'templ-check.mjs')]));
    hook.assert('Actual templ generate/fmt checks must retain source and committed Go bytes',()=>report.status==='pass'&&report.bytes_retained===true&&report.checks.length===2&&report.checks.every(check=>check.command==='templ'&&check.exit_code===0));
  });
  hook.check('css-measurements', () => { hook.run('npm', ['run', 'build']); hook.run(process.execPath, [script(hook, 'measure-css.mjs'), full ? 'full' : 'unit']); });
  hook.check('precompression',()=>{hook.run('npm',['run','build:sample']);hook.run(process.execPath,[script(hook,'precompression-check.mjs'),full?'full':'unit']);});
  hook.check('runtime-measurements', () => hook.run(process.execPath, [script(hook, 'measure-runtime.mjs'), full ? 'full' : 'unit']));
  hook.check('go-distribution',()=>hook.run(process.execPath,[script(hook,'go-distribution-test.mjs'),full?'full':'unit']));
  hook.check('npm-distribution',()=>{
    let stdout,failure;try{stdout=hook.run(process.execPath,[script(hook,'npm-distribution-test.mjs'),full?'full':'unit']);}catch(error){failure=error;stdout=error.stdout;}
    const report=JSON.parse(stdout),seen=new Set(),prefix=`.gate/${full?'full':'unit'}/npm-distribution-raw-`;
    for(const item of report.raw_artifacts??[]){
      const filename=regularPath(hook.context.root,item.path),bytes=fs.readFileSync(filename);
      hook.assert('Fresh independently hashed distribution native artifact',()=>item.path.startsWith(prefix)&&!seen.has(item.path)&&item.bytes===bytes.length&&item.sha256===digest(bytes)&&fs.statSync(filename).mtimeMs>=Date.parse(hook.context.started));
      seen.add(item.path);hook.artifact(item.path);
    }
    if(failure)throw failure;hook.assert('Actual complete distribution proof required',()=>report.schema===1&&report.check==='npm-distribution'&&report.status==='pass'&&report.packages?.length===2&&report.proofs?.length>0&&report.commands?.length>0&&seen.size>0);
  });
  if (!full) hook.skip('pg-live', 'no-dsn', () => !process.env.GATE_DB_DSN);
  else {
    hook.check('pg-live', () => {
      hook.assert('Full requires live disposable DSN', () => !!process.env.GATE_DB_DSN);
      const actual = events(hook.run('go', ['test', '-race', '-json', '-run', '^TestPostgresLive$', '-count=1', './...'], path.join(hook.context.root, 'web-kit/sample'), { CGO_ENABLED: '1' }));
      hook.assert('Live Postgres test absent/skipped', () => actual.some(event => event.Test === 'TestPostgresLive' && event.Action === 'run') && actual.some(event => event.Test === 'TestPostgresLive' && event.Action === 'pass') && !actual.some(event => event.Action === 'skip' || event.Action === 'fail'));
    });
    hook.check('app-healthy', () => hook.run(process.execPath, [script(hook, 'app-health.mjs')]));
    for (const lane of ['pw-islands', 'pw-behaviors', 'pw-motion', 'pw-journeys', 'axe', 'vitals', 'csp-trap']) hook.check(lane, () => {
      const laneStarted = Date.now();
      if (lane === 'axe' || lane === 'vitals') fs.rmSync(path.join(hook.context.root, `.gate/full/${lane}-measurement.json`), { force: true });
      hook.run(process.execPath, [script(hook, 'browser-lane.mjs'), lane, 'full']);
      if (lane === 'axe' || lane === 'vitals') acceptQualityMeasurement(hook, lane, laneStarted);
    });
    hook.check('screenshots', () => runScreenshots(hook, 'verify'));
  }
}
function assetsSync(hook) {
  hook.check('assets-sync', () => {
    hook.run('npm', ['run', 'build']); hook.run('npm', ['run', 'build:sample']);
    const source = fs.readFileSync(path.join(hook.context.root, 'versions.lock.json')), destination = path.join(hook.context.root, 'web-kit/sample/embedfs/versions.lock.json');
    fs.writeFileSync(destination, source); hook.assert('Embedded lock copy must match', () => fs.readFileSync(destination).equals(source));
  });
}
function copyFileIfExists(source, destination) { if (fs.existsSync(source)) fs.copyFileSync(source, destination); }
export function packageSource(source, destination) {
  fs.mkdirSync(destination, { recursive: true });
  const manifest = JSON.parse(fs.readFileSync(path.join(source, 'package.json')));
  for (const name of ['package.json', 'README.md', 'LICENSE', 'LICENSE.md', 'LICENSE.txt', 'NOTICE', '.npmrc']) copyFileIfExists(path.join(source, name), path.join(destination, name));
  for (const entry of manifest.files ?? []) {
    if (typeof entry !== 'string' || entry.startsWith('/') || entry.split('/').includes('..') || entry.includes('*')) throw Error('Package files need explicit safe paths');
    const file = path.join(source, entry); if (fs.existsSync(file)) fs.cpSync(file, path.join(destination, entry), { recursive: true, dereference: false, filter: from => !isPythonBytecodePath(path.relative(source, from)) });
  }
  return manifest;
}
// npm 12 pack JSON is keyed by owner, rather than the pre-12 array shape.
function packedOwner(output, manifest) {
  const data=JSON.parse(output);
  if(!data||typeof data!=='object'||Array.isArray(data)||Object.keys(data).length!==1||!Object.hasOwn(data,manifest.name))throw Error('Actual npm12 pack must return exactly the owning package key');
  const packed=data[manifest.name];
  if(!packed||packed.name!==manifest.name||packed.version!==manifest.version||packed.filename!==`${manifest.name.replace('@','').replace('/','-')}-${manifest.version}.tgz`)throw Error('Actual npm pack owner/version/filename differs');
  return packed;
}
function build(hook) {
  assetsSync(hook);
  hook.check('sample-build', () => {
    const destination = path.join(hook.context.root, '.gate/build/sample-app'); fs.mkdirSync(path.dirname(destination), { recursive: true });
    hook.run('go', ['build', '-trimpath', '-o', destination, '.'], path.join(hook.context.root, 'web-kit/sample'), { CGO_ENABLED: '0' });
    hook.assert('Actual sample executable required', () => fs.statSync(destination).size > 0); hook.artifact('.gate/build/sample-app');
  });
  hook.check('build', () => {
    const output = path.join(hook.context.root, '.gate/build'); fs.mkdirSync(output, { recursive: true });
    const staging = fs.mkdtempSync(path.join(output, '.pack-source-'));
    try {
      const uiManifest = packageSource(hook.context.root, staging), kitManifest = packageSource(path.join(hook.context.root, 'web-kit'), path.join(staging, 'web-kit'));
      const lock = fs.readFileSync(path.join(hook.context.root, 'versions.lock.json'));
      fs.writeFileSync(path.join(staging, 'web-kit/versions.lock.json'), lock);
      const uiPack = packedOwner(hook.run('npm', ['pack', staging, '--json', '--ignore-scripts', '--workspaces=false', '--pack-destination', output], staging), uiManifest);
      const kitSource=path.join(staging,'web-kit');
      const kitPack = packedOwner(hook.run('npm', ['pack', kitSource, '--json', '--ignore-scripts', '--workspaces=false', '--pack-destination', output], kitSource), kitManifest);
      hook.assert('Both actual npm package identities required', () => uiPack.name === '@roedu/ui' && kitPack.name === '@roedu/web-kit' && uiPack.version === uiManifest.version && kitPack.version === kitManifest.version);
      const archiveProof=[];
      for(const [pack,owner] of [[uiPack,staging],[kitPack,kitSource]]) {
        const bytes=fs.readFileSync(path.join(output,pack.filename)),parsed=npmArchive(bytes,pack.name,pack.filename),members=[];
        hook.assert('Actual build TGZ contains no compiler build state',()=>Array.isArray(pack.files)&&!pack.files.some(file=>/\.tsbuildinfo(?:\.(?:gz|br))?$/.test(file.path)||isPythonBytecodePath(file.path))&&![...parsed.entries.keys()].some(file=>/\.tsbuildinfo(?:\.(?:gz|br))?$/.test(file)||isPythonBytecodePath(file)));
        for(const [name,entry] of parsed.entries)if(entry.type==='file') {
          const relative=name.slice('package/'.length),source=path.join(owner,relative),stat=fs.lstatSync(source);
          // Pinned npm packs use portable tar permissions: owning read/write,
          // no group/other write. Accepted native packs show 0664 -> 0644 and
          // 0775 -> 0755; raw checkout group-write bits are not shipped.
          const portableMode=(stat.mode|0o600)&0o755;
          hook.assert('Actual archive member preserves prepared bytes and portable npm mode',()=>stat.isFile()&&!stat.isSymbolicLink()&&fs.readFileSync(source).equals(entry.data)&&portableMode===entry.mode);
          members.push({path:relative,bytes:entry.data.length,source_mode:stat.mode&0o777,mode:entry.mode,sha256:digest(entry.data)});
        }
        archiveProof.push({name:pack.name,version:parsed.manifest.version,file:pack.filename,archive_sha256:digest(bytes),compiler_state_members:0,python_bytecode_members:0,members:members.sort((a,b)=>a.path.localeCompare(b.path))});
      }
      const proofFile='.gate/build/npm-archive-proof.json';
      fs.writeFileSync(path.join(hook.context.root,proofFile),JSON.stringify({schema:1,sha:hook.context.sha,tree_sha256:hook.context.tree_sha256,toolchain_digest:hook.context.toolchain_digest,packages:archiveProof},null,2)+'\n');hook.artifact(proofFile);
      const files = [uiPack.filename, kitPack.filename, 'versions.lock.json']; fs.writeFileSync(path.join(output, 'versions.lock.json'), lock);
      const hashes = Object.fromEntries(files.map(file => [file, digest(fs.readFileSync(path.join(output, file)))]));
      fs.writeFileSync(path.join(output, 'SHA256SUMS'), files.map(file => `${hashes[file]}  ${file}\n`).join(''));
      const manifest = { schema: 1, source_sha: hook.context.sha, source_tree_sha256: hook.context.tree_sha256, toolchain_digest: hook.context.toolchain_digest, versions_lock_sha256: digest(lock), release_state: 'qualification bundle; release tag and owning-tag Go source archive require parent release', packages: [{ name: '@roedu/ui', version: uiManifest.version, file: files[0] }, { name: '@roedu/web-kit', version: kitManifest.version, file: files[1] }], files: hashes };
      fs.writeFileSync(path.join(output, 'kit-manifest.json'), JSON.stringify(manifest, null, 2) + '\n');
      for (const file of [...files, 'SHA256SUMS', 'kit-manifest.json']) hook.artifact(`.gate/build/${file}`);
      hook.assert('Packed bundle files are nonempty', () => files.every(file => fs.statSync(path.join(output, file)).size > 0));
    } finally { fs.rmSync(staging, { recursive: true, force: true }); }
  });
}
function runScreenshots(hook, mode) {
  const target=mode==='capture'?'baseline':'full',started=Date.now(),relative=`.gate/${target}/screenshots.json`;
  fs.rmSync(path.join(hook.context.root,relative),{force:true});
  let stdout,failure;try{stdout=hook.run(process.execPath,[script(hook,'screenshots.mjs'),mode]);}catch(error){failure=error;stdout=error.stdout;}
  const report=JSON.parse(stdout),filename=regularPath(hook.context.root,relative),bytes=fs.readFileSync(filename);
  // List actual failure diagnostics and PNGs before deciding whether the check passed.
  hook.artifact(relative);
  const saved=JSON.parse(bytes);hook.assert('Printed screenshot report equals retained actual receipt',()=>JSON.stringify(saved)===JSON.stringify(report));
  for(const record of report.pages??[])if(record.actual_file){
    const file=regularPath(hook.context.root,record.actual_file),png=fs.readFileSync(file);hook.artifact(record.actual_file);
    hook.assert('Actual screenshot PNG path/hash/freshness binding',()=>record.actual_file===`.gate/${target}/screenshots/${path.basename(record.file)}`&&png.length===record.bytes&&digest(png)===record.sha256&&fs.statSync(file).mtimeMs>=started);
  }
  if(failure)throw failure;
  hook.assert('Actual six-page source/image-bound screenshot result',()=>report.schema===1&&report.mode===mode&&report.status==='pass'&&report.sha===hook.context.sha&&report.tree_sha256===hook.context.tree_sha256&&report.app_image_id===process.env.GATE_APP_IMAGE_ID&&fs.statSync(filename).mtimeMs>=started&&Array.isArray(report.pages)&&report.pages.length===6);
  return report;
}
function baseline(hook) {
  hook.check('baseline-app-healthy', () => hook.run(process.execPath, [script(hook, 'app-health.mjs')]));
  hook.check('baseline-capture', () => {
    const report=runScreenshots(hook,'capture');
    for(const record of report.pages)hook.artifact(record.file);
    hook.artifact('baselines/core/chromium/capture.json');
  });
}

export function coreTask(target, invocation) {
  const hook = createHook(target, invocation);
  switch (target) {
    case 'setup': hook.check('npm-lock', () => { hook.run('npm', ['ci']); hook.run(process.execPath, [script(hook, 'npm-file-test.mjs')]); }); break;
    case 'unit': case 'full': unit(hook, target === 'full'); break;
    case 'deps':
      hook.check('npm-lock', () => { for (const directory of dependencyPackages(hook)) hook.run('npm', ['install', '--package-lock-only', '--ignore-scripts'], directory); });
      hook.check('go-mod-tidy', () => { for (const directory of modules(hook)) hook.run('go', ['mod', 'tidy'], directory); }); break;
    case 'gen':
      hook.check('tokens-generate', () => hook.run(process.execPath, [path.join(hook.context.root, 'src/tokens/generate.mjs')]));
      hook.check('templ-format-preview', () => {
        const source=path.join(hook.context.root,'web-kit/sample/sample.templ'),before=fs.readFileSync(source),preview=path.join(hook.context.root,'.gate/gen/formatted/sample.templ');
        fs.mkdirSync(path.dirname(preview),{recursive:true});fs.writeFileSync(preview,before);
        hook.run('templ',['fmt','-prettier-required=false',preview]);
        hook.assert('Formatting preview preserves authored source',()=>fs.readFileSync(source).equals(before));hook.artifact('.gate/gen/formatted/sample.templ');
      });
      hook.check('templ-generate', () => {
        hook.run('templ', ['generate', '-f', 'sample.templ', '-w', String(hook.context.parallel)], path.join(hook.context.root, 'web-kit/sample'));
        hook.assert('Actual generated templ Go output required',()=>fs.statSync(path.join(hook.context.root,'web-kit/sample/sample_templ.go')).size>0);hook.artifact('web-kit/sample/sample_templ.go');
      }); break;
    case 'assets-sync': assetsSync(hook); break;
    case 'build': build(hook); break;
    case 'baseline': baseline(hook); break;
    case 'legacy-freeze': throw Error('legacy:freeze lands in app session; no passing core stub');
    case 'e2e': case 'perf': throw Error('Core e2e/perf use full qualification; no partial success');
    default: throw Error(`Unknown core repo hook: ${target}`);
  }
  return hook.finish();
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try { const report = coreTask(process.argv[2], process.argv[3]); process.stdout.write(JSON.stringify(report) + '\n'); process.exitCode = report.checks.some(check => check.status === 'fail') ? 1 : 0; }
  catch (error) { process.stderr.write(error.message + '\n'); process.exitCode = 1; }
}
