#!/usr/bin/env python3
"""Equal native capture capability for both arms; no business grading thresholds."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET


def expand(value, root):
    if isinstance(value,str): return value.replace("__TESTROOT__",str(root))
    if isinstance(value,list): return [expand(x,root) for x in value]
    if isinstance(value,dict): return {key:expand(x,root) for key,x in value.items()}
    return value


def bind(node, values):
    count=0
    if isinstance(node,dict):
        if "TestBundlePath" in node:
            node.setdefault("EnvironmentVariables",{}).update(values);count+=1
        for value in list(node.values()): count+=bind(value,values)
    elif isinstance(node,list):
        for value in node: count+=bind(value,values)
    return count


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--platform",choices=["android","ios"],required=True)
    p.add_argument("--project",type=Path,required=True)
    p.add_argument("--fixture",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    started=time.monotonic();project=a.project.resolve();fixture=a.fixture.resolve();output=a.output.resolve()
    if output.exists() and any(output.iterdir()): raise SystemExit("Use a fresh output directory")
    output.mkdir(parents=True,exist_ok=True)
    environment=json.loads((Path(__file__).parent/"environment.json").read_text())
    env=os.environ.copy();env.update({"JAVA_HOME":environment["java_home"],"ANDROID_HOME":environment["android_sdk"],
        "DEVELOPER_DIR":environment["developer_dir"],"NATIVE_UI_OUTPUT":str(output),"NATIVE_UI_SCENARIO":"capture","BENCH_FIXTURE":str(fixture)})
    commands=[]
    def run(argv,cwd=project,capture=False):
        t=time.monotonic()
        result=subprocess.run(argv,cwd=cwd,env=env,check=True,text=True,capture_output=capture)
        commands.append({"argv":argv,"duration_seconds":round(time.monotonic()-t,3),"exit_code":result.returncode})
        return result
    if a.platform=="android":
        run(["./gradlew",":app:testDebugUnitTest","--tests","com.example.reply.BlindPanelUiTest.capture","--console=plain"])
        junit=project/"app/build/test-results/testDebugUnitTest/TEST-com.example.reply.BlindPanelUiTest.xml"
        suite=ET.parse(junit).getroot().attrib
        if int(suite["tests"])!=1 or int(suite.get("failures",0)) or int(suite.get("errors",0)): raise SystemExit("Intended native test did not pass")
        shutil.copy2(junit,output/"junit.xml")
        payload=(output/"paparazzi-report/runs/capture.js").read_text().split(" = ",1)[1].rstrip().removesuffix(";")
        shots=json.loads(payload)
        if len(shots)!=1 or shots[0]["testName"]!="com.example.reply.BlindPanelUiTest#capture": raise SystemExit("Wrong native snapshot")
        image=(output/"paparazzi-report"/shots[0]["file"]).resolve()
        if not image.is_relative_to(output): raise SystemExit("Escaped report path")
        shutil.copy2(image,output/"actual.png")
    else:
        cache=Path(__file__).parent/"native-cache/ios";derived=cache/"derived-data"
        destination="platform=iOS Simulator,id="+environment["ios_device"]
        run(["xcodebuild","build-for-testing","-scheme","AlertToast","-destination",destination,
            "-derivedDataPath",str(derived),"-clonedSourcePackagesDirPath",str(cache/"packages"),"CODE_SIGNING_ALLOWED=NO"])
        originals=sorted((derived/"Build/Products").glob("*.xctestrun"),key=lambda x:x.stat().st_mtime_ns,reverse=True)
        if not originals:raise SystemExit("Missing native test host")
        original=originals[0]
        with original.open("rb") as stream: config=expand(plistlib.load(stream),original.parent)
        if not bind(config,{key:env[key] for key in ["NATIVE_UI_OUTPUT","BENCH_FIXTURE"]}):raise SystemExit("Missing test target")
        configured=output/"capture.xctestrun"
        with configured.open("wb") as stream:plistlib.dump(config,stream)
        run(["xcodebuild","test-without-building","-xctestrun",str(configured),"-destination",destination,
             "-parallel-testing-enabled","NO","-only-testing:AlertToastTests/BlindPanelUiTests/testCapture",
             "-resultBundlePath",str(output/"result.xcresult")])
        result=run(["xcrun","xcresulttool","get","test-results","summary","--path",str(output/"result.xcresult"),"--compact"],capture=True)
        summary=json.loads(result.stdout)
        (output/"xcresult-summary.json").write_text(json.dumps(summary,indent=2)+"\n")
        if summary.get("totalTestCount")!=1 or summary.get("passedTests")!=1 or summary.get("failedTests")!=0:raise SystemExit("Wrong native test count")
    if not (output/"actual.png").exists() or not (output/"native-report.json").exists():raise SystemExit("Missing native output")
    sources=list((project/("app/src/main/java/com/example/reply/ui/components" if a.platform=="android" else "Sources/AlertToast")).glob("*Transfer*"))
    manifest={"platform":a.platform,"fixture_sha256":hashlib.sha256(fixture.read_bytes()).hexdigest(),
        "harness_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "actual_sha256":hashlib.sha256((output/"actual.png").read_bytes()).hexdigest(),
        "production_sources":{str(path.relative_to(project)):hashlib.sha256(path.read_bytes()).hexdigest() for path in sources if path.is_file()},
        "duration_seconds":round(time.monotonic()-started,3),"commands":commands,"status":"captured_not_graded"}
    (output/"capture.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps({"status":"captured_not_graded","actual":str(output/"actual.png"),"duration_seconds":manifest["duration_seconds"]}))


if __name__=="__main__":main()
