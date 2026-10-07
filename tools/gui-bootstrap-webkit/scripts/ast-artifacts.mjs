import * as fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { regularPath } from './locate-kit.mjs';

/** Add independently hashed current native AST outputs to the aggregate result.
 * Call inside the executed named check, including when the child check failed.
 */
export function collectAstArtifacts(hook, report) {
  if (report.artifacts === undefined) return;
  if (!Array.isArray(report.artifacts)) throw Error('AST artifacts must be an array');
  const target = hook.context.target.replaceAll(':', '-');
  const prefix = `.gate/${target}/ast-native/`;
  const seen = new Set();
  for (const reference of report.artifacts) {
    const match = typeof reference === 'string' && /^(\.gate\/[A-Za-z0-9-]+\/ast-native\/[A-Za-z0-9._/-]+) sha256:([a-f0-9]{64})$/.exec(reference);
    if (!match || !match[1].startsWith(prefix) || seen.has(match[1])) throw Error('Invalid, duplicate or cross-target AST artifact');
    seen.add(match[1]);
    const file = regularPath(hook.context.root, match[1]), stat = fs.statSync(file);
    const actual = createHash('sha256').update(fs.readFileSync(file)).digest('hex');
    hook.assert(`Fresh actual native AST artifact: ${path.basename(file)}`, () => stat.isFile() && stat.mtimeMs >= Date.parse(hook.context.started) && actual === match[2]);
    hook.artifact(match[1]);
  }
}
