import SwiftUI

/// Full-text verse search over the active pane's edition. Tapping a result jumps the reader to that verse.
struct SearchView: View {
    let state: AppState
    @State private var query = ""
    @State private var hits: [SearchHit] = []
    @FocusState private var focused: Bool
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        let editionId = state.activePaneState.editionId
        let editionName = state.editions.first { $0.id == editionId }?.displayName ?? editionId
        VStack(alignment: .leading, spacing: 8) {
            SheetHeader(title: "Search \(editionName)", done: "Close")
            TextField("Search verses", text: $query)
                .textFieldStyle(.roundedBorder)
                .autocorrectionDisabled()
                .focused($focused)
                .padding(.horizontal, 16)
            if query.count >= 2 {
                Text(hits.count >= 100 ? "First 100 matches" : "\(hits.count) matches")
                    .font(.caption).foregroundStyle(.secondary)
                    .padding(.horizontal, 16)
            }
            List(hits) { h in
                Button {
                    state.goToVerse(h.conical, h.chapter, h.verse)
                    dismiss()
                } label: {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("\(h.bookName) \(h.chapter):\(h.verse)").font(.subheadline.bold()).foregroundStyle(Theme.primary)
                        Text(h.text).lineLimit(3).foregroundStyle(.primary)
                    }
                }
                .buttonStyle(.plain)
            }
            .listStyle(.plain)
        }
        .onAppear { focused = true }
        .task(id: query) {
            try? await Task.sleep(for: .milliseconds(250)) // debounce while typing
            if Task.isCancelled { return }
            let q = query, repo = state.repo
            hits = q.count < 2 ? [] : await Task.detached { repo.search(editionId, q) }.value
        }
    }
}
