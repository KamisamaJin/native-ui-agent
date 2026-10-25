#!/usr/bin/env python3
"""Conservative endpoint metrics: unknown attribution never becomes FP or quality pass."""
import json,sys
from pathlib import Path

def ratio(n,d):return n/d if d else None

def summarize(value):
    initial=set(value['initial_confirmed_defects']);rows=[]
    for unit in value['arms']:
        residual=set(unit['residual_initial_defects']);regressions=set(unit['new_regressions'])
        assert residual<=initial
        alarms=unit['alarm_causes'];assert all(v in {'product','false_alarm','uncertain'}for v in alarms)
        confirmed=sum(v=='product'for v in alarms);false=sum(v=='false_alarm'for v in alarms);unknown=sum(v=='uncertain'for v in alarms)
        accepted=bool(unit['native_complete']and unit['source_audit_complete']and unit['independent_quality_complete']and not residual and not regressions)
        assert unit['failed']>=0 and unit['unassessed']>=0 and unit['applicable']>=unit['failed']+unit['unassessed']
        assert all(unit[k]>=0 for k in ['author_seconds','d0_seconds','repair_endpoint_seconds'])
        cost=unit['author_seconds']+unit['d0_seconds']+unit['repair_endpoint_seconds']
        rows.append({'unit':unit['unit'],'accepted':accepted,'initial_confirmed_defects':len(initial),'residual_initial_defects':len(residual),
                     'regressions':len(regressions),'repair_rate':ratio(len(initial-residual),len(initial)),
                     'final_initial_defect_miss_rate':ratio(len(residual),len(initial)),
                     'confirmed_product_alarms':confirmed,'confirmed_false_alarms':false,'uncertain_alarms':unknown,
                     'false_discovery_rate_among_judged':ratio(false,confirmed+false),
                     'false_discovery_bounds_all_alarms':[ratio(false,len(alarms)),ratio(false+unknown,len(alarms))],
                     'classic_false_positive_rate':None,'unassessed_fraction':ratio(unit['unassessed'],unit['applicable']),
                     'failed_endpoint_cost_seconds':None if accepted else cost,'successful_delivery_cost_seconds':cost if accepted else None,
                     'endpoint_cost_seconds':cost})
    return {'arms':rows,'scope':'n=1 paired exploratory PR; independent AI panels and frozen native assertions, not human gold. No successful cost is inferred from a failed endpoint; zero real-defect denominators remain null.'}

if __name__=='__main__':
 p=Path(sys.argv[1]);print(json.dumps(summarize(json.loads(p.read_text())),indent=2))
