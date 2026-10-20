from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from oracle_common import grade_task, match_claims, compare_pair

def grade(case, platform, observation_path, root=None, manual=None, source_root=None, api_review=None):
    return grade_task(Path(__file__).resolve().parents[1], case, platform, observation_path, root, manual, source_root, api_review)
