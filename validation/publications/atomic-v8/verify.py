#!/usr/bin/env python3
"""Replay the immutable v8 publication in its original source/CI view."""
import hashlib,json,os,shutil,subprocess,sys,tempfile
from pathlib import Path
P=Path(__file__).resolve().parent
REPO=P.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def materialize(root):
 meta=read(P/'publication.json')
 manifests=[REPO/meta['originalManifest'],REPO/meta['completionManifest']]
 for path,key in zip(manifests,['originalManifestSHA256','completionManifestSHA256']):assert sha(path)==meta[key]
 original=read(manifests[0]); completion=read(manifests[1])
 aliases=read(REPO/'validation/publications/atomic-v8-completion/original-publication.json')['mutableAliases']
 def put(rel,source,expected):
  assert source.is_file() and sha(source)==expected,rel
  target=root/rel;assert target.resolve().is_relative_to(root.resolve())
  target.parent.mkdir(parents=True,exist_ok=True)
  if target.exists():target.unlink()
  try:os.link(source,target)
  except OSError:shutil.copyfile(source,target)
 for rel,expected in original['files'].items():
  source=REPO/(aliases[rel]['archive'] if rel in aliases else rel)
  if rel in meta['mutableFiles'] and rel not in aliases:source=P/'original-mutable'/rel
  put(rel,source,expected['sha256'])
 for rel,expected in completion['files'].items():
  source=P/'original-mutable'/rel if rel in meta['mutableFiles'] else REPO/rel
  put(rel,source,expected['sha256'])
 for rel,expected in meta['mutableFiles'].items():put(rel,P/'original-mutable'/rel,expected)
 for path in manifests:put(str(path.relative_to(REPO)),path,sha(path))
 return meta

def main():
 with tempfile.TemporaryDirectory(prefix='native-v8-original-view-') as directory:
  root=Path(directory);materialize(root)
  # Read the real publication's tracked literal names, while hashing the
  # historical materialized bytes. No index/object/commit mutation is performed.
  env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',GIT_DIR=str(REPO/'.git'),GIT_WORK_TREE=str(root))
  commands=[['validation/publications/atomic-v8-completion/test_publication_closure.py'],['validation/publications/atomic-v8-completion/verify_completion.py','--prepare'],['validation/atomic-forward/verify_adapters.py'],['validation/atomic-forward/verify_study.py']]
  commands += [['validation/atomic-forward/'+name+'.py','--check'] for name in ['build_summary','costs','grading_costs','observation_costs','action_scope','build_tables','build_gallery','failure_index','disagreements']]
  commands += [['validation/publications/atomic-v8-completion/verify_completion.py']]
  for command in commands:subprocess.run([sys.executable,'-B',*command],cwd=root,env=env,check=True)
 print('PASS: immutable v8 sources, evidence, derived results and original publication closure')
if __name__=='__main__':main()
