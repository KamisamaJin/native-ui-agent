"""Administrative native PNG calibration; no component/style/business inference."""
from pathlib import Path
import math,struct

class NativeCalibrationUnavailable(ValueError):pass
AGREEMENT_TOLERANCE=0.01  # Same numeric scale agreement used by the initial protocol.

def _number(value):
    return type(value) in (int,float) and math.isfinite(value)

def _rect(value):
    if not isinstance(value,dict) or not all(_number(value.get(k)) for k in ("x","y","width","height")):
        raise NativeCalibrationUnavailable("Explicit finite native rectangle required")
    if value["width"]<=0 or value["height"]<=0:raise NativeCalibrationUnavailable("Positive native rectangle dimensions required")
    return {k:value[k] for k in ("x","y","width","height")}

def original_png_dimensions(path):
    with Path(path).open("rb") as stream:header=stream.read(24)
    if len(header)!=24 or header[:8]!=b"\x89PNG\r\n\x1a\n" or header[12:16]!=b"IHDR":
        raise NativeCalibrationUnavailable("Original native PNG header unavailable")
    w,h=struct.unpack(">II",header[16:24])
    if w<=0 or h<=0:raise NativeCalibrationUnavailable("Positive native PNG dimensions required")
    return w,h

def calibrate(snapshot,platform,png_width,png_height):
    if type(png_width) is not int or type(png_height) is not int or png_width<=0 or png_height<=0:
        raise NativeCalibrationUnavailable("Actual original PNG dimensions required")
    declared=snapshot.get("screenshot_pixels")
    if declared is not None:
        if not isinstance(declared,dict) or type(declared.get("width")) is not int or type(declared.get("height")) is not int:
            raise NativeCalibrationUnavailable("Malformed original screenshot pixel metadata")
        if (declared["width"],declared["height"])!=(png_width,png_height):
            raise NativeCalibrationUnavailable("PNG dimensions conflict with original screenshot metadata")
    if platform=="ios":
        frame=_rect(snapshot.get("app_frame"))
        coordinate_space="absolute app screen points"
        logical_origin=(frame["x"],frame["y"])
        logical_width,logical_height=frame["width"],frame["height"]
    elif platform=="android":
        viewport=snapshot.get("logical_viewport_dp")
        if not isinstance(viewport,dict) or not _number(viewport.get("width")) or not _number(viewport.get("height")) or viewport["width"]<=0 or viewport["height"]<=0:
            raise NativeCalibrationUnavailable("Original attached-view logical_viewport_dp required")
        logical_origin=(0,0)
        logical_width,logical_height=viewport["width"],viewport["height"]
        coordinate_space="attached Compose view dp"
    else:raise NativeCalibrationUnavailable("Unknown native PNG coordinate space")
    scale_x=png_width/logical_width
    scale_y=png_height/logical_height
    if abs(scale_x-scale_y)>AGREEMENT_TOLERANCE:
        raise NativeCalibrationUnavailable("Native app/view frame and PNG disagree on width/height scale")
    reported=snapshot.get("runtime",{}).get("screen_scale")
    if reported is not None:
        if not _number(reported) or reported<=0:
            raise NativeCalibrationUnavailable("Malformed reported native screen_scale")
        if abs(scale_x-reported)>AGREEMENT_TOLERANCE or abs(scale_y-reported)>AGREEMENT_TOLERANCE:
            raise NativeCalibrationUnavailable("Original PNG/frame scale conflicts with reported native screen_scale")
    result={"version":3,"platform":platform,"coordinate_space":coordinate_space,
            "origin_x":logical_origin[0],"origin_y":logical_origin[1],
            "logical_width":logical_width,"logical_height":logical_height,
            "png_width":png_width,"png_height":png_height,
            "scale_x":scale_x,"scale_y":scale_y,
            "native_pixels_per_logical_unit":scale_x}
    if platform=="ios" and snapshot.get("viewport") is not None:
        viewport=_rect(snapshot["viewport"])
        result["viewport_png_rect"]=project_rect(viewport,result)
    return result

def calibrate_png(snapshot,platform,path):
    return calibrate(snapshot,platform,*original_png_dimensions(path))

def project_rect(rect,calibration):
    native=_rect(rect)
    left=(native["x"]-calibration["origin_x"])*calibration["scale_x"]
    top=(native["y"]-calibration["origin_y"])*calibration["scale_y"]
    return [left,top,left+native["width"]*calibration["scale_x"],top+native["height"]*calibration["scale_y"]]

def validate_measurement_scale(calibration,declared_scale):
    if not _number(declared_scale) or declared_scale<=0:
        raise NativeCalibrationUnavailable("Finite positive measurement scale required")
    if abs(declared_scale-calibration["scale_x"])>AGREEMENT_TOLERANCE or abs(declared_scale-calibration["scale_y"])>AGREEMENT_TOLERANCE:
        raise NativeCalibrationUnavailable("Measurement scale contradicts original app/view PNG calibration")
    return declared_scale
