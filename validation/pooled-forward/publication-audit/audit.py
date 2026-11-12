"""Read-only replay of the recorded v4 paired-controller chain.

This checks recorded provenance/barriers, never imports Study/Run, executes SDKs,
judges a product, edits an input, grants new time or adopts historical evidence.
"""
import copy
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re


HELPER_SHA = '1a52cc62be5cee0bad34fefe8b54a7479761ca5ea5e8981937a8a1ad11ae6b05'
DOMAIN_SHA = 'fd82356e7b76a8b3099351d6de4d19259eeb241dd99e06b1c4efad3668ba7c8c'
LIMIT = 1200
DIAGNOSTICS = 2
META = {'sequence', 'previous_sha256', 'at_unix', 'at_clock', 'kind'}
ACTIONS = {'diagnostic', 'final', 'review-native', 'review-source', 'finish-review', 'retire'}


def need(value, message):
    if not value:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def finite(value):
    return type(value) in {int, float} and math.isfinite(value) and value >= 0


def pin(value):
    need(isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value), 'Exact SHA256 required')
    return value


def path(value):
    need(isinstance(value, str) and value.startswith('/') and '\x00' not in value, 'Absolute original path required')
    p = PurePosixPath(value)
    need(str(p) == value and not any(v in {'.', '..'} or v.casefold() == '.git' for v in value.split('/')), 'Unsafe original path')
    return p


def relative(value):
    need(isinstance(value, str) and value and '\\' not in value and '\x00' not in value, 'Relative member required')
    p = PurePosixPath(value)
    need(not p.is_absolute() and str(p) == value and not any(v in {'.', '..'} or v.casefold() == '.git' for v in value.split('/')), 'Unsafe member')
    return p


def intersects(a, b):
    return a == b or a.is_relative_to(b) or b.is_relative_to(a)


def policy(value):
    value = copy.deepcopy(value)
    for key in ['approved_at_utc', 'approved_by']:
        value.pop(key, None)
    for item in value['platforms'].values():
        item.pop('approved_component_revisions', None)
    return value


class Audit:
    def __init__(self, resolver, original_run_root):
        self.r = resolver; self.root = path(str(original_run_root)); self.cache = {}; self.directories = {}
        self.failures = []; self.late = []; self.domain_admissions = 0
        self.manifest = self.load(self.root / 'manifest.json')
        m = self.manifest
        need(m.get('version') == 1 and len(m.get('tasks', [])) == 5, 'Frozen v4 requires five paired tasks')
        need(path(m['run_root']) == self.root, 'Manifest run root differs')
        need(len({t['id'] for t in m['tasks']}) == 5 and all(len(t['arms']) == 2 for t in m['tasks']), 'Unique task pairs required')
        self.arms = {(t['id'], alias): arm for t in m['tasks'] for alias, arm in t['arms'].items()}
        for task, alias in self.arms:
            need(re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,63}', task) and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,63}', alias), 'Unsafe assignment ID')
        self.hidden_paths = [path(v) for a in self.arms.values() for v in a['hidden_configs'].values()]
        need(not any(intersects(self.root, h) for h in self.hidden_paths), 'Hidden configs intersect controller root')
        self.prepare(self.root)

    def physical(self, original):
        original = path(str(original))
        roots = [p for p in self.directories if original.is_relative_to(p)]
        return self.directories[max(roots, key=lambda p: len(p.parts))] / str(original.relative_to(max(roots, key=lambda p: len(p.parts)))) if roots else None

    def prepare(self, original):
        original = path(str(original))
        need(not any(intersects(original, h) for h in self.hidden_paths), 'Preauthorization directory includes hidden config')
        if self.physical(original) is None:
            self.directories[original] = self.r.directory(str(original))
        return self.physical(original)

    def raw(self, original):
        original = path(str(original))
        if original not in self.cache:
            actual = self.physical(original)
            self.cache[original] = actual.read_bytes() if actual is not None else self.r.read_bytes(str(original))
        return self.cache[original]

    def load(self, original):
        return json.loads(self.raw(original))

    def sha(self, original):
        return hashlib.sha256(self.raw(original)).hexdigest()

    def ref(self, value, parse=True):
        need(isinstance(value, dict) and set(value) == {'path', 'sha256'}, 'Exact file reference required')
        pin(value['sha256']); need(self.sha(value['path']) == value['sha256'], 'Referenced bytes differ: '+value['path'])
        return self.load(value['path']) if parse else self.raw(value['path'])

    def available(self, original):
        try:
            self.raw(original)
            return True
        except (KeyError, FileNotFoundError):
            return False

    def finish(self):
        for original, actual in self.directories.items():
            need(self.r.directory(str(original)) == actual, 'Verified directory mapping changed')
        for original, raw in self.cache.items():
            if self.physical(original) is None:
                need(self.r.hash(str(original)) == hashlib.sha256(raw).hexdigest(), 'Referenced external file changed')

    def snapshot(self, value, roots):
        need(set(value) == {'roots', 'files', 'content_sha256'} and value['files'], 'Exact nonempty source snapshot required')
        need([v['path'] for v in value['roots']] == roots, 'Source root order/namespace differs')
        for root in value['roots']:
            path(root['path'])
            need(set(root) == {'path', 'device', 'inode'} and all(type(root[k]) is int and root[k] >= 0 for k in ['device', 'inode']), 'Source identity missing')
        for name, row in value['files'].items():
            p = relative(name); index = p.parts[0]
            need(index.isdigit() and str(int(index)) == index and int(index) < len(roots) and len(p.parts) > 1, 'Source member root index invalid')
            need(set(row) == {'sha256', 'bytes'} and type(row['bytes']) is int and row['bytes'] >= 0, 'Source byte metadata invalid')
            pin(row['sha256'])
        need(value['content_sha256'] == digest(value['files']), 'Source content digest differs')
        return value

    def capsule(self, reference, roots):
        value = self.snapshot(self.ref(reference), roots); folder = path(reference['path']).parent / 'files'
        physical = self.physical(folder)
        need(physical is not None and physical.is_dir(), 'Source capsule must be under verified run root')
        actual = {p.relative_to(physical).as_posix() for p in physical.rglob('*') if p.is_file()}
        need(actual == set(value['files']), 'Source capsule members differ')
        for member, row in value['files'].items():
            raw = self.raw(folder / member)
            need(len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256'], 'Source capsule bytes differ')
        return value

    def events(self):
        folder = self.physical(self.root / 'events')
        files = sorted(folder.iterdir()); events = []; previous = None
        for i, f in enumerate(files):
            need(f.name == '%06d.json' % i and f.is_file(), 'Event file sequence/gap differs')
            original = self.root / 'events' / f.name; e = self.load(original)
            need(type(e['sequence']) is int and e['sequence'] == i and e['previous_sha256'] == previous, 'Event hash chain differs')
            need(finite(e['at_clock']) and finite(e['at_unix']) and isinstance(e['kind'], str), 'Event timestamps/kind invalid')
            previous = self.sha(original); events.append(e)
        need(events and events[0]['kind'] == 'initialized' and sum(e['kind'] == 'initialized' for e in events) == 1, 'Unique initial event required')
        need(events[0].get('cohort_members') == 10 and events[0].get('no_native_execution') is True and events[0].get('no_hidden_open') is True, 'Initial barrier declaration differs')
        return events

    def prerequisites(self):
        m = self.manifest; init = self.load(self.root / 'INIT.json')
        need(init['manifest_sha256'] == self.sha(self.root / 'manifest.json') and init['initial_cohort_sha256'] == self.sha(self.root / 'INITIAL-COHORT.json'), 'Initial admission hashes differ')
        need(init['helper_sha256'] == HELPER_SHA and init['domain_transport_sha256'] == DOMAIN_SHA, 'Unsupported frozen controller/domain version')
        self.init = init
        for key in ['protocol', 'speed_gate', 'design_approval']:
            self.ref(m[key])
        protocol = self.load(m['protocol']['path'])['business']
        need((protocol['tasks'], protocol['repair_budget_minutes'], protocol['diagnostic_requests_max']) == (5, 20, 2), 'Frozen budget protocol differs')
        gate = self.load(m['speed_gate']['path'])
        need(gate.get('passed') is True and gate.get('business_tasks_may_start') is True, 'Speed prerequisite did not authorize business')
        for key, hkey in [('path', 'sha256'), ('meter_path', 'meter_sha256'), ('meter_spec_path', 'meter_spec_sha256')]:
            self.ref({'path': m['envelope'][key], 'sha256': m['envelope'][hkey]}, parse=False)
        meter=self.load(m['envelope']['meter_spec_path'])
        need(meter['max_total_allocated_bytes']<=32*2**30 and meter['min_free_bytes']>=5*2**30,'Common meter budget exceeds frozen protocol')
        for tool in m['tools'].values():
            folder = self.prepare(path(tool['skill_root']))
            required = {'SKILL.md', 'scripts/ui_loop.py', *[p.relative_to(folder).as_posix() for p in (folder/'scripts').glob('*.py')],
                        *[p.relative_to(folder).as_posix() for p in (folder/'references').glob('*.md')],
                        *[p.relative_to(folder).as_posix() for p in (folder/'assets').rglob('*') if p.is_file()]}
            need(required <= set(tool['files']), 'Frozen tool omitted public members')
            for member, expected in tool['files'].items():
                relative(member); need(self.sha(path(tool['skill_root']) / member) == pin(expected), 'Frozen tool bytes differ')
        need({v['api'] for v in m['tools'].values()} == {'stateful-default', 'baseline-explicit-prior'}, 'Frozen paired APIs differ')
        if m.get('source_domain_reviews'):
            self.registry = self.ref(m['source_domain_reviews']['registry'])
            authority = self.load(self.root/'DOMAIN-AUTHORITY.json')
            need(self.sha(self.root/'DOMAIN-AUTHORITY.json') == init['domain_authority_sha256'] and authority['registry'] == m['source_domain_reviews']['registry'], 'Domain authority pin differs')
            self.authority = authority
        else:
            need(init.get('domain_authority_sha256') is None, 'Unexpected domain authority')
        cohort = self.load(self.root / 'INITIAL-COHORT.json')
        need(set(cohort) == {t['id'] for t in m['tasks']}, 'Initial task cohort differs')
        self.initial = {}; self.public = {}; self.initial_active = {}
        for t in m['tasks']:
            need(set(cohort[t['id']]) == set(t['arms']), 'Initial arm cohort differs')
            pairs = []
            for alias, a in t['arms'].items():
                key = t['id'], alias; base = self.root/'arms'/key[0]/key[1]
                need(cohort[key[0]][alias]['path'] == str(base/'initial/source.json'), 'Initial capsule pointer differs')
                value = self.capsule(cohort[key[0]][alias], a['source_roots']); self.initial[key] = value; pairs.append(value['files'])
                public = self.load(base/'public-inputs.json'); self.public[key] = public
                for p, expected in public.items():
                    need(not any(intersects(path(p), h) for h in self.hidden_paths), 'Hidden config in public readset')
                    need(self.sha(p) == pin(expected), 'Public input changed')
                self.initial_active[key] = {p: {'path': v, 'sha256': self.sha(v)} for p, v in a['public_configs'].items()}
                need(set(a['public_configs']) == set(a['hidden_configs']) and a['public_configs'], 'Public/hidden profiles differ')
            need(pairs[0] == pairs[1], 'Paired initial bytes differ')

    def domain_update(self, e, active, requests):
        key=e['task'], e['arm']; profile=e['profile']
        need(profile in active[key] and active[key][profile] == e['parent_config'], 'Domain config parent differs')
        req = self.ref(e['request']); capsule = self.ref(req['component_capsule'], parse=False)
        need(all(req[k] == e[k] for k in ['task','arm','profile','platform','request_id','component','policy_sha256']) and req['active_config'] == e['parent_config'], 'Domain request belongs to another assignment/config')
        self.snapshot(req['source'], self.arms[key]['source_roots'])
        need(req['source']['roots'] == self.initial[key]['roots'], 'Domain request source namespace differs')
        need(hashlib.sha256(capsule).hexdigest()==req['component']['sha256'] and len(capsule)==req['component']['bytes'], 'Domain request component capsule differs')
        namespaces=[str(i)+'/'+str(path(req['component']['path']).relative_to(path(root))) for i,root in enumerate(self.arms[key]['source_roots']) if path(req['component']['path']).is_relative_to(path(root))]
        need(any(req['source']['files'].get(p)=={'sha256':req['component']['sha256'],'bytes':req['component']['bytes']} for p in namespaces),'Domain component is not actual production source')
        need(any(v['kind'] == 'domain_review_requested' and v.get('request_id') == e['request_id'] and v['request'] == e['request'] for v in requests), 'Domain admission has no original request')
        folder=path(e['config']['path']).parent
        physical=self.physical(folder)
        need(physical is not None and {p.name for p in physical.iterdir()} == set(e['files']), 'Domain version inventory differs')
        for member, expected in e['files'].items():
            need(len(relative(member).parts) == 1 and self.sha(folder/member) == pin(expected), 'Domain version member differs')
        old=self.ref(e['parent_config']); new=self.ref(e['config'])
        need({k:v for k,v in old.items() if k!='coverage_domain_ref'} == {k:v for k,v in new.items() if k!='coverage_domain_ref'}, 'Domain admission changed another config field')
        previous=self.load(old['coverage_domain_ref']['path']); proposed=self.load(new['coverage_domain_ref']['path'])
        need(digest(previous) == old['coverage_domain_ref']['sha256'] and digest(proposed) == new['coverage_domain_ref']['sha256'] and digest(policy(previous)) == digest(policy(proposed)), 'Domain policy or canonical pin changed')
        added=[]
        for platform, definition in previous['platforms'].items():
            before=definition['approved_component_revisions']; after=proposed['platforms'][platform]['approved_component_revisions']
            need(all(k in after and after[k] == v for k,v in before.items()), 'Domain rewrote an old revision')
            seen=set()
            for label,row in after.items():
                need(re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,95}',label) and type(row.get('bytes')) is int and row['bytes'] >= 0, 'Domain revision label/bytes invalid')
                pair=pin(row.get('sha256')),row['bytes']; need(pair not in seen,'Domain duplicate revision alias'); seen.add(pair)
            for label in set(after)-set(before): added.append((platform,label,after[label]))
        need(set(previous['platforms']) == set(proposed['platforms']) and len(added) == 1 and added[0][0] == req['platform'] and added[0][1] == e['revision'] and added[0][2] == {'sha256':req['component']['sha256'],'bytes':req['component']['bytes']}, 'Domain append differs from actual component')
        seal=self.ref(e['review_seal']); provenance=self.ref(e['provenance']); reviewer=seal['reviewer_id']
        need(reviewer in self.registry['reviewers'] and seal['kind']=='source-domain-review-seal' and seal['version']==1, 'Unregistered domain seal')
        seal_root=path(e['review_seal']['path']).parent; registered=path(self.authority['identities'][reviewer]['path'])
        need(seal_root.is_relative_to(registered) and seal_root != registered and set(seal['files']) == {'review.json','approval.json','component.source'}, 'Domain reviewer location/inventory differs')
        for member, expected in seal['files'].items(): need(self.sha(seal_root/member) == pin(expected), 'Independent domain review member differs')
        record=self.load(seal_root/'review.json')
        checks={'version':1,'kind':'independent-source-domain-review','reviewer_id':reviewer,'scope':'source_shape_only','decision':'approved','request_id':req['request_id'],'request_sha256':e['request']['sha256'],'study_id':req['study_id'],'task':req['task'],'arm':req['arm'],'profile':req['profile'],'platform':req['platform'],'source_sha256':req['source']['content_sha256'],'component':req['component'],'parent_approval_sha256':req['parent_approval_sha256'],'policy_sha256':req['policy_sha256'],'config_sha256':req['active_config']['sha256']}
        need(all(record.get(k)==v for k,v in checks.items()) and isinstance(record.get('reason'),str) and record['reason'].strip() and record.get('proposed_approval_sha256')==digest(proposed), 'Domain review binds another request')
        actual=self.raw(seal_root/'component.source')
        need(hashlib.sha256(actual).hexdigest()==req['component']['sha256'] and len(actual)==req['component']['bytes'] and self.load(seal_root/'approval.json')==proposed, 'Domain independently reviewed bytes differ')
        pchecks={'version':1,'kind':'independent-source-domain-review-provenance','request_id':req['request_id'],'review_seal_sha256':e['review_seal']['sha256'],'reviewer_id':reviewer,'independent_of_repair':True}
        need(all(provenance.get(k)==v for k,v in pchecks.items()) and provenance.get('independent_of_repair') is True and provenance.get('operator_id') in self.registry['operators'] and isinstance(provenance.get('delivery_reference'),str) and provenance['delivery_reference'].strip(), 'Domain provenance differs')
        active[key][profile]=e['config']; self.domain_admissions+=1

    def readset(self, key, active):
        a=self.arms[key]; m=self.manifest
        return {'public_inputs':self.public[key], 'tool_files':m['tools'][a['tool']]['files'], 'helper_sha256':HELPER_SHA,
                'speed_gate':m['speed_gate'],'design_approval':m['design_approval'],'domain_transport_sha256':DOMAIN_SHA,
                'source_domain_registry':m.get('source_domain_reviews',{}).get('registry'),'active_configs':active}

    def outcome(self, request, row, original):
        need(self.load(original) == row and row['action'] == request['action'], 'Original outcome differs')
        need(finite(row['started_at_unix']) and finite(row['finished_at_unix']) and finite(row['wall_seconds']), 'Outcome time missing')
        if row.get('error'):
            failure=self.load(path(str(original)).parent/'failure.json')
            need(failure.get('error')==row['error'] and isinstance(failure.get('traceback'),str) and failure['traceback'].strip(),'Original failure/error traceback missing')
        for field in ['cycle','completion','bound_review','capture','submission']:
            if row.get(field):
                ref={k:row[field][k] for k in ['path','sha256']}; self.ref(ref,parse=False)
        if row.get('inventory'):
            inventory=self.ref(row['inventory'])
            for p,want in inventory.items(): need(self.sha(p)==pin(want),'Immutable service original changed')
            if row.get('service_output'):
                physical=self.physical(path(row['service_output']))
                if physical is not None:
                    actual={str(path(row['service_output'])/p.relative_to(physical).as_posix()) for p in physical.rglob('*') if p.is_file()}
                    need(actual==set(inventory),'Original service inventory omitted/added members')
        for ref in row.get('acquisition_evidence',{}).values():
            if ref: self.ref(ref,parse=False)
        integrity=row.get('integrity',{})
        need(type(integrity.get('passed')) is bool and type(row.get('accepted')) is bool, 'Explicit integrity/accepted flags required')
        if integrity['passed']:
            need(integrity.get('source_sha256')==request['source']['content_sha256'] and integrity.get('readset_sha256')==digest(request['readset']),'Outcome integrity binds another source/readset')
        accepted=row.get('exit_code')==0 and not row.get('error') and row.get('service_status')=='accepted' and integrity['passed']
        need(row['accepted']==accepted,'Outcome accepted contradicts original exit/status/integrity')
        if row.get('service_status') is not None and (row.get('completion') or row.get('cycle')):
            ref=row.get('completion') or row['cycle']
            need(self.load(ref['path']).get('status')==row['service_status'],'Service status contradicts original generated receipt')
        if row.get('error') or row.get('exit_code') not in {0,None} or not integrity['passed'] or row.get('interrupted'):
            self.failures.append({'request_id':request['request_id'],'profile':row['profile'],'action':row['action'],'exit_code':row.get('exit_code'),'error':row.get('error'),'integrity_passed':integrity['passed']})
        return row

    def tickets(self, events):
        active=copy.deepcopy(self.initial_active); queue=[]; running=None; enqueued={}; starts={}; completed={}; admits={}; seals={}
        by_arm={k:[] for k in self.arms}; previous_tasks=[]
        for t in self.manifest['tasks']:
            previous_tasks.append(t['id'])
        for e in events:
            kind=e['kind']; key=(e.get('task'),e.get('arm'))
            if kind=='task_admitted':
                need(e['task'] not in admits and e['task'] in previous_tasks,'Task admitted twice/foreign')
                need(e['arms']==list(next(t for t in self.manifest['tasks'] if t['id']==e['task'])['arms']),'Task admitted arm set differs')
                index=previous_tasks.index(e['task'])
                need(all((task,alias) in seals for task in previous_tasks[:index] for alias in next(t for t in self.manifest['tasks'] if t['id']==task)['arms']),'Later task started before earlier pair self-seals')
                admits[e['task']]=e
            elif kind=='domain_review_requested':
                need(key in self.arms and key not in seals and e['task'] in admits and any(v['kind']=='repair_started' for v in by_arm[key]),'Domain request outside active D0 assignment')
                need(not any((enqueued[v]['task'],enqueued[v]['arm'])==key for v in queue),'Domain request crossed pending native ticket')
                need(sum(v['kind']=='domain_review_requested' for v in by_arm[key]) < self.manifest.get('source_domain_reviews',{}).get('max_requests_per_arm',4),'Domain review cap exceeded')
                req=self.ref(e['request']); self.ref(req['component_capsule'],parse=False)
                need(all(req[k]==e[k] for k in ['task','arm','profile','request_id']) and req['active_config']==active[key][e['profile']] and req['readset']==self.readset(key,active[key]),'Domain request owner/readset differs')
                by_arm[key].append(e)
            elif kind=='domain_review_admitted':
                need(key in self.arms and key not in seals and not any(enqueued[v]['task']==key[0] and enqueued[v]['arm']==key[1] for v in queue),'Domain admission crossed active ticket/self-seal')
                self.domain_update(e,active,events[:e['sequence']])
                by_arm[key].append(e)
            elif kind=='request_enqueued':
                need(key in self.arms and e['task'] in admits and key not in seals,'Ticket outside admitted arm')
                rid=e['request_id']; need(re.fullmatch('[0-9a-f]{32}',rid) and rid not in enqueued,'Duplicate/invalid request ID')
                need(not any((enqueued[v]['task'],enqueued[v]['arm'])==key for v in queue),'Overlapping own-arm ticket')
                request=self.load(self.root/'requests'/rid/'request.json')
                need(request=={k:v for k,v in e.items() if k not in META},'Queued request differs from original file')
                need(request['action'] in ACTIONS and request['readset']==self.readset(key,active[key]) and request['active_configs']==active[key],'Ticket readset/config differs')
                self.snapshot(request['source'],self.arms[key]['source_roots'])
                need(request['source']['roots']==self.initial[key]['roots'],'Ticket source root identity changed')
                a=self.arms[key]; wanted=a.get('profile_order',sorted(a['public_configs']))
                if request['action'] in {'diagnostic','final','retire'}: need(request['profiles']==wanted,'Bundle profile order differs')
                else: need(len(request['profiles'])==1 and request['profiles'][0] in a['public_configs'],'Single-profile review differs')
                if request.get('submission'):
                    self.ref({k:request['submission'][k] for k in ['path','sha256']},parse=False)
                enqueued[rid]=request; queue.append(rid); by_arm[key].append(e)
            elif kind=='request_started':
                rid=e['request_id']; need(running is None and queue and queue[0]==rid and rid not in starts,'FIFO request start/retry differs')
                need((enqueued[rid]['task'],enqueued[rid]['arm'])==key and finite(e['queue_wait_seconds']),'Request start owner/time differs')
                starts[rid]=e; running=rid; by_arm[key].append(e)
            elif kind=='request_finished':
                rid=e['request_id']; need(running==rid and queue[0]==rid and rid not in completed,'Request completion/retry differs')
                need(e['result_path']==str(self.root/'requests'/rid/'result.json'),'Result namespace differs')
                result=self.ref({'path':e['result_path'],'sha256':e['result_sha256']}); request=enqueued[rid]
                need((request['task'],request['arm']) == key,'Request finish owner differs')
                need(all(result[k]==request[k] for k in ['task','arm','request_id']) and [v['profile'] for v in result['outcomes']]==request['profiles'],'Result assignment/profiles differ')
                need(finite(result['finished_at_clock']) and finite(result['finished_at_unix']) and finite(result['service_wall_seconds']) and result['queue_wait_seconds']==starts[rid]['queue_wait_seconds'],'Result clock identity differs')
                need(result['native_execution_is_not_delivery_acceptance'] is True,'SDK-success scope declaration missing')
                for row in result['outcomes']: self.outcome(request,row,self.root/'requests'/rid/row['profile']/'outcome.json')
                completed[rid]=result; queue.pop(0); running=None; by_arm[key].append(e)
            elif kind=='self_sealed':
                need(key in self.arms and key not in seals and not any((enqueued[v]['task'],enqueued[v]['arm'])==key for v in queue),'Self-seal has pending/duplicate ticket')
                need(e['active_configs']==active[key],'Self-seal changed active config')
                seals[key]=e; by_arm[key].append(e)
            elif key in by_arm:
                by_arm[key].append(e)
        need(not queue and running is None and set(completed)==set(enqueued),'Unclosed/interrupted request remains')
        need(set(seals)==set(self.arms),'Not all arm self-seals exist')
        self.orphan_enqueue_artifacts=[]
        for folder in self.physical(self.root/'requests').iterdir():
            need(folder.is_dir() and re.fullmatch('[0-9a-f]{32}',folder.name),'Unexpected request namespace member')
            if folder.name not in enqueued:
                entries=list(folder.iterdir())
                need(all(p.is_file() and p.name in {'request.json','original-submission.json'} for p in entries),'Unregistered request has terminal/native artifacts')
                self.orphan_enqueue_artifacts.append({'path':str(self.root/'requests'/folder.name),'members':sorted(p.name for p in entries),'scope':'Retained pre-enqueue artifacts only; not an executed or accepted request'})
        self.active=active; self.enqueued=enqueued; self.starts=starts; self.completed=completed; self.by_arm=by_arm; self.seals=seals

    def arm_seals(self):
        summaries={}; members={}
        for key,a in self.arms.items():
            own=self.by_arm[key]; diag=[e for e in own if e['kind']=='request_enqueued' and e['action']=='diagnostic']
            need(1<=len(diag)<=DIAGNOSTICS,'Diagnostic cap/first request missing')
            first=diag[0]; rid=first['request_id']; result=self.completed[rid]
            prepared=[e for e in own if e['kind']=='d0_result_prepared']; anchors=[e for e in own if e['kind']=='repair_started']; locks=[e for e in own if e['kind']=='source_locked']
            need(len(prepared)==len(anchors)==len(locks)==1,'Unique D0 prepared/anchor/final lock required')
            prepared=prepared[0]; anchor=anchors[0]; locked=locks[0]; finished=next(e for e in own if e['kind']=='request_finished' and e['request_id']==rid)
            need(first['source']==self.initial[key] and first['profiles']==list(a.get('profile_order',sorted(a['public_configs']))),'D0 did not use exact paired initial')
            need(first['sequence']<self.starts[rid]['sequence']<prepared['sequence']<finished['sequence']<anchor['sequence']<locked['sequence'],'D0/anchor/source-lock order differs')
            need(prepared['request_id']==rid and prepared['source_sha256']==first['source']['content_sha256'] and prepared['readset_sha256']==digest(first['readset']),'Prepared D0 identity differs')
            need(prepared['result_path']==finished['result_path'] and prepared['result_sha256']==finished['result_sha256'],'Prepared/finished result hash differs')
            for field,limit in [('finished_at_clock',prepared['at_clock']),('finished_at_unix',prepared['at_unix'])]: need(result[field]<=limit+1,'D0 timestamp contradicts original preparation')
            for row in result['outcomes']:
                ref={'path':str(self.root/'requests'/rid/row['profile']/'outcome.json'),'sha256':self.sha(self.root/'requests'/rid/row['profile']/'outcome.json')}
                need(prepared['outcome_files'].get(row['profile'])==ref and not row.get('interrupted') and row['integrity']['passed'] is True,'D0 terminal integrity/outcome proof missing')
            expected={'deadline_clock':result['finished_at_clock']+LIMIT,'deadline_at_unix':result['finished_at_unix']+LIMIT,'repair_budget_seconds':LIMIT,'d0_request_id':rid,'d0_finished_at_clock':result['finished_at_clock'],'d0_finished_at_unix':result['finished_at_unix'],'d0_result':{'path':prepared['result_path'],'sha256':prepared['result_sha256']},'d0_source_sha256':first['source']['content_sha256'],'d0_readset_sha256':digest(first['readset'])}
            need(all(anchor.get(k)==v for k,v in expected.items()),'First-D0 deadline anchor reset or changed')
            unlock=[e for e in own if e['kind']=='repair_unlocked']; need(len(unlock)<=1,'Repair unlocked twice')
            for e in unlock:
                need(anchor['sequence']<e['sequence']<locked['sequence'] and e['anchor_sequence']==anchor['sequence'] and all(e[k]==anchor[k] for k in ['deadline_clock','deadline_at_unix']),'Unlock used a new/missing source window')
            for e in diag[1:]: need(unlock and unlock[0]['sequence']<e['sequence']<locked['sequence'],'Diagnostic outside original editable source phase')
            for e in own:
                if e['kind']=='domain_review_admitted': need(e['source_deadline_clock']==anchor['deadline_clock'],'Domain review reset source window')
            need(type(locked.get('source_deadline_compliant')) is bool and isinstance(locked.get('changed_after_deadline'),list) and locked['source_deadline_compliant']==(not locked['changed_after_deadline']),'Late-source flags contradict each other')
            need(finite(locked.get('deadline_enforcement_lateness_seconds')),'Source lock lateness missing')
            if not locked['source_deadline_compliant'] or locked.get('deadline_enforcement_lateness_seconds',0):
                self.late.append({'task':key[0],'arm':key[1],'source_deadline_compliant':locked['source_deadline_compliant'],'changed_after_deadline':locked['changed_after_deadline'],'enforcement_lateness_seconds':locked.get('deadline_enforcement_lateness_seconds')})
            final=self.capsule({'path':locked['source_manifest'],'sha256':locked['source_manifest_sha256']},a['source_roots'])
            base=self.root/'arms'/key[0]/key[1]
            need(locked['source_manifest']==str(base/'final-source/source.json'),'Final source capsule pointer differs')
            need(final['roots']==self.initial[key]['roots'] and final['content_sha256']==locked['source_sha256'],'Final source identity differs')
            seal=self.seals[key]
            need(self.load(base/'SELF-SEAL.json')==seal and seal['source_sha256']==final['content_sha256'] and locked['sequence']<seal['sequence'],'Self-seal/file/final source differs')
            claim=self.ref({'path':seal['claim_path'],'sha256':seal['claim_sha256']})
            need(seal['claim_path']==str(base/'self-claim.json') and isinstance(claim.get('statement'),str) and claim['statement'].strip(),'Missing original self-claim')
            outcomes=[row for e in own if e['kind']=='request_finished' for row in self.completed[e['request_id']]['outcomes']]
            selected={}
            for profile in a['public_configs']:
                finals=[o for o in outcomes if o['profile']==profile and o['action']=='final']; need(finals,'Missing final public profile')
                last=finals[-1]; later=[o for o in outcomes if o['profile']==profile and o['action']=='finish-review' and o['started_at_unix']>=last['finished_at_unix']]
                selected[profile]=later[-1] if later else last
                candidates=[o for o in outcomes if o['profile']==profile and o['action'] in {'final','retire'} and o.get('service_output')]; need(candidates,'No final retirement candidate')
                last_resource=candidates[-1]; allowed={str(path(last_resource['service_output'])/'resources.json'),str(path(last_resource['envelope_record'])/'error-recovery/resources.json')}
                ref=seal['retirement'][profile]; need(ref['path'] in allowed,'Retirement proof belongs to an older/foreign outcome')
                resource=self.ref(ref); need(all(k in resource and not resource[k] for k in ['cleanup_errors','remaining_devices','remaining_directories']),'Positive resource closure missing')
            need(seal['final_outcomes']==selected and set(seal['retirement'])==set(a['public_configs']),'Self-seal final profile selection differs')
            accepted=all(o['accepted'] for o in selected.values()) and locked['source_deadline_compliant']
            need(type(seal['public_service_accepted']) is bool and seal['public_service_accepted']==accepted,'Public accepted contradicts final outcomes/source deadline')
            wall=seal['own_delivery_wall_seconds']; before=self.events_list[seal['sequence']-1]['at_clock']
            need(finite(wall) and max(0,before-first['at_clock'])<=wall<=seal['at_clock']-first['at_clock'],'Own-delivery wall does not end within self-seal interval')
            for e in own:
                if e['kind']=='request_enqueued':
                    if e['action']=='final': need(e['sequence']>locked['sequence'],'Final collection preceded source lock')
                    if e['sequence']>locked['sequence']: need(e['source']==final,'Request changed locked final source')
                    if not unlock or e['sequence']<unlock[0]['sequence']: need(e['source']==self.initial[key],'Source changed before original repair unlock')
                    need(e['sequence']<seal['sequence'],'Public request after self-seal')
            if not unlock: need(final==self.initial[key],'Final source changed without a repair unlock')
            summaries['/'.join(key)]={'source_unchanged':final['files']==self.initial[key]['files'],'public_service_accepted':accepted,'source_deadline_compliant':locked['source_deadline_compliant'],'diagnostic_requests':len(diag),'own_delivery_wall_seconds':wall,'self_seal_sequence':seal['sequence']}
            p=base/'SELF-SEAL.json'; members['/'.join(key)]={'path':str(p),'sha256':self.sha(p),'source_sha256':seal['source_sha256']}
        return summaries,members

    def hidden(self,events,members,required):
        cohort=[e for e in events if e['kind']=='cohort_sealed']; auth=[e for e in events if e['kind']=='hidden_authorized']; validated=[e for e in events if e['kind']=='hidden_contexts_validated']
        need(len(cohort)==1 and cohort[0]['members']==members and self.load(self.root/'COHORT-SEAL.json')==cohort[0],'Unique complete cohort seal differs')
        need(cohort[0]['sequence']>max(e['sequence'] for e in self.seals.values()),'Cohort sealed before all final source/self-claims')
        need(len(auth)<=1,'Hidden authorized more than once')
        if not auth:
            need(not required and not validated,'Hidden authorization absent')
            return {'cohort_sequence':cohort[0]['sequence'],'hidden_authorized':False}
        auth=auth[0]
        need(auth['sequence']>cohort[0]['sequence'] and auth['cohort_sha256']==self.sha(self.root/'COHORT-SEAL.json'),'Hidden authorization precedes/changes cohort')
        need(len(validated)==1 and validated[0]['sequence']>auth['sequence'] and validated[0]['authorization_sequence']==auth['sequence'],'Hidden context validation order differs')
        authorization=self.load(self.root/'HIDDEN-AUTHORIZATION.json')
        need(set(authorization)=={'authorization','hidden_configs','barrier_wait_seconds'},'Hidden authorization schema differs')
        need(authorization['authorization']==auth and set(authorization['hidden_configs'])=={t['id'] for t in self.manifest['tasks']},'Hidden authorization file differs')
        for t in self.manifest['tasks']: need(set(authorization['hidden_configs'][t['id']])==set(t['arms']),'Hidden arm membership differs')
        public_contexts=[]
        for key,a in self.arms.items():
            for ref in self.active[key].values():
                c=self.ref(ref); public_contexts += [path(v) for v in [c.get('review_store'),c.get('source_review_store'),c.get('workflow',{}).get('root')] if v]
        used=[]
        for key,a in self.arms.items():
            entries=authorization['hidden_configs'][key[0]][key[1]]
            need(set(entries)==set(a['hidden_configs']),'Hidden profile set differs')
            for profile,original in a['hidden_configs'].items():
                entry=entries[profile]; need(entry['path']==original,'Hidden config pointer differs')
                c=self.ref({'path':original,'sha256':entry['sha256']})
                need(c['source_roots']==a['source_roots'] and c['resources']['root'] in a['resource_roots'] and c['resources'].get('max_simulators',1)==1,'Hidden changed source/resource bound')
                roots=[path(v) for v in [c.get('review_store'),c.get('source_review_store'),c.get('workflow',{}).get('root')] if v]
                need(c.get('review_store') and c.get('source_review_store') and (self.manifest['tools'][a['tool']]['api']!='stateful-default' or c.get('workflow',{}).get('root')),'Fresh hidden context names missing')
                need(entry['context_roots']==list(map(str,roots)),'Hidden context declaration differs')
                blocked=public_contexts+[self.root,*map(path,a['source_roots']),*map(path,a['resource_roots'])]
                need(not any(intersects(r,other) for r in roots for other in blocked),'Hidden reused public/source/resource context')
                need(not any(intersects(r,other) and owner!=key for r in roots for owner,other in used),'Hidden contexts overlap another arm')
                used.extend((key,r) for r in roots)
            need(authorization['barrier_wait_seconds']['/'.join(key)]==auth['at_unix']-self.seals[key]['at_unix'],'Hidden barrier wait changed')
        need(set(authorization['barrier_wait_seconds'])==set(members),'Hidden barrier wait membership differs')
        return {'cohort_sequence':cohort[0]['sequence'],'hidden_authorized':True,'authorization_sequence':auth['sequence'],'context_validation_sequence':validated[0]['sequence'],'fresh_context_history_replay':'Names/disjointness and original authorization declaration only; historical emptiness is not inferred from the populated restore.'}

    def verify(self,require_hidden):
        self.prerequisites(); events=self.events(); self.events_list=events
        self.tickets(events); arms,members=self.arm_seals(); barrier=self.hidden(events,members,require_hidden)
        return {'version':1,'status':'verified','controller_sha256':HELPER_SHA,'domain_transport_sha256':DOMAIN_SHA,'event_count':len(events),'request_count':len(self.enqueued),'arms':arms,'barrier':barrier,'retained_failed_outcomes':self.failures,'retained_pre_enqueue_artifacts':self.orphan_enqueue_artifacts,'late_records':self.late,'domain_admission_count':self.domain_admissions,'scope':'Recorded controller/source-capsule/claim/service/resource/barrier integrity only. No new SDK, product grade, live-source validity, fresh-context-emptiness proof, source-author/independent-grader identity proof or assurance against bypassing the recorded controller.'}


def verify_run(resolver, original_run_root, *, require_hidden_authorization=True):
    """Return verified/failed without mutating the resolver, run, clock or oracle."""
    audit=None; errors=[]; result=None
    try:
        audit=Audit(resolver,original_run_root)
        result=audit.verify(require_hidden_authorization)
    except (ValueError,KeyError,OSError,TypeError,IndexError,AttributeError) as error:
        errors.append({'type':type(error).__name__,'message':str(error)})
    if audit is not None:
        try: audit.finish()
        except (ValueError,KeyError,OSError,TypeError) as error: errors.append({'type':type(error).__name__,'message':'Post-replay verification: '+str(error)})
    if errors:
        return {'version':1,'status':'failed','errors':errors,'scope':'Integrity failure retained; no repair, rewrite, excluded sample or product verdict.'}
    return result
