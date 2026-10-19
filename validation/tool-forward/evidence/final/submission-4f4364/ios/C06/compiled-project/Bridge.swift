import SwiftUI
import AlertToast
import Foundation

private func decodeReturnResolutionModel(_ o:[String:Any]) -> ReturnResolutionModel {
 ReturnResolutionModel(
  caseId: o["caseId"] as? String ?? "",
  merchant: o["merchant"] as? String ?? "",
  heading: o["heading"] as? String ?? "",
  orderReference: o["orderReference"] as? String ?? "",
  intro: o["intro"] as? String ?? "",
  status: ["editing": ReturnResolutionStatus.editing, "submitting": .submitting, "complete": .complete][o["status"] as! String]!,
  statusLabel: o["statusLabel"] as? String ?? "",
  item: decodeReturnResolutionItem(o["item"] as! [String:Any]),
  deadline: (o["deadline"] as? [String:Any]).map { decodeReturnResolutionDeadline($0) },
  contextMessage: o["contextMessage"] as? String ?? "",
  optionsTitle: o["optionsTitle"] as? String ?? "",
  options: (o["options"] as? [[String:Any]] ?? []).map { decodeReturnResolutionOption($0) },
  selectedOptionId: o["selectedOptionId"] as? String,
  sizesTitle: o["sizesTitle"] as? String ?? "",
  sizes: (o["sizes"] as? [[String:Any]] ?? []).map { decodeReturnResolutionSize($0) },
  selectedSizeId: o["selectedSizeId"] as? String,
  acknowledgementAccepted: o["acknowledgementAccepted"] as? Bool ?? false,
  notes: decodeReturnResolutionNotes(o["notes"] as! [String:Any]),
  notesExpanded: o["notesExpanded"] as? Bool ?? false,
  amountRows: (o["amountRows"] as? [[String:Any]] ?? []).map { decodeReturnResolutionAmountRow($0) },
  totalLabel: o["totalLabel"] as? String ?? "",
  totalValue: o["totalValue"] as? String ?? "",
  totalFootnote: o["totalFootnote"] as? String ?? "",
  idlePrimaryLabel: o["idlePrimaryLabel"] as? String ?? "",
  keepLabel: o["keepLabel"] as? String ?? "",
  progressTitle: o["progressTitle"] as? String ?? "",
  progressBody: o["progressBody"] as? String ?? "",
  resultTitle: o["resultTitle"] as? String ?? "",
  resultBody: o["resultBody"] as? String ?? "",
  resultReference: o["resultReference"] as? String ?? "",
  doneLabel: o["doneLabel"] as? String ?? "",
  strings: decodeReturnResolutionStrings(o["strings"] as! [String:Any])
 )
}
private func decodeReturnResolutionItem(_ o:[String:Any]) -> ReturnResolutionItem {
 ReturnResolutionItem(
  title: o["title"] as? String ?? "",
  variant: o["variant"] as? String ?? "",
  quantityLabel: o["quantityLabel"] as? String ?? "",
  paidLabel: o["paidLabel"] as? String ?? "",
  accent: ["teal": ReturnResolutionAccent.teal, "coral": .coral, "indigo": .indigo][o["accent"] as! String]!
 )
}
private func decodeReturnResolutionDeadline(_ o:[String:Any]) -> ReturnResolutionDeadline {
 ReturnResolutionDeadline(
  text: o["text"] as? String ?? "",
  urgent: o["urgent"] as? Bool ?? false
 )
}
private func decodeReturnResolutionOption(_ o:[String:Any]) -> ReturnResolutionOption {
 ReturnResolutionOption(
  id: o["id"] as? String ?? "",
  kind: ["refund": ReturnResolutionKind.refund, "credit": .credit, "exchange": .exchange][o["kind"] as! String]!,
  title: o["title"] as? String ?? "",
  description: o["description"] as? String ?? "",
  amountLabel: o["amountLabel"] as? String ?? "",
  tag: o["tag"] as? String,
  disabledReason: o["disabledReason"] as? String,
  detailTitle: o["detailTitle"] as? String ?? "",
  detailBody: o["detailBody"] as? String ?? "",
  acknowledgementLabel: o["acknowledgementLabel"] as? String,
  primaryLabel: o["primaryLabel"] as? String ?? ""
 )
}
private func decodeReturnResolutionSize(_ o:[String:Any]) -> ReturnResolutionSize {
 ReturnResolutionSize(
  id: o["id"] as? String ?? "",
  label: o["label"] as? String ?? "",
  unavailableReason: o["unavailableReason"] as? String
 )
}
private func decodeReturnResolutionNotes(_ o:[String:Any]) -> ReturnResolutionNotes {
 ReturnResolutionNotes(
  title: o["title"] as? String ?? "",
  body: o["body"] as? String ?? "",
  bullets: (o["bullets"] as? [String] ?? [])
 )
}
private func decodeReturnResolutionAmountRow(_ o:[String:Any]) -> ReturnResolutionAmountRow {
 ReturnResolutionAmountRow(
  id: o["id"] as? String ?? "",
  label: o["label"] as? String ?? "",
  value: o["value"] as? String ?? "",
  emphasized: o["emphasized"] as? Bool ?? false
 )
}
private func decodeReturnResolutionStrings(_ o:[String:Any]) -> ReturnResolutionStrings {
 ReturnResolutionStrings(
  chooseOption: o["chooseOption"] as? String ?? "",
  chooseSize: o["chooseSize"] as? String ?? "",
  acceptTerms: o["acceptTerms"] as? String ?? "",
  ready: o["ready"] as? String ?? "",
  noOptions: o["noOptions"] as? String ?? "",
  checkedValue: o["checkedValue"] as? String ?? "",
  uncheckedValue: o["uncheckedValue"] as? String ?? "",
  expandedValue: o["expandedValue"] as? String ?? "",
  collapsedValue: o["collapsedValue"] as? String ?? "",
  busyValue: o["busyValue"] as? String ?? ""
 )
}
private func event(_ a:ReturnResolutionAction)->String {
 var o:[String:Any]=[:]
 switch a {
 case let .selectOption(optionId): o=["type":"selectOption","optionId":optionId]
 case let .selectSize(sizeId): o=["type":"selectSize","sizeId":sizeId]
 case let .setAcknowledgement(accepted): o=["type":"setAcknowledgement","accepted":accepted]
 case let .setNotesExpanded(expanded): o=["type":"setNotesExpanded","expanded":expanded]
 case let .submit(optionId,sizeId,acknowledgementAccepted): o=["type":"submit","optionId":optionId,"sizeId":sizeId.map { $0 as Any } ?? NSNull(),"acknowledgementAccepted":acknowledgementAccepted]
 case .keepPurchase: o=["type":"keepPurchase"]
 case .done: o=["type":"done"]
 }
 return String(data:try! JSONSerialization.data(withJSONObject:o,options:[.sortedKeys]),encoding:.utf8)!
}
enum ObserverBridge {
 static func make(fixture:[String:Any],onEvent:@escaping(String)->Void)->AnyView {
  AnyView(ReturnResolutionCard(model:decodeReturnResolutionModel(fixture["model"] as! [String:Any]),onAction:{onEvent(event($0))}))
 }
}
