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
 private var phase="initial"
 private var attempts=0
 private var pendingName="initial"
 private var pendingStep:JsonObject?=null
 private var eventStart=0
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
 private fun visible(n:SemanticsNode)=rawBounds(n).bottom>0 && rawBounds(n).top<viewportHeight && rawBounds(n).width>0
 private fun fullyVisible(n:SemanticsNode)=rawBounds(n).top>=-0.5f && rawBounds(n).bottom<=viewportHeight+0.5f && rawBounds(n).width>0
 private fun tag(n:SemanticsNode)=n.config.getOrNull(SemanticsProperties.TestTag) ?: ""
 private fun capture(name:String,image:BufferedImage){
  val all=raw(); val imageName="${records.size.toString().padStart(3,'0')}-$name.png"
  ImageIO.write(image,"png",File(output,imageName))
  all.filter{visible(it)}.map{tag(it)}.filter{it.isNotBlank()}.forEach{observed.add(it)}
  bottomReached=bottomReached || all.any{tag(it)=="__observer.bottom" && fullyVisible(it)}
  records.add(buildJsonObject{
   put("binding",binding());put("runtime",binding());put("state_id",pendingName)
   put("screenshot_pixels",buildJsonObject{put("width",image.width);put("height",image.height)});put("logical_viewport_dp",buildJsonObject{put("width",view.width/density);put("height",view.height/density)});put("name",name);put("screenshot",imageName);put("frame",frame);put("scroll_offset_dp",scroll.value/density)
   put("scroll_max_dp",scroll.maxValue/density);put("viewport_height_dp",viewportHeight/density)
   put("nodes",buildJsonArray{all.forEach{node->
    val c=node.config;val layouts=mutableListOf<TextLayoutResult>();c.getOrNull(SemanticsActions.GetTextLayoutResult)?.action?.invoke(layouts)
    add(buildJsonObject{
     put("node_id",node.id);put("parent_id",node.parent?.id ?: -1);put("identifier",tag(node))
     put("label",c.getOrNull(SemanticsProperties.Text)?.joinToString{it.text} ?: "")
     put("content_description",c.getOrNull(SemanticsProperties.ContentDescription)?.joinToString() ?: "")
     put("enabled",!c.contains(SemanticsProperties.Disabled));put("selected",c.getOrNull(SemanticsProperties.Selected) ?: false)
     put("toggle_state",c.getOrNull(SemanticsProperties.ToggleableState)?.toString() ?: "")
     put("role",c.getOrNull(SemanticsProperties.Role)?.toString() ?: "");put("clickable",c.getOrNull(SemanticsActions.OnClick)?.action!=null)
     put("intersects_viewport",visible(node));put("fully_visible",fullyVisible(node))
     fun bounds(r:androidx.compose.ui.geometry.Rect)=buildJsonArray{add(r.left/density);add(r.top/density);add(r.right/density);add(r.bottom/density)}
     put("image_bounds_px",buildJsonArray{val r=rawBounds(node);val sx=image.width/(view.width/density);val sy=image.height/(view.height/density);add(r.left*sx);add(r.top*sy);add(r.right*sx);add(r.bottom*sy)});put("unclipped_bounds_dp",bounds(rawBounds(node)));put("bounds_dp",bounds(node.boundsInRoot));put("touch_bounds_dp",bounds(node.touchBoundsInRoot))
     layouts.firstOrNull()?.let{t->
      if(t.layoutInput.style.fontSize.value.isFinite())put("font_sp",t.layoutInput.style.fontSize.value)
      put("font_weight",t.layoutInput.style.fontWeight?.weight ?: -1)
      runCatching{t.layoutInput.style.color.toArgb().toLong() and 0xffffffffL}.getOrNull()?.let{put("color_argb",it)}
      put("lines",t.lineCount);put("overflow",t.hasVisualOverflow);put("ellipsized",(0 until t.lineCount).any{t.isLineEllipsized(it)})
     }
    })
   }})
   put("events",buildJsonArray{events.forEach{add(it)}})
  })
 }
 private fun scrollBy(delta:Float){scroll.dispatchRawDelta(delta)}
 private fun advance(image:BufferedImage){
  if(frame++ % 8!=0 || phase=="complete")return
  if(phase=="initial"){capture("initial",image);phase="sweep";attempts=0;return}
  if(phase=="sweep"){
   capture("scroll_${attempts}",image)
   if(scroll.value>=scroll.maxValue || attempts++>=45){scrollBy(-scroll.value.toFloat());phase="actions";return}
   scrollBy(viewportHeight*0.45f);return
  }
  if(phase=="after_action"){
   capture(pendingName,image)
   val item=pendingStep!!
   steps.add(buildJsonObject{item.forEach{(k,v)->put(k,v)};put("callback_delta",buildJsonArray{events.drop(eventStart).forEach{add(it)}});put("snapshot",records.lastIndex);put("binding_after",binding())})
   actionIndex++;phase="actions";attempts=0;return
  }
  if(actionIndex>=actions.size){capture("final",image);phase="complete";return}
  val action=actions[actionIndex];val type=string(action,"type")
  eventStart=events.size;pendingName=optional(action,"checkpoint") ?: "after_$actionIndex"
  if(type=="capture"){pendingStep=buildJsonObject{put("type",type);put("execution","observed")};phase="after_action";return}
  if(type=="scroll"){scrollBy(viewportHeight*0.45f);pendingStep=buildJsonObject{put("type",type);put("execution","observed")};phase="after_action";return}
  if(type=="apply_next_fixture"){
   inputIndex++;current=fixture["updates"]!!.jsonArray[inputIndex-1].jsonObject;pendingStep=buildJsonObject{put("type",type);put("execution","observed");put("model_update",true)};phase="after_action";return
  }
  if(type=="tap" || type=="scroll_until"){
   val id=string(action,"identifier");val matches=raw().filter{tag(it)==id};val node=matches.singleOrNull()
   if(node!=null && !fullyVisible(node) && attempts++<45){scrollBy(if(rawBounds(node).top<0)-viewportHeight*0.45f else viewportHeight*0.45f);return}
   val enabled=node?.let{!it.config.contains(SemanticsProperties.Disabled)} ?: false
   val target=node?.let{n->(listOf(n)+nodes(n)).firstOrNull{it.config.getOrNull(SemanticsActions.OnClick)?.action!=null}}
   val executed=if(type=="tap" && enabled && node!=null && fullyVisible(node))target?.config?.getOrNull(SemanticsActions.OnClick)?.action?.invoke() ?: false else false
   pendingStep=buildJsonObject{put("type",type);put("identifier",id);put("matches",matches.size);put("enabled",enabled);put("execution",if(executed || type=="scroll_until" && node!=null && fullyVisible(node))"observed" else if(node!=null && !enabled)"blocked_disabled" else "not_executed")}
   phase="after_action";return
  }
  pendingStep=buildJsonObject{put("type",type);put("execution","unsupported")};phase="after_action"
 }
 @get:Rule val paparazzi=Paparazzi(deviceConfig=DeviceConfig.PIXEL_5.copy(screenWidth=(number("width",390f)*2.75f).toInt(),screenHeight=(number("viewportHeight",600f)*2.75f).toInt(),nightMode=if(dark)NightMode.NIGHT else NightMode.NOTNIGHT,fontScale=number("fontScale",1f),softButtons=false),showSystemUi=false,
  snapshotHandler=object:SnapshotHandler{override fun close(){};override fun newFrameHandler(snapshot:Snapshot,frameCount:Int,fps:Int)=object:SnapshotHandler.FrameHandler{override fun close(){};override fun handle(image:BufferedImage){advance(image)}}})
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
  paparazzi.gif(view,"session",0L,240_000L,4)
  File(output,"observation.json").writeText(buildJsonObject{
   put("native_test","NativeObserverTest.capture");put("phase",phase);put("snapshots",JsonArray(records));put("steps",JsonArray(steps));put("events",buildJsonArray{events.forEach{add(it)}})
   put("coverage",buildJsonObject{put("bottom_reached",bottomReached);put("observed_identifiers",buildJsonArray{observed.sorted().forEach{add(it)}})})
   put("configuration",buildJsonObject{put("night_mode_mask",actualNight);put("font_scale",actualScale);put("density",density);put("direction",actualDirection)})
   put("scope","One attached native ComposeView in continuous Paparazzi frame session. Semantic OnClick invocation, not physical touch; native parent ScrollState displacement, not OS gestures. No Activity/navigation/lifecycle claims.")
  }.toString())
  check(phase=="complete"){"Observation frame budget exhausted"}
 }
}
