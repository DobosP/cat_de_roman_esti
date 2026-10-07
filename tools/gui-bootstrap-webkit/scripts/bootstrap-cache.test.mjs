// Synthetic input/launcher fixtures only. This never qualifies an application,
// original Cat runtime, release archive, or installed SDK. The baseline child
// deliberately fails after recording that the genuine bootstrap reached it.
import * as fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { spawnSync } from 'node:child_process';
import { randomUUID } from 'node:crypto';
import { verifyInputs, readTarGz } from './kit-bootstrap.mjs';
import { fixtureArchive, fixtureHash, makeUiAdoptionFixture } from './ui-adoption-fixture.mjs';

test('actual reusable and inline bootstrap reject cache in each sealed archive before launching', t => {
  assert.equal(process.platform, 'linux'); assert.equal(process.cwd(), '/work');
  const base = '/scratch/_temp'; assert.equal(fs.realpathSync(base), base);
  assert.ok(fs.lstatSync(base).isDirectory() && !fs.lstatSync(base).isSymbolicLink());
  const root = fs.mkdtempSync(path.join(base, 'synthetic-bootstrap-cache-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const f = makeUiAdoptionFixture(root), observations = [];
  const json = value => Buffer.from(JSON.stringify(value, null, 2) + '\n');
  const taskfileBytes = fs.readFileSync('Taskfile.yml'), taskfile = taskfileBytes.toString('utf8');
  assert.ok(taskfileBytes.equals(Buffer.from(taskfile)), 'trusted Taskfile bytes must be UTF-8');
  const marker = '  _KIT_SYNC_JS: |\n', start = taskfile.indexOf(marker);
  assert.ok(start >= 0 && taskfile.lastIndexOf(marker) === start, 'exactly one actual protected inline bootstrap scalar required');
  const lines = [];
  for (const line of taskfile.slice(start + marker.length).split('\n')) {
    if (line && !line.startsWith('    ')) break;
    lines.push(line ? line.slice(4) : '');
  }
  const inline = lines.join('\n').replace(/\n+$/, '') + '\n';
  assert.ok(inline.includes('function verifyInputs(root)') && inline.includes('bootstrapKitSync();'), 'execute the whole actual inline program, not a copied predicate or parser');
  const python = Buffer.from('# Synthetic owning Python source remains byte-identical.\n');
  const launchMarker = 'synthetic-launch-marker.json';
  const launcher = Buffer.from(`import fs from 'node:fs';\nfs.writeFileSync('${launchMarker}',JSON.stringify({synthetic:true,launcher_reached:true})+'\\n');\nprocess.stdout.write(JSON.stringify({mode:'sync',status:'fail',tag:'core-v1.1',checks:[{name:'synthetic-launcher-only',status:'fail',reason:'no application qualification',duration_ms:0}]})+'\\n');\nprocess.exitCode=1;\n`);
  const owners = [
    { filename: f.selected.filename, files: new Map([...f.selected.files, ['package/dist/fixture-source.py', python]]), source: 'package/dist/fixture-source.py', cachePrefix: 'package/dist/' },
    { filename: f.bundle.kitName, files: new Map([...f.bundle.kitFiles, ['package/scripts/kit-sync.mjs', launcher], ['package/lint/fixture-source.py', python]]), source: 'package/lint/fixture-source.py', cachePrefix: 'package/lint/' },
    { filename: f.bundle.goName, files: new Map([...f.bundle.goFiles, ['web-kit/tokens/fixture-source.py', python]]), source: 'web-kit/tokens/fixture-source.py', cachePrefix: 'web-kit/tokens/' }
  ];
  const clean = new Map(owners.map(owner => [owner.filename, fixtureArchive(owner.files)]));
  function seal(changedName, changedBytes) {
    const selected = new Map(clean); if (changedName) selected.set(changedName, changedBytes);
    for (const [filename, bytes] of selected) f.put('kit/' + filename, bytes);
    f.put('kit/SHA256SUMS', [...selected].map(([filename, bytes]) => `${fixtureHash(bytes)}  ${filename}\n`).join(''));
    return [...selected].map(([filename, bytes]) => ({ filename, sha256: fixtureHash(bytes) }));
  }
  const env = { ...process.env, GATE_SHA: 'a'.repeat(40), GATE_TREE_SHA256: 'b'.repeat(64), TOOLCHAIN_DIGEST: 'sha256:' + 'c'.repeat(64), GATE_DIRTY: 'false', GOMAXPROCS: '4', CSP_STAGE: 'report-only' };
  const config = { role: 'consumer', app: 'bootstrap_cache_fixture', npm_dir: 'frontend/node_modules/@roedu/web-kit', vendor_dir: 'frontend/vendor', go_dirs: ['server'] };
  const captured = { schema: 1, target: 'kit:sync', sha: env.GATE_SHA, tree_sha256: env.GATE_TREE_SHA256, toolchain_digest: env.TOOLCHAIN_DIGEST, config, config_sha256: fixtureHash(JSON.stringify(config)) };
  const metadata = json(captured), configPath = '.gate/kit-sync/wrapper-kit-config.json';
  const descriptor = { schema: 1, invocation: randomUUID(), target: 'kit:sync', sha: captured.sha, tree_sha256: captured.tree_sha256, toolchain_digest: captured.toolchain_digest, config_sha256: captured.config_sha256, config_path: configPath, config_file_sha256: fixtureHash(metadata) };
  f.put(configPath, metadata); f.put('.gate/wrapper-current.json', json(descriptor)); f.put('.gate/kit-sync/wrapper-current.json', json(descriptor));
  f.put('.gate.env', `TOOLCHAIN_DIGEST=${env.TOOLCHAIN_DIGEST}\nCSP_STAGE=report-only\nGATE_PARALLEL_MAX=4\n`);
  f.put('versions.lock.json', f.bundle.kitFiles.get('package/versions.lock.json'));
  function executeInline(label, archives) {
    for (const relative of [launchMarker, '.gate/kit-sync/_bootstrap', '.gate/kit-sync/result.json', '.gate/kit-sync/bootstrap-execution.json', '.gate/kit-sync/logs']) fs.rmSync(path.join(root, relative), { recursive: true, force: true });
    const result = spawnSync(process.execPath, ['--input-type=module', '-'], { cwd: root, env, input: inline, encoding: 'utf8', timeout: 30000, maxBuffer: 16 * 1024 * 1024 });
    assert.equal(result.error, undefined, result.error?.message); assert.equal(result.signal, null); assert.equal(result.status, 1, result.stderr);
    const reportBytes = fs.readFileSync(path.join(root, '.gate/kit-sync/result.json')), report = JSON.parse(reportBytes);
    assert.equal(report.status, 'fail'); assert.equal(report.target, 'kit:sync');
    assert.equal(report.sha, captured.sha); assert.equal(report.tree_sha256, captured.tree_sha256); assert.equal(report.toolchain_digest, captured.toolchain_digest);
    const execution = JSON.parse(fs.readFileSync(path.join(root, '.gate/kit-sync/bootstrap-execution.json')));
    // Full actual native streams/outcome and source-program binding survive in
    // the pinned parent test command's TAP diagnostics; no fabricated exit/log.
    observations.push({ label, command: process.execPath, args: ['--input-type=module', '-'], taskfile_sha256: fixtureHash(taskfileBytes), inline_sha256: fixtureHash(inline), archives, exit_code: result.status, signal: result.signal, stdout: result.stdout, stderr: result.stderr, stdout_sha256: fixtureHash(result.stdout), stderr_sha256: fixtureHash(result.stderr), result_sha256: fixtureHash(reportBytes), checks: report.checks, bootstrap_actions: execution.actions });
    return { report, execution };
  }
  const baselineArchives = seal();
  const baseline = verifyInputs(root);
  assert.equal(baseline.tag, 'core-v1.1'); assert.equal(baseline.archive, f.bundle.kitName); assert.deepEqual(baseline.script, launcher);
  for (const owner of owners) assert.deepEqual(readTarGz(fs.readFileSync(path.join(root, 'kit', owner.filename))).get(owner.source)?.data, python);
  const reached = executeInline('valid three-archive baseline preserves .py and reaches deliberately failing synthetic launcher', baselineArchives);
  assert.deepEqual(JSON.parse(fs.readFileSync(path.join(root, launchMarker))), { synthetic: true, launcher_reached: true });
  assert.ok(reached.execution.actions.some(action => action.phase === 'kit-sync' && action.exit_code === 1));
  assert.ok(reached.report.checks.some(check => check.name === 'synthetic-launcher-only' && check.status === 'fail'));
  for (const owner of owners) for (const suffix of ['__pycache__/sentinel', 'loose.pyc', 'nested/loose.pyo.gz', 'nested/loose.pyc.br']) {
    const member = owner.cachePrefix + suffix, archives = seal(owner.filename, fixtureArchive(new Map([...owner.files, [member, Buffer.from('synthetic runtime cache')]])));
    assert.throws(() => verifyInputs(root), error => error.message.includes('Excluded Python bytecode/cache') && error.message.includes(member));
    const refused = executeInline(`${owner.filename}: ${member}`, archives);
    assert.ok(refused.report.checks.some(check => check.status === 'fail' && check.reason?.includes('Excluded Python bytecode/cache') && check.reason.includes(member)), JSON.stringify(refused.report.checks));
    assert.equal(fs.existsSync(path.join(root, launchMarker)), false, 'cache refusal must precede packaged child execution');
    assert.equal(fs.existsSync(path.join(root, '.gate/kit-sync/_bootstrap')), false, 'cache refusal must precede script extraction');
    assert.deepEqual(refused.execution.actions, [], 'input refusal executes no packaged child command');
  }
  seal();
  for (const owner of owners) assert.deepEqual(readTarGz(fs.readFileSync(path.join(root, 'kit', owner.filename))).get(owner.source)?.data, python);
  t.diagnostic(JSON.stringify({ schema: 1, check: 'synthetic-bootstrap-cache-native-observations', qualification: 'input refusal and launcher reach only; every inline result intentionally fails', observations }));
});
