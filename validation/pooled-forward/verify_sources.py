#!/usr/bin/env python3
"""Verify released v13 bytes and its separately frozen common-floor control."""
import hashlib
import json
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
PINS = {
    'CANDIDATE-FREEZE-10.json': '6dac704edfb15491e59648ab0259f465469f81ed0f7b61d7cedf0e91e47140cf',
    'BASELINE-COMMON-FREEZE-6.json': 'e04a0db08a4a617c372e1f3f9a05dc3c1042fb53e59d48e08f189f03aaf302c4',
}


def verify():
    counts = {}
    for filename, expected in PINS.items():
        raw = (ROOT/filename).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == expected, 'Original source freeze differs'
        value = json.loads(raw)
        directory = ROOT/value['candidate']
        assert directory.parent == ROOT and not directory.is_symlink()
        for name, digest in value['files'].items():
            relative = PurePosixPath(name)
            assert not relative.is_absolute() and str(relative) == name and '..' not in relative.parts
            original = directory/name
            assert not original.is_symlink() and original.is_file()
            assert hashlib.sha256(original.read_bytes()).hexdigest() == digest, name
            if filename == 'CANDIDATE-FREEZE-10.json':
                released = REPO/'native-ui-agent'/name
                assert not released.is_symlink() and released.is_file()
                assert hashlib.sha256(released.read_bytes()).hexdigest() == digest, 'Released candidate differs: '+name
        counts[value['candidate']] = len(value['files'])
    return {'status': 'verified', 'frozen_member_counts': counts,
            'release_matches_candidate': True,
            'scope': 'Byte identity only. Common correctness fixes are present in the control; no native, business quality or complete delivery certification.'}


if __name__ == '__main__': print(json.dumps(verify(), sort_keys=True))
