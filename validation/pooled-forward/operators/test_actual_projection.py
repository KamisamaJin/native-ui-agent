import copy
import hashlib
import unittest

import actual_projection as module


class Reader:
    def __init__(self): self.files = {'/current/A.swift': b'line one\nline two\n', '/current/B.swift': b'other\n'}
    def read_bytes(self, path): return self.files[path]


def fixture():
    reader = Reader(); hashes = {path: hashlib.sha256(raw).hexdigest() for path, raw in reader.files.items()}
    claims = [{'id': name, 'method': 'source', 'owner': 'component', 'supported': True, 'files': {path: hashes[path]}}
              for name, path in [('a', '/current/A.swift'), ('b', '/current/B.swift')]]
    inventory = {'source/A.swift': {'sha256': hashes['/current/A.swift'], 'kind': 'production-source'},
                 'source/B.swift': {'sha256': hashes['/current/B.swift'], 'kind': 'production-source'}}
    aliases = {'source/A.swift': '/current/A.swift', 'source/B.swift': '/current/B.swift'}
    rows = [{'id': 'a', 'observed': True, 'reason': 'Inspected actual implementation', 'citations': [{'path': 'source/A.swift', 'line': 2}]},
            {'id': 'b', 'observed': False, 'reason': 'Concrete implementation contradiction', 'citations': [{'path': 'source/B.swift', 'line': 1}]}]
    return reader, claims, inventory, aliases, rows


class ProjectionControls(unittest.TestCase):
    def test_bad_source_citation_isolated_without_inventing_or_mutating_actual(self):
        reader, claims, inventory, aliases, rows = fixture(); rows[1]['citations'][0]['line'] = 22
        before = copy.deepcopy(rows); submission, proof = module.source_rows(claims, rows, inventory, aliases, reader)
        self.assertIs(submission['observations'][0]['observed'], True)
        self.assertIsNone(submission['observations'][1]['observed'])
        self.assertIs(proof['records'][1]['original_actual']['observed'], False)
        self.assertEqual(rows, before)

    def test_foreign_normative_subject_or_changed_current_source_stays_unknown(self):
        for change in ['kind', 'alias', 'hash', 'missing', 'unhashable']:
            reader, claims, inventory, aliases, rows = fixture()
            if change == 'kind': inventory['source/A.swift']['kind'] = 'normative-api-document'
            elif change == 'alias': aliases['source/A.swift'] = '/current/B.swift'
            elif change == 'hash': reader.files['/current/A.swift'] += b'edited\n'
            elif change == 'missing': del reader.files['/current/A.swift']
            else: rows[0]['citations'][0]['path'] = []
            result, _ = module.source_rows(claims, rows, inventory, aliases, reader)
            self.assertIsNone(result['observations'][0]['observed'])
            self.assertIs(result['observations'][1]['observed'], False)

    def test_missing_rows_bool_integer_lines_and_unsupported_provider_do_not_pass(self):
        for change in ['missing', 'actual-int', 'line-bool', 'provider']:
            reader, claims, inventory, aliases, rows = fixture()
            if change == 'missing': rows = rows[1:]
            elif change == 'actual-int': rows[0]['observed'] = 1
            elif change == 'line-bool': rows[0]['citations'][0]['line'] = True
            else: claims[0].update(supported=False, unsupported_reason='No verified provider')
            result, proof = module.source_rows(claims, rows, inventory, aliases, reader)
            if change == 'provider': self.assertEqual([r['id'] for r in result['observations']], ['b'])
            else: self.assertIsNone(result['observations'][0]['observed'])
            self.assertNotEqual(proof['records'][0]['binding'], 'retained-actual')

    def test_source_bridge_role_cannot_borrow_component_metadata(self):
        reader, claims, inventory, aliases, rows = fixture(); claims[0]['owner'] = 'bridge'
        result, _ = module.source_rows(claims, rows, inventory, aliases, reader)
        self.assertIsNone(result['observations'][0]['observed'])
        inventory['source/A.swift']['kind'] = 'actual-bridge-source'
        result, _ = module.source_rows(claims, rows, inventory, aliases, reader)
        self.assertIs(result['observations'][0]['observed'], True)

    def test_no_expected_unit_or_duplicate_identity_override(self):
        for change in ['expected', 'duplicate']:
            reader, claims, inventory, aliases, rows = fixture()
            if change == 'expected': rows[0]['expected'] = False
            else: rows.append(copy.deepcopy(rows[0]))
            with self.assertRaises(ValueError): module.source_rows(claims, rows, inventory, aliases, reader)

    def test_visual_wrong_state_frame_isolated_while_exact_actual_retained(self):
        context = {'catalog_sha256': 'a'*64, 'observation_sha256': 'b'*64}
        rows = [{'review_id': 'r1', 'actual': False, 'reason': 'Visible counterexample', 'snapshot_indices': [1]},
                {'review_id': 'r2', 'actual': True, 'reason': 'Original view', 'snapshot_indices': [1]}]
        before = copy.deepcopy(rows)
        result, proof = module.visual_rows(['r1', 'r2'], rows, context, context, {'r1': {1}, 'r2': {2}})
        self.assertIs(result['decisions'][0]['actual'], False)
        self.assertIsNone(result['decisions'][1]['actual'])
        self.assertIs(proof['records'][1]['original_actual']['actual'], True)
        self.assertEqual(rows, before)

    def test_visual_context_cannot_be_rewritten_and_frame_bool_not_integer(self):
        context = {'catalog_sha256': 'a'*64, 'observation_sha256': 'b'*64}
        wrong = dict(context, observation_sha256='c'*64)
        with self.assertRaises(ValueError): module.visual_rows([], [], wrong, context, {})
        rows = [{'review_id': 'r1', 'actual': True, 'reason': 'Claim', 'snapshot_indices': [True]}]
        result, _ = module.visual_rows(['r1'], rows, context, context, {'r1': {1}})
        self.assertIsNone(result['decisions'][0]['actual'])


if __name__ == '__main__': unittest.main(verbosity=2)
