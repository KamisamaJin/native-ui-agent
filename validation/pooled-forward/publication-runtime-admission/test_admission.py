"""Small source/host/support-library mechanism controls. Not native evaluation."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import unittest

import admit_runtime as ar


HERE=Path(__file__).resolve().parent
OUTPUT=None


class Mechanism(unittest.TestCase):
    def test_01_source_and_fixed_golden_pins(self):
        value=ar.verify_sources();self.assertEqual(value['golden_manifest_sha256'],ar.GOLDEN_SHA)

    def test_02_linux_ci_cannot_be_claimed_by_darwin(self):
        ar.check_target('linux-py311','Linux',(3,11))
        for system,version in [('Darwin',(3,11)),('Linux',(3,9)),('Linux',(3,12))]:
            with self.assertRaisesRegex(ValueError,'actual Linux Python3.11'):ar.check_target('linux-py311',system,version)

    def test_03_exact_pillow11_3_and_metadata(self):
        ar.check_pillow('11.3.0','11.3.0')
        for a,b in [('12.0.0','12.0.0'),('11.3.0','11.2.0'),('11.3.1','11.3.1')]:
            with self.assertRaisesRegex(ValueError,'Pillow11.3.0'):ar.check_pillow(a,b)

    def test_04_wheel_paths_and_libraries_are_explicit(self):
        self.assertEqual(ar.wheel_kind('PIL/Image.py'),'package');self.assertEqual(ar.wheel_kind('pillow.libs/libjpeg.so.62'),'support')
        self.assertEqual(ar.wheel_kind('pillow-11.3.0.dist-info/licenses/LICENSE'),'metadata')
        for path in ['../source.py','/actual/source.py','PIL/../source.py']:
            with self.assertRaises(ValueError):ar.wheel_kind(path)
        self.assertIsNone(ar.wheel_kind('unrelated_package/fake.py'))

    def test_05_unchanged_worker_and23_controls(self):
        self.assertEqual(ar.sha((HERE/'vendor/runner/worker.py').read_bytes()),'2e8d9865e6823c201a4be7a01b9e5de5e1e786e3f6b0d1736c2d85a160ee3f4c')
        self.assertEqual(ar.sha((HERE/'vendor/test_replay.py').read_bytes()),'7095e81059a864c713c1117c6ae226a8d90015f8faf0c4f8bb164d811b2b1869')

    def test_06_support_files_are_added_and_corruption_rejected(self):
        root=OUTPUT/'support-layout';root.mkdir();source=ar.verify_sources();owned=root/'owned';owned.mkdir()
        backends=ar.stage_sources(owned,source)
        runtime=owned/'vendor/runtime';ar.copy_raw(runtime/'PIL/__init__.py',b'# synthetic runtime inventory only; never imported\n')
        ar.copy_raw(runtime/'pillow.libs/proof.so',b'synthetic wheel support proof; never executed\n')
        inventory={'version':1,'kind':'externally-pinned-isolated-evaluator-code-inventory','backends':backends,
            'runtime':{'root':str(runtime),'files':{'PIL/__init__.py':ar.ref(runtime/'PIL/__init__.py')},
                       'support_files':{'pillow.libs/proof.so':ar.ref(runtime/'pillow.libs/proof.so')},
                       'interpreter':{'sha256':ar.sha(Path(sys.executable).read_bytes())},'version':sys.version}}
        inv=root/'INVENTORY.json';inv.write_text(json.dumps(inventory,indent=2)+'\n')
        spec=importlib.util.spec_from_file_location('mechanism_current_driver',owned/'replay.py');rp=importlib.util.module_from_spec(spec);spec.loader.exec_module(rp)
        class Reader:
            def read_bytes(self,p):return Path(p).read_bytes()
            def hash(self,p):return ar.sha(self.read_bytes(p))
            def directory(self,p):return Path(p)
        inv_ref={'path':str(inv),'sha256':ar.sha(inv.read_bytes())};worker_ref=ar.ref(owned/'runner/worker.py');reader=Reader()
        job,_=rp.code_job(rp.Access(reader),inv_ref,worker_ref,'A')
        self.assertTrue(any(r['physical_path']==str(runtime/'pillow.libs/proof.so') for r in job['code_files']))
        # Mutate only this synthetic support proof, not a real wheel/runtime.
        p=runtime/'pillow.libs/proof.so';p.chmod(0o644);p.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'Original pin differs'):rp.code_job(rp.Access(reader),inv_ref,worker_ref,'A')
        p.unlink()
        with self.assertRaisesRegex(ValueError,'support layout differs'):rp.code_job(rp.Access(reader),inv_ref,worker_ref,'A')


def main():
    global OUTPUT
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();OUTPUT=args.output.absolute()
    ar.need(OUTPUT.is_relative_to(HERE/'HOST') and not OUTPUT.exists(),'Fresh owned mechanism output required');OUTPUT.mkdir(parents=True,exist_ok=False)
    with (OUTPUT/'RUN.log').open('w') as stream:
        result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Mechanism))
    value={'version':1,'kind':'runtime-admission-mechanism-controls','tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'passed':result.wasSuccessful(),
           'synthetic_only':True,'support_library_bytes_executed':False,'actual_study_data_used':False}
    path=OUTPUT/'RESULT.json';path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n');print(json.dumps({'path':str(path),'sha256':ar.sha(path.read_bytes()),'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors)}))
    return 0 if result.wasSuccessful() else 1


if __name__=='__main__':raise SystemExit(main())
