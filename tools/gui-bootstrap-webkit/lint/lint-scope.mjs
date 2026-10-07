import { existsSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { localPath, readJSON, readLocal, validateConfig, walkRepository } from './validation-files.mjs';

const permitted = new Set(['banned-imports','banned-packages','compat-paths']);
export const bannedName = name => /^(?:@types\/react(?:$|[-/])|react(?:$|[-/])|preact\/compat(?:$|\/)|framer-motion(?:$|\/))/.test(name);
export function owningPackage(filename, packages) {
  return [...packages].filter(p=>p==='.'||filename.startsWith(p+'/')).sort((a,b)=>b.length-a.length)[0] ?? null;
}
export function glob(pattern) {
  if(typeof pattern!=='string'||!pattern||pattern.startsWith('/')||pattern.includes('\\')||pattern.split('/').some(x=>x==='..'||x==='.')||/[\[\]{}!\0]/.test(pattern)||/^[A-Za-z]:/.test(pattern)) throw new Error(`unsafe/unsupported scope pattern: ${pattern}`);
  if(!pattern.includes('/') || /^[*?]/.test(pattern) || pattern.split('/').includes('kit-shims')) throw new Error(`scope must have a narrow explicit prefix: ${pattern}`);
  let regex='^';
  for(let i=0;i<pattern.length;i++) {
    if(pattern[i]==='*'&&pattern[i+1]==='*') {if(pattern[i+2]==='/'){regex+='(?:.*/)?';i+=2;}else{regex+='.*';i++;}}
    else if(pattern[i]==='*')regex+='[^/]*';
    else if(pattern[i]==='?')regex+='[^/]';
    else regex+=pattern[i].replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
  }
  return new RegExp(regex+'$');
}
export function loadScope(root, config, files, packages) {
  const filename=localPath(root,'lint/scope.json',false);
  if(!existsSync(filename))return {entries:[],present:false};
  if(config.role==='core')throw new Error('lint/scope.json is forbidden for role core');
  const data=readJSON(root,'lint/scope.json');
  if(data.schema!==1||!Array.isArray(data.entries)||Object.keys(data).some(k=>!['schema','entries'].includes(k)))throw new Error('invalid lint scope schema');
  const entries=data.entries.map((entry,index)=>{
    if(!entry||Object.keys(entry).some(k=>!['paths','rules','reason','expires'].includes(k))||!Array.isArray(entry.paths)||!entry.paths.length||!Array.isArray(entry.rules)||!entry.rules.length||new Set(entry.paths).size!==entry.paths.length||new Set(entry.rules).size!==entry.rules.length||entry.rules.some(r=>!permitted.has(r))||typeof entry.reason!=='string'||!entry.reason.trim()||typeof entry.expires!=='string'||!entry.expires.trim())throw new Error(`invalid lint scope entry ${index}`);
    const patterns=entry.paths.map(pattern=>{
      const regex=glob(pattern);
      for(const pkg of packages) {
        const manifest=pkg==='.'?'package.json':pkg+'/package.json';
        if(regex.test(manifest))throw new Error(`whole package scope forbidden: ${pattern}`);
      }
      if(regex.test('package.json')||regex.test('AGENTS.md'))throw new Error(`repo root scope forbidden: ${pattern}`);
      const matched=files.filter(p=>regex.test(p));
      if(matched.some(p=>p.split('/').includes('kit-shims')))throw new Error(`kit-shims scope forbidden: ${pattern}`);
      return {pattern,regex,matched};
    });
    return {...entry,index,patterns};
  });
  return {entries,present:true};
}
// Tokenization prevents import-like strings/comments in test fixtures or rule
// definitions from becoming findings. JSX/templ attribute checks remain separate.
export function tokens(text) {
  const out=[];
  for(let i=0;i<text.length;) {
    const c=text[i];if(/\s/.test(c)){i++;continue;}
    if(text.startsWith('//',i)){let j=text.indexOf('\n',i+2);i=j<0?text.length:j;continue;}
    if(text.startsWith('/*',i)){let j=text.indexOf('*/',i+2);i=j<0?text.length:j+2;continue;}
    if(c==='"'||c==="'"||c==='`') {let raw='',quote=c;i++;while(i<text.length){if(text[i]==='\\'){raw+=text[i++];if(i<text.length)raw+=text[i++];continue;}if(text[i]===quote){i++;break;}raw+=text[i++];}raw=raw.replace(/\\(?:u\{([a-fA-F0-9]+)\}|u([a-fA-F0-9]{4})|x([a-fA-F0-9]{2})|(["'`\\bnfrtv]))/g,(_,wide,uni,hex,plain)=>wide||uni||hex?String.fromCodePoint(parseInt(wide??uni??hex,16)):({b:'\b',n:'\n',f:'\f',r:'\r',t:'\t',v:'\v'}[plain]??plain));out.push({kind:'string',value:raw});continue;}
    const m=/^[A-Za-z_$][\w$]*/.exec(text.slice(i));if(m){out.push({kind:'id',value:m[0]});i+=m[0].length;continue;}
    out.push({kind:'symbol',value:c});i++;
  }
  return out;
}
export function sourceFindings(root, files, entries) {
  const findings=[];
  const add=(rule,tool,path,scopable=false)=>findings.push({rule,tool_or_import:tool,paths:[path],scopable});
  for(const path of files) {
    if(['.eslintignore','.oxlintignore','.ast-grepignore','.sgignore'].includes(path.split('/').at(-1))) {
      if(readLocal(root,path).split('\n').some(x=>x.trim()&&!x.trim().startsWith('#')))add('ignore-bypass','unsupported ignore file',path);
    }
    if(/(?:oxlint|eslintrc|eslint\.config|sgconfig)/.test(path)&&/\.(?:json|[cm]?js|ya?ml)$/.test(path)) {
      if(/(?:no-restricted-imports|banned-imports|banned-packages|compat-paths)["']?\s*[:=]\s*(?:0|["']off["'])/.test(readLocal(root,path)))add('ignore-bypass','restricted rule disabled',path);
    }
    if(!/\.(?:[cm]?[jt]sx?|templ|html|go)$/.test(path))continue;
    const text=readLocal(root,path), ts=tokens(text);
    for(const line of text.split('\n')) {
      const disable=/\b(?:eslint|oxlint|ast-grep|sg)-(?:disable|ignore)(?:-next-line|-line)?\b([^\r\n]*)/.exec(line);
      if(disable&&(!disable[1].trim().replace(/\*\/$/,'')||/(?:restricted-import|banned-|compat-paths|all)/.test(disable[1])))add('inline-disable','restricted lint disable',path);
    }
    for(let i=0;i<ts.length;i++) {
      const t=ts[i],n=ts[i+1],v=ts[i+2];
      let imported;
      if(t.kind==='id'&&t.value==='from'&&n?.kind==='string')imported=n.value;
      if(t.kind==='id'&&t.value==='import'&&n?.kind==='string')imported=n.value;
      if(t.kind==='id'&&['import','require'].includes(t.value)&&n?.value==='('&&v?.kind==='string')imported=v.value;
      const importEntry=imported&&entries.get(imported.split('/').slice(0,imported.startsWith('@')?2:1).join('/'));
      if(imported&&(bannedName(imported)||['transitive-only','banned'].includes(importEntry?.status)))add('banned-imports',imported,path,bannedName(imported));
      if(t.kind==='id'&&['forwardRef','defaultProps'].includes(t.value))add(t.value,t.value,path);
      if(t.value==='useRef') {let j=i+1;if(ts[j]?.value==='<'){let depth=0;do{if(ts[j]?.value==='<')depth++;if(ts[j]?.value==='>')depth--;j++;}while(j<ts.length&&depth>0);}if(ts[j]?.value==='('&&ts[j+1]?.value===')')add('useRef-initial','useRef()',path);}
      if(t.value==='JSX'&&n?.value==='.'&&v?.value==='HTMLAttributes')add('JSX-types','JSX.HTMLAttributes',path);
      if(['Component','this'].includes(t.value)&&n?.value==='.'&&v?.value==='base')add('Component-base',`${t.value}.base`,path);
      if(t.value==='templ'&&n?.value==='.'&&v?.value==='SafeURL'&&ts[i+3]?.value==='(')add('templ-SafeURL','templ.SafeURL(',path);
    }
    if(/\.(?:tsx|jsx|templ|html)$/.test(path)) {
      const jsx=/\.(?:tsx|jsx)$/.test(path);
      const tags=[...text.matchAll(/<([A-Za-z][\w.:-]*)\b([^<>]*)>/g)];
      if(tags.some(tag=>(!jsx||!/[A-Z]/.test(tag[1][0]))&&/\bstyle\s*=\s*["'{]/.test(tag[2])))add('inline-style','style=',path);
      if(/\bon[a-z]+\s*=\s*["']/.test(text))add('inline-handler','on*=',path);
    }
  }
  return findings;
}
export function evaluateScopes(scope, findings, packages) {
  const errors=[],legacy_pending=[],used=new Map();
  for(const entry of scope.entries)used.set(entry.index,new Set());
  for(const finding of findings) {
    const matches=scope.entries.filter(entry=>finding.scopable&&entry.rules.includes(finding.rule)&&entry.patterns.some(pattern=>finding.package_dir!==undefined ? pattern.matched.some(p=>owningPackage(p,packages)===finding.package_dir&&/\.(?:[cm]?[jt]sx?|html|templ|go)$/.test(p)) : finding.paths.some(p=>pattern.regex.test(p))));
    if(!matches.length){errors.push(finding);continue;}
    for(const entry of matches) {
      for(const pattern of entry.patterns)if(finding.package_dir!==undefined?pattern.matched.some(p=>owningPackage(p,packages)===finding.package_dir&&/\.(?:[cm]?[jt]sx?|html|templ|go)$/.test(p)):finding.paths.some(p=>pattern.regex.test(p)))used.get(entry.index).add(pattern.pattern);
      legacy_pending.push({rule:finding.rule,tool_or_import:finding.tool_or_import,paths:[...new Set(finding.paths)].sort(),expires:entry.expires,source:'lint/scope.json'});
    }
  }
  for(const entry of scope.entries) {
    if(!used.get(entry.index).size)errors.push({rule:'lint-scope',tool_or_import:'stale entry',paths:entry.paths,scopable:false});
    for(const pattern of entry.patterns)if(!used.get(entry.index).has(pattern.pattern))errors.push({rule:'lint-scope',tool_or_import:'stale path',paths:[pattern.pattern],scopable:false});
  }
  const unique=values=>[...new Map(values.map(v=>[JSON.stringify(v),v])).values()].sort((a,b)=>JSON.stringify(a).localeCompare(JSON.stringify(b)));
  return {errors:unique(errors),legacy_pending:unique(legacy_pending)};
}
export function finish(findings, scope, packages) {
  const result=evaluateScopes(scope,findings,packages);
  return {schema:1,status:result.errors.length?'fail':'pass',reason:result.legacy_pending.length?'legacy-pending':result.errors.length?'validation-failed':'clean',...result};
}
export function taskConfig(root) {
  const r=spawnSync('task',['--silent','repo:kit-config'],{cwd:root,encoding:'utf8'});
  if(r.status!==0||r.error)throw new Error('task repo:kit-config failed');
  return validateConfig(root,JSON.parse(r.stdout));
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)) {
  // The complete checker collects package/TS/source findings before evaluating
  // staleness. Reuse it rather than letting a source-only lint check miss scopes.
  import('../scripts/versions-check.mjs').then(async m=>{
    if(process.argv.length!==2)throw new Error('lint-scope accepts no arguments');
    const result=await m.checkVersions({root:process.cwd(),config:taskConfig(process.cwd()),lintOnly:true});
    process.stdout.write(JSON.stringify(result)+'\n');if(result.status!=='pass'){for(const error of result.errors)process.stderr.write(`${error.rule}: ${error.tool_or_import} ${error.paths.join(', ')}\n`);process.exitCode=1;}
  }).catch(error=>{process.stderr.write(error.message+'\n');process.stdout.write(JSON.stringify({schema:1,status:'fail',reason:'validation-failed',errors:[{rule:'lint-scope',tool_or_import:error.message,paths:[]}],legacy_pending:[]})+'\n');process.exitCode=1;});
}
