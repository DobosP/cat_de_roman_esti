"""Pilot 3 pinned frequency admission, folding, binding and fail-closed regressions."""
from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import link_install as install

FIXTURE = 'burlan 96\nţară 20\nțară 5\nȚARĂ 1\ntara 14\nșoc 100\nsoc 1\ntata 7\ninvalid row no count\n'

class Pilot3FrequencyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='pilot3-frequency-',
                    dir=Path(os.environ.get('CAT_V5_TEST_SCRATCH', Path.cwd())))
        self.root = Path(self.temp.name)
        (self.root / 'frequency').mkdir()
        self.data = FIXTURE.encode()
        self.path = self.root / 'frequency/ro_full.txt'
        self.path.write_bytes(self.data)
        self.sha = install.digest(self.data)
        self.pins = patch.multiple(install, FULL_FREQUENCY_SHA256=self.sha,
                                  FULL_FREQUENCY_BYTES=len(self.data))
        self.pins.start()
        self.counts = install.frequency_lookup.load(self.path, self.sha)

    def tearDown(self):
        self.pins.stop()
        self.temp.cleanup()

    def source(self, label):
        return {'list': {'path': 'frequency/ro_full.txt', 'sha256': self.sha},
                'row': self.counts.lookup(label)}

    def verify(self, source, label='Burlan', campaign='v5-pilot-3'):
        return install.verify_frequency(self.root, source, label, campaign, {})

    def test_pinned_lookup_reuses_frequency_parser_and_sums_cedilla_comma_case(self):
        for label, exact, variants in [('Burlan', 96, 1), ('Țară', 26, 3), ('ŢARĂ', 26, 3)]:
            with self.subTest(label=label):
                row = self.verify(self.source(label), label)
                self.assertEqual((row['exact'], row['variants']), (exact, variants))
        self.assertEqual(self.counts.skipped, 1)
        self.assertEqual(install.MAX_INPUT, 1024 * 1024)

    def test_minority_flag_is_bound_and_cannot_be_hidden(self):
        source = self.source('soc')
        self.assertIs(source['row']['minority_spelling'], True)
        self.assertIs(self.verify(source, 'soc')['minority_spelling'], True)
        source['row']['minority_spelling'] = False
        with self.assertRaisesRegex(ValueError, 'Folded frequency result differs'):
            self.verify(source, 'soc')

    def test_rows_fail_closed_on_changed_missing_or_type_changed_fields(self):
        good = self.source('Burlan')
        changes = [('exact', 95), ('exact', True), ('exact', 96.0), ('label', 'burlan'),
                   ('variants', 2), ('undiacritised', 0), ('status', 'absent'),
                   ('dominant_spelling', None), ('minority_spelling', 0)]
        for key, value in changes:
            with self.subTest(key=key, value=value):
                bad = deepcopy(good)
                bad['row'][key] = value
                with self.assertRaisesRegex(ValueError, 'Folded frequency result differs'):
                    self.verify(bad)
        for key in good['row']:
            with self.subTest(missing=key):
                bad = deepcopy(good)
                del bad['row'][key]
                with self.assertRaisesRegex(ValueError, 'Folded frequency result differs'):
                    self.verify(bad)

    def test_nonpositive_fallback_absent_multiword_cannot_supply_exact(self):
        for label in ('tată', 'missing', 'cal de mare'):
            with self.subTest(label=label):
                with self.assertRaisesRegex(ValueError, 'Positive exact word frequency required'):
                    self.verify(self.source(label), label)

    def test_full_proof_requires_exact_path_pin_and_shape(self):
        for mutation in ('path', 'sha', 'extra', 'legacy'):
            with self.subTest(mutation=mutation):
                bad = self.source('Burlan')
                if mutation == 'path': bad['list']['path'] = 'legacy-cache/ro_full.txt'
                elif mutation == 'sha': bad['list']['sha256'] = '0' * 64
                elif mutation == 'extra': bad['list']['receipt'] = {}
                else: bad = {'receipt': {}, 'body_sha256': self.sha, 'word': 'burlan', 'count': 96}
                with self.assertRaisesRegex(ValueError, 'exact ADR-0235 pinned full frequency list'):
                    self.verify(bad)

    def test_missing_changed_truncated_oversized_and_invalid_utf8_bytes_fail_closed(self):
        source = self.source('Burlan')
        self.path.unlink()
        with self.assertRaisesRegex(ValueError, 'Missing or nonregular'):
            self.verify(source)
        for data in (self.data[:-1], b'x' + self.data[1:], self.data + b'x'):
            with self.subTest(size=len(data)):
                self.path.write_bytes(data)
                with self.assertRaises(ValueError):
                    self.verify(source)
        invalid = b'\xff 9\n'
        self.path.write_bytes(invalid)
        with patch.multiple(install, FULL_FREQUENCY_SHA256=install.digest(invalid),
                            FULL_FREQUENCY_BYTES=len(invalid)):
            source['list']['sha256'] = install.digest(invalid)
            with self.assertRaises(UnicodeDecodeError):
                self.verify(source)

    def test_list_and_parent_symlinks_are_refused(self):
        source = self.source('Burlan')
        real = self.root / 'real.txt'
        self.path.rename(real)
        self.path.symlink_to(real)
        with self.assertRaisesRegex(ValueError, 'Symlink artifact refused'):
            self.verify(source)
        self.path.unlink()
        (self.root / 'frequency').rename(self.root / 'actual-frequency')
        (self.root / 'frequency').symlink_to(self.root / 'actual-frequency', target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'Symlink artifact refused'):
            self.verify(source)

    def test_unsupported_campaign_has_no_legacy_fallback(self):
        with self.assertRaisesRegex(ValueError, 'Unsupported word frequency campaign'):
            self.verify({}, campaign='v5-pilot-4')

    def test_campaign_contract_admits_only_documented_versions_exact_base_and_full_pin(self):
        base = 'a' * 40
        for campaign in ('v5-pilot-2', 'v5-pilot-3'):
            contract = {'campaign': campaign, 'base_sha': base}
            if campaign.endswith('3'): contract['frequency'] = deepcopy(install.FULL_FREQUENCY_CONTRACT)
            self.assertEqual(install.campaign_contract(contract, base), campaign)
        for campaign in ('v5-pilot-1', 'v5-pilot-4', None):
            with self.assertRaisesRegex(ValueError, 'Baseline differs'):
                install.campaign_contract({'campaign': campaign, 'base_sha': base}, base)
        with self.assertRaisesRegex(ValueError, 'Baseline differs'):
            install.campaign_contract({'campaign': 'v5-pilot-2', 'base_sha': 'b'*40}, base)
        good = {'campaign': 'v5-pilot-3', 'base_sha': base,
                'frequency': deepcopy(install.FULL_FREQUENCY_CONTRACT)}
        for key in ('list', 'sha256', 'tool'):
            bad = deepcopy(good)
            bad['frequency'][key] = 'wrong'
            with self.assertRaisesRegex(ValueError, 'frequency contract differs'):
                install.campaign_contract(bad, base)
        for frequency in ({}, {**good['frequency'], 'extra': 1}, None):
            with self.assertRaisesRegex(ValueError, 'frequency contract differs'):
                install.campaign_contract({**good, 'frequency': frequency}, base)

    def test_historical_receipt_header_hash_and_path_checks_remain(self):
        body = b'miner 503\n'
        sha = install.digest(body)
        filename = install.digest(install.FREQUENCY_URL.encode('ascii')) + '.receipt.json'
        (self.root/'legacy-cache').mkdir()
        (self.root/'legacy-cache'/f'{sha}.body').write_bytes(body)
        def proof(headers=None, **changes):
            receipt = {'url': install.FREQUENCY_URL, 'status': 200, 'sha256': sha,
                       'bytes': len(body), 'headers': headers or {}}
            receipt.update(changes)
            raw = install.canonical(receipt)
            (self.root/'legacy-cache'/filename).write_bytes(raw)
            return {'receipt': {'path': 'legacy-cache/'+filename, 'sha256': install.digest(raw)},
                    'body_sha256': sha, 'word': 'miner', 'count': 503}
        self.assertEqual(self.verify(proof(), 'Miner', 'v5-pilot-2')['count'], 503)
        for headers in ({'content-signal':'ai-input=no'}, {'content-signal-present':'true'},
                        {'x-robots-tag':'noai'}, {'location':'/other'}, {'content-range':'bytes 0-2/9'},
                        {'content-encoding':'gzip'}):
            with self.subTest(headers=headers):
                with self.assertRaisesRegex(ValueError, 'ineligible source header'):
                    self.verify(proof(headers), 'Miner', 'v5-pilot-2')
        for changes in ({'status':206}, {'status':True}, {'bytes':99}, {'body_problem':'truncated'},
                        {'url':install.FREQUENCY_URL.replace('ro_50k', 'ro_full')}):
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):
                    self.verify(proof(**changes), 'Miner', 'v5-pilot-2')
        bad = proof()
        bad['receipt']['sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'receipt hash differs'):
            self.verify(bad, 'Miner', 'v5-pilot-2')
        bad = proof()
        bad['receipt']['path'] = '../'+bad['receipt']['path']
        with self.assertRaisesRegex(ValueError, 'outside the permitted cache'):
            self.verify(bad, 'Miner', 'v5-pilot-2')
        (self.root/'legacy-cache'/f'{sha}.body').write_bytes(b'x'+body[1:])
        with self.assertRaisesRegex(ValueError, 'body hash differs'):
            self.verify(proof(), 'Miner', 'v5-pilot-2')

if __name__ == '__main__':
    unittest.main()
