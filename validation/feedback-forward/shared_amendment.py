#!/usr/bin/env python3
"""Verify the separately declared shared source-only protocol supplement."""
from pathlib import Path
import study as s
R=s.R

def verify():
 meta=s.read(R/'PREIMPLEMENTATION-METHODS.json')
 for rel,h in meta['study_files'].items():assert s.sha(R/rel)==h,rel
 for rel,h in meta['repository_files'].items():assert s.sha(s.REPO/rel)==h,rel
 return meta
if __name__=='__main__':verify();print('Shared preimplementation supplement remains byte-exact')
