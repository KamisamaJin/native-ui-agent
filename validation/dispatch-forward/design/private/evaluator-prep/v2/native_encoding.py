"""Exact flat-model encoding profiles verified against independent native probes."""
from pathlib import Path
import json,hashlib,base64,functools
ROOT=Path(__file__).resolve().parent
class NativeEncodingUnavailable(ValueError):pass

def _bytes(model,platform):
    if platform not in ("ios","android"):raise NativeEncodingUnavailable("Unknown native platform")
    if not isinstance(model,dict) or any(not isinstance(k,str) or not k.isascii() for k in model):
        raise NativeEncodingUnavailable("Only the observed flat public ASCII-key model domain is established")
    for v in model.values():
        if type(v) not in (str,bool,int):raise NativeEncodingUnavailable("Native encoding for this model primitive type is not established")
        if type(v) is int and not -(2**31)<=v<2**31:raise NativeEncodingUnavailable("Integer outside established native Int model domain")
    try:
        text=json.dumps(model,ensure_ascii=False,sort_keys=platform=="ios",separators=(",",":"))
        if platform=="ios":text=text.replace("/","\\/")
        return text.encode("utf-8")
    except (UnicodeError,ValueError) as exc:raise NativeEncodingUnavailable("Native UTF-8 encoding not established") from exc

@functools.lru_cache(maxsize=2)
def verify_profile(platform):
    try:
        profile=json.loads((ROOT/"encoding-profiles.json").read_text())
        for f in profile["files"]:
            if hashlib.sha256((ROOT/f["path"]).read_bytes()).hexdigest()!=f["sha256"]:
                raise NativeEncodingUnavailable("Native serialization probe artifact changed")
        vectors=json.loads((ROOT/"encoding-vectors.json").read_text())["vectors"]
        native=json.loads((ROOT/profile["platforms"][platform]["native_output"]).read_text())
        outputs={r["id"]:base64.b64decode(r["utf8_base64"],validate=True) for r in native["results"]}
        if len(outputs)!=len(vectors):raise NativeEncodingUnavailable("Incomplete native encoding probe")
        for vector in vectors:
            if _bytes(vector["model"],platform)!=outputs[vector["id"]]:
                raise NativeEncodingUnavailable("Current profile differs from actual native serialization probe")
        return dict(platform=platform,profile_sha256=hashlib.sha256((ROOT/"encoding-profiles.json").read_bytes()).hexdigest(),
                    producer=profile["platforms"][platform]["producer"],producer_source_sha256=profile["platforms"][platform]["producer_source_sha256"],
                    native_probe_output_sha256=hashlib.sha256((ROOT/profile["platforms"][platform]["native_output"]).read_bytes()).hexdigest(),
                    established_domain="flat public model, ASCII member names, String/Bool/32-bit Int primitives")
    except NativeEncodingUnavailable:raise
    except (KeyError,OSError,ValueError,TypeError) as exc:
        raise NativeEncodingUnavailable("Native encoding profile/probe unavailable") from exc

def native_model_hash(model,platform):
    proof=verify_profile(platform)
    data=_bytes(model,platform)
    return hashlib.sha256(data).hexdigest(),dict(proof,encoded_byte_count=len(data))
