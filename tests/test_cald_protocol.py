"""Synthetic operator controls only. These are not blind critic transcripts."""
import concurrent.futures
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock

TOOL = Path(__file__).resolve().parents[1] / 'scripts/miner/cald_protocol.py'
spec = importlib.util.spec_from_file_location('cald_protocol', TOOL)
cald = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cald)


def save(path, value):
    path.write_bytes(cald.json_bytes(value))
    return path


def binding(path):
    raw = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


class CaldProtocolTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        cald.set_scratch_root(self.root)
        self.case = self.root / 'case'
        self.challenge = 'a' * 24
        self.words = ['unu', 'doi', 'trei', 'patru', 'cinci']
        self.calls = []
        self.failures = 0
        self.warm = 1
        self.prefix_change = False
        self.sentinel = 'n_PRIVATE_SENTINEL'
        self.provider_file = self.root / 'provider'
        self.provider_file.write_bytes(b'synthetic provider; subprocess always mocked')
        self.helper = self.root / 'helper'
        self.helper.write_bytes(b'synthetic helper')
        self.source = self.root / 'source'
        self.source.write_bytes(b'synthetic frozen source proof')
        self.rules = save(self.root / 'rules.json', {'unicode_version': '15.0.0',
                            'normalization_map': {chr(i): chr(i).lower() for i in range(65, 91)}})
        start = {'challenge_id': self.challenge, 'board_category': 'arta_cultura', 'difficulty': 'greu'}
        self.start_path = save(self.root / 'start.json', start)
        protocol = {**start, 'schema': 'cat-v4-c9-cald-public-protocol-1', 'task': 'Synthetic test protocol.',
                    'opening_guess_count': 5, 'adaptive_guess_limit': 8, 'max_total_submitted': 13,
                    'opening_response': {'schema': 'cat-v2-contexto-opening-response-2',
                                         'challenge_id': self.challenge, 'openers': ['five text guesses']},
                    'opening_warmth_requirement': {'maximum_raw_distance': 2, 'minimum_original_openers': 1}}
        self.protocol_path = save(self.root / 'protocol.json', protocol)
        sources = {'kg_sha256': 'b'*64, 'pack_sha256': 'c'*64, 'content_hash': 'sha256:' + 'd'*64}
        self.template = {'challenge_id': self.challenge, 'target': self.sentinel,
                         'category': start['board_category'], 'difficulty': start['difficulty'],
                         **sources, 'openers': [], 'adaptive': []}
        self.template_path = save(self.root / 'template.json', self.template)
        self.key = {'schema': 'cat-v4-c9-private-identity-1', 'author_diagnostic_sealed': True,
                    'author_id': 'synthetic', 'challenge_id': self.challenge, 'embedded_source_bindings': sources,
                    'helper_sha256': binding(self.helper)['sha256'], 'native_binary_sha256': binding(self.provider_file)['sha256'],
                    'prospective_pack_sha256': 'e'*64, 'qualification': 'Synthetic fixture only.',
                    'record': {'target': self.sentinel, 'category': start['board_category'], 'difficulty': start['difficulty'],
                               'id': 'synthetic', 'source': 'user', 'status': 'pending'},
                    'record_sha256': 'f'*64, 'review_binding': 'sha256:'+'f'*64, 'source_commit': '1'*40}
        self.key_path = save(self.root / 'key.json', self.key)
        self.config = {'schema': cald.CONFIG, 'controller': binding(TOOL), 'common': binding(TOOL.with_name('common.py')),
                       'provider': binding(self.provider_file), 'helper': binding(self.helper), 'normalization': binding(self.rules),
                       'source_inputs': [binding(self.source)], 'cases': {'synthetic': {
                           'start': binding(self.start_path), 'protocol': binding(self.protocol_path),
                           'key': binding(self.key_path), 'template': binding(self.template_path)}}}
        self.config_path = self.root / 'config.json'
        self.refresh()
        self.patch = mock.patch.object(cald.subprocess, 'run', self.provider)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.actor_index = 0

    def refresh(self):
        save(self.config_path, self.config)
        self.pin = binding(self.config_path)['sha256']

    def broker(self):
        return cald.Broker(self.config_path, self.pin, 'synthetic', self.case)

    def actor(self, action='open', **changes):
        value = {'challenge_id': self.challenge}
        if action == 'open':
            value.update(schema='cat-v2-contexto-opening-response-2', openers=self.words)
        elif action == 'guess':
            value.update(guess='adaptive', reason='Synthetic test action.')
        else:
            value.update(target='Țintă', dominant_sense='Synthetic dominant sense.', ambiguous=False)
        value.update(changes)
        self.actor_index += 1
        path = save(self.root / f'actor-{self.actor_index}.json', value)
        return path, binding(path)['sha256']

    def call(self, action, actor=None, turn=None, **changes):
        if action == 'init':
            return self.broker().run('init')
        path, pin = actor or self.actor(action, **changes)
        return self.broker().run(action, path, pin, turn)

    def opened(self, **changes):
        self.call('init')
        return self.call('open', **changes)

    def provider(self, argv, env, **kwargs):
        self.assertEqual(argv, [str(self.provider_file), '-test.run', '^TestV4NativeProspectiveCaldPreview$', '-test.v'])
        run = Path(env['CAT_V4_CALD_PREVIEW_DIR'])
        request = cald.json_object((run / 'request.json').read_bytes())
        self.calls.append(request)
        if self.failures:
            self.failures -= 1
            return types.SimpleNamespace(returncode=1, stdout=self.sentinel.encode(), stderr=b'/private/source/path')
        rows, guesses, won = [], [], False
        for index, word in enumerate(request['openers'] + request['adaptive']):
            if word == 'reject':
                rows.append({'status': 400, 'detail': self.sentinel + ' /private/key/path'})
                continue
            if word == 'unknown':
                rows.append({'status': 200, 'body': {'ok': False, 'won': False, 'attempts': len(guesses),
                                                    'message': self.sentinel, 'guesses': list(guesses), 'suggestions': ['Cuvânt']}})
                continue
            won = word == 'win'
            guess = {'attempt_number': len(guesses)+1, 'closeness': 100 if won else 50, 'distance': 0 if won else 4,
                     'id': self.sentinel if won else 'n_SYNTHETIC_' + str(index),
                     'label': 'Țintă' if won else word, 'rank': 1 if won else 100, 'temperature': 'Gasit' if won else 'Rece'}
            guesses.append(guess)
            body = {'ok': True, 'won': won, 'attempts': len(guesses), 'guess': guess, 'guesses': list(guesses),
                    'feedback': {'kind': 'found' if won else 'first', 'message': self.sentinel},
                    'source_path': '/private/source', 'resolved_token': self.sentinel}
            if won:
                body['target'] = {'id': request['target'], 'label': 'Țintă', 'description': 'Synthetic target sense.'}
            rows.append({'status': 200, 'body': body})
            if won:
                break
        if self.prefix_change and request['adaptive']:
            rows[0]['body']['guess']['rank'] += 1
        public = {**{k: request[k] for k in ('challenge_id', 'difficulty')},
                  'board_category': request['category'], 'feedback': rows}
        private = {'challenge_id': request['challenge_id'], 'target': request['target'], 'warm_openers': self.warm,
                   'raw_incoming': 5, 'raw_reachable': 120, 'raw_responsive': 40,
                   'won': won, 'direct_win': won, 'reload_verified': True, 'native_guesses_executed': len(rows)}
        (run / 'public.json').write_bytes(cald.native_bytes(public))
        (run / 'private.json').write_bytes(cald.native_bytes(private))
        return types.SimpleNamespace(returncode=0, stdout=b'synthetic', stderr=b'')

    def test_stale_config_actor_and_every_input_refuse_before_native(self):
        with self.assertRaises(ValueError):
            cald.Broker(self.config_path, '0'*64, 'synthetic', self.case)
        self.call('init')
        path, pin = self.actor()
        with self.assertRaises(ValueError):
            self.broker().run('open', path, '0'*64)
        for path in (self.start_path, self.protocol_path, self.key_path, self.template_path,
                     self.provider_file, self.helper, self.source, self.rules):
            original = path.read_bytes()
            path.write_bytes(original + b' ')
            with self.subTest(path=path.name), self.assertRaises(ValueError):
                self.call('open')
            path.write_bytes(original)
        self.assertEqual(self.calls, [])

    def test_same_category_target_drift_even_with_fresh_template_pin(self):
        self.template['target'] = 'n_OTHER_TARGET'
        save(self.template_path, self.template)
        self.config['cases']['synthetic']['template'] = binding(self.template_path)
        self.refresh()
        with self.assertRaises(ValueError):
            self.call('init')
        self.assertEqual(self.calls, [])

    def test_strict_duplicate_keys_exact_schema_and_types(self):
        self.call('init')
        path, pin = self.actor()
        raw = path.read_bytes().replace(b'"schema":', b'"schema":"ignored","schema":')
        path.write_bytes(raw)
        with self.assertRaises(ValueError):
            self.call('open', (path, binding(path)['sha256']))
        for changes in ({'ambiguous': False}, {'openers': 'abcde'}, {'openers': self.words[:4]},
                        {'openers': ['A', 'a', 'b', 'c', 'd']}, {'openers': [True, 'a', 'b', 'c', 'd']}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.call('open', **changes)
        self.assertEqual(self.calls, [])

    def test_public_recursive_allowlist_and_error_paths(self):
        result = self.opened(openers=['reject', 'unknown', 'trei', 'patru', 'cinci'])
        serialized = json.dumps(result)
        for forbidden in (self.sentinel, '/private', 'distance', 'resolved_token', 'source_path', 'n_SYNTHETIC'):
            self.assertNotIn(forbidden, serialized)
        self.assertEqual(result['feedback'][0]['detail'], 'Guess rejected.')
        self.assertEqual(result['feedback'][1]['body']['suggestions'], ['Cuvânt'])
        self.assertIn(self.sentinel.encode(), (self.case / '01/raw-public.json').read_bytes())
        with self.assertRaises(ValueError):
            cald.visible(self.sentinel)

    def test_unknown_and_repeated_submissions_count_to_full_cap(self):
        self.opened(openers=['unknown', 'reject', 'trei', 'patru', 'cinci'])
        for turn in range(1, 9):
            self.call('guess', turn=turn, guess='unknown' if turn % 2 else 'trei')
        state = cald.json_object((self.case / '09/receipt.json').read_bytes())['state']
        self.assertEqual((state['submitted'], state['adaptive']), (13, 8))
        with self.assertRaises(ValueError):
            self.call('guess', turn=9)
        self.assertEqual(len(self.calls), 9)
        result = self.call('final')
        self.assertFalse(result['mechanical_pass'])

    def test_early_win_keeps_five_committed_and_stops_adaptive(self):
        self.opened(openers=['win', 'doi', 'trei', 'patru', 'cinci'])
        receipt = cald.json_object((self.case / '01/receipt.json').read_bytes())
        self.assertEqual(receipt['state']['submitted'], 5)
        self.assertEqual(len(cald.json_object((self.case / '01/raw-public.json').read_bytes())['feedback']), 1)
        with self.assertRaises(ValueError):
            self.call('guess', turn=1)
        self.assertTrue(self.call('final')['mechanical_pass'])

    def test_final_requires_warmth_false_boolean_and_nonblank_sense(self):
        self.warm = 0
        self.opened()
        self.call('guess', turn=1, guess='win')
        for bad in (0, 1, 'false', None, [], {}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.call('final', ambiguous=bad)
        with self.assertRaises(ValueError):
            self.call('final', dominant_sense=' ')
        result = self.call('final', ambiguous=False)
        self.assertFalse(result['mechanical_pass'])
        self.assertFalse(result['checks']['original_warmth'])
        self.assertIn('semantic/FQ approval pending', result['qualification'])

    def test_honest_ambiguity_true_is_retained_as_mechanical_failure(self):
        self.opened()
        self.call('guess', turn=1, guess='win')
        result = self.call('final', ambiguous=True)
        self.assertFalse(result['mechanical_pass'])
        self.assertFalse(result['checks']['final_unambiguous'])
        self.assertTrue((self.case / '03/actor.json').exists())

    def test_openers_rewrite_and_native_prefix_changes_refuse(self):
        self.opened()
        path = self.case / '01/actor.json'
        path.write_bytes(path.read_bytes().replace(b'unu', b'NEW'))
        with self.assertRaises(ValueError):
            self.call('guess', turn=1)
        self.assertEqual(len(self.calls), 1)

    def test_prefix_drift_refuses_publication(self):
        self.opened()
        self.prefix_change = True
        with self.assertRaises(ValueError):
            self.call('guess', turn=1)
        self.assertFalse((self.case / '02/public.json').exists())
        self.assertFalse((self.case / '02/receipt.json').exists())

    def test_immutable_receipt_collision(self):
        self.opened()
        receipt = self.case / '01/receipt.json'
        before = receipt.read_bytes()
        with self.assertRaises(FileExistsError):
            cald.atomic_json(receipt, cald.json_object(before))
        self.assertEqual(receipt.read_bytes(), before)
        receipt.write_bytes(before + b' ')
        with self.assertRaises(ValueError):
            self.call('guess', turn=1)

    def test_identical_retry_is_idempotent_conflicting_retry_refused(self):
        self.call('init')
        actor = self.actor()
        first = self.call('open', actor)
        self.assertEqual(self.call('open', actor), first)
        self.assertEqual(len(self.calls), 1)
        with self.assertRaises(ValueError):
            self.call('open', openers=['changed', *self.words[1:]])
        guess = self.actor('guess')
        result = self.call('guess', guess, turn=1)
        self.assertEqual(self.call('guess', guess, turn=1), result)
        self.assertEqual(len(self.calls), 2)

    def test_technical_failure_exact_retry_recovers_without_reroll(self):
        self.call('init')
        actor = self.actor()
        self.failures = 1
        with self.assertRaises(ValueError):
            self.call('open', actor)
        self.assertFalse((self.case / '01/receipt.json').exists())
        with self.assertRaises(ValueError):
            self.call('open', openers=['changed', *self.words[1:]])
        result = self.call('open', actor)
        self.assertEqual(len(self.calls), 2)
        self.assertTrue((self.case / '01/native-0/native.stderr').exists())
        self.assertTrue((self.case / '01/receipt.json').exists())
        self.assertEqual(self.call('open', actor), result)

    def test_partial_receipt_publication_recovers_finished_native_output(self):
        self.call('init')
        actor = self.actor()
        original = cald.atomic_json
        def fail_commit(path, value):
            if path.name == 'receipt.json':
                cald.write_json(path.with_name('receipt.json.pending'), value)
                raise OSError('synthetic crash before atomic link')
            return original(path, value)
        with mock.patch.object(cald, 'atomic_json', fail_commit), self.assertRaises(OSError):
            self.call('open', actor)
        self.assertEqual(len(self.calls), 1)
        self.call('open', actor)
        self.assertEqual(len(self.calls), 1)

    def test_damaged_partial_intent_requires_manual_recovery(self):
        self.call('init')
        (self.case / '01').mkdir()
        with self.assertRaises(OSError):
            self.call('open')
        self.assertEqual(self.calls, [])

    def test_concurrent_same_turn_has_one_immutable_submission(self):
        self.opened()
        actors = [self.actor('guess', guess=word) for word in ('alpha', 'beta')]
        def run(actor):
            try:
                self.call('guess', actor, turn=1)
                return 'committed'
            except ValueError:
                return 'refused'
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            self.assertCountEqual(list(pool.map(run, actors)), ['committed', 'refused'])
        self.assertEqual(len(self.calls), 2)
        self.assertFalse((self.case / '03').exists())

    def test_native_duplicate_json_and_exact_target_binding_refuse(self):
        self.call('init')
        actor = self.actor()
        provider = self.provider
        def duplicate(argv, env, **kwargs):
            result = provider(argv, env, **kwargs)
            p = Path(env['CAT_V4_CALD_PREVIEW_DIR']) / 'private.json'
            p.write_bytes(p.read_bytes().replace(b'"won":', b'"won":true,"won":'))
            return result
        with mock.patch.object(cald.subprocess, 'run', duplicate), self.assertRaises(ValueError):
            self.call('open', actor)
        self.assertFalse((self.case / '01/receipt.json').exists())

    def test_winning_native_wrong_private_target_refuses(self):
        self.call('init')
        provider = self.provider
        def wrong_target(argv, env, **kwargs):
            result = provider(argv, env, **kwargs)
            p = Path(env['CAT_V4_CALD_PREVIEW_DIR']) / 'private.json'
            value = cald.json_object(p.read_bytes())
            value['target'] = 'n_OTHER'
            p.write_bytes(cald.native_bytes(value))
            return result
        with mock.patch.object(cald.subprocess, 'run', wrong_target), self.assertRaises(ValueError):
            self.call('open', openers=['win', *self.words[1:]])
        self.assertFalse((self.case / '01/public.json').exists())

    def test_final_wrong_target_has_failed_comparator_and_retained_response(self):
        self.opened()
        self.call('guess', turn=1, guess='win')
        result = self.call('final', target='Wrong target')
        self.assertFalse(result['mechanical_pass'])
        self.assertFalse(result['checks']['final_target_matches_native_label'])
        self.assertTrue((self.case / '03/actor.json').exists())

    def test_native_attempt_without_completion_fails_closed(self):
        self.call('init')
        actor = self.actor()
        def interruption(argv, env, **kwargs):
            raise OSError('synthetic interruption')
        with mock.patch.object(cald.subprocess, 'run', interruption), self.assertRaises(OSError):
            self.call('open', actor)
        with self.assertRaises(ValueError):
            self.call('open', actor)
        self.assertFalse((self.case / '01/receipt.json').exists())
        self.assertEqual(self.calls, [])

    def test_three_technical_attempts_are_bounded(self):
        self.call('init')
        actor = self.actor()
        self.failures = 5
        for _ in range(4):
            with self.assertRaises(ValueError):
                self.call('open', actor)
        self.assertEqual(len(self.calls), 3)

    def test_protocol_boolean_limit_and_unknown_fields_refuse_even_with_new_pin(self):
        p = cald.json_object(self.protocol_path.read_bytes())
        p['adaptive_guess_limit'] = True
        save(self.protocol_path, p)
        self.config['cases']['synthetic']['protocol'] = binding(self.protocol_path)
        self.refresh()
        with self.assertRaises(ValueError):
            self.call('init')
        p['adaptive_guess_limit'] = 8
        p['extra'] = 'unknown field'
        save(self.protocol_path, p)
        self.config['cases']['synthetic']['protocol'] = binding(self.protocol_path)
        self.refresh()
        with self.assertRaises(ValueError):
            self.call('init')

    def test_pinned_native_normalization_not_python_casefold_is_used(self):
        save(self.rules, {'unicode_version': '15.0.0', 'normalization_map': {'#': 'a'}})
        self.config['normalization'] = binding(self.rules)
        self.refresh()
        self.call('init')
        with self.assertRaises(ValueError):
            self.call('open', openers=['#', 'a', 'b', 'c', 'd'])
        self.assertEqual(self.calls, [])

    def test_receipt_chronology_is_enforced(self):
        self.opened()
        path = self.case / '01/receipt.json'
        value = cald.json_object(path.read_bytes())
        intent = cald.json_object((self.case / '01/intent.json').read_bytes())
        self.assertLessEqual(intent['observed_at'], value['committed_at'])
        value['committed_at'] = '1900-01-01T00:00:00+00:00'
        path.write_bytes(cald.json_bytes(value))
        (path.parent / 'receipt.json.sha256').write_text(hashlib.sha256(path.read_bytes()).hexdigest() + '\n')
        with self.assertRaises(ValueError):
            self.call('guess', turn=1)

    def test_optimized_python_still_refuses_and_errors_hide_paths(self):
        self.patch.stop()
        try:
            result = subprocess.run([sys.executable, '-I', '-B', '-O', str(TOOL), '--scratch-root', str(self.root),
                                     '--config', str(self.config_path), '--config-sha256', '0'*64,
                                     '--case', 'synthetic', '--case-dir', str(self.case), 'init'],
                                    capture_output=True, timeout=15)
        finally:
            self.patch.start()
        self.assertEqual(result.returncode, 2)
        self.assertNotIn(str(self.root).encode(), result.stderr)
        self.assertNotIn(self.sentinel.encode(), result.stderr)
        self.assertEqual(result.stdout, b'')


if __name__ == '__main__':
    unittest.main()
