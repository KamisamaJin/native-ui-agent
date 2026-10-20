#!/usr/bin/env python3
"""Disclose assignment only after original AND supplemental all-task barriers."""
import time
from pathlib import Path
import experiment as ex
R=Path(__file__).resolve().parent
original=ex.gate.authorize(R/'gates','grade-pair',R)
supplement=ex.gate.authorize(R/'shared-environment-v1/gates','graded',R)
path=R/'private/ASSIGNMENT-RELEASE.json';assert not path.exists()
a=ex.read(R/'private/assignment.json');ex.save(path,dict(releasedAtUnix=time.time(),gradeAliases=a['gradeAliases'],units=a['units'],originalFourStages=original,posthocSharedInfrastructureAllTasks=supplement,scope='Original primary four-stage anonymous grading and separate posthoc shared repair recheck sealed before this disclosure. No new product repair or detection-credit expansion.'))
ex.gate.seal(R/'gates','reveal',{'assignment':['private/assignment.json','private/ASSIGNMENT-RELEASE.json','shared-environment-v1/gates/graded.json']},R)
print('Assignment disclosed after both complete all-task grading barriers')
