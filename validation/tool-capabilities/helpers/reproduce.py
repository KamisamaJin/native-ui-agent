#!/usr/bin/env python3
"""Reproduce one generic native case from preserved immutable observer bundles."""
import argparse,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
cases={
 'baseline-semantic':('baseline-observer','semantic.json','baseline-semantic-actions.json'),
 'baseline-long':('baseline-observer','long.json','baseline-long-actions.json'),
 'candidate-semantic-positive':('candidate-observer-aaef','v2-semantic.json','v2-semantic-positive-actions.json'),
 'candidate-semantic-negative':('candidate-observer-aaef','v2-semantic.json','v2-semantic-negative-actions.json'),
 'candidate-long':('candidate-observer-aaef','v2-long.json','v2-long-actions.json'),
 'candidate-long-partial':('candidate-observer-aaef','v2-long-partial-isolated.json','v2-long-partial-isolated-actions.json')}
p=argparse.ArgumentParser(description=__doc__);p.add_argument('case',choices=cases);p.add_argument('--output',required=True,type=Path);a=p.parse_args();bundle,fixture,actions=cases[a.case]
cmd=[sys.executable,str(root/bundle/'scripts/ios_observe.py'),'run','--bridge',str(root/'ProbeBridge.swift'),'--fixtures',str(root/'fixtures'/fixture),'--actions',str(root/'fixtures'/actions),'--simulator','133B5850-2ED9-4A34-8B3B-2C06471378A8','--developer-dir','/Applications/Xcode.app/Contents/Developer','--output',str(a.output.resolve())]
raise SystemExit(subprocess.run(cmd).returncode)
