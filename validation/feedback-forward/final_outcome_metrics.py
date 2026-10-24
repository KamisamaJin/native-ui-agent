#!/usr/bin/env python3
"""Prospective final self-verification versus independent same-raw public quality."""
from metrics import ratio

def summarize(truth,self_rows,must_keys,*,self_accepted):
 public={r['key']:r for r in truth if r['case']in{'P1','P2'}}
 own={r['key']:r for r in self_rows};assert set(public)==set(own),'Complete same-source public final assertion population required'
 required=set(must_keys)
 product={k for k,r in public.items()if k in required and r['status']=='failed'and r.get('cause_category')=='product'}
 detected=sorted(k for k in product if own[k]['status']=='failed')
 missed=sorted(k for k in product if own[k]['status']=='passed')
 unresolved=sorted(k for k in product if own[k]['status']=='unassessed')
 assert len(detected)+len(missed)+len(unresolved)==len(product)
 false_alarms=sorted(k for k,r in public.items()if k in required and r['status']=='passed'and own[k]['status']=='failed')
 unknown_alarms=sorted(k for k,r in public.items()if k in required and own[k]['status']=='failed'and k not in product and k not in false_alarms)
 unknown=sorted(k for k,r in public.items()if k in required and r['status']=='unassessed')
 hidden=sorted(r['key']for r in truth if r['case']=='H1'and r['key']in required and r['status']=='failed'and r.get('cause_category')=='product')
 return {'confirmedFinalPublicMustProductFailures':len(product),'detectedFinalPublicFailures':detected,'finalKnownFalseNegatives':missed,'finalUnresolvedProductFailures':unresolved,
         'knownMissRate':ratio(len(missed),len(product)),'missBounds':[ratio(len(missed),len(product)),ratio(len(missed)+len(unresolved),len(product))],
         'finalKnownFalseAlarmRows':false_alarms,'finalUnknownAlarmRows':unknown_alarms,'conditionalFinalFalseDiscoveryRatio':ratio(len(false_alarms),len(detected)+len(false_alarms)),
         'classicalFalsePositiveRate':None,'selfAccepted':self_accepted,'confirmedFalseRelease':bool(self_accepted and product),'independentUnknownRelease':bool(self_accepted and unknown),
         'hiddenConfirmedMustFailures':hidden,'scope':'Complete fixed public assertion comparison on identical own-final raw bytes. Known FN means self-P versus independently confirmed product-F; U is separate, not repaired/pass. Hidden has no original self-observation denominator. Qualitative truth is dual-AI consensus, not human gold.'}
