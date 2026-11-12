import copy
import hashlib
import json
import unittest

import source_aliases as module


class Reader:
    def __init__(self): self.files = {}
    def put(self, path, raw): self.files[path] = raw; return hashlib.sha256(raw).hexdigest()
    def read_bytes(self, path): return self.files[path]


def fixture():
    reader = Reader(); members = {}; source = b'component one\n'; bridge = b'import Component\n'; place = b'include Sources\n'
    for alias, raw in [('source/0/Widget.swift', source), ('contracts/private/ios/Bridge.swift', bridge),
                       ('source/placement/ios/Package.swift', place), ('contracts/private/ios/API.md', b'API only\n')]:
        members[alias] = reader.put('/packet/'+alias, raw)
    packet = {'anonymous_group': 'Case00-X', 'fixed_source_file_count': 1, 'source_files': {'0/Widget.swift': {'sha256': members['source/0/Widget.swift'], 'bytes': len(source)}},
              'contracts': {'private': {'ios': {'bridge': 'contracts/private/ios/Bridge.swift', 'api': 'contracts/private/ios/API.md'}}},
              'production_placement': {'ios': 'source/placement/ios/Package.swift'}}
    members['PACKET.json'] = reader.put('/packet/PACKET.json', json.dumps(packet).encode())
    seal = {'version': 1, 'kind': 'anonymous-fixed-version-input-seal', 'anonymous_group': 'Case00-X', 'files': members}
    reference = {'path': '/packet/SEAL.json', 'sha256': reader.put('/packet/SEAL.json', json.dumps(seal).encode())}
    config = {'source_roots': ['/current/Sources'], 'bridge': '/current/Bridge.swift'}
    targets = [('/current/Sources/Widget.swift', source, 'component'), ('/current/Bridge.swift', bridge, 'bridge'), ('/current/Package.swift', place, 'integration')]
    claims = []
    for target, raw, owner in targets:
        digest = reader.put(target, raw)
        claims.append({'id': owner, 'owner': owner, 'method': 'source', 'supported': True, 'files': {target: digest}})
    return reader, reference, config, claims


class AliasControls(unittest.TestCase):
    def test_only_exact_source_roles_are_aliased_without_mutating_inputs(self):
        reader, ref, config, claims = fixture(); before = copy.deepcopy(claims)
        inventory, aliases, proof = module.derive(reader, ref, 'Case00-X', config, claims, 'private', 'ios')
        self.assertEqual(len(aliases), 3)
        self.assertNotIn('contracts/private/ios/API.md', aliases)
        self.assertEqual(inventory['contracts/private/ios/Bridge.swift']['kind'], 'actual-bridge-source')
        self.assertEqual(proof['unresolved_roles'], []); self.assertEqual(claims, before)

    def test_wrong_group_changed_copy_or_current_source_cannot_bind(self):
        for change in ['group', 'copy', 'current']:
            reader, ref, config, claims = fixture()
            group = 'Case00-Y' if change == 'group' else 'Case00-X'
            if change == 'copy': reader.files['/packet/source/0/Widget.swift'] += b'changed'
            if change == 'current': reader.files['/current/Sources/Widget.swift'] += b'changed'
            with self.assertRaises(ValueError): module.derive(reader, ref, group, config, claims, 'private', 'ios')

    def test_ambiguous_integration_bytes_do_not_choose_a_target(self):
        reader, ref, config, claims = fixture(); claims.append(copy.deepcopy(claims[-1])); claims[-1]['files'] = {'/another/Package.swift': next(iter(claims[-1]['files'].values()))}
        _inventory, aliases, proof = module.derive(reader, ref, 'Case00-X', config, claims, 'private', 'ios')
        self.assertNotIn('source/placement/ios/Package.swift', aliases)
        self.assertEqual(proof['unresolved_roles'][0]['candidate_count'], 2)

    def test_selected_bridge_must_match_actual_compiled_subject_bytes(self):
        reader, ref, config, claims = fixture(); reader.files['/current/Bridge.swift'] = b'normative stub\n'
        claims[1]['files']['/current/Bridge.swift'] = hashlib.sha256(reader.files['/current/Bridge.swift']).hexdigest()
        with self.assertRaises(ValueError): module.derive(reader, ref, 'Case00-X', config, claims, 'private', 'ios')

    def test_noncanonical_config_root_is_not_a_source_alias(self):
        reader, ref, config, claims = fixture(); config['source_roots'] = ['/current/../Sources']
        with self.assertRaises(ValueError): module.derive(reader, ref, 'Case00-X', config, claims, 'private', 'ios')


if __name__ == '__main__': unittest.main(verbosity=2)
