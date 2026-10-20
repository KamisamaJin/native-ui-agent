#!/usr/bin/env python3
"""Audit original plan values against independent design; never fill them for claims."""
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
from decimal import Decimal
R=Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def equivalent(options,row,m):
 expected=row['expected']
 if type(expected)in(int,float):
  def interval(a):
   if type(a.get('expected'))not in(int,float):return None
   v=Decimal(str(a['expected']));op=a.get('op','eq')
   if op=='eq':return(v,v)
   if op=='gte':return(v,None)
   if op=='lte':return(None,v)
   if op=='near'and type(a.get('tolerance'))in(int,float):
    t=Decimal(str(a['tolerance']));return(v-t,v+t)
   return None
  wanted=interval(dict(expected=expected,op=row['op'],tolerance=row['tolerance']));intervals=[interval(a)for a in options]
  if wanted and intervals and all(x is not None for x in intervals):
   lower=[x[0]for x in intervals if x[0]is not None];upper=[x[1]for x in intervals if x[1]is not None]
   return(max(lower)if lower else None,min(upper)if upper else None)==wanted
  return False
 return any('expected'in a and m.canonical(m.normalize_expected(a['expected'],row['unit']))==m.canonical(m.normalize_expected(expected,row['unit']))for a in options)

def main():
 p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');args=p.parse_args();table=read(R/'design/private/acceptance-table.json')['rows'];s=importlib.util.spec_from_file_location('sourceaudit_oracle',R/'design/private/grader.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);out={}
 assignment=read(R/'private/ASSIGNMENT-RELEASE.json')
 for alias,unit in assignment['gradeAliases'].items():
  ledger=[];extra=[];proofs=[]
  for case in ['P1','P2']:
   for platform in ['ios','android']:
    path=R/'submissions'/unit/'initial-agent-output/plans'/case/platform/'plan.json';plan=read(path);parts={};needed=[r for r in table if r['case']==case and r['platform']==platform and r['applicable']]
    for a in plan['assertions']:parts.setdefault((a.get('state'),a.get('requirement_id')),[]).append(a)
    for r in needed:
     options=parts.get((r['state'],r['requirement']),[]);same=[a for a in options if 'expected'in a and m.canonical(m.normalize_expected(a['expected'],r['unit']))==m.canonical(m.normalize_expected(r['expected'],r['unit']))];chosen=same[0]if same else options[0]if options else None
     ledger.append({'id':r['id'],'constraintEquivalent':equivalent(options,r,m),'approvedExpected':r['expected'],'approvedUnit':r['unit'],'candidateAssertionIDs':[a['id']for a in options],'valueStatus':'agree'if same else'constraint_equivalent'if equivalent(options,r,m)else'wrong'if options else'missing','candidateExpected':chosen.get('expected')if chosen else None,'candidateUnit':chosen.get('unit')if chosen else None,'candidateKind':chosen.get('kind')if chosen else None,'candidateOperator':chosen.get('op','eq')if chosen else None,'approvedOperator':r['op'],'approvedTolerance':r['tolerance'],'candidateTolerance':chosen.get('tolerance')if chosen else None,'scope':'Value agreement is independent audit, not proof runtime checker enforces identical precision/method or complete style observation.'})
    if 'design_contract'in plan:
     sys.path.insert(0,str(R/'candidate-v6/scripts'));import design_contract as dc
     dc.verify_generated(plan,read(R/'design/public/design-lock.json'),read(R/'design/private/DESIGN-SEAL.json')['public_design_lock_canonical_sha256'],platform);proofs.append({'case':case,'platform':platform,'verified':True,'planSHA256':sha(path)})
  out[alias]={'rows':ledger,'counts':{k:sum(r['valueStatus']==k for r in ledger)for k in ['agree','constraint_equivalent','wrong','missing']},'generatedProvenanceChecks':proofs,'scope':'Public applicable rows only; extra plan assertions remain in original files and do not increase this fixed denominator. Unit omission does not become a typed proof. No acceptance value is inserted into original detection claims.'}
 target=R/'expectation-audit.json'
 if args.write:target.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
 else:assert read(target)==out
 print(json.dumps({'status':'PASS','counts':{a:x['counts']for a,x in out.items()}}))
if __name__=='__main__':main()
