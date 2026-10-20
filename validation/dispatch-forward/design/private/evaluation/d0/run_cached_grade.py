"""Optional exact-decoder-cache runner; the frozen evaluator's ordinary CLI is valid.

python3 run_cached_grade.py --manifest PATH --output PATH --timing PATH
"""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import importlib.util,argparse,json,time,hashlib
HERE=Path(__file__).resolve().parent;R=HERE.parents[3]
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def main():
 p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--output',required=True);p.add_argument('--timing',required=True);a=p.parse_args()
 e=module('frozen_v3_cached_execution',R/'design/private/evaluator-prep/v3/evaluator.py');c=module('common_exact_png_cache',HERE/'png_decode_cache.py');h=c.install(e)
 started=time.perf_counter();e.grade(Path(a.manifest),Path(a.output));elapsed=time.perf_counter()-started
 metadata={'execution_optimization':'COMMON read-only exact frozen decoder cache; unrelated to candidate/treatment/tool benefit','wall_seconds':elapsed,'cache':h.metadata(),'wrapper_sha256':c.digest(HERE/'png_decode_cache.py'),'manifest_sha256':c.digest(a.manifest),'output_sha256':c.digest(a.output)}
 Path(a.timing).write_text(json.dumps(metadata,indent=2)+'\n');h.clear();print(json.dumps({'completed':True,'wall_seconds':elapsed,'output_sha256':metadata['output_sha256']}))
if __name__=='__main__':main()
