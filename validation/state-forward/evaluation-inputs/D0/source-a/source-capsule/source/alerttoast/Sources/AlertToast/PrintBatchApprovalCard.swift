import SwiftUI

public struct PrintBatchJob: Equatable {
    public let id: String
    public let title: String
    public let pages: Int
    public let copies: Int
    public let isColor: Bool
    public let selected: Bool
    public let locked: Bool
    public init(id: String, title: String, pages: Int, copies: Int, isColor: Bool, selected: Bool, locked: Bool) {
        self.id=id;self.title=title;self.pages=pages;self.copies=copies;self.isColor=isColor;self.selected=selected;self.locked=locked
    }
}
public struct PrintBatchModel: Equatable {
    public let modelID: String
    public let budgetCredits: Int
    public let allowPriority: Bool
    public let initialPaperMode: String
    public let initialPriority: Bool
    public let initialExpanded: Bool
    public let jobs: [PrintBatchJob]
    public init(modelID: String, budgetCredits: Int, allowPriority: Bool, initialPaperMode: String, initialPriority: Bool, initialExpanded: Bool, jobs: [PrintBatchJob]) {
        self.modelID=modelID;self.budgetCredits=budgetCredits;self.allowPriority=allowPriority;self.initialPaperMode=initialPaperMode;self.initialPriority=initialPriority;self.initialExpanded=initialExpanded;self.jobs=jobs
    }
}
public struct PrintBatchPresentation {
    public let isDark: Bool
    public let textScale: Double
    public let isRTL: Bool
    public init(isDark: Bool, textScale: Double, isRTL: Bool) {self.isDark=isDark;self.textScale=textScale;self.isRTL=isRTL}
}
private struct BatchLocalState {
    var modelID: String
    var selected: Set<String>
    var mode: String
    var priority: Bool
    var expanded: Bool
    init(_ model: PrintBatchModel) {
        modelID=model.modelID;selected=Set(model.jobs.filter(\.selected).map(\.id));mode=model.initialPaperMode;priority=model.initialPriority;expanded=model.initialExpanded
    }
}
private struct BatchColors {
    let surface: Color;let text: Color;let muted: Color;let accent: Color;let ready: Color;let error: Color;let background: Color;let onAccent: Color
    init(_ dark: Bool) {
        surface=Color(batchHex:dark ? 0x1B2532:0xFFFFFF);text=Color(batchHex:dark ? 0xF2F5FA:0x14243A);muted=Color(batchHex:dark ? 0xB7C4D5:0x53657A);accent=Color(batchHex:dark ? 0x8BB0FF:0x265FE4);ready=Color(batchHex:dark ? 0x75D6AA:0x167650);error=Color(batchHex:dark ? 0xFF9A96:0xB63835);background=Color(batchHex:dark ? 0x10161F:0xF5F7FA);onAccent=Color(batchHex:dark ? 0x14243A:0xFFFFFF)
    }
}
private extension Color {
    init(batchHex: UInt32) {self.init(.sRGB,red:Double((batchHex>>16)&255)/255,green:Double((batchHex>>8)&255)/255,blue:Double(batchHex&255)/255,opacity:1)}
}

@available(iOS 14, macOS 11, *)
public struct PrintBatchApprovalCard: View {
    private let model: PrintBatchModel
    private let presentation: PrintBatchPresentation
    private let onEvent: (String,[String:Any])->Void
    @State private var local: BatchLocalState
    public init(model: PrintBatchModel, presentation: PrintBatchPresentation, onEvent: @escaping (String,[String:Any])->Void) {
        self.model=model;self.presentation=presentation;self.onEvent=onEvent;_local=State(initialValue:BatchLocalState(model))
    }
    // Incoming IDs are rendered from their defaults immediately, before onChange commits the reset.
    private var current: BatchLocalState { local.modelID==model.modelID ? local:BatchLocalState(model) }
    private var colors: BatchColors {BatchColors(presentation.isDark)}
    private var chosen: [PrintBatchJob] {model.jobs.filter{current.selected.contains($0.id)}}
    private func sheets(_ job: PrintBatchJob)->Int {(current.mode=="duplex" ? (job.pages+1)/2:job.pages)*job.copies}
    private func ink(_ job: PrintBatchJob)->Int {job.pages*job.copies*(job.isColor ? 3:1)}
    private var inkCost: Int {chosen.reduce(0){$0+ink($1)}}
    private var paperCost: Int {chosen.reduce(0){$0+sheets($1)}}
    private var printed: Int {chosen.reduce(0){$0+$1.pages*$1.copies}}
    private var surcharge: Int {!chosen.isEmpty && current.priority ? 6:0}
    private var total: Int {inkCost+paperCost+surcharge}
    private var over: Bool {total>model.budgetCredits}
    private var canApprove: Bool {!chosen.isEmpty && !over}
    private var canPrioritize: Bool {model.allowPriority && !chosen.isEmpty}
    private var status: String {chosen.isEmpty ? "No jobs":over ? "Over budget":"Ready"}
    private var statusColor: Color {chosen.isEmpty ? colors.muted:over ? colors.error:colors.ready}
    private var balance: String {chosen.isEmpty ? "No charge selected":over ? "Short by \(total-model.budgetCredits) cr":"Balance after approval: \(model.budgetCredits-total) cr"}
    private var approval: String {chosen.isEmpty ? "Select a job to approve":over ? "Over budget by \(total-model.budgetCredits) cr":"Approve \(chosen.count) jobs · \(total) cr"}
    private func font(_ size: Double,_ weight: Font.Weight = .regular)->Font {.system(size:size*presentation.textScale,weight:weight,design:.default)}
    private func text(_ value: String,_ id: String,_ size: Double=12,_ weight: Font.Weight = .regular,_ color: Color?=nil)->some View {
        Text(value).font(font(size,weight)).foregroundColor(color ?? colors.text).fixedSize(horizontal:false,vertical:true).accessibilityIdentifier("printbatch."+id)
    }
    public var body: some View {
        VStack(alignment:.leading,spacing:12) {
            HStack(alignment:.top,spacing:8) {
                text("Print budget check","title",20,.semibold).frame(maxWidth:.infinity,alignment:.leading).layoutPriority(1)
                text(status,"status",12,.semibold,statusColor).padding(.horizontal,10).padding(.vertical,4).background(statusColor.opacity(0.13)).cornerRadius(12)
            }
            VStack(alignment:.leading,spacing:6) {
                text("Estimated charge","charge.caption",12,.regular,colors.muted)
                text("\(total) cr","charge.value",28,.bold)
                text("\(chosen.count) jobs • \(printed) pages • \(paperCost) sheets","summary",14,.regular,colors.muted)
            }
            VStack(spacing:0) {
                ForEach(Array(model.jobs.enumerated()),id:\.element.id) { index,job in
                    jobRow(job).padding(.vertical,12)
                    if index<model.jobs.count-1 {Rectangle().fill(colors.muted.opacity(0.25)).frame(height:1).accessibilityHidden(true)}
                }
            }
            VStack(alignment:.leading,spacing:8) {
                text("Paper mode","mode.title",14,.semibold)
                HStack(spacing:8) {modeButton("single","Single-sided");modeButton("duplex","Duplex")}
            }
            VStack(alignment:.leading,spacing:4) {
                Toggle(isOn:Binding(get:{current.priority},set:{ value in
                    guard canPrioritize, value != current.priority else{return}
                    var next=current;next.priority=value;local=next;onEvent("priorityChanged",["priority":value])
                })) {Text("Priority handling").font(font(14,.semibold)).foregroundColor(canPrioritize ? colors.text:colors.muted).fixedSize(horizontal:false,vertical:true)}
                    .toggleStyle(SwitchToggleStyle(tint:colors.accent)).frame(minHeight:48).disabled(!canPrioritize).accessibilityIdentifier("printbatch.priority")
                text(!model.allowPriority ? "Priority unavailable for this batch.":current.priority ? "Adds 6 cr to this batch.":"Add 6 cr for priority handling.","priority.helper",12,.regular,colors.muted)
            }
            Button(action:{var next=current;next.expanded.toggle();local=next;onEvent("breakdownChanged",["expanded":next.expanded])}) {
                Text(current.expanded ? "Hide cost breakdown":"Show cost breakdown").font(font(14,.semibold)).foregroundColor(colors.accent).fixedSize(horizontal:false,vertical:true).frame(maxWidth:.infinity,minHeight:48,alignment:.leading).contentShape(Rectangle())
            }.buttonStyle(PlainButtonStyle()).accessibilityIdentifier("printbatch.breakdown.toggle").accessibilityValue(current.expanded ? "Expanded":"Collapsed")
            if current.expanded {
                VStack(alignment:.leading,spacing:12) {
                    detail("ink","Ink",inkCost);detail("paper","Paper",paperCost);detail("priority","Priority",surcharge);detail("total","Total",total)
                }
            }
            text(balance,"balance",14,.regular,over && !chosen.isEmpty ? colors.error:colors.text)
            Button(action:approve) {
                Text(approval).font(font(14,.semibold)).foregroundColor(canApprove ? colors.onAccent:colors.muted).fixedSize(horizontal:false,vertical:true).padding(.horizontal,8).padding(.vertical,10).frame(maxWidth:.infinity,minHeight:48).background(canApprove ? colors.accent:colors.muted.opacity(0.12)).cornerRadius(10).contentShape(Rectangle())
            }.buttonStyle(PlainButtonStyle()).disabled(!canApprove).accessibilityIdentifier("printbatch.approve")
        }
        .padding(16).frame(maxWidth:.infinity,alignment:.leading).background(colors.surface).cornerRadius(16)
        .accessibilityElement(children:.contain).accessibilityIdentifier("printbatch.card")
        .environment(\.layoutDirection,presentation.isRTL ? .rightToLeft:.leftToRight)
        .onChange(of:model.modelID) {_ in local=BatchLocalState(model)}
    }
    private func jobRow(_ job: PrintBatchJob)->some View {
        let selected=current.selected.contains(job.id)
        return HStack(alignment:.top,spacing:8) {
            Button(action:{
                guard !job.locked else{return};var next=current
                if selected {next.selected.remove(job.id)}else{next.selected.insert(job.id)}
                local=next;onEvent("selectionChanged",["jobIDs":model.jobs.filter{next.selected.contains($0.id)}.map(\.id)])
            }) {
                Image(systemName:selected ? "checkmark.square.fill":"square").font(.system(size:22,weight:.regular)).foregroundColor(job.locked ? colors.muted:selected ? colors.accent:colors.muted).frame(width:48,height:48).background(job.locked ? colors.muted.opacity(0.08):Color.clear).cornerRadius(8).contentShape(Rectangle())
            }.buttonStyle(PlainButtonStyle()).disabled(job.locked).accessibilityIdentifier("printbatch.job.\(job.id).toggle").accessibilityLabel((selected ? "Deselect ":"Select ")+job.title).accessibilityValue(selected ? "Selected":"Not selected").accessibilityAddTraits(selected ? [.isSelected]:[])
            VStack(alignment:.leading,spacing:6) {
                text(job.title,"job.\(job.id).title",14,.semibold)
                text("\(job.pages) pages × \(job.copies) copies • \(job.isColor ? "Color":"Mono")\(job.locked ? " • Locked":"")","job.\(job.id).subtitle",12,.regular,colors.muted)
            }.frame(maxWidth:.infinity,alignment:.leading).layoutPriority(1)
            text("\(ink(job)+sheets(job)) cr","job.\(job.id).price",14).layoutPriority(2)
        }.frame(maxWidth:.infinity,alignment:.leading)
    }
    private func modeButton(_ mode: String,_ title: String)->some View {
        let selected=current.mode==mode
        return Button(action:{guard !selected else{return};var next=current;next.mode=mode;local=next;onEvent("paperModeChanged",["paperMode":mode])}) {
            Text(title).font(font(14,.semibold)).foregroundColor(selected ? colors.onAccent:colors.text).fixedSize(horizontal:false,vertical:true).padding(.horizontal,8).padding(.vertical,10).frame(maxWidth:.infinity,minHeight:48).background(selected ? colors.accent:colors.surface).cornerRadius(10).contentShape(Rectangle())
        }.buttonStyle(PlainButtonStyle()).accessibilityIdentifier("printbatch.mode."+mode).accessibilityValue(selected ? "Selected":"Not selected").accessibilityAddTraits(selected ? [.isSelected]:[])
    }
    private func detail(_ id: String,_ label: String,_ value: Int)->some View {
        HStack(alignment:.top,spacing:12) {text(label,"breakdown.\(id).label",12,.regular,colors.muted).frame(maxWidth:.infinity,alignment:.leading);text("\(value) cr","breakdown.\(id).value",12,.regular,colors.muted)}
    }
    private func approve() {
        guard canApprove else{return}
        onEvent("approve",["modelID":model.modelID,"jobIDs":chosen.map(\.id),"paperMode":current.mode,"priority":current.priority,"totalCredits":total,"printedPages":printed,"sheets":paperCost])
    }
}
