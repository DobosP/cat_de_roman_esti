import { readFileSync } from 'node:fs';
import assert from 'node:assert/strict';
// Emitted public entries must keep the committed source surface and declaration dependencies.
for(const entry of ['index','preact/index','behaviors/index','motion/index','net/index','storage/index']) {
  const source=readFileSync(`src/${entry}.ts`,'utf8');
  const decl=readFileSync(`dist/${entry}.d.ts`,'utf8');
  const exports=[...source.matchAll(/export\s+(?:\*\s+from\s+['"]([^'"]+)|\{([^}]+)\})/g)].map(m=>(m[1]??m[2]).replace(/\s/g,''));
  for(const e of exports)assert.ok(decl.replace(/\s/g,'').includes(e),`${entry}: declaration lost ${e}`);
  assert.ok(!/(?:from\s*|import\s*)['"](?:react(?:-dom|-router)?(?:\/[^'"]*)?|preact\/compat(?:\/[^'"]*)?|framer-motion|@types\/react[^'"]*)['"]/.test(decl),`${entry}: legacy types`);
}
console.log('declaration snapshot: all six public entry surfaces retained');
