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

/// A local enrollment draft. The parent owns scrolling and can replace the catalog
/// without replacing this view's identity.
public struct WorkshopEnrollmentCard: View {
    public var catalog: WorkshopCatalog
    private let onReserve: (WorkshopReservation) -> Void
    @Environment(\.colorScheme) private var colorScheme
    @State private var courseID: String?
    @State private var mode: WorkshopAttendance = .remote
    @State private var seats: Int
    @State private var workbook = false
    @State private var confirmed = false
    @ScaledMetric(relativeTo: .title2) private var titleSize: CGFloat = 22
    @ScaledMetric(relativeTo: .body) private var bodySize: CGFloat = 16
    @ScaledMetric(relativeTo: .subheadline) private var sectionSize: CGFloat = 14
    @ScaledMetric(relativeTo: .headline) private var totalSize: CGFloat = 18

    public init(catalog: WorkshopCatalog, onReserve: @escaping (WorkshopReservation) -> Void) {
        self.catalog = catalog
        self.onReserve = onReserve
        let first = catalog.courses.first { $0.capacity >= 1 }
        _courseID = State(initialValue: first?.id)
        _seats = State(initialValue: first == nil ? 0 : 1)
    }

    private var course: WorkshopCourse? {
        catalog.courses.first { $0.id == courseID && $0.capacity >= 1 }
    }
    private var dark: Bool { colorScheme == .dark }
    private var ink: Color { color(dark ? 0xF1F5F9 : 0x172B3A) }
    private var bodyInk: Color { color(dark ? 0xCBD5E1 : 0x425466) }
    private var surface: Color { color(dark ? 0x182635 : 0xFFFFFF) }
    private var selectedFill: Color { color(dark ? 0x233E52 : 0xE7F2F8) }
    private var accent: Color { color(dark ? 0x8ACBEE : 0x155E83) }
    private var workbookAvailable: Bool {
        mode == .onsite && course?.onsiteAvailable == true && course?.workbookAvailable == true
    }
    private var valid: Bool {
        guard let course = course else { return false }
        return [1, 3, 6].contains(seats) && seats <= course.capacity
            && (mode == .remote || course.onsiteAvailable)
            && (!workbook || workbookAvailable)
    }
    private var total: String {
        let price: Int
        if let course = course {
            price = seats * (course.seatPriceCents - (mode == .remote ? catalog.remoteDiscountCents : 0))
                + (workbook ? seats * catalog.workbookCents : 0)
                + (mode == .onsite ? catalog.onsiteFeeCents : 0)
        } else { price = 0 }
        let money = "\(price / 100)." + String(format: "%02d", price % 100)
        return "Total $\(money) · \(seats) \(seats == 1 ? "seat" : "seats") · \(mode == .remote ? "Remote" : "In person") · \(workbook ? "Workbooks" : "No workbooks")"
    }
    private var status: String {
        guard let course = course else { return "No courses available." }
        return confirmed
            ? "Reserved \(seats) \(seats == 1 ? "seat" : "seats") for \(course.title)."
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
                    option(item.title, id: "enroll.course.\(item.id)", selected: courseID == item.id,
                           enabled: !confirmed && item.capacity >= 1 && course != nil) {
                        guard !confirmed, item.capacity >= 1 else { return }
                        courseID = item.id
                        reconcileDraft(with: item)
                    }
                    Text(item.detail)
                        .font(.system(size: bodySize))
                        .foregroundColor(bodyInk)
                        .fixedSize(horizontal: false, vertical: true)
                        .padding(.horizontal, 12)
                }
            }
            VStack(alignment: .leading, spacing: 8) {
                section("Attendance")
                option("Remote", id: "enroll.mode.remote", selected: mode == .remote,
                       enabled: course != nil && !confirmed) {
                    guard course != nil, !confirmed else { return }
                    mode = .remote
                    workbook = false
                }
                option("In person", id: "enroll.mode.onsite", selected: mode == .onsite,
                       enabled: course?.onsiteAvailable == true && !confirmed) {
                    guard course?.onsiteAvailable == true, !confirmed else { return }
                    mode = .onsite
                }
            }
            VStack(alignment: .leading, spacing: 8) {
                section("Seats")
                ForEach([1, 3, 6], id: \.self) { count in
                    option("\(count) \(count == 1 ? "seat" : "seats")", id: "enroll.seats.\(count)",
                           selected: seats == count,
                           enabled: !confirmed && (course?.capacity ?? 0) >= count) {
                        guard !confirmed, (course?.capacity ?? 0) >= count else { return }
                        seats = count
                    }
                }
            }
            option("Printed workbook", id: "enroll.workbook", selected: workbook,
                   enabled: workbookAvailable && !confirmed) {
                guard workbookAvailable, !confirmed else { return }
                workbook.toggle()
            }
            Text(total)
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
                action("Reserve seats", id: "enroll.reserve", enabled: valid && !confirmed, primary: true) {
                    guard valid, !confirmed, let course = course else { return }
                    confirmed = true
                    onReserve(WorkshopReservation(courseID: course.id, mode: mode, seats: seats, workbook: workbook))
                }
                action("Edit selection", id: "enroll.edit", enabled: confirmed, primary: false) {
                    guard confirmed else { return }
                    confirmed = false
                }
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(16)
        .background(surface)
        .cornerRadius(16)
        .onChange(of: catalog) { updated in
            confirmed = false
            let next = updated.courses.first { $0.id == courseID && $0.capacity >= 1 }
                ?? updated.courses.first { $0.capacity >= 1 }
            courseID = next?.id
            reconcileDraft(with: next)
        }
    }

    private func reconcileDraft(with course: WorkshopCourse?) {
        guard let course = course else {
            mode = .remote
            seats = 0
            workbook = false
            return
        }
        if !course.onsiteAvailable { mode = .remote }
        if seats == 0 { seats = 1 }
        if ![1, 3, 6].contains(seats) || seats > course.capacity {
            seats = [6, 3, 1].first { $0 <= course.capacity } ?? 0
        }
        if mode == .remote || !course.workbookAvailable || !course.onsiteAvailable { workbook = false }
    }

    private func section(_ text: String) -> some View {
        Text(text).font(.system(size: sectionSize, weight: .semibold)).foregroundColor(ink)
    }
    private func option(_ text: String, id: String, selected: Bool, enabled: Bool,
                        perform: @escaping () -> Void) -> some View {
        Button(action: perform) {
            HStack(alignment: .firstTextBaseline, spacing: 6) {
                Text(selected ? "●" : "○").accessibilityHidden(true)
                Text(text).fixedSize(horizontal: false, vertical: true)
            }
            .font(.system(size: bodySize, weight: .semibold))
            .foregroundColor(ink)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(12)
            .frame(minHeight: 44)
            .background(selected ? selectedFill : surface)
            .overlay(RoundedRectangle(cornerRadius: 8).stroke(selected ? accent : bodyInk, lineWidth: 1))
            .cornerRadius(8)
            .contentShape(Rectangle())
        }
        .buttonStyle(EnrollmentButtonStyle())
        .disabled(!enabled)
        .opacity(enabled ? 1 : 0.65)
        .accessibilityLabel(Text(text))
        .accessibilityIdentifier(id)
        .accessibilityAddTraits(selected ? .isSelected : [])
    }
    private func action(_ text: String, id: String, enabled: Bool, primary: Bool,
                        perform: @escaping () -> Void) -> some View {
        Button(action: perform) {
            Text(text)
                .font(.system(size: bodySize, weight: .semibold))
                .fixedSize(horizontal: false, vertical: true)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(12)
                .frame(minHeight: 44)
                .foregroundColor(primary ? (dark ? color(0x172B3A) : .white) : ink)
                .background(primary ? accent : selectedFill)
                .cornerRadius(8)
                .contentShape(Rectangle())
        }
        .buttonStyle(EnrollmentButtonStyle())
        .disabled(!enabled)
        .opacity(enabled ? 1 : 0.65)
        .accessibilityIdentifier(id)
    }
    private func color(_ value: UInt32) -> Color {
        Color(red: Double((value >> 16) & 255) / 255,
              green: Double((value >> 8) & 255) / 255, blue: Double(value & 255) / 255)
    }
}

/// Keep the explicit disabled affordance on the card's label instead of also
/// inheriting PlainButtonStyle's dimming. Native Button enablement is unchanged.
private struct EnrollmentButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label.opacity(configuration.isPressed ? 0.85 : 1)
    }
}
