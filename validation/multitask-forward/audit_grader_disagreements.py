#!/usr/bin/env python3
"""UNSCORED posthoc audit of existing pixel-backed, grader-labelled false alarms."""
import argparse,hashlib,json,sys
from pathlib import Path
from PIL import Image
import experiment as ex
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R/'candidate-v7/scripts'));import native_checks as nc

def build():
 ex.gate.verify(R/'gates','grade-selfreview',R);t='T2';review=ex.read(R/'evaluation/selfreview'/t/'comparison.json');transport=ex.read(R/'evaluation-inputs/selfreview'/t/'source-b/claims.json');claims={x['original_finding_index']:x for x in transport['manual']};brief=R/'design-v2'/t/'public/BRIEF.md';out=[]
 # This is the complete set of independently labelled product FP claims in the
 # original sealed review with recorded flat-interior sampling evidence.
 for judged in review['sources']['source-b']['origin_metrics']['combined']['claims']:
  if judged['product_claim_class']!='FP':continue
  original=claims[judged['original_finding_index']]['original'];sample=original.get('actual',{})
  if 'samplePixel'not in sample:continue
  case,state,tag=sample['case'],original['state'],sample['tag'];expected=original['approved_disabled_fill'];assert expected in brief.read_text()
  original_path=R/str(sample['path']).split('/validation/multitask-forward/',1)[1];assert ex.sha(original_path)==sample['sha256']
  with Image.open(original_path)as im:actual=im.convert('RGB').getpixel(tuple(sample['samplePixel']));assert list(actual)==sample['sampleRgb']
  entry={'originalFindingIndex':judged['original_finding_index'],'originalGraderLabel':'FP','case':case,'state':state,'tag':tag,'originalClaimPixelVerified':list(actual),'originalClaimPNG':str(original_path.relative_to(R)),'originalClaimPNGSHA256':ex.sha(original_path),'declaredDisabledFill':expected,'brief':str(brief.relative_to(R)),'briefSHA256':ex.sha(brief),'originalGraderProductReason':judged['product_reason'],'commonCorpusSamples':[]}
  for alias in ['source-a','source-b']:
   for stage in ['D0','FINAL']:
    raw=R/'common-corpora'/t/alias/stage.lower()/'ios'/case;op=raw/'observation.json';obs=ex.read(op);plan=ex.read(R/'design-v2'/t/'public/compiled'/case/'ios/plan.json');spec=next(x for x in plan['states']if x['id']==state);frames=nc.state_evidence(obs,spec)[0];chosen=None
    for index,snapshot in frames:
     z=nc.resolve(snapshot,{'identifier':tag},'ios');c=z.get('control',{})
     if z.get('facts',{}).get('unique')and c.get('fully_within_viewport')and c.get('enabled')is False:chosen=(index,snapshot,c);break
    assert chosen,(alias,stage,case,state,tag)
    index,snapshot,c=chosen;frame=c['frame'];app=snapshot['app_frame'];png=raw/snapshot['screenshot']
    with Image.open(png)as im:
     sx=im.width/app['width'];sy=im.height/app['height'];assert abs(sx-sy)<1e-9
     # Reproduce the original claim's left+8pt, vertical-center flat-fill sample.
     x=round((frame['x']+8-app['x'])*sx);y=round((frame['y']+frame['height']/2-app['y'])*sy);rgb=im.convert('RGB');pixels=[rgb.getpixel((xx,yy))for xx in range(x-2,x+3)for yy in range(y-2,y+3)];colors=sorted(set(pixels));hexes=['#%02X%02X%02X'%rgb for rgb in colors]
    grade=R/'evaluation'/stage/t/alias/case/'ios/grade.json';row=next(x for x in ex.read(grade)['rows']if x['state']==state and x['requirement']=='visual-composition')
    entry['commonCorpusSamples'].append({'alias':alias,'stage':stage,'originalVisualGrade':row['status'],'grade':str(grade.relative_to(R)),'gradeSHA256':ex.sha(grade),'observation':str(op.relative_to(R)),'observationSHA256':ex.sha(op),'snapshot':index,'controlFrame':frame,'samplePointPixels':[x,y],'patchSize':5,'patchUniqueColors':hexes,'singleFlatColorEqualsDeclaredFill':len(hexes)==1 and hexes[0]==expected,'png':str(png.relative_to(R)),'pngSHA256':ex.sha(png)})
  out.append(entry)
 return {'scope':'UNSCORED posthoc disagreement audit, triggered by already sealed evaluator FP labels and original pixel-backed claims. No original score, claim, production code, design expectation or repair is changed. Reproduces original own-capture samples and examines the same two cases/controls/states symmetrically on BOTH anonymous common source corpora before/after. Pixels are rendered appearance, not computed SwiftUI color. A disagreement with the frozen qualitative AI grade requires external adjudication; do not present grader-labelled FP as objectively confirmed false alarms or infer a treatment gain from this audit. No additional native acquisition.','sampling':'Original left+8pt/vertical-center point; 5x5 flat patch; actual app-frame/screenshot scale; fully visible unique disabled native control. No threshold, color correction or changed contract.','disputes':out}
def main():
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');a=p.parse_args();v=build();path=R/'grader-disagreements.json'
 if a.write:assert not path.exists();ex.save(path,v)
 else:assert ex.read(path)==v
 print(json.dumps({'status':'PASS','existingPixelBackedGraderFPDisputes':len(v['disputes']),'samples':[[x['alias'],x['stage'],x['case']if'case'in x else d['case'],x['patchUniqueColors'],x['originalVisualGrade']]for d in v['disputes']for x in d['commonCorpusSamples']]}))
if __name__=='__main__':main()
