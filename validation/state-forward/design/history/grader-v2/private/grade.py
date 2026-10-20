#!/usr/bin/env python3
"""Frozen, conservative row grader. Uses normalized *actual* native evidence.
No source-to-runtime inference, target resolver, dispatcher, or new gate AST.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import math

HERE=Path(__file__).resolve().parent
VERDICTS={'pass':'P','fail':'F','unknown':'U'}

def strict_equal(a,b):
    if isinstance(b,bool): return type(a) is bool and a==b
    if type(b) is int:return type(a) is int and a==b
    if type(b) is float:return type(a) is float and a==b
    if isinstance(b,str): return isinstance(a,str) and ' '.join(a.splitlines())==b
    if isinstance(b,list): return isinstance(a,list) and len(a)==len(b) and all(strict_equal(x,y) for x,y in zip(a,b))
    if isinstance(b,dict): return isinstance(a,dict) and set(a)==set(b) and all(strict_equal(a[k],v) for k,v in b.items())
    return a is None and b is None

def color(v):
    if isinstance(v,int) and not isinstance(v,bool): return f'{v & 0xffffffff:08X}'
    if isinstance(v,str):
        s=v.removeprefix('#').upper()
        if len(s)==6:s='FF'+s
        if len(s)==8 and all(c in '0123456789ABCDEF' for c in s):return s
    return None

def context_ok(cell,rec):
    ctx=rec.get('context',{})
    for k in ['platform','caseID','stateID']:
        if ctx.get(k)!=cell.get(k):return False,f'{k} is not bound to this cell'
    if cell['classification'].startswith('runtime.') or cell['classification']=='stimulus.execution':
        for k in ['processID','inputRevision','eventRevision','mappingRef']:
            if k not in ctx or ctx[k] is None or ctx[k]=='':return False,f'missing native context {k}'
    return True,''

def gate_ok(cell,rec,interval=False):
    gate=rec.get('gate',{})
    if gate.get('verdict')!='pass':return False,'required stimulus not established by immutable native helper'
    if not gate.get('evidenceRefs'):return False,'stimulus provenance missing'
    if gate.get('kind')!=cell.get('gate'):return False,'wrong stimulus gate kind'
    if gate.get('kind')=='successfulExactActivation':
        if gate.get('targetID')!=cell['targetID']:return False,'successful dispatch belongs to another target'
        if gate.get('attempts')!=1:return False,'one exact activation attempt not established'
    if interval and gate.get('intervalComplete') is not True:return False,'complete immediate callback interval not established'
    return True,''

def native_measurement(cell,rec):
    actual=rec.get('actual');unit=rec.get('unit');u=rec.get('uncertainty')
    if isinstance(actual,dict) and 'value' in actual:
        unit=actual.get('unit',unit);u=actual.get('uncertainty',u);actual=actual['value']
    if not isinstance(actual,(int,float)) or isinstance(actual,bool) or not math.isfinite(actual):return None,None,'not a finite native scalar'
    if cell.get('unit') and unit!=cell['unit']:return None,None,'native unit missing or incompatible'
    if u is None:u=2.0 if rec.get('evidenceKind')=='native.bounds' else 0.0
    if not isinstance(u,(int,float)) or u<0:return None,None,'invalid measurement uncertainty'
    return actual,float(u),''

def result(cell,status,reason,rec=None,**extra):
    row={k:deepcopy(cell.get(k)) for k in ['cellID','platform','caseID','stateID','aspect','classification','targetID','operator','expected']}
    row.update(status=status,reason=reason,evidenceRefs=deepcopy(rec.get('evidenceRefs',[])) if rec else [],actual=deepcopy(rec.get('actual')) if rec else None)
    if rec:
        row['context']=deepcopy(rec.get('context'))
        row['normalization']={k:deepcopy(rec[k]) for k in ['unit','uncertainty','nativeProperty','capability','measurementNodePath','measurementCandidates','selectionCandidates','normalizationOccurrences','unresolvedRecords'] if k in rec}
    if rec and 'gate' in rec:row['gate']=deepcopy(rec['gate'])
    row.update(extra)
    return row

def grade_cell(cell,records):
    op=cell['operator'];cls=cell['classification']
    if op=='notApplicable':return result(cell,'N/A',cell['reason'])
    if not records:return result(cell,'U','no supplied native/review evidence')
    # Unavailable measurements are retained, but do not erase a valid same-epoch native fact.
    original_records=records
    unresolved=[r for r in records if r.get('actual') is None and r.get('evidenceKind','').startswith('native.') and r.get('completeCoverage') is not True and op!='stimulus']
    usable=[r for r in records if r not in unresolved]
    if not usable and unresolved:return result(cell,'U','native value unresolved',unresolved[0],unresolvedRecords=deepcopy(unresolved))
    records=usable
    # Deduplicate identical facts in exactly the same context; provenance paths may differ.
    fingerprints=set()
    for r in records:
        key={k:r.get(k) for k in ['actual','evidenceKind','context','gate','reviewVerdict','helperVerdict','completeCoverage','uncertainty','unit','nativeProperty']}
        fingerprints.add(json.dumps(key,sort_keys=True,ensure_ascii=False))
    if len(fingerprints)!=1:return result(cell,'U','conflicting or differently bound records',records[0],conflictingRecords=deepcopy(records))
    rec=deepcopy(records[0]);rec['evidenceRefs']=sorted({ref for r in records for ref in r.get('evidenceRefs',[])})
    rec['normalizationOccurrences']=[{k:deepcopy(r[k]) for k in ['evidenceRefs','measurementNodePath','measurementCandidates','selectionCandidates'] if k in r} for r in original_records]
    if unresolved:rec['unresolvedRecords']=deepcopy(unresolved)
    if not rec['evidenceRefs']:return result(cell,'U','no raw evidence reference',rec)
    valid,why=context_ok(cell,rec)
    if not valid:return result(cell,'U',why,rec)
    kind=rec.get('evidenceKind');actual=rec.get('actual');expected=cell['expected']
    if op in ['screenshotReview','sourceReview','inputReview']:
        needed={'screenshotReview':'manual.screenshot','sourceReview':'manual.source','inputReview':'input.integrity'}[op]
        if kind!=needed:return result(cell,'U','required explicit review/input evidence not supplied',rec)
        status=VERDICTS.get(rec.get('reviewVerdict'),'U')
        return result(cell,status,rec.get('reviewReason') or 'no explicit completed review verdict',rec)
    if op=='physicalHitRegion':
        if kind!='native.physicalHit' or rec.get('capability')!='genuineOSPhysicalHitRegion':return result(cell,'U','semantic bounds/actions do not inspect OS physical hit region',rec)
        value,u,why=native_measurement(cell,rec)
        if why:return result(cell,'U',why,rec)
        status='P' if value-u>=expected else ('F' if value+u<expected else 'U')
        return result(cell,status,'physical-hit minimum interval comparison',rec,measurement=dict(value=value,unit=cell.get('unit'),uncertainty=u,interval=[value-u,value+u],minimum=expected))
    if op in ['eventSequence','transition']:
        ok,why=gate_ok(cell,rec,interval=op=='eventSequence')
        if not ok:return result(cell,'U',why,rec)
        need='native.events' if op=='eventSequence' else 'native.transition'
        if kind!=need:return result(cell,'U','actual native behavior evidence missing',rec)
        if rec.get('helperVerdict')=='unknown':return result(cell,'U',rec.get('helperReason','native helper unresolved'),rec)
        if op=='eventSequence' and not isinstance(actual,list):return result(cell,'U','complete actual event list missing',rec)
        if op=='transition':
            if not isinstance(actual,dict) or set(actual)!=set(expected) or any(v is None for v in actual.values()):return result(cell,'U','resulting native state vector incomplete',rec)
            if rec.get('helperVerdict') not in ['pass','fail']:return result(cell,'U','native state-evidence helper provenance absent',rec)
        return result(cell,'P' if strict_equal(actual,expected) else 'F','exact established immediate event sequence' if op=='eventSequence' else 'established requested stimulus and native resulting state',rec)
    if op=='stimulus':
        if kind!='native.stimulus':return result(cell,'U','native dispatch/update evidence missing',rec)
        # The immutable helper judges requested dispatch. This is a separate execution class.
        v=VERDICTS.get(rec.get('helperVerdict'),'U')
        return result(cell,v,rec.get('helperReason','immutable helper requested-stimulus verdict'),rec)
    if op=='completeCoverage':
        if kind!='native.coverage':return result(cell,'U','bounded native coverage evidence missing',rec)
        if rec.get('helperVerdict') not in ['pass','fail']:return result(cell,'U','complete exact-target/absence coverage unresolved',rec)
        return result(cell,'P' if actual is True else 'F','bounded native target coverage helper verdict',rec)
    if op=='presence':
        if kind!='native.presence' or type(actual) is not bool:return result(cell,'U','native presence fact missing',rec)
        if actual is False and rec.get('completeCoverage') is not True:return result(cell,'U','absence lacks completed bounded native coverage',rec)
        return result(cell,'P' if actual==expected else 'F','native presence/absence comparison',rec)
    if op in ['enabled','selected','expanded','name']:
        if kind!='native.'+op:return result(cell,'U','matching native semantic attribute missing',rec)
        if actual is None:return result(cell,'U','native semantic attribute unresolved',rec)
        return result(cell,'P' if strict_equal(actual,expected) else 'F','current native semantic fact; prior activation not required',rec)
    if cls=='runtime.style.native':
        # The frozen publicAX capability does not provide arbitrary SwiftUI style values.
        if cell['platform']=='ios':return result(cell,'U','iOS publicAX has no generic SwiftUI style inspector',rec)
        asp=cell['aspect']
        if asp.endswith('.fontSize'):
            if kind!='native.fontSize':return result(cell,'U','exported TextLayout font_sp missing',rec)
        elif asp.endswith('.fontWeight'):
            if kind!='native.fontWeight':return result(cell,'U','actual exported native font weight missing',rec)
        elif op=='color':
            if kind!='native.color':return result(cell,'U','actual exported native color missing',rec)
            prop='fill' if asp.endswith('.fill') or asp in ['tokens.surfaceColor','tokens.backgroundColor'] else 'textColor'
            if rec.get('nativeProperty')!=prop:return result(cell,'U','native color property does not establish requested text/fill property',rec)
        elif kind!='native.scalar':return result(cell,'U','actual exported native scalar style missing',rec)
    if op=='color':
        a=color(actual);e=color(expected)
        if a is None or e is None:return result(cell,'U','noncanonical or missing actual ARGB color',rec)
        return result(cell,'P' if a==e else 'F','exact native ARGB comparison',rec,canonicalActual=a,canonicalExpected=e)
    if op in ['scalar','minimum']:
        if op=='minimum' and kind!='native.bounds':return result(cell,'U','native semantic bounds missing',rec)
        value,u,why=native_measurement(cell,rec)
        if why:return result(cell,'U',why,rec)
        if op=='minimum':
            status='P' if value-u>=expected else ('F' if value+u<expected else 'U');tol=None
        else:
            tol=.75 if cell['aspect'].endswith('.fontSize') else 2.0
            status='P' if value-u>=expected-tol and value+u<=expected+tol else ('F' if value+u<expected-tol or value-u>expected+tol else 'U')
        return result(cell,status,'native interval comparison using frozen precision',rec,measurement=dict(value=value,unit=cell.get('unit'),uncertainty=u,interval=[value-u,value+u],epsilon=tol))
    if op=='equal':
        required='native.fontWeight' if cell['aspect'].endswith('.fontWeight') else 'native.text'
        if kind!=required:return result(cell,'U','matching actual native value missing',rec)
        if actual is None:
            return result(cell,'F' if rec.get('completeCoverage') is True else 'U','required target absent after completed coverage' if rec.get('completeCoverage') else 'target unobserved without complete coverage',rec)
        return result(cell,'P' if strict_equal(actual,expected) else 'F','exact current native fact; prior activation not required',rec)
    return result(cell,'U','operator has no implemented evidence adapter',rec)

def summarize(rows):
    def panel(selected):
        c=Counter(r['status'] for r in selected);n=sum(c[s] for s in ['P','F','U']);obs=c['P']+c['F']
        return dict(P=c['P'],F=c['F'],U=c['U'],NA=c['N/A'],denominator=n,passShare=c['P']/n if n else None,observedFraction=obs/n if n else None,conditionalPass=c['P']/obs if obs else None)
    out={'all':panel(rows),'byClass':{},'byPlatform':{},'byCase':{},'byCheckpoint':{},'public':panel([r for r in rows if (r.get('caseID') or '').startswith('P')]),'heldout':panel([r for r in rows if (r.get('caseID') or '').startswith('H')])}
    for key,name in [('classification','byClass'),('platform','byPlatform'),('caseID','byCase'),('stateID','byCheckpoint')]:
        groups=defaultdict(list)
        for r in rows:groups[str(r.get(key))].append(r)
        out[name]={g:panel(v) for g,v in sorted(groups.items())}
    return out

def grade(oracle,evidence):
    if evidence.get('stage') not in ['D0','FINAL','paired-D0']:raise ValueError('Only explicitly supplied native scoring stages may be graded; self-review is matched separately.')
    recs=defaultdict(list);known={c['cellID'] for c in oracle['cells']}
    for r in evidence.get('records',[]):recs[r['cellID']].append(r)
    rows=[grade_cell(c,recs[c['cellID']]) for c in oracle['cells']]
    return dict(schemaVersion=1,anonymousID=evidence['anonymousID'],stage=evidence['stage'],rawEvidence=evidence.get('rawEvidence',[]),rows=rows,summary=summarize(rows),unmappedEvidence=[r for r in evidence.get('records',[]) if r['cellID'] not in known])

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--oracle',type=Path,default=HERE/'oracle.json');ap.add_argument('--evidence',type=Path);ap.add_argument('--batch',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    if bool(a.evidence)==bool(a.batch):ap.error('Supply either --evidence or a simultaneously supplied two-arm --batch')
    oracle=json.loads(a.oracle.read_text())
    if a.evidence:
        output=grade(oracle,json.loads(a.evidence.read_text()))
    else:
        b=json.loads(a.batch.read_text());corpora=b.get('corpora',[])
        if len(corpora)!=2 or len({c['anonymousID'] for c in corpora})!=2:raise ValueError('A batch must explicitly supply both distinct anonymous corpora.')
        evidences=[json.loads((a.batch.parent/c['normalizedEvidence']).read_text()) for c in corpora]
        if any(e['stage']!=b['stage'] for e in evidences):raise ValueError('Do not mix or predict stages.')
        output=dict(schemaVersion=1,stage=b['stage'],corpora=[grade(oracle,e) for e in evidences])
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'output':str(a.out),'sha256':hashlib.sha256(a.out.read_bytes()).hexdigest()},indent=2))

if __name__=='__main__':main()
