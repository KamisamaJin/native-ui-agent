package com.example.reply.ui.components

import androidx.compose.runtime.Composable
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Text
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.*
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

@Composable
fun QuietMomentCard(title:String,detail:String,canvas:Color,band:Color,onAcknowledge:()->Unit) {
 val ink=Color(0xFF202124)
 Column(Modifier.fillMaxWidth().background(canvas).testTag("moment.canvas").padding(20.dp),verticalArrangement=Arrangement.spacedBy(16.dp)) {
  Box(Modifier.fillMaxWidth().height(64.dp).background(band).semantics{contentDescription="Accent region"}.testTag("moment.band"))
  Text(title,color=ink,fontSize=22.sp,fontWeight=FontWeight.SemiBold,modifier=Modifier.testTag("moment.title"))
  Text(detail,color=ink,fontSize=17.sp,modifier=Modifier.testTag("moment.body"))
  Box(Modifier.fillMaxWidth().heightIn(min=48.dp).clickable(role=Role.Button,onClick=onAcknowledge).testTag("moment.action")) {
   Text("Acknowledge",color=ink,fontSize=17.sp)
  }
 }
}
