import copy
import hashlib
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT.parent/'publication-batch-review'
DISPATCH=ROOT.parent/'publication-dispatch-review'
PRIOR=ROOT.parent/'publication-batch-v4-review'
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
batch=load(ROOT/'revision-v8/alarm-material-tools-v8/batch.py','review_batch_v8')
dispatch=load(ROOT/'revision-v8/prepare_alarm_dispatch_v4.py','review_dispatch_v4')
def sha(raw):return hashlib.sha256(raw).hexdigest()

class Reader:
    def __init__(self,*unused):self.reads=[];self.overlay={};self.directories={}
    def checked(self,value):
        path=Path(value)
        if not path.is_absolute()or'..'in path.parts or not any(path.is_relative_to(base)for base in [ROOT,OLD,DISPATCH,PRIOR]):raise ValueError('Only named closed synthetic review roots allowed')
        if any(p.is_symlink()for p in [path,*path.parents]):raise ValueError('Synthetic nofollow path required')
        return path
    def read_bytes(self,value):
        path=self.checked(value);self.reads.append(str(path));return self.overlay[str(path)]if str(path)in self.overlay else path.read_bytes()
    def read_json(self,value):return batch.strict_json(self.read_bytes(value))
    def hash(self,value):return sha(self.read_bytes(value))
    def directory(self,value):
        path=self.checked(self.directories.get(str(value),str(value)))
        if not path.is_dir():raise FileNotFoundError(str(path))
        return path
reader=Reader()
cause={'path':str(OLD/'fixtures/cause/INDEX.json'),'sha256':reader.hash(OLD/'fixtures/cause/INDEX.json')}

def put(path,value,readonly=False):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);raw=batch.encoded(value)
    if path.exists():
        if path.read_bytes()!=raw:raise ValueError('Retained synthetic fixture bytes differ; use a fresh path')
        return{'path':str(path),'sha256':sha(raw)}
    with path.open('xb')as stream:stream.write(raw)
    if readonly:path.chmod(0o444)
    return{'path':str(path),'sha256':sha(raw)}
def ref(path):return{'path':str(path),'sha256':reader.hash(path)}
def entry(original_ref,pointer,text,kind='claimed_provenance_locator'):
    d=sha(text.encode());return{'original_ref':original_ref,'pointer':pointer,'member_kind':'string_value','original_utf8_sha256':d,'codepoint_length':len(text),'classification':kind,
        'contains_prose':False,'whole_container_metadata_permission':False,'reference_validated':False,'evidence_credit':False,'projection_authorized':False,
        'identity_spans':[{'start':0,'end':len(text),'unit':'unicode_codepoint','original_utf8_sha256':d,'span_kind':'complete_canonical_locator'if text.startswith('/')else'complete_execution_identifier'}]}

def authority(name,root,documents):
    base=ROOT/'fixtures'/name
    if (base/'AUTHORITY.json').exists():
        reference=ref(base/'AUTHORITY.json');existing=batch.pinned(reader,reference)
        catalog=batch.pinned(reader,existing['catalog_ref'])
        if existing['original_root']!=str(root)or batch.json_text(catalog['documents'],sort_keys=True)!=batch.json_text(documents,sort_keys=True):
            raise ValueError('Retained synthetic authority membership differs')
        return reference
    catalog={'version':1,'kind':'synthetic-metadata-responsibility-catalog','documents':documents,'uncertain_locations':[]}
    catalog_ref=put(base/'catalog/CATALOG.json',catalog,True)
    def seal(path,member,extras=None):
        metadata={'path':member['path'],'sha256':member['sha256'],'size_bytes':len(reader.read_bytes(member['path'])),'sealed_mode':'0444'}
        return put(path,{'version':1,'kind':'synthetic-independent-metadata-seal','artifact_manifest':[metadata],**(extras or{})},True)
    catalog_seal=seal(base/'catalog/SEAL.json',catalog_ref)
    originals=[doc['original_ref']for doc in documents]
    approved=[{'original_ref':doc['original_ref'],'pointer':e['pointer'],'member_kind':e['member_kind'],'location_sha256':batch.lens.canonical_sha(e,batch.m.projection)}for doc in documents for e in doc['locations']]
    approval={'version':1,'kind':'independent-worker-claim-metadata-responsibility-approval','catalog_seal':catalog_seal,'catalog_ref':catalog_ref,
        'original_document_refs':originals,'approved_locations':approved,'unapproved_locations':[],'all_originals_reverified_unchanged':True,'scope_limits':['Synthetic whole-scalar formatting only; no evidence or quality credit']}
    approval_ref=put(base/'approval/APPROVAL.json',approval,True)
    approval_seal=seal(base/'approval/SEAL.json',approval_ref,{'catalog_ref':catalog_ref,'catalog_seal':catalog_seal,'approval_ref':approval_ref})
    auth={'version':1,'kind':'externally-pinned-worker-metadata-disclosure-authority','original_root':str(root),'catalog_seal':catalog_seal,'catalog_ref':catalog_ref,
        'approval_seal':approval_seal,'approval_ref':approval_ref,'original_document_refs':originals,'lens_ref':ref(ROOT/'vendor/lens.py'),
        'lens_author_freeze':ref(ROOT/'vendor/AUTHOR-FREEZE.json'),'reference_validated':False,'evidence_credit':False,'quality_credit':False,
        'scope':'Disclosure metadata only; no fact edits, target validation or product/treatment credit.'}
    return put(base/'AUTHORITY.json',auth,True)

def study_authority(study,name):
    docs=[]
    for task in ['T1','T2','T3','T4','T5']:
        for arm in ['A','B']:docs.append({'original_ref':ref(study.run/'arms'/task/arm/'self-claim.json'),'locations':[]})
    return authority(name,study.root,docs)
