"""Portable original-fact replay through a pinned Resolver; no original fallback.

Fresh isolated backend processes are pure evaluations, not native/SDK runs.
Actual data requires a separately verified ALL30 CAUSE admission before any
plan/observation/submission/report/PNG bytes are opened.
"""
import base64
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys


FREEZES={'A':'e04a0db08a4a617c372e1f3f9a05dc3c1042fb53e59d48e08f189f03aaf302c4',
         'B':'6dac704edfb15491e59648ab0259f465469f81ed0f7b61d7cedf0e91e47140cf'}
MODULES={'review_contract','native_checks','native_pixels','design_contract','observation_contract',
         'native_geometry','action_guard','scroll_coverage','coverage_domain'}


def need(value,message):
    if not value:raise ValueError(message)


def sha(raw):return hashlib.sha256(raw).hexdigest()


def digest(value):return sha(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode())


def strict_json(raw):
    def pairs(items):
        out={}
        for k,v in items:need(k not in out,'Duplicate JSON key');out[k]=v
        return out
    def constant(_):raise ValueError('Nonfinite JSON')
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=constant)


def absolute(value):
    need(isinstance(value,str) and value.startswith('/') and '\x00' not in value and '\\' not in value,'Canonical original absolute key required')
    p=PurePosixPath(value);need(str(p)==value and all(v not in {'.','..'} and v.casefold()!='.git' for v in value.split('/')),'Unsafe original key')
    need(p.name!='MAPPING.json' and '/anonymous-map/' not in value and '/blind-quality/grades/' not in value,'Grade/mapping bodies are outside this replay API')
    return p


def relative(value):
    need(isinstance(value,str) and value and '\\' not in value and '\x00' not in value,'Canonical relative PNG member required')
    p=PurePosixPath(value);need(not p.is_absolute() and str(p)==value and all(v not in {'.','..'} and v.casefold()!='.git' for v in value.split('/')),'Unsafe relative member')
    return p


class Access:
    def __init__(self,reader):self.reader=reader;self.seen={};self.trees={}
    def raw(self,p):
        p=str(absolute(str(p)));raw=self.reader.read_bytes(p);actual=sha(raw)
        need(p not in self.seen or self.seen[p]==actual,'Original changed during replay');self.seen[p]=actual;return raw
    def pinned(self,ref,*,parse=True):
        need(isinstance(ref,dict) and set(ref)>={'path','sha256'} and re.fullmatch('[0-9a-f]{64}',ref['sha256']),'Explicit original SHA256 reference required')
        raw=self.raw(ref['path']);need(sha(raw)==ref['sha256'],'Original pin differs: '+ref['path'])
        if 'bytes' in ref:need(type(ref['bytes']) is int and len(raw)==ref['bytes'],'Original byte count differs')
        if 'canonical_sha256' in ref:need(digest(strict_json(raw))==ref['canonical_sha256'],'Canonical hash domain differs')
        return strict_json(raw) if parse else raw
    def directory(self,p):
        p=str(absolute(str(p)));physical=self.reader.directory(p);need(isinstance(physical,Path),'Verified directory Path required')
        names=set()
        for item in physical.rglob('*'):
            need(not item.is_symlink(),'Symlink in verified restored namespace')
            if item.is_file():names.add(str(relative(item.relative_to(physical).as_posix())))
            else:need(item.is_dir(),'Nonregular restored namespace member')
        need(p not in self.trees or self.trees[p]==names,'Restored namespace changed');self.trees[p]=names;return physical,names
    def recheck(self):
        for p,expected in self.seen.items():need(self.reader.hash(p)==expected,'Original changed after replay')
        for p in list(self.trees):self.directory(p)


def authorize(access,packet,packet_ref,admission_ref):
    kind=packet.get('data_scope')
    if kind=='synthetic-host-only':
        refs=[packet[k] for k in ['plan','lock','policy','observation','submission','capture_request','capture_receipt']]
        refs+=list(packet.get('expected_artifacts',{}).values())
        need(all(absolute(r['path']).is_relative_to('/recorded') for r in refs)
             and absolute(packet['native_root']).is_relative_to('/recorded'),'Synthetic mode rejects actual study keys')
        return 'synthetic-only'
    need(kind=='actual-after-all30-cause' and admission_ref is not None,'Actual replay is blocked until root supplies verified ALL30 CAUSE admission')
    admission=access.pinned(admission_ref)
    need(admission.get('kind')=='verified-all30-cause-replay-admission-v1' and admission.get('actual_replay_authorized') is True,
         'Explicit root ALL30 CAUSE replay admission required')
    allowed=admission.get('allowed_packet_refs')
    need(isinstance(allowed,list) and packet_ref in allowed,'Root admission does not authorize this exact replay packet pin')
    verification=access.pinned(admission['verification'])
    need(verification.get('status')=='verified' and verification.get('phase')=='cause' and verification.get('groups')==15
         and verification.get('distinct_contexts')==30 and verification.get('index')==admission['cause_index'],
         'Separately verified ALL30 CAUSE record-barrier report required')
    access.pinned(admission['cause_index'],parse=False)
    return 'externally-admitted-after-all30-cause'


def code_job(access,inventory_ref,worker_ref,backend):
    need(backend in FREEZES,'Explicit frozen backend A or B required')
    inventory=access.pinned(inventory_ref);need(inventory.get('kind')=='externally-pinned-isolated-evaluator-code-inventory' and inventory.get('version')==1,'Unsupported code inventory')
    tool=inventory['backends'][backend]
    need(tool['freeze']['sha256']==FREEZES[backend],'Exact original frozen backend identity required')
    frozen=access.pinned(tool['freeze']);files=tool['files'];need(set(files)=={'scripts/'+m+'.py' for m in MODULES},'Exact pure backend module inventory required')
    physical,names=access.directory(absolute(tool['root'])/'scripts')
    need(names=={m+'.py' for m in MODULES},'Uninventoried or missing backend import file')
    code_files=[]
    for rel,row in files.items():
        need(row['path']==str(absolute(tool['root'])/rel) and row['sha256']==frozen['files'][rel],'Backend code differs from exact frozen inventory')
        access.pinned(row,parse=False);code_files.append({'physical_path':str(physical/PurePosixPath(rel).name),'sha256':row['sha256'],'bytes':row['bytes']})
    runtime=inventory['runtime'];runtime_root,names=access.directory(absolute(runtime['root'])/'PIL')
    need(names=={str(PurePosixPath(k).relative_to('PIL')) for k in runtime['files']},'Uninventoried or missing Pillow runtime file')
    for rel,row in runtime['files'].items():
        need(row['path']==str(absolute(runtime['root'])/relative(rel)),'Foreign runtime code pin')
        access.pinned(row,parse=False);code_files.append({'physical_path':str(runtime_root/PurePosixPath(rel).relative_to('PIL')),'sha256':row['sha256'],'bytes':row['bytes']})
    # Current-host extension: manylinux wheels may use sibling *.libs paths.
    # Every support file and its complete layout is separately pinned; the
    # unchanged child worker verifies the appended files under runtime_root.
    support=runtime.get('support_files',{})
    support_tops={PurePosixPath(k).parts[0] for k in support}
    for top in sorted(support_tops):
        need(re.fullmatch('[A-Za-z0-9_.-]+[.]libs',top),'Unregistered runtime support namespace')
        support_root,support_names=access.directory(absolute(runtime['root'])/top)
        selected={k:v for k,v in support.items() if PurePosixPath(k).parts[0]==top}
        need(support_root.parent==runtime_root.parent and support_names=={str(PurePosixPath(k).relative_to(top)) for k in selected},
             'Runtime support layout differs or contains uninventoried files')
        for rel,row in selected.items():
            need(row['path']==str(absolute(runtime['root'])/relative(rel)),'Foreign runtime support pin')
            access.pinned(row,parse=False)
            code_files.append({'physical_path':str(support_root/PurePosixPath(rel).relative_to(top)),'sha256':row['sha256'],'bytes':row['bytes']})
    # Host runtime is explicit, separate from historical source/data validity.
    need(sha(Path(sys.executable).read_bytes())==runtime['interpreter']['sha256'] and sys.version==runtime['version'],
         'Replay interpreter differs from separately pinned compatible runtime')
    access.pinned(worker_ref,parse=False);worker_dir,_=access.directory(absolute(worker_ref['path']).parent)
    worker=worker_dir/absolute(worker_ref['path']).name
    return {'backend_root':str(physical),'runtime_root':str(runtime_root.parent),'code_files':code_files},worker


def execute(job,worker):
    process=subprocess.run([sys.executable,'-I','-S','-B',str(worker)],input=json.dumps(job,ensure_ascii=False,allow_nan=False).encode(),
                           stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=90,check=False)
    need(bool(process.stdout),'Isolated replay returned no JSON: '+process.stderr.decode(errors='replace')[-800:])
    value=strict_json(process.stdout);need(process.returncode==0 and value.get('status')=='replayed',
        'Isolated unchanged backend rejected input: '+str(value.get('error',process.stderr.decode(errors='replace')[-800:])))
    return value['result']


def replay(reader,packet_ref,inventory_ref,worker_ref,*,cause_admission_ref=None):
    """Pure replay; returns verified/failed/unsupported without changing originals.

    Actual gates are checked before original fact or expected-report bodies.
    Native source-domain and source-responsibility evaluation stay unsupported.
    """
    access=Access(reader)
    try:
        packet=access.pinned(packet_ref);need(packet.get('kind')=='original-fact-evaluator-replay-packet-v1' and packet.get('version')==1,'Unsupported replay packet')
        authorization=authorize(access,packet,packet_ref,cause_admission_ref)
        job,worker=code_job(access,inventory_ref,worker_ref,packet['backend'])
        inputs={}
        for key in ['plan','lock','policy','observation','submission']:
            raw=access.pinned(packet[key],parse=False);inputs[key]={'raw_base64':base64.b64encode(raw).decode(),'sha256':sha(raw)}
        need('canonical_sha256' in packet['lock'] and 'canonical_sha256' in packet['policy'],'Separate canonical design/policy pins required')
        native=absolute(packet['native_root']);need(packet['observation']['path']==str(native/'observation.json'),'Original native observation namespace differs')
        need(packet['capture_request']['path']==str(native.parent/'request.json')
             and packet['capture_receipt']['path']==str(native.parent/'result.json'),'Original capture request/receipt namespace differs')
        request=access.pinned(packet['capture_request']);receipt=access.pinned(packet['capture_receipt'])
        need(all(receipt.get(k)==v for k,v in request.items()) and receipt.get('observation_sha256')==packet['observation']['sha256']
             and receipt.get('image_hashes')==packet['image_hashes']
             and receipt.get('parent_plan_sha256')==digest(strict_json(base64.b64decode(inputs['plan']['raw_base64']))),
             'Original capture request/receipt/plan/native/image binding differs')
        capture_root,capture_names=access.directory(native.parent);native_root,native_names=access.directory(native)
        need(native_root.parent==capture_root,'Restored native/capture relative layout differs')
        images=packet['image_hashes'];need(isinstance(images,dict),'Explicit original image inventory required')
        need({n for n in native_names if n.lower().endswith('.png')}==set(images),'Original PNG inventory differs')
        for name,pin in images.items():
            raw=access.pinned({'path':str(native/relative(name)),'sha256':pin},parse=False)
            need(raw.startswith(b'\x89PNG\r\n\x1a\n'),'Original image is not PNG bytes')
        observation=strict_json(base64.b64decode(inputs['observation']['raw_base64']))
        for snapshot in observation.get('snapshots',[]):
            if 'screenshot' in snapshot:
                need(str(relative(snapshot['screenshot'])) in images,'Snapshot PNG lacks its original byte pin')
        domain=any(name in capture_names for name in ['coverage-domain-prepared.json','native/coverage-domain-input.json','native/coverage-domain-binding.json'])
        domain=domain or 'coverage-domain-prepared.json' in request.get('input_hashes',{})
        if domain:
            access.recheck()
            return {'status':'unsupported','provenance_bytes_verified':True,'backend_native_replay':'unsupported_original_production_domain_resolution',
                    'provenance_scope':'Explicit supplied input byte pins and request/receipt/native/image bindings only; complete acquisition/domain chain is separate.',
                    'source_responsibility_replay':'unsupported','current_source_delivery_verified':False,
                    'reason':'Unchanged coverage_domain backend resolves original production source namespaces. No original-path access, monkeypatch or replacement P is allowed.',
                    'additional_evidence_scope':'A separately labeled reader-aware verifier could check original capsule/request/provider/domain/compile-action proofs; it would not be this unchanged backend historical live-path test.',
                    'authorization':authorization,'original_files_checked':len(access.seen)}
        job.update(mode='evaluate',platform=packet['platform'],inputs=inputs,native_root=str(native_root),capture_root=str(capture_root),
                   lock_canonical_sha256=packet['lock']['canonical_sha256'],policy_canonical_sha256=packet['policy']['canonical_sha256'])
        rebuilt=execute(job,worker);comparisons={}
        for role,ref in packet.get('expected_artifacts',{}).items():
            need(role in {'catalog','manual','report'},'Unsupported expected artifact role')
            original=access.pinned(ref)
            if role=='catalog' and 'catalog_sha256' in original:
                expected={k:v for k,v in original.items() if k!='catalog_sha256'}
                need(original['catalog_sha256']==digest(expected),'Original catalog self-pin differs')
            else:expected=original
            need(expected==rebuilt[role],'Rebuilt '+role+' differs from original report; no verdict/provenance projection allowed')
            comparisons[role]='exact_original_values'
        access.recheck()
        return {'status':'verified','authorization':authorization,'provenance_bytes_verified':True,'backend_native_replay':'reproduced',
                'provenance_scope':'Explicit supplied input byte pins and request/receipt/native/image bindings only; complete acquisition/domain chain is separate.',
                'backend':packet['backend'],'backend_results':rebuilt,'comparisons':comparisons,'source_responsibility_replay':'unsupported',
                'current_source_delivery_verified':False,'original_files_checked':len(access.seen),
                'limits':'Frozen native/visual binding only. Actuals remain reviewer input; U is retained. No independent source responsibility, current-source eligibility, SDK freshness, product cause truth or delivery is inferred.'}
    except (ValueError,KeyError,TypeError,OSError,subprocess.TimeoutExpired) as exc:
        return {'status':'failed','provenance_bytes_verified':False,'backend_native_replay':'not_certified','source_responsibility_replay':'unsupported',
                'current_source_delivery_verified':False,'error':{'type':type(exc).__name__,'message':str(exc)}}
