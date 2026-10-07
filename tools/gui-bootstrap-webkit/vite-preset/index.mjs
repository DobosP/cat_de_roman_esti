import {readFileSync,writeFileSync} from 'node:fs';
import path from 'node:path';
import { mergeConfig } from 'vite';
import preact from '@preact/preset-vite';
import { gzipSync,brotliCompressSync,constants } from 'node:zlib';
export function precompress(){return {name:'roedu-precompress-final-files',writeBundle(options,bundle){const out=path.resolve(options.dir);for(const asset of Object.values(bundle)){
  if(!/\.(?:css|js)$/.test(asset.fileName))continue;
  const filename=path.resolve(out,asset.fileName);if(!filename.startsWith(out+path.sep))throw Error('Unsafe generated asset');const data=readFileSync(filename);
  writeFileSync(filename+'.gz',gzipSync(data,{level:6}));
  writeFileSync(filename+'.br',brotliCompressSync(data,{params:{[constants.BROTLI_PARAM_QUALITY]:11,[constants.BROTLI_PARAM_MODE]:constants.BROTLI_MODE_GENERIC}}));
}}};}
/** Shared delivery preset; caller controls app entry/output directory, never compat aliases. */
export function roeduPreset(overrides={}){
  const preset={base:'/static/',oxc:{jsx:{runtime:'automatic',importSource:'preact'}},resolve:{dedupe:['preact']},optimizeDeps:{include:['preact','preact/hooks','preact/jsx-runtime','preact/jsx-dev-runtime','preact-render-to-string','motion','motion/mini'],rolldownOptions:{transform:{jsx:{runtime:'automatic',importSource:'preact'}}}},plugins:[preact({reactAliasesEnabled:false}),precompress()],build:{manifest:true,rolldownOptions:{output:{minify:true,hashCharacters:'hex',entryFileNames:'assets/[name]-[hash:8].js',chunkFileNames:'assets/[name]-[hash:8].js',assetFileNames:'assets/[name]-[hash:8][extname]',codeSplitting:{groups:[{name:'preact',test:/node_modules\/preact\//}]}}}}};
  const result=mergeConfig(preset,overrides);
  if(result.resolve?.alias&&JSON.stringify(result.resolve.alias).includes('preact/compat'))throw Error('Compat aliases are forbidden');
  return result;
}
export default roeduPreset;
