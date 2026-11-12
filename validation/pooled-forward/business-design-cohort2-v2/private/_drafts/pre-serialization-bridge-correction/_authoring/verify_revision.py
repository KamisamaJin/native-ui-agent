#!/usr/bin/env python3
"""Verify only the authorized pre-code corrections and unchanged original corpus."""
from author import *
import re

ORIGINAL=ROOT.with_name('business-design-cohort2')
ORIGINAL_SEAL='f0d623acb5abb528536e4ac126ecacac020dd835bb6f784f73fe3b1c1245930d'

def main():
    assert sha(ORIGINAL/'SEAL.sha256')==ORIGINAL_SEAL
    old_inventory=(ORIGINAL/'SEAL.sha256').read_text().splitlines()
    assert len(old_inventory)==829
    for line in old_inventory:
        expected,rel=line.split('  ',1);assert sha(ORIGINAL/rel)==expected,rel
    preserved=[];bounds=[];api_corrections=[];fixtures_checked=0
    for t in TASKS:
        public=ROOT/'public/tasks'/t['id'];old_public=ORIGINAL/'public/tasks'/t['id']
        new_schema=load(public/'fixture.schema.json');old_schema=load(old_public/'fixture.schema.json')
        for field,slot in new_schema['properties'].items():
            before=old_schema['properties'][field]
            if slot['type']=='integer':
                assert type(slot['minimum']) is int and type(slot['maximum']) is int
                assert -2147483648<=slot['minimum']<=slot['maximum']<=2147483647
                assert slot['minimum']==before.get('minimum',-2147483648)
                assert slot['maximum']==before.get('maximum',2147483647)
                normalized=dict(slot);normalized.pop('minimum',None);normalized.pop('maximum',None)
                old_normalized=dict(before);old_normalized.pop('minimum',None);old_normalized.pop('maximum',None)
                assert normalized==old_normalized
                bounds.append(dict(task=t['id'],field=field,previous_minimum=before.get('minimum'),previous_maximum=before.get('maximum'),minimum=slot['minimum'],maximum=slot['maximum'],outside_values_rejected=[slot['minimum']-1,slot['maximum']+1],boundary_check='exact scalar integer range only; no native decoder or arbitrary arithmetic claim'))
            else:assert slot==before
        a=copy.deepcopy(new_schema);b=copy.deepcopy(old_schema);a.pop('properties');b.pop('properties');assert a==b
        api=(public/'API.md').read_text();kotlin=api.split('```kotlin\n',1)[1].split('```',1)[0];swift=api.split('```swift\n',1)[1].split('```',1)[0]
        for field,typ in COMMON_FIELDS+t['fields']:
            native_kotlin='Boolean' if typ=='Bool' else typ
            native_swift='[String]' if typ=='List<String>' else typ
            assert re.search(r'\bval '+field+r': '+re.escape(native_kotlin)+r'(?=[,\n])',kotlin),field
            assert re.search(r'\bpublic let '+field+r': '+re.escape(native_swift)+r'(?=\n)',swift),field
            if typ=='Bool':api_corrections.append(dict(task=t['id'],field=field,old_kotlin_type='Bool',new_kotlin_type='Boolean',unchanged_swift_type='Bool',unchanged_json_type='boolean',unchanged_bridge_decoder='asBoolean'))
        assert not re.search(r': Bool(?=[,\n])',kotlin)
        for rel in ['tokens.json','DESIGN.md','reference-blank.svg','reference-ready.svg','reference-long.svg']:
            assert sha(public/rel)==sha(old_public/rel),rel;preserved.append('public/tasks/'+t['id']+'/'+rel)
        for family in ['public','private']:
            p=ROOT/family/'tasks'/t['id'];old=ORIGINAL/family/'tasks'/t['id']
            for rel in ['flow.json','outcomes.json']:
                assert sha(p/rel)==sha(old/rel),str(p/rel);preserved.append(str((p/rel).relative_to(ROOT)))
            for platform in ['ios','android']:
                newp=p/platform;oldp=old/platform
                for rel in ['fixtures.json','actions.json','bindings.json','environment.json','reference.json','denominator.json','launch.json','routes.json','ObserverBridge.swift' if platform=='ios' else 'ObserverBridge.kt']:
                    assert sha(newp/rel)==sha(oldp/rel),str(newp/rel);preserved.append(str((newp/rel).relative_to(ROOT)))
                old_contract=load(oldp/'contract.json');new_contract=load(newp/'contract.json')
                assert old_contract.pop('approval_reference')!=new_contract.pop('approval_reference')
                assert old_contract==new_contract
                data=load(newp/'fixtures.json')
                for f in [data['initial'],*data['updates']]:
                    assert set(f)==set(new_schema['properties'])
                    for field,slot in new_schema['properties'].items():
                        value=f[field]
                        if slot['type']=='integer':assert type(value) is int and slot['minimum']<=value<=slot['maximum']
                        elif slot['type']=='boolean':assert type(value) is bool
                        elif slot['type']=='string':assert isinstance(value,str)
                        else:assert isinstance(value,list) and all(isinstance(v,str) for v in value)
                    fixtures_checked+=1
    assert len(bounds)==34 and len(api_corrections)==3
    assert sha(ROOT/'MASTER-DENOMINATOR.json')==sha(ORIGINAL/'MASTER-DENOMINATOR.json')
    preserved.append('MASTER-DENOMINATOR.json')
    ledger=dict(version=2,correction_context='Independent pre-code review; no initial production UI implementation exists.',original_root=str(ORIGINAL),original_seal_sha256=ORIGINAL_SEAL,original_inventory_files=829,original_inventory_preserved=True,original_rejection_records='Original sealed bundle and external review records are retained, never rewritten.',necessary_corrections=[dict(id='INPUT-INT32-DOMAIN',finding='The JSON schemas allowed integers outside the Kotlin Int and Gson asInt transport domain while public briefs claimed complete valid ranges.',change='Explicit signed Int32 bounds on every Int, retaining tighter prior minima and portfolioScore maximum100; accountBalanceCents explicitly ranges -2147483648..2147483647.',schema_field_bounds=bounds),dict(id='KOTLIN-BOOLEAN-TYPE',finding='Three Kotlin API fields were spelled Bool, which is the Swift name rather than the Kotlin Boolean type.',change='Correct only these three public Kotlin type spellings to Boolean; retain Swift Bool, schema boolean, supplied bridge asBoolean, raw fixture values and all business outcomes.',fields=api_corrections)],arithmetic_scope='The published component rules require comparisons, key equality, and string formatting. No sum, product, or caller revision increment is required. Finite-corpus capability checks do not certify arbitrary implementation arithmetic or universal overflow safety.',frozen_corpus_unchanged=True,unchanged_business_style_files=len(preserved),preserved_files=preserved,fixture_instances_checked_in_both_platform_packets=fixtures_checked,exact_contract_semantics_except_approval_reference=True,style_tolerances_changed=False,native_units_changed=False,source_approvals=0,native_runs=0,implementation_or_runtime_feedback_read=False,regenerated_metadata='New-root absolute paths, lock approval references and derived lock/plan/policy/catalog/execution/profile identities are regenerated. They do not change a business expectation.',superseded_v2_api_drafts='private/_drafts/before-kotlin-type-correction; all five staged API documents preserved before correcting three Kotlin type names.')
    write(ROOT/'CORRECTION-LEDGER.json',ledger)
    domain='''# Shared integer transport domain

All immutable input Int fields use the shared signed 32-bit domain supported by
Kotlin Int, Gson asInt, and the Swift input bridge: -2147483648 through2147483647.
The JSON schema narrows individual fields further. Existing nonnegative or
positive minima remain, revision is0..2147483647, and portfolioScore remains0..100.
accountBalanceCents explicitly allows the full signed range, including negatives.
Inputs outside fixture.schema.json are outside this component contract.

Revision is an opaque caller-supplied identity key. The component compares it and
never increments it. The published business predicates use comparison, key
equality, and string formatting. They require no sum or product. A producer that
introduces intermediate arithmetic must still preserve those published predicates;
these finite-corpus capability checks claim no arbitrary implementation overflow
proof or universal correctness outside the listed corpus.

Swift uses Bool and Kotlin uses Boolean for schema boolean fields. The supplied
bridges already decode booleans accordingly; no bridge or fixture value changed.
This clarification was fixed before any production UI code or native execution.
'''
    for t in TASKS:write(ROOT/'public/tasks'/t['id']/'INPUT-DOMAIN.md',domain)
    write(ROOT/'ALL-FINAL-INPUTS-FIXED.json',dict(version=2,fixed_at_utc=datetime.now(timezone.utc).isoformat(),original_seal_sha256=ORIGINAL_SEAL,task_ids=[t['id'] for t in TASKS],public_schema_sha256={t['id']:sha(ROOT/'public/tasks'/t['id']/'fixture.schema.json') for t in TASKS},public_api_sha256={t['id']:sha(ROOT/'public/tasks'/t['id']/'API.md') for t in TASKS},correction_ledger_sha256=sha(ROOT/'CORRECTION-LEDGER.json'),all_existing_fixture_outcome_style_unit_action_denominator_files_unchanged=True,production_ui_written=False,native_execution=False,statement='All five final schemas and language API signatures are fixed together before final dual-SUT pure preflight and the new revision seal.'))
    print(json.dumps({'original829_files_preserved':True,'bounded_integer_fields':len(bounds),'kotlin_Boolean_corrections':len(api_corrections),'preserved_business_style_files':len(preserved),'fixture_instances_checked':fixtures_checked,'native_runs':0}))
if __name__=='__main__':main()
