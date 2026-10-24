#!/usr/bin/env python3
"""Independent prospective design authoring. Writes only the assigned design root.

This file contains private fixture values and is not part of either public bundle.
No native command, production source read, or implementation is performed here.
"""
from pathlib import Path
import sys, json, hashlib, copy, traceback, datetime, textwrap, html, shutil
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT.parent / 'candidate-v9'
sys.path.insert(0, str(SKILL / 'scripts'))
import design_contract as dc
import requirement_routes as rr
import execution_plan as ep
import review_contract as rc
from PIL import Image, ImageDraw, ImageFont

def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def val(v, unit): return {'value':v, 'unit':unit}
def ref(pointer): return {'source':'reference','pointer':pointer}
def cell(pointer): return {'ios':ref(pointer),'android':ref(pointer)}
STATES = ['overview','permitted','requested','replaced']
COLORS = {'canvas':'#FFF4F6FA','surface':'#FFFFFFFF','ink':'#FF172B4D',
          'waiting':'#FFE9EFF8','ready':'#FFDDF4EC','requested':'#FFDDEBFF',
          'blocked':'#FFFFE5B3','enabled':'#FF2463C5','disabled':'#FFD8DEE8'}
TERMS = {
 'T1': {
  'component':'ColdStorageTransferPanel','model':'ColdStorageTransfer','row':'TransferHandlingNote',
  'prefix':'transfer','domain':'Cold-storage transfer release',
  'ios_path':'Sources/AlertToast/ColdStorageTransferPanel.swift',
  'android_path':'app/src/main/java/com/example/reply/ui/components/ColdStorageTransferPanel.kt',
  'disclosure_off':'Review handling','disclosure_on':'Hide handling',
  'choice_off':'Confirm seal checked','choice_on':'Seal check confirmed',
  'primary':'Release transfer','primary_done':'Requested',
  'section_name':'Handling notes',
  'public_titles':['Transfer to North research freezer','Evening transfer for the coastal laboratory'],
  'public_updated':['Quarantine transfer to West archive','Coolant hold for the coastal laboratory'],
  'private_title':'Transfer for the high-altitude seed bank',
  'private_updated':'Restricted transfer for the island genomics store',
  'notes':[
   ('Check the outer seal', 'Read the seal number against the paper manifest before moving the crate. If the security strip is torn, keep the crate in its present freezer and contact the receiving technician for a replacement transfer record.'),
   ('Prepare the receiving shelf', 'Clear the assigned shelf and place the receiving tray within easy reach. Keep unrelated specimens in their labeled compartments so that the new crate can be set down without moving other active research material.'),
   ('Keep the lid closed', 'Carry the crate with its insulated lid firmly latched. Open it only inside the receiving cold room, after the technician confirms the destination label and has the temperature logger ready for the arrival reading.'),
   ('Use the protected route', 'Take the marked indoor corridor between the loading room and the cold store. Avoid leaving the crate beside an exterior doorway while waiting for a lift; ask a colleague to hold the internal door instead.'),
   ('Record the logger reading', 'At the receiving shelf, read the logger without removing its probe from the packing sleeve. Write the displayed value and the time on the manifest, then return the logger to its original position inside the crate.'),
   ('Separate a suspect container', 'If one container has a loose cap or a damaged label, keep that container in the secondary tray. Do not relabel it from memory. Record its position and ask the receiving technician to confirm the sample identity.'),
   ('Confirm the handoff', 'Give the receiving technician the manifest and wait for a verbal acknowledgement of the crate identifier. The app records a release request only; the receiving team still completes its normal physical inventory and handoff procedure.'),
   ('Store the paperwork', 'Leave the signed manifest in the cold-room document sleeve after the handoff is complete. Keep the crate identifier visible at the front of the shelf so the next shift can find both the specimens and their record.')
  ],
  'hidden_notes':[
   ('Prepare the remote inventory', 'Match the seed-lot labels to the receiving inventory before leaving the staging room. The island store uses separate racks for active conservation material and long-term reserve lots; verify the rack designation with the receiving keeper.'),
   ('Check the padded carrier', 'Inspect the carrier corners and the insulated insert while the lid remains closed. Replace a wet or torn outer sleeve before departure, and keep the original transit label attached until the receiving keeper has accepted the carrier.'),
   ('Protect the accession tags', 'Keep the paper accession tags inside their clear sleeves throughout the transfer. Condensation can soften an exposed tag quickly, so use the printed lot number rather than handwriting a replacement from a partly visible label.'),
   ('Coordinate the doorway', 'Arrange for a second staff member to open the cold-room door before the carrier arrives. Set the carrier on the designated bench instead of on the floor while the receiving keeper confirms the available shelf space.'),
   ('Verify the receiving tray', 'Use the tray reserved for the listed accession group and check that its divider labels remain legible. A spare tray must be entered in the inventory before any individual containers are moved out of the carrier.'),
   ('Note an unusual reading', 'If the logger shows an unusual reading, leave the probe and packing in place. Record what the display actually shows and contact the conservation lead before deciding whether the lot can join the normal reserve inventory.'),
   ('Complete the keeper handoff', 'Wait for the keeper to repeat the carrier identifier and the destination rack. This request records the sender decision, while the receiving team independently signs its inventory record after checking the physical contents of the carrier.'),
   ('Leave the transfer record', 'Place the completed transfer record in the receiving rack sleeve with the carrier identifier facing outward. Let the next shift know where the reserve lot was placed so that its first scheduled inspection can proceed without searching.')
  ]
 },
 'T2': {
  'component':'OfflineAudioTourPanel','model':'OfflineAudioTour','row':'AudioTourChapter',
  'prefix':'audio','domain':'Museum audio-tour offline download',
  'ios_path':'Sources/AlertToast/OfflineAudioTourPanel.swift',
  'android_path':'app/src/main/java/com/example/reply/ui/components/OfflineAudioTourPanel.kt',
  'disclosure_off':'Review chapters','disclosure_on':'Hide chapters',
  'choice_off':'Wi-Fi only','choice_on':'Wi-Fi only',
  'primary':'Get audio','primary_done':'Requested',
  'section_name':'Chapters',
  'public_titles':['Harbor museum: voices of the working port','The sound of craft: a walk through the textile galleries'],
  'public_updated':['The night observatory collection','Winter gardens and the glasshouse collection'],
  'private_title':'River instruments: stories from the navigation hall',
  'private_updated':'Stone and shadow: the sculpture courtyard',
  'notes':[
   ('At the harbor gate', 'Begin beside the old harbor gate and listen for the bell that once announced a vessel arriving at the quay. The introduction describes how workers coordinated a busy waterfront before radios became part of everyday port life.'),
   ('The rope makers', 'Walk toward the long rope-making bench and compare the tools displayed above it. This chapter follows a small team preparing a heavy line, with pauses that let you examine the fibers and the worn wooden handles nearby.'),
   ('A shipwright workshop', 'Stand beside the half-built hull and look along the curve of its ribs. The shipwright describes choosing timber, checking a joint, and teaching an apprentice to notice a small gap before the outer planks were fitted.'),
   ('Work at the fish market', 'The market gallery brings together sellers, carriers, and the people who repaired baskets at the end of the day. Listen beside the weighing table, then look for the chalk price board before continuing into the next room.'),
   ('Signals across the water', 'At the signal cabinet, the narrator explains why a clear message mattered in poor weather. Short examples describe the flags and lamps without requiring you to identify every symbol, so you can listen while examining the original equipment.'),
   ('The engine room', 'Pause near the engine model and follow the route from the boiler to the propeller shaft. A mechanic recalls the rhythm of routine checks and explains how the crew recognized a change in the sound of a working engine.'),
   ('Letters from the voyage', 'The writing desk holds copies of letters sent home during long trips. This chapter reads brief passages about ordinary meals, changing weather, and missing family, with quiet intervals that give you time to inspect the handwriting on display.'),
   ('A changing waterfront', 'Finish at the large window overlooking the present harbor. The final voices discuss new jobs and familiar landmarks, inviting you to compare the view outside with the historical photographs on the adjacent wall before you leave the gallery.')
  ],
  'hidden_notes':[
   ('A river pilots desk', 'Start at the pilots desk and examine the folded river chart beneath its glass cover. The opening voice explains how crews planned a passage around shifting sandbanks and why a familiar route still needed careful attention on every journey.'),
   ('Measuring the current', 'Beside the current meter, listen to a surveyor describe taking a reading from a small boat. The account connects the instrument to a practical decision about when to leave the landing, without asking you to perform a calculation yourself.'),
   ('The bridge watch', 'At the bridge model, follow the lookout route from one side of the deck to the other. A retired crew member recalls watching for a low marker while another person kept track of the approaching bend in the river.'),
   ('Soundings in shallow water', 'The sounding line display introduces a job that required patience and clear spoken signals. Listen while looking at the marked lengths on the rope, then compare the working line with the later mechanical instrument in the neighboring case.'),
   ('Keeping a voyage log', 'Pause at the open logbook and notice the short entries written beside each date. This chapter explains how observations about weather, repairs, and waiting at a landing could help the next crew prepare for the same stretch of river.'),
   ('Repairing a navigation lamp', 'The lamp bench shows the small parts a keeper carried when a light failed. The narrator follows one routine repair and describes checking the beam from the water, where an apparently bright lamp might still be difficult to recognize.'),
   ('Voices at the crossing', 'Listen near the ferry photograph to hear three short memories of the crossing. Each speaker describes a different task, and the pauses between their accounts leave time to compare the landing shown in the image with the route map.'),
   ('Reading the river today', 'End beside the modern river map and find the old crossing on its edge. The closing chapter describes which habits of observation remain useful, even when the crew also carries electronic charts and receives regular messages from the shore station.')
  ]
 }
}

def fixtures_for(task, case):
    t=TERMS[task]; hidden=case=='H1'; p2=case=='P2'
    index=1 if p2 else 0
    title=t['private_title'] if hidden else t['public_titles'][index]
    title2=t['private_updated'] if hidden else t['public_updated'][index]
    rows=t['hidden_notes'] if hidden else t['notes']
    if p2 and task=='T1':
        rows=[
          ('Check the coastal manifest','Match the seal number to the coastal manifest before moving the crate. Keep a damaged seal in the current freezer and call the receiving technician.'),
          ('Prepare the shelf','Clear the coastal receiving shelf and put its tray within reach. Leave other specimens in their labeled compartments while the new crate is being placed.'),
          ('Keep the lid closed','Carry the crate with its insulated lid latched. Open it inside the receiving cold room after the technician checks the destination and prepares the logger.'),
          ('Follow the indoor route','Use the marked indoor corridor. Ask a colleague to hold the internal door so the crate does not wait beside an exterior entrance.'),
          ('Read the logger','Read the logger with its probe still in the packing sleeve. Record the displayed temperature and arrival time on the manifest before replacing the lid.'),
          ('Separate suspect containers','Put a container with a loose cap or damaged label in the secondary tray. Ask the technician to verify its identity before writing a replacement label.'),
          ('Confirm the handoff','Wait for the technician to acknowledge the crate identifier. This app records the release request; the receiving team completes its separate physical inventory and signature.'),
          ('Leave the paperwork','Place the signed manifest in the cold-room sleeve. Keep the crate identifier facing the aisle so the next shift can find the specimens and their record.')]
    elif p2 and task=='T2':
        rows=[
          ('The first spinning wheel','Begin beside the spinning wheel and examine the worn treadle. A weaver describes learning to keep the thread steady while watching the changing bundle of fiber.'),
          ('Choosing a fiber','At the fiber cabinet, compare the wool and flax samples. This chapter explains how their different textures influenced the cloth a workshop could make.'),
          ('Colors from the garden','Listen beside the dye pots to learn how plants produced familiar colors. Look for the small sample cards that record each workshop recipe.'),
          ('Setting the loom','Stand near the large loom and follow the line of its threads. The narrator describes preparing a pattern before the first row of cloth was woven.'),
          ('A pattern shared','The pattern books preserve ideas passed between makers. Pause at the open page while a designer explains adapting a familiar motif for a new commission.'),
          ('Mending a favorite coat','At the mending table, listen to a repairer describe choosing a patch. The nearby coat shows how careful work can preserve a garment for another generation.'),
          ('Cloth at the market','The market display follows a finished bolt from workshop to customer. Short memories describe measuring, bargaining, and choosing fabric for a special family occasion.'),
          ('Makers working today','Finish beside the contemporary textiles. The closing voices describe the tools they still use and invite you to compare their work with the older cloth nearby.')]
    records=[{'id':f'n{i+1}','title':h,'body':b} for i,(h,b) in enumerate(rows)]
    if task=='T1':
        identity=('XFR-9074' if hidden else 'XFR-4821' if p2 else 'XFR-2618')
        new_id=('XFR-9306' if hidden else 'XFR-5003' if p2 else 'XFR-2740')
        initial={'id':identity,'title':title,'destination':('Reserve rack C / bay 7' if hidden else 'Coastal rack F / bay 2' if p2 else 'North rack B / bay 4'),
                 'temperatureRange':('-24 to -18 °C' if hidden else '-22 to -16 °C' if p2 else '-20 to -14 °C'),
                 'sealIntact':True,'coolantReady':True,'notes':records}
        updated={'id':new_id,'title':title2,'destination':('Island rack H / bay 9' if hidden else 'Coastal hold J / bay 6' if p2 else 'West quarantine Q / bay 3'),
                 'temperatureRange':('-26 to -20 °C' if hidden else '-24 to -18 °C' if p2 else '-18 to -12 °C'),
                 'sealIntact':False if hidden or not p2 else True,'coolantReady':False if hidden or p2 else True,
                 'notes':[dict(x, id='r'+x['id']) for x in records]}
    else:
        identity=('TOUR-745' if hidden else 'TOUR-516' if p2 else 'TOUR-203')
        new_id=('TOUR-816' if hidden else 'TOUR-604' if p2 else 'TOUR-311')
        initial={'id':identity,'title':title,'language':('English · river collection' if hidden else 'English · textile collection' if p2 else 'English · harbor collection'),
                 'downloadSizeMB':(284 if hidden else 196 if p2 else 128),'availableMB':(680 if hidden else 440 if p2 else 320),
                 'meteredConnection':True,'chapters':records}
        updated={'id':new_id,'title':title2,'language':('English · courtyard collection' if hidden else 'English · garden collection' if p2 else 'English · sky collection'),
                 'downloadSizeMB':(372 if hidden else 246 if p2 else 214),'availableMB':(148 if hidden else 510 if p2 else 96),
                 'meteredConnection':True if p2 else False,'chapters':[dict(x,id='r'+x['id']) for x in records]}
    return {'initial':initial,'updates':[updated],'width':280 if p2 else 400,'viewportHeight':600,
            'theme':'light','dynamic_type':'xxxLarge' if p2 else 'large','fontScale':1.3 if p2 else 1.0,
            'direction':'rtl' if hidden else 'ltr','canvas_color':'#F4F6FA','max_scrolls':18,
            'state_capture':True,'required_identifiers':[t['prefix']+'.'+x for x in ['canvas','surface','inkMark','title','subtitle','status','disclosure','choice','primary']]}

def bridge_swift(task):
    if task=='T1':
        return '''import SwiftUI
import AlertToast

enum ObserverBridge {
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {
        let notes = (fixture["notes"] as! [[String: Any]]).map {
            TransferHandlingNote(id: $0["id"] as! String, title: $0["title"] as! String, body: $0["body"] as! String)
        }
        let transfer = ColdStorageTransfer(id: fixture["id"] as! String,
            title: fixture["title"] as! String, destination: fixture["destination"] as! String,
            temperatureRange: fixture["temperatureRange"] as! String,
            sealIntact: fixture["sealIntact"] as! Bool, coolantReady: fixture["coolantReady"] as! Bool, notes: notes)
        return AnyView(ColdStorageTransferPanel(transfer: transfer,
            onAcknowledgementChange: { checked in onEvent("transfer.ack:\\(transfer.id):\\(checked ? "true" : "false")") },
            onRelease: { id in onEvent("transfer.release:\\(id)") }))
    }
}
'''
    return '''import SwiftUI
import AlertToast

enum ObserverBridge {
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {
        let chapters = (fixture["chapters"] as! [[String: Any]]).map {
            AudioTourChapter(id: $0["id"] as! String, title: $0["title"] as! String, body: $0["body"] as! String)
        }
        let tour = OfflineAudioTour(id: fixture["id"] as! String,
            title: fixture["title"] as! String, language: fixture["language"] as! String,
            downloadSizeMB: fixture["downloadSizeMB"] as! Int, availableMB: fixture["availableMB"] as! Int,
            meteredConnection: fixture["meteredConnection"] as! Bool, chapters: chapters)
        return AnyView(OfflineAudioTourPanel(tour: tour,
            onWifiOnlyChange: { wifiOnly in onEvent("audio.wifiOnly:\\(tour.id):\\(wifiOnly ? "true" : "false")") },
            onDownload: { id, wifiOnly in onEvent("audio.download:\\(id):\\(wifiOnly ? "wifi" : "mobile")") }))
    }
}
'''

def bridge_kotlin(task):
    t=TERMS[task]
    common='''package org.nativeobserver

import androidx.compose.runtime.Composable
import kotlinx.serialization.json.*
'''
    common+='\n'.join('import com.example.reply.ui.components.'+name for name in [t['row'],t['model'],t['component']])+'\n\n'
    if task=='T1':
        return common+'''object ObserverBridge {
    @Composable
    fun Content(fixture: JsonObject, onEvent: (String) -> Unit) {
        val transfer = ColdStorageTransfer(
            id = fixture.getValue("id").jsonPrimitive.content,
            title = fixture.getValue("title").jsonPrimitive.content,
            destination = fixture.getValue("destination").jsonPrimitive.content,
            temperatureRange = fixture.getValue("temperatureRange").jsonPrimitive.content,
            sealIntact = fixture.getValue("sealIntact").jsonPrimitive.boolean,
            coolantReady = fixture.getValue("coolantReady").jsonPrimitive.boolean,
            notes = fixture.getValue("notes").jsonArray.map { value ->
                val row = value.jsonObject
                TransferHandlingNote(row.getValue("id").jsonPrimitive.content,
                    row.getValue("title").jsonPrimitive.content, row.getValue("body").jsonPrimitive.content)
            })
        ColdStorageTransferPanel(transfer = transfer,
            onAcknowledgementChange = { checked -> onEvent("transfer.ack:${transfer.id}:$checked") },
            onRelease = { id -> onEvent("transfer.release:$id") })
    }
}
'''
    return common+'''object ObserverBridge {
    @Composable
    fun Content(fixture: JsonObject, onEvent: (String) -> Unit) {
        val tour = OfflineAudioTour(
            id = fixture.getValue("id").jsonPrimitive.content,
            title = fixture.getValue("title").jsonPrimitive.content,
            language = fixture.getValue("language").jsonPrimitive.content,
            downloadSizeMB = fixture.getValue("downloadSizeMB").jsonPrimitive.int,
            availableMB = fixture.getValue("availableMB").jsonPrimitive.int,
            meteredConnection = fixture.getValue("meteredConnection").jsonPrimitive.boolean,
            chapters = fixture.getValue("chapters").jsonArray.map { value ->
                val row = value.jsonObject
                AudioTourChapter(row.getValue("id").jsonPrimitive.content,
                    row.getValue("title").jsonPrimitive.content, row.getValue("body").jsonPrimitive.content)
            })
        OfflineAudioTourPanel(tour = tour,
            onWifiOnlyChange = { wifiOnly -> onEvent("audio.wifiOnly:${tour.id}:$wifiOnly") },
            onDownload = { id, wifiOnly -> onEvent("audio.download:$id:${if (wifiOnly) "wifi" else "mobile"}") })
    }
}
'''

def api(task):
    t=TERMS[task]
    if task=='T1':
        model='''public struct TransferHandlingNote: Equatable, Identifiable {
    public let id: String
    public let title: String
    public let body: String
    public init(id: String, title: String, body: String)
}
public struct ColdStorageTransfer: Equatable, Identifiable {
    public let id: String
    public let title: String
    public let destination: String
    public let temperatureRange: String
    public let sealIntact: Bool
    public let coolantReady: Bool
    public let notes: [TransferHandlingNote]
    public init(id: String, title: String, destination: String, temperatureRange: String,
                sealIntact: Bool, coolantReady: Bool, notes: [TransferHandlingNote])
}
public struct ColdStorageTransferPanel: View {
    public init(transfer: ColdStorageTransfer,
                onAcknowledgementChange: @escaping (Bool) -> Void,
                onRelease: @escaping (String) -> Void)
    public var body: some View { get }
}'''
        kotlin='''data class TransferHandlingNote(val id: String, val title: String, val body: String)
data class ColdStorageTransfer(val id: String, val title: String, val destination: String,
    val temperatureRange: String, val sealIntact: Boolean, val coolantReady: Boolean,
    val notes: List<TransferHandlingNote>)
@Composable
fun ColdStorageTransferPanel(transfer: ColdStorageTransfer,
    onAcknowledgementChange: (Boolean) -> Unit, onRelease: (String) -> Unit,
    modifier: Modifier = Modifier)'''
    else:
        model='''public struct AudioTourChapter: Equatable, Identifiable {
    public let id: String
    public let title: String
    public let body: String
    public init(id: String, title: String, body: String)
}
public struct OfflineAudioTour: Equatable, Identifiable {
    public let id: String
    public let title: String
    public let language: String
    public let downloadSizeMB: Int
    public let availableMB: Int
    public let meteredConnection: Bool
    public let chapters: [AudioTourChapter]
    public init(id: String, title: String, language: String, downloadSizeMB: Int,
                availableMB: Int, meteredConnection: Bool, chapters: [AudioTourChapter])
}
public struct OfflineAudioTourPanel: View {
    public init(tour: OfflineAudioTour, onWifiOnlyChange: @escaping (Bool) -> Void,
                onDownload: @escaping (String, Bool) -> Void)
    public var body: some View { get }
}'''
        kotlin='''data class AudioTourChapter(val id: String, val title: String, val body: String)
data class OfflineAudioTour(val id: String, val title: String, val language: String,
    val downloadSizeMB: Int, val availableMB: Int, val meteredConnection: Boolean,
    val chapters: List<AudioTourChapter>)
@Composable
fun OfflineAudioTourPanel(tour: OfflineAudioTour, onWifiOnlyChange: (Boolean) -> Unit,
    onDownload: (String, Boolean) -> Unit, modifier: Modifier = Modifier)'''
    return f'''# {t['component']} public API

Implement a genuine production component, exported by AlertToast on iOS and by the Reply app on Android. The model declarations and component belong in these exact repository-relative production files:

- AlertToast repository: `{t['ios_path']}` (module `AlertToast`, iOS 14 compatible).
- Reply project (the upstream `Reply/` Gradle root): `{t['android_path']}` (package `com.example.reply.ui.components`).

The neutral pinned host versions are AlertToast `76a1c1793cd3443001c20c6033beb84453b25d9f` and Reply `53dccc7836952e3a04ed4bc1ec7afa7c8e27ff79`. These paths identify new production files; no existing source was inspected or copied to design a result.

Swift declarations below specify signatures, stored values, and exported types, not implementations:

```swift
import SwiftUI
{model}
```

Kotlin declarations (import `androidx.compose.runtime.Composable` and `androidx.compose.ui.Modifier`):

```kotlin
package com.example.reply.ui.components
{kotlin}
```

The callbacks are real production callbacks. Bridges only decode supplied caller values and forward callbacks. They own no UI, local state, layout, expected results, or replacement logic. IDs are stable strings, note/chapter IDs unique within a model. The observer calls `ObserverBridge.make(fixture:onEvent:) -> AnyView` or `org.nativeobserver.ObserverBridge.Content(current)` directly; all declared production initializers must therefore be public on Swift.

Semantic identifiers are literal `{t['prefix']}.canvas`, `.surface`, `.inkMark`, `.title`, `.subtitle`, `.status`, `.disclosure`, `.choice`, `.primary`, plus `.section.0.heading` / `.section.0.body` through `.section.7.heading` / `.section.7.body`. Each identifier belongs to exactly one actual native semantic node, not a duplicate proxy. Canvas and surface are noninteractive semantic containers that preserve descendant nodes. The ink mark is an explicitly accessible noninteractive solid rectangle labeled `Ink accent`, with its identifier on the rectangle's semantic allocation. Status is one semantic band with its label on the whole painted allocation. Its text must not create another copy of that identifier.

Use real native Buttons for disclosure, choice, and primary. Choice uses native selected semantics (SwiftUI selected trait; Compose `selected`), and primary uses native disabled semantics. A selected choice is still enabled until a request has been sent. On a request, disable both choice and primary. Disclosure stays enabled. For AX labels, exclude decorative check marks and do not concatenate status into a button label. The primary label fills its 56 pt/dp high rectangular native control allocation, with a matching content shape; the actual control boundary, rather than text glyph frame, is the geometry assertion basis. Do not merge all descendant Buttons into canvas/surface nodes.

All component state is production owned. When model identity changes, reset local disclosure, choice, and requested state with the rendered replacement, without callbacks. No wrapper `.id(...)` or Compose `key(...)` may be added by the bridge. Changing model ID is the independently fixed replacement stimulus; the current acceptance scenarios do not specify same-ID update behavior.
'''

def brief(task,scope):
    t=TERMS[task]
    if task=='T1':
        business='''1. Eligibility: an intact seal and prepared coolant are both required. A broken seal takes priority over missing coolant in status text. Missing coolant is independently exercised by P2 replacement.
2. Acknowledgement: initially unchecked; selecting the confirmation sets it true and calls `onAcknowledgementChange(true)` exactly once. Selecting it again before release clears it and emits false. Acknowledgement cannot override a seal/coolant hold.
3. Release: when eligible, acknowledged, and not already requested, primary calls `onRelease(transfer.id)` exactly once and becomes requested. No second release is possible in that local state. The component records a request; it does not perform a physical transfer.
4. Handling disclosure: initially closed, it toggles all note heading/body pairs in caller order. Disclosure produces no caller callback. Review/Hide labels reflect this state.
5. Identity replacement: a different transfer ID resets acknowledgement, disclosure, and requested to their initial values. Newly supplied title, destination, temperature range and guard values are rendered in the same mounted component, with zero callback receipt during update.

Status precedence: broken seal → `Seal needs attention`; otherwise coolant unavailable → `Coolant not ready`; otherwise requested → `Release requested`; otherwise acknowledged → `Ready for release`; otherwise `Awaiting check`. Primary is enabled iff `sealIntact && coolantReady && acknowledged && !requested`. Subtitle is `destination + " · " + temperatureRange`. Disclosure is `Review handling` / `Hide handling`. Primary is `Release transfer` / `Requested`. The confirmation label is `Confirm seal checked` / `Seal check confirmed`.'''
    else:
        business='''1. Storage: availableMB must be at least downloadSizeMB. Insufficient storage has priority over the network gate and displays `Storage needed`. Sizes are whole decimal MB values supplied by the caller; the component does not measure disk space.
2. Network choice: Wi-Fi only starts selected. On a metered connection this blocks downloading with `Wi-Fi required`. Tapping the native choice toggles it and calls `onWifiOnlyChange(newValue)` once. Disabling Wi-Fi only permits a metered download when storage is sufficient.
3. Download: when the storage and network gates allow it and no request is pending, primary calls `onDownload(tour.id, wifiOnly)` once, then displays requested and disables both choice and primary. It records a request, without fetching any audio.
4. Chapter disclosure: initially closed, it toggles all chapter heading/body pairs in caller order, with no caller callback. Review/Hide labels reflect this state.
5. Identity replacement: a new tour ID resets Wi-Fi only to true, disclosure to closed, and requested to false. The title, language and supplied MB values update in the same mounted component without callbacks. P1 replacement has insufficient storage; P2 replacement has enough storage but remains on a metered connection.

Status precedence: insufficient storage → `Storage needed`; otherwise requested → `Download requested`; otherwise meteredConnection && wifiOnly → `Wi-Fi required`; otherwise `Ready to download`. Primary is enabled iff `availableMB >= downloadSizeMB && !(meteredConnection && wifiOnly) && !requested`. Subtitle is `language + " · " + downloadSizeMB + " MB"`. Disclosure is `Review chapters` / `Hide chapters`. Primary is `Get audio` / `Requested`. The choice label is always `Wi-Fi only`, with selected state independently observable.'''
    environment_description='P1 is ordinary 400×600; P2 is narrow 280×600 with iOS xxxLarge / Android 1.3 font scale. Both cases use light appearance and LTR.' if scope=='public' else 'H1 uses independently fixed new caller values, 400×600, light appearance, normal platform text size (iOS large / Android 1.0), and RTL writing direction. H1 is private and its values must not be supplied to builders.'
    return f'''# {t['domain']}

Create `{t['component']}` as a reusable real SwiftUI component in AlertToast and a real Compose component in Reply. This is a prospective feature request. There is no known defect, injected failure, expected initial result, or implementation supplied to the designer.

{business}

The four checkpoints are overview, permitted (after disclosure and choice activation), requested (after a successful business primary activation), and replaced (after a real caller fixture update followed by a fresh full sweep). The independent reference contains all exact labels, values, units, tolerances, state IDs, event arrays, assertions, and obligation references. {environment_description} Native host horizontal padding is 16 on each side and top padding 24; actual component offered width is therefore requested width minus 32 native units, subject to the approved Android Float32 viewport encoding. Use the same source and production APIs for every case.

Layout: a full-width pale canvas owns an 8 pt/dp outer gutter; inside it a white surface owns 16 pt/dp content padding. Arrange a 6×40 pt/dp solid ink accent, title, subtitle, status band, disclosure, expanded content if open, choice, then primary in a single vertical flow. Nominal main gaps are 12 pt/dp and section gaps are 16 pt/dp. These internal layout tokens and status minimum height are advisory authoring values because the collector cannot observe generic SwiftUI layout allocations. The actual choice-to-primary native control edge gap is a separate measured MUST: 12 pt/dp ±0.75 pt/dp, with both real controls in the same native frame. Status text starts at least 16 native units inside its painted band; keep its leading 4% empty for the approved fill sample. All text wraps without line limits. Use a nominal minimum 56 pt/dp status band and allow it to grow with wrapped status text. Expanded reading material is realistic museum/handling copy, aimed at roughly 3–5 native 600-unit viewports under the selected configurations; this is design sizing guidance, not a fabricated measured height or benchmark padding requirement. Do not add fixed-height blank spacer rows to create scrolling. The native parent provides scrolling; the component adds no nested scroller.

Color roles are fixed opaque sRGB values in `reference.json`: canvas, white surface, navy ink accent, distinct waiting/ready/requested/blocked status fills, and enabled/disabled primary fills. Exact rendered fill, canvas, surface, and solid ink-mark values each have a separate pixel rule. The ink mark is the measured solid role carrier; it is not asserted to prove every text glyph color. Text ink is nominally the same navy, but generic computed SwiftUI color is unavailable and the exact text property is advisory. Typography guidance is title 22 pt/sp semibold, section heading 17 pt/sp semibold, body 17 pt on iOS / 16 sp on Android, with platform text scaling. Exact computed SwiftUI font is advisory. Title hierarchy, wrapping, overlap and clipping remain separate required visual propositions with source-backed atomic questions; no unavailable computed style can silently pass a MUST.

Native semantic label and selected/enabled checks establish current state; pixel atoms establish only their approved solid regions; two independent visual judges inspect every original state sweep for the qualitative atoms. No screenshot is a cross-platform pixel-perfect baseline. The static reference images communicate layout and hierarchy and contain the independent copy; their font rasterization is not an acceptance oracle. Long content needs overlapping sweep evidence and actual bottom reachability in each expanded state. Disabled controls are checked through enabled semantics; no blocked-disabled attempt is counted as successful callback dispatch. Choice and primary callback checks require successful native activation, and update quietness requires the actual same-process caller update method and original event interval.

App navigation, network transfer, file downloads, freezer hardware, screen safe areas outside the observer region, and background lifecycle are outside this component request. The observer integration proves this mounted production component under the declared parent. No SDK execution, native preview, screenshot from a product, or product implementation was accessed to author this specification. An independent feasibility review must occur before any builder or native run.
'''

def expectations(task, fixture):
    t=TERMS[task]; a=fixture['initial']; b=fixture['updates'][0]
    rows=a['notes' if task=='T1' else 'chapters']
    result={}
    for st in STATES:
        m=b if st=='replaced' else a
        if task=='T1':
            status=('Seal needs attention' if not m['sealIntact'] else 'Coolant not ready') if st=='replaced' else {
              'overview':'Awaiting check','permitted':'Ready for release','requested':'Release requested'}[st]
            subtitle=m['destination']+' · '+m['temperatureRange']
            checked=st in ['permitted','requested']
            choice=t['choice_on'] if checked else t['choice_off']
            event_choice=f'transfer.ack:{a["id"]}:true'
            event_request=f'transfer.release:{a["id"]}'
        else:
            status=('Storage needed' if m['availableMB']<m['downloadSizeMB'] else 'Wi-Fi required') if st=='replaced' else {
              'overview':'Wi-Fi required','permitted':'Ready to download','requested':'Download requested'}[st]
            subtitle=m['language']+' · '+str(m['downloadSizeMB'])+' MB'
            checked=st in ['overview','replaced'];choice='Wi-Fi only'
            event_choice=f'audio.wifiOnly:{a["id"]}:false'
            event_request=f'audio.download:{a["id"]}:mobile'
        role='blocked' if st=='replaced' or task=='T2' and st=='overview' else 'waiting' if st=='overview' else 'ready' if st=='permitted' else 'requested'
        result[st]={'title':val(m['title'],'string'),'subtitle':val(subtitle,'string'),'status':val(status,'string'),
          'disclosure':val(t['disclosure_on'] if st in ['permitted','requested'] else t['disclosure_off'],'string'),
          'choice':val(choice,'string'),'selected':val(checked,'bool'),'choiceEnabled':val(st!='requested','bool'),
          'primary':val(t['primary_done'] if st=='requested' else t['primary'],'string'),'enabled':val(st=='permitted','bool'),
          'statusColor':val(COLORS[role],'argb'),'buttonColor':val(COLORS['enabled' if st=='permitted' else 'disabled'],'argb'),
          'choiceEvents':val([event_choice],'events'),'requestEvents':val([event_request],'events')}
    return result, rows

def actions(task, exp):
    return [
      {'type':'sweep','state_id':'overview','max_steps':18},
      {'type':'tap','target':'disclosure','reveal':True,'max_steps':18},
      {'type':'tap','target':'choice','reveal':True,'max_steps':18,'expect_callback':exp['permitted']['choiceEvents']['value'][0]},
      {'type':'sweep','state_id':'permitted','max_steps':18},
      {'type':'tap','target':'primary','reveal':True,'max_steps':18,'expect_callback':exp['requested']['requestEvents']['value'][0]},
      {'type':'sweep','state_id':'requested','max_steps':18},
      {'type':'apply_next_fixture'},
      {'type':'sweep','state_id':'replaced','max_steps':18}]

def bundle(task, scope):
    t=TERMS[task]; dest=ROOT/task/scope; dest.mkdir(parents=True,exist_ok=True)
    write(dest/'BRIEF.md',brief(task,scope));write(dest/'API.md',api(task))
    write(dest/'Bridge.swift',bridge_swift(task));write(dest/'ObserverBridge.kt',bridge_kotlin(task))
    cases=['P1','P2'] if scope=='public' else ['H1']
    reference={'version':1,'component':t['component'],'design_owner':'Independent blind design author',
       'palette':{k:val(v,'argb') for k,v in COLORS.items()},
       'geometry':{p:{'primaryHeight':val(56,u),'tolerance':val(.75,u),'outerGutter':val(8,u),
           'innerPadding':val(16,u),'mainGap':val(12,u),'sectionGap':val(16,u),'choicePrimaryGap':val(12,u)} for p,u in [('ios','pt'),('android','dp')]},
       'typography_guidance':{'priority':'advisory','ios':{'title':val(22,'pt'),'heading':val(17,'pt'),'body':val(17,'pt')},
                             'android':{'title':val(22,'sp'),'heading':val(17,'sp'),'body':val(16,'sp')},
                             'computed_swiftui':'Unavailable to generic AX; not a measurable MUST'},
       'truth':val(True,'bool'),'quiet':val([],'events'),'cases':{},'launch':{},'questions':{},'obligations':[]}
    questions={
      'title-wrapping':('wrapping','The title displays every supplied word through natural wrapping, without truncation or an ellipsis.'),
      'body-wrapping':('wrapping','Every expanded body paragraph displays its complete supplied text through natural wrapping without an ellipsis.'),
      'title-hierarchy':('hierarchy','The title is visually more prominent than the expanded section headings.'),
      'horizontal-clipping':('clipping','All visible text and controls remain inside the component horizontal bounds without clipping.'),
      'row-overlap':('overlap','Successive rows in the component do not visually overlap.'),
      'flow-order':('content_presence','Main component blocks occur in one vertical column in this order: ink accent, title, subtitle, status, disclosure, any expanded sections, choice, primary.'),
      'collapsed-content':('content_presence',f'The {t["section_name"].lower()} body paragraphs are hidden while the disclosure is closed.'),
      'expanded-order':('content_presence',f'The eight expanded {t["section_name"].lower()} heading/body pairs appear in caller order.')}
    for key,(_,question) in questions.items(): reference['questions'][key]=val(question,'string')
    rules=[]
    def rule(id,kind,target=None,**kw):
        r={'id':id,'kind':kind,**({'target':target} if target else {}),**kw};rules.append(r)
    for rid,target,prop in [('title-label','title','label'),('subtitle-label','subtitle','label'),('status-label','status','label'),
       ('disclosure-label','disclosure','label'),('choice-label','choice','label'),('choice-selected','choice','selected'),
       ('choice-enabled','choice','enabled'),('primary-label','primary','label'),('primary-enabled','primary','enabled')]:
        rule(rid,'control',target,property=prop)
    rule('primary-height','geometry','primary',property='height',basis='control',measurement='accessibility_box',op='near')
    rule('choice-primary-gap','geometry','primary',reference_target='choice',property='gap_y',basis='control',measurement='accessibility_box',op='near')
    for rid,target,prop in [('status-fill','status','rendered_fill_argb'),('primary-fill','primary','rendered_fill_argb'),
       ('surface-fill','surface','rendered_fill_argb'),('canvas-fill','canvas','rendered_canvas_argb'),('ink-fill','inkMark','rendered_ink_argb')]:
        rule(rid,'manual',target,property=prop,coverage='target',allowed_methods=['native_pixels'])
    for i in range(8):
        rule(f'section-{i}-heading','control',f'section{i}Heading',property='label')
        rule(f'section-{i}-body','control',f'section{i}Body',property='label')
    for rid,(aspect,_) in questions.items():
        rule(rid,'manual','canvas',property=aspect,coverage='full_content',allowed_methods=['visual'])
    rule('choice-receipt','event');rule('request-receipt','event');rule('replacement-quiet','event',stimulus='caller_update')
    logical={r['target'] for r in rules if 'target' in r}
    bindings={name:{'identifier':t['prefix']+'.'+name} for name in logical if not name.startswith('section')}
    for i in range(8):
        for key,suffix in [('Heading','heading'),('Body','body')]:bindings[f'section{i}{key}']={'identifier':t['prefix']+f'.section.{i}.{suffix}'}
    put(dest/'bindings.json',bindings)
    scenarios={}
    envs={}
    for case in cases:
        f=fixtures_for(task,case);exp,rows=expectations(task,f)
        reference['cases'][case]={'caller':copy.deepcopy(f),'states':exp,'rows':rows}
        reference['launch'][case]={}
        cdir=dest/'cases'/case
        put(cdir/'fixtures.json',f)
        envs[case]={}
        for p in ['ios','android']:
            environment={'width':f['width'],'height':600,'direction':f['direction'],'theme':'light',
               **({'dynamic_type':f['dynamic_type']} if p=='ios' else {'font_scale':f['fontScale'],'dimension_encoding':'paparazzi-float32-screen-config-v1'})}
            put(cdir/f'environment.{p}.json',environment);envs[case][p]=dc.digest(environment)
            reference['launch'][case][p]={'fixtures_sha256':dc.digest(f),'bridge_sha256':sha(dest/('Bridge.swift' if p=='ios' else 'ObserverBridge.kt')),'scenario':case,'platform':p}
        route=actions(task,exp)
        bound=copy.deepcopy(route)
        for a in bound:
            if isinstance(a.get('target'),str): a['target']=bindings[a['target']]
        for p in ['ios','android']:put(cdir/f'actions.{p}.json',bound)
        values={}
        valuekeys={'title-label':'title','subtitle-label':'subtitle','status-label':'status','disclosure-label':'disclosure',
                  'choice-label':'choice','choice-selected':'selected','choice-enabled':'choiceEnabled','primary-label':'primary',
                  'primary-enabled':'enabled','status-fill':'statusColor','primary-fill':'buttonColor'}
        for r in rules:
            rid=r['id'];values[rid]={}
            for st in STATES:
                base=f'/cases/{case}/states/{st}'
                if rid in valuekeys: c=cell(base+'/'+valuekeys[rid])
                elif rid in ['primary-height','choice-primary-gap']:
                    c={p:ref('/geometry/'+p+('/primaryHeight' if rid=='primary-height' else '/choicePrimaryGap')) for p in ['ios','android']}
                    c['tolerance']={p:ref('/geometry/'+p+'/tolerance') for p in ['ios','android']}
                elif rid in ['canvas-fill','surface-fill','ink-fill']:
                    c=cell('/palette/'+{'canvas-fill':'canvas','surface-fill':'surface','ink-fill':'ink'}[rid])
                elif rid.startswith('section-'):
                    if st not in ['permitted','requested']:c={'not_applicable':'Disclosure is closed in this state, so no expanded section node exists; collapsed-content is independently required.'}
                    else:
                        _,i,field=rid.split('-');c=cell(f'/cases/{case}/rows/{i}/'+('title' if field=='heading' else 'body'))
                        # Rows are plain caller data. Add separately typed independent anchors below.
                        c=cell(f'/cases/{case}/rowAssertions/{i}/'+('title' if field=='heading' else 'body'))
                elif rid in questions:
                    if rid in ['body-wrapping','title-hierarchy','expanded-order'] and st not in ['permitted','requested']:
                        c={'not_applicable':'Expanded reading rows do not exist while disclosure is closed; title wrapping, clipping and overlap remain required.'}
                    elif rid=='collapsed-content' and st in ['permitted','requested']:
                        c={'not_applicable':'Disclosure is open; expanded-order and exact section text checks cover the opposite state.'}
                    else:c=cell('/truth')
                elif rid=='choice-receipt':
                    c=cell(base+'/choiceEvents') if st=='permitted' else {'not_applicable':'Only permitted is checkpointed after the successful native choice activation; other states have different stimuli.'}
                elif rid=='request-receipt':
                    c=cell(base+'/requestEvents') if st=='requested' else {'not_applicable':'Only requested is checkpointed after the successful native business primary activation; disabled states are never counted as dispatch.'}
                elif rid=='replacement-quiet':
                    c=cell('/quiet') if st=='replaced' else {'not_applicable':'Only replaced has the actual caller-update stimulus and original update receipt interval.'}
                else:raise ValueError(rid)
                values[rid][st]=c
        reference['cases'][case]['rowAssertions']=[{'title':val(row['title'],'string'),'body':val(row['body'],'string')} for row in rows]
        scenarios[case]={'states':[{'id':'overview','input_index':0,'after_action':0,'coverage':'full_content'},
          {'id':'permitted','input_index':0,'after_action':3,'stimulus_action':2,'coverage':'full_content'},
          {'id':'requested','input_index':0,'after_action':5,'stimulus_action':4,'coverage':'full_content'},
          {'id':'replaced','input_index':1,'after_action':7,'stimulus_action':6,'coverage':'full_content'}],
          'actions':route,'values':values}
    # Every normative clause is atomic and has explicit states and a verification route.
    obligations=[]; routes={}
    def obligation(id,clause,rids,states=STATES,risk='content',priority='must',regression=()):
        obligations.append({'id':id,'clause':clause,'priority':priority,'states':list(states),'risk':risk})
        routes[id]={'rule_ids':rids,'reason':clause+' Verified by the independently fixed rule cells on both native platforms.' if rids else
                    'Authoring guidance only: generic computed SwiftUI font/text color cannot be observed by this host; title hierarchy and solid ink role have separate MUST routes.',
                    'regression_obligations':list(regression)}
    for rid,clause in [
       ('title-label','The current caller title is exposed with its complete exact text.'),
       ('subtitle-label','The current caller summary uses the specified exact string composition.'),
       ('status-label','The status follows the independently specified guard/state precedence.'),
       ('disclosure-label','Disclosure wording reflects the current open or closed local state.'),
       ('choice-label','The native choice has its exact specified accessible label.'),
       ('choice-selected','The native selected trait reflects the local acknowledgement or Wi-Fi preference.'),
       ('choice-enabled','The native choice becomes disabled after the request and resets on replacement.'),
       ('primary-label','The primary uses the exact normal or requested label.'),
       ('primary-enabled','The primary native enabled state follows the business gates and request state.'),
       ('primary-height','The primary actual native control boundary is 56 pt/dp high within independently fixed 0.75 pt/dp tolerance.'),
       ('choice-primary-gap','The primary native control top edge is 12 pt/dp below the choice native control bottom edge, within independently fixed 0.75 pt/dp tolerance.'),
       ('status-fill','The status band leading inset has the independently fixed opaque state-role fill.'),
       ('primary-fill','The primary leading inset has the independently fixed enabled/disabled fill.'),
       ('surface-fill','The surface gutter renders the independently fixed opaque white surface role.'),
       ('canvas-fill','The component canvas gutter renders the independently fixed opaque canvas role.'),
       ('ink-fill','The solid ink accent renders the independently fixed opaque navy ink role.')]:
        obligation(rid,clause,[rid],risk='behavior' if rid in ['choice-selected','choice-enabled','primary-enabled'] else 'layout' if rid in ['primary-height','choice-primary-gap'] else 'style' if 'fill' in rid else 'content',
                   regression=['primary-enabled','status-label'] if rid in ['choice-selected','choice-enabled'] else [])
    for i in range(8):
        for field in ['heading','body']:
            rid=f'section-{i}-{field}'
            obligation(rid,f'Expanded section {i+1} {field} displays its exact caller text.',[rid],['permitted','requested'])
    for rid,(aspect,question) in questions.items():
        sts=['permitted','requested'] if rid in ['body-wrapping','title-hierarchy','expanded-order'] else ['overview','replaced'] if rid=='collapsed-content' else STATES
        obligation(rid,question,[rid],sts,'layout' if aspect in ['wrapping','overlap','clipping'] else 'style' if aspect=='hierarchy' else 'content')
    obligation('choice-receipt','A successful native choice activation emits exactly the source-backed single callback event.', ['choice-receipt'],['permitted'],'behavior',regression=['choice-selected','primary-enabled','status-label','primary-fill'])
    obligation('request-receipt','A successful native primary activation emits exactly the source-backed single business callback event.', ['request-receipt'],['requested'],'behavior',regression=['primary-enabled','choice-enabled','primary-label','status-label','primary-fill'])
    obligation('replacement-quiet','The actual same-process caller replacement emits no business callback.', ['replacement-quiet'],['replaced'],'behavior',regression=['title-label','subtitle-label','choice-selected','choice-enabled','primary-enabled','status-label','collapsed-content'])
    obligation('typography-nominal','Nominal title/body fonts, text ink, and internal spacing tokens follow the documented platform authoring values; exact computed SwiftUI fields and generic layout allocations are advisory.',[],risk='style',priority='advisory')
    reference['obligations']=obligations
    put(dest/'reference.json',reference)
    contract={'version':1,'design_owner':'Independent blind design author; no product implementation or feedback access',
       'approval_reference':str((dest/'approval.json').relative_to(ROOT))+'; preimplementation design proposal pending separate feasibility review',
       'sources':[{'id':'reference','path':'reference.json','sha256':sha(dest/'reference.json')}],
       'required_rule_ids':[r['id'] for r in rules],'rules':rules,'scenarios':scenarios}
    put(dest/'contract.json',contract)
    routefile={'version':1,'index':{'source':'reference','pointer':'/obligations'},'routes':routes};put(dest/'routes.json',routefile)
    lock=dc.seal(dest/'contract.json',dest);put(dest/'design-lock.json',lock);locksha=dc.digest(lock)
    atoms=[]
    for rid,target,aspect,region,visibility in [
      ('status-fill','status','rendered_fill',[.012,.20,.035,.80],'fully_visible'),
      ('primary-fill','primary','rendered_fill',[.02,.20,.04,.80],'fully_visible'),
      ('surface-fill','surface','rendered_fill',[.012,0,.028,1],'visible_fragment'),
      ('canvas-fill','canvas','rendered_canvas',[.002,0,.015,1],'visible_fragment'),
      ('ink-fill','inkMark','rendered_ink',[.20,.20,.80,.80],'fully_visible')]:
        atoms.append({'rule_id':rid,'aspect':aspect,'method':'native_pixels','sampling':{'region':region,'minimum_pixels':12,
           'minimum_support':.85,'channel_tolerance':0,'basis':'semantic','visibility':visibility}})
    for rid,(aspect,_) in questions.items():atoms.append({'rule_id':rid,'aspect':aspect,'method':'visual','question':ref('/questions/'+rid)})
    policy={'version':1,'design_lock_sha256':locksha,'approval_reference':contract['approval_reference'],
            'ownership':{'status':'component','primary':'component','surface':'component','canvas':'component','inkMark':'component'},'atoms':atoms}
    put(dest/'policy.json',policy)
    approval={'version':1,'status':'independently_authored_preimplementation_proposal',
       'scope':task+'/'+scope,'design_owner':'Independent blind design author',
       'design_lock_sha256':locksha,'policy_sha256':dc.digest(policy),'routes_sha256':dc.digest(routefile),
       'environment_sha256':envs,'launch':reference['launch'],
       'production_repositories':{'ios':'AlertToast','android':'Reply'},
       'production_paths':{'ios':[t['ios_path']],'android':[t['android_path']]},
       'approval_limits':'Digests freeze the independent proposal, launch inputs and verification obligations. Separate feasibility review is required before builders; this is not runtime or product acceptance.',
       'no_product_source_access':True,'no_native_execution':True,
       'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    put(dest/'approval.json',approval)
    for case in cases:
        for p in ['ios','android']:
            out=dest/'compiled'/case/p;out.mkdir(parents=True)
            original=dc.load(dest/'cases'/case/f'actions.{p}.json')
            plan,generated=dc.compile_contract(lock,locksha,case,p,bindings,original)
            put(out/'plan.json',plan);put(out/'actions.json',generated)
            coverage=rr.audit(lock,locksha,plan,routefile,dc.digest(routefile));put(out/'coverage.json',coverage)
            if coverage['must_route_gaps'] or coverage['unowned_assertions']:raise ValueError(coverage)
            f=dc.load(dest/'cases'/case/'fixtures.json')
            execution=ep.compile_execution(plan,lock,locksha,f,sha(dest/('Bridge.swift' if p=='ios' else 'ObserverBridge.kt')),
                 launch_ref={'source':'reference','pointer':f'/launch/{case}/{p}'})
            exdir=out/'execution-inputs';exdir.mkdir()
            put(out/'execution.json',execution);put(exdir/'actions.json',execution['actions']);put(exdir/'fixtures.json',execution['config'])
            catalog=rc.catalog(plan,lock,locksha,policy,dc.digest(policy),p)
            put(out/'review-catalog.json',dict(catalog,catalog_sha256=dc.digest(catalog)))
            ep.verify_execution(execution,plan,lock,locksha,f,sha(dest/('Bridge.swift' if p=='ios' else 'ObserverBridge.kt')))
            LOG.append({'operation':'frozen-candidate-v9-seal-compile-audit-execution-catalog',
              'scope':task+'/'+scope,'case':case,'platform':p,'assertions':len(plan['assertions']),
              'matrix_cells':len(plan['matrix_contract']['cells']),'must_route_gaps':coverage['must_route_gaps'],
              'design_lock_sha256':locksha,'execution_sha256':execution['execution_sha256']})
        create_references(dest,task,case,reference['cases'][case],dc.load(dest/'cases'/case/'fixtures.json'))
    primary=cases[0]
    shutil.copyfile(dest/'references'/primary/'permitted.svg',dest/'reference.svg')
    shutil.copyfile(dest/'references'/primary/'permitted.png',dest/'reference.png')
    write(dest/'COLLECTION.md',collection(task,scope,cases))
    # A digest-only seal is written after every constituent and compiled artifact.
    put(dest/'SEAL.json',{'files':{str(p.relative_to(dest)):sha(p) for p in sorted(dest.rglob('*')) if p.is_file() and p.name!='SEAL.json'}})

def collection(task,scope,cases):
    return f'''# Frozen collection contract

This {task}/{scope} bundle was compiled using the actual frozen `candidate-v9/scripts/design_contract.py`, `requirement_routes.py`, `execution_plan.py`, and `review_contract.py` functions, not copied or rewritten compilers. Every listed case ({', '.join(cases)}) is a separate approved scenario. The per-case platform plan, derived actions, route audit, full execution manifest, runtime fixture/actions, and atomic review catalog are under `compiled/<case>/<platform>/`. No native collection has occurred.

For a fresh source-bound native run, use frozen `execution_plan.py` with `--run`, the original case `fixtures.json`, original bridge, design lock and canonical approval digest, `--launch-source reference --launch-pointer /launch/<case>/<platform>`, the existing execution manifest, the platform policy and environment digests from `approval.json`, explicit production source roots from API.md, and a new evidence directory outside production source. The original fixture is not the derived execution-inputs fixture. iOS imports the real AlertToast package; Android uses the real Reply project. Use the pinned neutral host bootstrap tool configuration and already approved generic capability preflight; business code cannot substitute for that probe.

Do not edit plan or execution expectations after product feedback. A change in design requires a new independently reviewed revision and preserves this seal. All four states require fresh full content evidence; caller replacement uses stimulus action 6 with sweep checkpoint 7. Every event assertion binds the actual successful native method and original event interval. There is no callback assertion on a disabled tap. Empty expected events for replacement are assessed only after demonstrated actual caller update, never after a blocked action.

Native/pixel checks and two independently scoped qualitative reviews are both required. Collect exact original artifacts before using acceptance.py with the approved environment; review files contain actuals and original frame indices only. Do not equate compilation, reference PNG creation, native collection, or no coverage-route gaps with passed product acceptance.

The sole advisory obligation has an intentionally empty verification route: exact computed SwiftUI font/text color is unsupported. Every MUST has a nonempty feasible proposed route on both platforms. Independent N/A cells cover only closed disclosure descendants, opposite disclosure visual propositions, and unrelated callback stimulus classes. The independently commissioned feasibility reviewer must assess the semantic-node allocation and approved pixel regions before builders. Any rejected proposal or attempted schema generation remains in `design-logs`, outside the public/private seals.
'''

def create_references(dest,task,case,data,fixture):
    """Static design illustration only. Never native SDK, app, render or preview."""
    t=TERMS[task];width=fixture['width']; rtl=fixture['direction']=='rtl';scale=fixture['fontScale']
    # PIL's bundled default font is sufficient for independent English wireframes.
    fonts={s:ImageFont.load_default(size=int(s*scale)) for s in [13,16,17,22]}
    for st in STATES:
        exp=data['states'][st]; expanded=st in ['permitted','requested']
        x=16+8+16;cw=width-2*x; y=24+8+16; items=[]
        def rect(x0,y0,w,h,color):items.append(('rect',x0,y0,w,h,color))
        def text(value,size,color='#172B4D',weight='normal'):
            nonlocal y
            f=fonts[size]; words=value.split();lines=[];line=''
            for word in words:
                candidate=line+' '+word if line else word
                if f.getlength(candidate)>cw and line:lines.append(line);line=word
                else:line=candidate
            if line:lines.append(line)
            lh=round(size*scale*1.35)
            for line in lines:
                items.append(('text',x+cw if rtl else x,y+size*scale,line,size*scale,color,weight,rtl));y+=lh
            y+=12
        rect(x,y,6,40,'#172B4D');y+=52
        text(exp['title']['value'],22,weight='bold');text(exp['subtitle']['value'],16)
        status_y=y
        status_h=max(56,round(46*scale))
        rect(x,status_y,cw,status_h,'#'+exp['statusColor']['value'][3:]);y+=14
        items.append(('text',x+16 if not rtl else x+cw-16,y+17*scale,exp['status']['value'],17*scale,'#172B4D','bold',rtl))
        y=status_y+status_h+16
        text(exp['disclosure']['value'],17,weight='bold')
        if expanded:
            for row in data['rows']:
                text(row['title'],17,weight='bold');text(row['body'],16);y+=4
        check='[x] ' if exp['selected']['value'] else '[ ] '
        text(check+exp['choice']['value'],17)
        rect(x,y,cw,56,'#'+exp['buttonColor']['value'][3:])
        items.append(('text',x+cw/2,y+34,exp['primary']['value'],17,'#FFFFFF' if st=='permitted' else '#172B4D','bold','center'))
        y+=56+16+8
        height=max(600,int(y+24));img=Image.new('RGB',(width,height),'#F4F6FA');draw=ImageDraw.Draw(img)
        surface=(24,32,width-24,y-8);draw.rectangle(surface,fill='#FFFFFF')
        svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             f'<title>{html.escape(t["domain"])} — {case} — {st}</title>',
             '<desc>Independent design reference. Font metrics and full height are illustrative, not native measurements.</desc>',
             f'<rect width="{width}" height="{height}" fill="#F4F6FA"/>',
             f'<rect x="24" y="32" width="{width-48}" height="{y-40}" fill="#FFFFFF"/>']
        for item in items:
            if item[0]=='rect':
                _,xx,yy,ww,hh,color=item;draw.rectangle((xx,yy,xx+ww,yy+hh),fill=color)
                svg.append(f'<rect x="{xx}" y="{yy}" width="{ww}" height="{hh}" fill="{color}"/>')
            else:
                _,xx,yy,string,size,color,weight,align=item
                anchor='middle' if align=='center' else 'end' if align else 'start'
                font=ImageFont.load_default(size=int(size))
                draw.text((xx,yy),string,font=font,fill=color,anchor='ms' if align=='center' else 'rs' if align else 'ls')
                svg.append(f'<text x="{xx}" y="{yy}" font-family="sans-serif" font-size="{size}" font-weight="{weight}" fill="{color}" text-anchor="{anchor}">{html.escape(string)}</text>')
        svg.append('</svg>')
        out=dest/'references'/case;out.mkdir(parents=True,exist_ok=True)
        write(out/(st+'.svg'),'\n'.join(svg)+'\n');img.save(out/(st+'.png'))

LOG=[]
if __name__=='__main__':
    try:
        for task in ['T1','T2']:
            for scope in ['public','private']:bundle(task,scope)
        put(ROOT/'design-logs'/'compiler-results.json',LOG)
        put(ROOT/'design-logs'/'authoring-session.json',{
          'frozen_skill':str(SKILL),'scripts':{name:sha(SKILL/'scripts'/name) for name in ['design_contract.py','requirement_routes.py','execution_plan.py','review_contract.py']},
          'used_actual_modules':True,'sdk_execution':False,'product_source_access':False,
          'source_resources':'Frozen candidate-v9 skill, generic assets, neutral pinned host bootstrap/package/build instructions, and independently authored design files only.',
          'limitations':['No runtime feasibility or native acceptance is asserted.','Static reference image metrics are illustrative.','Computed SwiftUI typography/text ink are advisory.','No source-derived test expectations.'],
          'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat()})
        write(ROOT/'README.md','''# Sealed prospective design proposal

T1 is a cold-storage transfer release component. T2 is an offline museum audio-tour component. Each has independently authored public P1/P2 and private H1 packages, four checkpointed states, thin production API bridges, source-backed obligations, independent N/A reasons, approved launch inputs, and compiler-generated plans/coverage/execution manifests.

All output was designed before implementation. No product source, old study case/result, native SDK execution, product render, treatment assignment, or feedback was accessed. Only frozen candidate-v9 Skill resources and neutral pinned host API/build instructions were read. There is no planted defect or intended result. No product implementation was written. The bridges call only the proposed real production public APIs. The full package is a proposal awaiting root's independent feasibility review before builders.

Do not provide private fixtures, private references, or design-logs/author_design.py to builders. Public packages contain no H1 values. The generator and complete compiler attempt record are outside the per-bundle seals. The sole advisory obligation explicitly retains unavailable generic SwiftUI computed fonts/text ink. All MUST routes compile on both platforms without route gaps. This is static contract completeness, not runtime success.
''')
        files={str(p.relative_to(ROOT)):sha(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='DESIGN-SEAL.json'}
        put(ROOT/'DESIGN-SEAL.json',{'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':files,
          'no_product_source_access':True,'no_native_execution':True,'no_product_implementation':True,
          'status':'sealed_independent_design_proposal_pending_feasibility_review'})
        print(json.dumps({'status':'sealed','files':len(files),'compiled_case_platform_pairs':len(LOG),'root':str(ROOT)}))
    except Exception:
        attempt=ROOT/'design-logs'/('unsuccessful-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S'))
        attempt.mkdir(parents=True,exist_ok=True)
        for task in ['T1','T2']:
            for scope in ['public','private']:
                source=ROOT/task/scope
                if source.exists():shutil.copytree(source,attempt/task/scope)
        write(attempt/'traceback.txt',traceback.format_exc());put(attempt/'completed-operations.json',LOG)
        raise
