import SwiftUI

/// Movie-style transport for chapters:  |<  <<  [4 ====|---- 40]  >>  >|
/// plus split / lock-sync / search / bookmarks / random / settings / about.
struct TransportBar: View {
    let state: AppState
    let chapter: Int
    let chapterCount: Int

    var body: some View {
        VStack(spacing: 4) {
            HStack(spacing: 6) {
                icon("backward.end.fill", "First chapter") { state.firstChapter() }
                icon("backward.fill", "Previous chapter") { state.prevChapter() }
                Text("\(chapter)").font(.callout.bold()).frame(minWidth: 28)
                Slider(
                    value: Binding(
                        get: { Double(chapter) },
                        set: { state.seekChapter(Int($0.rounded())) }),
                    in: 1...Double(max(chapterCount, 2)),
                    step: 1)
                    .disabled(chapterCount <= 1)
                Text("\(chapterCount)").font(.callout).frame(minWidth: 28)
                icon("forward.fill", "Next chapter") { state.nextChapter() }
                icon("forward.end.fill", "Last chapter") { state.lastChapter() }
            }
            HStack(spacing: 22) {
                icon("rectangle.split.1x2", "Split screen", on: state.split) { state.toggleSplit() }
                if state.split {
                    icon(state.syncLocked ? "lock.fill" : "lock.open.fill", "Lock sync", on: state.syncLocked) {
                        state.toggleSyncLock()
                    }
                }
                icon("magnifyingglass", "Search") { state.sheet = .search }
                icon("bookmark.fill", "Bookmarks") { state.sheet = .bookmarks }
                icon("shuffle", "Random verse") { state.sheet = .randomizer }
                icon("gearshape.fill", "Settings") { state.sheet = .settings }
                icon("info.circle.fill", "About") { state.sheet = .about }
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
    }

    private func icon(_ name: String, _ label: String, on: Bool = false, _ action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Image(systemName: name)
                .font(.title3)
                .frame(minWidth: 32, minHeight: 32)
                .foregroundStyle(on ? Theme.primary : Color.secondary)
        }
        .buttonStyle(.borderless)
        .accessibilityLabel(label)
        .help(label)
    }
}
