#!/usr/bin/env python3
"""Observed phase wall times; no monetary/token cost or success inferred."""
import json
import study as s
R=s.R

def main():
 author=s.read(R/'submissions/initial-author-output/initial.json');start=s.read(R/'operators/author-start.json')['dispatchedAtUnix'];author_seconds=author['finishedAtUnix']-start
 d0=s.read(R/s.read(R/'operators/active-D0.json')['path']/'corpus.json');d0_native_seconds=d0['finishedAtUnix']-d0['startedAtUnix'];review=s.read(R/'operators/d0-review-endpoint.json');d0_review_seconds=review['finishedAtUnix']-review['startedAtUnix'];d0_seconds=d0_native_seconds+d0_review_seconds;release=s.read(R/'RELEASE.json')['releasedAtUnix'];rows=[]
 for unit in s.read(R/'private/assignment.json')['units']:
  closed=s.read(R/'submissions'/unit/'repair-closed.json');native=s.read(R/'endpoints'/(unit+'.json'));final=s.read(R/'self-endpoints'/(unit+'.json'));handoff=final['handoffAtUnix']
  feedback=[]
  for folder in sorted((R/'feedback'/unit).glob('request-*')):
   request=s.read(folder/'request.json');done=s.read(folder/'completed.json');corpus=s.read(folder/'evidence/corpus.json')
   feedback.append({'request':folder.name,'agent_requested_states':request['states'],'requested_cases':request['cases'],'request_seconds':done['finishedAtUnix']-request['startedAtUnix'],'collection_seconds':corpus['finishedAtUnix']-corpus['startedAtUnix'],'queue_seconds_sum':sum(v.get('queueSeconds',0)for v in corpus['runs'])})
  api=s.read(R/'corpora'/unit/'minimum-api/record.json');endpoint=final['finishedAtUnix']-handoff
  readiness=[s.read(p)['finishedAtUnix']for p in(R/'self-review'/unit).glob('*.json')if isinstance(s.read(p),dict)and isinstance(s.read(p).get('finishedAtUnix'),(int,float))];ready=max(readiness)if readiness else None
  rows.append({'unit':unit,'source_authoring_seconds':author_seconds,'shared_D0_acquisition_seconds':d0_seconds,'shared_D0_native_seconds':d0_native_seconds,'shared_D0_review_and_binding_seconds':d0_review_seconds,
               'handoff_to_source_closed_seconds_including_API':closed['closedAtUnix']-handoff,'minimum_API_seconds':api['finishedAtUnix']-api['startedAtUnix'],
               'source_closed_to_native_automatic_endpoint_seconds':native['finishedAtUnix']-closed['closedAtUnix'],
               'native_endpoint_to_required_final_actuals_seconds':final['finishedAtUnix']-native['finishedAtUnix'],
               'participant_reported_actuals_ready_at':ready,'handoff_to_original_actuals_ready_seconds':ready-handoff if ready else None,'actuals_ready_to_admission_binding_seconds':final['finishedAtUnix']-ready if ready else None,'handoff_to_full_self_endpoint_seconds':endpoint,'normal_workflow_endpoint_seconds':author_seconds+d0_seconds+endpoint,'normal_workflow_original_actuals_ready_seconds':author_seconds+d0_seconds+ready-handoff if ready else None,
               'author_dispatch_to_full_self_wall_seconds':final['finishedAtUnix']-start,'release_through_full_self_wall_seconds':final['finishedAtUnix']-release,
               'feedback_requests':feedback,'scope':'Observed endpoint includes operator binding wait; participant readiness is a separately labeled pre-admission lower endpoint, not accepted delivery. Success is decided separately by frozen metric conditions and independent quality.'})
 return {'arms':rows,'common_pre_author_window_seconds':start-release,'scope':'Exact observed wall time; includes required final actuals review. Shared contract/review/host-prep window is separate from source authoring; external hidden/panels and publication/CI reported separately. No USD/token billing data available.'}
if __name__=='__main__':print(json.dumps(main(),indent=2))
