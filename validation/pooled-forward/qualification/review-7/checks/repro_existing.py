"""Read-only current-freeze reproduction from this review's preserved artifacts."""
import sys,argparse,json
from pathlib import Path
sys.dont_write_bytecode=True
p=argparse.ArgumentParser();p.add_argument('--arm',choices=['candidate-v13.6','baseline-v12.6-common-3'],required=True);p.add_argument('--case',choices=['capture-index-bool','incomplete-whole-state-uniqueness','M01-full-after-action-bool','M02-full-after-action-float','M03-legacy-action-snapshot-bool'],required=True);a=p.parse_args();root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root.parents[1]/a.arm/'scripts'));import native_checks
group='metadata-scope'if a.case.startswith('M')else'delta';base=root/'work'/a.arm/group/a.case;o=json.loads((base/'observation.json').read_text());s=json.loads((base/'state.json').read_text())
if a.case=='incomplete-whole-state-uniqueness':target='semantic-target';prop='unique';expected=True
elif a.case=='M03-legacy-action-snapshot-bool':target='anchor-a';prop='present';expected=True
else:target='absent-target';prop='present';expected=False
plan={'version':1,'states':[s],'required_assertion_ids':['repro'],'assertions':[{'id':'repro','state':'start','kind':'control','target':{'identifier':target},'property':prop,'expected':expected}]};report=native_checks.evaluate(plan,o,'ios',root=base/'packet/native');print(json.dumps({'evidence_class':'HOST validator on preserved SIMULATED packet; no SDK/device','state':report['states']['start'],'assertion':report['assertions'][0]},indent=2))
