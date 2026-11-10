#!/usr/bin/env python3
"""Private Cald broker; mechanical evidence only, never content/FQ approval.

Root supplies an independently reviewed --config-sha256, not a self-generated
pin. Config schema cat-cald-operator-config-1 has exact keys: schema, controller,
common, provider, helper, normalization, source_inputs, cases. File bindings are
{path, sha256, bytes}; cases map names to {start, protocol, key, template} bindings.
source_inputs is the reviewed complete source/proof readset (retained historical
readset manifests may be bound by reference; this does not claim pruned bytes).
The embedded baseline pack tuple and private prospective pack remain distinct.

CLI: --scratch-root ROOT --config FILE --config-sha256 SHA --case NAME
     --case-dir PRIVATE_DIR init|open|guess|final [--response FILE --response-sha256 SHA] [--turn 1..8 for guess]
Opening is exactly protocol2. Adaptive is {challenge_id,guess,reason}. Final is
{challenge_id,target,dominant_sense,ambiguous}; target/sense must be nonblank and
ambiguity an actual bool. The final sense assertion remains for semantic review.
Only stdout is actor-safe: forward it, never the private files or logs.

Boundary: trusted Root/config/provider, untrusted actor JSON and stale/partial
files on a single-user Unix host. fcntl serializes writers, immutable receipts
are the only state, and atomic hard-link publication cannot replace evidence.
Exact retries recover finished output or append up to three technical attempts;
a damaged intent/receipt fails closed. Malformed envelopes are refused before a
submission; native rejected/unknown/repeated guesses each consume a submission.
No claims of same-user adversary isolation, signatures, content quality or HTTP
admission. No source mutation, new native algorithms, servers or network.
"""
import argparse
import contextlib
import datetime
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (fail, json_bytes, json_object, native_transform, read_regular,
                    scratch, set_scratch_root, sha256, write_bytes, write_json)

CONFIG = 'cat-cald-operator-config-1'
QUALIFICATION = 'Mechanical filter only; semantic/FQ approval pending.'
REQUEST_KEYS = 'challenge_id target category difficulty kg_sha256 pack_sha256 content_hash openers adaptive'.split()
PRIVATE_KEYS = 'challenge_id target warm_openers raw_incoming raw_reachable raw_responsive won direct_win reload_verified native_guesses_executed'.split()
HEX = re.compile(r'[0-9a-f]{64}')


def require(condition, message='invalid protocol evidence'):
    if not condition:
        fail(message)


def exact(value, keys):
    require(type(value) is dict and set(value) == set(keys), 'schema keys differ')


def text(value, limit=4096):
    require(type(value) is str and bool(value.strip()) and len(value.encode('utf-8')) <= limit,
            'invalid text')
    return value


def integer(value, low=0, high=1000000):
    require(type(value) is int and low <= value <= high, 'invalid integer')
    return value


def boolean(value):
    require(type(value) is bool, 'invalid boolean')
    return value


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def bound(binding):
    exact(binding, ('path', 'sha256', 'bytes'))
    require(type(binding['path']) is str and Path(binding['path']).is_absolute(), 'absolute input required')
    require(type(binding['sha256']) is str and HEX.fullmatch(binding['sha256']), 'invalid hash')
    integer(binding['bytes'], 0, 64 * 1024 * 1024)
    data = read_regular(binding['path'])
    require(len(data) == binding['bytes'] and sha256(data) == binding['sha256'], 'stale bound input')
    return data


def atomic_json(path, value):
    """One immutable commit marker, atomically visible and never overwritten."""
    data = json_bytes(value)
    pending = path.with_name(path.name + '.pending')
    if pending.exists():
        require(read_regular(pending) == data, 'incomplete or conflicting publication')
    else:
        write_bytes(pending, data)
    checksum = path.with_name(path.name + '.sha256')
    expected = (sha256(data) + '\n').encode()
    if checksum.exists():
        require(read_regular(checksum) == expected, 'publication hash differs')
    else:
        write_bytes(checksum, expected)
    os.link(pending, path)  # EEXIST is an integrity failure, including identical collisions.
    fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def native_bytes(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
    for literal, escaped in [('&', '\\u0026'), ('<', '\\u003c'), ('>', '\\u003e'),
                             ('\u2028', '\\u2028'), ('\u2029', '\\u2029')]:
        raw = raw.replace(literal, escaped)
    return (raw + '\n').encode()


def visible(value):
    value = text(value)
    require(not re.search(r'\bn_[A-Za-z0-9_]+\b|(?:^|\s)/(?:[^\s]+)|[A-Za-z]:\\|sha256:|[0-9a-f]{64}', value),
            'unsafe native display text')
    return value


def guess_view(value):
    require(type(value) is dict)
    return {'attempt_number': integer(value['attempt_number'], 1, 13),
            'closeness': integer(value['closeness'], 0, 100), 'label': visible(value['label']),
            'rank': integer(value['rank'], 1), 'temperature': temperature(value['temperature'])}


def temperature(value):
    require(value in ('Gasit', 'Fierbinte', 'Cald', 'Caldut', 'Rece', 'Foarte rece', 'Inghetat'))
    return value


def public_view(public):
    """Recursive explicit allowlist. Native errors/details/messages never escape."""
    result = {key: public[key] for key in ('challenge_id', 'board_category', 'difficulty')}
    result['feedback'] = []
    for row in public['feedback']:
        status = integer(row['status'], 100, 599)
        if status != 200:
            result['feedback'].append({'status': status, 'detail': 'Guess rejected.'})
            continue
        body = row['body']
        view = {'ok': boolean(body['ok']), 'won': boolean(body['won']),
                'attempts': integer(body['attempts'], 0, 13)}
        if view['ok']:
            view['guess'] = guess_view(body['guess'])
        else:
            require(view['won'] is False)
            view['message'] = 'Guess not recognized; submission counted.'
            if 'suggestions' in body:
                require(type(body['suggestions']) is list and len(body['suggestions']) <= 3)
                view['suggestions'] = [visible(label) for label in body['suggestions']]
            if 'needs_confirmation' in body:
                view['needs_confirmation'] = boolean(body['needs_confirmation'])
                view['resolved_label'] = visible(body['resolved_label'])
        require(type(body['guesses']) is list and len(body['guesses']) <= 13)
        view['guesses'] = [guess_view(guess) for guess in body['guesses']]
        for key in ('clue_available',):
            if key in body:
                view[key] = boolean(body[key])
        for key in ('clues_used', 'reachable_count', 'score'):
            if key in body:
                view[key] = integer(body[key])
        if 'feedback' in body:
            feedback = body['feedback']
            kind = feedback['kind']
            require(kind in ('first', 'found', 'new-best', 'warmer', 'colder', 'same', 'repeat'))
            view['feedback'] = {'kind': kind}
            if 'rank_delta' in feedback:
                view['feedback']['rank_delta'] = integer(feedback['rank_delta'], -1000000)
        if view['won']:
            target = body['target']
            view['target'] = {'label': visible(target['label']), 'description': visible(target['description'])}
        else:
            require('target' not in body, 'nonwinning target')
        result['feedback'].append({'status': 200, 'body': view})
    return result


class Broker:
    def __init__(self, config_path, expected_sha, case_name, case_dir):
        require(type(expected_sha) is str and HEX.fullmatch(expected_sha), 'expected config hash required')
        self.config_raw = read_regular(config_path)
        require(sha256(self.config_raw) == expected_sha, 'stale config')
        self.config_sha = expected_sha
        config = json_object(self.config_raw)
        exact(config, ('schema', 'controller', 'common', 'provider', 'helper', 'normalization', 'source_inputs', 'cases'))
        require(config['schema'] == CONFIG)
        require(Path(config['controller']['path']).resolve() == Path(__file__).resolve(), 'wrong controller path')
        require(Path(config['common']['path']).resolve() == Path(__file__).with_name('common.py').resolve(), 'wrong common path')
        for key in ('controller', 'common', 'provider', 'helper'):
            bound(config[key])
        require(type(config['source_inputs']) is list and bool(config['source_inputs']), 'source readset required')
        require(len({entry['path'] for entry in config['source_inputs']}) == len(config['source_inputs']))
        for binding in config['source_inputs']:
            bound(binding)
        rules = json_object(bound(config['normalization']))
        require(rules['unicode_version'] == '15.0.0' and type(rules['normalization_map']) is dict,
                'native Unicode15 normalization required')
        self.mapping = rules['normalization_map']
        require(all(type(k) is str and len(k) == 1 and type(v) is str for k, v in self.mapping.items()))
        require(type(config['cases']) is dict and case_name in config['cases'], 'unknown case')
        bindings = config['cases'][case_name]
        exact(bindings, ('start', 'protocol', 'key', 'template'))
        inputs = {name: json_object(bound(binding)) for name, binding in bindings.items()}
        self.start, self.protocol, self.key, self.template = (inputs[k] for k in ('start', 'protocol', 'key', 'template'))
        self.provider = config['provider']['path']
        self.config = config
        self.case_name = case_name
        self.directory = scratch(case_dir)
        self.validate_inputs()

    def validate_inputs(self):
        start, p, key, q = self.start, self.protocol, self.key, self.template
        exact(start, ('challenge_id', 'board_category', 'difficulty'))
        require(type(start['challenge_id']) is str and re.fullmatch(r'[0-9a-f]{24}', start['challenge_id']))
        text(start['board_category'], 80)
        require(start['difficulty'] in ('usor', 'normal', 'greu'))
        exact(p, 'schema task challenge_id board_category difficulty opening_guess_count adaptive_guess_limit max_total_submitted opening_response opening_warmth_requirement'.split())
        require(p['schema'] == 'cat-v4-c9-cald-public-protocol-1')
        require(all(p[k] == start[k] for k in start))
        for field, value in [('opening_guess_count', 5), ('adaptive_guess_limit', 8), ('max_total_submitted', 13)]:
            require(type(p[field]) is int and p[field] == value)
        exact(p['opening_warmth_requirement'], ('maximum_raw_distance', 'minimum_original_openers'))
        require(type(p['opening_warmth_requirement']['maximum_raw_distance']) is int and p['opening_warmth_requirement']['maximum_raw_distance'] == 2)
        require(type(p['opening_warmth_requirement']['minimum_original_openers']) is int and p['opening_warmth_requirement']['minimum_original_openers'] == 1)
        exact(p['opening_response'], ('schema', 'challenge_id', 'openers'))
        require(p['opening_response']['schema'] == 'cat-v2-contexto-opening-response-2' and p['opening_response']['challenge_id'] == start['challenge_id'])
        require(type(p['opening_response']['openers']) is list and all(type(w) is str for w in p['opening_response']['openers']))
        text(p['task'])
        exact(key, 'author_diagnostic_sealed author_id challenge_id embedded_source_bindings helper_sha256 native_binary_sha256 prospective_pack_sha256 qualification record record_sha256 review_binding schema source_commit'.split())
        require(key['schema'] == 'cat-v4-c9-private-identity-1' and key['author_diagnostic_sealed'] is True)
        exact(q, REQUEST_KEYS)
        require(type(q['openers']) is list and q['openers'] == [] and type(q['adaptive']) is list and q['adaptive'] == [])
        exact(key['record'], 'category difficulty id source status target'.split())
        exact(key['embedded_source_bindings'], ('kg_sha256', 'pack_sha256', 'content_hash'))
        require(key['challenge_id'] == q['challenge_id'] == start['challenge_id'])
        for field in ('target', 'category', 'difficulty'):
            require(type(q[field]) is str and q[field] == key['record'][field], 'private target binding differs')
        require(q['category'] == start['board_category'] and q['difficulty'] == start['difficulty'])
        require(all(q[k] == v for k, v in key['embedded_source_bindings'].items()), 'embedded source tuple differs')
        require(key['native_binary_sha256'] == self.config['provider']['sha256'] and key['helper_sha256'] == self.config['helper']['sha256'])
        require(type(key['prospective_pack_sha256']) is str and HEX.fullmatch(key['prospective_pack_sha256']))

    @contextlib.contextmanager
    def locked(self):
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        path = self.directory / '.writer'
        fd = os.open(path, os.O_CREAT | os.O_RDWR | getattr(os, 'O_NOFOLLOW', 0), 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            yield
        finally:
            os.close(fd)

    def history(self):
        events = sorted(p for p in self.directory.iterdir() if p.name != '.writer')
        receipts, previous = [], None
        for index, event in enumerate(events):
            require(event.is_dir() and event.name == f'{index:02}', 'event order differs')
            path = event / 'receipt.json'
            if not path.exists():
                require(index == len(events) - 1, 'partial event before successor')
                return receipts, event
            raw = read_regular(path)
            require(read_regular(event / 'receipt.json.sha256') == (sha256(raw) + '\n').encode(), 'receipt changed')
            receipt = json_object(raw)
            exact(receipt, ('config_sha256', 'case', 'previous', 'files', 'state', 'committed_at'))
            require(receipt['config_sha256'] == self.config_sha and receipt['case'] == self.case_name and receipt['previous'] == previous)
            require(type(receipt['files']) is dict)
            intent = json_object(read_regular(event / 'intent.json'))
            exact(intent, ('intent', 'actor_sha256', 'observed_at'))
            require(type(receipt['committed_at']) is str and type(intent['observed_at']) is str and
                    intent['observed_at'] <= receipt['committed_at'], 'event chronology differs')
            if receipts:
                require(receipts[-1]['committed_at'] <= intent['observed_at'], 'event order time differs')
            required = {'intent.json', 'actor.json', 'public.json'}
            if receipt['state']['action'] in ('open', 'guess'):
                required.update(('request.json', 'raw-public.json', 'raw-private.json'))
            require(set(receipt['files']) == required, 'incomplete receipt inventory')
            for rel, expected in receipt['files'].items():
                require(type(rel) is str and Path(rel).name == rel)
                require(sha256(read_regular(event / rel)) == expected, 'immutable event changed')
            receipt['_hash'] = sha256(raw)
            receipts.append(receipt)
            previous = sha256(raw)
        return receipts, None

    def commit(self, event, previous, files, state):
        receipt = {'config_sha256': self.config_sha, 'case': self.case_name, 'previous': previous,
                   'files': {name: sha256(read_regular(event / name)) for name in files},
                   'state': state, 'committed_at': now()}
        pending = event / 'receipt.json.pending'
        if pending.exists():
            retained = json_object(read_regular(pending))
            require({k: v for k, v in retained.items() if k != 'committed_at'} ==
                    {k: v for k, v in receipt.items() if k != 'committed_at'}, 'partial receipt differs')
            receipt = retained
        atomic_json(event / 'receipt.json', receipt)

    def actor(self, path, expected_sha, action):
        raw = read_regular(path)
        require(sha256(raw) == expected_sha, 'stale actor response')
        value = json_object(raw)
        keys = {'open': ('schema', 'challenge_id', 'openers'), 'guess': ('challenge_id', 'guess', 'reason'),
                'final': ('challenge_id', 'target', 'dominant_sense', 'ambiguous')}[action]
        exact(value, keys)
        require(value['challenge_id'] == self.start['challenge_id'])
        if action == 'open':
            require(value['schema'] == 'cat-v2-contexto-opening-response-2')
            require(type(value['openers']) is list and len(value['openers']) == 5)
            words = [text(w, 128) for w in value['openers']]
            normalized = [native_transform(w, self.mapping) for w in words]
            require(all(normalized) and len(set(normalized)) == 5, 'five distinct native-normalized openers required')
        elif action == 'guess':
            text(value['guess'], 128)
            require(bool(native_transform(value['guess'], self.mapping)))
            require(type(value['reason']) is str and len(value['reason'].encode()) <= 4096)
        else:
            text(value['target'], 128)
            text(value['dominant_sense'])
            boolean(value['ambiguous'])
        return raw, value

    def run(self, action, response=None, response_sha=None, turn=None):
        if action == 'guess':
            integer(turn, 1, 8)
        else:
            require(turn is None, 'turn only applies to adaptive guesses')
        raw, actor = (b'', None) if action == 'init' else self.actor(response, response_sha, action)
        with self.locked():
            history, partial = self.history()
            intent = {'action': action, 'actor_sha256': sha256(raw), 'config_sha256': self.config_sha,
                      'case': self.case_name, 'turn': turn, 'previous': history[-1]['_hash'] if history else None}
            # Turn number prevents a duplicate concurrent request consuming a new turn.
            for index, receipt in enumerate(history):
                old_dir = self.directory / f'{index:02}'
                old = json_object(read_regular(old_dir / 'intent.json'))['intent']
                if old['action'] == action and old['turn'] == turn:
                    require(old['actor_sha256'] == sha256(raw), 'committed action differs')
                    return json_object(read_regular(old_dir / 'public.json'))
            prior = history[-1]['state'] if history else None
            if action == 'init':
                require(not history, 'case already initialized')
            else:
                require(prior is not None and prior['action'] != 'final', 'case not active')
                if action == 'open':
                    require(prior['action'] == 'init', 'opening already committed')
                else:
                    require(prior['action'] in ('open', 'guess'), 'opening not committed')
                if action == 'guess':
                    require(turn == prior['adaptive'] + 1 and not prior['won'] and prior['adaptive'] < 8 and prior['submitted'] < 13, 'submission cap or native win')
            event = partial or self.directory / f'{len(history):02}'
            if partial:
                old = json_object(read_regular(event / 'intent.json'))
                require(old['intent'] == intent and read_regular(event / 'actor.json') == raw, 'partial event requires exact retry')
            else:
                event.mkdir(mode=0o700)
                write_bytes(event / 'actor.json', raw)
                atomic_json(event / 'intent.json', {'intent': intent, 'actor_sha256': sha256(raw), 'observed_at': now()})
            if action == 'init':
                public, state = self.start, {'action': 'init', 'submitted': 0, 'adaptive': 0, 'won': False}
                files = ['intent.json', 'actor.json', 'public.json']
            elif action == 'final':
                public = self.finalize(actor, prior)
                state = {**prior, 'action': 'final'}
                files = ['intent.json', 'actor.json', 'public.json']
            else:
                if action == 'open':
                    request = {**self.template, 'openers': actor['openers']}
                else:
                    request = json_object(read_regular(self.directory / f'{len(history)-1:02}' / 'request.json'))
                    request['adaptive'] = request['adaptive'] + [actor['guess']]
                if (event / 'request.json').exists():
                    require(read_regular(event / 'request.json') == json_bytes(request), 'request changed')
                else:
                    write_json(event / 'request.json', request)
                public, private = self.native(event, request, history)
                state = {'action': action, 'submitted': 5 + len(request['adaptive']), 'adaptive': len(request['adaptive']),
                         'won': private['won'], 'warm_openers': private['warm_openers'], 'direct_win': private['direct_win'],
                         'target_label': next((r['body']['target']['label'] for r in public['feedback'] if r.get('body', {}).get('won')), None)}
                public = public_view(public)
                files = ['intent.json', 'actor.json', 'request.json', 'public.json', 'raw-public.json', 'raw-private.json']
            if (event / 'public.json').exists():
                require(read_regular(event / 'public.json') == json_bytes(public), 'public publication differs')
            else:
                write_json(event / 'public.json', public)
            self.commit(event, intent['previous'], files, state)
            return public

    def native(self, event, request, history):
        # Retry verifies pins again in addition to the constructor before any execution.
        for attempt in range(3):
            run = event / f'native-{attempt}'
            fresh = not run.exists()
            if fresh:
                run.mkdir(mode=0o700)
                write_json(run / 'request.json', request)
                for name in ('controller', 'common', 'provider', 'helper', 'normalization'):
                    bound(self.config[name])
                for entry in self.config['source_inputs']:
                    bound(entry)
                for entry in self.config['cases'][self.case_name].values():
                    bound(entry)
                env = {key: value for key, value in os.environ.items() if key not in ('CAT_V4_CALD_PREVIEW_DIR',)}
                env['CAT_V4_CALD_PREVIEW_DIR'] = str(run)
                try:
                    result = subprocess.run([self.provider, '-test.run', '^TestV4NativeProspectiveCaldPreview$', '-test.v'],
                                            env=env, stdin=subprocess.DEVNULL, capture_output=True, timeout=180)
                    write_bytes(run / 'native.stdout', result.stdout)
                    write_bytes(run / 'native.stderr', result.stderr)
                    write_json(run / 'exit.json', {'code': result.returncode})
                except subprocess.SubprocessError:
                    write_json(run / 'exit.json', {'code': -1})
            require(read_regular(run / 'request.json') == json_bytes(request), 'native request changed')
            if not (run / 'exit.json').exists():
                # Process interruption with two complete outputs can still be validated.
                require((run / 'public.json').exists() and (run / 'private.json').exists(),
                        'interrupted native attempt; manual recovery required')
            elif json_object(read_regular(run / 'exit.json'))['code'] != 0:
                if fresh:
                    fail('native technical failure; exact retry required')
                continue
            raw_public, raw_private = read_regular(run / 'public.json'), read_regular(run / 'private.json')
            public, private = json_object(raw_public), json_object(raw_private)
            self.validate_native(public, private, request, raw_public, history)
            for name, data in [('raw-public.json', raw_public), ('raw-private.json', raw_private)]:
                if (event / name).exists():
                    require(read_regular(event / name) == data, 'raw native receipt differs')
                else:
                    write_bytes(event / name, data)
            return public, private
        fail('native technical attempts exhausted')

    def validate_native(self, public, private, request, raw, history):
        exact(public, ('challenge_id', 'board_category', 'difficulty', 'feedback'))
        require(all(public[k] == self.start[k] for k in self.start))
        exact(private, PRIVATE_KEYS)
        require(private['challenge_id'] == request['challenge_id'] and private['target'] == request['target'])
        for key in ('won', 'direct_win', 'reload_verified'):
            boolean(private[key])
        require(private['reload_verified'] is True)
        integer(private['warm_openers'], 0, 5)
        for key in ('raw_incoming', 'raw_reachable', 'raw_responsive'):
            integer(private[key])
        rows = public['feedback']
        require(type(rows) is list and 1 <= len(rows) <= 5 + len(request['adaptive']))
        require(integer(private['native_guesses_executed'], 1, 13) == len(rows))
        wins = []
        for index, row in enumerate(rows):
            require(type(row) is dict)
            if row['status'] != 200:
                continue
            body = row['body']
            boolean(body['won'])
            if not body['ok']:
                require(body['won'] is False)
                continue
            guess = body['guess']
            if body['won']:
                require(index == len(rows)-1 and body['target']['id'] == request['target'] == guess['id'] and guess['distance'] == 0,
                        'native exact target binding differs')
                wins.append(index)
        require(bool(wins) == private['won'] and private['direct_win'] == private['won'])
        require(private['won'] or len(rows) == 5 + len(request['adaptive']))
        if history[-1]['state']['action'] != 'init':
            previous_dir = self.directory / f'{len(history)-1:02}'
            old_raw = read_regular(previous_dir / 'raw-public.json')
            old = json_object(old_raw)
            prefix = {**public, 'feedback': rows[:len(old['feedback'])]}
            require(native_bytes(prefix) == old_raw, 'native feedback prefix changed')
            require(private['warm_openers'] == history[-1]['state']['warm_openers'])
            old_q = json_object(read_regular(previous_dir / 'request.json'))
            require(old_q['openers'] == request['openers'], 'original openers changed')
        # Validate allowlisted values before the raw output can be published.
        public_view(public)

    def finalize(self, actor, state):
        checks = {'native_won': state['won'], 'native_exact_target': state['direct_win'],
                  'original_warmth': state['warm_openers'] >= 1, 'final_unambiguous': actor['ambiguous'] is False,
                  'final_target_matches_native_label': native_transform(actor['target'], self.mapping) == native_transform(state['target_label'] or '', self.mapping),
                  'within_cap': state['submitted'] <= 13 and state['adaptive'] <= 8}
        return {'challenge_id': self.start['challenge_id'], 'mechanical_pass': all(checks.values()),
                'checks': checks, 'qualification': QUALIFICATION}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scratch-root', required=True)
    parser.add_argument('--config', required=True)
    parser.add_argument('--config-sha256', required=True)
    parser.add_argument('--case', required=True)
    parser.add_argument('--case-dir', required=True)
    parser.add_argument('action', choices=('init', 'open', 'guess', 'final'))
    parser.add_argument('--response')
    parser.add_argument('--response-sha256')
    parser.add_argument('--turn', type=int)
    args = parser.parse_args()
    try:
        set_scratch_root(args.scratch_root)
        broker = Broker(args.config, args.config_sha256, args.case, args.case_dir)
        value = broker.run(args.action, args.response, args.response_sha256, args.turn)
        print(json_bytes(value).decode(), end='')
    except Exception:
        # Never forward paths, raw native errors, keys or exception text.
        print('{"error":"Cald action refused; Root must inspect private evidence."}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
