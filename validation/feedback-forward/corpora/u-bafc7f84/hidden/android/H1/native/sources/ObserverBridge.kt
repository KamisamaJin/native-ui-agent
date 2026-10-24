package org.nativeobserver

import androidx.compose.runtime.Composable
import kotlinx.serialization.json.*
import com.example.reply.ui.components.TransferHandlingNote
import com.example.reply.ui.components.ColdStorageTransfer
import com.example.reply.ui.components.ColdStorageTransferPanel

object ObserverBridge {
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
