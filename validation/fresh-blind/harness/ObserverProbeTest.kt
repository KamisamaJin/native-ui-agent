package com.example.reply
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.platform.*
import androidx.compose.ui.semantics.*
import app.cash.paparazzi.*
import java.io.File
import java.awt.image.BufferedImage
import javax.imageio.ImageIO
import org.junit.Rule
import org.junit.Test
class ObserverProbeTest {
 @get:Rule val paparazzi=Paparazzi(deviceConfig=DeviceConfig.PIXEL_5,showSystemUi=false,snapshotHandler=object:SnapshotHandler { override fun close(){}; override fun newFrameHandler(snapshot:Snapshot, frameCount:Int, fps:Int)=object:SnapshotHandler.FrameHandler { override fun close(){}; override fun handle(image:BufferedImage){ advance(image) } } })
 var value by mutableStateOf("Before")
 var frame=0
 lateinit var view:ComposeView
 var event=0
 var raw:List<SemanticsNode> = emptyList()
 fun nodes(n:SemanticsNode):List<SemanticsNode> = listOf(n)+n.children.flatMap{nodes(it)}
 @Test fun capture() {
  view=ComposeView(paparazzi.context)
  view.setContent {
   val root=LocalView.current as ViewRootForTest
   SideEffect {raw=nodes(root.semanticsOwner.unmergedRootSemanticsNode)}
   MaterialTheme {Column {Text(value);Button(onClick={event++;value="Clicked"}){Text("Go")}}}
  }
  paparazzi.gif(view,"continuous",0L,1000L,2)
  check(frame==3)
  File("/tmp/native-android-probe-result.json").writeText("{\"event\":$event,\"same_view_state_update\":true}")
 }
 fun advance(image:BufferedImage){
  raw=nodes((view.getChildAt(0) as ViewRootForTest).semanticsOwner.unmergedRootSemanticsNode)
  ImageIO.write(image,"png",File("/tmp/native-android-probe-$frame.png"))
  when(frame){
   0->{check(raw.any{it.config.getOrNull(SemanticsProperties.Text)?.any{t->t.text=="Before"}==true}); val click=raw.first{it.config.getOrNull(SemanticsActions.OnClick)!=null}.config.getOrNull(SemanticsActions.OnClick)!!.action!!;check(click());check(event==1)}
   1->{check(raw.any{it.config.getOrNull(SemanticsProperties.Text)?.any{t->t.text=="Clicked"}==true}){"live update not observed"};value="Caller updated"}
   2->{check(raw.any{it.config.getOrNull(SemanticsProperties.Text)?.any{t->t.text=="Caller updated"}==true}){"caller update not observed"}}
  }
  frame++
 }
}
