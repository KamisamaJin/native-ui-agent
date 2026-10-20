"""Read-only execution cache for the exact frozen PNG decoder.

Stable API: handle = install(evaluator, max_entries=2, max_pixels=6500000).
The original CLI remains valid without installation. handle.metadata() and
handle.clear() expose administrative statistics and disposal. No matcher or
measurement is wrapped. Cache key is SHA256 of the full original PNG bytes;
resolved-path identity is rechecked on every call. Decoded objects are returned
unchanged and callers must treat them as immutable, as the frozen evaluator does.
"""
from pathlib import Path
from collections import OrderedDict
import hashlib,time

class ImmutablePNGChanged(ValueError):pass

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

class DecoderCache:
 def __init__(self,evaluator,max_entries,max_pixels):
  if not isinstance(max_entries,int) or max_entries<1 or not isinstance(max_pixels,int) or max_pixels<1:raise ValueError('Positive bounded cache limits required')
  self.original=evaluator.read_png;self.max_entries=max_entries;self.max_pixels=max_pixels
  self.cache=OrderedDict();self.identities={};self.pixels=0;self.calls=0;self.hits=0;self.decodes=0;self.seconds=0
  self.decoder_source=str(Path(evaluator.__file__).resolve());self.decoder_source_sha256=digest(self.decoder_source)
 def __call__(self,path):
  started=time.perf_counter();self.calls+=1;p=Path(path).resolve();key=digest(p)
  prior=self.identities.setdefault(str(p),key)
  if prior!=key:raise ImmutablePNGChanged('Previously observed original PNG bytes changed: '+str(p))
  if key in self.cache:
   self.hits+=1;value=self.cache.pop(key);self.cache[key]=value;self.seconds+=time.perf_counter()-started;return value
  value=self.original(p)
  if digest(p)!=key:raise ImmutablePNGChanged('Original PNG changed during exact decoder read: '+str(p))
  self.decodes+=1;n=value[0]*value[1]
  if n<=self.max_pixels:
   while self.cache and (len(self.cache)>=self.max_entries or self.pixels+n>self.max_pixels):
    _,old=self.cache.popitem(last=False);self.pixels-=old[0]*old[1]
   self.cache[key]=value;self.pixels+=n
  self.seconds+=time.perf_counter()-started;return value
 def clear(self):self.cache.clear();self.pixels=0
 def metadata(self):
  return {'policy':'full-original-byte SHA256 key; immutable resolved-path identity checked every call; exact decoder unchanged; returned dimensions/pixels/representation unmodified; no shared-result mutation',
  'max_entries':self.max_entries,'max_pixels':self.max_pixels,'current_entries':len(self.cache),'current_pixels':self.pixels,
  'calls':self.calls,'cache_hits':self.hits,'exact_decodes':self.decodes,'decoder_seconds':self.seconds,
  'decoder_source':self.decoder_source,'decoder_source_sha256':self.decoder_source_sha256}

def install(evaluator,max_entries=2,max_pixels=6500000):
 if isinstance(evaluator.read_png,DecoderCache):raise ValueError('Decoder cache already installed')
 handle=DecoderCache(evaluator,max_entries,max_pixels);evaluator.read_png=handle;return handle
