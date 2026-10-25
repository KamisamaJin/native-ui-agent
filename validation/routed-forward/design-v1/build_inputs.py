#!/usr/bin/env python3
"""Independent ListeningBreakPanel design authoring; never reads production code.

Run before sealing. --seal first checks every requirement mapping and schema,
then pins each scope and the complete design directory. No SDK is invoked.
"""
from pathlib import Path
import argparse, hashlib, importlib.util, json, re, sys, time

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
sys.path.insert(0, str(REPO / 'native-ui-agent/scripts'))
import design_contract as d
import requirement_routes as rr
import review_contract as rv
import execution_plan as xp
import acceptance

PLATFORMS = ['ios', 'android']
PRODUCTION = {'ios': ['Sources/AlertToast/ListeningBreakPanel.swift'],
              'android': ['app/src/main/java/com/example/reply/ui/components/ListeningBreakPanel.kt']}
OWNER = 'Independent business design author r11_business_design'

def typed(v, u): return {'value': v, 'unit': u}
def anchor(p): return {'source': 'reference', 'pointer': p}
def cell(p): return {pl: anchor(p) for pl in PLATFORMS}
def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

SWIFT = '''import SwiftUI
import AlertToast

// Caller adaptation only: every visible element and all local state belong to production.
enum ObserverBridge {
    static func make(fixture: [String: Any], onEvent: @escaping (String) -> Void) -> AnyView {
        let options = (fixture["options"] as! [[String: Any]]).map { item in
            ListeningBreakOption(id: item["id"] as! String,
                                 title: item["title"] as! String,
                                 detail: item["detail"] as! String,
                                 isAvailable: item["isAvailable"] as! Bool)
        }
        let input = ListeningBreakInput(sessionID: fixture["sessionID"] as! String,
                                        title: fixture["title"] as! String,
                                        introduction: fixture["introduction"] as! String,
                                        options: options,
                                        quietNote: fixture["quietNote"] as! String,
                                        footer: fixture["footer"] as! String)
        return AnyView(ListeningBreakPanel(input: input,
            onStart: { sessionID, optionID in onEvent("listening.started:\\(sessionID):\\(optionID)") },
            onCancel: { sessionID in onEvent("listening.canceled:\\(sessionID)") }))
    }
}
'''

KOTLIN = '''package org.nativeobserver

import androidx.compose.runtime.Composable
import com.example.reply.ui.components.ListeningBreakInput
import com.example.reply.ui.components.ListeningBreakOption
import com.example.reply.ui.components.ListeningBreakPanel
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.boolean
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

// Caller adaptation only; no remember, replacement key or product UI is supplied here.
object ObserverBridge {
    @Composable
    fun Content(fixture: JsonObject, onEvent: (String) -> Unit) {
        fun text(key: String) = fixture.getValue(key).jsonPrimitive.content
        val options = fixture.getValue("options").jsonArray.map { value ->
            val item = value.jsonObject
            ListeningBreakOption(id = item.getValue("id").jsonPrimitive.content,
                title = item.getValue("title").jsonPrimitive.content,
                detail = item.getValue("detail").jsonPrimitive.content,
                isAvailable = item.getValue("isAvailable").jsonPrimitive.boolean)
        }
        val input = ListeningBreakInput(sessionID = text("sessionID"), title = text("title"),
            introduction = text("introduction"), options = options,
            quietNote = text("quietNote"), footer = text("footer"))
        ListeningBreakPanel(input = input,
            onStart = { sessionID, optionID -> onEvent("listening.started:$sessionID:$optionID") },
            onCancel = { sessionID -> onEvent("listening.canceled:$sessionID") })
    }
}
'''

# Each clause is normative. The requirement document contains no unindexed prose
# obligations. The ledger maps these exact sentences to source-backed owners.
CLAUSES = [
('R01', 'Add the standalone ListeningBreakPanel component in exactly the approved single production file on each platform; retain the upstream library/application and its existing behavior.', 'audit', 'A-file-scope', '/source/file_scope'),
('R02', 'Expose the exact public, value-equatable data models and callable signatures in api-contract.json; the iOS component is a SwiftUI View available on iOS 14 and Android is a Compose @Composable in com.example.reply.ui.components.', 'audit', 'A-api', '/source/api'),
('R03', 'Accept valid caller inputs with a nonempty sessionID, at least one available option, unique ASCII option IDs matching [A-Za-z0-9_-]+, nonempty copy, and caller-preserved option order; the component owns no audio engine or network operation.', 'audit', 'A-input-domain', '/source/input_domain'),
('R04', 'Display this exact vertical order: input title, introduction, all option title/detail pairs in caller order, quietNote, fixed acknowledgement switch, status, conditional error, conditional success summary, primary action, Cancel action, and footer; display all caller copy verbatim.', 'runtime', 'O-copy', '/questions/content'),
('R05', 'Expose stable identifiers listening.canvas, listening.title, listening.introduction, listening.note, listening.acknowledge, listening.status, listening.primary, listening.cancel, listening.footer, listening.error and listening.summary; each option control uses listening.option.<id>.', 'audit', 'A-identifiers', '/source/identifiers'),
('R06', 'Give each option one native button with accessible label title + " — " + detail and a selected trait that matches its local selection; the acknowledgement is one labeled native switch with its real Boolean value.', 'runtime', 'O-semantics', '/source/semantics'),
('R07', 'Begin editing with no selection, acknowledgement off, no error or success summary, status "Choose a soundscape for your break.", and enabled Start listening and Cancel controls.', 'runtime', 'O-initial', '/state/ready/status'),
('R08', 'Selecting an available option exclusively selects its ID; selecting it again preserves that selection, changing to another available option replaces it, and unavailable options remain disabled and never selectable.', 'audit', 'A-selection', '/source/selection'),
('R09', 'While editing, a successful Start listening activation validates both an available selected option and acknowledgement on; unmet conditions leave editing active and show the applicable exact error text defined in api-contract.json without emitting onStart or onCancel.', 'audit', 'A-validation', '/source/validation'),
('R10', 'On valid Start listening activation, enter the started state synchronously, show status "Your listening break is ready.", show summary "Ready to begin: " + selected option title, and invoke onStart(sessionID, optionID) exactly once for that activation.', 'runtime', 'O-success', '/state/started/status'),
('R11', 'In the started state, retain all caller content, preserve the selected option and on acknowledgement, disable every option and the acknowledgement, and change the enabled primary label to "Choose again".', 'runtime', 'O-started-controls', '/state/started/primary'),
('R12', 'A Choose again activation returns to the initial editing state for the current input, clears selection, acknowledgement, errors and summary, and emits no callbacks.', 'runtime', 'O-renew', '/state/renewed/status'),
('R13', 'Cancel remains enabled in every state; each activation invokes onCancel(current sessionID) once and returns to initial editing for that same input, including repeated Cancel activations with no choices.', 'audit', 'A-cancel', '/source/cancel'),
('R14', 'Changing either editing choice clears the visible validation error; turning acknowledgement off is allowed while editing and does not clear the selected option.', 'audit', 'A-edit-error', '/source/edit_error'),
('R15', 'Any unequal full input replacement resets selection, acknowledgement, validation and started state before the replacement is rendered, even when sessionID and option IDs are unchanged; rendering an equal input preserves local state and neither case emits callbacks.', 'audit', 'A-replacement', '/source/replacement'),
('R16', 'Keep the component identity and business logic in production: the supplied bridges adapt fixture values and real callback arguments only, and neither bridge may force identity changes, supply local product state, or synthesize callback outcomes.', 'audit', 'A-bridge-boundary', '/source/bridge_boundary'),
('R17', 'Use exact opaque sRGB colors from reference.json: canvas behind the column and Cancel; option/selectedOption/unavailableOption on option surfaces; primary and primaryInk on the primary button; title on the heading; body on introduction, note, available option titles, acknowledgement, status, summary and Cancel text; muted on option details, unavailable option titles and footer; error on error text; border on every option outline; use no shadows, gradients or translucency.', 'audit', 'A-colors', '/source/colors'),
('R18', 'Render the component canvas in its canvas role color throughout all states and the primary button in its primary role color in both Start listening and Choose again states.', 'runtime', 'O-rendered-colors', '/colors/canvas'),
('R19', 'Use a single column filling its parent content width (the observer offers total width minus its own 32-unit horizontal inset), with 20 native units of internal canvas padding, 12 units between major blocks and options, 12-unit option and action corner radii, 16-unit option/action horizontal padding and 12-unit vertical padding, and a 1-unit option border; each title/detail option pair has a 4-unit internal gap and actions fill the available column width.', 'audit', 'A-spacing', '/source/spacing'),
('R20', 'Use platform-scaled system text at the base sizes and weights in reference.json: title 24 semibold, introduction/note/option title 16 regular except option title semibold, option detail/footer 14 regular, status/error/summary 16 regular, and action text 16 semibold.', 'audit', 'A-type', '/source/typography'),
('R21', 'Give the primary and Cancel native accessible/control rectangles minimum height 48 native units and minimum width 120 native units; option rectangles have minimum height 64 native units and may grow for content or text size.', 'runtime', 'O-control-size', '/geometry/actionMinHeight/ios'),
('R22', 'Allow all supplied copy and action labels to wrap without truncation, ellipsis, text scaling down, horizontal scrolling, clipping, or overlap; use leading alignment and let the parent vertical scroller reach every item at offered widths 320 through 430 and system text sizes through iOS accessibility2 / Android fontScale 1.6.', 'runtime', 'O-long-content', '/questions/wrapping'),
('R23', 'Keep source font and padding review separate from native rectangle and text facts: AX bounds do not establish computed font, padding, color or physical hit regions.', 'audit', 'A-evidence-boundary', '/source/evidence'),
('R24', 'The six route checkpoints and all assertions are fixed before implementation; callback verdicts require demonstrated successful dispatch to exactly one enabled native control in one input epoch, or demonstrated same-process caller replacement for caller_update, before comparing the exact callback interval.', 'audit', 'A-callback-evidence', '/source/callback_evidence'),
('R25', 'At every route checkpoint the visible content must be complete and mutually non-overlapping, including validation and success text when present; the canvas and primary color, content presence, wrapping and overlap are independent review atoms.', 'runtime', 'O-visual-integrity', '/questions/overlap'),
('R26', 'For the route, an invalid Start emits no events, a valid Start emits only the selected start event, Choose again emits no events, Cancel emits only its cancel event, and dirty-state caller replacement emits no events and displays only the new copy with reset local choices.', 'runtime', 'O-route-behavior', '/events/empty'),
('R27', 'Only valid Start listening and Cancel activations invoke the supplied callbacks; selection changes, acknowledgement changes, validation failures, Choose again, recomposition and caller replacements invoke neither callback, and each actual action uses the callbacks supplied by the current caller.', 'audit', 'A-callback-boundaries', '/source/callback_boundaries'),
]

CHECKPOINT_CLAUSES = [
 ('ready','Initial empty editing state.','O-initial'),
 ('validation','Activate Start listening with neither requirement satisfied; show both-condition error.','O-route-behavior'),
 ('started','Choose the first available option, turn acknowledgement on, then Start listening; one start callback.','O-success'),
 ('renewed','Activate Choose again; empty editing state and no callback.','O-renew'),
 ('canceled','Choose the second available option, acknowledge, then Cancel; one cancel callback and empty editing state.','O-route-behavior'),
 ('replaced','Make editing dirty with the first option and acknowledgement, then replace the entire input without remounting; new copy, empty local state, no callback.','O-route-behavior')]

API = {
 'version': 1,
 'ios': {'module': 'AlertToast', 'minimum': 'iOS 14.0',
  'models': [
   {'name':'ListeningBreakOption','conformance':['Equatable'],'access':'public','properties':{'id':'String','title':'String','detail':'String','isAvailable':'Bool'},'initializer':'public init(id: String, title: String, detail: String, isAvailable: Bool)'},
   {'name':'ListeningBreakInput','conformance':['Equatable'],'access':'public','properties':{'sessionID':'String','title':'String','introduction':'String','options':'[ListeningBreakOption]','quietNote':'String','footer':'String'},'initializer':'public init(sessionID: String, title: String, introduction: String, options: [ListeningBreakOption], quietNote: String, footer: String)'}],
  'component':'public struct ListeningBreakPanel: View',
  'initializer':'public init(input: ListeningBreakInput, onStart: @escaping (String, String) -> Void, onCancel: @escaping (String) -> Void)'},
 'android': {'package':'com.example.reply.ui.components','minimum':'upstream Reply Compose toolchain',
  'models':['data class ListeningBreakOption(val id: String, val title: String, val detail: String, val isAvailable: Boolean)',
            'data class ListeningBreakInput(val sessionID: String, val title: String, val introduction: String, val options: List<ListeningBreakOption>, val quietNote: String, val footer: String)'],
  'component':'@Composable fun ListeningBreakPanel(input: ListeningBreakInput, onStart: (String, String) -> Unit, onCancel: (String) -> Unit, modifier: Modifier = Modifier)'},
 'callbacks': {'onStart':['current input sessionID','selected option ID'], 'onCancel':['current input sessionID']},
 'copy': {'acknowledgement':'I have read the quiet-space note','start':'Start listening','again':'Choose again','cancel':'Cancel',
  'ready':'Choose a soundscape for your break.','started':'Your listening break is ready.', 'summaryPrefix':'Ready to begin: ',
  'errors':{'both':'Choose a soundscape and confirm the quiet-space note.','selection':'Choose an available soundscape.','acknowledgement':'Confirm the quiet-space note before starting.'}},
 'identity': 'Complete value equality across all declared input and ordered option fields; no forced identity from the caller.'}

def inputs(private):
    if not private:
        initial = {'sessionID':'afternoon-pause','title':'Make room for a listening break',
          'introduction':'Choose one soundscape for a short pause. You can change your choice before you begin.',
          'options':[
           {'id':'rain','title':'Rain on the conservatory roof','detail':'A gentle, even texture for a quiet five-minute pause.','isAvailable':True},
           {'id':'garden','title':'Morning in the community garden','detail':'Bird calls and distant leaves with occasional moments of silence.','isAvailable':True},
           {'id':'harbor','title':'Harbor bells','detail':'This soundscape is being refreshed and is currently unavailable.','isAvailable':False}],
          'quietNote':'Find a comfortable volume and a place where you can pause safely. You can stop whenever you wish.',
          'footer':'Your choice stays on this device for this session. Starting here does not play audio automatically.'}
        update = {'sessionID':'afternoon-pause','title':'A fresh collection for your next pause',
          'introduction':'The library has refreshed these listening notes. Please choose again for this updated session.',
          'options':[
           {'id':'rain','title':'Rain beneath the glass canopy','detail':'Soft rainfall, recorded from the sheltered side of the conservatory.','isAvailable':True},
           {'id':'garden','title':'Evening garden after the volunteers leave','detail':'A slower mix of rustling leaves and the last birds of the day.','isAvailable':True},
           {'id':'harbor','title':'Harbor bells — still unavailable','detail':'The recording team is preparing a new version.','isAvailable':False}],
          'quietNote':'Check your volume again before beginning. Leave room to hear the people and sounds around you.',
          'footer':'These updated descriptions replace the previous collection; make a new choice when you are ready.'}
        return initial, update, 390, 'large', 1.0
    initial = {'sessionID':'weekend-rest','title':'A small pocket of quiet between the busy parts of your day',
      'introduction':'Settle in at your own pace and choose a recording that feels comfortable today. Every soundscape has its own rhythm, and you are welcome to change your mind before beginning this listening break.',
      'options':[
       {'id':'brook','title':'A winding woodland brook after the overnight rain','detail':'Water moves over shallow stones while occasional birds call from deeper in the trees. There is no narration and no music, so the sound can leave plenty of space for your own thoughts.','isAvailable':True},
       {'id':'hearth','title':'A warm room beside the old library fireplace','detail':'Low crackles, a little movement in the room, and quiet intervals between them. The recording was made from an armchair a comfortable distance from the fire.','isAvailable':True},
       {'id':'meadow','title':'The far meadow beyond the orchard wall','detail':'This longer field recording is being prepared for the collection and cannot be selected yet. Another available soundscape can be chosen now.','isAvailable':False}],
      'quietNote':'Before starting, make sure you are somewhere you can rest without needing to watch for moving traffic, equipment, or other demands on your attention. Keep the volume comfortable enough to notice your surroundings, and stop the break whenever you need to.',
      'footer':'A listening break is simply an invitation to pause. There is no score to achieve, no timer you must complete, and no need to keep a particular pace. Your choice belongs to this local session, and this panel does not begin audio playback.'}
    update = {'sessionID':'weekend-rest','title':'The sound library has new notes for this quiet moment',
      'introduction':'The descriptions have been refreshed while this panel stayed open. Read the new notes and make whichever choice suits you now; earlier choices are cleared so this session begins with the current information.',
      'options':[
       {'id':'brook','title':'Woodland water near the little footbridge at dusk','detail':'The same gentle stream heard later in the day, with longer quiet spaces between the calls of birds and a soft breeze passing through the trees beside the water.','isAvailable':True},
       {'id':'hearth','title':'An afternoon by the reading room hearth after the rain','detail':'A little less crackle and a little more room tone, recorded while the building settled into a calm afternoon. Choose a comfortable volume before you begin.','isAvailable':True},
       {'id':'meadow','title':'Orchard meadow — preparation continues','detail':'This recording is still unavailable while its listening notes are prepared.','isAvailable':False}],
      'quietNote':'Take another moment to check that your resting place and volume still feel comfortable. You can pause or leave whenever your surroundings need your attention.',
      'footer':'The new collection has replaced the earlier descriptions without opening a new panel. You can now choose again from the current soundscapes and confirm the updated quiet-space note.'}
    return initial, update, 320, 'accessibility2', 1.6

def build_scope(name):
    scope = ROOT/name
    if (scope/'SEAL.json').exists(): raise ValueError('Already sealed: '+name)
    scope.mkdir(parents=True, exist_ok=True)
    private = name == 'private'
    case = 'quiet-library' if not private else 'long-library'
    initial, update, width, dynamic_type, font_scale = inputs(private)
    (scope/'Bridge.swift').write_text(SWIFT)
    (scope/'ObserverBridge.kt').write_text(KOTLIN)
    write(scope/'api-contract.json', API)
    states = [{'id':sid,'after_action':idx,'input_index':int(sid=='replaced'),'coverage':'full_content'}
        for sid,idx in [('ready',0),('validation',1),('started',4),('renewed',5),('canceled',8),('replaced',11)]]
    ids = [s['id'] for s in states]
    logical = {'canvas':'listening.canvas','title':'listening.title','introduction':'listening.introduction',
      'note':'listening.note','acknowledge':'listening.acknowledge','status':'listening.status',
      'primary':'listening.primary','cancel':'listening.cancel','footer':'listening.footer',
      'error':'listening.error','summary':'listening.summary'}
    logical.update({'option_a':'listening.option.'+initial['options'][0]['id'],
                    'option_b':'listening.option.'+initial['options'][1]['id'],
                    'unavailable':'listening.option.'+initial['options'][2]['id']})
    bindings = {k:{'identifier':v, **({'role':'button'} if k in {'primary','cancel','option_a','option_b','unavailable'} else {'role':'switch'} if k=='acknowledge' else {})} for k,v in logical.items()}
    actions = [{'type':'checkpoint','state_id':'ready'},
      {'type':'tap','target':'primary','reveal':True,'state_id':'validation'},
      {'type':'tap','target':'option_a','reveal':True},
      {'type':'tap','target':'acknowledge','reveal':True},
      {'type':'tap','target':'primary','reveal':True,'state_id':'started'},
      {'type':'tap','target':'primary','reveal':True,'state_id':'renewed'},
      {'type':'tap','target':'option_b','reveal':True},
      {'type':'tap','target':'acknowledge','reveal':True},
      {'type':'tap','target':'cancel','reveal':True,'state_id':'canceled'},
      {'type':'tap','target':'option_a','reveal':True},
      {'type':'tap','target':'acknowledge','reveal':True},
      {'type':'apply_next_fixture','state_id':'replaced'}]
    fixtures = {'initial':initial,'updates':[update],'width':width,'viewportHeight':600,
       'theme':'light','dynamic_type':dynamic_type,'fontScale':font_scale,'direction':'ltr',
       'canvas_color':'#F2F6F4','max_scrolls':32,'state_capture':True,
       'required_identifiers':[logical[x] for x in ['title','introduction','option_a','option_b','unavailable','note','acknowledge','status','primary','cancel','footer']]}
    write(scope/'cases'/case/'fixtures.json', fixtures)
    for pl in PLATFORMS: write(scope/('bindings.'+pl+'.json'), bindings)
    colors = {'canvas':'#FFF2F6F4','option':'#FFFFFFFF','selectedOption':'#FFE8F3EF','unavailableOption':'#FFF0F2F1',
       'primary':'#FF176B58','primaryInk':'#FFFFFFFF','title':'#FF172F2A','body':'#FF38564E','muted':'#FF687A75',
       'error':'#FFB0382C','border':'#FFABC6BC'}
    ref = {'version':1,'component':'ListeningBreakPanel', 'booleans':{'yes':typed(True,'bool'),'no':typed(False,'bool')},
       'colors':{k:typed(v,'argb') for k,v in colors.items()},
       'geometry':{k:{pl:typed(v,'pt' if pl=='ios' else 'dp') for pl in PLATFORMS}
        for k,v in {'actionMinHeight':48,'actionMinWidth':120,'optionMinHeight':64,'canvasPadding':20,'blockGap':12,'optionTextGap':4,'cornerRadius':12,'horizontalPadding':16,'verticalPadding':12,'borderWidth':1}.items()},
       'typography':{k:{'ios':typed(v,'pt'),'android':typed(v,'sp'),'weight':typed(w,'scalar')}
        for k,v,w in [('title',24,600),('body',16,400),('optionTitle',16,600),('detail',14,400),('action',16,600)]},
       'questions':{
        'content':typed('Are the input title, introduction, every ordered option title/detail, note and footer visibly rendered verbatim, plus the exact acknowledgement, status, action labels and applicable error/summary for this checkpoint?','string'),
        'wrapping':typed('Can every supplied text and action label be read in the full vertical sweep with wrapping and no truncation, ellipsis, scaling down, horizontal scrolling or clipping?','string'),
        'overlap':typed('Are all component text, option controls, acknowledgement, status, applicable error/summary and actions mutually non-overlapping throughout this checkpoint?','string')},
       'source':{},'copy':{k:typed(v,'string') for k,v in API['copy'].items() if isinstance(v,str)},
       'state':{},'events':{'empty':typed([],'events'),
         'start':typed(['listening.started:'+initial['sessionID']+':'+initial['options'][0]['id']],'events'),
         'cancel':typed(['listening.canceled:'+initial['sessionID']],'events')},
       'inputs':{'initial':initial,'replacement':update}, 'launch':{}}
    for rid,text,owner,ownerid,p in CLAUSES:
        if p.startswith('/source/'):
            ref['source'][p.rsplit('/',1)[-1]] = typed(text,'string')
    ref['source']['api'] = typed(json.dumps(API,ensure_ascii=False,sort_keys=True),'string')
    ref['source']['file_scope'] = typed('One independent new file per platform: '+json.dumps(PRODUCTION,sort_keys=True)+'; retain the upstream library/application and existing behavior.','string')
    ref['source']['validation'] = typed(CLAUSES[8][1]+' Exact error copy: '+json.dumps(API['copy']['errors'],sort_keys=True),'string')
    ref['source']['native_matrix'] = typed('The complete native rule/state matrix is owned by R04, R06, R07, R10, R11, R12, R21 and R26. Every applicable cell is independently specified by typed source pointers; conditional text absent in a state has an explicit N/A label cell and an assessed presence rule.','string')
    for sid,desc,oid in CHECKPOINT_CLAUSES: ref['source']['checkpoint_'+sid]=typed(desc,'string')
    # Each source-only color/spacing/font datum remains an explicit typed value;
    # the general proposition above supplies the complete role-to-usage context.
    for sid in ids:
        data = update if sid=='replaced' else initial
        started = sid=='started'
        ref['state'][sid] = {k:typed(data[k],'string') for k in ['title','introduction','quietNote','footer']}
        ref['state'][sid].update({
          'status':typed(API['copy']['started'] if started else API['copy']['ready'],'string'),
          'primary':typed(API['copy']['again'] if started else API['copy']['start'],'string'),
          'error':typed(API['copy']['errors']['both'],'string'),
          'summary':typed(API['copy']['summaryPrefix']+data['options'][0]['title'],'string')})
        for key,index in [('option_a',0),('option_b',1),('unavailable',2)]:
            opt=data['options'][index]
            ref['state'][sid][key]=typed(opt['title']+' — '+opt['detail'],'string')
    rules=[]
    def rule(id,kind,target=None,property=None,**kw):
        row={'id':id,'kind':kind,**({'target':target} if target else {}),**({'property':property} if property else {}),**kw}
        rules.append(row)
    for target,field in [('title','title'),('introduction','introduction'),('note','quietNote'),('footer','footer'),('status','status'),('primary','primary'),('option_a','option_a'),('option_b','option_b'),('unavailable','unavailable')]:
        rule(target+'-label','control',target,'label')
    for target in ['acknowledge','cancel']: rule(target+'-label','control',target,'label')
    for target in ['primary','cancel','option_a','option_b','unavailable','acknowledge']: rule(target+'-enabled','control',target,'enabled')
    for target in ['option_a','option_b']: rule(target+'-selected','control',target,'selected')
    rule('acknowledge-value','control','acknowledge','value')
    for target in ['error','summary']:
        rule(target+'-present','control',target,'present')
        rule(target+'-label','control',target,'label')
    for target in ['primary','cancel']:
        rule(target+'-height','geometry',target,'height',basis='control',measurement='accessibility_box',op='gte')
        rule(target+'-width','geometry',target,'width',basis='control',measurement='accessibility_box',op='gte')
    for target in ['option_a','option_b','unavailable']:
        # Semantic button boxes can be observed even when disabled.
        rule(target+'-height','geometry',target,'height',basis='semantic',measurement='accessibility_box',op='gte')
    rule('activation-events','event',stimulus='activation')
    rule('replacement-events','event',stimulus='caller_update')
    for rid,target,prop,method in [('canvas-color','canvas','rendered_canvas','native_pixels'),('primary-color','primary','rendered_fill','native_pixels'),('content-complete','canvas','content_presence','visual'),('text-wrap','canvas','wrapping','visual'),('content-overlap','canvas','overlap','visual')]:
        rule(rid,'manual',target,prop,coverage='full_content',allowed_methods=[method])
    values={r['id']:{} for r in rules}
    for r in rules:
        rid=r['id'];target=r.get('target')
        for sid in ids:
            started=sid=='started'
            if rid in [t+'-label' for t in ['title','introduction','note','footer','status','primary','option_a','option_b','unavailable']]:
                field='quietNote' if target=='note' else target
                v=cell('/state/'+sid+'/'+field)
            elif rid in {'acknowledge-label','cancel-label'}: v=cell('/copy/'+('acknowledgement' if target=='acknowledge' else 'cancel'))
            elif rid.endswith('-enabled'):
                yes=target in {'primary','cancel'} or target!='unavailable' and not started
                v=cell('/booleans/'+('yes' if yes else 'no'))
            elif rid.endswith('-selected') or rid=='acknowledge-value':
                yes=started and target in {'option_a','acknowledge'}
                v=cell('/booleans/'+('yes' if yes else 'no'))
            elif rid in {'error-present','summary-present'}:
                yes=sid==('validation' if target=='error' else 'started')
                v=cell('/booleans/'+('yes' if yes else 'no'))
            elif rid in {'error-label','summary-label'}:
                v=cell('/state/'+sid+'/'+target) if sid==('validation' if target=='error' else 'started') else {'not_applicable':'This conditional text is absent by the independently specified editing/started state.'}
            elif r['kind']=='geometry':
                key='optionMinHeight' if target in {'option_a','option_b','unavailable'} else 'actionMinHeight' if rid.endswith('height') else 'actionMinWidth'
                v={pl:anchor('/geometry/'+key+'/'+pl) for pl in PLATFORMS}
            elif rid=='activation-events':
                v=cell('/events/'+('start' if sid=='started' else 'cancel' if sid=='canceled' else 'empty')) if sid in {'validation','started','renewed','canceled'} else {'not_applicable':'No activation is the checkpoint stimulus; empty intervals are not behavior evidence without successful native activation.'}
            elif rid=='replacement-events':
                v=cell('/events/empty') if sid=='replaced' else {'not_applicable':'No caller replacement is dispatched at this checkpoint.'}
            elif rid in {'canvas-color','primary-color'}: v=cell('/colors/'+('canvas' if rid=='canvas-color' else 'primary'))
            else: v=cell('/booleans/yes')
            values[rid][sid]=v
    allrules=[r['id'] for r in rules]
    groups={
      'O-copy':[r for r in allrules if r.endswith('-label') and not r.startswith(('error','summary'))]+['content-complete'],
      'O-semantics':['option_a-selected','option_b-selected','acknowledge-value','option_a-label','option_b-label','unavailable-label','acknowledge-label'],
      'O-initial':['option_a-selected','option_b-selected','acknowledge-value','error-present','summary-present','status-label','primary-label','primary-enabled','cancel-enabled'],
      'O-success':['activation-events','status-label','summary-present','summary-label'],
      'O-started-controls':['option_a-selected','option_b-selected','acknowledge-value','option_a-enabled','option_b-enabled','unavailable-enabled','acknowledge-enabled','primary-label','primary-enabled','content-complete'],
      'O-renew':['activation-events','option_a-selected','option_b-selected','acknowledge-value','error-present','summary-present','status-label','primary-label'],
      'O-rendered-colors':['canvas-color','primary-color'],
      'O-control-size':[r for r in allrules if r.endswith(('-height','-width'))],
      'O-long-content':['text-wrap'],
      'O-visual-integrity':['content-complete','content-overlap'],
      'O-route-behavior':['activation-events','replacement-events','error-present','error-label','summary-present','option_a-selected','option_b-selected','acknowledge-value']}
    states_for={'O-initial':['ready'],'O-success':['started'],'O-started-controls':['started'],'O-renew':['renewed'],
       'O-route-behavior':['validation','started','renewed','canceled','replaced']}
    ref['obligations']=[{'id':oid,'clause':next(c[1] for c in CLAUSES if c[3]==oid),'priority':'must','states':states_for.get(oid,ids),
       'risk':'layout' if oid in {'O-control-size','O-long-content','O-visual-integrity'} else 'style' if oid=='O-rendered-colors' else 'content' if oid=='O-copy' else 'behavior'} for oid in groups]
    # Every assertion must have an owner even when more focused product clauses
    # use only a subset of states. The native model route owns all native facts.
    ref['obligations'].append({'id':'O-native-state','clause':'Native labels, enabled state, selection, toggle value, conditional presence and geometry match the fixed complete per-state matrix.','priority':'must','states':ids,'risk':'behavior'})
    groups['O-native-state']=[r for r in allrules if r not in {'activation-events','replacement-events'}]
    for pl in PLATFORMS:
        ref['launch'][pl]={'fixtures_sha256':d.digest(fixtures),'bridge_sha256':sha(scope/('Bridge.swift' if pl=='ios' else 'ObserverBridge.kt')),'scenario':case,'platform':pl}
    write(scope/'reference.json',ref)
    contract={'version':1,'design_owner':OWNER,'approval_reference':'approval.json; independent preimplementation design; second-person review is a separate gate',
       'sources':[{'id':'reference','path':'reference.json','sha256':sha(scope/'reference.json')}],
       'required_rule_ids':allrules,'rules':rules,'scenarios':{case:{'states':states,'actions':actions,'values':values}}}
    write(scope/'contract.json',contract)
    lock=d.seal(scope/'contract.json',scope);lsha=d.digest(lock);write(scope/'design-lock.json',lock)
    sampling={'region':[0.01,0.01,0.03,0.99],'minimum_pixels':12,'minimum_support':0.8,'channel_tolerance':2,'basis':'semantic','visibility':'visible_fragment'}
    primary_sampling={**sampling,'region':[0.025,0.35,0.06,0.65],'basis':'control','visibility':'fully_visible'}
    policy={'version':1,'design_lock_sha256':lsha,'approval_reference':'Independent design-owner visual atom approval before implementation',
       'ownership':{'canvas':'component','primary':'component'},'atoms':[
        {'rule_id':'canvas-color','aspect':'rendered_canvas','method':'native_pixels','sampling':sampling},
        {'rule_id':'primary-color','aspect':'rendered_fill','method':'native_pixels','sampling':primary_sampling},
        *[{'rule_id':rid,'aspect':aspect,'method':'visual','question':anchor('/questions/'+key)} for rid,aspect,key in [('content-complete','content_presence','content'),('text-wrap','wrapping','wrapping'),('content-overlap','overlap','overlap')]]]}
    write(scope/'policy.json',policy)
    routes={'version':1,'index':anchor('/obligations'),'routes':{oid:{'rule_ids':rs,'reason':'Independent native state facts or separately scoped atomic image proposition establish this exact approved clause.','regression_obligations':[]} for oid,rs in groups.items()}}
    write(scope/'routes.json',routes)
    audits=[]
    for rid,text,owner,ownerid,p in CLAUSES:
        if owner=='audit': audits.append({'id':ownerid,'clause':text,'priority':'must','platforms':PLATFORMS,'expected':anchor(p)})
    for k in colors:
        audits.append({'id':'A-color-'+k,'clause':'Use the '+k+' color role exactly as specified in R17.','priority':'must','platforms':PLATFORMS,'expected':anchor('/colors/'+k)})
    for k in ['canvasPadding','blockGap','optionTextGap','cornerRadius','horizontalPadding','verticalPadding','borderWidth']:
        for pl in PLATFORMS:
            audits.append({'id':'A-space-'+k+'-'+pl,'clause':'Use '+k+' in '+pl+' at the source value and placement defined in R19.','priority':'must','platforms':[pl],'expected':anchor('/geometry/'+k+'/'+pl)})
    for k in ref['typography']:
        for pl in PLATFORMS:
            audits.append({'id':'A-font-'+k+'-'+pl,'clause':'Use scaled system '+k+' text at the base size defined in R20 on '+pl+'.','priority':'must','platforms':[pl],'expected':anchor('/typography/'+k+'/'+pl)})
        audits.append({'id':'A-weight-'+k,'clause':'Use '+k+' text at the system weight defined in R20.','priority':'must','platforms':PLATFORMS,'expected':anchor('/typography/'+k+'/weight')})
    index={'version':1,'items':audits};write(scope/'audit-index.json',index)
    ledger=[]
    for rid,text,owner,ownerid,p in CLAUSES:
        auditids=[ownerid] if owner=='audit' else []
        if rid=='R17':auditids += [a['id'] for a in audits if a['id'].startswith('A-color-')]
        if rid=='R19':auditids += [a['id'] for a in audits if a['id'].startswith('A-space-')]
        if rid=='R20':auditids += [a['id'] for a in audits if a['id'].startswith(('A-font-','A-weight-'))]
        ledger.append({'clause_id':rid,'clause':text,'responsibility':'component' if rid not in {'R16','R23','R24'} else 'integration',
          'runtime_obligation_ids':[ownerid] if owner=='runtime' else [],'source_audit_ids':auditids,
          'expected':anchor(p),'boundary':'source_only' if owner=='audit' else 'runtime_or_atomic_visual',
          'reason':'Native tools cannot establish internal source choices or universal transition semantics.' if owner=='audit' else 'Fixed input-bound state and independent original-image atoms.'})
    # Explicit owner for the complete matrix obligation supplements, rather than
    # replaces, the individual prose mappings.
    ledger_obj={'version':1,'requirements_format':'Every normative prose clause is a bracketed R identifier; API and route tables are incorporated by R02 and R24.',
       'clauses':ledger,
       'checkpoint_clauses':[{'checkpoint':sid,'clause':desc,'responsibility':'component','runtime_obligation_ids':[oid],'source_audit_ids':['A-callback-evidence'],'expected':anchor('/source/checkpoint_'+sid)} for sid,desc,oid in CHECKPOINT_CLAUSES],
       'incorporated_artifacts':[{'artifact':'api-contract.json','responsibility':'component','source_audit_ids':['A-api'],'expected':anchor('/source/api')}],
       'supplemental_obligations':{'O-native-state':{'owner_clauses':['R04','R06','R07','R10','R11','R12','R21','R26'],'expected':anchor('/source/native_matrix')}}}
    write(scope/'source-review-ledger.json',ledger_obj)
    prose = '# ListeningBreakPanel — independent product requirements\n\n'
    prose += '\n\n'.join('['+rid+'] '+text for rid,text,*_ in CLAUSES)+'\n\n'
    prose += '| Checkpoint | Stimulus and expected product state |\n|---|---|\n'
    for sid,desc,oid in CHECKPOINT_CLAUSES:
        prose += '| '+sid+' | '+desc+' |\n'
    prose += '\nPublic API signatures and exact fixed strings: [api-contract.json](api-contract.json). Independent typed design values: [reference.json](reference.json).\n'
    (scope/'requirements.md').write_text(prose)
    envs={}
    for pl in PLATFORMS:
        env={'width':width,'height':600,'direction':'ltr','theme':'light',**({'dynamic_type':dynamic_type} if pl=='ios' else {'font_scale':font_scale,'dimension_encoding':'paparazzi-float32-screen-config-v1'})}
        envs[pl]=env
        write(scope/('environment.'+pl+'.json'),env)
        acceptance.environment({},env,pl)
        bound=[{**a,**({'target':bindings[a['target']]} if 'target' in a else {})} for a in actions]
        plan,enriched=d.compile_contract(lock,lsha,case,pl,bindings,bound)
        out=scope/'compiled'/case/pl
        for n,obj in [('plan.json',plan),('actions.json',enriched)]:write(out/n,obj)
        cat=rv.catalog(plan,lock,lsha,policy,d.digest(policy),pl);write(out/'review-catalog.json',cat)
        coverage=rr.audit(lock,lsha,plan,routes,d.digest(routes));write(out/'route-coverage.json',coverage)
        assert not coverage['must_route_gaps'] and not coverage['unowned_assertions'],coverage
        execution=xp.compile_execution(plan,lock,lsha,fixtures,ref['launch'][pl]['bridge_sha256'],launch_ref=anchor('/launch/'+pl))
        write(out/'execution.json',execution)
    approval={'version':1,'approvedAtUnix':time.time(),'approvedAtUTC':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'design_owner':OWNER,
      'status':'design_owner_approved_pending_independent_second_review','design_lock_sha256':lsha,'policy_sha256':d.digest(policy),'routes_sha256':d.digest(routes),
      'environment_sha256':{case:{pl:d.digest(envs[pl]) for pl in PLATFORMS}},'production_paths':PRODUCTION,
      'audit_index_sha256':d.digest(index),'source_review_ledger_sha256':d.digest(ledger_obj),'api_contract_sha256':d.digest(API),
      'api_minimum':{'ios':'14.0','android':'upstream Reply Compose toolchain'},'cases':[case],
      'authorship':'Independent new business specification; only generic schemas/observer entry contracts and neutral format generator consulted; no implementation or previous validation business consulted.',
      'verification_limit':'No SDK/build/runtime executed. Typed schemas, source-pointer derivations, complete requirement ownership and immutable input manifests are checked here; compilation and independent second-person design review remain subsequent gates.'}
    write(scope/'approval.json',approval)

def verify_scope(scope):
    load=lambda p:d.load(scope/p)
    approval=load('approval.json');lock=load('design-lock.json');lsha=approval['design_lock_sha256']
    d.validate_lock(lock,lsha)
    for name,key in [('policy.json','policy_sha256'),('routes.json','routes_sha256'),('audit-index.json','audit_index_sha256'),('source-review-ledger.json','source_review_ledger_sha256'),('api-contract.json','api_contract_sha256')]:
        assert d.digest(load(name))==approval[key],name
    reference=load('reference.json');assert reference==lock['sources']['reference']['document']
    ledger=load('source-review-ledger.json');index=load('audit-index.json')
    prose=(scope/'requirements.md').read_text()
    found=re.findall(r'^\[(R\d+)\] (.+)$',prose,re.M)
    assert found==[(r['clause_id'],r['clause']) for r in ledger['clauses']], 'Unmapped or changed normative prose'
    assert len(found)==len(set(k for k,v in found))==len(CLAUSES)
    assert [(k,v) for k,v in found]==[(c[0],c[1]) for c in CLAUSES]
    audits={a['id']:a for a in index['items']};assert len(audits)==len(index['items'])
    obligations={o['id']:o for o in reference['obligations']}
    owned_audits=set();owned_obligations=set()
    for row in ledger['clauses']:
        assert row['runtime_obligation_ids'] or row['source_audit_ids'], 'Ownerless prose clause'
        assert set(row['runtime_obligation_ids'])<=set(obligations)
        assert set(row['source_audit_ids'])<=set(audits)
        value,proof=d.expression(row['expected'],lock['sources']);assert proof
        if row['boundary']=='source_only':assert not row['runtime_obligation_ids']
        owned_audits.update(row['source_audit_ids']);owned_obligations.update(row['runtime_obligation_ids'])
    for oid,row in ledger['supplemental_obligations'].items():
        assert oid in obligations and set(row['owner_clauses'])<=set(k for k,v in found)
        d.expression(row['expected'],lock['sources'])
        owned_obligations.add(oid)
    assert [(r['checkpoint'],r['clause'],r['runtime_obligation_ids'][0]) for r in ledger['checkpoint_clauses']]==CHECKPOINT_CLAUSES
    for row in ledger['checkpoint_clauses']:
        assert '| '+row['checkpoint']+' | '+row['clause']+' |' in prose
        assert set(row['runtime_obligation_ids'])<=set(obligations) and set(row['source_audit_ids'])<=set(audits)
        datum,_=d.expression(row['expected'],lock['sources']);assert datum==typed(row['clause'],'string')
    assert len(ledger['incorporated_artifacts'])==1
    assert d.expression(ledger['incorporated_artifacts'][0]['expected'],lock['sources'])[0]==typed(json.dumps(load('api-contract.json'),ensure_ascii=False,sort_keys=True),'string')
    assert owned_audits==set(audits), 'Orphan source audit item'
    assert owned_obligations==set(obligations), 'Orphan runtime obligation'
    for a in audits.values():
        assert set(a)=={'id','clause','priority','platforms','expected'}
        assert a['clause'].strip() and a['priority'] in {'must','advisory'} and a['platforms'] and set(a['platforms'])<=set(PLATFORMS)
        d.expression(a['expected'],lock['sources'])
    assert approval['production_paths']==PRODUCTION
    assert len(lock['contract']['scenarios'])==1
    count=0
    for case in approval['cases']:
        scenario=lock['contract']['scenarios'][case]
        assert 1<=len(scenario['states'])<=6
        fixtures=load('cases/'+case+'/fixtures.json')
        assert fixtures['initial']==reference['inputs']['initial'] and fixtures['updates']==[reference['inputs']['replacement']]
        assert fixtures['initial']['sessionID']==fixtures['updates'][0]['sessionID']
        assert fixtures['initial']!=fixtures['updates'][0]
        for pl in PLATFORMS:
            env=load('environment.'+pl+'.json');assert d.digest(env)==approval['environment_sha256'][case][pl]
            acceptance.environment({},env,pl)
            plan=load('compiled/'+case+'/'+pl+'/plan.json')
            actions=d.verify_generated(plan,lock,lsha,pl)
            coverage=rr.audit(lock,lsha,plan,load('routes.json'),approval['routes_sha256'])
            assert not coverage['must_route_gaps'] and not coverage['unowned_assertions']
            cat=rv.catalog(plan,lock,lsha,load('policy.json'),approval['policy_sha256'],pl)
            assert cat==load('compiled/'+case+'/'+pl+'/review-catalog.json')
            bridge=scope/('Bridge.swift' if pl=='ios' else 'ObserverBridge.kt')
            execution=load('compiled/'+case+'/'+pl+'/execution.json')
            xp.verify_execution(execution,plan,lock,lsha,fixtures,sha(bridge))
            assert actions==load('compiled/'+case+'/'+pl+'/actions.json')
            assert len({a['requirement_id'] for a in plan['assertions']})==len(lock['contract']['rules']), 'No all-N/A or ownerless rule allowed'
            assert set(a['aspect'] for a in load('policy.json')['atoms'])=={'rendered_canvas','rendered_fill','content_presence','wrapping','overlap'}
            for a in plan['assertions']:
                if a['kind']=='event':assert a.get('stimulus') in {'activation','caller_update'}
            count+=len(plan['assertions'])
    return {'scope':scope.name,'clauses':len(found),'source_audits':len(audits),'runtime_obligations':len(obligations),'rules':len(lock['contract']['rules']),'platform_assertions':count,'semantic_ownership':'complete','native_sdk_invoked':False}

def seal_directory(path, scope):
    # The seal excludes only itself; all generated and authoring bytes are pinned.
    manifest={str(p.relative_to(path)):sha(p) for p in sorted(path.rglob('*')) if p.is_file() and p.name!='SEAL.json' and '__pycache__' not in p.parts}
    if path==ROOT:
        for child in ['public','private']: manifest[child+'/SEAL.json']=sha(path/child/'SEAL.json')
    write(path/'SEAL.json',{'version':1,'sealedAtUnix':time.time(),'sealedAtUTC':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'scope':scope,'files':manifest,'manifest_sha256':d.digest(manifest),'purpose':'Preimplementation independent design identity; no runtime correctness or human-gold claim.'})

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--seal',action='store_true');ap.add_argument('--verify-only',action='store_true');args=ap.parse_args()
    if not args.verify_only:
        if (ROOT/'SEAL.json').exists():raise ValueError('Design root already sealed')
        for name in ['public','private']:build_scope(name)
    reports=[verify_scope(ROOT/n) for n in ['public','private']]
    if not args.verify_only:write(ROOT/'semantic-self-check.json',{'version':1,'checkedAtUnix':time.time(),'checks':reports,'result':'passed',
      'semantic_review':[
       {'topic':'business completeness','result':'passed','basis':'R03-R16 and R27 define input domain, selection, every validation case, success, renewed editing, Cancel, equal/unequal replacement and all callback boundaries; none is a hidden-only semantic.'},
       {'topic':'public API','result':'passed','basis':'Exact models/signatures and fixed copy are pinned by api-contract.json plus source/api; the caller bridges contain only decoding and real callback forwarding, with no remount or local product state.'},
       {'topic':'typed coverage','result':'passed','basis':'Every prose clause and checkpoint sentence has responsibility and source pointer; every runtime obligation and source audit has a prose owner; every rule has applicable cells and obligation ownership.'},
       {'topic':'observability','result':'passed','basis':'Native runtime rules are labels, selection, enabled state, switch Boolean, conditional presence, native rectangles and dispatch-qualified callback intervals; computed font/padding are source-only.'},
       {'topic':'atomic review','result':'passed','basis':'Rendered canvas, rendered primary fill, content presence, wrapping and overlap are separate atoms; pixel policy has explicit original-image regions and channel tolerance.'},
       {'topic':'new data/environment','result':'passed','basis':'Both routes have the same six checkpoint semantics and are inside the public width/text-size domain. Long data changes no public behavior or oracle definition.'}],
      'scope':'Exact prose ownership, typed source pointers, schema, matrix, routes, environments and launch manifests; manual semantic self-review by the design author; no SDK or independent second-person approval.'})
    if args.seal:
        for n in ['public','private']:seal_directory(ROOT/n,n+' independent design')
        seal_directory(ROOT,'complete independent public/private design inputs and authoring scripts')
    print(json.dumps({'result':'passed','scopes':reports,'sealed':args.seal},ensure_ascii=False))

if __name__=='__main__':main()
