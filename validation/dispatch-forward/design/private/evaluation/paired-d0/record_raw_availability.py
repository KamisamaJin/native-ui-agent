"""Original-node field availability, kept outside all grade denominators.

No native_facts origin envelopes are generated and no grade is modified.
"""
import json, hashlib
from pathlib import Path
HERE = Path(__file__).resolve().parent
R = HERE.parents[3]
REPO = R.parents[1]
FIELDS = ['font_sp', 'font_weight', 'touch_bounds_dp', 'bounds_dp', 'unclipped_bounds_dp']
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
for aid in ['sample-716d41', 'sample-e318ec']:
    corpora = []
    for corpus in ['d0', 'paired-d0']:
        cap = R / 'private/grade-capsules' / corpus / aid
        manifest = read(cap / 'manifest.json')
        observations = []
        for entry in manifest['observations']:
            if entry['platform'] != 'android': continue
            path = cap / entry['observation']['path']
            assert sha(path) == entry['observation']['sha256']
            raw = read(path)
            fields = {}
            for field in FIELDS:
                occurrences = [(si, ni, n) for si, s in enumerate(raw['snapshots']) for ni, n in enumerate(s.get('nodes', [])) if n.get(field) is not None]
                fields[field] = {'raw_occurrences': len(occurrences), 'examples': [
                    {'pointer': f'/snapshots/{si}/nodes/{ni}/{field}', 'snapshot': si,
                     'node_id': n.get('node_id'), 'identifier': n.get('identifier'), 'value': n[field]}
                    for si, ni, n in occurrences[:3]]}
            observations.append({'case': entry['case'], 'original_observation': {'path': str(path.relative_to(REPO)), 'sha256': sha(path)},
                                 'snapshot_native_facts_envelope_occurrences': sum(len(s.get('native_facts', [])) for s in raw['snapshots']),
                                 'node_fields': fields})
        corpora.append({'corpus': corpus, 'observations': observations})
    result = {'anonymous_id': aid, 'scope': 'COMMON evaluation infrastructure format/inspection gap; raw field occurrence inventory only, outside every P/F/U denominator and all observation gains/losses.',
              'frozen_method': 'V3 native_capability requires an original native_runtime_fact with exact target, field, bound origin, runtime_inspection source kind, capability method, platform and named native probe. Original node fields alone do not satisfy that envelope format.',
              'interpretation': 'Raw Android font_sp/font_weight/touch_bounds_dp are present as explicitly recorded below. Capability U must not be described as absence of those raw fields, an observation win/loss, or a product failure. No origin envelope is fabricated, native probe inferred, physical hit region substituted, or earlier grade changed. Native control/text/bounds/pixel methods continue to consume supported original raw evidence.',
              'corpora': corpora}
    dest = HERE / aid / 'raw-capability-availability.json'
    assert not dest.exists()
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'completed': True}))
