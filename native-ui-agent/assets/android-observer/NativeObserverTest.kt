package org.nativeobserver

import android.view.View
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.ScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.*
import androidx.compose.ui.semantics.*
import androidx.compose.ui.state.ToggleableState
import androidx.compose.ui.text.TextLayoutResult
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import app.cash.paparazzi.*
import com.android.resources.NightMode

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import java.io.File
import java.awt.image.BufferedImage
import javax.imageio.ImageIO
import kotlinx.serialization.json.*
import org.junit.Rule
import org.junit.Test

class NativeObserverTest {
 private val output=File(requireNotNull(System.getenv("NATIVE_UI_OUTPUT")))
 private val fixture=Json.parseToJsonElement(File(requireNotNull(System.getenv("BENCH_FIXTURE"))).readText()).jsonObject
 private val environment=fixture
 private fun string(o:JsonObject,k:String)=o[k]!!.jsonPrimitive.content
 private fun optional(o:JsonObject,k:String)=o[k]?.jsonPrimitive?.contentOrNull
 private var current by mutableStateOf(fixture["initial"]!!.jsonObject)
 private var inputIndex=0
 private val session=java.util.UUID.randomUUID().toString()
 private fun binding()=buildJsonObject{put("fixture_index",inputIndex);put("event_revision",events.size);put("instance",session);put("input_sha256",java.security.MessageDigest.getInstance("SHA-256").digest(current.toString().toByteArray()).joinToString(""){"%02x".format(it)})}
 private val actions=fixture["actions"]?.jsonArray?.map{it.jsonObject} ?: emptyList()
 private val events=mutableListOf<String>()
 private val records=mutableListOf<JsonObject>()
 private val steps=mutableListOf<JsonObject>()
 private lateinit var view:ComposeView
 private lateinit var scroll:ScrollState
 private var density=1f
 private var viewportHeight=0f
 private var frame=0
 private var actionIndex=0
 private var phase="sweep_top"
 private var activeState="initial"
 private var activeAfterAction=-1
 private var stateFirst=0
 private var stateOriginal=JsonObject(emptyMap())
 private var sweepPurpose="initial"
 private var sweepLimit=80
 private var sweepCount=0
 private val stateCaptures=mutableListOf<JsonObject>()
 private var preparedUpdate=-1
 private var finalCaptured=false
 private val stateCapture=fixture["state_capture"]?.jsonPrimitive?.booleanOrNull ?: true
 private var attempts=0
 private var pendingName="initial"
 private var pendingStep:JsonObject?=null
 private var eventStart=0
 private var dispatch=JsonObject(emptyMap())
 private var afterBinding:JsonObject?=null
 private var afterDelta:List<String> = emptyList()
 private var immediateSnapshot=-1
 private var postAttempts=0
 private val postTrace=mutableListOf<JsonObject>()
 private var postTargetIndex=0
 private var postDirection=0
 private var postReversed=false
 private var postTargets=emptyList<JsonObject>()
 private val postIndices=mutableListOf<Int>()
 private class ObservationComplete:RuntimeException()
 private val observed=mutableSetOf<String>()
 private var bottomReached=false
 private var actualNight=-1
 private var actualScale=0f
 private var actualDirection=""
 private fun number(k:String,default:Float)=environment[k]?.jsonPrimitive?.floatOrNull ?: default
 private val dark=optional(environment,"theme")=="dark"
 private fun nodes(n:SemanticsNode):List<SemanticsNode> = listOf(n)+n.children.flatMap{nodes(it)}
 private fun raw()=nodes((view.getChildAt(0) as ViewRootForTest).semanticsOwner.unmergedRootSemanticsNode)
 private fun rawBounds(n:SemanticsNode):androidx.compose.ui.geometry.Rect {val p=n.positionInRoot;return androidx.compose.ui.geometry.Rect(p.x,p.y,p.x+n.size.width,p.y+n.size.height)}
 private fun visible(n:SemanticsNode)=rawBounds(n).let{it.bottom>0 && it.top<viewportHeight && it.right>0 && it.left<view.width && it.width>0 && it.height>0}
 private fun fullyVisible(n:SemanticsNode)=rawBounds(n).let{it.top>=-0.5f && it.bottom<=viewportHeight+0.5f && it.left>=-0.5f && it.right<=view.width+0.5f && it.width>0 && it.height>0}
 private fun tag(n:SemanticsNode)=n.config.getOrNull(SemanticsProperties.TestTag) ?: ""
 private fun capture(name:String,image:BufferedImage){
  val captureStart=System.nanoTime()
  val originalBinding=binding()
  val all=raw(); val imageName="${records.size.toString().padStart(3,'0')}-$name.png"
  ImageIO.write(image,"png",File(output,imageName))
  all.filter{visible(it)}.map{tag(it)}.filter{it.isNotBlank()}.forEach{observed.add(it)}
  bottomReached=bottomReached || all.any{tag(it)=="__observer.bottom" && fullyVisible(it)}
  records.add(buildJsonObject{
   put("binding",originalBinding);put("runtime",originalBinding);put("state_id",activeState)
   put("screenshot_pixels",buildJsonObject{put("width",image.width);put("height",image.height)});put("logical_viewport_dp",buildJsonObject{put("width",view.width/density);put("height",view.height/density)});put("name",name);put("screenshot",imageName);put("frame",frame);put("scroll_offset_dp",scroll.value/density)
   put("scroll_max_dp",scroll.maxValue/density);put("viewport_height_dp",viewportHeight/density)
   put("nodes",buildJsonArray{all.forEach{node->
    val c=node.config;val layouts=mutableListOf<TextLayoutResult>();c.getOrNull(SemanticsActions.GetTextLayoutResult)?.action?.invoke(layouts)
    add(buildJsonObject{
     put("node_id",node.id);put("parent_id",node.parent?.id ?: -1);put("identifier",tag(node))
     put("label",label(node));put("native_text",c.getOrNull(SemanticsProperties.Text)?.joinToString{it.text} ?: "");put("label_source","own native text/description, otherwise descendant native Text aggregation")
     put("content_description",c.getOrNull(SemanticsProperties.ContentDescription)?.joinToString() ?: "")
     put("enabled",!c.contains(SemanticsProperties.Disabled));put("selected",c.getOrNull(SemanticsProperties.Selected) ?: false)
     put("toggle_state",c.getOrNull(SemanticsProperties.ToggleableState)?.toString() ?: "")
     put("role",c.getOrNull(SemanticsProperties.Role)?.toString() ?: "");put("clickable",c.getOrNull(SemanticsActions.OnClick)?.action!=null)
     put("intersects_viewport",visible(node));put("fully_visible",fullyVisible(node))
     fun bounds(r:androidx.compose.ui.geometry.Rect)=buildJsonArray{add(r.left/density);add(r.top/density);add(r.right/density);add(r.bottom/density)}
     put("image_bounds_px",buildJsonArray{val r=rawBounds(node);val sx=image.width/(view.width/density);val sy=image.height/(view.height/density);add(r.left/density*sx);add(r.top/density*sy);add(r.right/density*sx);add(r.bottom/density*sy)});put("unclipped_bounds_dp",bounds(rawBounds(node)));put("bounds_dp",bounds(node.boundsInRoot));put("touch_bounds_dp",bounds(node.touchBoundsInRoot))
     layouts.firstOrNull()?.let{t->
      if(t.layoutInput.style.fontSize.value.isFinite())put("font_sp",t.layoutInput.style.fontSize.value)
      put("font_weight",t.layoutInput.style.fontWeight?.weight ?: -1)
      runCatching{t.layoutInput.style.color.toArgb().toLong() and 0xffffffffL}.getOrNull()?.let{put("color_argb",it)}
      put("lines",t.lineCount);put("overflow",t.hasVisualOverflow);put("ellipsized",(0 until t.lineCount).any{t.isLineEllipsized(it)})
     }
    })
   }})
   put("events",buildJsonArray{events.forEach{add(it)}})
   put("binding_after_capture",binding());put("capture_consistent",binding()==originalBinding)
   put("capture_seconds",(System.nanoTime()-captureStart)/1_000_000_000.0)
  })
 }
 private fun scrollBy(delta:Float){scroll.dispatchRawDelta(delta)}
 private fun label(n:SemanticsNode):String=n.config.getOrNull(SemanticsProperties.ContentDescription)?.joinToString() ?: n.config.getOrNull(SemanticsProperties.Text)?.joinToString{it.text} ?: n.children.flatMap{nodes(it)}.mapNotNull{it.config.getOrNull(SemanticsProperties.Text)?.joinToString{x->x.text}}.joinToString(", ")
 private fun select(spec:JsonObject)=raw().filter{n->
  val id=optional(spec,"identifier");val text=optional(spec,"label");val role=optional(spec,"role")
  (if(id!=null)tag(n)==id else text!=null && label(n)==text) && (role==null || n.config.getOrNull(SemanticsProperties.Role)?.toString()?.equals(role,true)==true || (role.equals("text",true) || role.equals("statictext",true)) && n.config.getOrNull(SemanticsProperties.Text)!=null)
 }
 private fun leaves(n:SemanticsNode):List<SemanticsNode>{
  return nodes(n).filter{it.config.getOrNull(SemanticsActions.OnClick)?.action!=null}
 }
 private fun targetReady(n:SemanticsNode):Boolean{
  val b=rawBounds(n)
  return if(b.height<=viewportHeight && b.width<=view.width)fullyVisible(n)else visible(n) && b.center.y in 0f..viewportHeight && b.center.x in 0f..view.width.toFloat()
 }
 private var postOrder=mutableListOf<Int>()
 private fun targetEvidence(spec:JsonObject):JsonObject{
  val observed=mutableListOf<Int>();val full=mutableListOf<Int>();var ambiguous=false
  for(index in postIndices){
   val s=records[index]
   if(s["binding"]!=afterBinding || s["capture_consistent"]?.jsonPrimitive?.booleanOrNull==false)continue
   val found=s["nodes"]!!.jsonArray.map{it.jsonObject}.filter{n->
    val id=optional(spec,"identifier");val text=optional(spec,"label");val role=optional(spec,"role")
    (if(id!=null)optional(n,"identifier")==id else text!=null && optional(n,"label")==text) && (role==null || optional(n,"role")?.equals(role,true)==true || (role.equals("text",true) || role.equals("statictext",true)) && !optional(n,"native_text").isNullOrEmpty())
   }
   if(found.size!=1){ambiguous=ambiguous || found.size>1;continue}
   val n=found.single();val bounds=n["unclipped_bounds_dp"]!!.jsonArray.map{it.jsonPrimitive.float};val w=s["logical_viewport_dp"]!!.jsonObject["width"]!!.jsonPrimitive.float;val h=s["logical_viewport_dp"]!!.jsonObject["height"]!!.jsonPrimitive.float
   if(n["fully_visible"]?.jsonPrimitive?.booleanOrNull==true){observed.add(index);full.add(index)}
   else if(n["intersects_viewport"]?.jsonPrimitive?.booleanOrNull==true && (bounds[2]-bounds[0]>w || bounds[3]-bounds[1]>h) && (bounds[0]+bounds[2])/2 in 0f..w && (bounds[1]+bounds[3])/2 in 0f..h)observed.add(index)
  }
  return buildJsonObject{put("selector",spec);put("status",if(observed.isEmpty())"unavailable"else"observed");put("snapshot_indices",buildJsonArray{observed.forEach{add(it)}});put("fully_visible",full.isNotEmpty());put("fully_visible_snapshot_indices",buildJsonArray{full.forEach{add(it)}});put("reason",if(observed.isNotEmpty())"original_native_target_frames"else if(ambiguous)"ambiguous_native_target"else"no_unique_visible_target_frame")}
 }
 private fun startSweep(id:String,after:Int,purpose:String,limit:Int=80){activeState=id;activeAfterAction=after;sweepPurpose=purpose;sweepLimit=limit.coerceIn(1,80);sweepCount=0;phase="sweep_top"}
 private fun finishSweep(){
  val samples=records.drop(stateFirst);val heights=samples.map{it["scroll_max_dp"]!!.jsonPrimitive.float+it["viewport_height_dp"]!!.jsonPrimitive.float}
  val intervals=samples.map{val a=it["scroll_offset_dp"]!!.jsonPrimitive.float;a to a+it["viewport_height_dp"]!!.jsonPrimitive.float}.sortedBy{it.first}
  var end=0f;var gap=0f;for((a,b)in intervals){gap=maxOf(gap,a-end);end=maxOf(end,b)}
  val stable=samples.all{it["binding"]==stateOriginal};val top=samples.any{it["scroll_offset_dp"]!!.jsonPrimitive.float<=0.5f};val bottom=samples.any{it["scroll_offset_dp"]!!.jsonPrimitive.float>=it["scroll_max_dp"]!!.jsonPrimitive.float-0.5f}
  stateCaptures.add(buildJsonObject{put("state_id",activeState);put("after_action",activeAfterAction);put("binding",stateOriginal);put("snapshot_indices",buildJsonArray{(stateFirst until records.size).forEach{add(it)}});put("top_reached",top);put("bottom_reached",bottom);put("stable_binding",stable);put("max_gap",gap);put("complete",top && bottom && stable && gap<=1 && (heights.maxOrNull() ?: 0f)-(heights.minOrNull() ?: 0f)<=1)})
  if(sweepPurpose=="final"){phase="complete"}else{phase="actions"}
 }
 private fun advance(image:BufferedImage){
  if(frame++ % 2!=0 || phase=="complete")return
  if(phase=="sweep_top"){scrollBy(-scroll.value.toFloat());stateFirst=records.size;stateOriginal=binding();phase="sweeping";return}
  if(phase=="sweeping"){
   capture("state_${activeState}_${sweepCount}",image)
   if(scroll.value>=scroll.maxValue || sweepCount++>=sweepLimit){finishSweep();return}
   scrollBy(viewportHeight*0.45f);return
  }
  if(phase=="after_action"){
   val action=actions[actionIndex]
   if(afterBinding==null){
    capture(pendingName,image);immediateSnapshot=records.lastIndex;afterBinding=binding();afterDelta=events.drop(eventStart).toList();postIndices.add(immediateSnapshot)
    postTargets=if(action["observe_after"]?.jsonPrimitive?.booleanOrNull==false)emptyList()else action["after_targets"]?.jsonArray?.map{it.jsonObject} ?: if(optional(action,"type")=="tap")listOf(action["after_target"]?.jsonObject ?: action["target"]?.jsonObject ?: buildJsonObject{put("identifier",optional(action,"identifier") ?: "")})else emptyList()
   }
   if(postOrder.isEmpty())postOrder=postTargets.indices.toMutableList()
   val needsImage=postTrace.isNotEmpty() && postTargets.any{spec->targetEvidence(spec)["status"]!!.jsonPrimitive.content!="observed" && select(spec).singleOrNull()?.let{targetReady(it)}==true}
   if(needsImage){capture(pendingName+"-post-target-"+postTargetIndex,image);postIndices.add(records.lastIndex)}
   val limit=(action["observation_max_scrolls"]?.jsonPrimitive?.intOrNull ?: 24).coerceIn(0,40)
   while(postTargetIndex<postTargets.size && binding()==afterBinding){
    // Reuse each coherent frame for all targets and visit the nearest unseen
    // native box. Keep requested_targets in original order for audit/replay.
    val next=(postTargetIndex until postOrder.size).minByOrNull{position->
     val spec=postTargets[postOrder[position]]
     if(targetEvidence(spec)["status"]!!.jsonPrimitive.content=="observed")-1f
     else select(spec).singleOrNull()?.let{kotlin.math.abs(rawBounds(it).center.y-viewportHeight/2)} ?: Float.MAX_VALUE
    } ?: postTargetIndex
    val selectedOrder=postOrder[next];postOrder[next]=postOrder[postTargetIndex];postOrder[postTargetIndex]=selectedOrder
    val wanted=postTargets[selectedOrder];val found=select(wanted);val target=found.singleOrNull()
    if(targetEvidence(wanted)["status"]!!.jsonPrimitive.content=="observed" || found.size>1 || postAttempts>=limit){postTargetIndex++;postDirection=0;postReversed=false;continue}
    if(target?.let{targetReady(it)}==true){capture(pendingName+"-post-target-"+postTargetIndex,image);postIndices.add(records.lastIndex);postTargetIndex++;postDirection=0;postReversed=false;continue}
    if(postDirection==0)postDirection=if(scroll.value>0)-1 else 1
    val b=target?.let{rawBounds(it)};val previous=scroll.value
    val delta=if(b!=null)(b.center.y-viewportHeight/2).coerceIn(-viewportHeight*0.65f,viewportHeight*0.65f)else viewportHeight*0.45f*postDirection
    scrollBy(delta);postAttempts++
    postTrace.add(buildJsonObject{put("selector",wanted);put("step",postAttempts);put("offset_before",previous/density);put("offset_after",scroll.value/density);put("target_observed",target!=null)})
    if(scroll.value!=previous)return
    if(target==null && !postReversed){postDirection = -postDirection;postReversed=true}else{postTargetIndex++;postDirection=0;postReversed=false}
   }
   val item=pendingStep!!;val finished=actionIndex
   val results=postTargets.map{targetEvidence(it)};val stable=binding()==afterBinding && postIndices.all{records[it]["binding"]==afterBinding && records[it]["capture_consistent"]?.jsonPrimitive?.booleanOrNull!=false}
   val observationSet=if(postTargets.isEmpty())JsonObject(emptyMap())else buildJsonObject{put("state_id",activeState);put("after_action",actionIndex);put("binding",afterBinding!!);put("binding_after_observation",binding());put("binding_stable",stable);put("snapshot_indices",buildJsonArray{postIndices.forEach{add(it)}});put("requested_targets",JsonArray(postTargets));put("targets",JsonArray(results));put("all_targets_observed",stable && results.all{it["status"]!!.jsonPrimitive.content=="observed"});put("scroll_budget",limit);put("scrolls_used",postAttempts);put("trace",JsonArray(postTrace));put("scope","targets_only; never full-content or absence proof")}
   steps.add(buildJsonObject{item.forEach{(k,v)->put(k,v)};put("dispatch",buildJsonObject{dispatch.forEach{(k,v)->put(k,v)};put("event_end",afterBinding!!["event_revision"]!!)});put("callback_delta",buildJsonArray{afterDelta.forEach{add(it)}});put("snapshot",records.lastIndex);put("immediate_after",immediateSnapshot);put("binding_after",afterBinding!!);put("state_id",activeState)
    put("observation_set",observationSet);put("post_action_viewport",buildJsonObject{val first=results.firstOrNull();if(first!=null)first.forEach{(k,v)->put(k,v)}else put("status","not_requested");put("snapshot",first?.get("snapshot_indices")?.jsonArray?.firstOrNull() ?: JsonPrimitive(records.lastIndex));put("binding_stable",stable)})})
   afterBinding=null;postAttempts=0;postTrace.clear();postIndices.clear();postTargets=emptyList();postOrder.clear();postTargetIndex=0;postDirection=0;postReversed=false
   val state=optional(actions[finished],"state_id");actionIndex++;attempts=0
   if(stateCapture && state!=null)startSweep(state,finished,"after")else phase="actions"
   return
  }
  if(actionIndex>=actions.size){if(!finalCaptured){finalCaptured=true;startSweep("final",actionIndex-1,"final")}else phase="complete";return}
  val action=actions[actionIndex];val type=string(action,"type")
  if(type=="apply_next_fixture" && stateCapture && preparedUpdate!=actionIndex){preparedUpdate=actionIndex;startSweep("before-update-$actionIndex",actionIndex-1,"before");return}
  eventStart=events.size;pendingName=optional(action,"name") ?: "action-$actionIndex";activeState=optional(action,"state_id") ?: "action-$actionIndex"
  dispatch=buildJsonObject{put("attempted",false);put("succeeded",false)}
  if(type=="sweep"){val state=optional(action,"state_id") ?: "action-$actionIndex";val n=action["max_steps"]?.jsonPrimitive?.intOrNull ?: 80;steps.add(buildJsonObject{put("type",type);put("outcome","observed");put("callback_delta",JsonArray(emptyList()));put("binding_after",binding())});actionIndex++;startSweep(state,actionIndex-1,"explicit",n);return}
  if(type=="capture" || type=="checkpoint"){pendingStep=buildJsonObject{put("type",type);put("outcome","observed")};phase="after_action";return}
  if(type=="scroll"){scrollBy(viewportHeight*(if(optional(action,"direction")=="up")-0.45f else 0.45f));pendingStep=buildJsonObject{put("type",type);put("outcome","observed")};phase="after_action";return}
  if(type=="apply_next_fixture"){
   val before=binding();inputIndex++;current=fixture["updates"]!!.jsonArray[inputIndex-1].jsonObject;dispatch=buildJsonObject{put("attempted",true);put("succeeded",true);put("method","caller_fixture_update");put("stimulus","caller_update");put("binding_before",before);put("event_start",eventStart)};pendingStep=buildJsonObject{put("type",type);put("outcome","updated");put("model_update",true)};phase="after_action";return
  }
  if(type=="tap" || type=="scroll_until"){
   val wanted=action["target"]?.jsonObject ?: buildJsonObject{put("identifier",optional(action,"identifier") ?: "")}
   val matches=select(wanted);val node=matches.singleOrNull();val controls=node?.let{leaves(it)} ?: emptyList();val target=controls.singleOrNull()
   if(node==null && matches.isEmpty() && scroll.value<scroll.maxValue && attempts++<40){scrollBy(viewportHeight*0.45f);return}
   val revealNode=if(type=="scroll_until")node else target
   if(revealNode!=null && !visible(revealNode) && attempts++<40){val b=rawBounds(revealNode);scrollBy((b.center.y-viewportHeight/2).coerceIn(-viewportHeight*0.65f,viewportHeight*0.65f));return}
   val enabled=target?.let{!it.config.contains(SemanticsProperties.Disabled)} ?: false
   val before=binding();val attempted=type=="tap" && enabled && target!=null && visible(target)
   val executed=if(attempted)target!!.config.getOrNull(SemanticsActions.OnClick)?.action?.invoke() ?: false else false
   dispatch=buildJsonObject{put("attempted",attempted);put("succeeded",executed);put("method","compose_onclick");put("stimulus","activation");put("binding_before",before);put("event_start",eventStart);put("matches",matches.size);put("native_controls",controls.size);put("enabled",enabled)}
   pendingStep=buildJsonObject{put("type",type);put("selector",wanted);put("matches",matches.size);put("native_controls",controls.size);put("enabled",enabled);put("outcome",if(executed)"tapped"else if(type=="scroll_until" && node!=null && visible(node))"observed"else if(target!=null && !enabled && visible(target) && action["allow_disabled"]?.jsonPrimitive?.booleanOrNull==true)"blocked_disabled"else"unavailable");put("semantic_node",node?.id ?: -1);put("activation_node",target?.id ?: -1)}
   phase="after_action";return
  }
  pendingStep=buildJsonObject{put("type",type);put("outcome","unsupported")};phase="after_action"
 }
 @get:Rule val paparazzi=Paparazzi(deviceConfig=DeviceConfig.PIXEL_5.copy(screenWidth=(number("width",390f)*2.75f).toInt(),screenHeight=(number("viewportHeight",600f)*2.75f).toInt(),nightMode=if(dark)NightMode.NIGHT else NightMode.NOTNIGHT,fontScale=number("fontScale",1f),softButtons=false),showSystemUi=false,
  snapshotHandler=object:SnapshotHandler{override fun close(){};override fun newFrameHandler(snapshot:Snapshot,frameCount:Int,fps:Int)=object:SnapshotHandler.FrameHandler{override fun close(){};override fun handle(image:BufferedImage){advance(image);if(phase=="complete")throw ObservationComplete()}}})
 @Test fun capture(){
  output.mkdirs();view=ComposeView(paparazzi.context)
  val preview=object:View(paparazzi.context){override fun isInEditMode()=true}
  view.setContent{
   density=LocalDensity.current.density;actualScale=LocalDensity.current.fontScale
   actualNight=LocalConfiguration.current.uiMode and android.content.res.Configuration.UI_MODE_NIGHT_MASK
   scroll=rememberScrollState();viewportHeight=number("viewportHeight",600f)*density
   val direction=if(optional(environment,"direction")=="rtl")LayoutDirection.Rtl else LayoutDirection.Ltr
   actualDirection=direction.toString()
   CompositionLocalProvider(LocalInspectionMode provides true,LocalView provides preview,LocalLayoutDirection provides direction){
    MaterialTheme(colorScheme=if(dark)darkColorScheme()else lightColorScheme()){
     Column(Modifier.fillMaxSize().background(if(dark)Color(0xFF0D1420)else Color(0xFFEDF1F6)).verticalScroll(scroll).padding(horizontal=16.dp).padding(top=24.dp,bottom=24.dp)){
      ObserverBridge.Content(current){event->events.add(event)}
      Text("End of observed component",Modifier.semantics{testTag="__observer.bottom"})
     }
    }
   }
  }
  try{paparazzi.gif(view,"session",0L,600_000L,4)}catch(done:ObservationComplete){check(phase=="complete")}
  File(output,"observation.json").writeText(buildJsonObject{
   put("schema_version",3);put("state_captures",JsonArray(stateCaptures));put("native_test","NativeObserverTest.capture");put("phase",phase);put("rendered_frames",frame);put("completion_stop","native_state_machine_complete");put("snapshots",JsonArray(records));put("steps",JsonArray(steps));put("events",buildJsonArray{events.forEach{add(it)}})
   put("coverage",buildJsonObject{put("bottom_reached",bottomReached);put("observed_identifiers",buildJsonArray{observed.sorted().forEach{add(it)}})})
   put("configuration",buildJsonObject{put("night_mode_mask",actualNight);put("font_scale",actualScale);put("density",density);put("direction",actualDirection)})
   put("scope","One attached native ComposeView in continuous Paparazzi frame session. Semantic OnClick invocation, not physical touch; native parent ScrollState displacement, not OS gestures. No Activity/navigation/lifecycle claims.")
  }.toString())
  check(phase=="complete"){"Observation frame budget exhausted"}
 }
}
