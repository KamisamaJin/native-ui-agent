#!/usr/bin/env python3
"""Recompute sealed empirical profile from original native rows; no new fit policy."""
import json
import study as s
import ax_calibration as calibration
R=s.R

def main():
 profile=s.read(R/'calibration/profile-final.json');rows=R/'evidence/ax-run-2/calibration-rows.json';obs=R/'evidence/ax-run-2/observation.json'
 assert s.sha(rows)==profile['provenance']['extraction_sha256']and s.sha(obs)==profile['provenance']['observation_sha256']
 assert s.sha(R/'ax-probe/SEAL.json')==profile['provenance']['probe_seal_sha256']
 assert calibration.fit(s.read(rows),profile['context'],profile['provenance'])==profile
 assert profile['factor_fit_uses_heldout']is False and not profile['heldout_failures']
 for proof in profile['raw_residuals']:assert all(v==0 for v in proof['residuals'].values())
 # Scope rejection and verdict immutability remain live unit/independent controls.
 print(json.dumps({'status':'PASS','complete_native_rows':s.read(rows)['summary']['runtime_rows'],'fit_rows':profile['fit_rows'],'heldout_rows':profile['heldout_rows'],'factor':profile['factor'],'scope':'Original zero-residual probe record agreement only; positive-error law/universal SwiftUI precision are unproved.'}))
if __name__=='__main__':main()
