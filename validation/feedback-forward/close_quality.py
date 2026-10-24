#!/usr/bin/env python3
"""Close only complete source AND runtime panels, preserving original algorithms."""
import argparse
import source_evaluation as source
import evaluation
p=argparse.ArgumentParser();p.add_argument('phase',choices=['d0','final']);p.add_argument('panel',choices=['one','two']);a=p.parse_args()
source.validate(a.phase,a.panel);evaluation.close(a.phase,a.panel)
if a.panel=='two':source.merge(a.phase)
