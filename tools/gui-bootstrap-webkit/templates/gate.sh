#!/usr/bin/env bash
# Native Linux gate; installed byte-identically as scripts/gate.sh and web-kit/templates/gate.sh.
# Worker: bash /absolute/worktree/scripts/gate.sh unit --sha <literal HEAD> [--dirty] [--parallel N]
# Targets/flags remain PROGRAM sec 4.2. Owner operations require an ephemeral GATE_OPERATOR=paul.
# Never set it in a worker. One gate per worktree; no host npm/go/task; no secret inputs.
set -euo pipefail; { die() { echo "gate: $*" >&2; exit 2; }; ROOT="$HOME/work/_worktrees/"   # { } is parsed whole: kit:sync may replace this file
[[ "$(pwd -P)" = "$PWD" ]] || die "symlinked worktree path"
[[ "$PWD/" != *//* && "$PWD/" != */./* && "$PWD/" != */../* && "$PWD/" =~ ^"$ROOT"[^/]+/[^/]+/$ ]] || die "refusing: $PWD is not exactly $ROOT<repo>/<slug>"
target=${1:-}; [ $# -gt 0 ] && shift; sha=""; dirty=false; par=""; fresh=0; keep=0; resolve=0; tag=""; op=${GATE_OPERATOR:-}
while [ $# -gt 0 ]; do case "$1" in --sha) [ $# -ge 2 ] || die "--sha needs a value"; sha=$2; shift 2;; --dirty) dirty=true; shift;; --resolve-versions) resolve=1; shift;;
  --tag) [ $# -ge 2 ] || die "--tag needs roedu-toolchain:<new tag>"; tag=$2; shift 2;;
  --parallel) [ $# -ge 2 ] || die "--parallel needs N"; par=$2; shift 2;;  --fresh) fresh=1; shift;;  --keep) keep=1; shift;;  *) die "unknown argument '$1'";; esac; done
case "$target" in unit|full|gen|deps|kit:sync|build|image|baseline|golden:capture|golden:verify|contract:refresh|legacy:freeze|e2e|perf) ;;
  qualify|shell|toolchain|trust) [ "$op" = paul ] || die "'$target' is Paul-only (GATE_OPERATOR=paul)";; *) die "unknown target '$target' (see usage above)";; esac
[ "$keep" = 0 ] || [ "$op" = paul ] || die "--keep is Paul-only"; [ "$resolve" = 0 ] || [ "$target" = gen ] || die "--resolve-versions is valid only with gen"
[ -z "$tag" ] || [ "$target" = toolchain ] || die "--tag is valid only with toolchain"
[[ $sha =~ ^[0-9a-f]{40}([0-9a-f]{24})?$ ]] || die "--sha <full commit sha> is mandatory"; tdir=${target//:/-}   # result dir: ':' becomes '-'
src=$PWD; repo=$(basename "$(dirname "$src")"); rawslug=$(basename "$src"); [[ $repo =~ ^[a-z0-9_-]+$ && $rawslug =~ ^[a-z0-9_-]+$ ]] || die "repo/slug must be lowercase portable names"
slug=$rawslug; key="$repo-$slug-$(printf %s "$src" | sha256sum | cut -c1-12)"; dst="$HOME/work/_temp/$slug/gates/$repo"
[ "$(git -C "$src" rev-parse --show-toplevel)" = "$src" ] || die "not the Git worktree root"
[ "$(git -C "$src" branch --show-current)" != main ] || die "never gate task work on main"
actual=$(git -C "$src" rev-parse HEAD) || die "not a git worktree"; [ "$actual" = "$sha" ] || die "--sha does not equal HEAD"
state=$(git -C "$src" status --porcelain); [ -z "$state" ] || [ "$dirty" = true ] || die "dirty source needs --dirty"
if [ "$dirty" = true ]; then case "$target" in trust|toolchain) die "owner pin/build needs a clean tree";; esac; fi
safe_path() { [ "$(realpath -m "$1")" = "$1" ] || die "symlink/traversal in gate storage path"; }
safe_path "$src/.gate/$tdir"; safe_path "$dst/.gate/$tdir"; safe_path "$HOME/gates/trust"; safe_path "$HOME/work/_temp/$slug/gates/$repo.lock"
mkdir -p "$HOME/work/_temp/$slug/gates"
# Unexpected ignored files are never included in a gate (no file contents read).
git -C "$src" ls-files --others --ignored --exclude-standard -z | python3 -I -c 'import sys; allowed={".git","node_modules",".gate",".vitest","dist","test-results","TASK_BRIEF.md","TASK_RESULT.md","SWARM_RESULT.md"}; bad=[p for p in sys.stdin.buffer.read().split(b"\0") if p and not any(x.decode(errors="surrogateescape") in allowed or x == b".env" or x.startswith(b".env.") for x in p.split(b"/"))]; sys.exit(bool(bad))' || die "unexpected ignored file in source; move it to owned scratch"
exec 9>>"$HOME/work/_temp/$slug/gates/$repo.lock"; flock -n 9 || die "another gate is already running for $slug"; rm -f -- "$src/.gate/$tdir/"{result,wrapper-fail}.json   # no stale pass
if [ "$fresh" = 1 ]; then rm -rf -- "$dst"; fi; mkdir -p "$dst"; EX=(.git node_modules .gate .vitest dist frontend/dist test-results .env ".env.*" TASK_BRIEF.md TASK_RESULT.md SWARM_RESULT.md)   # receiver-protected too
rsync -a --delete "${EX[@]/#/--exclude=}" "$src"/ "$dst"/; cd "$dst"; safe_path "$dst/.gate/$tdir"; rm -rf -- ".gate/$tdir"; mkdir -p ".gate/$tdir"
# Snapshot includes relative paths, executable mode and content; symlinks are refused
# because neither rsync nor a bind mount may read/write an external referent.
KIT_VENDOR=''; KIT_FILES=(); KIT_TREES=(); KIT_PRESERVED=(); KIT_APPLY=0
snapshot() { python3 -I - "$1" "$2" "$KIT_VENDOR" "$KIT_APPLY" "${#KIT_FILES[@]}" "${#KIT_TREES[@]}" "${#KIT_PRESERVED[@]}" "${KIT_FILES[@]}" "${KIT_TREES[@]}" "${KIT_PRESERVED[@]}" "${@:3}" <<'PY_SNAPSHOT'
import fnmatch, hashlib, os, re, stat, sys
root, kind, kit_vendor, kit_apply, nf, nt, np, *tail = sys.argv[1:]
nf, nt, np = int(nf), int(nt), int(np)
kit_files, kit_trees, preserved, allow = set(tail[:nf]), tail[nf:nf+nt], set(tail[nf+nt:nf+nt+np]), tail[nf+nt+np:]
def owned_go(p): return any(p == d or p.startswith(d+'/') for d in kit_trees)
def kit_owned(p):
    return p not in preserved and (p in kit_files or owned_go(p) or bool(kit_vendor and os.path.dirname(p) == kit_vendor and re.fullmatch(r'roedu-(ui|web-kit)-[^/]+\.tgz(?:\.sha256)?', os.path.basename(p))))
h = hashlib.sha256()
ignored = {'.git','node_modules','.gate','.vitest','dist','test-results'}
meta = {'TASK_BRIEF.md','TASK_RESULT.md','SWARM_RESULT.md'}
def skip(name, rel):
    if name == 'dist' and (kind == 'metadata' or kind != 'legacy-tree' and owned_go(rel)): return False
    return name in ignored or name in meta or name == '.env' or name.startswith('.env.')
def protected(p):
    return (p in preserved or p in {'budgets.json','scripts/gate.sh','compose.gate.yml','Taskfile.yml','.gate.env','Dockerfile.toolchain','versions.lock.json','Taskfile.repo.yml','engine.json','.gitattributes','AGENTS.md','docs/PROGRAM.md','.agent/PLANS.md','ci.yml','lint/scope.json','kit.lock.json'}
        or p.startswith(('.codex/','kit/','legacy/','.github/workflows/','web-kit/templates/','web-kit/schemas/'))
        or p in kit_files or owned_go(p) or bool(kit_vendor and (p == kit_vendor or p.startswith(kit_vendor+'/')))
        or '/baselines/' in '/'+p or re.search(r'(^|/)testdata/golden[^/]*/',p)
        or '/golden/testdata/' in '/'+p or p.endswith('/internal/contract/assets.json')
        or p.endswith('/engine.json'))
entries=[]
for base, dirs, files in os.walk(root, followlinks=False):
    dirs[:] = sorted(d for d in dirs if not skip(d,os.path.relpath(os.path.join(base,d),root)))
    for name in dirs + files:
        if skip(name,os.path.relpath(os.path.join(base,name),root)): continue
        path=os.path.join(base,name); rel=os.path.relpath(path,root)
        if os.path.islink(path): raise SystemExit('gate: source symlink refused: '+rel)
        if os.path.isfile(path): entries.append((rel,path))
for rel,path in sorted(entries):
    if kind == 'protected' and (not protected(rel) or rel not in preserved and (any(fnmatch.fnmatch('./'+rel,a) for a in allow) or kit_apply == '1' and kit_owned(rel))): continue
    if kind == 'trust' and rel not in allow: continue
    mode = 'x' if os.stat(path).st_mode & 0o111 else '-'
    h.update(os.fsencode(rel)+b'\0'+mode.encode()+b'\0'+hashlib.sha256(open(path,'rb').read()).digest())
print(h.hexdigest())
PY_SNAPSHOT
}
GATE_TREE_SHA256=$(snapshot . tree) || die "source snapshot failed"
[ "$GATE_TREE_SHA256" = "$(snapshot "$src" tree)" ] || die "source changed during copy"
prot() { snapshot . protected "$@"; }
# Reset inherited wrapper keys so only the committed literal env supplies them.
unset TOOLCHAIN_IMAGE TOOLCHAIN_DIGEST COMPOSE_FILE SYNC_BACK PG_MAJOR PG_SCRATCH_ROOT GATE_PARALLEL_MAX GATE_DB_IMAGE CSP_STAGE APP_DOCKERFILE QUALIFY_ARGS
[ -f .gate.env ] || die "no .gate.env"; K='TOOLCHAIN_(IMAGE|DIGEST)|COMPOSE_FILE|SYNC_BACK|PG_(MAJOR|SCRATCH_ROOT)|GATE_(PARALLEL_MAX|DB_IMAGE)|CSP_STAGE|APP_DOCKERFILE|QUALIFY_ARGS'
declare -A seen=()
while IFS= read -r line || [ -n "$line" ]; do
  [[ $line =~ ^[[:space:]]*(#|$) ]] && continue
  [[ $line = *=* && $line != *$'\r'* ]] || die ".gate.env needs LF literal KEY=VALUE"
  k=${line%%=*}; v=${line#*=}; [[ $k =~ ^($K)$ ]] || die ".gate.env unknown key (name only): $k"
  [ -z "${seen[$k]:-}" ] || die ".gate.env duplicate key: $k"; seen[$k]=1
  printf -v "$k" '%s' "$v"; export "$k"
done < .gate.env
for k in TOOLCHAIN_IMAGE TOOLCHAIN_DIGEST COMPOSE_FILE SYNC_BACK PG_MAJOR PG_SCRATCH_ROOT GATE_PARALLEL_MAX GATE_DB_IMAGE CSP_STAGE APP_DOCKERFILE QUALIFY_ARGS; do
  [ -n "${seen[$k]:-}" ] || die ".gate.env missing key: $k"
done
[ "$COMPOSE_FILE" = compose.gate.yml ] || die "COMPOSE_FILE must be compose.gate.yml"
[[ $APP_DOCKERFILE =~ ^[A-Za-z0-9_./-]+$ && $APP_DOCKERFILE != /* && $APP_DOCKERFILE != *..* ]] || die "invalid APP_DOCKERFILE"
[[ $TOOLCHAIN_IMAGE =~ ^roedu-toolchain:[a-z0-9][a-z0-9._-]{0,127}$ ]] || die "invalid TOOLCHAIN_IMAGE"
[[ $GATE_PARALLEL_MAX =~ ^[1-4]$ ]] || die "GATE_PARALLEL_MAX must be 1..4"
: "${TOOLCHAIN_IMAGE:?not set in .gate.env}" "${TOOLCHAIN_DIGEST:=}" "${COMPOSE_FILE:=compose.gate.yml}" "${SYNC_BACK:=}" "${PG_MAJOR:=}" "${GATE_PARALLEL_MAX:=4}"
: "${CSP_STAGE:=report-only}" "${APP_DOCKERFILE:=Dockerfile}" "${QUALIFY_ARGS:=}" "${GATE_DB_IMAGE:=postgres:$PG_MAJOR-trixie}"
case "$CSP_STAGE" in report-only) enf=false;; enforced) enf=true;; *) die "CSP_STAGE must be report-only or enforced, not '$CSP_STAGE'";; esac
unset GATE_DB_DSN GATE_APP_URL GATE_APP_IMAGE_ID COMPOSE_PROFILES COMPOSE_ENV_FILES
export DJANGO_CSP_ENFORCE=$enf RO_TEACHER_CSP_ENFORCE=$enf CAT_CSP_ENFORCE=$enf GATE_DB_IMAGE   # the one place the stage-B flags come from (sec 4.4)
case "$target" in full|e2e|perf|baseline|golden:capture|golden:verify|shell|toolchain) profile=full
  [[ $PG_MAJOR =~ ^[0-9]+$ ]] || die "PG_MAJOR in .gate.env is '$PG_MAJOR': Paul fills PROD_PG_MAJOR (PROGRAM.md sec 3)"
  [[ $GATE_DB_IMAGE != *__* && $GATE_DB_IMAGE != *'<'* ]] || die "GATE_DB_IMAGE '$GATE_DB_IMAGE' still holds a placeholder";; *) profile=unit;; esac
if [ "$profile" = full ]; then export GATE_DB_DSN=postgres://gate:gate@db:5432/gate?sslmode=disable GATE_APP_URL=http://roedu-gate.test:8080; fi
bounded_build() {
  local caps mem period quota
  caps=$(docker inspect -f '{{.HostConfig.Memory}} {{.HostConfig.CpuPeriod}} {{.HostConfig.CpuQuota}}' buildx_buildkit_roedu-gates-linux0 2>/dev/null) || die "owner must provision capped roedu-gates-linux builder"
  read -r mem period quota <<<"$caps"
  [[ $mem =~ ^[0-9]+$ && $period =~ ^[0-9]+$ && $quota =~ ^[0-9]+$ ]] && [ "$mem" -gt 0 ] && [ "$mem" -le 10737418240 ] && [ "$period" -gt 0 ] && [ "$quota" -gt 0 ] && [ "$quota" -le "$((8*period))" ] || die "builder limits exceed 8 CPUs/10GiB or are unset"
  docker buildx build --builder roedu-gates-linux --platform linux/amd64 "$@"
}
if [ "$target" = toolchain ]; then   # host-side, Paul only, BEFORE the trust check: the tag to build comes from --tag, never from .gate.env (which names the
  # image this tree is pinned to and stays untouched until the one GATE-CHANGE: toolchain <tag> commit). .gate.env is read here for PG_MAJOR only.
  [ "$repo" = roedu-ui ] && [ "$dirty" = false ] || die "toolchain builds only from a clean roedu-ui worktree (no --dirty) at the commit whose Dockerfile.toolchain it builds, never an app worktree"
  [[ $tag =~ ^roedu-toolchain:[a-z0-9][a-z0-9._-]{0,127}$ ]] || die "toolchain needs --tag roedu-toolchain:<new tag> (e.g. core-v1.N); got '$tag'"
  tar="$HOME/gates/toolchain/${tag//[:\/]/_}.tar"
  { [ "$tag" != "$TOOLCHAIN_IMAGE" ] && ! docker image inspect "$tag" >/dev/null 2>&1 && [ ! -e "$tar" ]; } \
    || die "$tag is pinned in .gate.env, present in docker, or saved as $tar: never rebuild a tag (every session pinned to it breaks); pick a new tag"
  f=""; for c in web-kit/templates/Dockerfile.toolchain Dockerfile.toolchain; do if [ -f "$c" ]; then f=$c; break; fi; done; [ -n "$f" ] || die "no Dockerfile.toolchain"
  bounded_build --load --build-arg "PG_MAJOR=$PG_MAJOR" -f "$f" -t "$tag" "$(dirname "$f")"   # context = the Dockerfile's own dir only
  mkdir -p "$HOME/gates/toolchain"; docker save -o "$tar" "$tag"   # restore: docker load -i
  echo "TOOLCHAIN_IMAGE=$tag"; echo "TOOLCHAIN_DIGEST=$(docker image inspect -f '{{.Id}}' "$tag")"
  echo "record both lines in .gate.env (+ web-kit/templates/.gate.env) and versions.lock.json toolchain_image in ONE 'GATE-CHANGE: toolchain ${tag#*:}' commit, then trust + unit" >&2
  exit 0; fi
for f in scripts/gate.sh .gate.env "$COMPOSE_FILE" Taskfile.yml; do [ -f "$f" ] && [ ! -L "$f" ] || die "trust set incomplete"; done
TP="$HOME/gates/trust"; TRUST=$(snapshot . trust scripts/gate.sh .gate.env "$COMPOSE_FILE" Taskfile.yml) || die "trust set incomplete"
if [ "$target" = trust ]; then [ "$dirty" = false ] || die "pin a clean commit"; mkdir -p "$TP"; echo "$repo/$slug sha=$sha $(date -u +%FT%TZ)" >> "$TP/$TRUST"; exit 0; fi
[ -f "$TP/$TRUST" ] || die "no trust pin for gate files $TRUST (wrapper/.gate.env/compose/Taskfile changed). Codex: GATE PENDING $target sha=$sha (untrusted gate files)"
[[ $TOOLCHAIN_DIGEST =~ ^sha256:[0-9a-f]{64}$ ]] || die "TOOLCHAIN_DIGEST in .gate.env is not pinned ('$TOOLCHAIN_DIGEST'): Paul runs 'toolchain --tag <new>', then GATE-CHANGE: toolchain <tag>"
have=$(docker image inspect -f '{{.Id}}' "$TOOLCHAIN_IMAGE" 2>/dev/null || true)   # locally built image: compare the image ID, not RepoDigests
[ -n "$have" ] || die "toolchain $TOOLCHAIN_IMAGE is absent here. Paul: docker load -i ~/gates/toolchain/${TOOLCHAIN_IMAGE//[:\/]/_}.tar; never rebuild a pinned tag."
[ "$have" = "$TOOLCHAIN_DIGEST" ] || die "toolchain $TOOLCHAIN_IMAGE is $have, .gate.env pins $TOOLCHAIN_DIGEST: the tag was rebuilt/retagged. Do NOT rebuild; Paul investigates."
P=${par:-$GATE_PARALLEL_MAX}; { [[ $P =~ ^[1-9][0-9]*$ ]] && [ "$P" -le "$GATE_PARALLEL_MAX" ]; } || die "--parallel must be 1..$GATE_PARALLEL_MAX (lower only)"
APP_IMG="roedu-app:gate-$key"; export COMPOSE_PROJECT_NAME="gate-$key" GATE_SHA=$sha GATE_DIRTY=$dirty GATE_TREE_SHA256 GATE_TRUST_SHA256=$TRUST GOMAXPROCS=$P GOFLAGS="-p=$P" \
  GATE_VERSIONS_RESOLVE=$resolve GATE_APP_IMAGE=$APP_IMG   # wrapper-owned: app = the image built from this tree; resolve only via --resolve-versions
DC=(docker compose --env-file .gate.env -f "$COMPOSE_FILE" -p "$COMPOSE_PROJECT_NAME")
# Host-only control is a sibling of /work: no task can rewrite its copy plan.
control=$(mktemp -d "$HOME/work/_temp/$slug/gates/$repo.wrapper-$tdir.XXXXXXXX") || die "cannot create gate control"
safe_path "$control"
[ "$(stat -c '%u:%a' "$control")" = "$(id -u):700" ] || die "gate control ownership/mode mismatch"
cp -- .gate.env "$control/.gate.env"; cp -- "$COMPOSE_FILE" "$control/compose.gate.yml"; cp -- Taskfile.yml "$control/Taskfile.yml"
[ -f Taskfile.repo.yml ] && [ ! -L Taskfile.repo.yml ] || die "repo hook file must be regular"
cp -- Taskfile.repo.yml "$control/Taskfile.repo.yml"
CONTROL_SHA=$(snapshot "$control" tree) || die "control snapshot failed"
MDC=(docker compose --project-directory "$dst" --env-file "$control/.gate.env" -f "$control/compose.gate.yml" -p "$COMPOSE_PROJECT_NAME")
cleanup_gate() { if [ "$keep" = 0 ]; then "${MDC[@]}" down -v --remove-orphans >/dev/null 2>&1 || true; fi; rm -rf -- "$control"; }
trap cleanup_gate EXIT
# The current selector is ephemeral; target histories remain intact. Expected bytes
# live in host-private control, so a task cannot publish a pass after changing it.
write_current_context() {
  python3 -I - "$control/config-before.json" "$control/current-wrapper.json" <<'PY_CURRENT_CONTEXT'
import hashlib,json,sys,uuid
source,destination=sys.argv[1:]; raw=open(source,'rb').read(); captured=json.loads(raw)
record={'schema':1,'invocation':str(uuid.uuid4()),'target':captured['target'],'sha':captured['sha'],'tree_sha256':captured['tree_sha256'],'toolchain_digest':captured['toolchain_digest'],'config_sha256':captured['config_sha256'],'config_path':'.gate/'+captured['target'].replace(':','-')+'/wrapper-kit-config.json','config_file_sha256':hashlib.sha256(raw).hexdigest()}
with open(destination,'xb') as output: output.write((json.dumps(record,separators=(',',':'))+'\n').encode())
PY_CURRENT_CONTEXT
  safe_path "$dst/.gate/wrapper-current.json"
  current_context_tmp=$(mktemp "$dst/.gate/current-context.XXXXXXXX.tmp") || return 4
  cp -- "$control/current-wrapper.json" "$current_context_tmp" || return 4
  chmod 0444 "$current_context_tmp" || return 4
  mv -fT -- "$current_context_tmp" "$dst/.gate/wrapper-current.json" || return 4
  cp -- "$control/current-wrapper.json" ".gate/$tdir/wrapper-current.json" || return 4
  chmod 0444 ".gate/$tdir/wrapper-current.json" || return 4
}
verify_current_context() {
  python3 -I - "$control/current-wrapper.json" "$dst" "$tdir" <<'PY_CURRENT_VERIFY'
import hashlib,json,os,stat,sys
expected,root,target=sys.argv[1:]
def regular(relative):
    cursor=root
    for index,part in enumerate(relative.split('/')):
        assert part and part not in ('.','..');cursor=os.path.join(cursor,part); mode=os.lstat(cursor).st_mode
        assert not stat.S_ISLNK(mode) and (stat.S_ISREG(mode) or stat.S_ISDIR(mode))
        if index<len(relative.split('/'))-1: assert stat.S_ISDIR(mode)
    assert stat.S_ISREG(os.lstat(cursor).st_mode);return cursor
raw=open(expected,'rb').read(); record=json.loads(raw)
assert record['target'].replace(':','-')==target
for relative in ('.gate/wrapper-current.json','.gate/'+target+'/wrapper-current.json'): assert open(regular(relative),'rb').read()==raw, 'current invocation descriptor changed'
config=open(regular(record['config_path']),'rb').read(); assert hashlib.sha256(config).hexdigest()==record['config_file_sha256'], 'current referenced configuration changed'
PY_CURRENT_VERIFY
}
capture_config() {
  "${MDC[@]}" --profile unit run --no-deps --rm -T --user "$(id -u):$(id -g)" runner node --input-type=module - "$target" "$sha" "$GATE_TREE_SHA256" "$TOOLCHAIN_DIGEST" <<'JS_WRAPPER_CONFIG'
import * as fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
const fail = message => { throw Error(message); };
const MODULE = 'github.com/DobosP/roedu-ui/web-kit';
const digest = value => createHash('sha256').update(value).digest('hex');
const ignored = new Set(['node_modules','.git','.gate','.vitest','dist','test-results','TASK_BRIEF.md','TASK_RESULT.md','SWARM_RESULT.md']);
const immutable = ['.codex','.agent','.github/workflows','kit','legacy','web-kit/templates','web-kit/schemas','Taskfile.repo.yml','ci.yml','lint/scope.json','kit.lock.json','AGENTS.md','docs/PROGRAM.md','budgets.json','engine.json','.gitattributes'];
const gates = ['scripts/gate.sh','compose.gate.yml','Taskfile.yml','Dockerfile.toolchain'];
function portable(value, dot = false) {
  if (dot && value === '.') return value;
  if (typeof value !== 'string' || !value) fail('Configured path must be a nonempty string');
  const normalized = value.endsWith('/') ? value.slice(0,-1) : value;
  if (!normalized || normalized.startsWith('/') || normalized.split('/').some(part => !/^[A-Za-z0-9_@.-]+$/.test(part) || part === '.' || part === '..')) fail('Configured path is not portable and literal');
  return normalized;
}
function ancestor(root, relative, kind, missing = false) {
  let current = root;
  for (const [index, part] of (relative === '.' ? [] : relative.split('/')).entries()) {
    current = path.join(current, part); let stat;
    try { stat = fs.lstatSync(current); } catch (error) { if (error.code === 'ENOENT' && missing) continue; throw error; }
    if (stat.isSymbolicLink() || (!stat.isDirectory() && !stat.isFile())) fail('Configured path has a symlink or nonregular ancestor');
    if (index !== relative.split('/').length - 1 && !stat.isDirectory()) fail('Configured ancestor is not a directory');
  }
  let stat; try { stat = fs.lstatSync(current); } catch (error) { if (error.code === 'ENOENT' && missing) return current; throw error; }
  if (kind === 'file' && !stat.isFile() || kind === 'dir' && !stat.isDirectory()) fail('Configured path has the wrong file type');
  return current;
}
const contains = (parent, child) => parent === child || child.startsWith(parent + '/');
function writable(relative) {
  if (relative.split('/').some(part => part.startsWith('.') || ignored.has(part) || ['kit','node_modules','vendor','third_party'].includes(part))) fail('Configured destination overlaps reserved or excluded source');
}
function discoverGo(root, relative = '.') {
  const current = ancestor(root, relative, 'dir'), found = [], mod = relative === '.' ? 'go.mod' : relative + '/go.mod';
  const filename = ancestor(root, mod, 'file', true);
  if (fs.existsSync(filename) && goRecords(fs.readFileSync(filename,'utf8')).some(record => record.kind === 'replace' && record.module === MODULE)) found.push(relative);
  for (const entry of fs.readdirSync(current,{withFileTypes:true}).sort((a,b)=>a.name.localeCompare(b.name))) {
    if (entry.name.startsWith('.') || ignored.has(entry.name) || ['kit','third_party','vendor','sample','testdata'].includes(entry.name)) continue;
    if (entry.isSymbolicLink()) fail('Symlink during configured Go discovery');
    if (entry.isDirectory()) found.push(...discoverGo(root, relative === '.' ? entry.name : relative + '/' + entry.name));
  }
  return found;
}
/** Closed Native E1 configuration. Absence is active; only Cat may stage the sealed original SDK. */
function validateUiAdoption(config) {
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
function normalConfig(root, input) {
  if (!input || typeof input !== 'object' || Array.isArray(input) || Object.keys(input).some(key => !['role','app','npm_dir','vendor_dir','go_dirs','ui_adoption'].includes(key))) fail('repo:kit-config has unknown fields');
  if (!['core','consumer'].includes(input.role) || typeof input.app !== 'string' || !/^[A-Za-z][A-Za-z0-9_-]*$/.test(input.app)) fail('Explicit role and portable app required');
  const phase = validateUiAdoption(input);
  const npm = portable(input.npm_dir ?? (input.role === 'core' ? 'web-kit' : 'frontend/node_modules/@roedu/web-kit'));
  if (npm.split('/').some(part => part.startsWith('.') || ignored.has(part) && part !== 'node_modules') || immutable.some(part => contains(part,npm))) fail('npm_dir is only an installed kit locator');
  ancestor(root,npm,'dir',true);
  const vendor = portable(input.vendor_dir ?? 'frontend/vendor');
  if (vendor.split('/').some(part => part.startsWith('.') || ignored.has(part) || ['kit','node_modules','third_party'].includes(part))) fail('Unsafe configured vendor destination');
  const dirs = input.go_dirs ?? (input.role === 'consumer' ? discoverGo(root) : []);
  if (!Array.isArray(dirs) || !dirs.length) fail('Nonempty configured Go modules required');
  const go = dirs.map(value => portable(value,true));
  if (new Set(go).size !== go.length) fail('Duplicate configured Go modules');
  for (const directory of go) {
    if (directory !== '.') writable(directory);
    ancestor(root,directory,'dir'); ancestor(root,directory === '.' ? 'go.mod' : directory + '/go.mod','file');
  }
  if (input.role === 'consumer') {
    const trees = [vendor,...go.map(directory => (directory === '.' ? '' : directory + '/') + 'third_party/webkit')];
    if (trees.some((item,index) => trees.some((other,j) => index !== j && (contains(item,other) || contains(other,item))))) fail('Configured destinations overlap');
    if (trees.some(item => [...immutable,...gates,'.gate.env','versions.lock.json'].some(other => contains(item,other) || contains(other,item)))) fail('Configured destinations overlap immutable hooks, kit or root config');
    for (const tree of trees) ancestor(root,tree,'dir',true);
    const parent = path.posix.dirname(vendor);
    ancestor(root,path.posix.join(parent,'package.json'),'file'); ancestor(root,path.posix.join(parent,'package-lock.json'),'file',true);
    for (const directory of go) ancestor(root,(directory === '.' ? '' : directory + '/') + 'go.sum','file',true);
  }
  return {role:input.role,app:input.app,npm_dir:npm,vendor_dir:vendor,go_dirs:go,...(phase?{ui_adoption:phase}:{})};
}
function goTokens(line) {
  const result = [];
  let index = 0;
  while (index < line.length) {
    if (/\s/.test(line[index])) { index++; continue; }
    if (line.slice(index, index + 2) === '//') break;
    if ('()'.includes(line[index])) { result.push(line[index++]); continue; }
    if (line.slice(index, index + 2) === '=>') { result.push('=>'); index += 2; continue; }
    if (line[index] === '"' || line[index] === '`') {
      const quote = line[index++]; let value = '', closed = false;
      while (index < line.length) {
        let character = line[index++];
        if (character === quote) { closed = true; break; }
        if (character === '\\' && quote === '"') {
          const escape = line[index++], simple = { a: '\x07', b: '\b', f: '\f', n: '\n', r: '\r', t: '\t', v: '\x0b', '\\': '\\', '"': '"' };
          if (Object.hasOwn(simple, escape)) character = simple[escape];
          else {
            let digits, base;
            if (escape === 'x' || escape === 'u' || escape === 'U') {
              const count = escape === 'x' ? 2 : escape === 'u' ? 4 : 8; digits = line.slice(index, index + count); index += count; base = 16;
              if (digits.length !== count || !/^[a-fA-F0-9]+$/.test(digits)) fail('Malformed quoted Go escape');
            } else if (/[0-7]/.test(escape ?? '')) {
              digits = escape + line.slice(index, index + 2); index += 2; base = 8;
              if (!/^[0-7]{3}$/.test(digits)) fail('Malformed quoted Go escape');
            } else fail('Malformed quoted Go escape');
            const point = Number.parseInt(digits, base);
            if (point > 0x10ffff || (point >= 0xd800 && point <= 0xdfff) || (base === 8 && point > 255)) fail('Invalid quoted Go code point');
            character = String.fromCodePoint(point);
          }
        }
        value += character;
      }
      if (!closed || /[\x00-\x1f\x7f]/.test(value)) fail('Malformed quoted Go path');
      result.push(value); continue;
    }
    const begin = index;
    while (index < line.length && !/\s/.test(line[index]) && !'()'.includes(line[index]) && line.slice(index, index + 2) !== '//' && line.slice(index, index + 2) !== '=>') index++;
    result.push(line.slice(begin, index));
  }
  return result;
}
function goRecords(text) {
  if (text.includes('\0')) fail('Malformed Go module text');
  let block = '', modules = 0;
  const records = [];
  for (const [index, line] of text.split(/\r?\n/).entries()) {
    const tokens = goTokens(line); if (!tokens.length) continue;
    if (tokens[0] === ')') { if (!block || tokens.length !== 1) fail('Malformed Go directive block'); block = ''; continue; }
    if (tokens.length === 2 && tokens[1] === '(') { if (block) fail('Nested Go directive block'); block = tokens[0]; continue; }
    const kind = block || tokens[0], body = block ? tokens : tokens.slice(1);
    if (kind === 'module') { if (body.length !== 1) fail('Malformed Go module directive'); modules++; records.push({ index, kind, module: body[0] }); }
    if (kind === 'require') {
      if (body.length !== 2) fail('Malformed Go require directive');
      records.push({ index, kind, module: body[0], version: body[1] });
    }
    if (kind === 'replace') {
      const arrow = body.indexOf('=>');
      if (![1, 2].includes(arrow) || ![arrow + 2, arrow + 3].includes(body.length)) fail('Malformed Go replace directive');
      records.push({ index, kind, module: body[0], version: arrow === 2 ? body[1] : undefined, target: body[arrow + 1], targetVersion: body[arrow + 2] });
    }
  }
  if (block || modules !== 1) fail('One complete Go module directive required');
  return records;
}
// WRAPPER_CONFIG_MAIN
try {
  const started = Date.now();
  const child = spawnSync('task',['--silent','repo:kit-config'],{cwd:process.cwd(),encoding:'utf8',maxBuffer:1024*1024,timeout:60000});
  if (child.error || child.signal || child.status !== 0 || child.stderr.trim()) fail('Actual repo:kit-config failed or emitted diagnostics');
  const config = normalConfig(process.cwd(),JSON.parse(child.stdout));
  process.stdout.write(JSON.stringify({schema:1,target:process.argv[2],sha:process.argv[3],tree_sha256:process.argv[4],toolchain_digest:process.argv[5],config,config_sha256:digest(JSON.stringify(config)),command:{command:'task',args:['--silent','repo:kit-config'],exit_code:child.status,duration_ms:Date.now()-started,stdout_sha256:digest(child.stdout),stderr_sha256:digest(child.stderr)}})+'\n');
} catch (error) { process.stderr.write('gate config: '+error.message+'\n'); process.exitCode=2; }
JS_WRAPPER_CONFIG
}
metadata_paths() { python3 -I - "$1" "$src" "$dst" "$target" "$sha" "$GATE_TREE_SHA256" "$TOOLCHAIN_DIGEST" "$2" <<'PY_METADATA'
import hashlib,json,os,re,stat,sys
filename,src,dst,target,sha,tree,image,out=sys.argv[1:]
m=json.load(open(filename)); assert m['schema']==1
for key,value in [('target',target),('sha',sha),('tree_sha256',tree),('toolchain_digest',image)]: assert m[key]==value,key
c=m['config']; assert set(c) in ({'role','app','npm_dir','vendor_dir','go_dirs'},{'role','app','npm_dir','vendor_dir','go_dirs','ui_adoption'}) and c['role'] in ('core','consumer')
assert re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*',c['app'])
assert m['config_sha256']==hashlib.sha256(json.dumps(c,separators=(',',':')).encode()).hexdigest()
cmd=m['command']; assert cmd['command']=='task' and cmd['args']==['--silent','repo:kit-config'] and cmd['exit_code']==0
assert type(cmd['duration_ms']) is int and cmd['duration_ms']>=0 and all(re.fullmatch('[0-9a-f]{64}',cmd[k]) for k in ('stdout_sha256','stderr_sha256'))
def portable(p,dot=False):
    assert type(p) is str and (dot and p=='.' or p and not p.startswith('/') and all(re.fullmatch('[A-Za-z0-9_@.-]+',x) and x not in ('.','..') for x in p.split('/'))), 'nonliteral metadata path'
    return p
def ancestor(root,p,kind,missing=False):
    cursor=root; parts=[] if p=='.' else p.split('/')
    for i,part in enumerate(parts):
        cursor=os.path.join(cursor,part)
        try: st=os.lstat(cursor)
        except FileNotFoundError:
            assert missing; continue
        assert not stat.S_ISLNK(st.st_mode) and (stat.S_ISDIR(st.st_mode) or stat.S_ISREG(st.st_mode)), 'nonregular source/runner ancestor'
        if i < len(parts)-1: assert stat.S_ISDIR(st.st_mode)
    if os.path.lexists(cursor): assert stat.S_ISREG(os.lstat(cursor).st_mode) if kind=='file' else stat.S_ISDIR(os.lstat(cursor).st_mode)
def regular_tree(root,p):
    ancestor(root,p,'dir',True); base=os.path.join(root,p)
    if not os.path.exists(base): return
    for directory,dirs,files in os.walk(base,followlinks=False):
        for name in dirs+files:
            st=os.lstat(os.path.join(directory,name)); assert not stat.S_ISLNK(st.st_mode) and (stat.S_ISDIR(st.st_mode) or stat.S_ISREG(st.st_mode)), 'nonregular owned tree'
def ui_phase(config):
    if 'ui_adoption' not in config: return None
    phase=config['ui_adoption']; assert config['role']=='consumer' and config['app']=='cat_de_roman_esti'
    assert type(phase) is dict and set(phase)=={'mode','until','legacy'} and phase['mode']=='staged-react' and phase['until']=='S1-M2', 'closed ui_adoption phase required'
    legacy=phase['legacy']; assert type(legacy) is dict and set(legacy)=={'version','archive_sha256','source_sha','receipt','receipt_sha256'} and legacy['version']=='0.3.0'
    for key in ('archive_sha256','receipt_sha256'): assert type(legacy[key]) is str and re.fullmatch('[a-f0-9]{64}',legacy[key]), 'typed legacy seal required'
    assert type(legacy['source_sha']) is str and re.fullmatch('[a-f0-9]{40}([a-f0-9]{24})?',legacy['source_sha'])
    receipt=portable(legacy['receipt']); assert not re.search(r'\.tsbuildinfo(?:\.(?:gz|br))?$',receipt); assert not any(receipt==directory or receipt.startswith(directory+'/') for directory in (config['vendor_dir'],config['npm_dir'])); excluded={'kit','node_modules','third_party','vendor','dist','embedfs','test-results','TASK_BRIEF.md','TASK_RESULT.md','SWARM_RESULT.md'}
    assert all(not p.startswith('.') and p not in excluded for p in receipt.split('/')), 'receipt is outside included source'
    return phase
phase=ui_phase(c)
portable(c['npm_dir']); portable(c['vendor_dir']); assert type(c['go_dirs']) is list and c['go_dirs'] and len(set(c['go_dirs']))==len(c['go_dirs'])
for p in c['go_dirs']: portable(p,True)
files=[]; trees=[]; vendor=''
if c['role']=='consumer':
    vendor=c['vendor_dir']; parent=os.path.dirname(vendor)
    files=['scripts/gate.sh','compose.gate.yml','Taskfile.yml','Dockerfile.toolchain','versions.lock.json',os.path.join(parent,'package.json'),os.path.join(parent,'package-lock.json')]
    for d in c['go_dirs']:
        prefix='' if d=='.' else d+'/'
        files.extend([prefix+'go.mod',prefix+'go.sum']); trees.append(prefix+'third_party/webkit')
for root in (src,dst):
    ancestor(root,c['npm_dir'],'dir',True)
    for d in c['go_dirs']: ancestor(root,d,'dir'); ancestor(root,('' if d=='.' else d+'/')+'go.mod','file')
    for p in files: ancestor(root,p,'file',True)
    for p in ([vendor] if vendor else [])+trees: regular_tree(root,p)
    if vendor and os.path.exists(os.path.join(root,vendor)):
        for name in os.listdir(os.path.join(root,vendor)):
            if re.fullmatch(r'roedu-(ui|web-kit)-[^/]+\.tgz(?:\.sha256)?',name): ancestor(root,vendor+'/'+name,'file')
preserved=[]; phase_record={'mode':'active','paths':[]}
if phase:
    legacy=phase['legacy']; sdk=vendor+'/roedu-ui-'+legacy['version']+'.tgz'; sidecar=sdk+'.sha256'; receipt=legacy['receipt']
    preserved=[sdk,sidecar,receipt]; states=[]; manifest=os.path.join(os.path.dirname(vendor),'package.json'); pointer='file:'+os.path.basename(vendor)+'/roedu-ui-'+legacy['version']+'.tgz'
    for root in (src,dst):
        for relative in (sdk,receipt): ancestor(root,relative,'file')
        assert hashlib.sha256(open(os.path.join(root,sdk),'rb').read()).hexdigest()==legacy['archive_sha256'], 'sealed original SDK bytes changed'
        assert hashlib.sha256(open(os.path.join(root,receipt),'rb').read()).hexdigest()==legacy['receipt_sha256'], 'sealed original runtime receipt changed'
        ancestor(root,manifest,'file'); package=json.load(open(os.path.join(root,manifest)))
        sections=[name for name in ('dependencies','devDependencies','optionalDependencies','peerDependencies') if '@roedu/ui' in package.get(name,{})]
        assert len(sections)==1 and sections[0]!='peerDependencies' and package[sections[0]]['@roedu/ui']==pointer, 'staged UI must preserve only the already-selected original pointer'
        ancestor(root,sidecar,'file',True); sidecar_file=os.path.join(root,sidecar); exists=os.path.lexists(sidecar_file)
        if exists:
            value=open(sidecar_file,'rb').read(); match=re.fullmatch(rb'([a-f0-9]{64})(?:[ \t]+\*?([^\r\n]+))?\r?\n?',value)
            assert match and match[1].decode()==legacy['archive_sha256'] and (match[2] is None or match[2].decode()==os.path.basename(sdk)), 'original SDK sidecar disagrees with its seal'
        values=[]
        for relative in preserved:
            filename=os.path.join(root,relative); exists=os.path.lexists(filename)
            values.append({'path':relative,'exists':exists,'sha256':hashlib.sha256(open(filename,'rb').read()).hexdigest() if exists else None,'mode':stat.S_IMODE(os.lstat(filename).st_mode) if exists else None})
        states.append(values)
    assert states[0]==states[1], 'source and runner sealed UI paths differ'
    phase_record={'mode':'staged-react','config':phase,'pointer':{'manifest':manifest,'section':sections[0],'value':pointer},'paths':states[0]}
with open(os.path.join(out,'phase-preserved.json'),'w') as f: json.dump(phase_record,f,separators=(',',':')); f.write('\n')
def records(name,values):
    with open(os.path.join(out,name),'wb') as f:
        for value in values: f.write(value.encode()+b'\0')
records('vendor.paths',[vendor] if vendor else []); records('file.paths',files); records('tree.paths',trees); records('preserved.paths',preserved)
patterns=['/'+p for p in files]+['/'+p+'/***' for p in trees]
if vendor: patterns += ['/'+vendor+'/'+family+suffix for family in ('roedu-ui-*','roedu-web-kit-*') for suffix in ('.tgz','.tgz.sha256')]
records('sync.paths',patterns)
PY_METADATA
}

DEPS=(package.json package-lock.json go.mod go.sum); KIT=(./scripts/gate.sh ./compose.gate.yml ./Taskfile.yml ./Dockerfile.toolchain)   # never .gate.env (per-repo values)
case "$target" in golden:capture) allow=('*/testdata/golden*/*' '*/golden/testdata/*');; contract:refresh) allow=('*/internal/contract/assets.json');;
  legacy:freeze) allow=('./legacy/*');; baseline) allow=('*/baselines/*');; kit:sync) allow=("${KIT[@]}" ./.gate.env ./versions.lock.json);; *) allow=('/none');; esac
if [ "$target" = gen ] && [ "$resolve" = 1 ]; then allow+=(./versions.lock.json); fi
before=$(prot "${allow[@]}") || die "protected baseline failed"; rc=0; stage=kit-config; primary_started=0
case "$target" in unit|full) cmd=(task "gate:$target");; shell) cmd=(bash);; *) cmd=(task "$target");; esac
provisional_tree=$GATE_TREE_SHA256
meta_before=$(snapshot . metadata) || rc=2
if [ "$rc" = 0 ]; then capture_config > "$control/config-discovery.json" || rc=$?; fi
if [ "$rc" = 0 ] && [ "$meta_before" != "$(snapshot . metadata)" ]; then rc=3; stage=metadata-mutated-source; fi
if [ "$rc" = 0 ]; then metadata_paths "$control/config-discovery.json" "$control" || rc=2; fi
if [ "$rc" = 0 ]; then
  mapfile -d '' -t KIT_FILES < "$control/file.paths"; mapfile -d '' -t KIT_TREES < "$control/tree.paths"; mapfile -d '' -t KIT_PRESERVED < "$control/preserved.paths"
  KIT_VENDOR=$(tr -d '\0' < "$control/vendor.paths")
  [ "$target" != kit:sync ] || [ -n "$KIT_VENDOR" ] || { rc=2; stage=kit-role; }
fi
if [ "$rc" = 0 ]; then
  # Generic copy excludes dist. Restore only owned Go trees before final identity.
  [ "$provisional_tree" = "$(snapshot "$src" legacy-tree)" ] && [ "$state" = "$(git -C "$src" status --porcelain)" ] || { rc=4; stage=source-changed; }
  if [ "$rc" = 0 ]; then for p in "${KIT_TREES[@]}"; do
    if [ -d "$src/$p" ]; then mkdir -p -- "$dst/$p"; FGO=(); for x in "${EX[@]}"; do [ "$x" = dist ] || FGO+=("--exclude=$x"); done
      rsync -a --delete "${FGO[@]}" "$src/$p/" "$dst/$p/" || { rc=4; stage=go-source-copy; break; }; fi
  done; fi
fi
if [ "$rc" = 0 ]; then
  GATE_TREE_SHA256=$(snapshot . tree) || rc=2; export GATE_TREE_SHA256
  [ "$GATE_TREE_SHA256" = "$(snapshot "$src" tree)" ] || { rc=4; stage=source-changed; }
fi
if [ "$rc" = 0 ]; then
  meta_before=$(snapshot . metadata) || rc=2
  if [ "$rc" = 0 ]; then capture_config > "$control/config-before.json" || rc=$?; fi
  if [ "$rc" = 0 ] && [ "$meta_before" != "$(snapshot . metadata)" ]; then rc=3; stage=metadata-mutated-source; fi
  if [ "$rc" = 0 ]; then if ! python3 -I - "$control/config-discovery.json" "$control/config-before.json" <<'PY_CONFIG_EQUAL'
import json,sys
assert json.load(open(sys.argv[1]))['config']==json.load(open(sys.argv[2]))['config'], 'configuration changed during source copy'
PY_CONFIG_EQUAL
    then rc=2; fi
  fi
fi
if [ "$rc" = 0 ]; then
  metadata_paths "$control/config-before.json" "$control" || rc=2
  CONFIG_SHA=$(sha256sum "$control/config-before.json" | cut -d' ' -f1) || rc=2
  PLAN_SHA=$(snapshot "$control" trust config-before.json vendor.paths file.paths tree.paths sync.paths preserved.paths phase-preserved.json) || rc=2
  if [ "$rc" = 0 ]; then cp -- "$control/config-before.json" ".gate/$tdir/wrapper-kit-config.json" || rc=4; if [ "$rc" = 0 ]; then chmod 0444 ".gate/$tdir/wrapper-kit-config.json" || rc=4; fi; fi
  if [ "$rc" = 0 ]; then write_current_context || { rc=4; stage=current-context-write; }; fi
  if [ "$target" = kit:sync ] && [ "$rc" = 0 ]; then KIT_APPLY=1; fi
  if [ "$target" = deps ] || { [ "$target" = gen ] && [ "$resolve" = 1 ]; }; then for p in "${KIT_FILES[@]}"; do case "$p" in scripts/gate.sh|compose.gate.yml|Taskfile.yml|Dockerfile.toolchain|versions.lock.json) ;; *) allow+=("./$p");; esac; done; fi
  before=$(prot "${allow[@]}") || rc=2
fi
record_app_image() {
  GATE_APP_IMAGE_ID=$(docker image inspect -f '{{.Id}}' "$APP_IMG") || return 2
  [[ $GATE_APP_IMAGE_ID =~ ^sha256:[0-9a-f]{64}$ ]] || return 2
  export GATE_APP_IMAGE_ID
}
if [ "$rc" = 0 ]; then primary_started=1; case "$target" in image) stage=image; bounded_build --load --no-cache --build-arg "GATE_SHA=$sha" --build-arg "GATE_TREE_SHA256=$GATE_TREE_SHA256" --label "org.opencontainers.image.revision=$sha" --label "org.roedu.tree-sha256=$GATE_TREE_SHA256" -f "$APP_DOCKERFILE" -t "$APP_IMG" . || rc=$?
  if [ "$rc" = 0 ]; then record_app_image || rc=$?; fi
  if [ "$rc" = 0 ]; then stage=task; "${MDC[@]}" --profile unit run --no-deps --rm --user "$(id -u):$(id -g)" runner task image:record || rc=$?; fi;;   # host-side, digest-pinned bases
  qualify) [ -f scripts/qualify-native.sh ] || die "qualify exists only in social"; read -ra qa <<<"$QUALIFY_ARGS"; stage=qualify; bash scripts/qualify-native.sh "${qa[@]}" || rc=$?;;
  *) if [ "$profile" = full ] && [ ! -f "$APP_DOCKERFILE" ]; then rc=2; stage=missing-app-image; fi
     if [ "$profile" = full ] && [ -f "$APP_DOCKERFILE" ]; then stage=app-image; bounded_build --load -q --build-arg "GATE_SHA=$sha" --build-arg "GATE_TREE_SHA256=$GATE_TREE_SHA256" --label "org.opencontainers.image.revision=$sha" --label "org.roedu.tree-sha256=$GATE_TREE_SHA256" -f "$APP_DOCKERFILE" -t "$APP_IMG" . >/dev/null || rc=$?; if [ "$rc" = 0 ]; then record_app_image || rc=$?; fi; fi
     if [ "$rc" = 0 ] && [ "$profile" = full ]; then
       "${MDC[@]}" --profile full up -d --wait db app || rc=$?
       if [ "$rc" = 0 ]; then
         running_container=$("${MDC[@]}" --profile full ps -q app) || rc=$?
         if [ "$rc" = 0 ]; then
           running_image=$(docker inspect -f '{{.Image}}' "$running_container") || rc=$?
           if [ "$running_image" != "$GATE_APP_IMAGE_ID" ]; then rc=2; stage=runtime-image-mismatch; fi
         fi
       fi
     fi
     if [ "$rc" = 0 ]; then stage=task; "${MDC[@]}" --profile "$profile" run --no-deps --rm --user "$(id -u):$(id -g)" runner "${cmd[@]}" || rc=$?; fi;; esac; fi
if [ "$primary_started" = 1 ] && ! verify_current_context; then rc=4; stage=current-context-changed; fi
safe_path "$src/.gate/$tdir"; safe_path "$dst/.gate/$tdir"; safe_path "$dst/.gate/$tdir/result.json"
[ -z "$(find ".gate/$tdir" -type l -print -quit)" ] || die "symlink in gate evidence"
if [ "$rc" = 0 ] && [ ! -f ".gate/$tdir/result.json" ]; then
  case "$target" in image|qualify|shell) ;; *) rc=5; stage=missing-result;; esac
fi
if [ -f ".gate/$tdir/result.json" ]; then
  if ! python3 -I - ".gate/$tdir/result.json" "$target" "$sha" "$dirty" "$GATE_TREE_SHA256" "$TOOLCHAIN_DIGEST" "$P" "$CSP_STAGE" <<'PY_RESULT'
import hashlib,json,sys
p,target,sha,dirty,tree,image,parallel,csp=sys.argv[1:]
r=json.load(open(p)); required={'schema','target','status','sha','dirty','tree_sha256','toolchain_digest','versions_lock_sha256','parallel','started','finished','checks','csp','budgets','artifacts'}
assert required <= r.keys() and r['schema']==1
for k,v in [('target',target),('sha',sha),('dirty',dirty=='true'),('tree_sha256',tree),('toolchain_digest',image),('parallel',int(parallel)),('versions_lock_sha256',hashlib.sha256(open('versions.lock.json','rb').read()).hexdigest())]: assert r[k]==v,k
assert r['status'] in ('pass','fail') and isinstance(r['checks'],list) and r['checks']
assert r['csp']['stage']==csp
assert all(type(r['csp'][k]) is int and r['csp'][k]>=0 for k in ('violations','legacy_violations'))
if r['status']=='pass':
    assert r['csp']['violations']==0
    assert all(v.get('status')!='fail' for v in r['budgets'].values())
for c in r['checks']:
    assert c['status'] in ('pass','fail','skipped')
    if r['status']=='pass':
        assert c['status']!='fail'
        if c['status']=='skipped': assert target=='unit' and c.get('reason') in ('no-dsn','no-device')
if r['status']=='pass' and target=='full': assert all(c['status']=='pass' for c in r['checks'])
PY_RESULT
  then rc=5; rm -f ".gate/$tdir/result.json"; stage=invalid-result; fi
fi
if [ "$rc" = 0 ] && [ -f ".gate/$tdir/result.json" ] && ! python3 -I -c 'import json,sys; sys.exit(json.load(open(sys.argv[1]))["status"] != "pass")' ".gate/$tdir/result.json"; then rc=1; stage=task-result-fail; fi
ro=0; if [ "$primary_started" = 1 ] && [ "$before" != "$(prot "${allow[@]}")" ]; then ro=1; rc=3; stage=read-only-path; rm -f ".gate/$tdir/result.json"; fi   # sec 4.8: no result counts
if [ "$rc" != 0 ] && [ ! -f ".gate/$tdir/result.json" ]; then printf '{"status":"fail","reason":"wrapper:%s","rc":%s,"sha":"%s","tree_sha256":"%s"}\n' \
  "$stage" "$rc" "$sha" "$GATE_TREE_SHA256" > ".gate/$tdir/wrapper-fail.json"; fi
if [ "$ro" = 1 ]; then mkdir -p "$src/.gate/$tdir"; rsync -a --delete ".gate/$tdir/" "$src/.gate/$tdir/"; fi   # always: a run without a result clears the source copy too
if [ "$ro" = 1 ]; then echo "gate: '$target' changed a read-only path (sec 4.8); result discarded, nothing else synced back" >&2; exit 3; fi
if [ "$rc" = 0 ] && [ "$GATE_TREE_SHA256" != "$(snapshot "$src" tree)" ]; then
  rc=4; echo "gate: source changed during gate; refusing sync-back" >&2
fi
if [ "$rc" = 0 ]; then
  stage=post-config
  [ "$CONTROL_SHA" = "$(snapshot "$control" trust .gate.env compose.gate.yml Taskfile.yml Taskfile.repo.yml)" ] && [ "$PLAN_SHA" = "$(snapshot "$control" trust config-before.json vendor.paths file.paths tree.paths sync.paths preserved.paths phase-preserved.json)" ] || { rc=4; stage=control-changed; }
  [ "$(sha256sum Taskfile.repo.yml | cut -d' ' -f1)" = "$(sha256sum "$control/Taskfile.repo.yml" | cut -d' ' -f1)" ] || { rc=3; stage=repo-hook-changed; }
  if [ "$rc" = 0 ]; then
    post_tree=$(snapshot . metadata) || rc=2
    cp -- Taskfile.yml "$control/applied-Taskfile.yml" || rc=4
    if [ "$rc" = 0 ]; then cp -- "$control/Taskfile.yml" Taskfile.yml || rc=4; fi
    if [ "$rc" = 0 ]; then capture_config > "$control/config-after.json" || rc=$?; fi
    cp -- "$control/applied-Taskfile.yml" Taskfile.yml || { rc=4; stage=taskfile-restore; }
    if [ -f "$control/config-after.json" ]; then cp -- "$control/config-after.json" ".gate/$tdir/wrapper-config-after.json" || rc=4; fi
    if [ "$rc" = 0 ] && [ "$post_tree" != "$(snapshot . metadata)" ]; then rc=3; stage=metadata-mutated-source; fi
    if [ "$rc" = 0 ]; then if ! python3 -I - "$control/config-before.json" "$control/config-after.json" <<'PY_POST_CONFIG'
import json,sys
assert json.load(open(sys.argv[1]))['config']==json.load(open(sys.argv[2]))['config'], 'configuration changed during task'
PY_POST_CONFIG
      then rc=4; stage=config-drift; fi
    fi
  fi
  if [ "$rc" = 0 ] && [ "$CONFIG_SHA" != "$(sha256sum ".gate/$tdir/wrapper-kit-config.json" | cut -d' ' -f1)" ]; then rc=4; stage=frozen-config-changed; fi
fi
read -ra XS <<<"$SYNC_BACK"; for p in "${XS[@]}"; do [[ $p =~ ^[A-Za-z0-9_.*/-]+$ ]] || die "bad SYNC_BACK pattern '$p'"; done   # sync-back per target (sec 4.2 step 8)
SB=(); case "$target" in gen) SB=("${XS[@]}" '*_templ.go' routes_gen.go vm_gen.go tokens.css 'theme-*.css' tokens.ts tokens.go)
       if [ "$resolve" = 1 ]; then SB+=(versions.lock.json "${DEPS[@]}"); fi;;   deps) SB=("${XS[@]}" "${DEPS[@]}");;
  kit:sync) if [ "$rc" = 0 ]; then mapfile -d '' -t SB < "$control/sync.paths" || rc=4; fi;;   # exact frozen paths; no XS or DEPS globs
  golden:capture) SB=('testdata/golden*/***' 'golden/testdata/***');;  contract:refresh) SB=('internal/contract/assets.json');;
  legacy:freeze) SB=('/legacy/***');;  baseline) SB=('baselines/***');; esac
if [ "$target" = kit:sync ] && [ "$rc" = 0 ]; then
  ni=$(grep -E '^TOOLCHAIN_IMAGE=' .gate.env | tail -n1 || true); nd=$(grep -E '^TOOLCHAIN_DIGEST=' .gate.env | tail -n1 || true)
  if ! [[ ${ni#*=} =~ ^roedu-toolchain:[a-z0-9][a-z0-9._-]{0,127}$ && ${nd#*=} =~ ^sha256:[0-9a-f]{64}$ ]]; then rc=4; fi
fi
if [ "$rc" = 0 ] && ! verify_current_context; then rc=4; stage=current-context-changed; fi
if [ "$rc" = 0 ] && [ ${#SB[@]} -gt 0 ]; then
  # Frozen host plan; guard both source and runner before ANY source mutation.
  [ "$GATE_TREE_SHA256" = "$(snapshot "$src" tree)" ] || { rc=4; stage=source-changed; }
  [ "$PLAN_SHA" = "$(snapshot "$control" trust config-before.json vendor.paths file.paths tree.paths sync.paths preserved.paths phase-preserved.json)" ] || { rc=4; stage=plan-changed; }
  if [ "$rc" = 0 ]; then metadata_paths "$control/config-before.json" "$control" || { rc=4; stage=sync-ancestors; }; fi
fi
if [ "$rc" = 0 ] && [ "$target" = kit:sync ]; then
  # Exact file operations and exact owned Go subtrees: never root-wide deletion.
  if ! python3 -I - "$control" "$src" "$dst" <<'PY_KIT_RETURN'
import hashlib,json,os,re,shutil,stat,subprocess,sys
control,source,mirror=sys.argv[1:]
def records(name):
    raw=open(os.path.join(control,name),'rb').read()
    assert not raw or raw.endswith(b'\0')
    values=[v.decode('utf-8') for v in raw.split(b'\0') if v]
    assert len(values)==len(set(values))
    for value in values:
        assert value and not value.startswith('/') and all(re.fullmatch('[A-Za-z0-9_@.-]+',p) and p not in ('.','..') for p in value.split('/'))
    return values
def guard(root,relative,kind,missing=True):
    current=root
    for i,part in enumerate(relative.split('/')):
        current=os.path.join(current,part)
        if not os.path.lexists(current):
            assert missing; continue
        mode=os.lstat(current).st_mode
        assert not stat.S_ISLNK(mode) and (stat.S_ISREG(mode) or stat.S_ISDIR(mode))
        if i<len(relative.split('/'))-1: assert stat.S_ISDIR(mode)
    if os.path.lexists(current):
        assert stat.S_ISREG(os.lstat(current).st_mode) if kind=='file' else stat.S_ISDIR(os.lstat(current).st_mode)
    elif not missing: raise AssertionError('Required return path absent')
    return current
def tree_guard(root,relative):
    base=guard(root,relative,'dir')
    if os.path.exists(base):
        for directory,dirs,files in os.walk(base,followlinks=False):
            for name in dirs+files:
                mode=os.lstat(os.path.join(directory,name)).st_mode
                assert not stat.S_ISLNK(mode) and (stat.S_ISREG(mode) or stat.S_ISDIR(mode))
    return base
files,trees,vendors,preserved=records('file.paths'),records('tree.paths'),records('vendor.paths'),set(records('preserved.paths'))
assert len(vendors)==1
vendor=vendors[0]; owned=re.compile(r'roedu-(ui|web-kit)-[^/]+\.tgz(?:\.sha256)?')
archives=set()
for root in (source,mirror):
    directory=guard(root,vendor,'dir')
    if os.path.isdir(directory):
        for name in os.listdir(directory):
            if owned.fullmatch(name): archives.add(vendor+'/'+name)
for relative in files+sorted(archives):
    for root in (source,mirror): guard(root,relative,'file')
for relative in trees:
    tree_guard(source,relative); tree_guard(mirror,relative); guard(mirror,relative,'dir',False)
phase=json.load(open(os.path.join(control,'phase-preserved.json')))
if phase['mode']=='staged-react':
    legacy=phase['config']['legacy']; assert preserved=={item['path'] for item in phase['paths']}
    for root in (source,mirror):
        for item in phase['paths']:
            filename=guard(root,item['path'],'file',not item['exists'])
            assert os.path.lexists(filename)==item['exists'], 'sealed SDK sidecar presence changed'
            if item['exists']: assert hashlib.sha256(open(filename,'rb').read()).hexdigest()==item['sha256'] and stat.S_IMODE(os.lstat(filename).st_mode)==item['mode'], 'sealed source/runner UI member changed'
        pointer=phase['pointer']; filename=guard(root,pointer['manifest'],'file',False); package=json.load(open(filename))
        sections=[name for name in ('dependencies','devDependencies','optionalDependencies','peerDependencies') if '@roedu/ui' in package.get(name,{})]
        assert sections==[pointer['section']] and package[sections[0]]['@roedu/ui']==pointer['value'], 'sealed original UI pointer changed'
    # Input filenames and hashes derive only from the selected committed bundle.
    selections=[]
    for root in (source,mirror):
        directory=guard(root,'kit','dir',False); names=set(os.listdir(directory)); tag=open(guard(root,'kit/CORE_TAG','file',False)).read()
        assert re.fullmatch(r'core-v1\.\d+\n?',tag); ui=[name for name in names if re.fullmatch(r'roedu-ui-\d+\.\d+\.\d+\.tgz',name)]; npm=[name for name in names if re.fullmatch(r'roedu-web-kit-\d+\.\d+\.\d+\.tgz',name)]
        assert len(ui)==len(npm)==1; go='web-kit-go-'+tag.strip()+'.tgz'; assert names=={'CORE_TAG','SHA256SUMS',ui[0],npm[0],go}
        sums={}
        for line in open(guard(root,'kit/SHA256SUMS','file',False)).read().splitlines():
            match=re.fullmatch(r'([a-f0-9]{64}) [ *]([^/\\\s]+)',line); assert match and match[2] in (ui[0],npm[0],go) and match[2] not in sums; sums[match[2]]=match[1]
        assert len(sums)==3
        for name,value in sums.items(): assert hashlib.sha256(open(guard(root,'kit/'+name,'file',False),'rb').read()).hexdigest()==value
        assert ui[0]!='roedu-ui-'+legacy['version']+'.tgz', 'selected staged UI must be distinct from sealed original'
        selections.append((tag,ui[0],npm[0],sums))
    assert selections[0]==selections[1], 'source/runner selected bundle differs'
    _,ui,npm,sums=selections[0]; allowed={vendor+'/'+name+suffix for name in (ui,npm) for suffix in ('','.sha256')}|{item['path'] for item in phase['paths'] if item['exists'] and item['path'].startswith(vendor+'/')}
    mirrored={vendor+'/'+name for name in os.listdir(guard(mirror,vendor,'dir',False)) if owned.fullmatch(name)}
    assert mirrored==allowed, 'staged phase cannot retain unrelated or stale owned archives'
    for name in (ui,npm):
        assert hashlib.sha256(open(guard(mirror,vendor+'/'+name,'file',False),'rb').read()).hexdigest()==sums[name]
        assert open(guard(mirror,vendor+'/'+name+'.sha256','file',False),'rb').read()==(sums[name]+'  '+name+'\n').encode(), 'selected archive sidecar differs'
else: assert phase['mode']=='active' and not preserved
# All destinations and both source sets were checked before the first mutation.
for relative in files+sorted(archives):
    if relative in preserved: continue
    src=guard(mirror,relative,'file'); dst=guard(source,relative,'file')
    if os.path.isfile(src):
        os.makedirs(os.path.dirname(dst),exist_ok=True); shutil.copy2(src,dst)
    elif os.path.isfile(dst): os.unlink(dst)
for relative in trees:
    src=guard(mirror,relative,'dir',False); dst=guard(source,relative,'dir')
    os.makedirs(dst,exist_ok=True)
    subprocess.run(['rsync','-a','--delete',src+'/',dst+'/'],check=True)
PY_KIT_RETURN
  then rc=4; stage=kit-return; fi
fi
if [ "$rc" = 0 ] && [ ${#SB[@]} -gt 0 ] && [ "$target" != kit:sync ]; then
  F=(); for p in "${EX[@]}"; do [ "$target" = kit:sync ] && [ "$p" = dist ] || F+=("--exclude=$p"); done
  for p in "${SB[@]}"; do F+=("--include=$p"); done
  # Real producer status is retained; no process-substitution status is lost.
  rsync -am --delete "${F[@]}" --include='*/' --exclude='*' ./ "$src"/ > "$control/sync.log" 2>&1 || { rc=4; stage=sync-back; }
  cat "$control/sync.log"
fi
if [ "$target" = kit:sync ] && [ "$rc" = 0 ]; then   # .gate.env is never synced back whole: only the tag's TOOLCHAIN_IMAGE/TOOLCHAIN_DIGEST lines move into it
  ni=$(grep -E '^TOOLCHAIN_IMAGE=' .gate.env | tr -d '\r' | tail -n1 || true); nd=$(grep -E '^TOOLCHAIN_DIGEST=' .gate.env | tr -d '\r' | tail -n1 || true)
  if [[ ${ni#*=} =~ ^roedu-toolchain:[a-z0-9][a-z0-9._-]{0,127}$ && ${nd#*=} =~ ^sha256:[0-9a-f]{64}$ ]]; then
    if [ "$ni" != "TOOLCHAIN_IMAGE=$TOOLCHAIN_IMAGE" ] || [ "$nd" != "TOOLCHAIN_DIGEST=$TOOLCHAIN_DIGEST" ]; then
      sed -i -e "s|^TOOLCHAIN_IMAGE=.*|$ni|" -e "s|^TOOLCHAIN_DIGEST=.*|$nd|" "$src/.gate.env" || rc=4; fi   # every other key and line stays byte-identical
  else echo "gate: kit:sync left no valid TOOLCHAIN_IMAGE/TOOLCHAIN_DIGEST in .gate.env; the worktree's .gate.env is untouched" >&2; rc=4; fi; fi
if [ "$rc" != 0 ] && [ -f ".gate/$tdir/result.json" ]; then
  if python3 -I -c 'import json,sys; sys.exit(json.load(open(sys.argv[1]))["status"] != "pass")' ".gate/$tdir/result.json"; then rm -f ".gate/$tdir/result.json"; fi
fi
if [ "$rc" = 4 ]; then
  rm -f ".gate/$tdir/result.json"
  printf '{"status":"fail","reason":"wrapper:sync-back","rc":4,"sha":"%s","tree_sha256":"%s"}\n' "$sha" "$GATE_TREE_SHA256" > ".gate/$tdir/wrapper-fail.json"
fi
if [ "$rc" != 0 ] && [ ! -f ".gate/$tdir/result.json" ] && [ ! -f ".gate/$tdir/wrapper-fail.json" ]; then
  printf '{"status":"fail","reason":"wrapper:%s","rc":%s,"sha":"%s","tree_sha256":"%s"}\n' "$stage" "$rc" "$sha" "$GATE_TREE_SHA256" > ".gate/$tdir/wrapper-fail.json"
fi
mkdir -p "$src/.gate/$tdir"
if [ "$primary_started" = 1 ] && ! verify_current_context; then
  rc=4; stage=current-context-changed; rm -f ".gate/$tdir/result.json"
  printf '{"status":"fail","reason":"wrapper:current-context-changed","rc":4,"sha":"%s","tree_sha256":"%s"}\n' "$sha" "$GATE_TREE_SHA256" > ".gate/$tdir/wrapper-fail.json"
fi
if ! rsync -a --delete ".gate/$tdir/" "$src/.gate/$tdir/"; then
  rm -f "$src/.gate/$tdir/result.json"
  printf '{"status":"fail","reason":"wrapper:evidence-copy","rc":4,"sha":"%s"}\n' "$sha" > "$src/.gate/$tdir/wrapper-fail.json"
  exit 4
fi
exit "$rc"; }
