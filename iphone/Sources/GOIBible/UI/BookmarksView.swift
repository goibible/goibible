import SwiftUI

struct BookmarksView: View {
    let state: AppState
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        let pane = state.activePaneState
        let _ = state.bookmarkVersion
        let bookmarks = state.repo.bookmarksNear(pane.editionId, pane.conical, pane.chapter)
        VStack(alignment: .leading, spacing: 0) {
            SheetHeader(title: "Bookmarks")
            if bookmarks.isEmpty {
                Text("No bookmarks yet.").foregroundStyle(.secondary).padding(16)
                Spacer()
            } else {
                List(bookmarks) { b in
                    HStack {
                        Button {
                            state.goTo(editionId: b.editionId, b.conical, b.chapter, b.verse)
                            dismiss()
                        } label: {
                            VStack(alignment: .leading, spacing: 2) {
                                Text("\(b.bookName) \(b.chapter):\(b.verse)").bold()
                                Text(b.editionName).font(.caption).foregroundStyle(.secondary)
                                Text(b.text).lineLimit(2)
                            }
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .contentShape(Rectangle())
                        }
                        .buttonStyle(.plain)
                        Button { state.removeBookmark(id: b.id) } label: { Image(systemName: "trash") }
                            .buttonStyle(.borderless)
                            .accessibilityLabel("Remove bookmark")
                    }
                }
                .listStyle(.plain)
            }
        }
    }
}
