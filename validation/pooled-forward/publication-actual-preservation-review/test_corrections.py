"""Retained v1 fixture reuse; correct two test/API errors without another tree."""
import argparse
import json
from pathlib import Path
import traceback

import preserve as p


def main():
    parser = argparse.ArgumentParser(description=__doc__);parser.add_argument('--host', type=Path, required=True);parser.add_argument('--transport-only', action='store_true')
    args = parser.parse_args();host = args.host.absolute();prior = p.reference(host/('CORRECTIONS-RESULT.json' if args.transport_only else 'RESULT.json'));report = p.pinned(prior)
    p.need((report['passed'], report['failed']) == ((2, 1) if args.transport_only else (14, 2)), 'Exact retained checkpoint required')
    records = []
    def case(name, function):
        try:records.append({'name': name, 'status': 'passed', 'evidence': function()})
        except BaseException as error:records.append({'name': name, 'status': 'failed', 'error_type': type(error).__name__, 'message': str(error), 'traceback': traceback.format_exc()})
    def rejects(function, text):
        try:function()
        except (ValueError, KeyError) as error:
            p.need(text in str(error), 'Wrong rejection: '+str(error));return str(error)
        raise AssertionError('Hostile control accepted')
    def unsafe():
        original = host/'unsafe-fixture/.git/not-a-live-repo'
        selected, structure, unknown = set(), [], []
        p.walk(original.parent.parent, [], set(), selected, structure, unknown)
        p.need(not selected and len(unknown) == 1 and structure[0]['kind'].startswith('excluded-Git'), 'Unsafe fixture not explicitly unresolved')
        before = original.lstat();original.parent.rename(host/'unsafe-fixture/inert-git-fixture')
        archived = host/'unsafe-fixture/inert-git-fixture/not-a-live-repo';copy = p.reference(archived)
        p.need(copy['sha256'] == p.sha(b'opaque hostile fixture\n') and archived.stat().st_ino == before.st_ino, 'Hostile fixture bytes/identity lost')
        return {'discovered_unsafe_namespace': unknown[0], 'no_Git_content_or_targets_read_by_selector': True,
                'explicit_synthetic_inert_preservation': {'old_key': str(original), 'new_copy': copy, 'same_inode': True,
                    'not_an_original_key_override': True}}
    if not args.transport_only:case('corrected discovery explicitly blocks unsafe Git namespace before strict archive path parser', unsafe)
    def transport():
        archive = host/'archive';index = p.A.file_hash(archive/'INDEX.json');p.A.verify(archive, index)
        mapping = host/'readonly-restore/RESTORED-MAP.json';map_sha = p.A.file_hash(mapping)
        base = p.R.Resolver(mapping, map_sha256=map_sha, index_sha256=index)
        for original in base._rows:base.hash(original)
        project = host/'project';original = project/'study/request.json';subject = project/'study/cache/business/workspace/reply/src/subject.kt'
        p.need(not original.exists() and not subject.exists(), 'Original subjects must be absent for this control')
        raw = ('{\n  "path": "'+str(subject)+'",\n  "text": "π unchanged"\n}\n').encode()
        p.need(base.read_bytes(str(original)) == raw, 'Original bytes rewritten/fallback used')
        directory = base.directory(str(subject.parent));p.need((directory/subject.name).read_bytes() == b'// exact selected subject\n', 'Directory namespace differs')
        errors = {'unregistered_original': rejects(lambda: base.read_bytes(str(project/'unregistered-live.json')), 'absent'),
                  'map_pin': rejects(lambda: p.R.Resolver(mapping, map_sha256='0'*64, index_sha256=index), 'differs'),
                  'index_pin': rejects(lambda: p.A.verify(archive, '0'*64), 'differs')}
        p.need(all(int(row['restored_mode'], 8) & 0o222 == 0 for row in base._rows.values()), 'Writable restored input')
        physical = base.file(str(original));physical.chmod(0o644);physical.write_bytes(b'X'+raw[1:]);physical.chmod(0o444)
        errors['same_size_restored_SHA'] = rejects(lambda: base.read_bytes(str(original)), 'SHA256 differs')
        return {'archive_index_sha256': index, 'restore_map_sha256': map_sha, 'mapped_files_before_intentional_corruption': len(base._rows),
                'originals_absent_JSON_bytes_unchanged': True, 'readonly_before_corruption': True, 'hostile_rejections': errors,
                'final_restore_intentionally_corrupted_after_verified_roundtrip': True}
    case('completed genuine archive/Resolver controls with absent originals and changed restored bytes', transport)
    def semantic_scratch():
        study = host/'semantic-study';folder = study/'cache/business/initial/T1/compile-attempt-2/ios';folder.mkdir(parents=True)
        rows = []
        for name, derived, project in [('retarget', folder/'compile.xcresult', folder/'project/Observer.xcodeproj'),
                                       ('proof-inside-scratch', folder/'DerivedData', folder/'DerivedData/Observer.xcodeproj')]:
            target = folder/('command.json' if name == 'retarget' else 'attempt/command.json')
            if name != 'retarget':
                folder2 = study/'cache/business/initial/T1/compile-attempt-3/ios';folder2.mkdir(parents=True);target = folder2/'command.json'
                derived, project = folder2/'DerivedData', folder2/'DerivedData/Observer.xcodeproj'
            value = {'platform': 'ios', 'argv': ['xcodebuild', 'build-for-testing', '-derivedDataPath', str(derived), '-project', str(project), '-resultBundlePath', str(target.parent/'compile.xcresult')]}
            target.write_text(json.dumps(value));reference = p.reference(target)
            error = rejects(lambda: p.compile_scratch_exclusion(reference, study), 'Only exact' if name == 'retarget' else 'Compiler proof aliases')
            rows.append({'input': reference, 'rejected': error})
        return rows
    if not args.transport_only:case('valid compiler namespaces reject scratch retargeting and proof aliases', semantic_scratch)
    result = {'version': 1, 'kind': 'retained-v1-bounded-correction-controls', 'prior_result': prior,
              'prior_raw_failures_retained': True, 'passed': sum(r['status'] == 'passed' for r in records),
              'failed': sum(r['status'] == 'failed' for r in records), 'controls': records,
              'scope': 'Only corrected metadata-discovery/test exception/API handling and two additional semantic compile exclusions; no actual study pack/replay/cleanup.'}
    saved = p.save(host/('CORRECTIONS-TRANSPORT-RESULT.json' if args.transport_only else 'CORRECTIONS-RESULT.json'), result);print(json.dumps({'passed': result['passed'], 'failed': result['failed'], 'result': saved}))
    raise SystemExit(0 if result['failed'] == 0 else 1)


if __name__ == '__main__':main()
