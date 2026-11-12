#!/usr/bin/env python3
"""Pure supplementary source/token intent inspection; no actual source approval."""
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from run_pure_checks import C, O, load, save, digest
from check_business_and_scope import SPECS

def main():
    rows = []
    issues = []
    for task, spec in SPECS.items():
        public = C / 'public/tasks' / task
        schema = load(public / 'fixture.schema.json')
        api = (public / 'API.md').read_text()
        swift = re.search(r'```swift\n(.*?)```', api, re.S)[1]
        kotlin = re.search(r'```kotlin\n(.*?)```', api, re.S)[1]
        swift_fields = dict(re.findall(r'public let (\w+): (\[String\]|\w+)', swift))
        kotlin_fields = dict(re.findall(r'val (\w+): (List<String>|\w+)', kotlin))
        assert set(swift_fields) == set(kotlin_fields) == set(schema['properties'])
        for key, prop in schema['properties'].items():
            expected_swift = {'string': 'String', 'integer': 'Int', 'boolean': 'Bool', 'array': '[String]'}[prop['type']]
            expected_kotlin = {'string': 'String', 'integer': 'Int', 'boolean': 'Boolean', 'array': 'List<String>'}[prop['type']]
            if swift_fields[key] != expected_swift or kotlin_fields[key] != expected_kotlin:
                issues.append({'id': 'API-TYPE-' + task + '-' + key, 'priority': 'blocking-design',
                    'task': task, 'field': key, 'schema_type': prop['type'],
                    'swift_declared': swift_fields[key], 'swift_required': expected_swift,
                    'kotlin_declared': kotlin_fields[key], 'kotlin_required': expected_kotlin,
                    'source': str((public / 'API.md').relative_to(C)),
                    'scope': 'Published design signature contradiction only; no native source was built or observed.'})
        tokens = load(public / 'tokens.json')
        assert all(tokens[x]['unit'] == 'argb' and tokens[x]['value'].startswith('#FF') for x in ['surface', 'row', 'selected', 'accent', 'disabled', 'ink', 'muted', 'onAccent', 'outline'])
        svg_rows = []
        for p in sorted(public.glob('*.svg')):
            doc = ET.fromstring(p.read_text())
            assert doc.attrib['width'] == '390'
            assert not re.search(r'https?://(?!www.w3.org)', p.read_text())
            assert 'Independent authored design, not runtime output' in p.read_text()
            svg_rows.append({'path': str(p.relative_to(C)), 'authored_structure_only': True})
        for family in ['public', 'private']:
            for platform in ['ios', 'android']:
                p = C / family / 'tasks' / task / platform
                reference = load(p / 'reference.json')
                assert reference['tokens'] == tokens
                expected = load(p.parent / 'outcomes.json')
                first_root = next(iter(spec['roots']))
                for sid, outcome in expected.items():
                    state = reference['states'][sid]
                    assert state['surface-fill'] == tokens['surface']
                    assert state['primary-fill'] == tokens['accent' if outcome['visible']['submit-enabled'] else 'disabled']
                    assert state['first-option-fill'] == tokens['selected' if outcome['local']['root'] == first_root else 'row']
                    if platform == 'android':
                        for target, size, weight, color in [('title', 24, 600, 'ink'), ('context', 15, 400, 'muted')]:
                            assert state[target + '-font_sp'] == {'value': size, 'unit': 'sp'}
                            assert state[target + '-font_weight'] == {'value': weight, 'unit': 'scalar'}
                            assert state[target + '-color_argb'] == tokens[color]
                            assert state[target + '-overflow'] == {'value': False, 'unit': 'bool'}
                            assert state[target + '-ellipsized'] == {'value': False, 'unit': 'bool'}
                            # These are declared lower bounds, not predicted exact
                            # native line counts. Long authored text has stronger
                            # conservative bounds; no layout is rendered here.
                            line_min = state[target + '-lines']
                            assert line_min['unit'] == 'count' and line_min['value'] in ({1, 2} if target == 'title' else {1, 3})
                            if line_min['value'] > 1:
                                assert len(outcome['visible'][target + '-label']) >= (100 if target == 'title' else 500)
                bridge = p / ('ObserverBridge.swift' if platform == 'ios' else 'ObserverBridge.kt')
                content = bridge.read_text()
                code = '\n'.join(line for line in content.splitlines() if not line.lstrip().startswith('//'))
                assert not re.search(r'\b(if|when|remember|State|VStack|Column|Button|Text|LazyColumn|ScrollView|LaunchedEffect)\b', code)
                assert 'onEvent: onEvent' in code if platform == 'ios' else 'onEvent = onEvent' in code
                assert len(re.findall(r'fixture\["', code) if platform == 'ios' else re.findall(r'fixture\.get(?:AsJsonArray)?\(', code)) == len(schema['properties'])
                if platform == 'android': assert 'ContrastAwareReplyTheme {' in code
                subjects = list((p / 'pure-subjects/production').iterdir())
                assert len(subjects) == 1
                assert all(line.startswith('//') for line in subjects[0].read_text().splitlines())
                assert 'PURE CAPABILITY PLACEHOLDER ONLY' in subjects[0].read_text()
                assert 'PURE CAPABILITY PLACEHOLDER' in load(p / 'pure-subjects/integration/placement.json')['purpose']
        # Planned surface and row gutters are geometrically inside opaque painted
        # fills and before the required 16-unit content inset, away from corners.
        surface_width, row_width = 390 - 2 * 16, 390 - 4 * 16
        assert surface_width * .035 < 16 and row_width * .035 < 16
        assert 48 * .25 >= 8
        rows.append({'task': task, 'passed': not any(x['task'] == task for x in issues), 'field_count': len(schema['properties']),
                     'authored_api_schema_types_agree': not any(x['task'] == task for x in issues), 'all_four_bridges_are_direct_decoders': True,
                     'placeholders_contain_no_UI_implementation': True, 'gutter_paint_geometry_is_consistent_as_intent': True,
                     'source_truth': 'unassessed', 'native_truth': 'not_run', 'svgs': svg_rows})
    save(O / 'additional-authored-metadata-checks.json', {'passed': not issues, 'tasks': rows, 'issues': issues,
        'scope': 'Authored signatures/bridge text/tokens/structural SVGs/planned gutter positions only; no rendering or actual source approval.'})
    print({'passed': not issues, 'tasks': len(rows), 'issues': issues})

if __name__ == '__main__': main()
