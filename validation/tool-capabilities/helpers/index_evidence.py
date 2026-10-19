#!/usr/bin/env python3
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];cases=[]
for directory in sorted((root/'evidence').iterdir()):
    if not directory.is_dir()or not(directory/'manifest.json').exists():continue
    m=json.loads((directory/'manifest.json').read_text());o=json.loads((directory/'observation.json').read_text())
    cases.append({'case':directory.name,'manifest':str((directory/'manifest.json').relative_to(root)),'observation_sha256':hashlib.sha256((directory/'observation.json').read_bytes()).hexdigest(),'native_test_count':m.get('native_test_count'),'collector_status':m.get('status'),'native_build_exit':m.get('build_exit_code'),'native_test_exit':m.get('test_exit_code'),'snapshot_count':len(o['snapshots']),'state_capture_count':len(o.get('state_captures',[])),'issues':o.get('issues'),'source_hashes':m.get('source_hashes')})
frozen=json.loads((root/'expected/freeze-manifest.json').read_text());intact=all(hashlib.sha256((root/p).read_bytes()).hexdigest()==h for p,h in frozen['sha256'].items())
(root/'EVIDENCE-INDEX.json').write_text(json.dumps({'scope':'Generic native tool capabilities; no business outcome claims','frozen_expectations_intact':intact,'native_test_count_total':sum(c['native_test_count'] or 0 for c in cases),'cases':cases},indent=2)+'\n')
