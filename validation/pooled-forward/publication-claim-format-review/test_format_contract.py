"""Bounded synthetic hostile controls. No actual material projection."""
import copy
import json
import unittest
from unittest import mock

import verify_catalog as v


def ref(path='/synthetic/original.json', digest='a'*64):return {'path': path, 'sha256': digest}


def location(value, pointer='/reference/path', classification='claimed_provenance_locator', member_kind='string_value'):
    text = v.resolve(value, pointer, member_kind)
    return {'original_ref': ref(), 'pointer': pointer, 'member_kind': member_kind,
            'original_value_sha256': v.sha(text.encode()), 'original_utf8_sha256': v.sha(text.encode()),
            'original_json_string_sha256': v.sha(json.dumps(text, ensure_ascii=False, separators=(',', ':')).encode()),
            'codepoint_length': len(text), 'classification': classification,
            'structural_reason': 'Synthetic separate locator/identifier slot', 'source_context_explanation': 'No target evidence credit',
            'decision_reason_id': 'synthetic-format-only', 'parent_pointer': pointer.rsplit('/', 1)[0],
            'parent_shape_only': {}, 'identity_spans': [{'start': 0, 'end': len(text), 'unit': 'unicode_codepoint',
                'original_utf8_sha256': v.sha(text.encode()), 'span_kind': 'complete_canonical_locator' if v.canonical_path(text) else 'complete_execution_identifier'}],
            'contains_prose': False, 'protected_boundary_names': [x for x in v.parts(pointer) if v.normalize(x) in v.BLOCKED],
            'whole_container_metadata_permission': False, 'reference_validated': False, 'evidence_credit': False, 'projection_authorized': False}


def contract(loc):
    catalog = {'documents': [{'original_ref': ref(), 'locations': [loc]}]}
    row = {'original_ref': ref(), 'pointer': loc['pointer'], 'member_kind': loc['member_kind'], 'location_sha256': v.location_sha256(loc)}
    approval = {'version': 1, 'kind': 'independent-worker-claim-metadata-responsibility-approval',
                'catalog_seal': ref('/synthetic/catalog/SEAL.json'), 'catalog_ref': ref('/synthetic/catalog/CATALOG.json'),
                'original_document_refs': [ref()], 'approved_locations': [row], 'unapproved_locations': [],
                'all_originals_reverified_unchanged': True, 'scope_limits': ['Synthetic responsibility only; no validity or projection.']}
    return catalog, approval


class FormatContract(unittest.TestCase):
    def setUp(self):self.value = {'reference': {'path': '/Users/example/δ/🙂.json'}}

    def test_01_whole_unicode_codepoint_span(self):
        loc = location(self.value)
        text = v.validate_location(loc, self.value)
        self.assertNotEqual(len(text), len(text.encode()))
        self.assertEqual(loc['identity_spans'][0]['end'], len(text))

    def test_02_entire_location_canonical_json_hash_uses_unicode(self):
        loc = location(self.value);loc['structural_reason'] = 'Unicode δ🙂'
        expected = v.sha(json.dumps(loc, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode())
        self.assertEqual(v.location_sha256(loc), expected)
        self.assertNotEqual(expected, v.sha(json.dumps(loc, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()))

    def test_03_partial_byte_offset_and_wrong_unit_spans_refused(self):
        for mutation in [lambda x: x.update(start=1), lambda x: x.update(end=1), lambda x: x.update(unit='utf8_byte'),
                         lambda x: x.update(end=len(self.value['reference']['path'].encode()))]:
            loc = location(self.value);mutation(loc['identity_spans'][0])
            with self.assertRaisesRegex(ValueError, 'Unicode-codepoint span'):
                v.validate_location(loc, self.value)

    def test_04_utf8_and_json_hashes_are_separate_and_exact(self):
        for field in ['original_value_sha256', 'original_utf8_sha256', 'original_json_string_sha256']:
            loc = location(self.value);loc[field] = '0'*64
            with self.assertRaises(ValueError):v.validate_location(loc, self.value)

    def test_05_every_unconditional_raw_container_refused(self):
        for field in ['actual', 'expected', 'observed', 'rendered', 'measured', 'payload', 'text', 'value', 'label', 'callback', 'event']:
            value = {field: {'path': '/Users/example/unexamined.json'}}
            loc = location(value, '/'+field+'/path');catalog, approval = contract(loc)
            with self.assertRaises(ValueError):v.validate_location(loc, value)
            with self.assertRaises(ValueError):v.validate_approval(catalog, approval)

    def test_06_actual_filepath_leaf_always_refused(self):
        for field in ['actual_filepath', 'ACTUAL_FILEPATH', 'Actual-FilePath']:
            value = {field: '/Users/example/unexamined.swift'};loc = location(value, '/'+field)
            with self.assertRaises(ValueError):v.validate_location(loc, value)

    def test_07_compound_summary_separate_locator_not_container(self):
        value = {'actual_public_summary': {'record': {'path': '/Users/example/record.json'}, 'status': 'U', 'accepted': False, 'count': 0}}
        before = copy.deepcopy(value);loc = location(value, '/actual_public_summary/record/path')
        v.validate_location(loc, value);catalog, approval = contract(loc)
        self.assertEqual(len(v.validate_approval(catalog, approval)), 1)
        self.assertEqual(value, before)
        loc['whole_container_metadata_permission'] = True
        with self.assertRaises(ValueError):v.validate_location(loc, value)

    def test_08_prose_cannot_receive_complete_locator_approval(self):
        value = {'reference': {'path': 'See the recorded /Users/example/result.json'}}
        loc = location(value)
        with self.assertRaises(ValueError):v.validate_location(loc, value)
        loc = location(self.value);loc['contains_prose'] = True
        with self.assertRaises(ValueError):v.validate_approval(*contract(loc))

    def test_09_boolean_or_whole_container_not_scalar_metadata(self):
        loc = location(self.value)
        for value in [{'reference': {'path': True}}, {'reference': {'path': {'nested': 'x'}}}]:
            with self.assertRaisesRegex(ValueError, 'not a string'):v.validate_location(loc, value)

    def test_10_identity_object_key_is_accounted_but_never_approved(self):
        value = {'/Users/example/key': 'preserved'};ptr = '/~1Users~1example~1key'
        loc = location(value, ptr, member_kind='object_key')
        with self.assertRaises(ValueError):v.validate_approval(*contract(loc))
        found = v.inventory(value)
        self.assertEqual(sum(bool(x['identity_probes']) for x in found['keys']), 1)

    def test_11_uncertain_or_proposition_stays_unapproved(self):
        for classification in ['uncertain', 'actual_or_proposition']:
            loc = location(self.value, classification=classification);catalog, approval = contract(loc)
            with self.assertRaises(ValueError):v.validate_approval(catalog, approval)
            approval['unapproved_locations'] = approval['approved_locations'];approval['approved_locations'] = []
            self.assertEqual(v.validate_approval(catalog, approval), {})

    def test_12_entire_location_hash_binds_reason_role_shape_and_flags(self):
        for field, value in [('structural_reason', 'changed'), ('classification', 'execution_identity_metadata'),
                             ('parent_shape_only', {'new': 'string'}), ('evidence_credit', True)]:
            loc = location(self.value);catalog, approval = contract(loc);loc[field] = value
            with self.assertRaisesRegex(ValueError, 'entire|Entire'):v.validate_approval(catalog, approval)

    def test_13_unknown_pointer_or_original_reference_refused(self):
        for mutation in [lambda x: x.update(pointer='/not/original'), lambda x: x['original_ref'].update(sha256='0'*64)]:
            loc = location(self.value);catalog, approval = contract(loc);mutation(approval['approved_locations'][0])
            with self.assertRaises(ValueError):v.validate_approval(catalog, approval)

    def test_14_duplicate_missing_or_selectively_filtered_approval_refused(self):
        loc = location(self.value);catalog, approval = contract(loc)
        approval['approved_locations'].append(copy.deepcopy(approval['approved_locations'][0]))
        with self.assertRaises(ValueError):v.validate_approval(catalog, approval)
        _, approval = contract(loc);approval['approved_locations'] = []
        with self.assertRaisesRegex(ValueError, 'every catalogued'):v.validate_approval(catalog, approval)
        catalog['documents'][0]['locations'].append(copy.deepcopy(loc))
        with self.assertRaisesRegex(ValueError, 'Duplicate catalogue'):v.validate_approval(catalog, contract(loc)[1])

    def test_15_role_cannot_grant_reference_validity_evidence_or_projection(self):
        for field in ['reference_validated', 'evidence_credit', 'projection_authorized']:
            loc = location(self.value);loc[field] = True
            with self.assertRaises(ValueError):v.validate_location(loc, self.value)
            with self.assertRaises(ValueError):v.validate_approval(*contract(loc))

    def test_16_inventory_is_uniform_over_strings_keys_and_scalar_types(self):
        value = {'summary': {'path': '/Users/example/a'}, 'payload': {'text': '/Users/example/b'},
                 'array': ['plain', 'f'*32], 'status': 'U', 'accepted': False, 'count': 0}
        before = copy.deepcopy(value);found = v.inventory(value)
        self.assertEqual(len(found['strings']), 5)
        self.assertEqual(sum(bool(x['identity_probes']) for x in found['strings']), 3)
        self.assertEqual(found['scalar_types']['/accepted'], 'boolean')
        self.assertEqual(value, before)

    def test_17_no_locator_target_stat_read_or_resolve(self):
        loc = location(self.value)
        with mock.patch('pathlib.Path.stat', side_effect=AssertionError('target stat forbidden')), \
             mock.patch('pathlib.Path.read_bytes', side_effect=AssertionError('target read forbidden')), \
             mock.patch('pathlib.Path.resolve', side_effect=AssertionError('target resolve forbidden')):
            v.validate_location(loc, self.value);v.inventory(self.value)
        with self.assertRaisesRegex(ValueError, 'outside explicit'):
            v.ExactReader('/synthetic', {}).read_bytes('/not/authorized/reference-target')

    def test_18_pointer_escaping_and_array_index_are_exact(self):
        value = {'a/b~c': [{'path': '/Users/example/a'}]}
        loc = location(value, '/a~1b~0c/0/path');v.validate_location(loc, value)
        with self.assertRaises(ValueError):v.resolve(value, '/a~1b~0c/00/path')
        with self.assertRaises(ValueError):v.parts('/bad~2key')

    def test_19_approval_requires_original_reverification_and_preserves_input(self):
        loc = location(self.value);catalog, approval = contract(loc);before = copy.deepcopy((catalog, approval))
        approved = v.validate_approval(catalog, approval)
        next(iter(approved.values()))['structural_reason'] = 'mutation of returned copy'
        self.assertEqual((catalog, approval), before)
        approval['all_originals_reverified_unchanged'] = False
        with self.assertRaises(ValueError):v.validate_approval(catalog, approval)

    def test_20_external_catalogue_seal_is_required_before_any_catalogue_read(self):
        loc = location(self.value);_, approval = contract(loc);raw = v.canonical(approval)
        approval_ref = ref('/synthetic/APPROVAL.json', v.sha(raw))
        class Reader:
            def __init__(self):self.reads = []
            def read_bytes(self, path):
                self.reads.append(path)
                if path != approval_ref['path']:raise AssertionError('Unexpected catalogue/target read')
                return raw
        reader = Reader()
        with self.assertRaisesRegex(ValueError, 'External catalogue authority'):
            v.verify_contract(reader, approval_ref, ref('/synthetic/catalog/SEAL.json', '0'*64))
        self.assertEqual(reader.reads, [approval_ref['path']])


if __name__ == '__main__':unittest.main(verbosity=2)
