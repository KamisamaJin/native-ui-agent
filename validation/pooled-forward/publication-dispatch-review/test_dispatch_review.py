"""Targeted semantic dispatch controls; all input bodies are synthetic."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from fixture_dispatch import Fixture, HERE, sha, encoded

BATCH_ROOT = HERE.parent/'publication-batch-review'
OBSERVATIONS = []


class DispatchReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f = Fixture(BATCH_ROOT)
        cls.checked = cls.f.checked()

    def overlay(self, reader, reference, value):
        raw = self.f.batch.encoded(value)
        reader.overlay[reference['path']] = raw
        return dict(reference, sha256=sha(raw))

    def value(self, reader, reference):
        return self.f.batch.pinned_value(reader, reference)

    def verify(self, reader, *, author=False, **refs):
        f = self.f;module = f.author if author else f.reviewed
        return module.verify_prepared(f.batch, reader, f.root, refs.get('cause', f.cause_ref),
            refs.get('packets', f.packets_ref), refs.get('selection', f.selection_ref), refs.get('actors', f.actors_ref))

    def selected_change(self, reader, *, spec=None, derivations=None):
        selected = self.value(reader, self.f.selection_ref)
        row = selected['groups'][-1]
        key, callback = ('spec', spec) if spec else ('derivations', derivations)
        value = self.value(reader, row[key]);callback(value)
        row[key] = self.overlay(reader, row[key], value)
        selection_ref = self.overlay(reader, self.f.selection_ref, selected)
        packets = self.value(reader, self.f.packets_ref);packets['selection_seal'] = selection_ref
        return {'selection': selection_ref, 'packets': self.overlay(reader, self.f.packets_ref, packets)}

    def cause_rebind(self, reader, cause):
        cause_ref = self.overlay(reader, self.f.cause_ref, cause)
        selected = self.value(reader, self.f.selection_ref);selected['first_cause_barrier'] = cause_ref
        for row in selected['groups']:
            spec = self.value(reader, row['spec']);spec['first_cause_barrier'] = cause_ref
            row['spec'] = self.overlay(reader, row['spec'], spec)
        selection_ref = self.overlay(reader, self.f.selection_ref, selected)
        packets = self.value(reader, self.f.packets_ref);packets['selection_seal'] = selection_ref
        for row in packets['groups']:
            ledger = self.value(reader, row['operator_ledger']);ledger['first_cause_barrier'] = cause_ref
            row['operator_ledger'] = self.overlay(reader, row['operator_ledger'], ledger)
        return {'cause': cause_ref, 'selection': selection_ref, 'packets': self.overlay(reader, self.f.packets_ref, packets)}

    def previous(self, reader, previous=None, *, author=False, group=None):
        f = self.f;group = group or f.reviewed.ORDER[-1]
        if previous is None:previous = f.ends[f.reviewed.ORDER[f.reviewed.ORDER.index(group)-1]]
        if author:
            return f.author.verify_previous(f.phase, reader, f.root, group, previous, f.cause_ref, self.checked['packet_rows'])
        return f.reviewed.verify_previous(f.phase, reader, f.root, group, previous, f.cause_ref, self.checked['packet_rows'],
            cause_rows=self.checked['cause_rows'], base_refs=self.checked['base_refs'], bindings=self.checked['bindings'])

    def previous_change(self, reader, *, start=None, end=None, prepared=None):
        previous = self.f.ends[self.f.reviewed.ORDER[-2]]
        value = self.value(reader, previous)
        if start or prepared:
            original_start = value['start'];started = self.value(reader, original_start)
            if prepared:
                pr = started['dispatch_prepared'];body = self.value(reader, pr);prepared(body)
                started['dispatch_prepared'] = self.overlay(reader, pr, body)
            if start:start(started)
            value['start'] = self.overlay(reader, original_start, started)
        if end:end(value)
        return self.overlay(reader, previous, value)

    def original_admission(self, reader, operation, label):
        operation()
        OBSERVATIONS.append({'control': self.id(), 'frozen_v2_admitted': label,
                             'changed_synthetic_bytes': {p: {'sha256': sha(v), 'utf8': v.decode()} for p, v in reader.overlay.items() if self.f.reader.overlay.get(p) != v}})

    def test_01_all15_complete_unmocked_selection_packet_actor_and_base_path(self):
        self.assertEqual(set(self.checked['cause_rows']), set(self.f.reviewed.ORDER))
        self.assertEqual(len(self.checked['packet_rows']), 15)
        self.assertEqual(len(self.checked['base_refs']), 15)
        self.assertEqual(len({a for row in self.checked['cause_rows'].values() for a in row['actors'].values()}), 30)
        author = self.f.checked(author=True)
        self.assertEqual(author['base_refs'], self.checked['base_refs'])

    def test_02_complete_fourteen_pair_predecessor_chain(self):
        self.previous(self.f.reader.clone())

    def test_03_cause_barrier_precedes_any_alarm_input_read(self):
        reader = self.f.reader.clone()
        cause = self.value(reader, self.f.cause_ref);cause['groups'].pop()
        bad = self.overlay(reader, self.f.cause_ref, cause);reader.reads.clear()
        with self.assertRaisesRegex(ValueError, 'All fifteen'):
            self.verify(reader, cause=bad)
        self.assertEqual(reader.reads, [bad['path']])

    def test_04_last_actor_mismatch_is_rejected(self):
        reader = self.f.reader.clone();actors = self.value(reader, self.f.actors_ref)
        actors['groups'][self.f.reviewed.ORDER[-1]]['actors']['J2'] = '/root/synthetic_wrong_actor'
        bad = self.overlay(reader, self.f.actors_ref, actors)
        with self.assertRaisesRegex(ValueError, 'Original contexts differ'):
            self.verify(reader, actors=bad)

    def test_05_selection_root_code_and_packet_selection_binding(self):
        for field, changed in [('original_root', '/synthetic/wrong-root'), ('code_pins', {})]:
            reader = self.f.reader.clone();value = self.value(reader, self.f.selection_ref);value[field] = changed
            bad = self.overlay(reader, self.f.selection_ref, value)
            with self.assertRaisesRegex(ValueError, 'selection provenance differs'):
                self.verify(reader, selection=bad)
        reader = self.f.reader.clone();value = self.value(reader, self.f.packets_ref);value['selection_seal']['sha256'] = '0'*64
        bad = self.overlay(reader, self.f.packets_ref, value)
        with self.assertRaisesRegex(ValueError, 'selected inputs'):
            self.verify(reader, packets=bad)

    def test_06_last_spec_group_semantics_with_valid_outer_pins(self):
        reader = self.f.reader.clone()
        refs = self.selected_change(reader, spec=lambda v: v.update(anonymous_group='Case01-I'))
        with self.assertRaisesRegex(ValueError, 'group/spec/cause differs'):
            self.verify(reader, **refs)

    def test_07_derivation_semantics_with_valid_outer_pins(self):
        reader = self.f.reader.clone()
        refs = self.selected_change(reader, derivations=lambda v: v[0]['emitter_admission'].update(forged=True))
        with self.assertRaisesRegex(ValueError, 'admission proof differs'):
            self.verify(reader, **refs)

    def test_08_fixed_control_bytes(self):
        reader = self.f.reader.clone();reader.overlay[str(self.f.root/'business-quality-tools/ALARM-POLICY-v1.json')] = b'{}'
        with self.assertRaisesRegex(ValueError, 'policy bytes differ'):
            self.verify(reader)

    def test_09_repinned_packet_seal_and_ledger_semantics(self):
        for member, mutation, message in [
            ('packet_seal', lambda v: v.update(anonymous_group='Case01-I'), 'different version'),
            ('operator_ledger', lambda v: v.update(anonymous_group='Case01-I'), 'ledger differs')]:
            reader = self.f.reader.clone();packets = self.value(reader, self.f.packets_ref);row = packets['groups'][-1]
            value = self.value(reader, row[member]);mutation(value);row[member] = self.overlay(reader, row[member], value)
            bad = self.overlay(reader, self.f.packets_ref, packets)
            with self.assertRaisesRegex(ValueError, message):
                self.verify(reader, packets=bad)

    def test_10_original_v2_ignores_changed_base_member(self):
        reader = self.f.reader.clone();base = self.checked['base_refs'][self.f.reviewed.ORDER[-1]]
        reader.overlay[str(Path(base['path']).parent/'PACKET.json')] = b'changed synthetic member\n'
        self.original_admission(reader, lambda: self.verify(reader, author=True), 'changed own base member accepted')
        with self.assertRaisesRegex(ValueError, 'Base member bytes differ'):
            self.verify(reader)

    def test_11_repinned_base_member_wrong_group_is_not_just_hash_failure(self):
        reader = self.f.reader.clone();cause = self.value(reader, self.f.cause_ref);row = cause['groups'][-1]
        base = row['inputs'][0];seal = self.value(reader, base)
        member_ref = {'path': str(Path(base['path']).parent/'PACKET.json'), 'sha256': seal['files']['PACKET.json']}
        value = self.value(reader, member_ref);value['anonymous_group'] = 'Case01-I'
        new_member = self.overlay(reader, member_ref, value);seal['files']['PACKET.json'] = new_member['sha256']
        row['inputs'] = [self.overlay(reader, base, seal)];refs = self.cause_rebind(reader, cause)
        self.original_admission(reader, lambda: self.verify(reader, author=True, **refs), 'base member foreign group accepted after complete valid synthetic repinning')
        with self.assertRaisesRegex(ValueError, 'Base member group differs'):
            self.verify(reader, **refs)

    def test_12_borrowed_header_only_base_is_explicitly_unsupported(self):
        f = self.f;reader = f.reader.clone();root = f.batch_root/'fixtures/rich'
        # The borrowed batch fixture omitted this dispatch-only fixed control.
        # Declare exact known bytes as an overlay; never alter the frozen tree.
        reader.overlay[str(root/'business-quality-tools/ALARM-POLICY-v1.json')] = reader.read_bytes(str(f.root/'business-quality-tools/ALARM-POLICY-v1.json'))
        cause = f.ref(f.batch_root/'fixtures/cause/INDEX.json');selected = f.ref(f.case/'selection/ALL-SPECS-SEAL.json');packets = f.ref(f.case/'ALL-PACKETS.json')
        f.author.verify_prepared(f.batch, reader, root, cause, packets, selected, f.actors_ref)
        OBSERVATIONS.append({'control': self.id(), 'frozen_v2_admitted': 'all15 borrowed header-only base seals; not complete base-member evidence'})
        with self.assertRaisesRegex(ValueError, 'Complete own base'):
            f.reviewed.verify_prepared(f.batch, reader, root, cause, packets, selected, f.actors_ref)

    def test_13_prior_start_group_and_judges_semantics(self):
        for field, wrong in [('anonymous_group', 'Case01-I'), ('judges', ['J1'])]:
            reader = self.f.reader.clone();previous = self.previous_change(reader, start=lambda v: v.update({field: wrong}))
            self.original_admission(reader, lambda: self.previous(reader, previous, author=True), 'prior START '+field+' not checked')
            with self.assertRaisesRegex(ValueError, 'input binding differs'):
                self.previous(reader, previous)

    def test_14_prior_base_and_original_cause_semantics(self):
        for field, wrong in [('base_packet', self.checked['base_refs']['Case01-I']), ('original_cause_episode', self.checked['cause_rows']['Case01-I']['episode_end'])]:
            reader = self.f.reader.clone();previous = self.previous_change(reader, start=lambda v: v.update({field: wrong}))
            self.original_admission(reader, lambda: self.previous(reader, previous, author=True), 'prior START '+field+' not checked')
            with self.assertRaisesRegex(ValueError, 'input binding differs'):
                self.previous(reader, previous)

    def test_15_prior_dispatch_actor_code_and_group_semantics(self):
        for mutation in [lambda v: v['entries'][0].update(actor='/root/synthetic_wrong_actor'),
                         lambda v: v['batch'].update(sha256='0'*64), lambda v: v.update(group='Case01-I')]:
            reader = self.f.reader.clone();previous = self.previous_change(reader, prepared=mutation)
            self.original_admission(reader, lambda: self.previous(reader, previous, author=True), 'prior PREPARED actor/code/group unverified')
            with self.assertRaisesRegex(ValueError, 'Previous (original actor|dispatch input)'):
                self.previous(reader, previous)

    def test_16_exact_grade_ref_not_only_role_seal(self):
        reader = self.f.reader.clone()
        previous = self.previous_change(reader, end=lambda v: v['outputs']['J1'].update(grade=v['outputs']['J2']['grade']))
        self.original_admission(reader, lambda: self.previous(reader, previous, author=True), 'wrong grade ref accepted beside valid own role seal')
        with self.assertRaisesRegex(ValueError, 'exact grade/member reference differs'):
            self.previous(reader, previous)

    def test_17_prior_pair_missing_member_count_or_broken_chain_rejected(self):
        reader = self.f.reader.clone();previous = self.previous_change(reader, end=lambda v: v['outputs']['J1'].pop('members'))
        with self.assertRaisesRegex(ValueError, 'grade output reference differs'):
            self.previous(reader, previous)
        bad = dict(self.f.ends[self.f.reviewed.ORDER[-2]], sha256='0'*64)
        with self.assertRaisesRegex(ValueError, 'bytes differ'):
            self.previous(self.f.reader.clone(), bad)

    def test_18_first_group_accepts_no_predecessor_and_rejects_one(self):
        f = self.f
        f.reviewed.verify_previous(f.phase, f.reader, f.root, f.reviewed.ORDER[0], None, f.cause_ref, self.checked['packet_rows'],
            cause_rows=self.checked['cause_rows'], base_refs=self.checked['base_refs'], bindings=self.checked['bindings'])
        with self.assertRaisesRegex(ValueError, 'preceding pair closure required'):
            self.previous(f.reader, f.ends[f.reviewed.ORDER[0]], group=f.reviewed.ORDER[0])

    def test_19_successful_cli_original_context_prompts_and_start(self):
        f = self.f;host = HERE/'HOST';host.mkdir(exist_ok=True)
        source = (HERE/'prepare_alarm_dispatch_v3.py').read_bytes()
        old = b'9f3bf306a5a57875cfb6149fdf9365b6476599074486f60b1d0c65fb304453bc'
        self.assertEqual(source.count(old), 1)
        replacement = f.outer_ref['sha256'].encode();variant = source.replace(old, replacement)
        script = host/'SYNTHETIC-ANCHOR-CLI.py'
        command = [sys.executable, '-B', str(script), '--root', str(f.root), '--group', f.reviewed.ORDER[0]]
        for name, ref in [('batch', f.batch_ref), ('cause-index', f.cause_ref), ('packets-index', f.packets_ref), ('selection-seal', f.selection_ref), ('actors', f.actors_ref)]:
            command += ['--'+name, ref['path'], '--'+name+'-sha256', ref['sha256']]
        if script.exists():
            # Revalidate the completed one-shot preparation; preserve its inputs,
            # source, stdout and created namespace instead of overwriting them.
            record = json.loads((host/'CLI-EXECUTION.json').read_bytes())
            self.assertEqual(script.read_bytes(), variant)
            self.assertEqual(record['returncode'], 0)
            self.assertEqual(record['test_variant_sha256'], sha(variant))
            self.assertEqual(sha(Path(record['source_observations']['path']).read_bytes()), record['source_observations']['sha256'])
            self.assertEqual(sha((host/'CLI.stdout').read_bytes()), record['stdout_sha256'])
            self.assertEqual(sha((host/'CLI.stderr').read_bytes()), record['stderr_sha256'])
            from types import SimpleNamespace
            completed = SimpleNamespace(returncode=record['returncode'], stdout=(host/'CLI.stdout').read_bytes(), stderr=(host/'CLI.stderr').read_bytes())
            execution = 'revalidated retained successful one-shot execution'
        else:
            with script.open('xb') as stream:stream.write(variant)
            completed = subprocess.run(command, capture_output=True)
            (host/'CLI.stdout').write_bytes(completed.stdout);(host/'CLI.stderr').write_bytes(completed.stderr)
            execution = 'executed fresh one-shot CLI'
        self.assertEqual(completed.returncode, 0, completed.stderr.decode())
        answer = json.loads(completed.stdout);prepared = json.loads(Path(answer['prepared']['path']).read_bytes())
        self.assertEqual([e['actor'] for e in prepared['entries']], list(self.checked['cause_rows']['Case01-I']['actors'].values()))
        self.assertEqual(prepared['dispatcher']['sha256'], sha(variant))
        start_path = f.root/'cache/business/blind-quality/episodes/Case01-I/alarm/START.json'
        start = json.loads(start_path.read_bytes())
        self.assertEqual(start['base_packet'], self.checked['base_refs']['Case01-I'])
        self.assertEqual(start['original_cause_episode'], self.checked['cause_rows']['Case01-I']['episode_end'])
        self.assertEqual(start['dispatch_prepared'], answer['prepared'])
        self.assertEqual(start['shared_clock_basis'], 'clock_gettime(CLOCK_MONOTONIC)')
        for entry in prepared['entries']:
            raw = Path(entry['prompt']['path']).read_bytes();text = raw.decode()
            self.assertEqual(sha(raw), entry['prompt']['sha256'])
            self.assertIn('Continue your own prior context.', text)
            self.assertIn('worker-public versus post-seal-private visibility', text)
            self.assertIn(self.checked['base_refs']['Case01-I']['sha256'], text)
            self.assertIn(self.checked['packet_rows']['Case01-I']['packet_seal']['sha256'], text)
            self.assertFalse(any(group in text for group in f.reviewed.ORDER if group != 'Case01-I'))
            self.assertEqual(Path(entry['prompt']['path']).stat().st_mode & 0o222, 0)
            self.assertFalse(Path(entry['output']).exists())
        OBSERVATIONS.append({'control': self.id(), 'synthetic_cli_anchor_only': {'original_literal': old.decode(), 'synthetic_literal': replacement.decode(), 'production_source_sha256': sha(source), 'test_variant_sha256': sha(variant), 'replacements': 1}, 'execution': execution, 'cli_returncode': completed.returncode, 'prepared': answer['prepared']})


if __name__ == '__main__':
    unittest.main(verbosity=2)
