from pathlib import Path
import sys,subprocess
platform=sys.argv[1]
for case in ['wide-expanded','narrow-dark-rtl','large-compact','empty','toggle','progress-edges']:
 result=subprocess.run(['python3','skill/scripts/ui_loop.py','capture','--project','.','--profile',f'self-review/profiles/{platform}-{case}.json','--output',f'self-review/captures/{platform}/{case}'])
 print(platform,case,'exit',result.returncode,flush=True)
