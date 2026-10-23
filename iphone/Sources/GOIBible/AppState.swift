import Foundation
import Observation

@Observable
final class PaneState {
    var editionId: String
    var conical: Int
    var chapter: Int
    /// Verse to scroll to once the chapter is shown (set by search/bookmarks), then cleared.
    var pendingVerse: Int?
    /// Top visible verse; drives lock-sync scrolling between panes.
    var topVerse: Int?

    init(editionId: String, conical: Int, chapter: Int) {
        self.editionId = editionId
        self.conical = conical
        self.chapter = chapter
    }
}

enum Sheet: String, Identifiable {
    case settings, about, search, bookmarks, randomizer
    var id: String { rawValue }
}

/// All UI state + the "movie transport" navigation logic.
/// When split & syncLocked, chapter navigation drives both panes; edition (language) stays per-pane.
@Observable
final class AppState {
    let repo: BibleRepo
    @ObservationIgnored private let prefs = UserDefaults.standard

    private(set) var split: Bool
    private(set) var syncLocked: Bool
    var activePane = 0
    var sheet: Sheet?
    private(set) var bookmarkVersion = 0
    private(set) var darkMode: Bool
    private(set) var fontKey: String
    private(set) var fontSize: Int
    private(set) var editions: [Edition]
    let panes: [PaneState]

    init(repo: BibleRepo) {
        self.repo = repo
        let prefs = UserDefaults.standard  // local: self isn't fully initialized yet
        prefs.register(defaults: ["darkMode": true, "fontKey": "literata", "fontSize": 12])
        split = prefs.bool(forKey: "split")
        syncLocked = prefs.bool(forKey: "syncLocked")
        darkMode = prefs.bool(forKey: "darkMode")
        fontKey = prefs.string(forKey: "fontKey") ?? "literata"
        fontSize = prefs.integer(forKey: "fontSize")
        let editions = repo.editions()
        self.editions = editions
        let defaultEdition = editions.first { $0.id == "GOI_En" }?.id ?? editions.first?.id ?? ""
        panes = (0..<2).map { i in
            PaneState(
                editionId: prefs.string(forKey: "p\(i)_edition") ?? defaultEdition,
                conical: max(1, prefs.integer(forKey: "p\(i)_conical")),
                chapter: max(1, prefs.integer(forKey: "p\(i)_chapter")))
        }
        if editions.isEmpty == false { refreshEditions() }
    }

    var activePaneState: PaneState { panes[activePane] }

    func updateDarkMode(_ enabled: Bool) { darkMode = enabled; save() }
    func updateFont(_ key: String) { fontKey = key; save() }
    func updateFontSize(_ size: Int) { fontSize = min(max(size, 10), 28); save() }

    private func save() {
        prefs.set(split, forKey: "split")
        prefs.set(syncLocked, forKey: "syncLocked")
        prefs.set(darkMode, forKey: "darkMode")
        prefs.set(fontKey, forKey: "fontKey")
        prefs.set(fontSize, forKey: "fontSize")
        for (i, p) in panes.enumerated() {
            prefs.set(p.editionId, forKey: "p\(i)_edition")
            prefs.set(p.conical, forKey: "p\(i)_conical")
            prefs.set(p.chapter, forKey: "p\(i)_chapter")
        }
    }

    private func clampChapter(_ p: PaneState) {
        p.chapter = min(max(p.chapter, 1), max(repo.chapterCount(p.editionId, p.conical), 1))
    }

    func refreshEditions() {
        editions = repo.editions()
        // If a removed edition was showing, fall back to the first remaining one.
        for p in panes where !editions.contains(where: { $0.id == p.editionId }) {
            guard let first = editions.first else { break }
            p.editionId = first.id
            let books = repo.books(p.editionId)
            if !books.contains(where: { $0.conical == p.conical }) {
                p.conical = books.first?.conical ?? 1
                p.chapter = 1
            }
            clampChapter(p)
            p.pendingVerse = nil
        }
        save()
    }

    func toggleSplit() {
        split.toggle()
        if !split { activePane = 0 }
        save()
    }

    func toggleSyncLock() {
        syncLocked.toggle()
        if syncLocked {
            // Snap the other pane to the active pane's position on lock.
            let src = panes[activePane], dst = panes[1 - activePane]
            dst.conical = src.conical
            dst.chapter = src.chapter
            dst.topVerse = src.topVerse
        }
        save()
    }

    private var targets: [PaneState] { split && syncLocked ? panes : [panes[activePane]] }

    func setEdition(_ editionId: String) {
        let p = panes[activePane]
        p.editionId = editionId
        // Clamp position to what exists in this edition.
        let books = repo.books(editionId)
        if !books.contains(where: { $0.conical == p.conical }) {
            p.conical = books.first?.conical ?? 1
            p.chapter = 1
        } else {
            clampChapter(p)
        }
        save()
    }

    /// Step to the previous/next book available in each target pane's edition.
    func stepBook(_ delta: Int) {
        for p in targets {
            let books = repo.books(p.editionId)
            guard let idx = books.firstIndex(where: { $0.conical == p.conical }),
                  books.indices.contains(idx + delta) else { continue }
            p.conical = books[idx + delta].conical
            p.chapter = 1
        }
        save()
    }

    func setBook(_ conical: Int) {
        for p in targets { p.conical = conical; p.chapter = 1 }
        save()
    }

    /// Jump straight to a verse (from search); respects lock sync like other navigation.
    func goToVerse(_ conical: Int, _ chapter: Int, _ verse: Int) {
        for p in targets { p.conical = conical; p.chapter = chapter; p.pendingVerse = verse }
        save()
    }

    /// Bookmarks and the randomizer also switch the active pane's edition.
    func goTo(editionId: String, _ conical: Int, _ chapter: Int, _ verse: Int) {
        let p = panes[activePane]
        p.editionId = editionId
        p.conical = conical
        p.chapter = chapter
        p.pendingVerse = verse
        save()
    }

    func toggleBookmark(_ editionId: String, _ conical: Int, _ chapter: Int, _ verse: Int) {
        if repo.isBookmarked(editionId, conical, chapter, verse) {
            repo.removeBookmark(editionId, conical, chapter, verse)
        } else {
            repo.addBookmark(editionId, conical, chapter, verse)
        }
        bookmarkVersion += 1
    }

    func removeBookmark(id: Int64) {
        repo.removeBookmark(id: id)
        bookmarkVersion += 1
    }

    func seekChapter(_ chapter: Int) {
        for p in targets { p.chapter = chapter; clampChapter(p) }
        save()
    }

    func firstChapter() { seekChapter(1) }

    func lastChapter() {
        for p in targets { p.chapter = max(repo.chapterCount(p.editionId, p.conical), 1) }
        save()
    }

    /// Next chapter; past the last chapter, roll into the next book available in the pane's edition.
    func nextChapter() {
        for p in targets {
            if p.chapter < repo.chapterCount(p.editionId, p.conical) {
                p.chapter += 1
            } else {
                let books = repo.books(p.editionId)
                if let idx = books.firstIndex(where: { $0.conical == p.conical }), idx < books.count - 1 {
                    p.conical = books[idx + 1].conical
                    p.chapter = 1
                }
            }
        }
        save()
    }

    /// Previous chapter; before chapter 1, roll into the last chapter of the previous book.
    func prevChapter() {
        for p in targets {
            if p.chapter > 1 {
                p.chapter -= 1
            } else {
                let books = repo.books(p.editionId)
                if let idx = books.firstIndex(where: { $0.conical == p.conical }), idx > 0 {
                    p.conical = books[idx - 1].conical
                    p.chapter = max(repo.chapterCount(p.editionId, p.conical), 1)
                }
            }
        }
        save()
    }
}
