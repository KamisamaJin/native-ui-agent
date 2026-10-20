"""Stage one SHA-validated frame from this session's fresh native acquisition.
This is evidence reuse, not a second native run; staging.json records that boundary.
"""
from pathlib import Path
import argparse,json,hashlib,shutil
p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--fixtures',type=Path,required=True);p.add_argument('--actions',type=Path,required=True);p.add_argument('--observation-sha256',required=True);p.add_argument('--index',type=int,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
r=a.run.resolve();m=json.loads((r/'manifest.json').read_text());o=json.loads((r/'observation.json').read_text())
assert m['native_test_count']==1
assert m.get('test_exit_code',m.get('exit_code'))==0
assert sha(r/'observation.json')==a.observation_sha256
assert sha(a.fixtures)==m['input_hashes']['fixtures']
assert sha(a.actions)==m['input_hashes']['actions']
for path,digest in m['source_hashes'].items():assert sha(Path(path))==digest,('source changed',path)
for path,digest in m['image_hashes'].items():assert sha(r/path)==digest,('image changed',path)
f=r/o['snapshots'][a.index]['screenshot'];assert sha(f)==m['image_hashes'][str(f.relative_to(r))]
a.output.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,a.output/'actual.png')
(a.output/'staging.json').write_text(json.dumps({'execution':'Verified reuse of native acquisition already performed in this forward test; no second native runtime execution.','native_run':str(r),'native_started_at':m['started_at'],'native_finished_at':m['finished_at'],'manifest_sha256':sha(r/'manifest.json'),'observation_sha256':sha(r/'observation.json'),'snapshot_index':a.index,'original_image':str(f),'image_sha256':sha(f),'validated_source_count':len(m['source_hashes']),'validated_image_count':len(m['image_hashes'])},indent=2)+'\n')
