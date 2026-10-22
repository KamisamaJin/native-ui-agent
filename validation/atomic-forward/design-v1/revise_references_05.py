from pathlib import Path
import shutil,json,datetime,sys
R=Path(__file__).resolve().parent;A=R/'authoring-attempts'/'attempt-04-references';A.mkdir(parents=True)
shutil.copy2(R/'generate_design.py',A/'generate_design.py')
p=R/'generate_design.py';s=p.read_text();old="label=item['label']+(' · Unavailable' if not item['available'] else '')\n  label_lines=";new="label=('☑ ' if t['multi'] and item['id'] in ['a','b'] else '☐ ' if t['multi'] else '')+item['label']+(' · Unavailable' if not item['available'] else '')\n  label_lines=";assert old in s;s=s.replace(old,new);p.write_text(s)
# Locks seal typed values, which are unchanged. The final task/canvas proposal is not yet sealed.
from generate_design import TASKS,draw,reference
for t in TASKS:
 for scope,cs in [('public',['P1','P2']),('private',['H1'])]:
  folder=R/t['id']/scope
  for cid in cs:
   for ext in ['svg','png','meta.json']:
    old=folder/f'reference-{cid}-expanded.{ext}';q=A/old.relative_to(R);q.parent.mkdir(parents=True,exist_ok=True);shutil.move(str(old),str(q))
   draw(t,cid,folder,reference(t,cs))
(R/'revision-05-record.json').write_text(json.dumps({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reason':'Pre-task-seal independent image QA found checkbox prefix missing from reference card height estimate; include its width before wrapping. Original reference images preserved, locked typed values and all plan/policy identities unchanged. No native SDK/implementation used.'},indent=2)+'\n')
(R/'private').mkdir();shutil.move(str(R/'private-reference-contact-sheet.png'),str(R/'private'/'contact-sheet-before-reference-revision.png'))
