"""Independent publication revision of frozen metric arithmetic, synthetic-tested.

No truth judgment, reveal, barrier verification or product dataset access.
Call only after independent sealed correspondence, alarm adjudication and reveal.
"""
import math
import re
import statistics


CASES={f'Case0{i}' for i in range(1,6)}
GATES={'public_current_all_must_passed','private_current_all_must_passed','source_all_must_passed',
       'owned_resources_closed','independent_quality_complete'}


def need(value,message):
    if not value:raise ValueError(message)


def seconds(value):
    need(type(value) in {int,float} and math.isfinite(value) and value>=0,'Measured finite nonnegative seconds required')
    return value


def total(values):
    try:value=math.fsum(values)
    except OverflowError:raise ValueError('Aggregate cost exceeds finite arithmetic domain')
    need(math.isfinite(value),'Aggregate cost exceeds finite arithmetic domain')
    return value


def fraction(n,d):
    need(type(n) is int and type(d) is int and 0<=n<=d,'Bounded integer denominator required')
    return {'numerator':n,'denominator':d,'value':n/d if d else None}


def unique(rows,key='id'):
    need(isinstance(rows,list) and all(isinstance(r,dict) and isinstance(r.get(key),str) and r[key] for r in rows),'Identified metric rows required')
    out={r[key]:r for r in rows};need(len(out)==len(rows),'Duplicate metric unit');return out


def provenance(row,*,repair=False):
    need(type(row.get('worker_visible')) is bool,'Explicit Boolean worker_visible required')
    proof=row.get('provenance')
    need(isinstance(proof,dict) and set(proof)=={'phase','source_version','evidence'}
         and proof['phase'] in {'worker_public','independent_private_after_seal'}
         and isinstance(proof['source_version'],str) and re.fullmatch('[0-9a-f]{64}',proof['source_version'])
         and isinstance(proof['evidence'],list) and proof['evidence'],'Original phase/source-version/evidence provenance required')
    need(proof['phase']!='independent_private_after_seal' or row['worker_visible'] is False,
         'Post-seal independent validation cannot be worker-visible development evidence')
    if repair:
        need(row['worker_visible'] is True and proof['phase']=='worker_public',
             'Only an evidence-backed worker-public action can enter attempted repair')
    return proof['phase']


def coverage(final, frozen_registry):
    """Mandatory counts use frozen per-platform/state denominators; N/A separate.

    The independent input producer authenticates applicability and row truth.
    This function checks arithmetic/identity, never infers them from SDK exits.
    """
    need(isinstance(frozen_registry,list) and frozen_registry,'Separately authenticated frozen coverage registry required')
    registry={}
    for spec in frozen_registry:
        need(set(spec)=={'platform','state','family','applicable_ids','not_applicable_ids','evidence'},'Exact frozen applicability registry schema required')
        key=(spec['platform'],spec['state'],spec['family']);need(key not in registry,'Duplicate frozen applicability scope');registry[key]=spec
    rows=final['mandatory_coverage'];need(isinstance(rows,list) and rows,'Explicit frozen mandatory coverage rows required')
    seen=set();counts={'passed':0,'failed':0,'unassessed':0,'applicable':0,'not_applicable':0};families={}
    for row in rows:
        need(set(row)=={'platform','state','family','frozen_applicable_ids','passed_ids','failed_ids','unassessed_ids','not_applicable_ids','denominator_evidence'},
             'Exact mandatory coverage denominator schema required')
        key=(row['platform'],row['state'],row['family'])
        need(row['platform'] in {'ios','android'} and isinstance(row['state'],str) and row['state']
             and row['family'] in {'public_native_image','private_native_image','source'} and key not in seen,
             'Unique explicit platform/state/family coverage slots required');seen.add(key)
        need(isinstance(row['denominator_evidence'],list) and row['denominator_evidence'],'Frozen applicability evidence required')
        need(key in registry and row['frozen_applicable_ids']==registry[key]['applicable_ids']
             and row['not_applicable_ids']==registry[key]['not_applicable_ids']
             and row['denominator_evidence']==registry[key]['evidence'], 'Coverage denominator differs from separately frozen applicability registry')
        sets={}
        for field in ['frozen_applicable_ids','passed_ids','failed_ids','unassessed_ids','not_applicable_ids']:
            values=row[field];need(isinstance(values,list) and all(isinstance(v,str) and v for v in values) and len(values)==len(set(values)),
                                   'Unique explicit obligation IDs required');sets[field]=set(values)
        required=sets['frozen_applicable_ids'];p,f,u=(sets[k] for k in ['passed_ids','failed_ids','unassessed_ids'])
        need(not(p&f or p&u or f&u) and required==p|f|u and not(required&sets['not_applicable_ids']),
             'Mandatory denominator must be partitioned exactly; N/A cannot become pass')
        item={'passed':len(p),'failed':len(f),'unassessed':len(u),'applicable':len(required),'not_applicable':len(sets['not_applicable_ids'])}
        for k,v in item.items():counts[k]+=v
        family=families.setdefault(row['family'],{'passed':0,'failed':0,'unassessed':0,'applicable':0,'not_applicable':0})
        for k,v in item.items():family[k]+=v
    need({(p,f) for p,s,f in seen}=={(p,f) for p in ['ios','android'] for f in ['public_native_image','private_native_image','source']},
         'Both platforms and all three mandatory evidence families must remain represented')
    need(seen==set(registry),'Every frozen platform/state/family scope must be reported exactly once')
    return {'counts':counts,'unassessed_fraction':fraction(counts['unassessed'],counts['applicable']),
            'families':families,'complete':counts['failed']==counts['unassessed']==0}


def summarize(cases,arm,assignment,*,shared_costs,coverage_denominators):
    by=unique(cases,'case_id');need(set(by)==set(assignment)==CASES and arm in {'A','B'},'Exactly five paired PRs required')
    need(isinstance(shared_costs,dict) and set(shared_costs)=={'initial_oracle_seconds','design_preparation_seconds','common_infrastructure_seconds','independent_grading_matcher_seconds'},
         'Explicit separately reported shared cost categories required')
    shared={k:seconds(v) for k,v in shared_costs.items()};shared_total=total(shared.values())
    need(isinstance(coverage_denominators,dict) and set(coverage_denominators)==CASES,'Five separately frozen coverage denominator registries required')
    names=['initial','present','removed','unknown_relation','detected_initial','attempted_initial','attempted_removed','regression','unresolved_regression',
           'true_alarm','false_alarm','unresolved_alarm','false_positive_validation','unresolved_positive_validation','delivered']
    counts={k:0 for k in names};by_phase={p:{k:0 for k in ['true','false','unresolved']} for p in ['worker_public','independent_private_after_seal']}
    public=[];hidden=[];records=[];cover_totals={k:0 for k in ['passed','failed','unassessed','applicable','not_applicable']}
    for case_id in sorted(by):
        case=by[case_id];pair=assignment[case_id]
        need(set(pair)=={'A','B'} and set(pair.values())=={'X','Y'} and set(case['versions'])=={'X','Y'},'Exact paired reveal required')
        initial=unique(case['confirmed_initial_causes']);final=case['versions'][pair[arm]]
        relations=unique(final['initial_relations'],'initial_cause_id');need(set(relations)==set(initial),'Every confirmed initial cause needs one relation')
        for row in relations.values():need(row['status'] in {'present','removed','unresolved'} and isinstance(row.get('evidence'),list) and row['evidence'],'Explicit relation/evidence required')
        status={k:r['status'] for k,r in relations.items()};detected=set();attempted=set()
        for row in unique(final['defect_alarms']).values():
            phase=provenance(row);verdict=row['verdict'];need(verdict in {'true','false','unresolved'},'Explicit alarm adjudication required')
            ids=row['initial_cause_ids'];need(isinstance(ids,list) and len(ids)==len(set(ids)) and set(ids)<=set(initial),'Alarm correspondence must name initial causes')
            need(verdict=='true' or not ids,'False/unresolved alarms cannot earn detection credit')
            if verdict=='true' and row['worker_visible'] and phase=='worker_public':detected.update(ids)
            counts[verdict+'_alarm']+=1;by_phase[phase][verdict]+=1
        for row in unique(final['attempted_repairs']).values():
            provenance(row,repair=True);ids=row['initial_cause_ids']
            need(isinstance(ids,list) and len(ids)==len(set(ids)) and set(ids)<=set(initial) and isinstance(row.get('evidence'),list) and row['evidence'],
                 'Actual attempted repair correspondence/evidence required');attempted.update(ids)
        regressions=unique(final['new_regressions']);uncertain=unique(final['unresolved_regressions'])
        need(all(isinstance(r.get('evidence'),list) and r['evidence'] for r in regressions.values()),'Confirmed regression evidence required')
        claims=unique(final['positive_validation_claims'])
        need(all(r['verdict'] in {'true','false','unresolved'} for r in claims.values()),'Explicit positive-validation verdict required')
        gates=final['delivery_obligations'];need(set(gates)==GATES and all(type(v) is bool for v in gates.values()),'All five explicit delivery gates required')
        need(isinstance(final['unresolved_quality'],list),'Explicit unresolved-quality inventory required; null is not complete')
        need(set(coverage_denominators[case_id])=={'X','Y'},'Both anonymous frozen applicability registries required')
        cov=coverage(final,coverage_denominators[case_id][pair[arm]])
        # A recorded pass gate cannot conceal an F/U in its own frozen family.
        family_gate={'public_native_image':'public_current_all_must_passed','private_native_image':'private_current_all_must_passed','source':'source_all_must_passed'}
        for family,gate in family_gate.items():
            family_counts=cov['families'][family]
            need(not gates[gate] or family_counts['failed']==family_counts['unassessed']==0,'Delivery pass contradicts frozen mandatory F/U coverage')
        complete=(all(gates.values()) and cov['complete'] and all(v=='removed' for v in status.values())
                  and not regressions and not uncertain and not final['unresolved_quality'])
        p,h=seconds(final['public_wall_seconds']),seconds(final['hidden_validation_wall_seconds']);public.append(p);hidden.append(h)
        counts['initial']+=len(initial)
        for label,key in [('present','present'),('removed','removed'),('unresolved','unknown_relation')]:counts[key]+=sum(v==label for v in status.values())
        counts['detected_initial']+=len(detected);counts['attempted_initial']+=len(attempted);counts['attempted_removed']+=sum(status[k]=='removed' for k in attempted)
        counts['regression']+=len(regressions);counts['unresolved_regression']+=len(uncertain);counts['delivered']+=int(complete)
        counts['false_positive_validation']+=sum(r['verdict']=='false' for r in claims.values());counts['unresolved_positive_validation']+=sum(r['verdict']=='unresolved' for r in claims.values())
        for k,v in cov['counts'].items():cover_totals[k]+=v
        records.append({'case_id':case_id,'anonymous_version':pair[arm],'complete_delivery':complete,'coverage':cov,'public_wall_seconds':p,'hidden_validation_wall_seconds':h})
    p,h=total(public),total(hidden);combined=total([p,h]);d=counts['delivered'];denom=counts['initial'];adjudicated=counts['true_alarm']+counts['false_alarm'];all_alarms=adjudicated+counts['unresolved_alarm']
    def alarm_summary(v):
        known=v['true']+v['false'];all_count=known+v['unresolved']
        return {'counts':dict(v),'adjudicated_denominator':known,'unadjudicated_denominator':v['unresolved'],
                'false_discovery_fraction':fraction(v['false'],known),'unadjudicated_fraction':fraction(v['unresolved'],all_count)}
    return {'version':2,'arm':arm,'attempts':5,'counts':counts,
        'final_residual_miss_fraction':fraction(counts['present'],denom),'unresolved_initial_relation_fraction':fraction(counts['unknown_relation'],denom),
        'initial_detection_fraction':fraction(counts['detected_initial'],denom),'repair_fraction':fraction(counts['removed'],denom),
        'attempted_repair_fraction':fraction(counts['attempted_removed'],counts['attempted_initial']),
        'false_discovery_fraction':fraction(counts['false_alarm'],adjudicated),
        'alarm_adjudicated_denominator':adjudicated,'alarm_unadjudicated_denominator':counts['unresolved_alarm'],
        'unadjudicated_alarm_fraction':fraction(counts['unresolved_alarm'],all_alarms),
        'alarm_by_phase':{k:alarm_summary(v) for k,v in by_phase.items()},
        'mandatory_coverage':{'counts':cover_totals,'unassessed_fraction':fraction(cover_totals['unassessed'],cover_totals['applicable'])},
        'complete_delivery_fraction':fraction(d,5),
        'cost':{'all_attempt_public_seconds':p,'public_median_seconds':statistics.median(public),'public_range_seconds':[min(public),max(public)],
                'hidden_validation_seconds':h,'combined_seconds':combined,'successful_delivery_seconds':p/d if d else None,
                'combined_successful_delivery_seconds':combined/d if d else None,'shared_costs_reported_separately':shared,
                'shared_cost_total_seconds':shared_total,'model_billing':None,'tokens':None,'human_monetary_cost':None},
        'attempt_records':records,
        'scope':'Arithmetic only over separately authenticated independent adjudication/reveal and frozen applicability evidence. Hidden post-seal alarms never establish worker detection or repair. U and N/A remain separate; no current-source or product truth certification.'}
