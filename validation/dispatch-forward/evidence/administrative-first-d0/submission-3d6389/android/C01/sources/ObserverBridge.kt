package org.nativeobserver

import androidx.compose.runtime.Composable
import com.example.reply.ui.waterround.WaterRoundModel
import com.example.reply.ui.waterround.WaterRoundAction
import com.example.reply.ui.waterround.WateringMethod
import com.example.reply.ui.waterround.WaterRoundRelease
import kotlinx.serialization.json.*

object ObserverBridge {
    @Composable fun Content(input: JsonObject, onEvent: (String) -> Unit) {
        val model = WaterRoundModel(
            roundId = input.getValue("roundId").jsonPrimitive.content,
            title = input.getValue("title").jsonPrimitive.content,
            description = input.getValue("description").jsonPrimitive.content,
            notice = input.getValue("notice").jsonPrimitive.content,
            bedCount = input.getValue("bedCount").jsonPrimitive.int,
            dripLitresPerBed = input.getValue("dripLitresPerBed").jsonPrimitive.int,
            soakLitresPerBed = input.getValue("soakLitresPerBed").jsonPrimitive.int,
            dripPrimeLitres = input.getValue("dripPrimeLitres").jsonPrimitive.int,
            tankLitres = input.getValue("tankLitres").jsonPrimitive.int,
            reserveLitres = input.getValue("reserveLitres").jsonPrimitive.int,
            soakAllowed = input.getValue("soakAllowed").jsonPrimitive.boolean,
            selectedMethod = WateringMethod.valueOf(input.getValue("selectedMethod").jsonPrimitive.content),
            reserveAcknowledged = input.getValue("reserveAcknowledged").jsonPrimitive.boolean,
            isEnabled = input.getValue("isEnabled").jsonPrimitive.boolean,
            isSubmitting = input.getValue("isSubmitting").jsonPrimitive.boolean)
        WaterRoundRelease(model = model, onAction = { action ->
            when (action) {
                is WaterRoundAction.methodRequested -> onEvent("methodRequested|roundId=${action.roundId}|method=${action.method.name}")
                is WaterRoundAction.reserveAcknowledgementRequested -> onEvent("reserveAcknowledgementRequested|roundId=${action.roundId}|acknowledged=${action.acknowledged}")
                is WaterRoundAction.releaseRequested -> onEvent("releaseRequested|roundId=${action.roundId}|method=${action.method.name}|bedCount=${action.bedCount}|requestedLitres=${action.requestedLitres}|remainingLitres=${action.remainingLitres}|reserveUsedLitres=${action.reserveUsedLitres}")
            }
        })
    }
}
