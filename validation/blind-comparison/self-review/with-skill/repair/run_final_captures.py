from pathlib import Path
import sys,subprocess,json
platform=sys.argv[1]
profiles=Path('repair/profiles')
p=json.loads(Path(f'self-review/profiles/{platform}-wide-expanded.json').read_text())
p['target']['description']='Final public smoke';p['target']['sources'][-1]='public-smoke.json';p['commands'][0]['argv'][p['commands'][0]['argv'].index('--fixture')+1]='public-smoke.json';p['environment'].update({'theme':'light','font_scale':1,'layout_direction':'LTR','viewport':'390 x 620','ios_category':'large'})
(profiles/f'{platform}-public-smoke.json').write_text(json.dumps(p,indent=2)+'\n')
if platform=='ios':
 p=json.loads(Path('self-review/profiles/ios-narrow-light.json').read_text());(profiles/'ios-narrow-failed.json').write_text(json.dumps(p,indent=2)+'\n')
cases=['I01','I02','I03','I04','I05','I06','public-smoke']+(['narrow-failed'] if platform=='ios' else [])
for case in cases:
 result=subprocess.run(['python3','skill/scripts/ui_loop.py','capture','--project','.','--profile',str(profiles/f'{platform}-{case}.json'),'--output',f'repair/final-captures/{platform}/{case}'])
 print(platform,case,'exit',result.returncode,flush=True)
