#!/usr/bin/env python3
"""Empirical native projection diagnostics; never change a design threshold/verdict.

The profile is fitted before business code and checked on held-out native leaves.
An interval crossing a decision boundary is uncertainty, never a passing waiver.
"""
from __future__ import annotations
import argparse,copy,json,math
from fractions import Fraction
from pathlib import Path
import design_contract as d
import native_geometry as geometry


def budget(frame, axis):
    key='x'if axis=='width'else'y'
    a=float(frame[key]);size=float(frame[axis])
    return math.ulp(a)+math.ulp(a+size)+math.ulp(size)


def fit(extraction, context, provenance):
    rows=extraction['rows'];splits=extraction['sample_split'];usable=[];rejected=[]
    for row in rows:
        if not row.get('eligible_identity_transform_sample')or not row.get('fully_within_viewport'):continue
        runtime=row['runtime'];frame=row['raw_xcui_frame'];reference=row['reference_bounds']
        if any(geometry.number(runtime['bounds'][k])!=geometry.number(reference[k])for k in ['x','y','width','height']):
            rejected.append({'identifier':row['identifier'],'reason':'Runtime bounds differ from sealed reference'});continue
        native=runtime['accessibility_frame']
        # Snapshot position and in-process reference must describe the same
        # settled projection. Preserve excluded scroll-coherence failures.
        coherent=all(abs(float(frame[k])-float(native[k]))<=8*(math.ulp(float(frame[k]))+math.ulp(float(native[k])))for k in ['x','y'])
        if not coherent:
            rejected.append({'identifier':row['identifier'],'reason':'Position changed between reference and XCUI snapshot'});continue
        item={'identifier':row['identifier'],'split':row['split'],'frame':frame,'bounds':runtime['bounds'],'residuals':{},'ratios':{}}
        for axis in ['width','height']:
            error=abs(float(geometry.number(frame[axis])-geometry.number(runtime['bounds'][axis])))
            item['residuals'][axis]=error;item['ratios'][axis]=error/budget(frame,axis)
        usable.append(item)
    fitting=[v for v in usable if v['split']=='fit'];held=[v for v in usable if v['split']=='heldout']
    present={v['identifier']for v in fitting};held_present={v['identifier']for v in held}
    factor=max(1,math.ceil(max((r for v in fitting for r in v['ratios'].values()),default=0)))
    # This is a predeclared small floating-projection model, not an arbitrary
    # fitted tolerance. Large semantic/projection discrepancies invalidate it.
    fit_supported=factor<=8
    held_failures=[{'identifier':v['identifier'],'axis':axis,'ratio':v['ratios'][axis]}for v in held for axis in ['width','height']if v['ratios'][axis]>factor]
    valid=bool(fitting and held and present==set(splits['fit'])and held_present==set(splits['heldout'])and fit_supported and not held_failures)
    positions=[abs(float(v['frame'][k]))for v in usable for k in ['x','y']]
    sizes=[float(v['frame'][k])for v in usable for k in ['width','height']]
    return {'version':1,'provider':'xcui_cgrect','numeric_encoding':'binary64','status':'validated'if valid else'unsupported_or_incomplete',
            'context':context,'provenance':provenance,'factor':factor,'factor_fit_uses_heldout':False,'maximum_supported_factor':8,
            'fit_ids':sorted(present),'heldout_ids':sorted(held_present),'fit_rows':len(fitting),'heldout_rows':len(held),
            'heldout_failures':held_failures,'rejected_rows':rejected,'raw_residuals':usable,
            'domain':{'max_abs_coordinate':max(positions,default=0),'max_extent':max(sizes,default=0),
                      'max_extent_by_axis':{axis:max((v['frame'][axis]for v in usable),default=0)for axis in ['width','height']}},
            'formula':'factor * (ulp(origin) + ulp(origin + extent) + ulp(extent)); fit factor capped at 8; separate native holdout.',
            'scope':'Diagnostic empirical coordinate-projection envelope for observed identity-transform UIKit leaves/current context. Not a universal guarantee for SwiftUI, custom AX, layout allocation, touch area, fonts or padding. Original strict outcomes and thresholds remain unchanged.'}


def classify(measurement, expected, op, tolerance, profile, runtime):
    context=profile.get('context',{});sources=measurement.get('sources',[])
    valid=(profile.get('status')=='validated'and profile.get('provider')=='xcui_cgrect'and profile.get('numeric_encoding')=='binary64'
           and 1<=profile.get('factor',0)<=8 and profile.get('factor_fit_uses_heldout')is False
           and context and all(runtime.get(k)==v for k,v in context.items()))
    prop=measurement.get('property')
    axes=['width']if prop in {'width','gap_x','inset_left','inset_right'}else['height']if prop in {'height','gap_y','inset_top','inset_bottom'}else['width','height']
    radii=[]
    for source in sources:
        frame=source.get('sample',{});domain=profile.get('domain',{})
        if (source.get('provider')!='xcui_cgrect'or any(type(frame.get(k))not in {int,float}or not math.isfinite(frame[k])for k in ['x','y','width','height'])
                or max(abs(frame['x']),abs(frame['y']))>domain.get('max_abs_coordinate',-1)
                or any(frame[axis]>domain.get('max_extent_by_axis',{}).get(axis,domain.get('max_extent',-1))for axis in axes)):
            valid=False;continue
        radii.append(profile['factor']*sum(budget(frame,axis)for axis in axes))
    if not valid or not radii:return {'classification':'outside_calibrated_scope','strict_verdict_preserved':True,'reason':'Profile/context/sample domain does not establish a calibrated projection envelope'}
    radius=sum((geometry.number(v)for v in radii),Fraction(0));value=Fraction(*measurement['ratio']);wanted=geometry.number(expected)
    low,high=value-radius,value+radius
    if op=='gte':overlap=low<wanted<=high
    elif op=='lte':overlap=low<=wanted<high
    elif op=='eq':overlap=low<=wanted<=high
    elif op=='near':
        tol=geometry.number(tolerance);overlap=not(high<wanted-tol or low>wanted+tol)and not(low>=wanted-tol and high<=wanted+tol)
    else:raise ValueError('Known numeric comparator required')
    return {'classification':'boundary_overlap'if overlap else'definite_within_profile','strict_verdict_preserved':True,
            'interval_ratios':[[low.numerator,low.denominator],[high.numerator,high.denominator]],
            'radius_ratio':[radius.numerator,radius.denominator],'expected_unchanged':expected,'operator_unchanged':op,
            'reason':'Boundary overlaps an empirical numeric envelope; no pass or product cause is inferred'if overlap else'Strict comparison is separated from the boundary by the calibrated numeric envelope',
            'scope':profile['scope']}


def annotate(plan, observation, report, profile):
    result=copy.deepcopy(report)
    if plan['design_contract']['platform']!='ios':return result
    rules={r['id']:r for r in plan['assertions']};snapshots=observation.get('snapshots',[])
    for row in result.get('assertions',result.get('rows',[])):
        rule=rules[row['id']]
        if rule['kind']!='geometry'or row['status']=='passed':continue
        diagnoses=[]
        for measurement in row.get('geometry_evidence',[]):
            if 'ratio'not in measurement:continue
            index=measurement['snapshot'];runtime=snapshots[index].get('runtime',{})if 0<=index<len(snapshots)else{}
            diagnoses.append(classify(dict(measurement,property=rule['property']),rule['expected'],rule.get('op','eq'),rule.get('tolerance'),profile,runtime))
        if diagnoses:
            category='outside_calibrated_scope'if any(v['classification']=='outside_calibrated_scope'for v in diagnoses)else'boundary_overlap'if any(v['classification']=='boundary_overlap'for v in diagnoses)else'definite_within_profile'
            row['measurement_calibration']={'classification':category,'samples':diagnoses,'profile_sha256':d.digest(profile),'raw_status':row['status'],'expected_and_tolerance_unchanged':True}
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--extraction',type=Path,required=True);p.add_argument('--context',type=Path,required=True);p.add_argument('--provenance',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    with a.output.open('x')as f:f.write(json.dumps(fit(d.load(a.extraction),d.load(a.context),d.load(a.provenance)),indent=2)+'\n')
