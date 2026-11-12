"""Exact source-copy aliases for common post-seal responsibility binding.

Only frozen packet roles and exact whole-file byte equivalence are used. There
is no source-text search, basename guess, expected-value lookup or actual
inference. The caller separately authenticates current config/compiled claims,
source scope and the correspondence group before invoking the frozen binder.
"""
import hashlib
import json
from pathlib import PurePosixPath
import re


def need(ok, why):
    if not ok: raise ValueError(why)


def sha(raw): return hashlib.sha256(raw).hexdigest()


def relative(value):
    need(type(value) is str and value and '\\' not in value and '\x00' not in value, 'Safe source member required')
    path = PurePosixPath(value)
    need(not path.is_absolute() and str(path) == value and '..' not in path.parts
         and not any(x.casefold() == '.git' for x in path.parts), 'Safe relative source member required')
    return path


def absolute(value):
    need(type(value) is str and value.startswith('/') and '\\' not in value and '\x00' not in value,
         'Canonical current absolute source reference required')
    path = PurePosixPath(value)
    need(str(path) == value and '..' not in path.parts and not any(x.casefold() == '.git' for x in path.parts),
         'Canonical current absolute source reference required')
    return path


def strict_json(raw):
    def pairs(items):
        out = {}
        for key, value in items:
            need(key not in out, 'Duplicate source metadata key'); out[key] = value
        return out
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('Nonfinite metadata')))


def derive(reader, packet_seal_ref, group, config, compiled_claims, family, platform):
    need(family in {'public', 'private'} and platform in {'ios', 'android'}, 'Exact original source context required')
    need(type(group) is str and group, 'Explicit anonymous group identity required')
    need(type(packet_seal_ref) is dict and set(packet_seal_ref) == {'path', 'sha256'}, 'External packet seal ref required')
    absolute(packet_seal_ref['path'])
    raw = reader.read_bytes(packet_seal_ref['path'])
    need(sha(raw) == packet_seal_ref['sha256'], 'Original packet seal pin differs')
    seal = strict_json(raw); root = PurePosixPath(packet_seal_ref['path']).parent
    need(root.is_absolute() and PurePosixPath(packet_seal_ref['path']).name == 'SEAL.json'
         and seal.get('kind') == 'anonymous-fixed-version-input-seal' and seal.get('anonymous_group') == group
         and type(seal.get('version')) is int and seal['version'] == 1, 'Exact own base packet seal required')
    def member(name):
        name = str(relative(name)); expected = seal['files'].get(name)
        need(type(expected) is str and re.fullmatch('[0-9a-f]{64}', expected), 'Original declared packet member required')
        data = reader.read_bytes(str(root/name)); need(sha(data) == expected, 'Original source-copy bytes differ')
        return data, expected
    packet = strict_json(member('PACKET.json')[0])
    need(packet.get('anonymous_group') == group and type(packet.get('source_files')) is dict,
         'Original own-group source map required')
    need(type(packet.get('fixed_source_file_count')) is int
         and packet['fixed_source_file_count'] == len(packet['source_files']) > 0, 'Complete declared fixed source map required')
    roots = config['source_roots']; approved = {}
    need(type(roots) is list and roots and len(set(roots)) == len(roots), 'Unique original source roots required')
    for path in roots + [config['bridge']]: absolute(path)
    for claim in compiled_claims:
        if claim['method'] != 'source' or not claim.get('supported'): continue
        for path, digest in claim['files'].items():
            absolute(path)
            need(path not in approved or approved[path] == digest, 'Conflicting current subject pin')
            approved[path] = digest
    inventory = {}; aliases = {}; proof = []; unresolved = []
    def add(alias, target, kind):
        _viewed, digest = member(alias)
        if target not in approved: return
        need(sha(reader.read_bytes(target)) == approved[target] == digest, 'Viewed bytes are not the exact current approved subject')
        need(alias not in aliases or aliases[alias] == target, 'Ambiguous source-copy alias')
        aliases[alias] = target; inventory[alias] = {'sha256': digest, 'kind': kind}
        proof.append({'anonymous_path': alias, 'actual_path': target, 'sha256': digest, 'kind': kind,
                      'relation': 'Exact whole-file bytes within the separately approved current subject role'})
    for key, entry in packet['source_files'].items():
        parts = relative(key).parts
        need(len(parts) >= 2 and parts[0].isdigit() and str(int(parts[0])) == parts[0]
             and 0 <= int(parts[0]) < len(roots), 'Original stable source-root index required')
        need(type(entry) is dict and set(entry) == {'sha256', 'bytes'} and type(entry['bytes']) is int and entry['bytes'] >= 0,
             'Exact original source member hash/bytes required')
        alias = 'source/' + key; data, digest = member(alias)
        target = str(PurePosixPath(roots[int(parts[0])])/PurePosixPath(*parts[1:]))
        need(digest == entry['sha256'] and len(data) == entry['bytes']
             and sha(reader.read_bytes(target)) == digest, 'Current listed source member differs')
        add(alias, target, 'production-source')
    bridge = packet['contracts'][family][platform].get('bridge')
    if bridge is not None: add(bridge, config['bridge'], 'actual-bridge-source')
    else: unresolved.append({'role': 'actual-bridge-source', 'reason': 'No original selected-family bridge copy'})
    placement = packet.get('production_placement', {}).get(platform)
    if placement is not None:
        _data, digest = member(placement)
        candidates = sorted({path for claim in compiled_claims
            if claim['method'] == 'source' and claim.get('supported') and claim['owner'] == 'integration'
            for path, expected in claim['files'].items() if expected == digest})
        if len(candidates) == 1: add(placement, candidates[0], 'production-placement')
        else: unresolved.append({'role': 'production-placement', 'reason': 'No unique exact current approved integration subject',
                                'candidate_count': len(candidates)})
    return inventory, aliases, {'version': 1, 'kind': 'exact-neutral-source-copy-alias-derivation',
        'packet_seal': packet_seal_ref, 'group': group, 'family': family, 'platform': platform,
        'fixed_source_file_count_verified': len(packet['source_files']), 'aliases': proof, 'unresolved_roles': unresolved,
        'scope': 'Copy/current-subject identity for the listed members only. The caller/frozen native controller still establishes full current source namespace and capture eligibility. No original actual, source truth, executed integration or delivery pass. Other document roles, including normative API documents, never become aliases.'}
