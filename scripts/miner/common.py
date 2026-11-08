"""Read-only I/O and deterministic graph inspection.

Threat model. On a single-user development host, accidental escape from the
selected repository or fresh scratch tree, stale or malformed inputs, special
files, answer leakage and overwriting retained evidence are in scope. Reads
bind the bytes parsed, and outputs are private and exclusive. A concurrent
same-user attacker moving directories, tampering with tool files or inspecting
another role's files is outside this boundary. Hashes and sidecars support an
audit of separate role dispatches. They cannot prove isolation, signatures,
native runtime behavior or semantic approval.
"""
import argparse
import bisect
import collections
import hashlib
import json
import math
import os
import re
import stat
from pathlib import Path
import sys
import unicodedata

sys.dont_write_bytecode = True
_scratch_root = None
FIX = 'cat_de_roman_esti/fixtures/'
PACK_GAMES = ('conexiuni', 'contexto', 'lant', 'alchimie')
GAMES = PACK_GAMES + ('intrusul', 'perechi')
DIFFICULTIES = ('usor', 'normal', 'greu')
ALIASES = dict(zip(('cx','ct','lt','al','iq','pq'), GAMES))
MAX_BYTES = 64 * 1024 * 1024


def fail(message):
    raise ValueError(message)


def beneath(path, base):
    path, base = Path(path).expanduser().resolve(), Path(base).resolve()
    if path == base or base in path.parents:
        return path
    fail(f'path outside allowed tree: {path}')


def in_git_checkout(path):
    return any((parent / '.git').is_file() or (parent / '.git' / 'HEAD').is_file()
               for parent in (path, *path.parents))


def set_scratch_root(path):
    global _scratch_root
    root = Path(path).expanduser().resolve(strict=True)
    if not root.is_dir() or root == root.parent:
        fail('scratch root must be an existing directory below the filesystem root')
    if in_git_checkout(root):
        fail('scratch root must be outside Git checkouts')
    if (root / FIX / 'kg_sample.json').is_file():
        fail('scratch root must be separate from the Cat repository')
    _scratch_root = root


def add_scratch_argument(parser):
    parser.add_argument('--scratch-root', required=True, help='existing scratch directory outside Git checkouts')


def scratch(path):
    if _scratch_root is None:
        fail('an explicit scratch root is required')
    return beneath(path, _scratch_root)


def repo_or_scratch(path, repo):
    p = Path(path).expanduser().resolve()
    if p == _scratch_root or _scratch_root in p.parents:
        return p
    return beneath(p, repo.root)


def output_path(path):
    p = scratch(path)
    if p == _scratch_root or os.path.lexists(Path(path).expanduser()) or os.path.lexists(p):
        fail(f'output exists or is not a new file: {p}')
    if in_git_checkout(p.parent):
        fail('output must be outside Git checkouts')
    return p


def write_bytes(path, data):
    p = output_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p = output_path(p)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_BINARY', 0)
    fd = os.open(p, flags, 0o600)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
    except OSError:
        p.unlink(missing_ok=True)
        raise
    return sha256(data)


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode('utf-8')


def write_json(path, value):
    return write_bytes(path, json_bytes(value))


def read_regular(path):
    p = Path(path)
    # Refuse special files before open on platforms without O_NONBLOCK.
    if not stat.S_ISREG(p.stat().st_mode):
        fail(f'input is not a regular file: {p}')
    flags = os.O_RDONLY | getattr(os, 'O_NONBLOCK', 0) | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_BINARY', 0)
    with os.fdopen(os.open(p, flags), 'rb') as file:
        before = os.fstat(file.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_BYTES:
            fail(f'input is not a bounded regular file: {p}')
        data = file.read(MAX_BYTES + 1)
        after = os.fstat(file.fileno())
    if len(data) > MAX_BYTES:
        fail(f'input too large: {p}')
    if len(data) != before.st_size or (before.st_mtime_ns, before.st_ctime_ns) != (after.st_mtime_ns, after.st_ctime_ns):
        fail(f'input changed during read: {p}')
    return data


def strict_json(data):
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                fail(f'duplicate JSON key: {key}')
            result[key] = value
        return result

    def finite_float(value):
        parsed = float(value)
        if not math.isfinite(parsed):
            fail('non-finite JSON number')
        return parsed

    return json.loads(data.decode('utf-8'), object_pairs_hook=unique_object,
                      parse_float=finite_float, parse_constant=finite_float)


def json_object(data):
    value = strict_json(data)
    if not isinstance(value, dict):
        fail('expected a JSON object')
    return value


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def digest_file(path):
    return sha256(read_regular(path))


def norm(text):
    # Inspection key only. Native Unicode15 normalization/resolver gates remain mandatory.
    return ' '.join(''.join(c for c in unicodedata.normalize('NFKD', text) if not unicodedata.combining(c)).casefold().split())


def native_transform(surface,mapping):
    transformed=''.join(mapping.get(c,c) for c in surface)
    return re.sub(r'[\x09-\x0d\x1c-\x20\x85\xa0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+',' ',transformed).strip(' ')


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for k, v in value.items():
            yield from strings(k)
            yield from strings(v)
    elif isinstance(value, (list, tuple, set, frozenset)):
        for v in value:
            yield from strings(v)


def canonical_set(values):
    return sorted(set(values))


def partitions(groups):
    return sorted(sorted(group) for group in groups)


def signature(game, row):
    p = row.get('payload', row)
    if game == 'conexiuni':
        value = partitions(p['groups'].values())
    elif game == 'contexto':
        value = p['target']
    elif game == 'lant':
        value = [p['start'], p['target']]  # Direction is intentional.
    elif game == 'alchimie':
        value = [sorted(p['seeds']), p['target']]
    elif game == 'intrusul':
        value = sorted(p['members'] + [p['intruder']])
    elif game == 'perechi':
        value = partitions(pair['members'] for pair in p['pairs'])
    else:
        fail(f'unknown game: {game}')
    return hashlib.sha256(json_bytes([game, value])).hexdigest()


class Repo:
    def __init__(self, root):
        self.root = Path(root).expanduser().resolve()
        if not (self.root / FIX / 'kg_sample.json').is_file():
            fail('root must be an explicit Cat repository path')
        if _scratch_root and (self.root == _scratch_root or self.root in _scratch_root.parents or _scratch_root in self.root.parents):
            fail('scratch root and repository must be disjoint')
        self.cache = {}
        self.text_cache = {}
        self.line_cache = {}

    def data(self, rel):
        return strict_json(self.read(rel))

    def read(self, rel):
        p = beneath(self.root / rel, self.root)
        key = p.relative_to(self.root).as_posix()
        if key not in self.cache:
            self.cache[key] = read_regular(p)
        return self.cache[key]

    def text(self, rel):
        if rel not in self.text_cache:
            self.text_cache[rel] = self.read(rel).decode('utf-8')
        return self.text_cache[rel]

    def cite(self, rel, needle=None, start=1):
        text = self.text(rel)
        if rel not in self.line_cache:
            self.line_cache[rel] = [-1] + [i for i,c in enumerate(text) if c=='\n']
        offsets = self.line_cache[rel]
        offset = text.find(needle, offsets[min(len(offsets)-1,max(0,start-1))]+1) if needle is not None else -1
        line = bisect.bisect_left(offsets,offset) if offset>=0 else start
        return f'{rel}:{line}'

    def bindings(self):
        return [{'path': k, 'sha256': hashlib.sha256(v).hexdigest(), 'bytes': len(v)} for k, v in sorted(self.cache.items())]

    def provenance(self):
        return {'root': str(self.root), 'source_bindings': self.bindings(), 'tool_bindings': [
            {'path': p.name, 'sha256': digest_file(p)} for p in sorted(Path(__file__).parent.glob('*.py'))],
            'qualification': 'Read-only inspection; no validation, import, gate, runtime or review qualification.'}


def inventory(repo):
    pack = repo.data(FIX+'games_pack.json')
    rankings = repo.data(FIX+'board_rankings_v37.json')
    ratings = {r['id']: r for r in rankings['boards']}
    if len(ratings) != len(rankings['boards']):
        fail('duplicate ranking IDs')
    held = collections.defaultdict(list)
    for name in ('board_demotions_v43.json', 'contexto_demotions_v44.json', 'contexto_impact_reserve_v69.json', 'release_reserve_v1.json'):
        raw = repo.data(FIX+name)
        for id_ in raw['ids']:
            held[id_].append(repo.cite(FIX+name, json.dumps(id_, ensure_ascii=False)))
    reserve = repo.data(FIX+'release_reserve_v1.json')
    quick_held = {r['id']: repo.cite(FIX+'release_reserve_v1.json', json.dumps(r['id'])) for r in reserve['quick']}
    rows = []
    for game in PACK_GAMES:
        for r in pack[game]:
            rating = ratings.get(r['id'])
            if rating is None or rating.get('status') != r.get('status') or rating.get('game') != game:
                fail(f'missing/drifted ranking: {r["id"]}')
            rows.append({**r, 'game': game, 'held': held.get(r['id'], []),
                         'pilot_eligible': rating.get('pilot_eligible') is True,
                         'origin': FIX+'games_pack.json'})
    for name in ('derived_catalog_v38.json', 'quick_games_v92.json'):
        for r in repo.data(FIX+name)['boards']:
            if r['game'] not in ('intrusul', 'perechi'):
                fail('unexpected quick game')
            rows.append({**r, 'held': [quick_held[r['id']]] if r['id'] in quick_held else [], 'origin': FIX+name})
    ids = [r['id'] for r in rows]
    if len(set(ids)) != len(ids):
        fail('duplicate inventory IDs')
    return rows, held, quick_held


class Graph:
    def __init__(self, repo, raw=None):
        self.repo = repo
        if raw is None:
            raw = repo.data(FIX+'kg_sample.json')
        self.nodes = {n['id']: n for n in raw['kg_nodes']}
        self.adj = {id_: {} for id_ in self.nodes}
        self.rev = {id_: {} for id_ in self.nodes}
        for e in raw['kg_edges']:
            if e.get('is_distractor'):
                continue
            pairs = [(e['src_id'], e['dst_id'])]
            if e.get('bidirectional'):
                pairs.append((e['dst_id'], e['src_id']))
            for a, b in pairs:
                if a not in self.nodes or b not in self.nodes:
                    fail('edge has missing node')
                old = self.adj[a].get(b)
                if old is None or e['strength'] > old['strength']:
                    self.adj[a][b] = e
        for a in self.adj:
            self.adj[a] = dict(sorted(self.adj[a].items()))
            for b,e in self.adj[a].items():
                self.rev[b][a] = e
        self.edges = raw['kg_edges']

    def bfs(self, start, reverse=False, depth=None):
        links = self.rev if reverse else self.adj
        distances = {start: 0}
        q = collections.deque([start])
        while q:
            a = q.popleft()
            if depth is not None and distances[a] >= depth:
                continue
            for b in sorted(links[a]):
                if b not in distances:
                    distances[b] = distances[a]+1
                    q.append(b)
        return distances

    def edge_ref(self, e):
        return self.repo.cite(FIX+'kg_sample.json', json.dumps(e['id']))

    def undirected_strength(self, a, b):
        return max(self.adj[a].get(b, {}).get('strength', 0), self.adj[b].get(a, {}).get('strength', 0))


def run(main):
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError, RecursionError) as e:
        print(f'ERROR: {e}', file=sys.stderr)
        raise SystemExit(2)
