import subprocess,os,json
from pathlib import Path
R=Path(__file__).resolve().parent;env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode.app/Contents/Developer');d=json.loads(subprocess.check_output(['xcrun','simctl','list','devices','--json'],env=env));found=[x for xs in d['devices'].values()for x in xs if x['udid']=='A23C7E6D-E267-4C1D-85E0-1A480EFC0BAF'];assert len(found)==1 and found[0]['state']=='Shutdown';(R/'simulator-final-state.json').write_text(json.dumps(found[0],indent=2)+'\n');print(found[0]['udid'],found[0]['state'])
