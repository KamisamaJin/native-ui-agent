"""Source-sample geometry tests; these are metrology controls, not UI defects."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import native_checks as n
import native_geometry as g


def node(x=10000.0, y=50000.0, width=198, height=132, density=2.75):
    return dict(node_id=1, parent_id=-1, identifier='neutral', label='Neutral',
                intersects_viewport=True, fully_visible=True, unclipped_bounds_dp=[10, 20, 82, 67.99994],
                native_geometry=dict(version=1, provider='compose_semantics_int_size', coordinate_unit='px',
                                     density=density, position_px=[x,y], size_px=[width,height]))


class NativeGeometryTests(unittest.TestCase):
    def measure(self, value, **changes):
        rule=dict(target={'identifier':'neutral'}, property='height', **changes)
        return n.geometry_measurement({'nodes':[value]}, rule, 'android')

    def test_native_extent_does_not_subtract_rounded_scrolled_endpoints(self):
        for y in [0, 501.25, 99999.75, 100000000.0]:
            measurement=self.measure(node(y=y))
            self.assertEqual(measurement['value'],48)
            self.assertEqual(measurement['ratio'],[48,1])
            self.assertTrue(g.compare(measurement,48,'gte'))
            self.assertIn('compose_semantics_int_size',str(measurement['sources']))

    def test_real_smaller_or_larger_samples_still_fail(self):
        self.assertFalse(g.compare(self.measure(node(height=131)),48,'gte'))
        self.assertFalse(g.compare(self.measure(node(height=133)),48,'lte'))
        self.assertFalse(g.compare(self.measure(node(height=133)),48,'near',0.1))
        self.assertTrue(g.compare(self.measure(node(height=133)),48,'near',0.5))

    def test_untrusted_or_missing_native_data_does_not_get_precision_credit(self):
        original=node();del original['native_geometry']
        measurement=self.measure(original)
        self.assertEqual(measurement['method'],'legacy_rounded_bounds')
        self.assertFalse(n.compare(measurement['value'],48,'gte'))
        for key,value in [('density',0),('density',True),('density',float('nan')),
                          ('size_px',[198,131.0]),('position_px',[1,float('inf')]),('provider','invented')]:
            invalid=node();invalid['native_geometry'][key]=value
            self.assertIsNone(self.measure(invalid))

    def test_relations_use_two_unique_visible_boxes_same_frame(self):
        first=node(x=27.5,y=55,width=198);other=node(x=246.125,y=55);other['identifier']='second';other['node_id']=2
        rule=dict(target={'identifier':'second'},reference_target={'identifier':'neutral'},property='gap_x')
        result=n.geometry_measurement({'nodes':[first,other]},rule,'android')
        self.assertEqual(result['value'],7.5)
        other['fully_visible']=False
        self.assertIsNone(n.geometry_measurement({'nodes':[first,other]},rule,'android'))

    def test_direct_cgrect_extent_avoids_cancellation(self):
        value=dict(frame=dict(x=1e18,y=1e18,width=12,height=24))
        box,proof=g.native_box(value,'ios')
        self.assertEqual(box[2],12)
        self.assertEqual(box[3],24)
        self.assertEqual(proof['provider'],'xcui_cgrect')

    def test_real_conflict_remains_unassessed_and_legacy_data_stays_strict(self):
        binding={'instance':'neutral','input_sha256':'x','fixture_index':0,'event_revision':0}
        snapshots=[dict(nodes=[node(height=h)],state_id='s',binding=binding,capture_consistent=True)for h in [131,133]]
        bundle=dict(state_id='s',after_action=0,binding=binding,binding_after_observation=binding,binding_stable=True,snapshot_indices=[0,1])
        observation=dict(snapshots=snapshots,steps=[dict(state_id='s',binding_after=binding,immediate_after=0,after=1,observation_set=bundle)])
        plan=dict(version=1,states=[dict(id='s',input_index=0,after_action=0,coverage='targets')],assertions=[dict(id='height',state='s',kind='geometry',target={'identifier':'neutral'},property='height',expected=48,op='gte')])
        row=n.evaluate(plan,observation,'android')['assertions'][0]
        self.assertEqual(row['status'],'unassessed')
        self.assertEqual(len(row['geometry_evidence']),2)
        snapshots[0]['nodes'][0]['native_geometry']['size_px'][1]=132
        snapshots[1]['nodes'][0]['native_geometry']['size_px'][1]=132
        self.assertEqual(n.evaluate(plan,observation,'android')['assertions'][0]['status'],'passed')
        plan['assertions'][0]['measurement']='layout_box'
        self.assertEqual(n.evaluate(plan,observation,'android')['assertions'][0]['status'],'unassessed')

if __name__=='__main__':unittest.main()
