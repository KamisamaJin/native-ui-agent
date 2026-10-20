#!/usr/bin/env python3
"""Synthetic original PNG/native-metadata controls. No candidate artifacts used."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import importlib.util,json,copy,tempfile,struct,zlib,binascii,hashlib,datetime,math
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("frozen_v3_geometry_controls",ROOT/"evaluator.py")
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
g=e.geometry_calibration_module()
results=[]
def test(name,fn):
    fn();results.append({"id":name,"status":"PASS"})
def reject(fn):
    try:fn()
    except (g.NativeCalibrationUnavailable,ValueError):return
    raise AssertionError("Invalid geometry calibration accepted")
def png(path,width,height):
    def chunk(kind,data):
        return struct.pack(">I",len(data))+kind+data+struct.pack(">I",binascii.crc32(kind+data)&0xffffffff)
    compressor=zlib.compressobj()
    data=[]
    row=b"\x00"+b"\xff\xff\xff"*width
    for y in range(height):
        if 30<=y<90:
            marked=bytearray(row)
            marked[1+30*3:1+33*3]=b"\x00"*9
            data.append(compressor.compress(bytes(marked)))
        else:data.append(compressor.compress(row))
    data.append(compressor.flush())
    content=b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",struct.pack(">IIBBBBB",width,height,8,2,0,0,0))+chunk(b"IDAT",b"".join(data))+chunk(b"IEND",b"")
    path.write_bytes(content)
def ios(width=390,origin=(0,0)):
    x,y=origin
    return {"app_frame":{"x":x,"y":y,"width":402,"height":874},
            "viewport":{"x":x+(402-width)/2,"y":y+62,"width":width,"height":600},
            "screenshot_pixels":{"width":1206,"height":2622},"runtime":{"screen_scale":3},"screenshot":"original.png"}

with tempfile.TemporaryDirectory(prefix="original-png-calibration-",dir=ROOT) as tmp:
    root=Path(tmp);image=root/"original.png";png(image,1206,2622)
    for width in (320,390):
        def known(w=width):
            calibration=g.calibrate_png(ios(w),"ios",image)
            assert calibration["native_pixels_per_logical_unit"]==3
            vp=ios(w)["viewport"]
            assert calibration["viewport_png_rect"]==[(402-w)/2*3,186,((402-w)/2+w)*3,1986]
        test("full-App-PNG-calibrates-host-"+str(width),known)
        test("reject-PNG-over-narrow-viewport-scale-"+str(width),
             lambda w=width:reject(lambda:g.validate_measurement_scale(g.calibrate_png(ios(w),"ios",image),1206/w)))
    def nonzero_origin():
        snapshot=ios(390,(100.5,200.25));calibration=g.calibrate_png(snapshot,"ios",image)
        projected=g.project_rect({"x":122.5,"y":300.25,"width":100,"height":20},calibration)
        assert projected==[66,300,366,360]
        assert calibration["viewport_png_rect"]==[18,186,1188,1986]
    test("subtract-nonzero-App-origin-before-projection",nonzero_origin)
    def negative_origin():
        snapshot=ios(320,(-40,-20));calibration=g.calibrate_png(snapshot,"ios",image)
        assert g.project_rect({"x":-30,"y":-10,"width":4,"height":6},calibration)==[30,30,42,48]
    test("negative-App-origin-projects-correctly",negative_origin)
    def roundtrip():
        c=g.calibrate_png(ios(320,(100,200)),"ios",image)
        rect={"x":120,"y":260,"width":17,"height":11}
        left,top,right,bottom=g.project_rect(rect,c)
        assert left/c["scale_x"]+c["origin_x"]==rect["x"]
        assert top/c["scale_y"]+c["origin_y"]==rect["y"]
        assert (right-left)/c["scale_x"]==rect["width"]
        assert (bottom-top)/c["scale_y"]==rect["height"]
    test("native-to-PNG-coordinate-roundtrip",roundtrip)
    mutations={
      "missing-App-frame":lambda s:s.pop("app_frame"),
      "zero-App-width":lambda s:s["app_frame"].update(width=0),
      "negative-App-height":lambda s:s["app_frame"].update(height=-874),
      "nonfinite-App-origin":lambda s:s["app_frame"].update(x=float("nan")),
      "conflicting-native-screen-scale":lambda s:s["runtime"].update(screen_scale=2),
      "Boolean-native-screen-scale":lambda s:s["runtime"].update(screen_scale=True),
      "conflicting-PNG-width-metadata":lambda s:s["screenshot_pixels"].update(width=1170),
      "conflicting-PNG-height-metadata":lambda s:s["screenshot_pixels"].update(height=1800),
      "Boolean-PNG-width":lambda s:s["screenshot_pixels"].update(width=True),
      "anisotropic-App-frame":lambda s:s["app_frame"].update(height=800)
    }
    for name,mutation in mutations.items():
        def invalid(m=mutation):
            snapshot=ios();m(snapshot)
            reject(lambda:g.calibrate_png(snapshot,"ios",image))
        test("reject-"+name,invalid)
    def no_reported_scale():
        snapshot=ios();snapshot["runtime"].pop("screen_scale")
        assert g.calibrate_png(snapshot,"ios",image)["scale_x"]==3
    test("explicit-App-frame-and-original-PNG-suffice-without-optional-reported-scale",no_reported_scale)
    cropped=root/"cropped.png";png(cropped,1170,1800)
    def cropped_viewport():
        snapshot=ios();snapshot["screenshot_pixels"]={"width":1170,"height":1800}
        reject(lambda:g.calibrate_png(snapshot,"ios",cropped))
    test("reject-viewport-crop-as-full-App-image",cropped_viewport)
    # The old faulty width-only formula would accept this declared scale; V3 rejects it.
    test("reject-anisotropic-crop-scale",lambda:reject(lambda:g.calibrate(ios(), "ios",1170,2622)))
    def unknown_platform():
        reject(lambda:g.calibrate_png(ios(),"unknown",image))
    test("reject-unknown-coordinate-space",unknown_platform)
    android_image=root/"android.png";png(android_image,1072,1650)
    android={"logical_viewport_dp":{"width":1072/2.75,"height":600},
             "screenshot_pixels":{"width":1072,"height":1650},"screenshot":"android.png"}
    def android_scale():
        c=g.calibrate_png(android,"android",android_image)
        assert abs(c["scale_x"]-2.75)<1e-12 and c["scale_y"]==2.75
        assert g.project_rect({"x":16,"y":24,"width":100,"height":44},c)==[44,66,319,187]
    test("Android-full-attached-view-actual-logical_viewport_dp",android_scale)
    def android_missing():
        snapshot=copy.deepcopy(android);snapshot.pop("logical_viewport_dp")
        reject(lambda:g.calibrate_png(snapshot,"android",android_image))
    test("reject-Android-missing-attached-view-dp-metadata",android_missing)
    def android_conflict():
        snapshot=copy.deepcopy(android);snapshot["logical_viewport_dp"]["height"]=550
        reject(lambda:g.calibrate_png(snapshot,"android",android_image))
    test("reject-Android-conflicting-width-height-scale",android_conflict)

    def visual_geometry(width=390,origin=(0,0),wrong_scale=False,missing_frame=False):
        snapshot=ios(width,origin)
        if missing_frame:snapshot.pop("app_frame")
        observation={"snapshots":[snapshot]}
        obs=root/"observation.json";obs.write_text(json.dumps(observation))
        obsref={"path":"observation.json","sha256":e.digest(obs)}
        image_ref={"path":"original.png","sha256":e.digest(image)}
        row={"key":"ios/SYN/initial/scale-control","method":"pixels","platform":"ios",
             "expected":{"part":"border_width","equals":1,"unit":"logical","tolerance":1},
             "full_content":False}
        decision={"key":row["key"],"outcome":"P","method":"pixels",
            "reason":"Synthetic strip only validates coordinate format, not a business component style.",
            "observation_sha256":obsref["sha256"],"snapshot_indices":[0],"evidence":[image_ref],
            "target_region":{"0":[20,20,50,100]},"witness":"Original synthetic 3-native-pixel vertical strip at x30..32.",
            "measurement":{"segments":[{"snapshot":0,"a":[30,40],"b":[33,40],
               "native_pixels_per_logical_unit":1206/width if wrong_scale else 3}]}}
        context={"found":[(0,snapshot)],"complete":True,"observation_ref":obsref,"observation":observation}
        if wrong_scale:
            reject(lambda:e.visual_decision(row,decision,context,root))
        else:
            outcome,actual,reason,_=e.visual_decision(row,decision,context,root)
            assert outcome==("U" if missing_frame else "P"),reason
            if not missing_frame:assert actual==[1.0]
    test("integrated-pixel-geometry-measurement-host390",visual_geometry)
    test("integrated-pixel-geometry-measurement-host320",lambda:visual_geometry(320))
    test("integrated-pixel-geometry-nonzero-origin",lambda:visual_geometry(390,(100.5,200.25)))
    test("integrated-reject-viewport-derived-measurement-scale",lambda:visual_geometry(390,wrong_scale=True))
    test("integrated-missing-App-frame-stays-U",lambda:visual_geometry(missing_frame=True))

report={"version":3,"status":"PASS","tested_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "candidate_source_images_or_evidence_used":False,"generic_evidence_read":False,
        "synthetic_original_PNGs_only":True,"control_count":len(results),"controls":results}
(ROOT/"geometry-controls-report.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps({"status":"PASS","control_count":len(results)}))
