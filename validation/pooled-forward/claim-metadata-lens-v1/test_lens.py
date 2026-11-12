import copy
import hashlib
import importlib.util
from pathlib import Path
import unittest

import lens


P = Path(__file__).resolve().parents[1] / 'publication-alarm-review/revision-v2/anonymous_projection.py'
assert hashlib.sha256(P.read_bytes()).hexdigest() == '5bc14d37d11bd755dad38cf1f13b5bbc133eccedceb13ebb1e037dbd07361f2b'
spec = importlib.util.spec_from_file_location('lens_test_frozen_projection', P)
projection = importlib.util.module_from_spec(spec); spec.loader.exec_module(projection)
REF = {'path': '/recorded/own/self-claim.json', 'sha256': 'a' * 64}


def entry(pointer, text, classification='claimed_provenance_locator'):
    raw = hashlib.sha256(text.encode()).hexdigest()
    return {'original_ref': REF, 'pointer': pointer, 'member_kind': 'string_value',
            'original_utf8_sha256': raw, 'codepoint_length': len(text), 'classification': classification,
            'contains_prose': False, 'whole_container_metadata_permission': False,
            'reference_validated': False, 'evidence_credit': False, 'projection_authorized': False,
            'identity_spans': [{'start': 0, 'end': len(text), 'unit': 'unicode_codepoint',
                                'original_utf8_sha256': raw, 'span_kind': 'complete_canonical_locator'
                                if text.startswith('/') else 'complete_execution_identifier'}]}


def run(value, entries, approvals=None):
    if approvals is None: approvals = {lens.canonical_sha(e, projection) for e in entries}
    return lens.project(value, REF, entries, approvals, projection)


class LensTests(unittest.TestCase):
    def test_metadata_under_compound_summary_only_changes_scalar(self):
        path = '/Users/rex/recorded/capture.json'
        v = {'actual_run_statuses': {'capture': {'path': path, 'sha256': 'b' * 64},
                                    'status': 'failed', 'actual': False, 'counts': [1, 0, None]}}
        before = copy.deepcopy(v); e = entry('/actual_run_statuses/capture/path', path)
        projected, proof = run(v, [e])
        self.assertEqual(v, before)
        self.assertEqual(projected['actual_run_statuses']['capture']['sha256'], 'b' * 64)
        expected = copy.deepcopy(before); expected['actual_run_statuses']['capture']['path'] = 'record-ref-0001'
        self.assertEqual(projected, expected); self.assertFalse(proof['changes'][0]['evidence_credit'])

    def test_every_raw_boundary_and_protected_leaf_blocks(self):
        path = '/Users/rex/recorded/x.json'
        for word in projection.PROTECTED_KEYS:
            with self.assertRaises(ValueError): run({word: {'path': path}}, [entry('/' + word + '/path', path)])
        with self.assertRaises(ValueError): run({'actual_filepath': path}, [entry('/actual_filepath', path)])

    def test_same_identity_stays_equal_without_dictionary_hash_tokens(self):
        e = [entry('/arm', 'A', 'execution_identity_metadata'), entry('/other', 'A', 'execution_identity_metadata')]
        v, _ = run({'arm': 'A', 'other': 'A', 'actual': 'A'}, e)
        self.assertEqual(v['arm'], v['other']); self.assertEqual(v['actual'], 'A')
        self.assertNotIn(hashlib.sha256(b'A').hexdigest(), projection.json_text(v))

    def test_no_collision_with_original_literal(self):
        v, _ = run({'arm': 'A', 'note': 'record-ref-0001'}, [entry('/arm', 'A', 'execution_identity_metadata')])
        self.assertEqual(v['arm'], 'record-ref-0002'); self.assertEqual(v['note'], 'record-ref-0001')

    def test_missing_forged_duplicate_and_foreign_approvals_reject(self):
        path = '/Users/rex/recorded/x.json'; e = entry('/path', path)
        for entries, approvals in [([e], set()), ([e, e], {lens.canonical_sha(e, projection)}),
                                   ([e], {lens.canonical_sha(e, projection), 'c' * 64})]:
            with self.assertRaises(ValueError): run({'path': path}, entries, approvals)
        forged = copy.deepcopy(e); forged['original_utf8_sha256'] = '0' * 64
        with self.assertRaises(ValueError): run({'path': path}, [forged])
        foreign = copy.deepcopy(e); foreign['original_ref'] = dict(REF, path='/recorded/other/self-claim.json')
        with self.assertRaises(ValueError): run({'path': path}, [foreign])

    def test_no_unclassified_identity_or_object_key_redaction(self):
        with self.assertRaises(ValueError): run({'path': '/Users/rex/recorded/x.json'}, [])
        with self.assertRaises(ValueError): run({'/Users/rex/key': 'unchanged'}, [])

    def test_prose_partial_span_and_invalid_role_do_not_hide_claim(self):
        path = '/Users/rex/recorded/x.json'
        for change in [{'contains_prose': True}, {'classification': 'actual_or_proposition'},
                       {'evidence_credit': True}, {'whole_container_metadata_permission': True}]:
            e = entry('/path', path); e.update(change)
            with self.assertRaises(ValueError): run({'path': path}, [e])
        e = entry('/path', path); e['identity_spans'][0]['end'] -= 1
        with self.assertRaises(ValueError): run({'path': path}, [e])
        prose = 'all checks pass /Users/rex/a'
        with self.assertRaises(ValueError): run({'command': prose}, [entry('/command', prose, 'execution_identity_metadata')])

    def test_unicode_and_rfc6901_pointer_keep_exact_facts(self):
        path = '/Users/rex/资料 folder/结果.json'; e = entry('/a~1b~0c/0/path', path)
        value = {'a/b~c': [{'path': path, 'expected': 17.5, 'actual': False}]}
        projected, _ = run(value, [e])
        self.assertEqual(projected['a/b~c'][0]['expected'], 17.5)
        self.assertIs(projected['a/b~c'][0]['actual'], False)


if __name__ == '__main__': unittest.main()
