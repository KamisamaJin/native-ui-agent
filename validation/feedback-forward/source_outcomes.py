#!/usr/bin/env python3
"""Prospective source-only outcomes, kept separate from rendered/runtime truth."""
from metrics import ratio

def summarize(initial,final,original_self,final_self,*,complete_accepted):
 before={r['id']:r for r in initial};after={r['id']:r for r in final};own0={r['id']:r for r in original_self};own={r['id']:r for r in final_self}
 assert set(before)==set(after)==set(own0)==set(own),'Complete fixed source-audit population required'
 product={k for k,r in before.items()if r['priority']=='must'and r['status']=='failed'and r.get('cause_category')=='product'}
 final_product={k for k,r in after.items()if r['priority']=='must'and r['status']=='failed'and r.get('cause_category')=='product'}
 repaired=sorted(k for k in product if after[k]['status']=='passed');unknown=sorted(k for k in product if after[k]['status']=='unassessed')
 missed=sorted(k for k in final_product if own[k]['status']=='passed');unresolved=sorted(k for k in final_product if own[k]['status']=='unassessed');found=sorted(k for k in final_product if own[k]['status']=='failed')
 fp=sorted(k for k,r in after.items()if r['priority']=='must'and r['status']=='passed'and own[k]['status']=='failed')
 return {'initialConfirmedSourceProductViolations':sorted(product),'repaired':repaired,'repairUnknown':unknown,'repairRate':ratio(len(repaired),len(product)),'newConfirmedSourceRegressions':sorted(k for k,r in after.items()if before[k]['status']=='passed'and r['status']=='failed'and r.get('cause_category')=='product'),
         'finalConfirmedSourceProductViolations':sorted(final_product),'finalDetected':found,'finalKnownMisses':missed,'finalUnresolved':unresolved,'knownMissRate':ratio(len(missed),len(final_product)),'missBounds':[ratio(len(missed),len(final_product)),ratio(len(missed)+len(unresolved),len(final_product))],
         'finalKnownAssertionFalseAlarms':fp,'conditionalFalseDiscoveryRatio':ratio(len(fp),len(found)+len(fp)),
         'originalDetectedSourceRows':sorted(k for k in product if own0[k]['status']=='failed'),'finalStrictUnknown':sorted(k for k,r in after.items()if r['priority']=='must'and r['status']=='unassessed'),
         'confirmedSourceFalseRelease':bool(complete_accepted and final_product),'scope':'Source-review evidence only, no rendered-style or physical-runtime claim. Dual-AI judgments are not human gold. Related runtime/source manifestations are not added as independent bugs.'}
