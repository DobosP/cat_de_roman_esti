import * as fs from 'node:fs';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import assert from 'node:assert/strict';

assert.equal(process.argv.length, 2, 'Usage: templ-check.mjs');
const sample = 'web-kit/sample';
const source = `${sample}/sample.templ`, generated = `${sample}/sample_templ.go`;
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
const read = file => { assert.ok(fs.lstatSync(file).isFile() && !fs.lstatSync(file).isSymbolicLink(), 'templ qualification requires actual regular source/output'); return fs.readFileSync(file); };
const sourceBytes = read(source), generatedBytes = read(generated);
assert.ok(sourceBytes.length && generatedBytes.length, 'Authored templ and actual committed generated Go must both exist');
const workers = Number(process.env.GOMAXPROCS);
assert.ok(Number.isInteger(workers) && workers > 0, 'Native wrapper worker binding required');
const report = { schema: 1, status: 'fail', workers, source: { file: source, sha256: digest(sourceBytes) }, generated: { file: generated, sha256: digest(generatedBytes) }, checks: [] };
try {
  for (const args of [['generate', '-check', '-path', sample, '-w', String(workers)], ['fmt', '-fail', '-prettier-required=false', source]]) {
    const started = Date.now(), result = spawnSync('templ', args, { encoding: 'utf8', maxBuffer: 16 * 1024 * 1024 });
    report.checks.push({ command: 'templ', args, exit_code: result.status ?? -1, duration_ms: Date.now() - started, stdout_sha256: digest(result.stdout ?? ''), stderr_sha256: digest(result.stderr ?? '') });
    if (result.stdout) process.stderr.write(result.stdout); if (result.stderr) process.stderr.write(result.stderr);
    assert.equal(result.status, 0, `Actual templ ${args[0]} qualification failed`);
  }
  report.status = 'pass';
} catch (error) {
  report.error = error.message;
} finally {
  report.source_after_sha256 = digest(read(source)); report.generated_after_sha256 = digest(read(generated));
  report.bytes_retained = report.source_after_sha256 === report.source.sha256 && report.generated_after_sha256 === report.generated.sha256;
  if (!report.bytes_retained) { report.status = 'fail'; report.error = 'templ qualification changed authored source or committed generated Go'; }
  process.stdout.write(JSON.stringify(report) + '\n');
  process.exitCode = report.status === 'pass' ? 0 : 1;
}
