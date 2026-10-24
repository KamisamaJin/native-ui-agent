#!/usr/bin/env python3
"""Deliver the original builder task plus the predeclared shared API supplement."""
import argparse,time
import study as s
import prepare_builder_request as base
import shared_amendment
R=s.R
p=argparse.ArgumentParser();p.add_argument('task',choices=['T1','T2']);a=p.parse_args();shared_amendment.verify();authorization=s.gate.authorize(R/'gates','design-review',R)
w=R/'cache'/('builder-'+a.task);scope=R/'design'/a.task/'public'
text=base.T.format(workspace=w,public=scope,compile=R/'compile_only.py')
extension=(R/'BUILD-API-EXTENSION.txt').read_text().replace('CHECK_MINIMUM_API',str(R/'check_minimum_api.py')).replace('WORKSPACE',str(w)).replace('PUBLIC',str(scope))
text+='\n\n'+extension+'\nAll approved source-only MUSTs are in implementation-audit.json/reference.json. They remain part of the independent requirement; no source-only judgment establishes rendered styles.\n'
s.save(R/'operators'/(a.task+'-initial-delivery.json'),{'deliveredAtUnix':time.time(),'authorization':authorization,'prompt':text,'originalBuilderTemplateSHA256':s.sha(R/'prepare_builder_request.py'),'sharedExtensionSHA256':s.sha(R/'BUILD-API-EXTENSION.txt')})
print(text)
