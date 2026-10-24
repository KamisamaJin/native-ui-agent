#!/usr/bin/env python3
"""Transport the already frozen quality prompt and shared source supplement."""
import argparse,time
import study as s
import prepare_quality_request as base,shared_amendment
R=s.R
p=argparse.ArgumentParser();p.add_argument('phase',choices=['d0','final']);p.add_argument('panel',choices=['one','two']);p.add_argument('task',choices=['T1','T2']);a=p.parse_args();shared_amendment.verify()
text=base.prepare(a.phase,a.panel,a.task)
extra=(R/'QUALITY-SOURCE-EXTENSION.txt').read_text().replace('SOURCE_INPUTS',str(R/'source-evaluation-inputs'/a.phase/a.task)).replace('TOOLS_SOURCE_AUDIT',str(s.REPO/'tools/implementation_audit.py')).replace('SOURCE_AUDIT_DOC',str(R/'SOURCE-AUDIT.md')).replace('OUTPUT',str(R/'judgments'/a.phase/a.panel/a.task))
text+='\n\n'+extra
s.save(R/'operators'/('quality-'+a.phase+'-'+a.panel+'-'+a.task+'-amended-delivery.json'),{'deliveredAtUnix':time.time(),'prompt':text,'sourceSupplementSHA256':s.sha(R/'QUALITY-SOURCE-EXTENSION.txt'),'scope':'Transport only; unchanged frozen runtime quality prompt plus prospectively shared source-review extension.'})
print(text)
