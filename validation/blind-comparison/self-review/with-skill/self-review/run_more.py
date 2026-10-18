import subprocess,sys
platform=sys.argv[1]
for case in ['narrow-light','largest-narrow','empty-collapsed','row-informational']:
 r=subprocess.run(['python3','skill/scripts/ui_loop.py','capture','--project','.','--profile',f'self-review/profiles/{platform}-{case}.json','--output',f'self-review/captures/{platform}/{case}'])
 print(platform,case,r.returncode,flush=True)
