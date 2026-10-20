package org.nativeobserver

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import com.example.reply.ui.printbatch.PrintBatchApprovalCard
import com.example.reply.ui.printbatch.PrintBatchJob
import com.example.reply.ui.printbatch.PrintBatchModel
import com.example.reply.ui.printbatch.PrintBatchPresentation
import org.json.JSONObject

@Composable
fun ObserverBridge(fixture: JSONObject, onEvent: (String) -> Unit, modifier: Modifier = Modifier) {
    val host = fixture.getJSONObject("host")
    val raw = fixture.optJSONObject("model") ?: fixture.getJSONArray("models").getJSONObject(fixture.optInt("activeModelIndex", 0))
    val rawJobs = raw.getJSONArray("jobs")
    val jobs = (0 until rawJobs.length()).map { index ->
        val j = rawJobs.getJSONObject(index)
        PrintBatchJob(j.getString("id"), j.getString("title"), j.getInt("pages"), j.getInt("copies"), j.getBoolean("isColor"), j.getBoolean("selected"), j.getBoolean("locked"))
    }
    val model = PrintBatchModel(raw.getString("modelID"), raw.getInt("budgetCredits"), raw.getBoolean("allowPriority"), raw.getString("initialPaperMode"), raw.getBoolean("initialPriority"), raw.getBoolean("initialExpanded"), jobs)
    val presentation = PrintBatchPresentation(host.getString("theme") == "dark", host.getDouble("textScale"), host.getString("direction") == "rtl")
    PrintBatchApprovalCard(model, presentation, { name, payload ->
        onEvent(JSONObject(mapOf("name" to name, "payload" to JSONObject(payload))).toString())
    }, modifier)
}
