"""Bounded synthetic metadata/base/chain fixture; reuse sealed batch bytes read-only."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import stat

HERE = Path(__file__).resolve().parent
BATCH_FREEZE_SHA = '704d360588ae6b22f36ff3852bb1f5fec516bd82375e51b16beba933ea940d84'
AUTHOR_FREEZE_SHA = 'd9bd3cf6513a51d70955c0a9bb6e4b724901b350c8376b4d98642f6947d95451'
BATCH_SHA = '3e4ac201f98262fabcfad4368743a471716b80714de1b09c1716b1b1825f6646'


def sha(raw): return hashlib.sha256(raw).hexdigest()
def encoded(value): return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)+'\n').encode()


def load(path, name, wanted):
    if sha(path.read_bytes()) != wanted:
        raise ValueError('Code pin differs: '+str(path))
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result


class Reader:
    def __init__(self, batch_root, own_root, inventory, overlay=None):
        self.batch_root, self.own_root = batch_root, own_root
        self.inventory = inventory
        self.overlay = {} if overlay is None else overlay
        self.directories = {}
        self.reads = []

    def clone(self):
        result = Reader(self.batch_root, self.own_root, self.inventory, dict(self.overlay))
        result.directories = dict(self.directories)
        return result

    def read_bytes(self, original):
        path = Path(original)
        self.reads.append(str(path))
        if str(path) in self.overlay:
            return self.overlay[str(path)]
        if not path.is_absolute() or '..' in path.parts or not (path.is_relative_to(self.batch_root) or path.is_relative_to(self.own_root)):
            raise ValueError('Outside explicit synthetic namespaces')
        if any(p.is_symlink() for p in [path, *path.parents]):
            raise ValueError('Synthetic input symlink')
        if not stat.S_ISREG(path.stat().st_mode):
            raise ValueError('Synthetic regular input required')
        raw = path.read_bytes()
        if path.is_relative_to(self.batch_root):
            key = path.relative_to(self.batch_root).as_posix()
            if key not in self.inventory or sha(raw) != self.inventory[key]['sha256']:
                raise ValueError('Borrowed frozen synthetic byte pin differs')
        return raw

    def directory(self, original):
        if original in self.directories:
            # Explicit restored synthetic role namespace; never an original fallback.
            return self.directory(self.directories[original])
        path = Path(original)
        if not path.is_absolute() or '..' in path.parts or not (path.is_relative_to(self.batch_root) or path.is_relative_to(self.own_root)):
            raise ValueError('Outside explicit synthetic directory namespaces')
        if any(p.is_symlink() for p in [path, *path.parents]) or not path.is_dir():
            raise ValueError('Physical synthetic namespace required')
        if path.is_relative_to(self.batch_root):
            prefix = path.relative_to(self.batch_root).as_posix()+'/'
            actual = {p.relative_to(path).as_posix() for p in path.rglob('*') if p.is_file()}
            expected = {k[len(prefix):] for k in self.inventory if k.startswith(prefix)}
            if actual != expected or any(p.is_symlink() for p in path.rglob('*')):
                raise ValueError('Borrowed synthetic namespace membership differs')
        return path


class Fixture:
    def __init__(self, batch_root, *, create=False):
        self.batch_root = Path(batch_root).resolve()
        freeze_raw = (self.batch_root/'REVIEW-FREEZE.json').read_bytes()
        if sha(freeze_raw) != BATCH_FREEZE_SHA:
            raise ValueError('External batch review freeze differs')
        self.inventory = json.loads(freeze_raw)['files_excluding_this_freeze']
        self.root = HERE/'SYNTHETIC/study'
        self.reader = Reader(self.batch_root, HERE, self.inventory)
        batch_path = self.batch_root/'revision-v3/alarm-material-tools-v3/batch.py'
        for relative in ['revision-v3/alarm-material-tools-v3/batch.py', 'revision-v3/alarm-material-tools-v3/material.py',
                         'revision-v3/alarm-material-tools-v3/EMITTER-SCHEMA-v2.json',
                         *['revision-v3/publication-alarm-review/revision-v2/'+n+'.py' for n in ['anonymous_projection', 'phase_barriers', 'alarm_packet']]]:
            self.reader.read_bytes(str(self.batch_root/relative))
        self.batch = load(batch_path, 'pinned_dispatch_batch_fixture', BATCH_SHA)
        self.phase = self.batch._presentation['phase_barriers']
        self.author = load(HERE/'vendor/prepare_alarm_dispatch_v2.py', 'frozen_dispatch_author', '08354bac9fc95894408c81371f6d9482efe338ef95479de3f564eec780ec81e3')
        self.reviewed = load(HERE/'prepare_alarm_dispatch_v3.py', 'reviewed_dispatch', sha((HERE/'prepare_alarm_dispatch_v3.py').read_bytes()))
        self.case = self.batch_root/'results/v3/cases/test_01_complete_unmocked_all15_selection_and_packaging'
        self.batch_ref = {'path': str(batch_path), 'sha256': BATCH_SHA}
        self.dispatcher_ref = {'path': str(HERE/'prepare_alarm_dispatch_v3.py'), 'sha256': sha((HERE/'prepare_alarm_dispatch_v3.py').read_bytes())}
        if create:
            self.build()
        else:
            value = json.loads((HERE/'SYNTHETIC/REFS.json').read_bytes())
            for key, val in value.items():setattr(self, key, val)
        self.reader.overlay.update({p: raw.encode() for p, raw in json.loads((HERE/'SYNTHETIC/VIRTUAL-CHAIN.json').read_bytes()).items()})
        self.reader.directories.update(json.loads((HERE/'SYNTHETIC/DIRECTORIES.json').read_bytes()))

    def read(self, reference): return self.phase.original(self.reader, reference)

    def put(self, relative, value=None, raw=None):
        path = HERE/relative
        path.parent.mkdir(parents=True, exist_ok=True)
        body = self.batch.encoded(value) if raw is None else raw
        with path.open('xb') as stream:stream.write(body)
        path.chmod(0o444)
        return {'path': str(path), 'sha256': sha(body)}

    def ref(self, path):return {'path': str(path), 'sha256': sha(self.reader.read_bytes(str(path)))}

    def build(self):
        if (HERE/'SYNTHETIC').exists():raise ValueError('Fresh bounded synthetic fixture required')
        for name in self.reviewed.CONTROLS:
            self.put('SYNTHETIC/study/business-quality-tools/'+name, raw=self.reader.read_bytes(str(self.batch_root/'snapshots/source'/name)))
        self.put('SYNTHETIC/study/business-quality-tools/quality_clock.py', raw=(HERE/'vendor/quality_clock.py').read_bytes())
        self.put('SYNTHETIC/study/publication-resolver/resolver.py', raw=self.reader.read_bytes(str(self.batch_root/'snapshots/source/resolver.py')))
        old_cause = self.read(self.ref(self.batch_root/'fixtures/cause/INDEX.json'))
        cause = copy.deepcopy(old_cause)
        for row in cause['groups']:
            group = row['group']; files = {}
            members = {'PACKET.json': encoded({'version': 1, 'anonymous_group': group, 'scope': 'Synthetic base only; no source/native truth'}),
                       'GRADE-TEMPLATE.json': encoded({'version': 1, 'anonymous_group': group, 'kind': 'independent-blind-cause-grade', 'product_causes': [], 'independent_quality_complete': None}),
                       'INSTRUCTIONS.md': b'SYNTHETIC original base instructions. No product finding.\n'}
            for name, raw in members.items():files[name] = self.put('SYNTHETIC/base/'+group+'/'+name, raw=raw)['sha256']
            row['inputs'] = [self.put('SYNTHETIC/base/'+group+'/SEAL.json', {'version': 1, 'kind': 'anonymous-fixed-version-input-seal', 'anonymous_group': group, 'files': files})]
        self.cause_ref = self.put('SYNTHETIC/CAUSE.json', cause)
        self.actors_ref = self.put('SYNTHETIC/ACTORS.json', {'kind': 'original-independent-role-context-registry', 'groups': {r['group']: {'actors': r['actors']} for r in cause['groups']}})
        selected = self.read(self.ref(self.case/'selection/ALL-SPECS-SEAL.json'))
        selected.update(original_root=str(self.root), first_cause_barrier=self.cause_ref)
        for row in selected['groups']:
            spec = self.read(row['spec']);spec['first_cause_barrier'] = self.cause_ref
            for key, name in [('instructions', 'ALARM-INSTRUCTIONS-v1.md'), ('grade_template', 'ALARM-GRADE-TEMPLATE-v1.json')]:
                spec[key] = self.ref(self.root/'business-quality-tools'/name)
            row['spec'] = self.put('SYNTHETIC/specs/'+row['group']+'.json', spec)
        self.selection_ref = self.put('SYNTHETIC/SELECTION.json', selected)
        packets = self.read(self.ref(self.case/'ALL-PACKETS.json'))
        packets['selection_seal'] = self.selection_ref
        for row in packets['groups']:
            ledger = self.read(row['operator_ledger']);ledger['first_cause_barrier'] = self.cause_ref
            for copy_row in ledger['copies']:
                for name in self.reviewed.CONTROLS:
                    if Path(copy_row['original']['path']).name == name:
                        copy_row['original'] = self.ref(self.root/'business-quality-tools'/name)
            row['operator_ledger'] = self.put('SYNTHETIC/ledgers/'+row['group']+'.json', ledger)
        self.packets_ref = self.put('SYNTHETIC/PACKETS.json', packets)
        outer_files = {}
        for i in range(153):
            name = 'member-%03d%s.txt' % (i, '-δ' if i == 152 else '')
            relative = 'case-01/anonymous/'+name
            outer_files[relative] = self.put('SYNTHETIC/study/business-source-review-cohort2/source-contract-supplements/'+relative,
                                           raw=('SYNTHETIC own contract member '+str(i)+'\n').encode())['sha256']
        self.outer_ref = self.put('SYNTHETIC/study/business-source-review-cohort2/source-contract-supplements/OPERATOR-SEAL.json',
                                  {'version': 1, 'kind': 'synthetic-owned-supplement-outer-seal', 'files': outer_files})
        checked = self.checked()
        virtual = {};directories = {};previous = None;self.ends = {}
        def virtual_put(path, value=None, raw=None):
            body = encoded(value) if raw is None else raw
            virtual[str(path)] = body.decode();return {'path': str(path), 'sha256': sha(body)}
        # Four physical members per pair support the genuine unmocked role verifier;
        # chain START/PREPARED/END/prompts remain explicitly registered virtual bytes.
        for group in self.reviewed.ORDER[:-1]:
            outputs = {};entries = []
            destination = self.root/'operators/cohort2/coordination'/self.reviewed.DISPATCH_DIRECTORY/group
            for judge in ['J1', 'J2']:
                output = self.root/'cache/business/blind-quality/grades'/group/judge/'alarm'
                physical = HERE/'SYNTHETIC/role-store'/group/judge/'alarm'
                directories[str(output)] = str(physical)
                grade_copy = self.put(str((physical/'grade.json').relative_to(HERE)), {'anonymous_group': group, 'judge_id': judge, 'scope': 'Synthetic sealed alarm role record; no product finding'})
                grade = virtual_put(output/'grade.json', raw=Path(grade_copy['path']).read_bytes())
                seal_copy = self.put(str((physical/'SEAL.json').relative_to(HERE)), {'version': 1, 'kind': 'independent-blind-alarm-grade-seal', 'anonymous_group': group, 'judge_id': judge, 'files': {'grade.json': grade['sha256']}})
                seal = virtual_put(output/'SEAL.json', raw=Path(seal_copy['path']).read_bytes())
                outputs[judge] = {'seal': seal, 'grade': grade, 'members': 1}
                prompt = virtual_put(destination/(judge+'-PROMPT.txt'), raw=('SYNTHETIC original '+group+' '+judge+' context prompt\n').encode())
                entries.append({'judge': judge, 'actor': checked['cause_rows'][group]['actors'][judge], 'prompt': prompt, 'output': str(output)})
            prepared = {'version': 3, 'kind': 'verified-original-context-alarm-dispatch', 'group': group, 'entries': entries,
                        **checked['bindings'], 'base_packet': checked['base_refs'][group], 'packet_seal': checked['packet_rows'][group]['packet_seal'],
                        'original_cause_episode': checked['cause_rows'][group]['episode_end'], 'previous_pair': previous, 'mapping_revealed': False}
            pr = virtual_put(destination/'PREPARED.json', prepared)
            episode = self.root/'cache/business/blind-quality/episodes'/group/'alarm'
            start = virtual_put(episode/'START.json', {'version': 3, 'kind': 'parallel-independent-alarm-episode-start', 'anonymous_group': group,
                'judges': ['J1', 'J2'], 'first_cause_barrier': self.cause_ref, 'packet_seal': checked['packet_rows'][group]['packet_seal'],
                'base_packet': checked['base_refs'][group], 'original_cause_episode': checked['cause_rows'][group]['episode_end'],
                'dispatch_prepared': pr, 'previous_pair': previous})
            previous = virtual_put(episode/'END.json', {'version': 2, 'kind': 'parallel-independent-alarm-episode-end', 'status': 'sealed',
                'anonymous_group': group, 'judges': ['J1', 'J2'], 'start': start, 'outputs': outputs})
            self.ends[group] = previous
        self.put('SYNTHETIC/VIRTUAL-CHAIN.json', virtual)
        self.put('SYNTHETIC/DIRECTORIES.json', directories)
        refs = {key: getattr(self, key) for key in ['cause_ref', 'actors_ref', 'selection_ref', 'packets_ref', 'outer_ref', 'ends']}
        self.put('SYNTHETIC/REFS.json', refs)
        self.put('SYNTHETIC/SCOPE.json', {'synthetic_only': True, 'borrowed_review_freeze': BATCH_FREEZE_SHA,
            'reused_readonly_all15_packet_bytes': True, 'actual_study_reads': False,
            'metadata_rebinding': 'Fresh full synthetic base inputs; new synthetic cause index; selection root/cause/control refs and corresponding operator ledger refs repinned, with original raw/derived documents and all anonymous alarm packet bytes unchanged.',
            'virtual_chain': 'Explicit serialized synthetic original-key bytes; physical own alarm role dirs contain genuinely hashed grade/seal files. No live path fallback for virtual keys.',
            'native_quality_claim': False})

    def checked(self, reader=None, author=False):
        reader = self.reader if reader is None else reader
        module = self.author if author else self.reviewed
        result = module.verify_prepared(self.batch, reader, self.root, self.cause_ref, self.packets_ref, self.selection_ref, self.actors_ref)
        if not author:
            result['bindings'].update(batch=self.batch_ref, dispatcher=self.dispatcher_ref)
        return result


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser();p.add_argument('--batch-review', type=Path, required=True)
    args = p.parse_args();value = Fixture(args.batch_review, create=True)
    print(json.dumps({'synthetic_root': str(value.root), 'new_files': sum(p.is_file() for p in HERE.rglob('*')), 'refs': str(HERE/'SYNTHETIC/REFS.json')}))
