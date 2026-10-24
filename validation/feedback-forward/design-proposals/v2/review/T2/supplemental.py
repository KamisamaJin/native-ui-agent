#!/usr/bin/env python3
import json,time,sys,hashlib,xml.etree.ElementTree as E
from pathlib import Path
root=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill');p=root/'validation/feedback-forward/design/T2/public';o=root/'validation/feedback-forward/design-review/T2'
sys.dont_write_bytecode=True;sys.path.insert(0,str(root/'validation/feedback-forward/candidate-v9/scripts'))
import design_contract as d
start=time.time();r=d.load(p/'reference.json');a=d.load(p/'approval.json');results=[]
for case in ['P1','P2']:
 for platform in ['ios','android']:
  submitted=d.load(p/f'compiled/{case}/{platform}/review-catalog.json');actual=d.load(o/f'{case}-{platform}-catalog.json')
  results.append({'case':case,'platform':platform,'initial_comparison_difference':'CLI adds catalog_sha256 to API result; retained in commands.json as same_as_submitted:false','cli_envelope_equal':submitted==dict(actual,catalog_sha256=d.digest(actual)),'catalog_digest_verified':submitted['catalog_sha256']==d.digest(actual)})
role={case:{s:{'status':x['status']['value'],'fill':x['statusColor']['value']}for s,x in v['states'].items()}for case,v in r['cases'].items()}
used={x['statusColor']['value']for v in r['cases'].values()for x in v['states'].values()};unexercised=[k for k in ['waiting','ready','requested','blocked']if r['palette'][k]['value']not in used]
images=[]
for f in sorted(p.rglob('*.svg')):
 t=E.parse(f).getroot();images.append({'path':str(f.relative_to(p)),'width':t.get('width'),'height':t.get('height'),'text_elements':len(list(t.iter('{http://www.w3.org/2000/svg}text'))),'fills':sorted({x.get('fill')for x in t.iter()if x.get('fill')})})
missing_api=['Swift AudioTourChapter/OfflineAudioTour Equatable and Identifiable conformances, public stored values and exact declarations','Swift production iOS 14 compatibility (frozen observer host targets iOS 17)','Kotlin data-class semantics and modifier: Modifier = Modifier public parameter','Noninteractive canvas/surface/ink carrier and primary matching content shape/label allocation are not explicit source propositions']
value={'command':'SDK-free catalog CLI envelope normalization, status-role coverage and SVG inspection','startedAtUnix':start,'finishedAtUnix':time.time(),'catalog_envelopes':results,'status_role_values':role,'unexercised_status_roles':unexercised,'svg_inspection':images,'api_source_index_gaps':missing_api,'operator_limitations':[{'command':'initial rg inventory used validation/design-proposals/v1/design/T2/public instead of validation/feedback-forward/design-proposals/v1/design/T2/public','outcome':'rg printed No such file or directory; corrected path in subsequent reads; no expectation/tool/source fix'},{'command':'initial rg inventory included validation/feedback-forward root','outcome':'printed filenames for other task/private/v1 artifacts; no unauthorized file content or review conclusion was opened; all later content reads were scoped'},{'command':'shared implementation_audit definitions via module API','outcome':'shared script prepends live native-ui-agent/scripts; to respect frozen-only read scope, candidate-v9 design_contract was imported first and asserted by resolved module path; unmodified CLI dependency not independently checked'}]}
(o/'supplemental.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({'catalog_envelopes':results,'unexercised_status_roles':unexercised,'svg_count':len(images)},indent=2))
