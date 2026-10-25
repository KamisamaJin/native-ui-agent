"""Fixed semantic oracle, independent of controller implementation.

An API adapter supplies actual observations as JSON. Each observation is a
per-case mapping containing the keys declared in cases.json. Additional raw data
is retained by the runner. This module never imports the implementation.
"""
import json
from pathlib import Path


def verify(case_id, observed):
    cases = json.loads((Path(__file__).parent / 'cases.json').read_text())['cases']
    expected = next(row['required'] for row in cases if row['id'] == case_id)
    failures = []
    for key, value in expected.items():
        if key not in observed:
            failures.append({'key': key, 'expected': value, 'actual': '<unobserved>'})
        elif observed[key] != value:
            failures.append({'key': key, 'expected': value, 'actual': observed[key]})
    return {'id': case_id, 'status': 'passed' if not failures else 'failed',
            'failures': failures}


if __name__ == '__main__':
    import sys
    value = json.loads(Path(sys.argv[1]).read_text())
    result = [verify(row['id'], row['observed']) for row in value['results']]
    print(json.dumps({'results': result}, indent=2))
    raise SystemExit(0 if all(row['status'] == 'passed' for row in result) else 1)
