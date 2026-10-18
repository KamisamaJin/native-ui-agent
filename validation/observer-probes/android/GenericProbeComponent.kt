package com.example.reply.ui.components
import androidx.compose.runtime.Composable
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.*
import androidx.compose.ui.unit.dp
enum class VisitRescheduleMode {Loading,Choosing,Unavailable,Confirmed}
enum class VisitSlotAvailability {Available,Limited,Unavailable}
data class VisitAppointment(val dayLabel:String,val timeLabel:String)
data class VisitSlot(val id:String,val timeLabel:String,val detail:String,val availability:VisitSlotAvailability,val feeLabel:String?,val unavailableReason:String?)
data class VisitSlotGroup(val id:String,val dayLabel:String,val slots:List<VisitSlot>)
data class VisitConfirmation(val appointment:VisitAppointment,val reference:String,val note:String)
data class VisitRescheduleModel(val mode:VisitRescheduleMode,val serviceTitle:String,val location:String,val currentAppointment:VisitAppointment,val groups:List<VisitSlotGroup>,val selectedSlotId:String?,val feeAccepted:Boolean,val unavailableMessage:String?,val confirmation:VisitConfirmation?)
sealed class VisitRescheduleAction { data class SelectSlot(val slotId:String):VisitRescheduleAction();data class SetFeeAccepted(val accepted:Boolean):VisitRescheduleAction();data class Confirm(val slotId:String):VisitRescheduleAction();object Retry:VisitRescheduleAction();object Done:VisitRescheduleAction() }
@Composable fun VisitReschedulePanel(model:VisitRescheduleModel,onAction:(VisitRescheduleAction)->Unit,modifier:Modifier=Modifier){Column(modifier){Text(model.serviceTitle,Modifier.semantics{testTag="probe.title"});repeat(18){Text("Generic probe row $it",Modifier.height(60.dp))};Button(onClick={onAction(VisitRescheduleAction.Confirm("probe"))},modifier=Modifier.semantics{testTag="visit.confirm"}){Text("Generic probe action")}}}
