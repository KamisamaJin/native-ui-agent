"""Enter independently viewed FINAL pixel observations; no D0 outcomes imported."""
import datetime,json
import raw_review as r
PATH=r.HERE/'manual-reviews.json'
def put(sub,pl,cid,observation):
 data=r.load(PATH);v=data[sub];d=r.state_data(sub,pl,cid)
 observation['reviewedAtUTC']=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
 observation['actualFixtureEqualsFrozenModel']=d['fixtureEquals']
 observation['actualAnonymousSourceMatches']=d['sourceMatch']
 v['pixelReviews']=[x for x in v['pixelReviews'] if (x['platform'],x['contextId'])!=(pl,cid)]
 v['pixelReviews'].append(dict(platform=pl,contextId=cid,observation=observation));r.write(PATH,data)
def full(sub,pl,cid,*,selectedOption,selectedSize=None,checkmark=False,expanded=False,clippedFields=None,overlapPairs=None,regions=None,flow=None,fields=None):
 c=r.CTX[cid];assert c['fullVisualCheckpoint']
 rows=[x for x in r.PLAN if x['platform']==pl and x['contextId']==cid and x['aspect']=='observedPixels']
 # The expected catalog supplies stable field/region names after each concrete
 # native image sequence has been directly read. Any observed difference must
 # be entered explicitly; this helper is not a visual comparator or auto-pass.
 put(sub,pl,cid,dict(fields=c['visualInventory']['allVisibleFieldIds'] if fields is None else fields,regions=next(x['expected'] for x in rows if x['criterion']=='visibleDocumentedRegionsEqual') if regions is None else regions,flow=next(x['expected'] for x in rows if x['criterion']=='majorRegionFlowEquals') if flow is None else flow,selectedOption=selectedOption,selectedSize=selectedSize,checkmark=checkmark,expanded=expanded,clippedFields=clippedFields or [],overlapPairs=overlapPairs or [],actuallyObservedStrings=[x['expected'] for x in rows if x['criterion']=='fullyReadableTextEquals'],fullSequenceDirectlyReviewed=True))
def focused(sub,pl,cid,**observations):
 assert not r.CTX[cid]['fullVisualCheckpoint'];put(sub,pl,cid,observations)
def colors(sub,pl,cid,values):
 data=r.load(PATH);data[sub]['colorSamples'][pl][cid]=values;r.write(PATH,data)
def complete_case(sub,pl,case):
 data=r.load(PATH);v=data[sub];have={(x['platform'],x['contextId']) for x in v['pixelReviews']}
 need={(pl,x['contextId']) for x in r.PLAN if x['platform']==pl and x['contextId'] and x['contextId'].startswith(case+'/') and x['aspect']=='observedPixels'}
 assert need<=have,sorted(need-have)
 for cid,c in r.CTX.items():
  if c['caseId']==case:
   d=r.state_data(sub,pl,cid);assert d['fixtureEquals'] and all(d['sourceMatch'].values())
 if dict(platform=pl,caseId=case) not in v['reviewedCases']:v['reviewedCases'].append(dict(platform=pl,caseId=case))
 r.write(PATH,data)
