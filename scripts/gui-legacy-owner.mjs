// UNAPPLIED source proposal for scripts/gui-legacy-owner.mjs.
// Existing createHook APIs only; caller invokes this after actual PG/parity and
// still invokes the unchanged900/browser/baseline command if this check fails.
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
const hash = (bytes) => crypto.createHash('sha256').update(bytes).digest('hex');

function readRegular(file) {
  assert.equal(fs.realpathSync(file), file);
  const fd = fs.openSync(file, fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW);
  try { assert.ok(fs.fstatSync(fd).isFile()); return fs.readFileSync(fd); }
  finally { fs.closeSync(fd); }
}
function writeExclusive(file, bytes) {
  const pending = file + '.pending';
  const fd = fs.openSync(pending, fs.constants.O_WRONLY | fs.constants.O_CREAT | fs.constants.O_EXCL | fs.constants.O_NOFOLLOW, 0o600);
  try { fs.writeFileSync(fd, bytes); fs.fsyncSync(fd); } finally { fs.closeSync(fd); }
  fs.linkSync(pending, file); fs.unlinkSync(pending);
}

export function runOwnerLegacyJourney(hook) {
  const context = hook.context, base = path.join(context.root, '.gate/full');
  hook.check('cat-legacy-owner-journey', () => {
    hook.assert('Actual full context only', () => context.target === 'full');
    const descriptorBytes = readRegular(path.join(base, 'wrapper-current.json'));
    const descriptor = JSON.parse(descriptorBytes);
    hook.assert('Protected actual wrapper/source/tree/toolchain binding', () => descriptor.target === 'full'
      && descriptor.sha === context.sha && descriptor.tree_sha256 === context.tree_sha256
      && descriptor.toolchain_digest === process.env.TOOLCHAIN_DIGEST);
    assert.match(descriptor.invocation, /^[0-9a-f-]{36}$/);
    const parent = path.join(base, 'legacy-owner');
    fs.mkdirSync(parent, { mode: 0o700 });
    const directory = path.join(parent, descriptor.invocation);
    fs.mkdirSync(directory, { mode: 0o700 });
    for (const file of [parent, directory]) {
      assert.equal(fs.realpathSync(file), file); assert.equal(fs.lstatSync(file).uid, process.getuid());
      assert.equal(fs.lstatSync(file).mode & 0o777, 0o700);
    }
    const intent = { schema: 1, target: 'full', run_id: descriptor.invocation,
      runner_invocation: context.invocation, wrapper_invocation: descriptor.invocation,
      descriptor_sha256: hash(descriptorBytes), source_sha: context.sha, tree_sha256: context.tree_sha256,
      toolchain_digest: descriptor.toolchain_digest, app_image_id: process.env.GATE_APP_IMAGE_ID,
      current_manifest_sha256: hash(readRegular(path.join(context.root, 'go-backend/embedfs/dist/.vite/manifest.json'))),
      current_versions_lock_sha256: hash(readRegular(path.join(context.root, 'versions.lock.json'))),
      expected_legacy_policy_stage: process.env.CSP_STAGE };
    assert.match(intent.app_image_id, /^sha256:[0-9a-f]{64}$/);
    assert.ok(['report-only', 'enforced'].includes(intent.expected_legacy_policy_stage));
    const intentPath = path.join(directory, 'intent.json');
    const intentBytes = Buffer.from(JSON.stringify(intent, null, 2) + '\n');
    writeExclusive(intentPath, intentBytes);
    hook.artifact(path.relative(context.root, intentPath));
    try {
      const requestPath = path.join(directory, 'request.json');
      for (const phase of ['preflight', 'observe', 'confirm']) {
        hook.run('node', ['scripts/gui-legacy-owner-probe.mjs', phase, requestPath], context.root);
      }
      const confirmationBytes = readRegular(path.join(directory, 'confirm.json'));
      const actual = JSON.parse(confirmationBytes);
      hook.assert('Genuine same-full legacy observation and owned cleanup', () => actual.status === 'pass'
        && actual.errors.length === 0 && actual.cleanup_verified === true
        && actual.source === context.sha && actual.tree_sha256 === context.tree_sha256
        && actual.wrapper_invocation === descriptor.invocation && actual.runner_invocation === context.invocation
        && actual.app_image_id === process.env.GATE_APP_IMAGE_ID
        && Number.isInteger(actual.legacy_violations) && actual.legacy_violations >= 0);
      writeExclusive(path.join(base, 'legacy-observation.json'), confirmationBytes);
      hook.artifact('.gate/full/legacy-observation.json');
    } catch (error) {
      writeExclusive(path.join(directory, 'abort.json'), Buffer.from(JSON.stringify({ status: 'abort', intent_sha256: hash(intentBytes) }) + '\n'));
      // Wait for the real owner's bounded cleanup even when the browser command failed.
      try { hook.run('node', ['scripts/gui-legacy-owner-probe.mjs', 'confirm', path.join(directory, 'request.json')], context.root); }
      catch { /* The original failed command and cleanup failure remain real recorded actions. */ }
      throw error;
    } finally {
      for (const name of fs.readdirSync(directory)) {
        const file = path.join(directory, name);
        assert.ok(fs.lstatSync(file).isFile() && !fs.lstatSync(file).isSymbolicLink());
        hook.artifact(path.relative(context.root, file));
      }
    }
  });
}

// Use this in gui-full-browser only after executing the unchanged current900,
// asset/active-CSP observations and baseline verification. Never fall back to0.
export function readActualLegacyObservation(root, expected) {
  const bytes = readRegular(path.join(root, '.gate/full/legacy-observation.json'));
  const value = JSON.parse(bytes);
  assert.equal(value.status, 'pass'); assert.deepEqual(value.errors, []);
  assert.equal(value.cleanup_verified, true);
  for (const [key, field] of [['source', 'sha'], ['tree_sha256', 'tree_sha256'],
    ['app_image_id', 'app_image_id'], ['runner_invocation', 'runner_invocation'],
    ['wrapper_invocation', 'wrapper_invocation']]) assert.equal(value[key], expected[field]);
  assert.ok(Number.isInteger(value.legacy_violations) && value.legacy_violations >= 0);
  return { count: value.legacy_violations, sha256: hash(bytes) };
}
