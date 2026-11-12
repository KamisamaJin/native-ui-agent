from harness import *

BASE=project('source-duty',source_duty=True)
def source_missing():
 first,_,_=command('feedback',BASE)
 v,r,o=command('final-missing-source',BASE,extra=['--final'])
 assert_that(v['status']=='review_source' and v['capture_reused'] and not v['native_executed'],'required missing source duty did not block adopted final')
 return {'cycle':str(o/'cycle.json'),'status':v['status'],'blocking':v['evidence_responsibility']['blocking_claims']}
check('source-duty-missing-blocks-final',source_missing)

def bind_source(name,actual):
 file=BASE/'production'/'ios'/'Component.swift';submission=save(BASE/(name+'.json'),{'version':1,'observations':[{'id':'source-duty','observed':actual,'reason':'HOST controlled source line 1 contains Ready; conflicting response deliberately supplied' if not actual else 'HOST actual source line 1 contains Ready.','citations':[{'path':str(file),'line':1}]}]})
 _,record,out=command(name,BASE,action='bind-source-review',extra=['--submission',submission])
 return json.loads(record['stdout'])

def source_closes():
 ref=bind_source('source-actual-true',True)
 cycle=BASE/'evidence'/'final-missing-source'/'cycle.json'
 v,r,o=command('finish-current-source',BASE,action='finish-native-review',extra=['--cycle',cycle,'--cycle-sha256',sha(cycle)])
 assert_that(v['status']=='accepted' and r['simulated_collection_count']==0,'bound source actual did not close original final evidence')
 return {'completion':str(o/'completion.json'),'source_receipt':ref,'collector_count':0}
check('source-duty-bound-current-closes-original',source_closes)

def source_conflict():
 ref=bind_source('source-actual-conflict',False)
 cycle=BASE/'evidence'/'final-missing-source'/'cycle.json'
 v,r,o=command('finish-conflicting-source',BASE,action='finish-native-review',extra=['--cycle',cycle,'--cycle-sha256',sha(cycle)],expect=1)
 assert_that(v['status']=='not_accepted' and r['simulated_collection_count']==0,'conflicting source observations accepted or triggered redundant collector')
 admission=d.load(o/'admission.json');row=admission['evidence_responsibility']['rows'][0]
 assert_that(row['status']=='unassessed' and 'Conflicting' in row['reason'],'source disagreement was overwritten')
 return {'completion':str(o/'completion.json'),'source_receipt':ref,'row':row}
check('source-duty-conflict-stays-unresolved',source_conflict)

# Completion identity controls begin from an independent pending task each time.
def invalid_completion_proof(kind):
 base=project('repair-proof-'+kind,broken=True);v,_,o=command('failure',base);task=o/'repair-task.json'
 (base/'production'/'ios'/'Component.swift').write_text('Ready\n')
 v,r,c=command('complete',base,action='complete-native-repair',extra=['--task',task,'--task-sha256',sha(task)])
 state=d.load(base/'workflow'/'ios.json');path=Path(state['completion']['path']);original=path.read_bytes()
 pristine=ROOT/'raw'/('original-repair-completion-'+kind+'.json');pristine.write_bytes(original)
 if kind=='missing':path.unlink()
 else:
  data=d.load(path);data['measured_changed_files']=['FOREIGN.swift'];save(path,data)
 v,r,o=command('next-with-'+kind+'-proof',base,expect=2)
 assert_that(v is None and r['simulated_collection_count']==0,'invalid completion proof was ignored')
 cleanup(base,label='explicit-cleanup')
 return {'raw':str(ROOT/'raw'/(base.name+'--next-with-'+kind+'-proof.command.json')),'original_proof':str(pristine),'stderr':r['stderr']}
check('missing-completion-proof-blocks-default',lambda:invalid_completion_proof('missing'))
check('tampered-completion-proof-blocks-default',lambda:invalid_completion_proof('tampered'))

save(ROOT/'raw'/'source-results.json',RESULTS)
