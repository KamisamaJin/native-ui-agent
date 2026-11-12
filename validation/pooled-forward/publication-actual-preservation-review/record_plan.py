"""Author shape/metadata plan; no actual pack, cleanup or grade/map output."""
import json
import os
import argparse
from pathlib import Path

import preserve as p


def main():
    here = Path(__file__).resolve().parent;study = here.parent;project = study.parents[1]
    parser = argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir', type=Path, default=here)
    output = parser.parse_args().output_dir.absolute();p.need(output == here or output.is_relative_to(here), 'Own new metadata output only')
    output.mkdir(parents=True, exist_ok=True)
    def ref(relative, expected=None):
        result = p.reference(study/relative)
        if expected:p.need(result['sha256'] == expected, 'Root-supplied anchor differs')
        return result
    native_snapshot = ref('publication-native-chain/HOST/actual-whole-pre-binding-v1/SNAPSHOT.json', '9b1ea5e2a26c165483fa0c6c4fdf479b1894a85cbbe0e0519cbcae524257fca5')
    native_result = ref('publication-native-chain/HOST/actual-whole-pre-binding-v1/RESULT.json', '636c0658b4a4a471a7ac70f19fd0009580a45dbe71b74dbae1207914b14ad8e5')
    history = ref('publication-native-chain/history/HOST/final-pre-binding-v1/LEDGER.json', 'c56e48ec653514cc53d7cf9ac2bcae0c863ebab8385da3485b74ac7ce919b491')
    occurrence_result = ref('operators/cohort2/coordination/PUBLIC-FEATURE-REPLAY-v2.json', 'db48d5773d34e4d52bc379408c867b05dc3f8cb37b3217efc4006b6c7a6eca3d')
    occurrence_input = p.pinned(occurrence_result)['input'];p.pinned(occurrence_input)
    original = p.pinned(native_result);snapshot = p.pinned(native_snapshot)
    p.need(original['snapshot'] == native_snapshot, 'Native input/result binding differs')
    manifest = p.pinned(snapshot['anchors']['manifest']);preparation = p.pinned(snapshot['anchors']['initial_preparation'])
    source_roots, subjects, configs, journals, workspaces = set(), set(), set(), set(), set()
    def config(path):
        path = Path(path);p.need(path.is_relative_to(project), 'Config outside declared project')
        cfg = p.read_json(path);configs.add(str(path));source_roots.update(cfg['source_roots'])
        for paths in cfg.get('evidence_subjects', {}).values():subjects.update(paths)
        journal = Path(cfg['resources']['root'])/'events.jsonl'
        if journal.is_file():journals.add(str(journal))
    for task in manifest['tasks']:
        for arm in task['arms'].values():
            workspaces.add(arm['workspace'])
            for kind in ['public_configs', 'hidden_configs']:
                for path in arm[kind].values():config(path)
    def initial(value):
        if isinstance(value, dict):
            if 'source_roots' in value:source_roots.update(value['source_roots'])
            if isinstance(value.get('config'), dict) and set(value['config']) == {'path', 'sha256'}:
                p.pinned(value['config']);config(value['config']['path'])
            for sub in value.values():initial(sub)
        elif isinstance(value, list):
            for sub in value:initial(sub)
    initial(preparation)
    for i in range(1, 6):
        workspaces.update(str(study/f'cache/business/{prefix}/T{i}/workspace') for prefix in ['initial', 'initial-reference'])
    # Only licence/notice/commit metadata from owned stock clones, not upstream
    # source trees, Git objects, SDKs or build dependencies.
    commits = []
    for workspace in sorted(workspaces):
        w = Path(workspace)
        if not w.is_dir():continue
        for repo in sorted(w.iterdir()):
            if not repo.is_dir() or repo.is_symlink():continue
            for candidate in list(repo.iterdir()):
                if candidate.is_file() and not candidate.is_symlink() and candidate.name.upper().startswith(('LICENSE', 'NOTICE', 'COPYING')):subjects.add(str(candidate))
            git = repo/'.git';head = git/'HEAD';commit = None
            if git.is_dir() and not git.is_symlink() and head.is_file() and not head.is_symlink():
                text = head.read_text().strip()
                if text.startswith('ref: '):
                    relative = Path(text[5:])
                    if not relative.is_absolute() and '..' not in relative.parts:
                        loose = git/relative
                        if loose.is_file() and not loose.is_symlink():commit = loose.read_text().strip()
                        elif (git/'packed-refs').is_file():
                            for line in (git/'packed-refs').read_text().splitlines():
                                if line and not line.startswith(('#', '^')) and line.split(' ', 1)[-1] == str(relative):commit = line.split(' ', 1)[0]
                else:commit = text
            if commit is not None:
                import re
                p.need(re.fullmatch('[0-9a-f]{40,64}', commit), 'Unexpected stock clone commit metadata')
                commits.append({'repository_root': str(repo), 'commit_id': commit, 'git_objects_read': False})
    p.save(output/'UPSTREAM-COMMIT-METADATA.json', {'kind': 'owned-stock-upstream-commit-metadata', 'records': commits, 'git_commands_or_objects_read': False})
    for name in ['LICENSE', 'NOTICE', 'README.md', 'THIRD_PARTY_NOTICES.md', '.gitignore']:
        path = project/name
        if path.is_file() and not path.is_symlink():subjects.add(str(path))
    upstream_notice = p.reference(project/'THIRD_PARTY_NOTICES.md')
    upstream_licenses = [p.reference(project/'validation/native-ui-pilot/licenses'/name) for name in ['android-LICENSE', 'ios-LICENSE']]
    subjects.update(row['path'] for row in upstream_licenses)
    # The frozen public Audit caches direct directory-backed reads; include its
    # cache explicitly rather than pretending reader interception saw them all.
    class Reader:
        def read_bytes(self, original):return p.R.read_regular(original)[0]
        def read_json(self, original):return p.R.strict_json(self.read_bytes(original))
        def hash(self, original):return p.sha(self.read_bytes(original))
        def directory(self, original):
            fd = p.R.open_directory(original);os.close(fd);return Path(original)
    reader = Reader();audit = p.module('audit').Audit(reader, str(study/'cache/business/run-cohort2'))
    public = audit.verify(True);audit.finish()
    public_refs = [{'path': str(k), 'sha256': p.sha(v)} for k, v in audit.cache.items() if str(k) not in journals]
    p.save(output/'PUBLIC-READSET.json', {'status': public['status'], 'event_count': public['event_count'], 'files_read': public_refs,
        'scope': 'Recorded public controller replay only; direct cached reads included, no grade or mapping body output.'})
    cold_entry = ref('operators/archive-selection/closed-synthetic-host-v1/ENTRY.json')
    cold_roots = p.pinned(cold_entry)['selection'];p.need(len(cold_roots) == 48, 'Exact original48 closed synthetic roots required')
    registry_path = project/'validation/publications/managed-v12-replay/SOURCE-INVENTORY.json'
    registry_ref = p.reference(registry_path);registry = p.pinned(registry_ref)
    aliases = []
    for row in registry['files'].values():
        if row['source'].startswith('validation/pooled-forward/baseline-v12.6/'):
            path = project/row['source'];raw = p.A.read_file(path)
            p.need(p.sha(raw) == row['sha256'] and len(raw) == row['bytes'], 'Historical v12 plain source differs')
            import hashlib
            p.need(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest() == row['git_blob'], 'Historical original Git blob differs (no Git command used)')
            aliases.append({'path': str(path), 'sha256': row['sha256'], 'bytes': row['bytes'], 'original_git_blob_sha1': row['git_blob']})
    p.need(len(aliases) == 72, 'All72 historical nonidentical plain aliases required')
    p.save(output/'HISTORICAL-72-SOURCES.json', {'registry_ref': registry_ref, 'aliases': aliases, 'other23543_registry_inputs_not_recopied': True})
    scratch = [p.compile_scratch_exclusion(p.reference(path), study) for path in sorted((study/'cache/business/initial').glob('*/compile-attempt-*/ios/command.json'))]
    p.need(scratch, 'Initial compiler command authority missing')
    additional = [native_snapshot, native_result, history, occurrence_input, occurrence_result, registry_ref,
                  *public_refs, *[p.reference(Path(x)) for x in sorted(configs|subjects)], *[x['command_ref'] for x in scratch]]
    plan = {'kind': 'finite-actual-preservation-plan-v1', 'version': 1, 'project_root': str(project), 'study_root': str(study),
        'static_roots': [str(study)], 'cache_evidence_roots': [str(study/'cache/business')],
        'workspace_exclusions': sorted(workspaces), 'regenerable_cache_exclusions': [x['path'] for x in scratch],
        'compile_scratch_exclusions': scratch, 'initial_compile_source_ref': ref('initial_compile.py'), 'already_cold_roots': cold_roots,
        'source_roots': sorted(source_roots), 'subject_files': sorted(subjects|configs),
        'plain_code_roots': [str(project/x) for x in ['native-ui-agent', 'mobile-native-delivery', 'tools', '.github']],
        'transport_failure_input_roots': [str(study/'cache/publication-archives/closed-synthetic-host-v1')],
        'active_streams': [{'path': str(study/'operators/whole-study-meter-v2.jsonl'), 'role': 'active whole-study stream', 'stop_path': None},
                           {'path': str(study/'operators/cohort2/business-arm-disk.jsonl'), 'role': 'active arm stream', 'stop_path': None}],
        'recorded_prefix_journal_paths': sorted(journals), 'native_recorded_readset': native_result, 'native_snapshot': native_snapshot,
        'history_ledger': history, 'occurrence_input': occurrence_input, 'occurrence_recorded_result': occurrence_result,
        'additional_required_refs': additional,
        'external_cold_refs': [ref('publications/closed-qualification-v1/TRANSPORT.json', '941790690a13b58d05e6a4823f73d954eb441dd8c7958e7b2ae9478b84983ef8'),
                               ref('publications/closed-synthetic-host-v1/TRANSPORT.json', 'a6641b4e42d8ea542db0cafa91d5677c7b344ad6de79b10ff512fdf7e1bc9a21')],
        'scope_policy_ref': ref('PUBLICATION-AND-CLEANUP-POLICY-v1.json'), 'cold48_entry_ref': cold_entry,
        'upstream_declared_notice_ref': upstream_notice, 'upstream_license_refs': upstream_licenses,
        'upstream_identity_limit': 'Exact declared revisions are retained in the pinned original notice; no present clone-Git freshness or commit ancestry is inferred from missing .git files.',
        'plain_historical_source_registry_ref': registry_ref,
        'protected_active_shells': [str(study/'cache/business/run-cohort2'), str(study/'cache/business'), str(study/'cache')],
        'protected_plain_code_roots': [*[str(project/x) for x in ['native-ui-agent', 'mobile-native-delivery', 'tools', '.github']], *[str(q) for q in study.iterdir() if q.is_dir() and q.name.startswith(('baseline-', 'candidate-'))]],
        'cleanup_sequence': ['Root verifies positive ownership/member intent plus all archive/readonly replay and cold receipts',
            'Remove only recorded archived children/owned closed build scratch; preserve exact run-cohort2/business/cache shells and cache owner marker',
            'Keep both original meters running through bulk cleanup; root confirms exact stop paths, closes/verifies both final streams',
            'Preserve terminal streams/publication/cleanup records as separate immutable supplement; only then positively remove empty cache shells'],
        'pending': sorted(p.PROOFS)+['final meter stop paths and terminal supplement'],
        'actual_pack_ready': False, 'cleanup_authorized': False}
    result = p.save(output/'PLAN.json', plan)
    p.save(output/'PENDING-CLOSURE.json', {'version': 1, 'kind': 'root-final-preservation-closure-v1', 'closed': False,
        'pending': sorted(p.PROOFS), 'proof_refs': {}, 'portable_source_domain_evaluation': 'unsupported', 'portable_source_responsibility_evaluation': 'unsupported'})
    print(json.dumps({'plan': result, 'native_recorded_files': len(original['files_read']), 'public_recorded_files': len(public_refs),
        'source_roots': len(source_roots), 'subject_files_and_configs': len(subjects|configs), 'cold_prefixes': len(cold_roots), 'historical_aliases_verified': len(aliases), 'ready': False}))


if __name__ == '__main__':main()
