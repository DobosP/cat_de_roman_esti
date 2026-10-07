import { existsSync, lstatSync, readdirSync, readFileSync, realpathSync } from 'node:fs';
import { isAbsolute, join, relative, resolve, sep } from 'node:path';
import { validateUiAdoption } from '../scripts/ui-adoption-config.mjs';
import { isPythonBytecodePath } from '../scripts/kit-sync.mjs';
export const inside = (root, p) => p === root || p.startsWith(root + sep);
export const posix = value => value.split(sep).join('/');
export function localPath(root, value, required = true) {
  if (typeof value !== 'string' || !value || isAbsolute(value) || /^[A-Za-z]:/.test(value) || value.includes('\\') || value.split('/').includes('..') || value.includes('\0')) throw new Error('invalid repository-relative path');
  const p = resolve(root, value);
  if (!inside(root, p)) throw new Error('path escapes repository');
  let current = root;
  for (const part of relative(root, p).split(sep).filter(Boolean)) {
    current = join(current, part);
    if (!existsSync(current)) { if (required) throw new Error(`required path missing: ${posix(relative(root,p))}`); break; }
    if (lstatSync(current).isSymbolicLink()) throw new Error(`repository symlink refused: ${posix(relative(root,current))}`);
  }
  return p;
}
export function readLocal(root, value) { return readFileSync(localPath(root,value),'utf8'); }
export function readJSON(root, value) { return JSON.parse(readLocal(root,value)); }
export function validateConfig(root, config) {
  const keys = ['role','app','npm_dir','vendor_dir','go_dirs'];
  if (!config || Object.keys(config).some(k=>!keys.includes(k)&&k!=='ui_adoption') || keys.some(k=>!(k in config))) throw new Error('repo:kit-config must carry role/app/npm_dir/vendor_dir/go_dirs and only the optional closed ui_adoption');
  validateUiAdoption(config);
  if (!['core','consumer'].includes(config.role) || typeof config.app !== 'string' || !config.app.trim()) throw new Error('invalid kit role/app');
  if (!Array.isArray(config.go_dirs) || !config.go_dirs.length || new Set(config.go_dirs).size!==config.go_dirs.length) throw new Error('go_dirs must list distinct actual Go modules');
  localPath(root,config.npm_dir); localPath(root,config.vendor_dir,false);
  for (const p of config.go_dirs) localPath(root,p);
  return config;
}
export function walkRepository(root, config) {
  root = resolve(root);
  if (lstatSync(root).isSymbolicLink() || realpathSync(root)!==root) throw new Error('repository root must be a real directory');
  const excludedNames = new Set(['node_modules','.git','.gate','.vitest','dist','test-results','testdata','fixtures','third_party']);
  const kit = posix(config.npm_dir).replace(/^\.\//,'').replace(/\/$/,'');
  const excludedPaths = new Set([`${kit}/templates`,`${kit}/schemas`,'legacy']);
  const files=[],excluded=[];
  function walk(dir) {
    for (const entry of readdirSync(dir,{withFileTypes:true}).sort((a,b)=>a.name.localeCompare(b.name))) {
      const path=join(dir,entry.name), rel=posix(relative(root,path));
      if (isPythonBytecodePath(rel) || excludedNames.has(entry.name) || excludedPaths.has(rel) || /(?:^|\/)embedfs\/legacy(?:\/|$)/.test(rel)) { excluded.push(rel);continue; }
      const stat=lstatSync(path);
      if (stat.isSymbolicLink()) throw new Error(`repository symlink refused: ${rel}`);
      if (stat.isDirectory()) walk(path);
      else if (stat.isFile()) files.push(rel);
      else throw new Error(`nonregular repository entry: ${rel}`);
    }
  }
  walk(root); return {files,excluded};
}
// Preserve string literals while removing JSONC comments and trailing commas.
export function parseJSONC(text) {
  let out='',quoted=false,escape=false;
  for(let i=0;i<text.length;i++) {
    const c=text[i];
    if(quoted) {out+=c;if(escape)escape=false;else if(c==='\\')escape=true;else if(c==='"')quoted=false;continue;}
    if(c==='"'){quoted=true;out+=c;continue;}
    if(c==='/'&&text[i+1]==='/'){while(i<text.length&&text[i]!=='\n')i++;out+='\n';continue;}
    if(c==='/'&&text[i+1]==='*'){i+=2;while(i<text.length&&!(text[i]==='*'&&text[i+1]==='/'))i++;i++;out+=' ';continue;}
    out+=c;
  }
  let clean='';quoted=false;escape=false;
  for(let i=0;i<out.length;i++) {
    const c=out[i];
    if(quoted){clean+=c;if(escape)escape=false;else if(c==='\\')escape=true;else if(c==='"')quoted=false;continue;}
    if(c==='"'){quoted=true;clean+=c;continue;}
    if(c===','){let j=i+1;while(/\s/.test(out[j]??'')&&j<out.length)j++;if(out[j]==='}'||out[j]===']')continue;}
    clean+=c;
  }
  return JSON.parse(clean);
}
