import { readdirSync,readFileSync,writeFileSync,mkdirSync } from 'node:fs';
import { gzipSync,brotliCompressSync,constants } from 'node:zlib';
function css(dir){return readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?css(`${dir}/${e.name}`):e.name.endsWith('.css')?[`${dir}/${e.name}`]:[]);}
const measurements=Object.fromEntries([...css('src/tokens'),...css('src/css'),...css('src/preact'),'dist/roedu-ui.css'].map(file=>{const data=readFileSync(file);return [file,{bytes:data.length,gz:gzipSync(data,{level:6}).length,br:brotliCompressSync(data,{params:{[constants.BROTLI_PARAM_QUALITY]:11,[constants.BROTLI_PARAM_MODE]:constants.BROTLI_MODE_GENERIC}}).length}];}));
const report={schema:1,runtime:{node:process.version,zlib:process.versions.zlib,brotli:process.versions.brotli},methods:{gzip:{level:6},brotli:{quality:11,mode:'generic'}},files:measurements};
const target=process.argv[2]??'unit';mkdirSync(`.gate/${target}`,{recursive:true});writeFileSync(`.gate/${target}/measurements.json`,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
