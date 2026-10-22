import sys,subprocess
from pathlib import Path
R=Path(__file__).resolve().parent;S=R.parents[2]/'native-ui-agent/scripts'
p,scenario=sys.argv[1:];out=R/'captures'/f'{p}-{scenario}';cmd=[sys.executable,str(S/f'{p if p=="ios"else"android"}_observe.py'),'run','--bridge',str(R/'bridges'/('Bridge.swift'if p=='ios'else'Bridge.kt')),'--fixtures',str(R/'fixtures'/f'{p}-{scenario}.json'),'--actions',str(R/'generated'/f'{p}-{scenario}'/'actions.json'),'--output',str(out)]
if p=='ios':cmd+=['--package',str(R/'cache/generic-host/alerttoast'),'--product','AlertToast','--simulator','A23C7E6D-E267-4C1D-85E0-1A480EFC0BAF','--developer-dir','/Applications/Xcode.app/Contents/Developer','--build-cache',str(R/'cache/ios-build')]
else:cmd+=['--project',str(R/'cache/generic-host/reply/Reply'),'--java-home','/Users/rex/Library/Java/JavaVirtualMachines/jbr-21.0.11/Contents/Home','--android-sdk','/Users/rex/Library/Android/sdk']
sys.exit(subprocess.run([sys.executable,str(R/'run.py')]+cmd).returncode)
