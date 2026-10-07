import { build } from 'vite';
import preact from '@preact/preset-vite';
import { gzipSync,brotliCompressSync,constants } from 'node:zlib';
import { writeFileSync,mkdirSync } from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const targets={
  'preact-runtime':"export * from 'preact';export * from 'preact/hooks';",
  'motion-mini-spring':"export {animate} from 'motion/mini';export {spring} from 'motion';",
  ...Object.fromEntries(['islands','invoker','hovercard','wizard','meter','speak','comfort'].map(name=>[name,'export * from '+JSON.stringify(path.resolve('src/behaviors/'+name+'.ts'))+';'])),
};
const files={},library_formatted={};
const target=process.argv[2]??'unit';const entriesDir=`.gate/${target}/measurement-entries`;mkdirSync(entriesDir,{recursive:true});
const bundlesDir=`.gate/${target}/measurement-bundles`;mkdirSync(bundlesDir,{recursive:true});
const sizes=bytes=>({bytes:bytes.length,gz:gzipSync(bytes,{level:6}).length,br:brotliCompressSync(bytes,{params:{[constants.BROTLI_PARAM_QUALITY]:11,[constants.BROTLI_PARAM_MODE]:constants.BROTLI_MODE_GENERIC}}).length});
for(const [name,source] of Object.entries(targets)){
  const entry=path.resolve(entriesDir,`${name}.ts`);writeFileSync(entry,source);
  for(const production of [false,true]) {
    // Vite 8 ES-library defaults deliberately disable minified code generation.
    // Compare that default, then measure the same explicit minifier shipped by UI.
    const bundle=await build({configFile:false,logLevel:'error',plugins:[preact({reactAliasesEnabled:false})],build:{write:false,minify:true,cssCodeSplit:false,lib:{entry,formats:['es']},rolldownOptions:{output:{codeSplitting:false,...(production?{minify:true}:{})}}}});
    const chunks=(Array.isArray(bundle)?bundle:[bundle]).flatMap(x=>x.output).filter(x=>x.type==='chunk');
    assert.equal(chunks.length,1,'isolated measurement must be one actual Rolldown bundle');
    const bytes=Buffer.from(chunks[0].code);(production?files:library_formatted)[name]=sizes(bytes);
    writeFileSync(`${bundlesDir}/${name}${production?'':'.library-formatted'}.js`,bytes);
  }
}
mkdirSync(`.gate/${target}`,{recursive:true});writeFileSync(`.gate/${target}/runtime-measurements.json`,JSON.stringify({schema:1,node:process.version,methods:{bundle:'Vite 8 ES library; Rolldown output.minify=true, preserving annotation comments',gzip_level:6,brotli_quality:11,brotli_mode:'generic'},files,library_formatted},null,2)+'\n');console.log(files);
assert.ok(files.islands.gz<=1100,`islands ${files.islands.gz} gzip bytes exceeds 1100`);
