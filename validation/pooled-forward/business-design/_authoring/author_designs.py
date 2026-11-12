#!/usr/bin/env python3
"""Independent preimplementation design authoring. Never production code or a native renderer.

This file contains held-out inputs. Give implementers ONLY T*/public/.
It materializes static typed design documents from the author's declarative state ledger.
"""
import copy
import hashlib
import json
from pathlib import Path
import textwrap
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[2]
OWNER = "Independent design/oracle author /root/v13_business_design"
START = "2026-11-10T16:23:29Z"

def rawsha(b): return hashlib.sha256(b).hexdigest()
def canonical(x): return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
def digest(x): return rawsha(canonical(x))
def write(p, x):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(x, indent=2, ensure_ascii=False)+"\n" if not isinstance(x,str) else x, encoding="utf-8")
def typed(v, unit=None):
    if unit is None:
        unit = "bool" if isinstance(v,bool) else "string" if isinstance(v,str) else "number"
    return {"value":v,"unit":unit}
def row(id, label, detail, **kw): return dict(id=id,label=label,detail=detail,**kw)
def fld(type, **kw): return dict(type=type,**kw)
def obj(properties, **kw): return dict(type="object",properties=properties,required=list(properties),additionalProperties=False,**kw)
S = fld("string",minLength=1,maxLength=500)
ID = fld("string",pattern="^[A-Za-z0-9-]{1,32}$")
B = fld("boolean")
N = fld("integer",minimum=0,maximum=100000000)
def array(item): return fld("array",items=item,minItems=1,maxItems=4)
def common_schema(extra):
    return obj(dict(entityId=ID,entityTitle=S,description=S,**extra))

TOKENS = {
    "colors":{
        "surface":typed("#FFFFFFFF","argb"),"canvas":typed("#FFFFF8F4","argb"),
        "ink":typed("#FF201B13","argb"),"secondaryInk":typed("#FF4F4539","argb"),
        "primary":typed("#FF805610","argb"),"onPrimary":typed("#FFFFFFFF","argb"),
        "selected":typed("#FFFFDDB3","argb"),"disabled":typed("#FFF3E6DA","argb"),
        "disabledPrimary":typed("#FFEDE0D4","argb"),"outline":typed("#FF817567","argb"),
        "summary":typed("#FFFFF1E5","argb")},
    "ios":{
        "titleSize":typed(22,"pt"),"titleWeight":typed(600),"bodySize":typed(16,"pt"),
        "buttonHeight":typed(48,"pt"),"panelInset":typed(16,"pt"),"sectionGap":typed(16,"pt"),
        "rowInset":typed(12,"pt"),"rowGap":typed(8,"pt"),"paintGutter":typed(24,"pt"),
        "panelRadius":typed(16,"pt"),"rowRadius":typed(8,"pt")},
    "android":{
        "titleSize":typed(22,"sp"),"titleWeight":typed(600),"bodySize":typed(16,"sp"),
        "bodyWeight":typed(400),"buttonHeight":typed(48,"dp"),"panelInset":typed(16,"dp"),
        "sectionGap":typed(16,"dp"),"rowInset":typed(12,"dp"),"rowGap":typed(8,"dp"),
        "paintGutter":typed(24,"dp"),"panelRadius":typed(16,"dp"),"rowRadius":typed(8,"dp")},
    "measurementSources":{
        "palette":"Stock Reply ui/theme/Color.kt, light palette, lines 23–57; iOS adopts these explicit component colors because AlertToast.AlertStyle accepts arbitrary SwiftUI Color.",
        "androidTypography":"Stock Reply ui/theme/Type.kt titleLarge (22sp,600,28sp line height) and bodyLarge (16sp,400,24sp line height).",
        "iosTypography":"Independent design choice: system font, fixed 22pt semibold title, 16pt regular body at approved Large Dynamic Type; visual intent only, no computed SwiftUI font claim.",
        "spacing":"Independent design choice, informed by AlertToast.banner VStack leading/spacing10/cornerRadius10 and ReplyEmailListItem Column padding20. This design explicitly fixes its own 16/12/8 rhythm and 16/8 radii, rather than claiming those are upstream defaults.",
        "shape":"Stock Reply Shapes.kt supports 8dp small and 16dp medium; iOS adopts explicit matching pt design values."}
}

def control(label, enabled=True, selected=False, detail=None, kind="option"):
    d=dict(label=label,enabled=enabled,kind=kind)
    if kind in ("option","toggle"): d["selected"]=selected
    if detail is not None: d["detail"]=detail
    return d

def snap(f, controls, summary, status, ready, submitted=False, preview=None):
    if submitted:
        for c in controls.values(): c["enabled"]=False
    return dict(entity=f["entityId"]+" · "+f["entityTitle"],description=f["description"],
                controls=controls,summary=summary,status=status,primary_enabled=ready and not submitted,
                submitted=submitted,preview=preview)

# A state entry explicitly fixes the caller input epoch and the business decision state.
# The helpers below perform only transparent design arithmetic; no implementation is consulted.
def t1(f, selected=(), packing=False, submitted=False):
    selected=set(selected)
    cs={"lot"+chr(65+i):control(x["label"],x["available"],x["id"] in selected,
        x["detail"]+f"\n{x['units']} units · "+("Available" if x["available"] else "Held: "+x["holdReason"])) for i,x in enumerate(f["lots"])}
    cs["packing"]=control("Packing list checked",True,packing,kind="toggle")
    n=len(selected); units=sum(x["units"] for x in f["lots"] if x["id"] in selected)
    ready=n>0 and packing
    status=(f"Release recorded for {n} lots." if submitted else "Select at least one available lot." if not n else "Check packing list to release." if not packing else f"Ready to release {n} lots.")
    return snap(f,cs,f"{n} lots selected · {units} units",status,ready,submitted)

def t2(f, mode=None, slot=None, notify=False, submitted=False):
    cs={"inPerson":control("Visit in person",True,mode=="in_person"),"video":control("Visit by video",f["allowVideo"],mode=="video")}
    for i,x in enumerate(f["slots"]):
        ok=mode is not None and x["available"] and mode in x["modes"]
        cs["slot"+chr(65+i)]=control(x["label"],ok,slot==x["id"],x["detail"]+"\n"+("Available" if x["available"] else "Full")+" · "+", ".join(x["modes"]))
    cs["notify"]=control("Notify the attendee",True,notify,kind="toggle")
    title=next((x["label"] for x in f["slots"] if x["id"]==slot),"No time selected")
    summary=("Video" if mode=="video" else "In person" if mode=="in_person" else "No visit mode")+" · "+title
    ready=mode is not None and slot is not None and notify
    status="Appointment move recorded." if submitted else "Choose a visit mode." if mode is None else "Choose an available time for this mode." if slot is None else "Confirm attendee notification." if not notify else "Ready to move this appointment."
    return snap(f,cs,summary,status,ready,submitted)

def money(n): return f"USD {n//100:,}.{n%100:02d}"
def t3(f, credit=False, method=None, authorize=False, submitted=False):
    applied=min(f["creditCents"],f["dueCents"]) if credit else 0
    remain=f["dueCents"]-applied
    cs={"credit":control("Apply account credit",f["creditCents"]>0,credit,kind="toggle")}
    for i,x in enumerate(f["methods"]):
        cs["method"+chr(65+i)]=control(x["label"],remain>0 and x["available"],method==x["id"],x["detail"]+"\n"+("Available" if x["available"] else "Unavailable: "+x["unavailableReason"]))
    cs["authorize"]=control("I authorize this settlement",True,authorize,kind="toggle")
    ready=(remain==0 or method is not None) and authorize
    status="Settlement recorded." if submitted else "Choose a payment method for the remaining amount." if remain>0 and method is None else "Authorize this settlement." if not authorize else "Ready to settle this invoice."
    return snap(f,cs,f"Credit {money(applied)} · Remaining {money(remain)}",status,ready,submitted)

def notice_preview(f,audience,workaround):
    a=next(x for x in f["audiences"] if x["id"]==audience)
    return "Subject: "+f["subject"]+"\nAudience: "+a["label"]+f" ({a['recipients']})\n"+f["message"]+("\nWorkaround: "+f["workaround"] if workaround else "")
def t4(f, audience=None, workaround=False, preview=False, approved=False, submitted=False):
    cs={"audience"+chr(65+i):control(x["label"],x["allowed"] and x["recipients"]>0,audience==x["id"],x["detail"]+f"\n{x['recipients']} recipients · "+("Allowed" if x["allowed"] else "Blocked: "+x["blockedReason"])) for i,x in enumerate(f["audiences"])}
    cs["workaround"]=control("Include troubleshooting steps",bool(f["workaround"]),workaround,kind="toggle")
    cs["previewAction"]=control("Preview notice",audience is not None,kind="action")
    cs["approve"]=control("Customer wording reviewed",preview,approved,kind="toggle")
    a=next((x for x in f["audiences"] if x["id"]==audience),None)
    summary=(a["label"]+f" · {a['recipients']} recipients" if a else "No audience selected")+" · Steps "+("included" if workaround else "omitted")
    ready=audience is not None and preview and approved
    status="Notice publication recorded." if submitted else "Choose an allowed audience." if not a else "Preview the current draft." if not preview else "Review the customer wording." if not approved else "Ready to publish this notice."
    return snap(f,cs,summary,status,ready,submitted,notice_preview(f,audience,workaround) if preview else None)

def t5(f, accessories=False, data=False, power=False, route=None, custody=False, submitted=False):
    base=accessories and (not f["dataBearing"] or data)
    cs={"accessories":control("Accessories counted",True,accessories,kind="toggle"),
        "data":control("Stored data erased",f["dataBearing"],data,kind="toggle"),
        "power":control("Power test passed",True,power,kind="toggle"),
        "restock":control("Return to stock",base and power and f["restockAllowed"],route=="restock",f["restockDetail"]),
        "repair":control("Send for repair",base and f["repairAllowed"],route=="repair",f["repairDetail"]),
        "recycle":control("Send for recycling",base and f["recycleAllowed"],route=="recycle",f["recycleDetail"]),
        "custody":control("Chain of custody checked",route is not None,custody,kind="toggle")}
    ready=route is not None and custody
    summary="Accessories "+("counted" if accessories else "unchecked")+" · Data "+("erased" if data else "pending" if f["dataBearing"] else "not required")+" · Power "+("passed" if power else "unchecked")+" · Route "+(route or "none")
    status="Return routing recorded." if submitted else "Complete accessories and data checks." if not base else "Choose an eligible disposition." if not route else "Confirm the chain of custody." if not custody else "Ready to route this return."
    return snap(f,cs,summary,status,ready,submitted)

def sequence(fixtures, states):
    """States: (name,input_epoch,action_or_None,snapshot,event_delta,stimulus_class)."""
    actions=[]; ledger=[]
    for name,epoch,action,expected,events,stimulus in states:
        si=None
        if action:
            si=len(actions)
            actions.append(action)
        ai=len(actions)
        full = action is None or action["type"]=="apply_next_fixture" or expected["primary_enabled"] or expected["submitted"] or expected["preview"] is not None
        observation = {"type":"sweep","state_id":name,"max_scrolls":18} if full else {"type":"checkpoint","state_id":name}
        actions.append(observation)
        s={"id":name,"input_index":epoch,"after_action":ai,"coverage":"full_content" if full else "targets"}
        if si is not None: s["stimulus_action"]=si
        ledger.append({"state":s,"expected":expected,"events":events,"stimulus":stimulus})
    assert len(actions)<=40
    return dict(fixtures=fixtures,actions=actions,ledger=ledger)
def tap(target, was_selected=None, event=None):
    pre=[dict(target=target,property="enabled",op="eq",expected=True)]
    if was_selected is not None: pre.append(dict(target=target,property="selected",op="eq",expected=was_selected))
    d=dict(type="tap",target=target,reveal=True,max_steps=18,preconditions=pre)
    if event: d["expect_callback"]=event
    return d
def upd(): return dict(type="apply_next_fixture")
def entry(name,epoch,action,expected,events=(),stimulus="tap"):
    return name,epoch,action,expected,list(events),"none" if action is None else "caller_update" if action["type"]=="apply_next_fixture" else stimulus

TASKS=[]

# T1: shipment release. Caller state replacement prunes held choices without losing a surviving lot.
p0=dict(entityId="OR-481",entityTitle="Museum installation freight",description="Release only the cartons that can travel together today. The receiving dock needs the complete conservation note, handling restrictions, and the destination team name before any freight leaves the depot.",lots=[
row("L-A","Release lot A","Framed exhibition panels for the east gallery. Keep the protective corner blocks fitted during loading.",units=7,available=True,holdReason=""),
row("L-B","Release lot B","Temperature-sensitive samples travel only after the cold-chain seal is approved.",units=4,available=False,holdReason="Cold-chain seal not approved"),
row("L-C","Release lot C","Reusable mounting brackets and the full printed installation schedule.",units=3,available=True,holdReason="")])
p1=copy.deepcopy(p0);p1["description"]="Receiving instructions changed: use the service entrance on Harbor Street and retain the loading record for the conservation team. Review the packing list again before releasing the remaining eligible lot.";p1["lots"][2].update(available=False,holdReason="Destination storage unavailable")
p2=copy.deepcopy(p0);p2.update(entityId="OR-482",entityTitle="Archive return shipment",description="This is a different order using the same choice labels. No selection, packing approval, or recorded release from the museum freight belongs to this return shipment.")
pub=sequence([p0,p1,p2],[entry("initial",0,None,t1(p0)),entry("one-lot",0,tap("lotC",False),t1(p0,["L-C"])),entry("two-lots",0,tap("lotA",False),t1(p0,["L-C","L-A"])),entry("ready",0,tap("packing",False),t1(p0,["L-C","L-A"],True)),entry("released",0,tap("primary",event="release|OR-481|L-A,L-C"),t1(p0,["L-A","L-C"],True,True),["release|OR-481|L-A,L-C"]),entry("same-order-pruned",1,upd(),t1(p1,["L-A"])),entry("ready-again",1,tap("packing",False),t1(p1,["L-A"],True)),entry("released-again",1,tap("primary",event="release|OR-481|L-A"),t1(p1,["L-A"],True,True),["release|OR-481|L-A"]),entry("changed-order",2,upd(),t1(p2))])
h0=copy.deepcopy(p0);h0.update(entityId="OR-936",entityTitle="Northern depot accessibility refit and replacement display materials",description="The northern depot is coordinating a multi-room accessibility refit with a receiving team that shares its loading bay with another institution. Preserve the full delivery note, including the instruction to call the facilities desk after arrival, leave the archival labels attached, and keep the last pallet upright while the rear lift is in use.")
h0["lots"]=[row("Z-90","Release northern lot","Very long conservation packaging instruction: this lot contains folded interpretive panels, replacement tactile labels, and a rigid display support that must remain flat until the destination crew has signed the receiving sheet.",units=17,available=True,holdReason=""),row("A-02","Release accessible fittings","A mixed lot of access rails and small fittings, each in a labeled reusable pouch. Do not separate the pouch list from its returnable crate.",units=8,available=True,holdReason=""),row("M-14","Release reserve stock","Reserve labels and mounting plates remain held while the receiving institution confirms whether its storage area is ready.",units=5,available=False,holdReason="Written receiving approval missing")]
h1=copy.deepcopy(h0);h1["lots"][0].update(available=False,holdReason="Protective transit cover failed inspection");h1["lots"][1]["units"]=12;h1["description"]+=" The available fittings now include four additional units; the release summary must use the replacement quantities."
h2=copy.deepcopy(h0);h2.update(entityId="OR-937",entityTitle="Separate southern depot return")
hid=sequence([h0,h1,h2],[entry("initial",0,None,t1(h0)),entry("first-lot",0,tap("lotA",False),t1(h0,["Z-90"])),entry("reverse-order-selection",0,tap("lotB",False),t1(h0,["Z-90","A-02"])),entry("ready",0,tap("packing",False),t1(h0,["Z-90","A-02"],True)),entry("released",0,tap("primary",event="release|OR-936|A-02,Z-90"),t1(h0,["Z-90","A-02"],True,True),["release|OR-936|A-02,Z-90"]),entry("same-order-pruned",1,upd(),t1(h1,["A-02"])),entry("ready-again",1,tap("packing",False),t1(h1,["A-02"],True)),entry("released-survivor",1,tap("primary",event="release|OR-936|A-02"),t1(h1,["A-02"],True,True),["release|OR-936|A-02"]),entry("changed-order",2,upd(),t1(h2))])
TASKS.append(dict(id="T1",name="Shipment release checklist",api="ShipmentReleasePanel",fixture="ShipmentReleaseFixture",child={"lots":"ReleaseLot"},primary="Release selected lots",public=pub,private=hid,
schema=common_schema(dict(lots=array(obj(dict(id=ID,label=S,detail=S,units=fld("integer",minimum=1,maximum=9999),available=B,holdReason=fld("string",maxLength=500)))))),
rules="""1. Every lot is displayed in caller order. An available lot toggles membership in a multi-selection. Held lots remain visible, disabled, and show their supplied hold reason; a held lot cannot be selected.
2. Initially no lots are selected and Packing list checked is off. Any selection change clears packing approval. At least one selected available lot and packing approval are required to release.
3. Summary is exactly '{N} lots selected · {U} units', where U sums current selected quantities. Status strings and punctuation are fixed by the public outcome ledger.
4. A successful release emits exactly one 'release|{entityId}|{comma-separated selected IDs in ascending Unicode lexical order}'. No other user action emits an event. A recorded release locks all controls and primary submission; duplicate submission is disabled.
5. On replacement with the same entityId, preserve only selected IDs that are still present and available, recompute quantities from replacement data, clear packing approval and recorded status, and emit no event. On a changed entityId, clear all selection, approval, and recorded status, even when labels or IDs are reused.
6. The release callback is a local request/receipt, not proof of a network shipment. No network, timer, random, async, or full application navigation is involved."""))

# T2: appointment compatibility and replacement.
p0=dict(entityId="BK-320",entityTitle="Community design review",description="Move this appointment only after checking both the visit mode and the offered time. The attendee needs enough notice to rearrange accessible transport or prepare a quiet place for the video review.",allowVideo=True,slots=[row("S-1","Choose Tuesday morning","Tuesday 10:30–11:15. The consultation includes time for an interpreter and review of the annotated floor plan.",available=True,modes=["in_person","video"]),row("S-2","Choose Wednesday afternoon","Wednesday 14:00–14:45 at the town hall annex.",available=False,modes=["in_person"]),row("S-3","Choose Thursday video","Thursday 16:00–16:45 with the remote design team.",available=True,modes=["video"])])
p1=copy.deepcopy(p0);p1["slots"][2]["available"]=False;p1["description"]="The Thursday remote slot filled while this offer was open. Keep a valid visit mode, clear an unavailable chosen time, and request a fresh attendee-notification approval for the replacement offer."
p2=copy.deepcopy(p0);p2.update(entityId="BK-321",entityTitle="Different attendee consultation",allowVideo=False,description="A separate booking uses the same time labels. Video visits are unavailable for this attendee. Start with no visit mode, no selected time, and no notification approval.")
pub=sequence([p0,p1,p2],[entry("initial",0,None,t2(p0)),entry("video-mode",0,tap("video",False),t2(p0,"video")),entry("time-selected",0,tap("slotC",False),t2(p0,"video","S-3")),entry("ready",0,tap("notify",False),t2(p0,"video","S-3",True)),entry("moved",0,tap("primary",event="reschedule|BK-320|video|S-3"),t2(p0,"video","S-3",True,True),["reschedule|BK-320|video|S-3"]),entry("same-booking-full-slot",1,upd(),t2(p1,"video")),entry("new-time",1,tap("slotA",False),t2(p1,"video","S-1")),entry("ready-again",1,tap("notify",False),t2(p1,"video","S-1",True)),entry("moved-again",1,tap("primary",event="reschedule|BK-320|video|S-1"),t2(p1,"video","S-1",True,True),["reschedule|BK-320|video|S-1"]),entry("changed-booking",2,upd(),t2(p2))])
h0=copy.deepcopy(p0);h0.update(entityId="BK-908",entityTitle="Extended assisted planning consultation with a support worker",allowVideo=False,description="The attendee is arranging a support worker, accessible transport, and an interpreter for a detailed planning consultation. Keep every scheduling instruction readable: the support worker must receive the same time as the attendee, the visit mode must match the chosen offer, and the detailed review cannot be shortened to fit the screen.");h0["slots"]=[row("Q-7","Choose assisted morning","Monday 09:15–10:30 in the accessible meeting room beyond the main reception. Allow the attendee time to unpack printed drawings and check the induction-loop setup.",available=True,modes=["in_person"]),row("Q-8","Choose assisted afternoon","Monday 13:30–14:45. The alternate room is currently fully booked.",available=False,modes=["in_person"]),row("Q-9","Choose remote review","Friday 15:15–16:30 with the same interpreter joining remotely.",available=True,modes=["video"])]
h1=copy.deepcopy(h0);h1["allowVideo"]=True;h1["slots"][0]["available"]=True;h1["description"]+=" The replacement now permits a video visit, but the Monday assisted morning remains in-person only."
h2=copy.deepcopy(h0);h2.update(entityId="BK-909",entityTitle="New booking with reused offer IDs")
hid=sequence([h0,h1,h2],[entry("initial",0,None,t2(h0)),entry("in-person",0,tap("inPerson",False),t2(h0,"in_person")),entry("time-selected",0,tap("slotA",False),t2(h0,"in_person","Q-7")),entry("ready",0,tap("notify",False),t2(h0,"in_person","Q-7",True)),entry("moved",0,tap("primary",event="reschedule|BK-908|in_person|Q-7"),t2(h0,"in_person","Q-7",True,True),["reschedule|BK-908|in_person|Q-7"]),entry("same-booking-preserved",1,upd(),t2(h1,"in_person","Q-7")),entry("mode-invalidates-time",1,tap("video",False),t2(h1,"video")),entry("remote-time",1,tap("slotC",False),t2(h1,"video","Q-9")),entry("ready-again",1,tap("notify",False),t2(h1,"video","Q-9",True)),entry("moved-again",1,tap("primary",event="reschedule|BK-908|video|Q-9"),t2(h1,"video","Q-9",True,True),["reschedule|BK-908|video|Q-9"]),entry("changed-booking",2,upd(),t2(h2))])
TASKS.append(dict(id="T2",name="Appointment rescheduling offer",api="AppointmentReschedulePanel",fixture="AppointmentRescheduleFixture",child={"slots":"RescheduleSlot"},primary="Move appointment",public=pub,private=hid,
schema=common_schema(dict(allowVideo=B,slots=array(obj(dict(id=ID,label=S,detail=S,available=B,modes=fld("array",items=fld("string",enum=["in_person","video"]),minItems=1,maxItems=2,uniqueItems=True)))))),
rules="""1. Begin with no visit mode, time, or attendee-notification approval. In person is available; Video is available only when allowVideo is true. Modes are single selection.
2. Times are displayed in caller order. A time is enabled only when it is available and supports the selected mode. Choosing another mode preserves the selected time only if that time remains available and compatible; otherwise it clears the time. Choosing a time selects exactly one. Any actual mode/time change clears notification approval.
3. Move appointment requires a selected available compatible time and Notify the attendee selected. The summary uses 'Video'/'In person'/'No visit mode', then ' · ', then the selected time label or 'No time selected'.
4. Successful submission emits exactly one 'reschedule|{entityId}|{in_person or video}|{slotId}', then locks the offer. All other decision taps emit zero events.
5. Same-entity replacement preserves an allowed chosen mode and a still available compatible chosen time; invalid choices clear. Notification approval and recorded status always clear. A changed entityId clears mode, time, approval, and recorded status, including reused slot IDs. Replacement emits no callback.
6. The component requests an appointment move locally; actual calendar mutation and app navigation are outside scope."""))

# T3: arithmetic and exclusive credit settlement route.
p0=dict(entityId="INV-640",entityTitle="Workshop materials invoice",description="Allocate the available account credit before choosing how to settle the remaining amount. This invoice includes reusable workshop supplies, documented delivery charges, and a separate reference for the accounts team. Amounts are integer US cents; never calculate using binary floating-point money.",dueCents=12500,creditCents=4500,methods=[row("bank","Pay by bank transfer","Use the verified operating account ending 0428. The payment reference must remain attached to this invoice.",available=True,unavailableReason=""),row("card","Pay by company card","The company card is temporarily unavailable for this supplier.",available=False,unavailableReason="Supplier card payments paused")])
p1=copy.deepcopy(p0);p1.update(dueCents=4000,description="A corrected invoice reduced the amount due below the available credit. Keep the choice to apply credit, clamp applied credit to the new amount due, and clear a now-unnecessary payment method. Authorization must be renewed.")
p2=copy.deepcopy(p0);p2.update(entityId="INV-641",entityTitle="Separate studio invoice",dueCents=9000,description="A different invoice uses the same saved payment methods. Start without applying credit, selecting a method, or carrying authorization from the previous invoice.")
pub=sequence([p0,p1,p2],[entry("initial",0,None,t3(p0)),entry("credit-applied",0,tap("credit",False),t3(p0,True)),entry("bank-selected",0,tap("methodA",False),t3(p0,True,"bank")),entry("ready",0,tap("authorize",False),t3(p0,True,"bank",True)),entry("settled",0,tap("primary",event="settle|INV-640|4500|8000|bank"),t3(p0,True,"bank",True,True),["settle|INV-640|4500|8000|bank"]),entry("same-invoice-credit-only",1,upd(),t3(p1,True)),entry("credit-only-ready",1,tap("authorize",False),t3(p1,True,None,True)),entry("credit-only-settled",1,tap("primary",event="settle|INV-640|4000|0|credit"),t3(p1,True,None,True,True),["settle|INV-640|4000|0|credit"]),entry("changed-invoice",2,upd(),t3(p2))])
h0=copy.deepcopy(p0);h0.update(entityId="INV-992",entityTitle="Specialist accessible exhibition equipment and consolidated delivery",description="The supplier consolidated several small equipment lines into one invoice. Preserve the complete remittance instructions and the statement that account credit must be capped at the amount actually due. A one-cent difference matters to the balance, and the authorized method must be the currently available one rather than the first method in the supplied list.",dueCents=10199,creditCents=3333);h0["methods"][0].update(available=False,unavailableReason="Bank verification pending");h0["methods"][1].update(available=True,unavailableReason="",detail="Use the purchasing card with the documented spending approval, and retain the unusually long supplier reference supplied with the invoice.")
h1=copy.deepcopy(h0);h1["creditCents"]=0;h1["methods"][0].update(available=True,unavailableReason="");h1["description"]+=" The replacement removes available credit, while the selected card remains valid."
h2=copy.deepcopy(h0);h2.update(entityId="INV-993",entityTitle="New invoice covered by excess credit",dueCents=1000,creditCents=5000)
hid=sequence([h0,h1,h2],[entry("initial",0,None,t3(h0)),entry("credit-applied",0,tap("credit",False),t3(h0,True)),entry("card-selected",0,tap("methodB",False),t3(h0,True,"card")),entry("ready",0,tap("authorize",False),t3(h0,True,"card",True)),entry("settled",0,tap("primary",event="settle|INV-992|3333|6866|card"),t3(h0,True,"card",True,True),["settle|INV-992|3333|6866|card"]),entry("same-invoice-credit-withdrawn",1,upd(),t3(h1,False,"card")),entry("ready-again",1,tap("authorize",False),t3(h1,False,"card",True)),entry("settled-again",1,tap("primary",event="settle|INV-992|0|10199|card"),t3(h1,False,"card",True,True),["settle|INV-992|0|10199|card"]),entry("changed-invoice",2,upd(),t3(h2)),entry("excess-credit-clamped",2,tap("credit",False),t3(h2,True)),entry("credit-only-ready",2,tap("authorize",False),t3(h2,True,None,True)),entry("credit-only-settled",2,tap("primary",event="settle|INV-993|1000|0|credit"),t3(h2,True,None,True,True),["settle|INV-993|1000|0|credit"])])
TASKS.append(dict(id="T3",name="Invoice credit-and-payment allocation",api="InvoiceSettlementPanel",fixture="InvoiceSettlementFixture",child={"methods":"SettlementMethod"},primary="Settle invoice",public=pub,private=hid,
schema=common_schema(dict(dueCents=fld("integer",minimum=1,maximum=100000000),creditCents=N,methods=array(obj(dict(id=ID,label=S,detail=S,available=B,unavailableReason=fld("string",maxLength=500)))))),
rules="""1. Start with credit off, no payment method selected, no authorization. Apply account credit is disabled when creditCents is zero. If on, applied credit = min(creditCents,dueCents); otherwise zero. Remaining = dueCents minus applied credit. Use integer cents and fixed USD formatting with two decimals and comma thousands separators.
2. Payment methods are single selection, enabled only when available and remaining is positive. When remaining becomes zero, clear any method selection and disable every method. A credit or method change clears authorization.
3. Settle invoice requires authorization and either remaining zero or an enabled selected method. Summary is 'Credit USD {applied} · Remaining USD {remaining}', as shown by exact public outcomes.
4. Submit emits exactly one 'settle|{entityId}|{applied integer cents}|{remaining integer cents}|{methodId}', using literal 'credit' when remaining is zero. Then lock all controls. Decision taps emit no events.
5. Same-entity replacement keeps credit on only if positive credit remains, keeps a chosen method only if still available and remaining stays positive, recomputes both amounts, and clears authorization/recorded state. A changed entityId resets credit, method, authorization, and recorded state. Replacement is silent.
6. This is an allocation request UI; payment processing, banking, taxation, and external accounting persistence are outside scope."""))

# T4: a draft/preview/approval workflow rather than immediate submit.
p0=dict(entityId="INC-214",entityTitle="Workshop booking interruption",description="Prepare a clear notice for the affected audience. A preview is a local draft, and publication requires a separate wording review after the current audience and troubleshooting choice are fixed.",subject="Workshop booking service is interrupted",message="Some workshop bookings cannot be confirmed. Existing confirmations remain valid. The support team is reviewing the queue and will publish another update through the agreed communication channel.",workaround="Keep the booking reference and contact the support desk before submitting the form again.",audiences=[row("customers","Notify affected customers","Customers with bookings awaiting confirmation need a direct explanation and a usable next step.",recipients=124,allowed=True,blockedReason=""),row("staff","Notify service staff","The operations team needs the same factual update for its customer conversations.",recipients=18,allowed=True,blockedReason=""),row("partners","Notify partner offices","Partner offices have no affected bookings in this incident.",recipients=0,allowed=True,blockedReason="")])
p1=copy.deepcopy(p0);p1["message"]="Booking confirmations are being restored in batches. Customers should keep their existing reference and wait for the confirmation message before making another booking.";p1["workaround"]="Ask the support desk to check the original booking reference before creating a replacement request.";p1["description"]="The caller replaced the incident wording. Preserve valid draft choices, but discard the old preview and wording review so that revised content is previewed and approved again."
p2=copy.deepcopy(p0);p2.update(entityId="INC-215",entityTitle="Separate ticketing incident",description="A separate incident starts with no audience, troubleshooting choice, preview, approval, or recorded publication.")
pub=sequence([p0,p1,p2],[entry("initial",0,None,t4(p0)),entry("audience-selected",0,tap("audienceA",False),t4(p0,"customers")),entry("steps-selected",0,tap("workaround",False),t4(p0,"customers",True)),entry("previewed",0,tap("previewAction"),t4(p0,"customers",True,True)),entry("ready",0,tap("approve",False),t4(p0,"customers",True,True,True)),entry("published",0,tap("primary",event="publish|INC-214|customers|124|steps:on"),t4(p0,"customers",True,True,True,True),["publish|INC-214|customers|124|steps:on"]),entry("same-incident-draft",1,upd(),t4(p1,"customers",True)),entry("repreviewed",1,tap("previewAction"),t4(p1,"customers",True,True)),entry("ready-again",1,tap("approve",False),t4(p1,"customers",True,True,True)),entry("republished",1,tap("primary",event="publish|INC-214|customers|124|steps:on"),t4(p1,"customers",True,True,True,True),["publish|INC-214|customers|124|steps:on"]),entry("changed-incident",2,upd(),t4(p2))])
h0=copy.deepcopy(p0);h0.update(entityId="INC-880",entityTitle="Regional membership and assisted-registration service interruption",description="Staff are supporting members who cannot complete assisted registration. The notice must retain the full explanation for people who saved a partially completed form, including the distinction between an unconfirmed request and a confirmed membership, and must not promise a recovery time that has not been provided by the incident owner.",subject="Assisted registration requests may need a staff review before confirmation",message="Requests saved during the interruption remain in the review queue. A saved request does not yet establish a confirmed membership. Staff should locate the original reference, explain the current status in plain language, and avoid asking a member to enter the same details repeatedly while the regional team checks the queue.",workaround="");h0["audiences"][0].update(allowed=False,blockedReason="Direct customer wording has not been approved");h0["audiences"][1].update(recipients=47,detail="Regional service staff, assisted-registration volunteers, and the named support coordinator need the full operational explanation for their next member conversation.")
h1=copy.deepcopy(h0);h1["audiences"][0].update(allowed=True,blockedReason="",recipients=203);h1["audiences"][1].update(allowed=False,blockedReason="Staff escalation moved to a separate internal bulletin");h1["workaround"]="Ask the member for the saved request reference, read back the contact details already on that request, and send any correction to the support coordinator. Do not create a duplicate membership request."
h2=copy.deepcopy(h0);h2.update(entityId="INC-881",entityTitle="Different service incident with reused audience IDs")
hid=sequence([h0,h1,h2],[entry("initial",0,None,t4(h0)),entry("staff-selected",0,tap("audienceB",False),t4(h0,"staff")),entry("previewed",0,tap("previewAction"),t4(h0,"staff",False,True)),entry("ready",0,tap("approve",False),t4(h0,"staff",False,True,True)),entry("published",0,tap("primary",event="publish|INC-880|staff|47|steps:off"),t4(h0,"staff",False,True,True,True),["publish|INC-880|staff|47|steps:off"]),entry("same-incident-blocked-audience",1,upd(),t4(h1)),entry("customers-selected",1,tap("audienceA",False),t4(h1,"customers")),entry("steps-selected",1,tap("workaround",False),t4(h1,"customers",True)),entry("repreviewed",1,tap("previewAction"),t4(h1,"customers",True,True)),entry("ready-again",1,tap("approve",False),t4(h1,"customers",True,True,True)),entry("republished",1,tap("primary",event="publish|INC-880|customers|203|steps:on"),t4(h1,"customers",True,True,True,True),["publish|INC-880|customers|203|steps:on"]),entry("changed-incident",2,upd(),t4(h2))])
TASKS.append(dict(id="T4",name="Service outage notice composer",api="OutageNoticePanel",fixture="OutageNoticeFixture",child={"audiences":"NoticeAudience"},primary="Publish notice",public=pub,private=hid,
schema=common_schema(dict(subject=S,message=S,workaround=fld("string",maxLength=500),audiences=array(obj(dict(id=ID,label=S,detail=S,recipients=N,allowed=B,blockedReason=fld("string",maxLength=500)))))),
rules="""1. Begin with no audience, troubleshooting off, no preview, no wording review. Audiences are single selection and enabled only when allowed and recipients > 0. Show zero-recipient and blocked audiences; keep their descriptive reasons readable.
2. Include troubleshooting steps is enabled only for a nonempty workaround. An actual audience or troubleshooting change invalidates the preview and wording review. Preview notice is enabled when an allowed audience is selected and creates the exact deterministic preview: 'Subject: {subject}\\nAudience: {audience label} ({recipients})\\n{message}', appending '\\nWorkaround: {workaround}' only when troubleshooting is on. Previewing again clears wording review.
3. Before a preview exists, its content is absent and Customer wording reviewed is disabled/off. Publish notice requires a current preview and wording review. The preview remains visible after publication.
4. Publish emits exactly one 'publish|{entityId}|{audienceId}|{current recipient integer}|steps:{on or off}', then locks all controls. Preview and decision actions emit zero events. This is a local publication request, not an actual outbound message.
5. Same-entity replacement preserves the audience only if still allowed with positive recipients, preserves troubleshooting only if a nonempty workaround remains, and always clears preview, review, and recorded state. Changed entityId clears every decision. Replacement emits nothing.
6. Summary is '{selected audience label} · {count} recipients' or 'No audience selected', followed by ' · Steps included'/' · Steps omitted'. Exact status/preview content is part of the public outcomes; no recovery time, delivery channel, or other text is invented."""))

# T5: inspection-dependent disposition, including selection invalidation.
p0=dict(entityId="RET-517",entityTitle="Portable interpretation tablet return",description="Record the physical checks before routing this returned tablet. A return can be offered for stock only after its power test, accessories count, and required data erasure are complete. Keep the original complaint and the next handling instruction visible for the receiving team.",dataBearing=True,restockAllowed=True,repairAllowed=True,recycleAllowed=False,restockDetail="Restock only after the tablet passes the power test and its data and accessories checks are complete.",repairDetail="A technician can inspect the intermittent charging fault after safe intake checks.",recycleDetail="Recycling is unavailable while this model remains in the repair program.")
p1=copy.deepcopy(p0);p1.update(restockAllowed=False,description="The model has been removed from the restock program. Keep completed intake checks for this same return, clear a now-ineligible disposition, and request a fresh chain-of-custody approval.")
p2=copy.deepcopy(p0);p2.update(entityId="RET-518",entityTitle="Non-data-bearing audio stand return",dataBearing=False,description="A separate non-data-bearing item uses the same disposition labels. Begin with every intake check and disposition unset. Stored data erased is disabled and off because this item has no stored data.")
pub=sequence([p0,p1,p2],[entry("initial",0,None,t5(p0)),entry("accessories",0,tap("accessories",False),t5(p0,True)),entry("data-erased",0,tap("data",False),t5(p0,True,True)),entry("power-passed",0,tap("power",False),t5(p0,True,True,True)),entry("restock-selected",0,tap("restock",False),t5(p0,True,True,True,"restock")),entry("ready",0,tap("custody",False),t5(p0,True,True,True,"restock",True)),entry("routed",0,tap("primary",event="route-return|RET-517|restock|power:pass|data:erased|accessories:counted"),t5(p0,True,True,True,"restock",True,True),["route-return|RET-517|restock|power:pass|data:erased|accessories:counted"]),entry("same-return-ineligible",1,upd(),t5(p1,True,True,True)),entry("repair-selected",1,tap("repair",False),t5(p1,True,True,True,"repair")),entry("ready-again",1,tap("custody",False),t5(p1,True,True,True,"repair",True)),entry("routed-again",1,tap("primary",event="route-return|RET-517|repair|power:pass|data:erased|accessories:counted"),t5(p1,True,True,True,"repair",True,True),["route-return|RET-517|repair|power:pass|data:erased|accessories:counted"]),entry("changed-return",2,upd(),t5(p2))])
h0=copy.deepcopy(p0);h0.update(entityId="RET-903",entityTitle="Loaned accessible reading device and specialist charging accessories",description="The loaned reading device was returned with an intermittent power complaint and a bag of specialist charging accessories. The receiving team must retain the full intake note, including the requirement to erase locally stored reading material, count the separately packaged cable adaptors, and document the next custodian before any onward routing occurs.",restockDetail="Return to stock is conditional on a successful power test as well as the completed intake checks. A later change to the power result must invalidate this route immediately.",repairDetail="The specialist repair team can accept a device without a passed power test once the accessories and data checks are complete.",recycleAllowed=True,recycleDetail="Approved material recovery is available after the same safe intake checks, with the complete chain-of-custody record attached.")
h1=copy.deepcopy(h0);h1.update(dataBearing=False,description="The caller corrected the record: this same asset uses a removable storage module that has already been retained separately, so the returned assembly is not data-bearing. Preserve other valid checks and a valid repair route, force the data checkbox off, and clear custody approval.")
h2=copy.deepcopy(h0);h2.update(entityId="RET-904",entityTitle="Different return with reused route choices")
hid=sequence([h0,h1,h2],[entry("initial",0,None,t5(h0)),entry("accessories",0,tap("accessories",False),t5(h0,True)),entry("data-erased",0,tap("data",False),t5(h0,True,True)),entry("power-passed",0,tap("power",False),t5(h0,True,True,True)),entry("restock-selected",0,tap("restock",False),t5(h0,True,True,True,"restock")),entry("power-revoked-clears-route",0,tap("power",True),t5(h0,True,True,False)),entry("repair-selected",0,tap("repair",False),t5(h0,True,True,False,"repair")),entry("ready",0,tap("custody",False),t5(h0,True,True,False,"repair",True)),entry("routed",0,tap("primary",event="route-return|RET-903|repair|power:unchecked|data:erased|accessories:counted"),t5(h0,True,True,False,"repair",True,True),["route-return|RET-903|repair|power:unchecked|data:erased|accessories:counted"]),entry("same-return-no-data",1,upd(),t5(h1,True,False,False,"repair")),entry("ready-again",1,tap("custody",False),t5(h1,True,False,False,"repair",True)),entry("routed-again",1,tap("primary",event="route-return|RET-903|repair|power:unchecked|data:not-required|accessories:counted"),t5(h1,True,False,False,"repair",True,True),["route-return|RET-903|repair|power:unchecked|data:not-required|accessories:counted"]),entry("changed-return",2,upd(),t5(h2))])
TASKS.append(dict(id="T5",name="Equipment return disposition",api="EquipmentReturnPanel",fixture="EquipmentReturnFixture",child={},primary="Record disposition",public=pub,private=hid,
schema=common_schema(dict(dataBearing=B,restockAllowed=B,repairAllowed=B,recycleAllowed=B,restockDetail=S,repairDetail=S,recycleDetail=S)),
rules="""1. Start with Accessories counted, Stored data erased, Power test passed, and Chain of custody checked off; no disposition. Stored data erased is disabled and forced off when dataBearing is false. Other inspection checks remain actual user decisions, not fixture-driven automatic approvals.
2. Base intake eligibility requires Accessories counted and, for data-bearing items, Stored data erased. Return to stock additionally requires Power test passed and restockAllowed. Send for repair requires repairAllowed plus base eligibility; Send for recycling requires recycleAllowed plus base eligibility. Show every route even when disabled.
3. Routes are single selection. Any inspection change clears chain-of-custody approval and clears the selected route only when that route becomes ineligible. A route change clears custody approval. Custody approval is enabled only with a selected eligible route. Record disposition requires that route and custody approval.
4. Submit emits exactly one 'route-return|{entityId}|{restock/repair/recycle}|power:{pass/unchecked}|data:{erased/not-required}|accessories:counted', then locks all controls. All other taps emit nothing. The published eligibility rules ensure a data-bearing submit always uses erased.
5. Same-entity replacement preserves accessories and power checks, preserves data-erased only while the replacement is data-bearing, preserves a route only if still eligible, and clears custody approval and recorded state. Changed entityId clears all checks, route, approval, and recorded status, including reused labels. Replacement emits nothing.
6. The summary displays all four facts in this order: 'Accessories counted/unchecked · Data erased/pending/not required · Power passed/unchecked · Route {restock/repair/recycle/none}'. This is an intake routing request, not proof of actual erasure, repair, or external inventory mutation."""))

