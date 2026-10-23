import SwiftUI

/// Title + Done row used at the top of every sheet (works the same on iOS and macOS).
struct SheetHeader: View {
    let title: String
    var done = "Done"
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        HStack {
            Text(title).font(.title2.bold())
            Spacer()
            Button(done) { dismiss() }
        }
        .padding([.horizontal, .top], 16)
        .padding(.bottom, 8)
    }
}
