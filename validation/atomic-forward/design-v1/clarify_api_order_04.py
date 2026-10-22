from pathlib import Path
import shutil,json,datetime
R=Path(__file__).resolve().parent;A=R/'authoring-attempts'/'attempt-03-api-doc';A.mkdir(parents=True)
items=[('T1','WorkshopSlotPlannerModel','onSelect: (String) -> Void','onReserve: (String) -> Void'),('T2','RiverSensorTriageModel','onSelect: (String) -> Void','onAcknowledge: (String) -> Void'),('T3','BicycleServiceIntakeModel','onToggle: (String, Bool) -> Void','onSubmit: ([String]) -> Void')]
for tid,model,sel,submit in items:
 p=R/tid/'public'/'API.md';q=A/tid/'API.md';q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
 s=p.read_text();old=f'init(model: {model}, {sel}, {submit}, onDetailsChange: (Bool) -> Void)';new=f'init(model: {model}, {sel}, onDetailsChange: (Bool) -> Void, {submit})'
 assert old in s;s=s.replace(old,new);p.write_text(s)
(R/'revision-04-record.json').write_text(json.dumps({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reason':'Before final task sealing, correct Swift signature documentation order to the already-authoritative unchanged Bridge.swift order. No API behavior, reference value, rule, action, lock or policy changed. Original doc preserved.'},indent=2)+'\n')
