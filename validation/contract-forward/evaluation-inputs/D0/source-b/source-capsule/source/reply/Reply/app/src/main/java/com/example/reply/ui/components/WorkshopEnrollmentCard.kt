package com.example.reply.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.semantics.selected
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp


data class WorkshopCourse(
    val id: String,
    val title: String,
    val detail: String,
    val seatPriceCents: Int,
    val capacity: Int,
    val onsiteAvailable: Boolean,
    val workbookAvailable: Boolean,
)

data class WorkshopCatalog(
    val title: String,
    val detail: String,
    val courses: List<WorkshopCourse>,
    val remoteDiscountCents: Int,
    val onsiteFeeCents: Int,
    val workbookCents: Int,
)

enum class WorkshopAttendance { REMOTE, ONSITE }

data class WorkshopReservation(
    val courseID: String,
    val mode: WorkshopAttendance,
    val seats: Int,
    val workbook: Boolean,
)

private data class EnrollmentDraft(
    val courseID: String?,
    val mode: WorkshopAttendance = WorkshopAttendance.REMOTE,
    val seats: Int = 1,
    val workbook: Boolean = false,
    val confirmed: Boolean = false,
)

private fun reconcileDraft(catalog: WorkshopCatalog, draft: EnrollmentDraft): EnrollmentDraft {
    val course = catalog.courses.firstOrNull { it.id == draft.courseID && it.capacity >= 1 }
        ?: catalog.courses.firstOrNull { it.capacity >= 1 }
        ?: return EnrollmentDraft(courseID = null, seats = 0)
    val mode = if (course.onsiteAvailable) draft.mode else WorkshopAttendance.REMOTE
    val seats = when {
        draft.seats == 0 -> 1
        draft.seats in listOf(1, 3, 6) && draft.seats <= course.capacity -> draft.seats
        else -> listOf(6, 3, 1).first { it <= course.capacity }
    }
    return draft.copy(
        courseID = course.id,
        mode = mode,
        seats = seats,
        workbook = draft.workbook && mode == WorkshopAttendance.ONSITE &&
            course.onsiteAvailable && course.workbookAvailable,
        confirmed = false,
    )
}

private data class EnrollmentColors(
    val ink: Color,
    val body: Color,
    val surface: Color,
    val selectedFill: Color,
    val accent: Color,
    val onAccent: Color,
)

/** Local form state; the caller owns the single vertical scroll container. */
@Composable
fun WorkshopEnrollmentCard(
    catalog: WorkshopCatalog,
    onReserve: (WorkshopReservation) -> Unit,
    modifier: Modifier = Modifier,
) {
    var draft by remember {
        mutableStateOf(reconcileDraft(catalog, EnrollmentDraft(courseID = null)))
    }
    var previousCatalog by remember { mutableStateOf(catalog) }
    // Track changing live input without keying/recreating the component or its draft.
    if (previousCatalog != catalog) {
        draft = reconcileDraft(catalog, draft)
        previousCatalog = catalog
    }
    val course = catalog.courses.firstOrNull { it.id == draft.courseID && it.capacity >= 1 }
    val workbookAvailable = course != null && course.onsiteAvailable && course.workbookAvailable &&
        draft.mode == WorkshopAttendance.ONSITE
    val valid = course != null && draft.seats in listOf(1, 3, 6) &&
        draft.seats <= course.capacity &&
        (draft.mode == WorkshopAttendance.REMOTE || course.onsiteAvailable) &&
        (!draft.workbook || workbookAvailable)
    val dark = isSystemInDarkTheme()
    val colors = if (dark) {
        EnrollmentColors(Color(0xFFF1F5F9), Color(0xFFCBD5E1), Color(0xFF182635),
            Color(0xFF233E52), Color(0xFF8ACBEE), Color(0xFF172B3A))
    } else {
        EnrollmentColors(Color(0xFF172B3A), Color(0xFF425466), Color(0xFFFFFFFF),
            Color(0xFFE7F2F8), Color(0xFF155E83), Color.White)
    }
    val totalCents = if (course == null) 0L else {
        draft.seats.toLong() * (course.seatPriceCents.toLong() -
            if (draft.mode == WorkshopAttendance.REMOTE) catalog.remoteDiscountCents else 0) +
            (if (draft.workbook) draft.seats.toLong() * catalog.workbookCents else 0L) +
            (if (draft.mode == WorkshopAttendance.ONSITE) catalog.onsiteFeeCents.toLong() else 0L)
    }
    val seatLabel = "${draft.seats} ${if (draft.seats == 1) "seat" else "seats"}"
    val total = "Total $${totalCents / 100}.${(totalCents % 100).toString().padStart(2, '0')} · " +
        "$seatLabel · ${if (draft.mode == WorkshopAttendance.REMOTE) "Remote" else "In person"} · " +
        if (draft.workbook) "Workbooks" else "No workbooks"
    val status = when {
        course == null -> "No courses available."
        draft.confirmed -> "Reserved $seatLabel for ${course.title}."
        else -> "Choose options, then reserve."
    }

    Column(
        modifier = modifier.fillMaxWidth().clip(RoundedCornerShape(16.dp))
            .background(colors.surface).padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(20.dp),
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(catalog.title, modifier = Modifier.testTag("enroll.title"),
                color = colors.ink, fontSize = 22.sp, fontWeight = FontWeight.SemiBold)
            Text(catalog.detail, modifier = Modifier.testTag("enroll.detail"),
                color = colors.body, fontSize = 16.sp)
        }
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            EnrollmentSection("Courses", colors)
            catalog.courses.forEach { item ->
                EnrollmentOption(item.title, "enroll.course.${item.id}",
                    selected = draft.courseID == item.id,
                    enabled = !draft.confirmed && course != null && item.capacity >= 1,
                    colors = colors) {
                    if (!draft.confirmed && item.capacity >= 1) {
                        draft = reconcileDraft(catalog, draft.copy(courseID = item.id))
                    }
                }
                Text(item.detail, modifier = Modifier.padding(horizontal = 12.dp),
                    color = colors.body, fontSize = 16.sp)
            }
        }
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            EnrollmentSection("Attendance", colors)
            EnrollmentOption("Remote", "enroll.mode.remote",
                selected = draft.mode == WorkshopAttendance.REMOTE,
                enabled = course != null && !draft.confirmed, colors = colors) {
                if (course != null && !draft.confirmed) {
                    draft = draft.copy(mode = WorkshopAttendance.REMOTE, workbook = false)
                }
            }
            EnrollmentOption("In person", "enroll.mode.onsite",
                selected = draft.mode == WorkshopAttendance.ONSITE,
                enabled = course?.onsiteAvailable == true && !draft.confirmed, colors = colors) {
                if (course?.onsiteAvailable == true && !draft.confirmed) {
                    draft = draft.copy(mode = WorkshopAttendance.ONSITE)
                }
            }
        }
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            EnrollmentSection("Seats", colors)
            listOf(1, 3, 6).forEach { count ->
                EnrollmentOption("$count ${if (count == 1) "seat" else "seats"}",
                    "enroll.seats.$count", selected = draft.seats == count,
                    enabled = !draft.confirmed && (course?.capacity ?: 0) >= count, colors = colors) {
                    if (!draft.confirmed && (course?.capacity ?: 0) >= count) {
                        draft = draft.copy(seats = count)
                    }
                }
            }
        }
        EnrollmentOption("Printed workbook", "enroll.workbook", selected = draft.workbook,
            enabled = workbookAvailable && !draft.confirmed, colors = colors) {
            if (workbookAvailable && !draft.confirmed) draft = draft.copy(workbook = !draft.workbook)
        }
        Text(total, modifier = Modifier.fillMaxWidth().clip(RoundedCornerShape(8.dp))
            .background(colors.selectedFill).padding(12.dp).testTag("enroll.total"),
            color = colors.ink, fontSize = 18.sp, fontWeight = FontWeight.SemiBold)
        Text(status, modifier = Modifier.testTag("enroll.status"), color = colors.body, fontSize = 16.sp)
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            EnrollmentAction("Reserve seats", "enroll.reserve", enabled = valid && !draft.confirmed,
                background = colors.accent, foreground = colors.onAccent) {
                if (valid && !draft.confirmed && course != null) {
                    val reservation = WorkshopReservation(course.id, draft.mode, draft.seats, draft.workbook)
                    draft = draft.copy(confirmed = true)
                    onReserve(reservation)
                }
            }
            EnrollmentAction("Edit selection", "enroll.edit", enabled = draft.confirmed,
                background = colors.selectedFill, foreground = colors.ink) {
                if (draft.confirmed) draft = draft.copy(confirmed = false)
            }
        }
    }
}

@Composable
private fun EnrollmentSection(text: String, colors: EnrollmentColors) {
    Text(text, color = colors.ink, fontSize = 14.sp, fontWeight = FontWeight.SemiBold)
}

@Composable
private fun EnrollmentOption(
    title: String,
    tag: String,
    selected: Boolean,
    enabled: Boolean,
    colors: EnrollmentColors,
    onClick: () -> Unit,
) {
    Row(
        modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)
            .alpha(if (enabled) 1f else 0.65f)
            .clip(RoundedCornerShape(8.dp))
            .background(if (selected) colors.selectedFill else colors.surface)
            .border(1.dp, if (selected) colors.accent else colors.body, RoundedCornerShape(8.dp))
            .testTag(tag).semantics { this.selected = selected }
            .clickable(enabled = enabled, role = Role.Button, onClick = onClick)
            .padding(12.dp),
        verticalAlignment = Alignment.Top,
        horizontalArrangement = Arrangement.spacedBy(6.dp),
    ) {
        Text(if (selected) "●" else "○", modifier = Modifier.clearAndSetSemantics {},
            color = colors.ink, fontSize = 16.sp)
        Text(title, modifier = Modifier.weight(1f), color = colors.ink,
            fontSize = 16.sp, fontWeight = FontWeight.SemiBold)
    }
}

@Composable
private fun EnrollmentAction(
    title: String,
    tag: String,
    enabled: Boolean,
    background: Color,
    foreground: Color,
    onClick: () -> Unit,
) {
    Text(title, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)
        .alpha(if (enabled) 1f else 0.65f).clip(RoundedCornerShape(8.dp))
        .background(background).testTag(tag)
        .clickable(enabled = enabled, role = Role.Button, onClick = onClick).padding(12.dp),
        color = foreground, fontSize = 16.sp, fontWeight = FontWeight.SemiBold)
}
