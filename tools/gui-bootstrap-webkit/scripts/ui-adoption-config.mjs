/** Closed Native E1 configuration. Absence is active; only Cat may stage the sealed original SDK. */
export function validateUiAdoption(config) {
  if (!Object.hasOwn(config, 'ui_adoption')) return undefined;
  const phase = config.ui_adoption;
  const fields = (value, keys) => !!value && typeof value === 'object' && !Array.isArray(value) && Object.keys(value).length === keys.length && keys.every(key => Object.hasOwn(value, key));
  if (config.role !== 'consumer' || config.app !== 'cat_de_roman_esti' || !fields(phase, ['mode', 'until', 'legacy']) || phase.mode !== 'staged-react' || phase.until !== 'S1-M2') throw Error('Unsupported or malformed ui_adoption phase');
  const legacy = phase.legacy;
  if (!fields(legacy, ['version', 'archive_sha256', 'source_sha', 'receipt', 'receipt_sha256']) || legacy.version !== '0.3.0' || typeof legacy.archive_sha256 !== 'string' || typeof legacy.source_sha !== 'string' || typeof legacy.receipt_sha256 !== 'string' || !/^[a-f0-9]{64}$/.test(legacy.archive_sha256) || !/^[a-f0-9]{40}([a-f0-9]{24})?$/.test(legacy.source_sha) || !/^[a-f0-9]{64}$/.test(legacy.receipt_sha256)) throw Error('Malformed sealed original UI identity');
  const receipt = legacy.receipt;
  const excluded = new Set(['kit', 'node_modules', 'third_party', 'vendor', 'dist', 'embedfs', 'test-results', 'TASK_BRIEF.md', 'TASK_RESULT.md', 'SWARM_RESULT.md']);
  if (typeof receipt !== 'string' || !receipt || receipt.startsWith('/') || /\.tsbuildinfo(?:\.(?:gz|br))?$/.test(receipt) || receipt.split('/').some(part => !/^[A-Za-z0-9_@.-]+$/.test(part) || part === '.' || part === '..' || part.startsWith('.') || excluded.has(part))) throw Error('Original UI receipt must be a literal source-owned path outside caches, inputs and dependencies');
  if ([config.vendor_dir ?? 'frontend/vendor', config.npm_dir ?? 'frontend/node_modules/@roedu/web-kit'].some(directory => typeof directory === 'string' && (receipt === directory || receipt.startsWith(directory + '/')))) throw Error('Original UI receipt overlaps a configured dependency directory');
  return { mode: 'staged-react', until: 'S1-M2', legacy: { version: '0.3.0', archive_sha256: legacy.archive_sha256, source_sha: legacy.source_sha, receipt, receipt_sha256: legacy.receipt_sha256 } };
}
