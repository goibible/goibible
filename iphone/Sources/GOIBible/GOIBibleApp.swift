import SwiftUI

@main
struct GOIBibleApp: App {
    @State private var state: AppState? = {
        registerFonts()
        return (try? BibleRepo()).map { AppState(repo: $0) }
    }()

    var body: some Scene {
        WindowGroup {
            if let state {
                RootView(state: state)
            } else {
                Text("Could not open the Bible database.").padding()
            }
        }
        #if os(macOS)
        .defaultSize(width: 900, height: 1000)
        #endif
    }
}

struct RootView: View {
    @Bindable var state: AppState

    var body: some View {
        ReaderScreen(state: state)
            .tint(Theme.primary)
            .preferredColorScheme(state.darkMode ? .dark : .light)
            .sheet(item: $state.sheet) { sheet in
                Group {
                    switch sheet {
                    case .settings: SettingsView(state: state)
                    case .about: AboutView()
                    case .search: SearchView(state: state)
                    case .bookmarks: BookmarksView(state: state)
                    case .randomizer: RandomizerView(state: state)
                    }
                }
                .tint(Theme.primary)
                .preferredColorScheme(state.darkMode ? .dark : .light)
                #if os(macOS)
                .frame(minWidth: 520, minHeight: 560)
                #endif
            }
    }
}

struct ReaderScreen: View {
    @Bindable var state: AppState

    var body: some View {
        let active = state.activePaneState
        let chapterCount = max(state.repo.chapterCount(active.editionId, active.conical), 1)
        VStack(spacing: 0) {
            ForEach(0..<(state.split ? 2 : 1), id: \.self) { i in
                ReaderPane(state: state, pane: state.panes[i], index: i)
            }
            TransportBar(state: state, chapter: active.chapter, chapterCount: chapterCount)
        }
        // Lock sync: mirror the focused pane's top verse onto the other pane.
        .onChange(of: active.topVerse) { _, top in
            guard state.split, state.syncLocked, let top else { return }
            let other = state.panes[1 - state.activePane]
            if other.topVerse != top { other.topVerse = top }
        }
    }
}
