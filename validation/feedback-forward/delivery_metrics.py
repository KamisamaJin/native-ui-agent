#!/usr/bin/env python3
"""Fixed equal-initial population quality, gate and endpoint calculations."""
from metrics import ratio,coverage,repairs

def compare(initial,final,clusters,required_ids):
 before={v['key']:v for v in initial};after={v['key']:v for v in final}
 assert set(before)<=set(after),'D0 public obligations cannot disappear from final denominator'
 bad=[k for k,v in after.items()if k in required_ids and v['status']=='failed'and v.get('cause_category')=='product']
 unresolved=[k for k,v in after.items()if k in required_ids and v['status']=='unassessed']
 regressions=[k for k,v in after.items()if k in before and before[k]['status']=='passed'and v['status']=='failed'and v.get('cause_category')=='product']
 return {'coverage':coverage(list(after.values())),'repairs':repairs(initial,final,clusters),
         'finalConfirmedMustViolations':bad,'unresolvedMustRows':unresolved,'confirmedProductRegressions':regressions,
         'finalPublicMissRate':ratio(sum(after[k]['status']=='failed'for k,v in before.items()if v['status']=='failed'and v.get('cause_category')=='product'),sum(v['status']=='failed'and v.get('cause_category')=='product'for v in before.values())),
         'scope':'Equal initial public population. FINAL hidden failures have no D0 repair denominator. U is not repaired.'}

def cost(handoff,endpoint,requests,accepted,accepted_endpoint=None):
 assert endpoint>=handoff
 assert accepted_endpoint is None or (accepted and accepted_endpoint>=endpoint)
 return {'handoffToPublicVerificationSeconds':endpoint-handoff,'handoffToAcceptedSeconds':accepted_endpoint-handoff if accepted_endpoint is not None else None,
         'accepted':accepted,'requestCount':len(requests),'requestWallSeconds':sum(r['finishedAtUnix']-r['startedAtUnix']for r in requests),
         'queueSeconds':sum(r.get('queueSeconds',0)for r in requests),
         'scope':'Per-consumer endpoint, including actual queue. Native resource sums may overlap; failed/unknown gate is not an accepted PR.'}
