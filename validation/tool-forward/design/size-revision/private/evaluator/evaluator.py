#!/usr/bin/env python3
"""Independent, member-complete evidence ledger assembler. No native evidence is inferred.

prepare/self-check read only this evaluator's frozen design. assemble is intentionally
unusable until an actual evidence packet and explicitly permitted paths are supplied.
Raw legacy layouts are normalized by a reviewer/adapter after their paths are authorized;
no new raw metadata schema is required. This program never fixes candidate source.
"""
from __future__ import annotations
import argparse,copy,datetime,hashlib,json,pathlib,re,sys

HERE=pathlib.Path(__file__).resolve().parent
REV=HERE.parent.parent
ORACLE=REV/'private/oracle.json'
EXPECTED_ORACLE_SHA='3728d2961548354f866dc0490cd4d05b5513a9bd81813b8e45234bc0620c875b'
EXPECTED_COUNTS={'D0':2209,'FINAL':2897}
OUTCOMES={'PASS','FAIL','UNASSESSED'}
SOURCE_EXTENSIONS={'.swift','.kt','.kts','.m','.mm','.h','.hpp','.py','.sh','.js','.jsx','.ts','.tsx','.java','.c','.cpp'}
SOURCE_AUDIT_EXTENSIONS={'.swift','.kt','.kts','.m','.mm','.h','.hpp','.java','.gradle','.properties','.pbxproj','.xcconfig','.xml','.toml'}
METHOD_KINDS={
 'renderedPixels':{'actualNativeScreenshot','imageDerivedObservation'},
 'nativeBounds':{'actualNativeLayoutFrame','actualAccessibilityFrame','actualNativeHitRegionInstrumentation','actualHitTestTrace','actualPhysicalTouchTrace'},
 'nativeSemantics':{'actualNativeSemantics','actualNativeExecutionTrace'},
 'callbackTrace':{'actualCallbackTrace','actualNativeExecutionTrace'},
 'nativeInteraction':{'actualNativeExecutionTrace','actualNativeEnvironmentObservation'},
 'nativeTypography':{'actualResolvedRuntimeFont'},
 'sourceAudit':{'anonymousSource'},
}
PHYSICAL_KINDS={'actualNativeHitRegionInstrumentation','actualHitTestTrace','actualPhysicalTouchTrace'}
PHYSICAL_ACTIVATION={'osPhysicalTap','iosXCUITap','androidInjectedTouchGesture','nativePhysicalTap'}
ACCESSIBLE_ACTIVATION={'accessibilityPerformAction','iosAXPerformAction','androidAccessibilityActionClick','androidNativeSemanticOnClick'}


def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()
def read_json(path:pathlib.Path):return json.loads(path.read_text())
def canonical(value)->bytes:return json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')
def write_json(path:pathlib.Path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def frozen_oracle():
    data=ORACLE.read_bytes()
    if sha(data)!=EXPECTED_ORACLE_SHA:raise ValueError('Frozen selected oracle hash mismatch; do not substitute a changed contract.')
    return json.loads(data)

def concrete_assertions(state):
    for a in state['assertions']:
        yield copy.deepcopy(a),None
    for group in state['parameterizedGroups']:
        inherited={k:copy.deepcopy(v) for k,v in group.items() if k not in {'members','groupKey','coveragePolicy'}}
        for member in group['members']:
            item=copy.deepcopy(inherited);item.update(copy.deepcopy(member))
            item['parameterizedGroupKey']=group['groupKey']
            item['memberCoveragePolicy']=group['coveragePolicy']
            yield item,group['groupKey']

def collection_scope(assertion,state):
    criterion=assertion['criterion']
    if criterion in {'actualCapturedFieldIdSetEquals','documentedIdentifierSetEquals','visibleDocumentedRegionsEqual','majorRegionFlowEquals'}:
        return {'coverageIds':assertion['expected'],'comparison':'ordered-sequence' if criterion=='majorRegionFlowEquals' else 'set'}
    if criterion in {'overlappingMeaningfulRegionPairsEqual','horizontalOverflowRegionIdsEqual'}:
        return {'coverageIds':state.get('visualInventory',{}).get('allVisibleFieldIds',[]),'comparison':'empty-violation-set-over-observed-scope'}
    return None

def expand(oracle,phase):
    if phase not in EXPECTED_COUNTS:raise ValueError('Unknown phase')
    contexts={};rows=[]
    def append(item,context_id=None,state=None):
        for platform in item['platforms']:
            row=copy.deepcopy(item)
            row['platform']=platform;row['assessmentId']=platform+'::'+item['key']
            row['contextId']=context_id;row['phase']=phase
            row['sourceOnly']=item['aspect'] in {'sourceOnlyAPI','sourceOnlyCompatibility'}
            row['collectionScope']=collection_scope(item,state) if state else None
            rows.append(row)
    for a in oracle['sourceAssertions']:append(a)
    for case in oracle['cases']:
        if phase=='D0' and case['split']!='initial':continue
        previous=None
        for state in case['checkpoints']:
            cid=case['caseId']+'/'+state['stateId']
            model=case['models'][state['modelId']]
            contexts[cid]={
                'caseId':case['caseId'],'split':case['split'],'stateId':state['stateId'],
                'modelId':state['modelId'],'model':model,'modelSha256':sha(canonical(model)),
                'environment':case['environment'],'environmentSha256':sha(canonical(case['environment'])),
                'trigger':state['trigger'],'previousStateId':previous,
                'fullVisualCheckpoint':state['fullVisualCheckpoint'],'captureScope':state['captureScope'],
                'focusedVisualTargets':state.get('focusedVisualTargets',[]),
                'visualInventory':state.get('visualInventory'),'coverageNotes':state.get('coverageNotes',[]),
            }
            for a,group in concrete_assertions(state):append(a,cid,state)
            previous=state['stateId']
    ids=[r['assessmentId'] for r in rows]
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate platform/key after expansion')
    if len(rows)!=EXPECTED_COUNTS[phase]:raise ValueError(f'{phase} count mismatch: {len(rows)}')
    return {'schemaVersion':1,'phase':phase,'oracleSHA256':EXPECTED_ORACLE_SHA,'requiredAssessmentCount':len(rows),'assessments':rows},contexts

def prepare():
    oracle=frozen_oracle()
    info={}
    for phase in ['D0','FINAL']:
        plan,contexts=expand(oracle,phase)
        write_json(HERE/('expanded-'+phase+'.json'),plan)
        write_json(HERE/('contexts-'+phase+'.json'),{'schemaVersion':1,'phase':phase,'oracleSHA256':EXPECTED_ORACLE_SHA,'contexts':contexts})
        counts={p:sum(r['platform']==p for r in plan['assessments']) for p in ['android','apple']}
        info[phase]={'total':len(plan['assessments']),'byPlatform':counts,'contexts':len(contexts),'runtime':sum(not r['sourceOnly'] for r in plan['assessments']),'source':sum(r['sourceOnly'] for r in plan['assessments'])}
    return info


def beneath(path:pathlib.Path,roots:list[pathlib.Path])->bool:
    resolved=path.resolve()
    return any(resolved==root.resolve() or (root.is_dir() and root.resolve() in resolved.parents) for root in roots)

def kind_admissible(row,record):
    """Content-class guards; no raw metadata fields are required by these rules."""
    method=record.get('method');kind=record.get('kind')
    if method not in row['allowedEvidenceMethods']:return False,'Required evidence class is '+','.join(row['allowedEvidenceMethods'])
    if kind not in METHOD_KINDS.get(method,set()):return False,'This observation kind cannot establish the required native property'
    if row['sourceOnly'] and kind!='anonymousSource':return False,'Only an anonymous source audit establishes this source-only predicate'
    if not row['sourceOnly'] and kind=='anonymousSource':return False,'Source declarations do not establish a runtime property'
    if row['criterion']=='minimumTouchBounds' and kind not in PHYSICAL_KINDS:
        return False,'Accessibility/layout frames do not establish physical hit bounds; actual native hit-region or physical hit-test evidence is required'
    if method=='nativeTypography' and kind!='actualResolvedRuntimeFont':
        return False,'Source font declarations are not resolved runtime typography'
    if row['criterion']=='executedNativeActivation':
        mechanism=record.get('observedActivationMechanism')
        requested=row['expected']['method']
        if mechanism=='blockedBeforeDispatch':
            return False,'Observer declined dispatch; actual activation of the native control was not exercised'
        if requested=='tap' and mechanism not in PHYSICAL_ACTIVATION:
            return False,'Requested physical tap is not established by the observed activation mechanism'
        if requested=='accessibilityActivate' and mechanism not in ACCESSIBLE_ACTIVATION:
            return False,'Requested accessibility activation is not established by the observed activation mechanism'
    return True,None


def validate_ref(ref,row,allowed_evidence,allowed_source):
    path=pathlib.Path(ref['path'])
    if not path.is_absolute():raise ValueError('Exact raw source paths must be absolute')
    roots=allowed_source if row['sourceOnly'] else allowed_evidence
    if not beneath(path,roots):raise ValueError('Raw path is outside the explicitly permitted scope: '+str(path))
    if not row['sourceOnly'] and path.suffix.lower() in SOURCE_EXTENSIONS:
        raise ValueError('A source/script file cannot substitute for runtime evidence and is not read for runtime grading')
    if row['sourceOnly'] and path.suffix.lower() not in SOURCE_AUDIT_EXTENSIONS:
        raise ValueError('Only actual source/build-declaration files are read for sourceAssertions; no reviews, README, skill or outcome documents')
    if not path.is_file():raise ValueError('Permitted raw evidence file does not exist: '+str(path))
    data=path.read_bytes()
    if not data:raise ValueError('Raw evidence file is empty: '+str(path))
    digest=sha(data)
    if ref.get('sha256') and ref['sha256']!=digest:raise ValueError('Raw evidence hash mismatch: '+str(path))
    locator=ref.get('locator',{'kind':'whole-file'})
    if locator.get('kind')=='lines':
        lines=data.decode('utf-8').splitlines();start=locator['start'];end=locator.get('end',start)
        if not (1<=start<=end<=len(lines)):raise ValueError('Raw source line locator is out of range')
    if locator.get('kind')=='json-pointer':
        value=json.loads(data);pointer=locator.get('pointer','')
        if pointer:
            if not pointer.startswith('/'):raise ValueError('Invalid JSON pointer')
            for token in pointer[1:].split('/'):
                token=token.replace('~1','/').replace('~0','~')
                value=value[int(token)] if isinstance(value,list) else value[token]
    return {'path':str(path.resolve()),'sha256':digest,'locator':locator}


def binding_problems(binding,row,context,packet):
    problems=[]
    if binding.get('candidateId')!=packet['candidateId']:problems.append('candidate identity not bound')
    if binding.get('sourceSnapshotId')!=packet['sourceSnapshotId']:problems.append('anonymous source snapshot not bound')
    if binding.get('platform')!=row['platform']:problems.append('platform not bound')
    if not binding.get('basis'):problems.append('binding basis not recorded')
    if not binding.get('explanation'):problems.append('binding explanation not recorded')
    if context:
        for k in ['caseId','stateId','modelId','modelSha256','environmentSha256']:
            if binding.get(k)!=context[k]:problems.append(k+' not bound to this exact checkpoint/input')
    return problems


def assemble(phase,candidate,packet_path,ledger_path,out_path,allowed_evidence,allowed_source):
    # This guard prevents pre-evidence grading. prepare never creates outcome rows.
    if not allowed_evidence:raise ValueError('Actual raw evidence and explicit permitted evidence scope are required before grading')
    if HERE not in out_path.resolve().parents:raise ValueError('Results must be new files under this evaluator directory')
    if out_path.exists():raise ValueError('Never overwrite an existing assessment or preparation artifact; use a new result path')
    plan,contexts=expand(frozen_oracle(),phase)
    packet=read_json(packet_path);ledger=read_json(ledger_path)
    if packet.get('candidateId')!=candidate or packet.get('phase')!=phase:raise ValueError('Packet identity/phase mismatch')
    if not packet.get('sourceSnapshotId'):raise ValueError('Anonymous source-snapshot binding is required')
    records=packet.get('records',[])
    if not records:raise ValueError('Do not grade without actual raw evidence records')
    if len({r['id'] for r in records})!=len(records):raise ValueError('Duplicate evidence record ID')
    records={r['id']:r for r in records}
    # Confirm at least one real permitted runtime artifact before producing any result.
    present=False
    for record in records.values():
        if record.get('method')=='sourceAudit':continue
        for ref in record.get('rawRefs',[]):
            path=pathlib.Path(ref['path'])
            if path.is_absolute() and beneath(path,allowed_evidence) and path.is_file() and path.stat().st_size>0 and path.suffix.lower() not in SOURCE_EXTENSIONS:
                present=True
    if not present:raise ValueError('No actual permitted raw runtime artifact was supplied; grading has not begun')
    if ledger.get('candidateId')!=candidate or ledger.get('phase')!=phase:raise ValueError('Ledger identity/phase mismatch')
    entries=ledger.get('assessments',[])
    if len({e['assessmentId'] for e in entries})!=len(entries):raise ValueError('Duplicate assessment decision; resolve conflicting observations explicitly')
    entries={e['assessmentId']:e for e in entries}
    valid_ids={r['assessmentId'] for r in plan['assessments']}
    if set(entries)-valid_ids:raise ValueError('Ledger includes unknown/nonselected assessment keys')
    results=[]
    for row in plan['assessments']:
        entry=entries.get(row['assessmentId']);context=contexts.get(row['contextId'])
        outcome='UNASSESSED';reason='No assessment-bound adequate raw observation has been entered.'
        exact=[];considered=[];accepted=[];rejections=[];binding={};coverage=[]
        if entry:
            requested=entry.get('outcome')
            if requested not in OUTCOMES:raise ValueError('Unknown outcome in ledger')
            binding=entry.get('binding',{});coverage=entry.get('observedCoverageIds',[])
            issues=binding_problems(binding,row,context,packet)
            if entry.get('conflictingEvidenceRecordIds'):issues.append('unresolved contradictory raw observations')
            for eid in entry.get('evidenceRecordIds',[]):
                record=records.get(eid)
                if not record:rejections.append('Unknown evidence record '+eid);continue
                adequate,why=kind_admissible(row,record)
                if not record.get('rawRefs'):rejections.append(eid+': no exact raw source reference');continue
                if not row['sourceOnly'] and record.get('kind')=='anonymousSource':
                    rejections.append(eid+': source reference was not opened for a runtime assertion');continue
                try:
                    refs=[validate_ref(ref,row,allowed_evidence,allowed_source) for ref in record['rawRefs']]
                except (ValueError,KeyError,UnicodeError,json.JSONDecodeError) as err:
                    rejections.append(eid+': '+str(err));continue
                considered.extend(dict(ref,method=record['method'],kind=record['kind'],evidenceRecordId=eid) for ref in refs)
                if not adequate:rejections.append(eid+': '+why);continue
                exact.extend(dict(ref,method=record['method'],kind=record['kind'],evidenceRecordId=eid) for ref in refs);accepted.append(eid)
            if requested in {'PASS','FAIL'}:
                if not accepted:issues.append('no adequate actual evidence of the required method')
                if not entry.get('reason'):issues.append('no concrete observation/reason recorded')
                if row.get('parameterizedGroupKey') and not coverage:issues.append('actual row/field member coverage not recorded')
                scope=row.get('collectionScope')
                if scope:
                    observed=entry.get('collectionCoverage',{})
                    actual=entry.get('actualObservedSet')
                    counterexample=entry.get('counterexample',{})
                    direct_counterexample=bool(counterexample.get('description') and counterexample.get('targetIds') and counterexample.get('evidenceRecordIds') and all(eid in accepted for eid in counterexample['evidenceRecordIds']))
                    # A real counterexample can establish FAIL without observing every
                    # other row. PASS always needs the complete required observation scope.
                    if requested=='PASS' or not direct_counterexample:
                        for target in scope['coverageIds']:
                            status=observed.get(target)
                            if status not in {'OBSERVED','ABSENT_OBSERVED'}:issues.append('unobserved collection entry: '+str(target))
                        if actual is None:issues.append('actual observed collection not recorded')
                    if requested=='PASS':
                        if any(v=='ABSENT_OBSERVED' for v in observed.values()):issues.append('PASS conflicts with observed absent required collection entry')
                        if actual is not None:
                            equal=actual==row['expected'] if scope['comparison']=='ordered-sequence' else {canonical(x) for x in actual}=={canonical(x) for x in row['expected']}
                            if not equal:issues.append('PASS conflicts with actual collection mismatch')
                    if requested=='FAIL' and not direct_counterexample and actual is not None:
                        equal=actual==row['expected'] if scope['comparison']=='ordered-sequence' else {canonical(x) for x in actual}=={canonical(x) for x in row['expected']}
                        if equal:issues.append('FAIL has neither a collection mismatch nor a direct counterexample')
                if issues:
                    reason='Unsupported for this exact predicate: '+'; '.join(issues)
                else:outcome=requested;reason=entry['reason']
            else:reason=entry.get('reason') or 'Required observation is inaccessible or insufficient.'
        else:issues=[]
        result={k:row[k] for k in ['assessmentId','key','platform','phase','contextId','aspect','target','criterion','expected','requirementRefs','sourceOnly']}
        required_binding={'candidateId':candidate,'sourceSnapshotId':packet['sourceSnapshotId'],'platform':row['platform']}
        if context:required_binding.update({k:context[k] for k in ['caseId','stateId','modelId','modelSha256','environmentSha256']})
        binding_status='ESTABLISHED' if binding and not binding_problems(binding,row,context,packet) else 'UNASSESSED'
        result.update(outcome=outcome,exactSources=exact,consideredSources=considered,acceptedEvidenceRecordIds=accepted,rejectedEvidence=rejections,requiredBinding=required_binding,binding=binding,bindingStatus=binding_status,observedCoverageIds=coverage,collectionCoverage=entry.get('collectionCoverage',{}) if entry else {},actualObservedSet=entry.get('actualObservedSet') if entry else None,counterexample=entry.get('counterexample') if entry else None,missingEvidenceMethod=row['allowedEvidenceMethods'] if outcome=='UNASSESSED' else [],missingEvidenceDetail=reason if outcome=='UNASSESSED' else None,reason=reason)
        if row.get('parameterizedGroupKey'):result['parameterizedGroupKey']=row['parameterizedGroupKey']
        results.append(result)
    report={'schemaVersion':1,'candidateId':candidate,'phase':phase,'sourceSnapshotId':packet['sourceSnapshotId'],'oracleSHA256':EXPECTED_ORACLE_SHA,'planSHA256':sha(canonical(plan)),'generatedAtUTC':now(),'packetExactSource':{'path':str(packet_path.resolve()),'sha256':sha(packet_path.read_bytes())},'ledgerExactSource':{'path':str(ledger_path.resolve()),'sha256':sha(ledger_path.read_bytes())},'requiredAssessmentCount':len(results),'results':results,'rollups':rollups(results)}
    validate_report(report)
    out_path.parent.mkdir(parents=True,exist_ok=True)
    write_json(out_path,report)
    return report['rollups']


def rollup(values):
    counts={o:sum(v['outcome']==o for v in values) for o in ['PASS','FAIL','UNASSESSED']}
    status='FAIL' if counts['FAIL'] else 'INCOMPLETE' if counts['UNASSESSED'] else 'PASS'
    return {'status':status,'counts':counts,'total':len(values)}

def rollups(rows):
    rules={}
    for platform in ['android','apple']:
        for ref in ['P01','P02','P03','P04','P05','P06','P07']:
            matches=[r for r in rows if r['platform']==platform and ref in r['requirementRefs']]
            rules[platform+'/'+ref]=rollup(matches)
    return {'overall':rollup(rows),'platforms':{p:rollup([r for r in rows if r['platform']==p]) for p in ['android','apple']},'publicRules':rules,'scopeWarning':'Strict rollups apply to enumerated mandatory predicates only. They do not assert unexamined details or an exhaustive input cross-product.'}

def validate_report(report):
    plan,contexts=expand(frozen_oracle(),report['phase'])
    actual=report['results'];expected={a['assessmentId'] for a in plan['assessments']}
    if len(actual)!=len(expected) or {a['assessmentId'] for a in actual}!=expected:raise ValueError('Every required platform/key must appear exactly once')
    if len({a['assessmentId'] for a in actual})!=len(actual):raise ValueError('Duplicate result key')
    planned={a['assessmentId']:a for a in plan['assessments']}
    if report['requiredAssessmentCount']!=len(expected) or report['oracleSHA256']!=EXPECTED_ORACLE_SHA:raise ValueError('Report contract/count mismatch')
    for row in actual:
        original=planned[row['assessmentId']]
        for field in ['key','platform','phase','contextId','aspect','target','criterion','expected','requirementRefs','sourceOnly']:
            if row[field]!=original[field]:raise ValueError('Report changed frozen assertion metadata: '+field)
        if row['outcome'] not in OUTCOMES:raise ValueError('Invalid outcome')
        if row['outcome']=='UNASSESSED' and not row.get('missingEvidenceMethod'):raise ValueError('UNASSESSED requires explicit missingEvidenceMethod')
        if row['outcome'] in {'PASS','FAIL'}:
            if not row.get('exactSources') or not row.get('binding'):raise ValueError('Decisive outcomes require exact raw sources and binding')
            if row.get('missingEvidenceMethod'):raise ValueError('A decisive outcome cannot simultaneously lack its required method')
            if row.get('bindingStatus')!='ESTABLISHED' or binding_problems(row['binding'],original,contexts.get(original['contextId']),report):raise ValueError('Decisive outcome binding is not established')
    if report['rollups']!=rollups(actual):raise ValueError('Strict rollups do not match the actual atomic outcomes')
    for summary in report['rollups']['publicRules'].values():
        if summary['status']=='PASS' and summary['counts']['UNASSESSED']:raise ValueError('Partial-rule PASS is prohibited')
    return True


def self_check():
    oracle=frozen_oracle();d0,dc=expand(oracle,'D0');final,fc=expand(oracle,'FINAL')
    assert len(d0['assessments'])==2209 and len(final['assessments'])==2897
    assert sum(not x['sourceOnly'] for x in d0['assessments'])==1830
    assert sum(not x['sourceOnly'] for x in final['assessments'])==2518
    assert sum(x['sourceOnly'] for x in final['assessments'])==379
    minimum=next(x for x in final['assessments'] if x['criterion']=='minimumTouchBounds')
    assert not kind_admissible(minimum,{'method':'nativeBounds','kind':'actualAccessibilityFrame'})[0]
    assert not kind_admissible(minimum,{'method':'nativeBounds','kind':'actualNativeLayoutFrame'})[0]
    assert kind_admissible(minimum,{'method':'nativeBounds','kind':'actualHitTestTrace'})[0]
    font=next(x for x in final['assessments'] if x['aspect']=='nativeTypography')
    assert not kind_admissible(font,{'method':'sourceAudit','kind':'anonymousSource'})[0]
    assert kind_admissible(font,{'method':'nativeTypography','kind':'actualResolvedRuntimeFont'})[0]
    tap=next(x for x in final['assessments'] if x['criterion']=='executedNativeActivation' and x['expected']['method']=='tap')
    ax=next(x for x in final['assessments'] if x['criterion']=='executedNativeActivation' and x['expected']['method']=='accessibilityActivate')
    assert not kind_admissible(tap,{'method':'nativeInteraction','kind':'actualNativeExecutionTrace','observedActivationMechanism':'androidNativeSemanticOnClick'})[0]
    assert kind_admissible(tap,{'method':'nativeInteraction','kind':'actualNativeExecutionTrace','observedActivationMechanism':'iosXCUITap'})[0]
    assert not kind_admissible(ax,{'method':'nativeInteraction','kind':'actualNativeExecutionTrace','observedActivationMechanism':'iosXCUITap'})[0]
    assert kind_admissible(ax,{'method':'nativeInteraction','kind':'actualNativeExecutionTrace','observedActivationMechanism':'androidNativeSemanticOnClick'})[0]
    assert not kind_admissible(tap,{'method':'nativeInteraction','kind':'actualNativeExecutionTrace','observedActivationMechanism':'blockedBeforeDispatch'})[0]
    role=next(x for x in final['assessments'] if x['aspect']=='nativeSemantics')
    assert not kind_admissible(role,{'method':'renderedPixels','kind':'actualNativeScreenshot'})[0]
    assert rollup([{'outcome':'PASS'},{'outcome':'UNASSESSED'}])['status']=='INCOMPLETE'
    assert rollup([{'outcome':'FAIL'},{'outcome':'UNASSESSED'}])['status']=='FAIL'
    assert len(dc)==35 and len(fc)==47
    return {'selfCheck':'PASS','D0':{'total':2209,'runtime':1830,'source':379},'FINAL':{'total':2897,'runtime':2518,'source':379},'candidateFilesRead':0,'businessOutcomesProduced':0}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('prepare');sub.add_parser('self-check')
    v=sub.add_parser('validate-report');v.add_argument('report',type=pathlib.Path)
    a=sub.add_parser('assemble');a.add_argument('--phase',choices=['D0','FINAL'],required=True);a.add_argument('--candidate',required=True)
    a.add_argument('--packet',type=pathlib.Path,required=True);a.add_argument('--ledger',type=pathlib.Path,required=True);a.add_argument('--out',type=pathlib.Path,required=True)
    a.add_argument('--permit-evidence',type=pathlib.Path,action='append',default=[]);a.add_argument('--permit-source',type=pathlib.Path,action='append',default=[])
    args=parser.parse_args()
    if args.command=='prepare':result=prepare()
    elif args.command=='self-check':result=self_check()
    elif args.command=='validate-report':result={'valid':validate_report(read_json(args.report))}
    else:result=assemble(args.phase,args.candidate,args.packet,args.ledger,args.out,args.permit_evidence,args.permit_source)
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
