"""Record completed original-pixel inspection and derive hash-bound review manifests.
Only fresh FINAL review artifacts are written; delivered capsules remain unchanged.
"""
import json,hashlib,datetime
from pathlib import Path
HERE=Path(__file__).resolve().parent;R=HERE.parents[3];REPO=R.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
index=read(HERE/'inspection-image-index.json')
assert len(index)==147
for item in index:
 assert sha(Path(item['path']))==item['sha256']
 for occ in item['occurrences']:assert sha(Path(occ['path']))==item['sha256']
for aid in ['sample-716d41','sample-e318ec']:
 cap=R/'private/grade-capsules/final'/aid;out=HERE/aid;images=[]
 for item in index:
  occurrences=[]
  for occ in item['occurrences']:
   if occ['anonymous_id']!=aid:continue
   occurrences.append({**occ,'path':str(Path(occ['path']).relative_to(REPO))})
  if occurrences:images.append({'sha256':item['sha256'],'viewed_with':'view_image original native pixels','occurrences':occurrences})
 register={'review_completed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'phase':'final','scope':'All FINAL original native full-state PNG sweeps, independently inspected for this phase. Byte-identical FINAL images reviewed once with every original state occurrence retained. Full sweep checked for all text, section order and direction. Measured palette and geometry are separately reproducible in visual-review.json. Runtime native font/padding/hit capability facts are never inferred from inspection.','images':images}
 (out/'inspection-register.json').write_text(json.dumps(register,ensure_ascii=False,indent=2)+'\n')
 manifest=read(cap/'manifest.json')
 for name in ['visual_review','source_review']:
  artifact=cap/(name.replace('_','-')+'.json');assert artifact.exists()
  manifest[name]={'path':artifact.name,'sha256':sha(artifact)}
 dest=cap/'manifest-reviewed.json';assert not dest.exists();dest.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'anonymous_id':aid,'reviewed_manifest_sha256':sha(dest),'completed':True}))
