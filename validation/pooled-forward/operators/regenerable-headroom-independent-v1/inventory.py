#!/usr/bin/env python3
"""Read-only finite regenerable-cache inventory. Contains no deletion/SDK API."""
import hashlib
import json
import os
from pathlib import Path
import stat
import time

R=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/pooled-forward')
OUT=R/'operators/regenerable-headroom-independent-v1'
SPEC=R/'cache/publication-archives/closed-business-main-v2/SPEC.json'
PLAN=R/'operators/main-preservation-plan-v3/PLAN.json'
NAMES={'.git','.gradle','build','.build'}
OWNER_SHA='d62df53bd1dee9691e40e34e02b6e8006e07258b8dff46053b656ec9ceb18a55'


def need(ok,why):
    if not ok:raise ValueError(why)
def safe(raw):
    p=Path(raw);need(p.is_absolute()and str(p)==os.path.normpath(str(p)),'Canonical absolute path required')
    need(not any(q.is_symlink()for q in [p,*p.parents]),'Symlink ancestor is not physical ownership')
    return p
def sha(p):
    h=hashlib.sha256()
    with safe(p).open('rb')as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def ref(p):return{'path':str(p),'sha256':sha(p)}
def load(p):return json.loads(safe(p).read_bytes())
def pinned(p,wanted):need(sha(p)==wanted,'Input pin differs: '+str(p));return load(p)
def under(p,root):return p==root or p.is_relative_to(root)
def intersects(a,b):return under(a,b)or under(b,a)
def write(name,value):
    p=OUT/name
    with p.open('x')as f:json.dump(value,f,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
    p.chmod(0o444);return ref(p)
def identity(p):
    s=p.lstat();return{'device':s.st_dev,'inode':s.st_ino,'mode':format(stat.S_IMODE(s.st_mode),'04o'),'uid':s.st_uid,'gid':s.st_gid,'nlink':s.st_nlink,'size_bytes':s.st_size,'allocated_file_bytes':s.st_blocks*512,'mtime_ns':s.st_mtime_ns,'ctime_ns':s.st_ctime_ns}
def tree(root):
    stack=[root];rows=[]
    while stack:
        p=stack.pop();s=p.lstat();row={'path':str(p),**identity(p)}
        if stat.S_ISDIR(s.st_mode):row['kind']='directory';stack.extend(Path(e.path)for e in sorted(os.scandir(p),key=lambda x:x.name,reverse=True))
        elif stat.S_ISREG(s.st_mode):row['kind']='regular'
        elif stat.S_ISLNK(s.st_mode):row.update(kind='symlink-metadata-only',target=os.readlink(p))
        else:row['kind']='special-metadata-only'
        rows.append(row)
    return rows
def latest_meter(path):
    with path.open('rb')as f:
        f.seek(0,2);size=f.tell();f.seek(max(0,size-262144));raw=f.read()
    for line in reversed(raw.splitlines()):
        try:d=json.loads(line)
        except (ValueError,UnicodeDecodeError):continue
        if type(d)is dict and 'total_allocated_bytes'in d:return{'path':str(path),'size_at_read':size,'last_complete_sample':d}
    return{'path':str(path),'last_complete_sample':None}


def main():
    start=time.time();spec=pinned(SPEC,'01d572c64bc51a8e905b0eeb57b694f4ef2f9f395ead373f3163439ed08f9e10')
    plan=pinned(PLAN,'ff9568246013be8bb2962543be256bb2203fb4ed7145108c292c44321e52c558')
    owner=R/'cache/OWNER.json';need(sha(owner)==OWNER_SHA,'Cache marker differs');cache=R/'cache';ci=identity(cache)
    need((ci['device'],ci['inode'])==(16777232,26682812),'Cache physical identity differs')
    main_workspaces=[safe(x)for x in plan['workspace_exclusions']];need(len(main_workspaces)==20,'Expected exact20 current workspaces')
    rejected=[R/f'cache/business-rejected-cohort1/{t}/{a}/workspace'for t in ['T1','T2']for a in ['A','B']]
    rejected +=[R/f'cache/business-rejected-cohort1/initial/{t}/workspace'for t in ['T1','T2']]
    workspaces=main_workspaces+rejected
    protected_paths={safe(x['path'])for x in spec['files']}|{safe(x)for x in plan['subject_files']}
    protected_paths|={safe(x['path'])for x in plan['additional_required_refs']}
    protected_roots={safe(x)for x in plan['source_roots']+plan['protected_plain_code_roots']}
    workspace_proofs=[];source_root_receipts=[]
    for w in workspaces:
        safe(w);need(w.is_dir()and under(w,cache),'Task cache workspace absent or foreign')
        records={name:ref(w/name)for name in ['setup.json','STOCK-COPY.json','commands.json']if(w/name).is_file()}
        need(set(records)=={'setup.json','STOCK-COPY.json','commands.json'},'Preserve exact setup/stock/command evidence')
        protected_paths.update(Path(x['path'])for x in records.values());stock=load(w/'STOCK-COPY.json');old=safe(stock['workspace'])
        roots=[]
        for original in stock['production_source_roots']:
            original=safe(original);need(under(original,old),'Stock source-role metadata escapes historical workspace')
            current=w/original.relative_to(old);safe(current);need(current.is_dir(),'Current production source-role root absent')
            roots.append(str(current));protected_roots.add(current)
        dep=stock.get('private_jdk_dependency',{}).get('path')
        if dep:
            p=safe(dep);need(under(p,old),'Historical dependency outside workspace');protected_paths.add(w/p.relative_to(old))
        workspace_proofs.append({'path':str(w),'physical_identity':identity(w),'scope':'main-explicit-workspace-exclusion'if w in main_workspaces else'root-authorized-rejected-cohort-workspace-inventory-only',
            'metadata_refs_retained':records,'historical_embedded_workspace':str(old),'production_source_roots_preserved':roots,
            'historical_paths_rewritten':False,'ownership_basis':'Exact task cache marker/dev/inode + canonical no-symlink physical descendants; original producer receipts are evidence, not deletion authority.'})
    # Every current production source member is protected by physical inode too.
    for root in protected_roots:
        if root.is_dir()and under(root,cache):
            for row in tree(root):
                if row['kind']=='regular':protected_paths.add(Path(row['path']))
    # All source seals and compiler evidence are kept; main SPEC includes them.
    protected_inodes={};missing=[]
    for p in sorted(protected_paths):
        if not p.exists():missing.append(str(p));continue
        s=p.lstat()
        if stat.S_ISREG(s.st_mode):protected_inodes.setdefault((s.st_dev,s.st_ino),[]).append(str(p))
    targets=[];dd_proofs=[]
    for record in plan['compile_scratch_exclusions']:
        cp=Path(record['command_ref']['path']);need(ref(cp)==record['command_ref'],'Compiler command pin changed');d=load(cp);argv=d['argv'];target=safe(record['path'])
        need(argv[:2]==['xcodebuild','build-for-testing']and argv.count('-derivedDataPath')==1 and argv[argv.index('-derivedDataPath')+1]==str(target),'Not exact compiler-declared scratch')
        need(target==cp.parent/'DerivedData'and str(target)in plan['regenerable_cache_exclusions'],'Scratch path differs from explicit plan')
        for flag in ['-project','-resultBundlePath']:
            need(argv.count(flag)==1 and not under(safe(argv[argv.index(flag)+1]),target),'Compile project/result proof overlaps scratch')
        need(cp in protected_paths,'Compiler command must be protected by main selection')
        proof={'path':str(target),'command_ref':record['command_ref'],'original_project':argv[argv.index('-project')+1],'original_xcresult':argv[argv.index('-resultBundlePath')+1],'scope':record['scope']}
        dd_proofs.append(proof);targets.append((target,'main-compiler-DerivedData',proof))
    for w in workspaces:
        stack=[w]
        while stack:
            p=stack.pop()
            for e in sorted(os.scandir(p),key=lambda x:x.name):
                q=Path(e.path);s=q.lstat()
                if not stat.S_ISDIR(s.st_mode):continue
                if any(under(q,x)for x in protected_roots):continue
                if e.name in NAMES:
                    descriptors=[]
                    for parent in [q.parent,*q.parents]:
                        if not under(parent,w):break
                        for name in ['Package.swift','build.gradle.kts','build.gradle','settings.gradle.kts','settings.gradle']:
                            d=parent/name
                            if d.is_file()and not d.is_symlink():descriptors.append(ref(d))
                    targets.append((q,'main-workspace-regenerable-candidate'if w in main_workspaces else'rejected-workspace-regenerable-candidate',{'workspace':str(w),'cache_kind':e.name,'producer_or_build_descriptors':descriptors}));continue
                stack.append(q)
    inventories=[];all_unique={};all_dirs=set();all_symlinks=0
    for number,(target,kind,proof)in enumerate(sorted(targets,key=lambda x:str(x[0]))):
        safe(target);need(under(target,cache)and target!=cache,'Candidate outside owned cache')
        before=identity(target);entries=tree(target);after=identity(target)
        regular=[x for x in entries if x['kind']=='regular'];dirs=[x for x in entries if x['kind']=='directory'];links=[x for x in entries if x['kind']=='symlink-metadata-only'];special=[x for x in entries if x['kind']=='special-metadata-only']
        lexical=[str(p)for p in protected_paths if under(p,target)]
        source_overlap=[str(p)for p in protected_roots if intersects(p,target)]
        inode_hits=[{'candidate':x['path'],'protected':protected_inodes[(x['device'],x['inode'])]}for x in regular if(x['device'],x['inode'])in protected_inodes]
        foreign=[x['path']for x in entries if x['device']!=ci['device']]
        stable=before==after
        blocks=[]
        if lexical:blocks.append('protected-file-path-intersection')
        if source_overlap:blocks.append('protected-source-or-code-root-overlap')
        if inode_hits:blocks.append('protected-physical-inode-intersection')
        if foreign:blocks.append('foreign-filesystem-member')
        if special:blocks.append('special-file-member')
        if not stable:blocks.append('namespace-changed-during-read-only-inventory')
        if target.name in {'build','.build','.gradle'}and not proof.get('producer_or_build_descriptors'):blocks.append('no-local-build-descriptor-proof')
        git=None
        if target.name=='.git':
            hp=target/'HEAD';git={'head_ref':ref(hp)if hp.is_file()and not hp.is_symlink()else None,'refs_paths':[x['path']for x in regular if under(Path(x['path']),target/'refs')or Path(x['path']).name=='packed-refs'],'limit':'Git metadata/history is not assumed reconstructible from its name or stock HEAD alone; any Git target needs separate exact-ref/history preservation admission.'};blocks.append('git-history-requires-separate-preservation-admission')
        unique={}
        for x in regular:
            key=(x['device'],x['inode']);unique.setdefault(key,x['allocated_file_bytes']);all_unique.setdefault(key,x['allocated_file_bytes'])
        all_dirs.update((x['device'],x['inode'])for x in dirs);all_symlinks+=len(links)
        inv_ref=write(f'target-{number:03d}.json',{'version':1,'root':str(target),'entries':entries,'symlink_targets_followed':False})
        inventories.append({'path':str(target),'kind':kind,'root_identity':before,'root_identity_unchanged':stable,'ownership':{'cache_marker':ref(owner),'cache_identity':{'device':ci['device'],'inode':ci['inode']},'canonical_descendant_no_symlink_ancestors':True,'all_members_same_filesystem':not foreign},'selection_exclusion_proof':proof,'inventory':inv_ref,'regular_files':len(regular),'directories':len(dirs),'symlinks_metadata_only':len(links),'special_entries':len(special),'logical_file_bytes':sum(x['size_bytes']for x in regular),'allocated_file_bytes_path_sum':sum(x['allocated_file_bytes']for x in regular),'allocated_file_bytes_unique_inodes':sum(unique.values()),'hardlinked_regular_files':sum(x['nlink']>1 for x in regular),'main_spec_or_other_protected_path_intersections':lexical,'production_or_plain_code_root_overlap':source_overlap,'protected_inode_intersections':inode_hits,'blockers':blocks,'git_history_proof_limit':git,'read_only_inventory_candidate':not blocks,'deletion_authorized':False,'cleanup_requirement':'Root must independently admit exact current identity/member freeze and use no-follow deletion; symlinks are only link metadata and their targets are never in this byte sum.'})
    meter=latest_meter(R/'operators/whole-study-meter-v2.jsonl')
    summary={'version':1,'kind':'read-only-regenerable-headroom-independent-inventory','main_spec':ref(SPEC),'main_plan':ref(PLAN),'cache_identity_authority':ref(R/'operators/cache-current-identity.json'),'owner':ref(owner),'cache_physical_identity':ci,'main_spec_files':len(spec['files']),'main_spec_source_bytes':sum(x['bytes']for x in spec['files']),'current_main_workspace_count':20,'rejected_workspace_count':6,'protected_paths_count':len(protected_paths),'protected_regular_inode_count':len(protected_inodes),'protected_paths_currently_missing':missing,'workspace_proofs':workspace_proofs,'compiler_scratch_proofs':dd_proofs,'targets':inventories,'all_candidate_allocated_file_bytes_unique_inodes':sum(all_unique.values()),'all_candidate_regular_file_paths':sum(x['regular_files']for x in inventories),'all_candidate_symlinks_metadata_only':all_symlinks,'latest_existing_meter_sample':meter,'restore_additional_bytes_estimate_from_root':12500000000,'fixed_budget_bytes':34359738368,'deletion_performed':False,'sdk_git_or_device_commands_executed':False,'original_executed_110_tree_or_SUT_modified':False,'limitations':['st_blocks*512 is allocated-file accounting, not guaranteed freed APFS physical bytes; hardlinks/clones/snapshots may share allocation.','Workspace/source setup/STOCK-COPY/commands, every main SPEC file, production source roots, subjects and compiler/xcresult evidence remain outside targets.','Candidate identity/membership is a point-in-time read-only snapshot; this is no deletion authority.','Qualification/benchmark original cleanup is not admitted by this inventory; exact original-map/current-byte/physical-owner proof is still required.'],'started_at_unix':start,'finished_at_unix':time.time()}
    need(sha(SPEC)==summary['main_spec']['sha256']and sha(PLAN)==summary['main_plan']['sha256']and sha(owner)==OWNER_SHA,'Authority changed during audit')
    need((cache.lstat().st_dev,cache.lstat().st_ino)==(16777232,26682812),'Cache replaced during audit')
    write('INVENTORY.json',summary)
    print(json.dumps({'targets':len(inventories),'main_dd_targets':sum(x['kind']=='main-compiler-DerivedData'for x in inventories),'candidate_allocated_unique_bytes':sum(all_unique.values()),'protected_intersection_targets':sum(bool(x['main_spec_or_other_protected_path_intersections']or x['production_or_plain_code_root_overlap']or x['protected_inode_intersections'])for x in inventories),'blocker_targets':sum(bool(x['blockers'])for x in inventories),'missing_protected_paths':len(missing),'deletion_performed':False}))


if __name__=='__main__':main()
