import SwiftUI
public enum ReturnResolutionStatus { case editing, submitting, complete }
public enum ReturnResolutionKind { case refund, credit, exchange }
public enum ReturnResolutionAccent { case teal, coral, indigo }
public struct ReturnResolutionModel {
 public let caseId: String
 public let merchant: String
 public let heading: String
 public let orderReference: String
 public let intro: String
 public let status: ReturnResolutionStatus
 public let statusLabel: String
 public let item: ReturnResolutionItem
 public let deadline: ReturnResolutionDeadline?
 public let contextMessage: String
 public let optionsTitle: String
 public let options: [ReturnResolutionOption]
 public let selectedOptionId: String?
 public let sizesTitle: String
 public let sizes: [ReturnResolutionSize]
 public let selectedSizeId: String?
 public let acknowledgementAccepted: Bool
 public let notes: ReturnResolutionNotes
 public let notesExpanded: Bool
 public let amountRows: [ReturnResolutionAmountRow]
 public let totalLabel: String
 public let totalValue: String
 public let totalFootnote: String
 public let idlePrimaryLabel: String
 public let keepLabel: String
 public let progressTitle: String
 public let progressBody: String
 public let resultTitle: String
 public let resultBody: String
 public let resultReference: String
 public let doneLabel: String
 public let strings: ReturnResolutionStrings
 public init(caseId: String, merchant: String, heading: String, orderReference: String, intro: String, status: ReturnResolutionStatus, statusLabel: String, item: ReturnResolutionItem, deadline: ReturnResolutionDeadline?, contextMessage: String, optionsTitle: String, options: [ReturnResolutionOption], selectedOptionId: String?, sizesTitle: String, sizes: [ReturnResolutionSize], selectedSizeId: String?, acknowledgementAccepted: Bool, notes: ReturnResolutionNotes, notesExpanded: Bool, amountRows: [ReturnResolutionAmountRow], totalLabel: String, totalValue: String, totalFootnote: String, idlePrimaryLabel: String, keepLabel: String, progressTitle: String, progressBody: String, resultTitle: String, resultBody: String, resultReference: String, doneLabel: String, strings: ReturnResolutionStrings){self.caseId=caseId;self.merchant=merchant;self.heading=heading;self.orderReference=orderReference;self.intro=intro;self.status=status;self.statusLabel=statusLabel;self.item=item;self.deadline=deadline;self.contextMessage=contextMessage;self.optionsTitle=optionsTitle;self.options=options;self.selectedOptionId=selectedOptionId;self.sizesTitle=sizesTitle;self.sizes=sizes;self.selectedSizeId=selectedSizeId;self.acknowledgementAccepted=acknowledgementAccepted;self.notes=notes;self.notesExpanded=notesExpanded;self.amountRows=amountRows;self.totalLabel=totalLabel;self.totalValue=totalValue;self.totalFootnote=totalFootnote;self.idlePrimaryLabel=idlePrimaryLabel;self.keepLabel=keepLabel;self.progressTitle=progressTitle;self.progressBody=progressBody;self.resultTitle=resultTitle;self.resultBody=resultBody;self.resultReference=resultReference;self.doneLabel=doneLabel;self.strings=strings;}
}
public struct ReturnResolutionItem {
 public let title: String
 public let variant: String
 public let quantityLabel: String
 public let paidLabel: String
 public let accent: ReturnResolutionAccent
 public init(title: String, variant: String, quantityLabel: String, paidLabel: String, accent: ReturnResolutionAccent){self.title=title;self.variant=variant;self.quantityLabel=quantityLabel;self.paidLabel=paidLabel;self.accent=accent;}
}
public struct ReturnResolutionDeadline {
 public let text: String
 public let urgent: Bool
 public init(text: String, urgent: Bool){self.text=text;self.urgent=urgent;}
}
public struct ReturnResolutionOption {
 public let id: String
 public let kind: ReturnResolutionKind
 public let title: String
 public let description: String
 public let amountLabel: String
 public let tag: String?
 public let disabledReason: String?
 public let detailTitle: String
 public let detailBody: String
 public let acknowledgementLabel: String?
 public let primaryLabel: String
 public init(id: String, kind: ReturnResolutionKind, title: String, description: String, amountLabel: String, tag: String?, disabledReason: String?, detailTitle: String, detailBody: String, acknowledgementLabel: String?, primaryLabel: String){self.id=id;self.kind=kind;self.title=title;self.description=description;self.amountLabel=amountLabel;self.tag=tag;self.disabledReason=disabledReason;self.detailTitle=detailTitle;self.detailBody=detailBody;self.acknowledgementLabel=acknowledgementLabel;self.primaryLabel=primaryLabel;}
}
public struct ReturnResolutionSize {
 public let id: String
 public let label: String
 public let unavailableReason: String?
 public init(id: String, label: String, unavailableReason: String?){self.id=id;self.label=label;self.unavailableReason=unavailableReason;}
}
public struct ReturnResolutionNotes {
 public let title: String
 public let body: String
 public let bullets: [String]
 public init(title: String, body: String, bullets: [String]){self.title=title;self.body=body;self.bullets=bullets;}
}
public struct ReturnResolutionAmountRow {
 public let id: String
 public let label: String
 public let value: String
 public let emphasized: Bool
 public init(id: String, label: String, value: String, emphasized: Bool){self.id=id;self.label=label;self.value=value;self.emphasized=emphasized;}
}
public struct ReturnResolutionStrings {
 public let chooseOption: String
 public let chooseSize: String
 public let acceptTerms: String
 public let ready: String
 public let noOptions: String
 public let checkedValue: String
 public let uncheckedValue: String
 public let expandedValue: String
 public let collapsedValue: String
 public let busyValue: String
 public init(chooseOption: String, chooseSize: String, acceptTerms: String, ready: String, noOptions: String, checkedValue: String, uncheckedValue: String, expandedValue: String, collapsedValue: String, busyValue: String){self.chooseOption=chooseOption;self.chooseSize=chooseSize;self.acceptTerms=acceptTerms;self.ready=ready;self.noOptions=noOptions;self.checkedValue=checkedValue;self.uncheckedValue=uncheckedValue;self.expandedValue=expandedValue;self.collapsedValue=collapsedValue;self.busyValue=busyValue;}
}
public enum ReturnResolutionAction {case selectOption(optionId:String), selectSize(sizeId:String), setAcknowledgement(accepted:Bool), setNotesExpanded(expanded:Bool), submit(optionId:String,sizeId:String?,acknowledgementAccepted:Bool), keepPurchase, done}
public struct ReturnResolutionCard:View {let model:ReturnResolutionModel;let onAction:(ReturnResolutionAction)->Void;public init(model:ReturnResolutionModel,onAction:@escaping(ReturnResolutionAction)->Void){self.model=model;self.onAction=onAction};public var body:some View{Text(model.heading)}}
import SwiftUI
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
