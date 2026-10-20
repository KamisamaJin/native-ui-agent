/*
 * Copyright 2026 The Android Open Source Project
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at https://www.apache.org/licenses/LICENSE-2.0
 */
package com.example.reply.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.luminance
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/** A caller-owned course and its remaining enrollment capacity. */
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
    val seats: Int,
    val workbook: Boolean = false,
    val confirmed: Boolean = false,
) {
    fun forCourse(course: WorkshopCourse): EnrollmentDraft {
        val nextMode = if (course.onsiteAvailable) mode else WorkshopAttendance.REMOTE
        val nextSeats = if (seats in listOf(1, 3, 6) && seats <= course.capacity) seats
            else listOf(6, 3, 1).firstOrNull { it <= course.capacity } ?: 0
        return copy(
            courseID = course.id,
            mode = nextMode,
            seats = nextSeats,
            workbook = workbook && nextMode == WorkshopAttendance.ONSITE && course.workbookAvailable,
        )
    }

    fun replacing(catalog: WorkshopCatalog): EnrollmentDraft {
        val nextCourse = catalog.courses.firstOrNull { it.id == courseID && it.capacity >= 1 }
            ?: catalog.courses.firstOrNull { it.capacity >= 1 }
            ?: return EnrollmentDraft(courseID = null, seats = 0)
        return copy(confirmed = false, seats = if (courseID == null) 1 else seats).forCourse(nextCourse)
    }

    companion object {
        fun initial(catalog: WorkshopCatalog): EnrollmentDraft {
            val first = catalog.courses.firstOrNull { it.capacity >= 1 }
            return EnrollmentDraft(courseID = first?.id, seats = if (first == null) 0 else 1)
        }
    }
}

private data class EnrollmentColors(
    val ink: Color,
    val body: Color,
    val surface: Color,
    val selected: Color,
    val accent: Color,
    val onAccent: Color,
)

/**
 * A local enrollment draft. The caller supplies the theme and the single outer scroller.
 * A changed catalog reconciles this same component's choices without dispatching an event.
 */
@Composable
fun WorkshopEnrollmentCard(
    catalog: WorkshopCatalog,
    onReserve: (WorkshopReservation) -> Unit,
    modifier: Modifier = Modifier,
) {
    var previousCatalog by remember { mutableStateOf(catalog) }
    var draft by remember { mutableStateOf(EnrollmentDraft.initial(catalog)) }
    // Reconcile before emitting content, so a caller update never presents a stale confirmation.
    if (previousCatalog != catalog) {
        draft = draft.replacing(catalog)
        previousCatalog = catalog
    }
    val course = catalog.courses.firstOrNull { it.id == draft.courseID && it.capacity >= 1 }
    val dark = MaterialTheme.colorScheme.surface.luminance() < 0.5f
    val colors = if (dark) EnrollmentColors(
        Color(0xFFF1F5F9), Color(0xFFCBD5E1), Color(0xFF182635),
        Color(0xFF233E52), Color(0xFF8ACBEE), Color(0xFF172B3A),
    ) else EnrollmentColors(
        Color(0xFF172B3A), Color(0xFF425466), Color.White,
        Color(0xFFE7F2F8), Color(0xFF155E83), Color.White,
    )
    val valid = course != null && draft.seats in listOf(1, 3, 6) && draft.seats <= course.capacity
    val seatLabel = if (draft.seats == 1) "seat" else "seats"
    val modeLabel = if (draft.mode == WorkshopAttendance.REMOTE) "Remote" else "In person"
    val seatCost = course?.let {
        it.seatPriceCents.toLong() - if (draft.mode == WorkshopAttendance.REMOTE) catalog.remoteDiscountCents else 0
    } ?: 0L
    val total = if (course == null) 0L else draft.seats * (
        seatCost + if (draft.workbook) catalog.workbookCents else 0
    ) + if (draft.mode == WorkshopAttendance.ONSITE) catalog.onsiteFeeCents else 0
    val money = "${total / 100}.${(total % 100).toString().padStart(2, '0')}"
    val totalLabel = "Total $$money · ${draft.seats} $seatLabel · $modeLabel · " +
        if (draft.workbook) "Workbooks" else "No workbooks"
    val status = when {
        course == null -> "No courses available."
        draft.confirmed -> "Reserved ${draft.seats} $seatLabel for ${course.title}."
        else -> "Choose options, then reserve."
    }

    Column(
        modifier = modifier.fillMaxWidth()
            .background(colors.surface, RoundedCornerShape(16.dp)).padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(20.dp),
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(
                catalog.title, modifier = Modifier.testTag("enroll.title"), color = colors.ink,
                fontSize = 22.sp, fontWeight = FontWeight.SemiBold,
            )
            Text(
                catalog.detail, modifier = Modifier.testTag("enroll.detail"),
                color = colors.body, fontSize = 16.sp,
            )
        }
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            EnrollmentSection("Courses", colors)
            catalog.courses.forEach { item ->
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    EnrollmentOption(
                        title = item.title, tag = "enroll.course.${item.id}",
                        selected = draft.courseID == item.id,
                        enabled = !draft.confirmed && item.capacity >= 1 && course != null,
                        colors = colors,
                    ) { draft = draft.forCourse(item) }
                    Text(
                        item.detail, modifier = Modifier.padding(horizontal = 12.dp),
                        color = colors.body, fontSize = 16.sp,
                    )
                }
            }
        }
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            EnrollmentSection("Attendance", colors)
            EnrollmentOption(
                "Remote", "enroll.mode.remote", draft.mode == WorkshopAttendance.REMOTE,
                !draft.confirmed && course != null, colors,
            ) { draft = draft.copy(mode = WorkshopAttendance.REMOTE, workbook = false) }
            EnrollmentOption(
                "In person", "enroll.mode.onsite", draft.mode == WorkshopAttendance.ONSITE,
                !draft.confirmed && course?.onsiteAvailable == true, colors,
            ) { draft = draft.copy(mode = WorkshopAttendance.ONSITE) }
        }
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            EnrollmentSection("Seats", colors)
            listOf(1, 3, 6).forEach { seats ->
                EnrollmentOption(
                    "$seats ${if (seats == 1) "seat" else "seats"}", "enroll.seats.$seats",
                    draft.seats == seats,
                    !draft.confirmed && course != null && seats <= course.capacity, colors,
                ) { draft = draft.copy(seats = seats) }
            }
        }
        EnrollmentOption(
            "Printed workbook", "enroll.workbook", draft.workbook,
            !draft.confirmed && draft.mode == WorkshopAttendance.ONSITE && course?.workbookAvailable == true,
            colors, Role.Checkbox,
        ) { draft = draft.copy(workbook = !draft.workbook) }
        Text(
            totalLabel,
            modifier = Modifier.fillMaxWidth().background(colors.selected, RoundedCornerShape(8.dp))
                .padding(12.dp).testTag("enroll.total"),
            color = colors.ink, fontSize = 18.sp, fontWeight = FontWeight.SemiBold,
        )
        Text(status, modifier = Modifier.testTag("enroll.status"), color = colors.body, fontSize = 16.sp)
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(
                onClick = {
                    if (valid && !draft.confirmed && course != null) {
                        val reservation = WorkshopReservation(course.id, draft.mode, draft.seats, draft.workbook)
                        draft = draft.copy(confirmed = true)
                        onReserve(reservation)
                    }
                },
                enabled = valid && !draft.confirmed,
                modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag("enroll.reserve"),
                shape = RoundedCornerShape(8.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = colors.accent, contentColor = colors.onAccent,
                    disabledContainerColor = colors.accent.copy(alpha = 0.62f),
                    disabledContentColor = colors.onAccent.copy(alpha = 0.8f),
                ),
            ) {
                Text("Reserve seats", modifier = Modifier.fillMaxWidth(), fontSize = 16.sp, fontWeight = FontWeight.SemiBold)
            }
            Button(
                onClick = { if (draft.confirmed) draft = draft.copy(confirmed = false) },
                enabled = draft.confirmed,
                modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp).testTag("enroll.edit"),
                shape = RoundedCornerShape(8.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = colors.selected, contentColor = colors.ink,
                    disabledContainerColor = colors.selected.copy(alpha = 0.62f),
                    disabledContentColor = colors.ink.copy(alpha = 0.62f),
                ),
            ) {
                Text("Edit selection", modifier = Modifier.fillMaxWidth(), fontSize = 16.sp, fontWeight = FontWeight.SemiBold)
            }
        }
    }
}

@Composable
private fun EnrollmentSection(title: String, colors: EnrollmentColors) {
    Text(title, color = colors.ink, fontSize = 14.sp, fontWeight = FontWeight.SemiBold)
}

@Composable
private fun EnrollmentOption(
    title: String,
    tag: String,
    selected: Boolean,
    enabled: Boolean,
    colors: EnrollmentColors,
    role: Role = Role.RadioButton,
    onClick: () -> Unit,
) {
    Row(
        modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)
            .background(if (selected) colors.selected else colors.surface, RoundedCornerShape(8.dp))
            .border(1.dp, if (selected) colors.accent else colors.body, RoundedCornerShape(8.dp))
            .selectable(selected = selected, enabled = enabled, role = role, onClick = { if (enabled) onClick() })
            .testTag(tag).alpha(if (enabled) 1f else 0.62f).padding(12.dp),
        horizontalArrangement = Arrangement.spacedBy(6.dp),
        verticalAlignment = Alignment.Top,
    ) {
        Text(
            if (selected) "●" else "○", modifier = Modifier.clearAndSetSemantics { },
            color = colors.ink, fontSize = 16.sp,
        )
        Text(title, modifier = Modifier.weight(1f), color = colors.ink, fontSize = 16.sp, fontWeight = FontWeight.SemiBold)
    }
}
