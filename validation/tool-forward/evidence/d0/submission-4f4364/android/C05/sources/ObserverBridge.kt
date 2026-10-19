package org.nativeobserver
import androidx.compose.runtime.Composable
import androidx.compose.material3.*
import androidx.compose.foundation.isSystemInDarkTheme
import com.example.reply.ui.components.*
import kotlinx.serialization.json.*
private fun decodeReturnResolutionModel(o:JsonObject)=ReturnResolutionModel(
 caseId=o["caseId"]!!.jsonPrimitive.content,
 merchant=o["merchant"]!!.jsonPrimitive.content,
 heading=o["heading"]!!.jsonPrimitive.content,
 orderReference=o["orderReference"]!!.jsonPrimitive.content,
 intro=o["intro"]!!.jsonPrimitive.content,
 status=ReturnResolutionStatus.valueOf(o["status"]!!.jsonPrimitive.content.uppercase()),
 statusLabel=o["statusLabel"]!!.jsonPrimitive.content,
 item=decodeReturnResolutionItem(o["item"]!!.jsonObject),
 deadline=o["deadline"]?.takeUnless { it is JsonNull }?.jsonObject?.let { decodeReturnResolutionDeadline(it) },
 contextMessage=o["contextMessage"]!!.jsonPrimitive.content,
 optionsTitle=o["optionsTitle"]!!.jsonPrimitive.content,
 options=o["options"]!!.jsonArray.map { decodeReturnResolutionOption(it.jsonObject) },
 selectedOptionId=o["selectedOptionId"]?.jsonPrimitive?.contentOrNull,
 sizesTitle=o["sizesTitle"]!!.jsonPrimitive.content,
 sizes=o["sizes"]!!.jsonArray.map { decodeReturnResolutionSize(it.jsonObject) },
 selectedSizeId=o["selectedSizeId"]?.jsonPrimitive?.contentOrNull,
 acknowledgementAccepted=o["acknowledgementAccepted"]!!.jsonPrimitive.boolean,
 notes=decodeReturnResolutionNotes(o["notes"]!!.jsonObject),
 notesExpanded=o["notesExpanded"]!!.jsonPrimitive.boolean,
 amountRows=o["amountRows"]!!.jsonArray.map { decodeReturnResolutionAmountRow(it.jsonObject) },
 totalLabel=o["totalLabel"]!!.jsonPrimitive.content,
 totalValue=o["totalValue"]!!.jsonPrimitive.content,
 totalFootnote=o["totalFootnote"]!!.jsonPrimitive.content,
 idlePrimaryLabel=o["idlePrimaryLabel"]!!.jsonPrimitive.content,
 keepLabel=o["keepLabel"]!!.jsonPrimitive.content,
 progressTitle=o["progressTitle"]!!.jsonPrimitive.content,
 progressBody=o["progressBody"]!!.jsonPrimitive.content,
 resultTitle=o["resultTitle"]!!.jsonPrimitive.content,
 resultBody=o["resultBody"]!!.jsonPrimitive.content,
 resultReference=o["resultReference"]!!.jsonPrimitive.content,
 doneLabel=o["doneLabel"]!!.jsonPrimitive.content,
 strings=decodeReturnResolutionStrings(o["strings"]!!.jsonObject)
)
private fun decodeReturnResolutionItem(o:JsonObject)=ReturnResolutionItem(
 title=o["title"]!!.jsonPrimitive.content,
 variant=o["variant"]!!.jsonPrimitive.content,
 quantityLabel=o["quantityLabel"]!!.jsonPrimitive.content,
 paidLabel=o["paidLabel"]!!.jsonPrimitive.content,
 accent=ReturnResolutionAccent.valueOf(o["accent"]!!.jsonPrimitive.content.uppercase())
)
private fun decodeReturnResolutionDeadline(o:JsonObject)=ReturnResolutionDeadline(
 text=o["text"]!!.jsonPrimitive.content,
 urgent=o["urgent"]!!.jsonPrimitive.boolean
)
private fun decodeReturnResolutionOption(o:JsonObject)=ReturnResolutionOption(
 id=o["id"]!!.jsonPrimitive.content,
 kind=ReturnResolutionKind.valueOf(o["kind"]!!.jsonPrimitive.content.uppercase()),
 title=o["title"]!!.jsonPrimitive.content,
 description=o["description"]!!.jsonPrimitive.content,
 amountLabel=o["amountLabel"]!!.jsonPrimitive.content,
 tag=o["tag"]?.jsonPrimitive?.contentOrNull,
 disabledReason=o["disabledReason"]?.jsonPrimitive?.contentOrNull,
 detailTitle=o["detailTitle"]!!.jsonPrimitive.content,
 detailBody=o["detailBody"]!!.jsonPrimitive.content,
 acknowledgementLabel=o["acknowledgementLabel"]?.jsonPrimitive?.contentOrNull,
 primaryLabel=o["primaryLabel"]!!.jsonPrimitive.content
)
private fun decodeReturnResolutionSize(o:JsonObject)=ReturnResolutionSize(
 id=o["id"]!!.jsonPrimitive.content,
 label=o["label"]!!.jsonPrimitive.content,
 unavailableReason=o["unavailableReason"]?.jsonPrimitive?.contentOrNull
)
private fun decodeReturnResolutionNotes(o:JsonObject)=ReturnResolutionNotes(
 title=o["title"]!!.jsonPrimitive.content,
 body=o["body"]!!.jsonPrimitive.content,
 bullets=o["bullets"]!!.jsonArray.map { it.jsonPrimitive.content }
)
private fun decodeReturnResolutionAmountRow(o:JsonObject)=ReturnResolutionAmountRow(
 id=o["id"]!!.jsonPrimitive.content,
 label=o["label"]!!.jsonPrimitive.content,
 value=o["value"]!!.jsonPrimitive.content,
 emphasized=o["emphasized"]!!.jsonPrimitive.boolean
)
private fun decodeReturnResolutionStrings(o:JsonObject)=ReturnResolutionStrings(
 chooseOption=o["chooseOption"]!!.jsonPrimitive.content,
 chooseSize=o["chooseSize"]!!.jsonPrimitive.content,
 acceptTerms=o["acceptTerms"]!!.jsonPrimitive.content,
 ready=o["ready"]!!.jsonPrimitive.content,
 noOptions=o["noOptions"]!!.jsonPrimitive.content,
 checkedValue=o["checkedValue"]!!.jsonPrimitive.content,
 uncheckedValue=o["uncheckedValue"]!!.jsonPrimitive.content,
 expandedValue=o["expandedValue"]!!.jsonPrimitive.content,
 collapsedValue=o["collapsedValue"]!!.jsonPrimitive.content,
 busyValue=o["busyValue"]!!.jsonPrimitive.content
)
private fun event(a:ReturnResolutionAction):String=buildJsonObject{
 when(a){
 is ReturnResolutionAction.SelectOption->{put("type","selectOption");put("optionId",a.optionId)}
 is ReturnResolutionAction.SelectSize->{put("type","selectSize");put("sizeId",a.sizeId)}
 is ReturnResolutionAction.SetAcknowledgement->{put("type","setAcknowledgement");put("accepted",a.accepted)}
 is ReturnResolutionAction.SetNotesExpanded->{put("type","setNotesExpanded");put("expanded",a.expanded)}
 is ReturnResolutionAction.Submit->{put("type","submit");put("optionId",a.optionId);put("sizeId",a.sizeId?.let{JsonPrimitive(it)} ?: JsonNull);put("acknowledgementAccepted",a.acknowledgementAccepted)}
 ReturnResolutionAction.KeepPurchase->put("type","keepPurchase")
 ReturnResolutionAction.Done->put("type","done")
 }
}.toString()
object ObserverBridge {
 @Composable fun Content(input:JsonObject,onEvent:(String)->Unit){
  MaterialTheme(colorScheme=if(isSystemInDarkTheme())darkColorScheme()else lightColorScheme()){
   ReturnResolutionCard(model=decodeReturnResolutionModel(input["model"]!!.jsonObject),onAction={onEvent(event(it))})
  }
 }
}
