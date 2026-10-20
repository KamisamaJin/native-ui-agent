package org.nativeobserver

import androidx.compose.runtime.Composable
import com.example.reply.ui.components.WorkshopCatalog
import com.example.reply.ui.components.WorkshopCourse
import com.example.reply.ui.components.WorkshopEnrollmentCard
import kotlinx.serialization.json.*

object ObserverBridge {
    @Composable
    fun Content(fixture: JsonObject, onEvent: (String) -> Unit) {
        fun text(o: JsonObject, k: String) = o[k]!!.jsonPrimitive.content
        fun number(o: JsonObject, k: String) = o[k]!!.jsonPrimitive.int
        fun flag(o: JsonObject, k: String) = o[k]!!.jsonPrimitive.boolean
        val catalog = WorkshopCatalog(
            title = text(fixture, "title"), detail = text(fixture, "detail"),
            courses = fixture["courses"]!!.jsonArray.map { entry ->
                val c = entry.jsonObject
                WorkshopCourse(text(c,"id"), text(c,"title"), text(c,"detail"),
                    number(c,"seatPriceCents"), number(c,"capacity"),
                    flag(c,"onsiteAvailable"), flag(c,"workbookAvailable"))
            },
            remoteDiscountCents = number(fixture,"remoteDiscountCents"),
            onsiteFeeCents = number(fixture,"onsiteFeeCents"), workbookCents = number(fixture,"workbookCents")
        )
        WorkshopEnrollmentCard(catalog = catalog, onReserve = { reservation ->
            onEvent("reserve:${reservation.courseID}:${reservation.mode.name.lowercase()}:${reservation.seats}:${reservation.workbook}")
        })
    }
}
