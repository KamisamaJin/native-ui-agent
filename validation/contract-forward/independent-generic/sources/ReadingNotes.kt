package com.example.readingnotes

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.Alignment
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

@Composable
fun ReadingNotes(title:String,footer:String,prefix:String,onOpen:()->Unit) {
 var open by remember { mutableStateOf(false) }
 val ink=Color(0xFF204B6D)
 Column(Modifier.fillMaxWidth(),verticalArrangement=Arrangement.spacedBy(16.dp)) {
  Text(title,Modifier.testTag("reading.heading"),color=ink,fontSize=26.sp,fontWeight=FontWeight.SemiBold)
  Text("A calm place to review one observation at a time.",Modifier.testTag("reading.ink"),color=ink,fontSize=16.sp)
  Row(horizontalArrangement=Arrangement.spacedBy(12.dp)) {
   Marker("Focus","reading.markerA",ink)
   Marker("Notes","reading.markerB",ink)
  }
  Button(onClick={if(!open){open=true;onOpen()}},modifier=Modifier.fillMaxWidth().height(48.dp).testTag("reading.disclosure"),shape=RoundedCornerShape(12.dp),colors=ButtonDefaults.buttonColors(containerColor=ink)) {
   Text(if(open)"Notes open"else"Open notes",fontSize=16.sp,fontWeight=FontWeight.Medium)
  }
  Text(if(open)"Notes open"else"Notes closed",Modifier.testTag("reading.status"),color=ink,fontSize=14.sp,fontWeight=FontWeight.Medium)
  repeat(12) { index ->
   Column(Modifier.fillMaxWidth().heightIn(min=80.dp).clip(RoundedCornerShape(10.dp)).background(Color.White).padding(horizontal=12.dp).testTag("reading.row.$index"),verticalArrangement=Arrangement.Center) {
    Text("$prefix ${index+1}",color=ink,fontSize=16.sp,fontWeight=FontWeight.SemiBold)
    Spacer(Modifier.height(6.dp))
    Text("Read the whole line, pause briefly, and leave room for a thoughtful response.",color=Color(0xFF415161),fontSize=14.sp)
   }
  }
  Text(footer,Modifier.padding(vertical=12.dp).testTag("reading.footer"),color=ink,fontSize=16.sp,fontWeight=FontWeight.SemiBold)
 }
}

@Composable
private fun Marker(text:String,tag:String,ink:Color) {
 Box(Modifier.width(72.dp).height(32.dp).clip(RoundedCornerShape(8.dp)).background(Color(0xFFDDEAF4)).testTag(tag),contentAlignment=Alignment.Center) {Text(text,color=ink,fontSize=14.sp,fontWeight=FontWeight.Medium)}
}
