#!/usr/bin/env python3
"""Identical source-gate supplement for both assigned frozen Skill conditions."""
import argparse,time
import study as s
import shared_amendment,prepare_repair_request
R=s.R
p=argparse.ArgumentParser();p.add_argument('unit');a=p.parse_args();shared_amendment.verify()
text=prepare_repair_request.prepare(a.unit);w=R/'cache'/a.unit;cfg=s.read(R/'private/assignment.json')['units'][a.unit];scope=R/'design'/cfg['task']/'public'
extra=(R/'REPAIR-SOURCE-EXTENSION.txt').read_text().replace('SOURCE_CHECK',str(R/'source_check.py')).replace('COMPLETE_CHECK',str(R/'complete_self_check.py')).replace('SOURCE_AUDIT_DOC',str(R/'SOURCE-AUDIT.md')).replace('WORKSPACE',str(w))
api=(R/'BUILD-API-EXTENSION.txt').read_text().replace('CHECK_MINIMUM_API',str(R/'check_minimum_api.py')).replace('WORKSPACE',str(w)).replace('PUBLIC',str(scope))
text+='\n\n'+extra+'\n\n'+api
s.save(R/'operators'/(a.unit+'-amended-delivery.json'),{'deliveredAtUnix':time.time(),'prompt':text,'sharedSupplementSHA256':s.sha(R/'PREIMPLEMENTATION-METHODS.json'),'scope':'Original budget, original same-PR inputs and assigned tools; shared source/API gate and complete endpoint extension.'})
print(text)
