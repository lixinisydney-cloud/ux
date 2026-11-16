"""Validate the shipped Codex result, distinct from synthetic API fixtures."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from classify_notes import ClassificationError, load_dataset, validate_envelope


class PrecomputedData(unittest.TestCase):
    def setUp(self):
        self.notes, self.groups = load_dataset(ROOT / 'data/notes.json', ROOT / 'data/groups.json')
        self.result = json.loads((ROOT / 'data/classifications.precomputed.json').read_text())

    def test_shipped_counts_and_semantic_cases(self):
        validate_envelope(self.result, self.notes, self.groups, expected_mode='precomputed')
        rows = {r['noteId']: r for r in self.result['assignments']}
        initial = [rows[n['id']] for n in self.notes if n['availability'] == 'initial']
        self.assertEqual(len(initial), 35)
        self.assertEqual(sum(bool(r['memberships']) for r in initial), 34)
        self.assertEqual([r['noteId'] for r in initial if not r['memberships']], ['ambiguous-1'])
        self.assertEqual({r['noteId'] for r in initial if len(r['memberships']) == 2},
                         {'d7', 'c5', 'case-b', 'cross-1'})
        expected = {'case-a': {'design'}, 'case-b': {'career', 'design'},
                    'cross-1': {'travel', 'food'}, 'h2': {'home'},
                    'new1': {'home'}, 'new2': {'design'}, 'new3': {'travel'}}
        for note, groups in expected.items():
            self.assertEqual({m['groupId'] for m in rows[note]['memberships']}, groups)

    def test_invalid_and_misattributed_results_rejected(self):
        mutations = [('provider', 'openai'), ('model', 'gpt-4.1-mini'),
                     ('datasetHash', '0' * 64), ('notesCount', 35), ('mode', 'real')]
        for key, value in mutations:
            with self.subTest(key=key):
                invalid = copy.deepcopy(self.result)
                invalid[key] = value
                with self.assertRaises(ClassificationError):
                    validate_envelope(invalid, self.notes, self.groups, expected_mode='precomputed')

    def test_bootstrap_matches_authoritative_json(self):
        script = (ROOT / 'data/offline-bundle.js').read_text()
        bundle = json.loads(script.split('globalThis.RE_BOOTSTRAP=', 1)[1].rstrip(';\n'))
        self.assertEqual(bundle['precomputed'], self.result)


if __name__ == '__main__':
    unittest.main(verbosity=2)
