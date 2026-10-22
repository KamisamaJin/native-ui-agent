#!/usr/bin/env python3
import argparse,time
from pathlib import Path
import experiment as ex
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('phase',choices=['initial','review','repair']);p.add_argument('unit');p.add_argument('agent');a=p.parse_args();stage={'initial':'design','review':'own-d0','repair':'reviews'}[a.phase];receipt=ex.gate.authorize(R/'gates',stage,R);dest=R/'operators/dispatch'/(a.unit+'-'+a.phase+'.json');assert not dest.exists();ex.save(dest,{'recordedAfterDispatchAtUnix':time.time(),'unit':a.unit,'phase':a.phase,'agent':a.agent,'promptSHA256':ex.sha(R/'prompts'/(a.unit+'-'+a.phase+'.txt')),'authorization':receipt,'schedule':'Paired task blocks, two independent agent slots; both arms in a task dispatched together. Actual first-action times are recorded by each agent.'});print('Recorded dispatch',a.unit,a.phase)
