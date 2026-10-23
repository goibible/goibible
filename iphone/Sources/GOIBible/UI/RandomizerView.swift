import SwiftUI

struct RandomizerView: View {
    let state: AppState
    @State private var selectedEdition = ""
    @State private var verse: RandomVerse?
    @State private var loading = false
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            SheetHeader(title: "Random Verse", done: "Close")
            Picker("Edition", selection: $selectedEdition) {
                ForEach(state.editions) { Text($0.displayName).tag($0.id) }
            }
            .pickerStyle(.menu)
            .padding(.horizontal, 16)

            Group {
                if let verse {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("\(verse.bookName) \(verse.chapter):\(verse.verse)").font(.headline).foregroundStyle(Theme.primary)
                        Text(verse.editionName).font(.caption).foregroundStyle(.secondary)
                        Text(verse.text).font(readerFont(state.fontKey, size: CGFloat(state.fontSize)))
                            .textSelection(.enabled)
                    }
                } else {
                    Text(loading ? "Loading…" : "No verse available.").foregroundStyle(.secondary)
                }
            }
            .padding(.horizontal, 16)

            HStack {
                Spacer()
                Button("Go") {
                    if let verse {
                        state.goTo(editionId: verse.editionId, verse.conical, verse.chapter, verse.verse)
                        dismiss()
                    }
                }
                .disabled(verse == nil)
                Button("New Verse") { Task { await pick() } }
                    .buttonStyle(.borderedProminent)
                    .disabled(selectedEdition.isEmpty || loading)
            }
            .padding(16)
            Spacer()
        }
        .onAppear {
            let active = state.activePaneState.editionId
            selectedEdition = state.editions.contains { $0.id == active } ? active : (state.editions.first?.id ?? "")
        }
        .task(id: selectedEdition) { await pick() }
        .presentationDetents([.medium, .large])
    }

    private func pick() async {
        guard !selectedEdition.isEmpty else { return }
        loading = true
        let id = selectedEdition, repo = state.repo
        verse = await Task.detached { repo.randomVerse(id) }.value
        loading = false
    }
}
