from pathlib import Path
import json,hashlib,datetime,collections
R=Path('/Users/rex/Documents/ChatGPT/mobile-native-skill/validation/managed-forward/business-quality');P=R/'packet-public';H=R/'packet-initial-hidden';O=R/'reviewer-1';idx=json.loads((P/'SOURCE-INDEX.json').read_text());regs=json.loads((O/'initial-hidden-target-regions.json').read_text());groups=json.loads((O/'initial-hidden-target-groups.json').read_text());frags=json.loads((O/'initial-hidden-summary-fragments.json').read_text());fgroups=json.loads((O/'initial-hidden-summary-fragment-groups.json').read_text());src=json.loads((O/'source-actuals.json').read_text());actuals=[];coverage=[]
viewed_groups={0,1,2,3,4,5,8,9,10,11,13,14,16,17,18,19,22,24,25,26,27,28,29,30,33,36,37,39,40,41,42,43,44,46,47,49};viewed_fragment_groups={1,2,4,5,6,7,8,9}
reasons={'title-wrapping':'The full current Arabic occasion title is readable across its native wrapped lines, including its final word; no line is truncated or ellipsized.','option-clipping':'All three current Arabic option descriptions, including each final sentence/word, remain within their growing cards. A viewport-edge fragment in another original scroll frame does not signify card clipping.','balance-overlap':'The current summary separates heading, dish, label/value stacks and balance. Balance copy/amount do not overlap other card text.','title-hierarchy':'The current Arabic occasion title is visibly larger and more prominent than the section heading in the same native environment. This is image hierarchy, not a computed font measurement.'}
for cand in ['initial']:
 for plat in ['ios','android']:
  b=H/cand/plat;obs=json.loads((b/'native/observation.json').read_text());req=json.loads((b/'review-request.json').read_text());template=req['submission_template'];ridrows={r['review_id']:r for r in req['rows']};evidence=[]
  for d in template['decisions']:
   rr=ridrows[d['review_id']];st=rr['state'];rule=rr['id'].split('/')[-1];targets=['menu.title'] if rule=='title-wrapping' else ['menu.title','@heading'] if rule=='title-hierarchy' else ['menu.option.chickpea','menu.option.aubergine','menu.option.barley'] if rule=='option-clipping' else ['menu.summary'];ev=[]
   for tag in targets:
    found=[r for r in regs if r['candidate']==cand and r['platform']==plat and r['state']==st and r['target']==tag and not r.get('unavailable')]
    if found:
     r=found[0];g=next(g for g in groups if any(m.get('candidate')==cand and m['platform']==plat and m['state']==st and m['target']==tag and m['snapshot']==r['snapshot'] for m in g['members']));assert g['group'] in viewed_groups,(cand,plat,st,tag,g['group']);ev.append({**r,'group':g['group'],'inspected_representative':g['representative']})
    else:
     assert tag=='menu.summary'
     fs=[r for r in frags if r['candidate']==cand and r['platform']==plat and r['state']==st]
     for r in fs:
      g=next(g for g in fgroups if any(m['candidate']==cand and m['platform']==plat and m['state']==st and m['snapshot']==r['snapshot'] for m in g['members']))
      if g['group'] in viewed_fragment_groups:ev.append({**r,'fragment_group':g['group'],'inspected_representative':g['representative']})
     vv=sorted(r['fragment_vertical_interval'] for r in ev if r.get('target')=='menu.summary.fragment');assert vv and vv[0][0]==0;covered=0
     for lo,hi in vv:assert lo<=covered;covered=max(covered,hi)
     assert any(r['fragment_vertical_interval'][1] == r['target_full_height_px'] for r in ev if r.get('target')=='menu.summary.fragment')
   cap=next(c for c in obs['state_captures'] if c['state_id']==st);ti=sorted(set(r['snapshot'] for r in ev));reason=reasons[rule]+' Original target snapshots '+','.join(map(str,ti))+' in the complete, stable '+st+' state sweep; source '+idx[cand][plat]['sha256']+'. Original target pixel identities and exact byte-equal state associations are retained in visual-actuals-initial-hidden.json. No stitched image was used.'
   if any(r['target']=='menu.summary.fragment' for r in ev):reason+=' The overlapping original summary fragments jointly cover its full native height; the scrolling viewport boundary is not a card boundary.'
   d.update({'actual':True,'reason':reason,'snapshot_indices':cap['snapshot_indices']})
   actuals.append({'candidate':cand,'scope':'private','platform':plat,'claim_id':rr['id'],'review_id':d['review_id'],'actual':True,'observed':True,'reason':reason,'snapshot_indices':cap['snapshot_indices'],'target_snapshot_indices':ti,'source_identity':idx[cand][plat],'state_binding':ev[0]['binding'],'observation_sha256':template['observation_sha256'],'catalog_sha256':template['catalog_sha256'],'citations':ev,'full_content_coverage':{'complete':cap['complete'],'stable_binding':cap['stable_binding'],'snapshot_indices':cap['snapshot_indices']}})
  assert len(template['decisions'])==32 and all(d['actual'] is True for d in template['decisions'])
  name=f'initial-hidden-{plat}-submission.json';(O/name).write_text(json.dumps(template,indent=2,ensure_ascii=False)+'\n')
  au=json.loads((b/'automatic.json').read_text());coverage.append({'candidate':cand,'scope':'private','platform':plat,'required_native':303,'matrix_cells':312,'fixed_not_applicable':9,'original_automatic_counts':au['counts'],'original_unassessed_ids':[r['id'] for r in au['assertions'] if r['status']=='unassessed'],'typed_raw_rederived':{'P':247,'F':0,'U':0},'native_pixels_original':{'P':18 if plat=='ios' else 24,'F':6 if plat=='ios' else 0,'U':0},'independent_visual':{'P':32,'F':0,'U':0},'native_combined':{'P':297 if plat=='ios' else 303,'F':6 if plat=='ios' else 0,'U':0},'required_source':17,'source':{'P':16 if plat=='ios' else 17,'F':1 if plat=='ios' else 0,'U':0},'mandatory_remaining_U':[],'submission':name,'submission_sha256':hashlib.sha256((O/name).read_bytes()).hexdigest(),'source_identity':idx[cand][plat]})
(O/'visual-actuals-initial-hidden.json').write_text(json.dumps({'version':1,'reviewer':'reviewer-1','phase':'initial-hidden-complete','packet_seal_sha256':'a8d3dd36b1680daa8736f80d29b9d587b4b9ec7153944d54b0b95a47af6f3c1a','actuals_only':True,'actuals':actuals,'method':'Original PNG target regions inspected independently; exact decoded byte equality supports reuse across explicitly bound current states/candidates. Complete sweep indices supplied for each catalog full-content atom. Source rules cannot replace rendered observations.','inspected_region_groups':sorted(viewed_groups),'inspected_fragment_groups':sorted(viewed_fragment_groups)},indent=2,ensure_ascii=False)+'\n')
sa=[]
for r in src['actuals']:
 if r['candidate']!='initial':continue
 rr={**r,'scopes':['private'],'phase':'initial-hidden','citations':r['citations']+[{'path':'initial-hidden-binding-checks.json','candidate':r['candidate'],'platform':r['platform'],'fact':'source-before/after match byte-identical reviewed subject; fixed decode/direct bridge digest; no producer source-claims used'}]};sa.append(rr)
(O/'source-actuals-initial-hidden.json').write_text(json.dumps({'version':1,'reviewer':'reviewer-1','actuals_only':True,'source_responsibility_reference':'packet-public/design/private/reference.json#/responsibilities','actuals':sa,'producer_metadata_ignored':True},indent=2,ensure_ascii=False)+'\n')

(O/'initial-hidden-coverage.json').write_text(json.dumps(coverage,indent=2)+'\n')
print('Saved',len(actuals),'initial visual actuals,',len(sa),'source actuals, and two original-template submissions')
