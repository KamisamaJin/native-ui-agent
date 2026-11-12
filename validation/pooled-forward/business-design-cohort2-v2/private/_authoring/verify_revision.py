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
    preserved=[];bounds=[];api_corrections=[];bridge_corrections=[];fixtures_checked=0
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
            if typ=='Bool':api_corrections.append(dict(task=t['id'],field=field,old_kotlin_type='Bool',new_kotlin_type='Boolean',unchanged_swift_type='Bool',unchanged_json_type='boolean',bridge_decoder_before='asBoolean',bridge_decoder_after='jsonPrimitive.boolean'))
        assert not re.search(r': Bool(?=[,\n])',kotlin)
        for rel in ['tokens.json','DESIGN.md','reference-blank.svg','reference-ready.svg','reference-long.svg']:
            assert sha(public/rel)==sha(old_public/rel),rel;preserved.append('public/tasks/'+t['id']+'/'+rel)
        for family in ['public','private']:
            p=ROOT/family/'tasks'/t['id'];old=ORIGINAL/family/'tasks'/t['id']
            for rel in ['flow.json','outcomes.json']:
                assert sha(p/rel)==sha(old/rel),str(p/rel);preserved.append(str((p/rel).relative_to(ROOT)))
            for platform in ['ios','android']:
                newp=p/platform;oldp=old/platform
                unchanged=['fixtures.json','actions.json','bindings.json','environment.json','reference.json','denominator.json','routes.json']
                if platform=='ios':unchanged+=['launch.json','ObserverBridge.swift']
                for rel in unchanged:
                    assert sha(newp/rel)==sha(oldp/rel),str(newp/rel);preserved.append(str((newp/rel).relative_to(ROOT)))
                if platform=='android':
                    newbridge=(newp/'ObserverBridge.kt').read_text()
                    assert 'import kotlinx.serialization.json.JsonObject' in newbridge and 'com.google.gson' not in newbridge
                    assert 'fun Content(fixture: JsonObject, onEvent: (String) -> Unit)' in newbridge
                    assert 'ContrastAwareReplyTheme(darkTheme = false, dynamicColor = false)' in newbridge
                    assert t['api']+'(input = input, onEvent = onEvent)' in newbridge
                    for field,typ in COMMON_FIELDS+t['fields']:
                        suffix={'String':'jsonPrimitive.content','Int':'jsonPrimitive.int','Bool':'jsonPrimitive.boolean','List<String>':'jsonArray.map { it.jsonPrimitive.content }'}[typ]
                        assert 'fixture["'+field+'"]!!.'+suffix in newbridge
                    oldlaunch=load(oldp/'launch.json');newlaunch=load(newp/'launch.json')
                    assert oldlaunch['android'].pop('bridge_sha256')==sha(oldp/'ObserverBridge.kt')
                    assert newlaunch['android'].pop('bridge_sha256')==sha(newp/'ObserverBridge.kt')
                    assert oldlaunch==newlaunch
                    bridge_corrections.append(dict(task=t['id'],family=family,path=str((newp/'ObserverBridge.kt').relative_to(ROOT)),before_sha256=sha(oldp/'ObserverBridge.kt'),after_sha256=sha(newp/'ObserverBridge.kt'),unchanged_decoded_fields=[k for k,_ in COMMON_FIELDS+t['fields']],callback_forwarded_verbatim=True,changes=['host-compatible kotlinx.serialization.json.JsonObject and primitive/list accessors','explicit stock darkTheme=false and dynamicColor=false']))
                old_contract=load(oldp/'contract.json');new_contract=load(newp/'contract.json')
                assert old_contract.pop('approval_reference')!=new_contract.pop('approval_reference')
                if platform=='android':
                    for contract in [old_contract,new_contract]:
                        next(s for s in contract['sources'] if s['id']=='launch')['sha256']='bridge-identity-resealed'
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
    assert len(bounds)==34 and len(api_corrections)==3 and len(bridge_corrections)==10
    assert sha(ROOT/'MASTER-DENOMINATOR.json')==sha(ORIGINAL/'MASTER-DENOMINATOR.json')
    preserved.append('MASTER-DENOMINATOR.json')
    host=REPO/'validation/pooled-forward/candidate-v13.9/assets/android-observer/NativeObserverTest.kt';baselinehost=REPO/'validation/pooled-forward/baseline-v12.6-common-6/assets/android-observer/NativeObserverTest.kt';theme=REPO/'validation/pooled-forward/cache/hosts/reply/Reply/app/src/main/java/com/example/reply/ui/theme/Theme.kt'
    assert sha(host)==sha(baselinehost)
    ledger=dict(version=3,correction_context='Independent pre-code review; no initial production UI implementation exists.',original_root=str(ORIGINAL),original_seal_sha256=ORIGINAL_SEAL,original_inventory_files=829,original_inventory_preserved=True,original_rejection_records='Original sealed bundle and external review records are retained, never rewritten.',necessary_corrections=[dict(id='INPUT-INT32-DOMAIN',finding='The JSON schemas allowed integers outside the shared Kotlin Int transport domain while public briefs claimed complete valid ranges.',change='Explicit signed Int32 bounds on every Int, retaining tighter prior minima and portfolioScore maximum100; accountBalanceCents explicitly ranges -2147483648..2147483647.',schema_field_bounds=bounds),dict(id='KOTLIN-BOOLEAN-TYPE',finding='Three Kotlin API fields were spelled Bool, which is the Swift name rather than the Kotlin Boolean type.',change='Correct only these three public Kotlin type spellings to Boolean; retain Swift Bool, schema boolean, raw fixture values and all business outcomes.',fields=api_corrections),dict(id='ANDROID-HOST-JSON-ABI',finding='The supplied bridges accepted Gson JsonObject while the actual frozen host passes kotlinx.serialization.json.JsonObject.',change='Use the exact host JSON type and serialization primitive/list accessors; preserve the same immutable model field values and verbatim onEvent forwarding.',host_source=str(host.relative_to(REPO)),host_source_sha256=sha(host),baseline_host_sha256=sha(baselinehost),primary_source_lines=[29,35,37,39,297],bridge_files=bridge_corrections),dict(id='ANDROID-FIXED-THEME',finding='The fixed light/non-dynamic environment should be explicit at the actual stock theme entry.',change='Pass darkTheme=false and dynamicColor=false to stock ContrastAwareReplyTheme; no global theme, style expectation, fixture, action, or business rule changes.',theme_source=str(theme.relative_to(REPO)),theme_source_sha256=sha(theme),primary_source_lines=[295,296,298])],arithmetic_scope='The published component rules require comparisons, key equality, and string formatting. No sum, product, or caller revision increment is required. Finite-corpus capability checks do not certify arbitrary implementation arithmetic or universal overflow safety.',frozen_corpus_unchanged=True,unchanged_business_style_files=len(preserved),preserved_files=preserved,fixture_instances_checked_in_both_platform_packets=fixtures_checked,exact_contract_semantics_except_approval_reference_and_android_launch_bridge_identity=True,style_tolerances_changed=False,native_units_changed=False,source_approvals=0,native_runs=0,implementation_or_runtime_feedback_read=False,regenerated_metadata='New-root paths, explicit Android bridge bytes/launch hashes, lock approval references and derived lock/plan/policy/catalog/execution/profile identities are regenerated. They do not change a business expectation.',superseded_v2_drafts=['private/_drafts/before-kotlin-type-correction','private/_drafts/pre-serialization-bridge-correction; complete earlier v2 staging and pure receipts preserved before the ABI correction.'])
    write(ROOT/'CORRECTION-LEDGER.json',ledger)
    domain='''# Shared integer transport domain

All immutable input Int fields use the shared signed 32-bit domain supported by
Kotlin Int, Kotlin serialization jsonPrimitive.int, and the Swift input bridge:
-2147483648 through 2147483647.
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

Swift uses Bool and Kotlin uses Boolean for schema boolean fields. The final Android
bridge accepts the host's kotlinx.serialization.json.JsonObject and uses its
jsonPrimitive.boolean accessor. Model field values and callback forwarding are
unchanged. The stock theme is explicitly light and non-dynamic for this fixed profile.
This clarification was fixed before any production UI code or native execution.
'''
    for t in TASKS:write(ROOT/'public/tasks'/t['id']/'INPUT-DOMAIN.md',domain)
    write(ROOT/'ALL-FINAL-INPUTS-FIXED.json',dict(version=3,fixed_at_utc=datetime.now(timezone.utc).isoformat(),original_seal_sha256=ORIGINAL_SEAL,task_ids=[t['id'] for t in TASKS],public_schema_sha256={t['id']:sha(ROOT/'public/tasks'/t['id']/'fixture.schema.json') for t in TASKS},public_api_sha256={t['id']:sha(ROOT/'public/tasks'/t['id']/'API.md') for t in TASKS},bridge_sha256={family+'-'+t['id']+'-'+platform:sha(ROOT/family/'tasks'/t['id']/platform/('ObserverBridge.swift' if platform=='ios' else 'ObserverBridge.kt')) for family in ['public','private'] for t in TASKS for platform in ['ios','android']},correction_ledger_sha256=sha(ROOT/'CORRECTION-LEDGER.json'),all_existing_fixture_outcome_style_unit_action_denominator_files_unchanged=True,production_ui_written=False,native_execution=False,statement='All five final schemas, language signatures, and exact host-compatible bridges were fixed together by materialize.py before these final dual-SUT pure checks. This index pins those bytes before the new revision seal.'))
    print(json.dumps({'original829_files_preserved':True,'bounded_integer_fields':len(bounds),'kotlin_Boolean_corrections':len(api_corrections),'android_bridge_corrections':len(bridge_corrections),'preserved_business_style_files':len(preserved),'fixture_instances_checked':fixtures_checked,'native_runs':0}))
if __name__=='__main__':main()
