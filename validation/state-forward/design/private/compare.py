#!/usr/bin/env python3
"""Fixed-row repairs and format-neutral review matching after manual adjudication.
Claims retain all originals. No machine_findings field is required or inspected.
"""
import argparse
from collections import Counter
import json
from pathlib import Path

def compare(d0,final,review=None):
    if d0['anonymousID']!=final['anonymousID']:raise ValueError('Cannot compare different anonymous sources')
    before={r['cellID']:r for r in d0['rows']};after={r['cellID']:r for r in final['rows']}
    if set(before)!=set(after):raise ValueError('A fixed denominator must be retained')
    natural={i:r for i,r in before.items() if r['status']=='F' and r['classification'].startswith('runtime.')}
    repaired=[dict(cellID=i,classification=r['classification'],caseID=r['caseID'],stateID=r['stateID'],before='F',after=after[i]['status']) for i,r in natural.items()]
    transitions=Counter(r['after'] for r in repaired)
    changes=[dict(cellID=i,classification=r['classification'],before=r['status'],after=after[i]['status']) for i,r in before.items() if r['status']!=after[i]['status']]
    output=dict(anonymousID=d0['anonymousID'],naturalFRows=len(natural),repairDenominator=len(natural) or None,repairShare=transitions['P']/len(natural) if natural else None,fixedRows=repaired,fixedRowTransitions=dict(transitions),allStatusChanges=changes)
    if review is None:return output
    claims=review.get('claims',[]);seen=set();manual=set();typed=set();adjudicated=[];counts=Counter();duplicates=[];signatures={}
    for c in claims:
        if c['claimID'] in seen:raise ValueError('claimID must be unique; duplicate content keeps distinct claimID')
        seen.add(c['claimID']);r=dict(c);matches=c.get('matches',[])
        exact=[m['cellID'] for m in matches if m.get('adjudication')=='exact' and m.get('cellID') in before and before[m['cellID']]['status']=='F']
        typed_eligible=c.get('origin')=='typed' and c.get('typedCheckEstablished') is True and bool(c.get('typedNativeReportRefs'))
        if c.get('origin')=='manual':manual.update(set(exact)&set(natural))
        if typed_eligible:typed.update(set(exact)&set(natural))
        if exact and (c.get('origin')!='typed' or typed_eligible):status='confirmedTrue'
        elif matches and all(m.get('adjudication')=='false' for m in matches):status='confirmedFalse'
        else:status='uncertainOrUnmapped'
        counts[status]+=1
        r.update(matchingStatus=status,confirmedExactCellIDs=exact,typedEligible=typed_eligible)
        sig=(c.get('origin'),tuple(sorted(exact)),c.get('scope','unspecified'))
        if exact and sig in signatures:duplicates.append(dict(claimID=c['claimID'],duplicates=signatures[sig]))
        elif exact:signatures[sig]=c['claimID']
        adjudicated.append(r)
    adjudicable=counts['confirmedTrue']+counts['confirmedFalse'];allclaims=adjudicable+counts['uncertainOrUnmapped'];fp=counts['confirmedFalse'];uncertain=counts['uncertainOrUnmapped']
    output['reviewMatching']=dict(claims=adjudicated,duplicates=duplicates,manualDetectedRows=sorted(manual),actualTypedDetectedRows=sorted(typed),manualExclusiveRows=sorted(manual-typed),typedExclusiveRows=sorted(typed-manual),bothRows=sorted(manual&typed),combinedDetectedRows=sorted(manual|typed),manualDetectionShare=len(manual)/len(natural) if natural else None,combinedDetectionShare=len(manual|typed)/len(natural) if natural else None,claimCounts=dict(counts),conditionalFalseDiscoveryShare=fp/adjudicable if adjudicable else None,allUncertainConservativeInterval=[fp/allclaims,(fp+uncertain)/allclaims] if allclaims else None,classicalFPR=None,classicalFPRReason='No complete true-negative claim universe is enumerated.')
    scopes={}
    for scope in sorted({c.get('scope','unspecified') for c in adjudicated}):
        cs=Counter(c['matchingStatus'] for c in adjudicated if c.get('scope','unspecified')==scope)
        n=cs['confirmedTrue']+cs['confirmedFalse'];alln=n+cs['uncertainOrUnmapped'];f=cs['confirmedFalse'];u=cs['uncertainOrUnmapped']
        scopes[scope]=dict(claimCounts=dict(cs),conditionalFalseDiscoveryShare=f/n if n else None,allUncertainConservativeInterval=[f/alln,(f+u)/alln] if alln else None)
    output['reviewMatching']['byScope']=scopes
    return output

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--d0',type=Path,required=True);ap.add_argument('--final',type=Path,required=True);ap.add_argument('--review',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    output=compare(json.loads(a.d0.read_text()),json.loads(a.final.read_text()),json.loads(a.review.read_text()) if a.review else None)
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':main()
