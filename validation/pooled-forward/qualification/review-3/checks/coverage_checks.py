from harness import *

def incomplete():
 base=project('coverage-incomplete')
 v,r,o=command('missing-second-state',base,env_extra={'REVIEW_DROP_STATE':'second'})
 capture=d.load(Path(v['capture_result']));report=d.load(Path(v['capture_result']).parent/'automatic.json')
 assert_that(not capture['coverage_satisfied'] and report['counts']=={'passed':1,'failed':0,'unassessed':1},'incomplete packet dropped or changed mandatory P/U denominator')
 first_sha=v['capture_sha256']
 v,r,o=command('final-still-incomplete',base,extra=['--final'],env_extra={'REVIEW_DROP_STATE':'second'})
 assert_that(v['status']!='accepted' and v['native_executed'] and not v['capture_reused'],'incomplete full-marker packet relabeled as accepted')
 post=d.load(o/'capture'/'automatic.json')
 assert_that(post['counts']=={'passed':1,'failed':0,'unassessed':1},'final incomplete work changed raw denominator')
 v,r,final=command('final-reacquire-complete',base,extra=['--final'])
 assert_that(v['status']=='accepted' and v['native_executed'] and not v['capture_reused'] and v['capture_sha256']!=first_sha,'missing evidence did not force new complete collection')
 return {'initial_capture':str(base/'evidence'/'missing-second-state'/'capture'/'result.json'),'incomplete_final':str(o/'cycle.json'),'new_complete_final':str(final/'cycle.json'),'mandatory_count':2,'raw_incomplete_status_counts':report['counts']}
check('incomplete-full-packet-retains-U-and-reacquires',incomplete)

def torn():
 base=project('coverage-torn')
 v,r,o=command('torn-native-epoch',base,extra=['--final'],env_extra={'REVIEW_TORN_CAPTURE':'1'})
 capture=d.load(Path(v['capture_result']));report=d.load(Path(v['capture_result']).parent/'automatic.json')
 assert_that(v['status']!='accepted' and not capture['coverage_satisfied'] and report['counts']=={'passed':0,'failed':0,'unassessed':2},'torn hierarchy/image epoch earned native credit or lost mandatory rows')
 cleanup(base,label='explicit-cleanup')
 return {'cycle':str(o/'cycle.json'),'counts':report['counts'],'reasons':[r['reason'] for r in report['assertions']]}
check('torn-epoch-retains-all-mandatory-U',torn)
save(ROOT/'raw'/'coverage-results.json',RESULTS)
