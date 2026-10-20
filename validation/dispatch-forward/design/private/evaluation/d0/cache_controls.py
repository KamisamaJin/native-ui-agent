import sys
sys.dont_write_bytecode=True
from pathlib import Path
import hashlib,json,struct,zlib,importlib.util,tempfile
HERE=Path(__file__).resolve().parent;R=HERE.parents[3]
def module(name,p):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
e=module('cache_control_eval',R/'design/private/evaluator-prep/v3/evaluator.py');c=module('cache_control_wrapper',HERE/'png_decode_cache.py')
def png(rgb):
 def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',3,2,8,2,0,0,0))+chunk(b'IDAT',zlib.compress((b'\x00'+bytes(rgb)*3)*2))+chunk(b'IEND',b'')
checks=[]
with tempfile.TemporaryDirectory(prefix='d0-decoder-equivalence-') as tmp:
 p=Path(tmp)/'a.png';p.write_bytes(png((11,29,47)));q=Path(tmp)/'same.png';q.write_bytes(p.read_bytes());b=Path(tmp)/'different.png';b.write_bytes(png((81,103,127)))
 uncached=e.read_png(p);other=e.read_png(b);h=c.install(e,max_entries=1,max_pixels=12)
 checks.append({'id':'exact-decoder-value-and-representation','passed':e.read_png(p)==uncached and type(e.read_png(p))==type(uncached)})
 checks.append({'id':'same-original-sha-reuses-unmodified-value','passed':e.read_png(q)==uncached and h.hits>=1})
 checks.append({'id':'different-sha-gets-different-exact-decode','passed':e.read_png(b)==other and other!=uncached})
 p.write_bytes(png((190,170,150)))
 try:e.read_png(p);rejected=False
 except c.ImmutablePNGChanged:rejected=True
 checks.append({'id':'changed-original-bytes-rejected-before-stale-hit','passed':rejected})
 checks.append({'id':'bounded-entry-and-pixel-count','passed':len(h.cache)<=1 and h.pixels<=12})
 h.clear();checks.append({'id':'clear-discards-decoded-cache','passed':len(h.cache)==0 and h.pixels==0})
report={'scope':'generic synthetic PNGs only; no business/candidate expectations or native UI run','controls':checks,'all_passed':all(x['passed'] for x in checks),'metadata':h.metadata(),'wrapper_sha256':c.digest(HERE/'png_decode_cache.py')}
(HERE/'cache-controls-report.json').write_text(json.dumps(report,indent=2)+'\n')
assert report['all_passed'];print(json.dumps({'controls':len(checks),'all_passed':report['all_passed'],'wrapper_sha256':report['wrapper_sha256']}))
