#!/usr/bin/env python3
"""Publish tested shared width adapter only after blind stages and reveal."""
import hashlib,json,shutil,time
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parent;REPO=R.parents[1]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inventory(root):return {str(p.relative_to(root)):sha(p)for p in sorted(root.rglob('*'))if p.is_file()and '__pycache__'not in p.parts and p.name!='.DS_Store'}
def main():
 release=R/'private/ASSIGNMENT-RELEASE.json';assert release.is_file();out=R/'RELEASE-BUNDLE.json';assert not out.exists();live=REPO/'native-ui-agent';assert inventory(live)==inventory(R/'candidate-v6')
 shutil.copy2(R/'runtime-candidate-v6/scripts/ios_observe.py',live/'scripts/ios_observe.py')
 p=live/'assets/ios-observer/CONTRACT.md';s=p.read_text();old='The host offers width 320 or 390 points and a 600-point native vertical ScrollView,';new='The frontend accepts a finite offered width from 160 to 1024 points. The host uses\na 600-point native vertical ScrollView; actual native viewport/content frames must\nestablish whether a requested width fits the chosen simulator,';assert old in s;p.write_text(s.replace(old,new))
 p=live/'references/native-tools.md';s=p.read_text();assert 'width320/390'in s;p.write_text(s.replace('width320/390','finite offered width160–1024pt (verify actual viewport)'))
 files=inventory(live);original=inventory(R/'candidate-v6');changed=sorted(k for k in files if files[k]!=original[k]);assert changed==['assets/ios-observer/CONTRACT.md','references/native-tools.md','scripts/ios_observe.py']
 out.write_text(json.dumps({'publishedAtUTC':datetime.now(timezone.utc).isoformat(),'publishedAtUnix':time.time(),'baseFrozenTool':'candidate-v6','commonWidthAdapter':'runtime-candidate-v6','commonReleaseChanges':changed,'assignmentReleaseSHA256':sha(release),'commonWidthAmendmentSHA256':sha(R/'COMMON-WIDTH-AMENDMENT.json'),'files':files,'scope':'Live release includes exact shared frontend adapter already exercised on both arms and neutral340pt. Frozen experiment tools/evidence remain unchanged. Documentation mirrors shared width policy; no post-outcome observer/assertion/expected-value adjustment.'},indent=2)+'\n');print('tested shared adapter published; frozen trial tools unchanged')
if __name__=='__main__':main()
