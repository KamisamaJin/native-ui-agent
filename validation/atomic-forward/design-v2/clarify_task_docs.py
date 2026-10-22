from pathlib import Path
import shutil,json,datetime
R=Path(__file__).resolve().parent;A=R/'attempts'/'02-template-docs';A.mkdir(parents=True)
for tid in ['T1','T2','T3']:
 b=R/tid/'public'
 for n in ['BRIEF.md','API.md']:
  q=A/tid/n;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(b/n,q)
 p=b/'BRIEF.md';s=p.read_text()
 s=s.replace('It sends the current selected ID (or ordered-independent set) without clearing the draft.', 'It sends the current selected ID without clearing the draft.' if tid!='T3' else 'It sends the current selected ID set without clearing the draft.')
 s=s.replace('The component never confirms a reservation, field intervention or repair itself.',{'T1':'The component only requests a station place; it never confirms a reservation.','T2':'Acknowledgement assigns review responsibility; it never authorises field intervention.','T3':'Submission only requests a mechanic review; it never authorises repair or takes payment.'}[tid])
 s=s.replace('below the item label (and severity on T2)', 'below the item label and severity' if tid=='T2' else 'below the item label')
 old="Selecting a new incident while open moves the dossier to that incident (T2); the other components retain their global detail block. T1 and T3 global disclosure content is exactly model.guidance. T2 opening with no selection shows model.guidance in a full-width block immediately below the disclosure; with a selection it instead shows only that incident's detail inline below its selected card. Collapsed content and unselected incident details are intentionally hidden. Each item label, item detail, notice, subtitle and footer must remain fully readable."
 new=("Selecting a new incident while open moves the dossier to that incident. Opening with no selection shows model.guidance in a full-width block immediately below the disclosure; with a selection it instead shows only that incident's detail inline below its selected card. Collapsed guidance and unselected incident details are intentionally hidden." if tid=='T2' else "The global disclosure content is exactly model.guidance and stays in its global position when choices change. Its body is intentionally hidden when collapsed.")+" Every text item required visible under the current selection/disclosure rules, including labels, visible reasons/details, notice, subtitle and footer, must remain fully readable. Missing required text must not count as correct wrapping."
 assert old in s;s=s.replace(old,new)
 old='Also outside this selected ledger are T1 grid column count/breakpoint; T2 rail/severity/dossier placement and moving an open dossier on selection; T3 grouping and deselecting one item while preserving others; selected-background treatment, every unsampled canvas region and remaining typography hierarchy.'
 own={'T1':'grid column count/breakpoint','T2':'rail/severity/dossier placement and moving an open dossier on selection','T3':'grouping, estimate panel placement and deselecting one item while preserving others'}[tid]
 s=s.replace(old,'Also outside this selected ledger are '+own+'; selected-background treatment, every unsampled canvas region and remaining typography hierarchy.')
 p.write_text(s)
 p=b/'API.md';s=p.read_text();old='Model guidance is the exact global/no-selection disclosure body; selected T2 dossier uses the selected item detail. T2 label includes its time; uppercase severity is inside the same selection button, only its rail is external.'
 new="Model guidance is the exact no-selection disclosure body; with a selected incident its detail is the inline dossier body. Each incident label includes its time; uppercase severity is inside the same selection button, only its rail is external." if tid=='T2' else 'Model guidance is the exact global disclosure body; it is independent of which choices are selected.'
 assert old in s;s=s.replace(old,new)
 if tid!='T3':s=s.replace('Submission forwards the current selected IDs; bridge sorts set IDs only to normalize event order.','Submission forwards the one current selected ID without rewriting it.')
 p.write_text(s)
(R/'DOCUMENT-CLARIFICATIONS.json').write_text(json.dumps({'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Remove cross-task template prose, use per-task global/inline guidance, submission semantics and out-of-ledger topology. No rule/cell/action/expected value change.','preserved_originals':'attempts/02-template-docs'},indent=2)+'\n')
