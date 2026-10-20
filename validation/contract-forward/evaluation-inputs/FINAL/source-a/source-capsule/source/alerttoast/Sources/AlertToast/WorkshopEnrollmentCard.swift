import SwiftUI

public struct WorkshopCourse: Codable, Equatable {
    public var id: String
    public var title: String
    public var detail: String
    public var seatPriceCents: Int
    public var capacity: Int
    public var onsiteAvailable: Bool
    public var workbookAvailable: Bool

    public init(id: String, title: String, detail: String, seatPriceCents: Int,
                capacity: Int, onsiteAvailable: Bool, workbookAvailable: Bool) {
        self.id = id
        self.title = title
        self.detail = detail
        self.seatPriceCents = seatPriceCents
        self.capacity = capacity
        self.onsiteAvailable = onsiteAvailable
        self.workbookAvailable = workbookAvailable
    }
}

public struct WorkshopCatalog: Codable, Equatable {
    public var title: String
    public var detail: String
    public var courses: [WorkshopCourse]
    public var remoteDiscountCents: Int
    public var onsiteFeeCents: Int
    public var workbookCents: Int

    public init(title: String, detail: String, courses: [WorkshopCourse],
                remoteDiscountCents: Int, onsiteFeeCents: Int, workbookCents: Int) {
        self.title = title
        self.detail = detail
        self.courses = courses
        self.remoteDiscountCents = remoteDiscountCents
        self.onsiteFeeCents = onsiteFeeCents
        self.workbookCents = workbookCents
    }
}

public enum WorkshopAttendance: String, Codable { case remote, onsite }

public struct WorkshopReservation: Equatable {
    public var courseID: String
    public var mode: WorkshopAttendance
    public var seats: Int
    public var workbook: Bool

    public init(courseID: String, mode: WorkshopAttendance, seats: Int, workbook: Bool) {
        self.courseID = courseID
        self.mode = mode
        self.seats = seats
        self.workbook = workbook
    }
}

private struct WorkshopDraft {
    var courseID: String?
    var mode: WorkshopAttendance = .remote
    var seats: Int
    var workbook = false
    var confirmed = false

    init(catalog: WorkshopCatalog) {
        courseID = catalog.courses.first(where: { $0.capacity >= 1 })?.id
        seats = courseID == nil ? 0 : 1
    }

    mutating func reconcile(catalog: WorkshopCatalog) {
        confirmed = false
        let wasEmpty = courseID == nil
        let preserved = catalog.courses.first { $0.id == courseID && $0.capacity >= 1 }
        guard let course = preserved ?? catalog.courses.first(where: { $0.capacity >= 1 }) else {
            courseID = nil
            mode = .remote
            seats = 0
            workbook = false
            return
        }
        courseID = course.id
        if wasEmpty { seats = 1 }
        reconcileChoices(course: course)
    }

    mutating func reconcileChoices(course: WorkshopCourse) {
        if !course.onsiteAvailable { mode = .remote }
        if ![1, 3, 6].contains(seats) || seats > course.capacity {
            seats = [6, 3, 1].first(where: { $0 <= course.capacity }) ?? 0
        }
        if mode == .remote || !course.workbookAvailable { workbook = false }
    }
}

@available(iOS 14, macOS 11, *)
public struct WorkshopEnrollmentCard: View {
    public var catalog: WorkshopCatalog
    private let onReserve: (WorkshopReservation) -> Void
    @State private var draft: WorkshopDraft
    @Environment(\.colorScheme) private var colorScheme
    @ScaledMetric(relativeTo: .title2) private var titleSize: CGFloat = 22
    @ScaledMetric(relativeTo: .body) private var bodySize: CGFloat = 16
    @ScaledMetric(relativeTo: .subheadline) private var sectionSize: CGFloat = 14
    @ScaledMetric(relativeTo: .headline) private var totalSize: CGFloat = 18

    public init(catalog: WorkshopCatalog, onReserve: @escaping (WorkshopReservation) -> Void) {
        self.catalog = catalog
        self.onReserve = onReserve
        _draft = State(initialValue: WorkshopDraft(catalog: catalog))
    }

    private var course: WorkshopCourse? {
        catalog.courses.first { $0.id == draft.courseID && $0.capacity >= 1 }
    }
    private var dark: Bool { colorScheme == .dark }
    private var ink: Color { rgb(dark ? 0xF1F5F9 : 0x172B3A) }
    private var bodyInk: Color { rgb(dark ? 0xCBD5E1 : 0x425466) }
    private var surface: Color { rgb(dark ? 0x182635 : 0xFFFFFF) }
    private var selectedFill: Color { rgb(dark ? 0x233E52 : 0xE7F2F8) }
    private var accent: Color { rgb(dark ? 0x8ACBEE : 0x155E83) }
    private var valid: Bool { course != nil && [1, 3, 6].contains(draft.seats) && draft.seats <= (course?.capacity ?? 0) }
    private var total: Int {
        guard let course = course else { return 0 }
        let seatPrice = course.seatPriceCents - (draft.mode == .remote ? catalog.remoteDiscountCents : 0)
        return draft.seats * (seatPrice + (draft.workbook ? catalog.workbookCents : 0))
            + (draft.mode == .onsite ? catalog.onsiteFeeCents : 0)
    }
    private var totalLabel: String {
        let cents = total
        let money = "\(cents / 100)." + String(format: "%02d", cents % 100)
        return "Total $\(money) · \(draft.seats) \(draft.seats == 1 ? "seat" : "seats") · \(draft.mode == .remote ? "Remote" : "In person") · \(draft.workbook ? "Workbooks" : "No workbooks")"
    }
    private var status: String {
        guard let course = course else { return "No courses available." }
        return draft.confirmed
            ? "Reserved \(draft.seats) \(draft.seats == 1 ? "seat" : "seats") for \(course.title)."
            : "Choose options, then reserve."
    }

    public var body: some View {
        VStack(alignment: .leading, spacing: 20) {
            VStack(alignment: .leading, spacing: 8) {
                Text(catalog.title)
                    .font(.system(size: titleSize, weight: .semibold))
                    .foregroundColor(ink)
                    .fixedSize(horizontal: false, vertical: true)
                    .accessibilityIdentifier("enroll.title")
                Text(catalog.detail)
                    .font(.system(size: bodySize))
                    .foregroundColor(bodyInk)
                    .fixedSize(horizontal: false, vertical: true)
                    .accessibilityIdentifier("enroll.detail")
            }
            VStack(alignment: .leading, spacing: 8) {
                section("Courses")
                ForEach(catalog.courses, id: \.id) { item in
                    VStack(alignment: .leading, spacing: 8) {
                        option(item.title, identifier: "enroll.course.\(item.id)",
                               selected: draft.courseID == item.id,
                               enabled: !draft.confirmed && item.capacity >= 1 && course != nil) {
                            draft.courseID = item.id
                            draft.reconcileChoices(course: item)
                        }
                        Text(item.detail)
                            .font(.system(size: bodySize))
                            .foregroundColor(bodyInk)
                            .fixedSize(horizontal: false, vertical: true)
                            .padding(.horizontal, 12)
                    }
                }
            }
            VStack(alignment: .leading, spacing: 8) {
                section("Attendance")
                option("Remote", identifier: "enroll.mode.remote", selected: draft.mode == .remote,
                       enabled: !draft.confirmed && course != nil) {
                    draft.mode = .remote
                    draft.workbook = false
                }
                option("In person", identifier: "enroll.mode.onsite", selected: draft.mode == .onsite,
                       enabled: !draft.confirmed && course?.onsiteAvailable == true) {
                    draft.mode = .onsite
                }
            }
            VStack(alignment: .leading, spacing: 8) {
                section("Seats")
                ForEach([1, 3, 6], id: \.self) { seats in
                    option("\(seats) \(seats == 1 ? "seat" : "seats")", identifier: "enroll.seats.\(seats)",
                           selected: draft.seats == seats,
                           enabled: !draft.confirmed && course != nil && seats <= (course?.capacity ?? 0)) {
                        draft.seats = seats
                    }
                }
            }
            option("Printed workbook", identifier: "enroll.workbook", selected: draft.workbook,
                   enabled: !draft.confirmed && draft.mode == .onsite && course?.workbookAvailable == true) {
                draft.workbook.toggle()
            }
            Text(totalLabel)
                .font(.system(size: totalSize, weight: .semibold))
                .foregroundColor(ink)
                .fixedSize(horizontal: false, vertical: true)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(12)
                .background(selectedFill)
                .cornerRadius(8)
                .accessibilityIdentifier("enroll.total")
            Text(status)
                .font(.system(size: bodySize))
                .foregroundColor(bodyInk)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityIdentifier("enroll.status")
            VStack(spacing: 8) {
                action("Reserve seats", identifier: "enroll.reserve", enabled: valid && !draft.confirmed, primary: true) {
                    guard valid, !draft.confirmed, let course = course else { return }
                    draft.confirmed = true
                    onReserve(WorkshopReservation(courseID: course.id, mode: draft.mode,
                                                  seats: draft.seats, workbook: draft.workbook))
                }
                action("Edit selection", identifier: "enroll.edit", enabled: draft.confirmed, primary: false) {
                    guard draft.confirmed else { return }
                    draft.confirmed = false
                }
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(16)
        .background(surface)
        .cornerRadius(16)
        .onChange(of: catalog) { replacement in draft.reconcile(catalog: replacement) }
    }

    private func section(_ title: String) -> some View {
        Text(title).font(.system(size: sectionSize, weight: .semibold)).foregroundColor(ink)
    }

    private func option(_ title: String, identifier: String, selected: Bool, enabled: Bool,
                        perform: @escaping () -> Void) -> some View {
        Button(action: { if enabled { perform() } }) {
            HStack(alignment: .firstTextBaseline, spacing: 6) {
                Text(selected ? "●" : "○").accessibilityHidden(true)
                Text(title).fixedSize(horizontal: false, vertical: true)
            }
            .font(.system(size: bodySize, weight: .semibold))
            .foregroundColor(ink)
            .frame(maxWidth: .infinity, minHeight: 20, alignment: .leading)
            .padding(12)
            .background(selected ? selectedFill : surface)
            .overlay(RoundedRectangle(cornerRadius: 8).stroke(selected ? accent : bodyInk, lineWidth: 1))
            .cornerRadius(8)
            .contentShape(Rectangle())
        }
        .buttonStyle(WorkshopEnrollmentButtonStyle())
        .accessibilityLabel(Text(title))
        .accessibilityIdentifier(identifier)
        .accessibilityAddTraits(selected ? .isSelected : [])
        .disabled(!enabled)
        .opacity(enabled ? 1 : 0.62)
    }

    private func action(_ title: String, identifier: String, enabled: Bool, primary: Bool,
                        perform: @escaping () -> Void) -> some View {
        Button(action: { if enabled { perform() } }) {
            Text(title)
                .font(.system(size: bodySize, weight: .semibold))
                .fixedSize(horizontal: false, vertical: true)
                .frame(maxWidth: .infinity, minHeight: 20, alignment: .leading)
                .padding(12)
                .foregroundColor(primary ? (dark ? rgb(0x172B3A) : .white) : ink)
                .background(primary ? accent : selectedFill)
                .cornerRadius(8)
                .contentShape(Rectangle())
        }
        .buttonStyle(WorkshopEnrollmentButtonStyle())
        .accessibilityIdentifier(identifier)
        .disabled(!enabled)
        .opacity(enabled ? 1 : 0.62)
    }

    private func rgb(_ hex: UInt32) -> Color {
        Color(red: Double((hex >> 16) & 255) / 255,
              green: Double((hex >> 8) & 255) / 255,
              blue: Double(hex & 255) / 255)
    }
}


/// Keep the explicit card palette when disabled; the controls apply one readable
/// disabled opacity while Button still supplies its native disabled semantics.
@available(iOS 14, macOS 11, *)
private struct WorkshopEnrollmentButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label.opacity(configuration.isPressed ? 0.85 : 1)
    }
}
