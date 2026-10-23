import SwiftUI

/// One reader window: "lang | Book | Ch N" header + verse list.
/// Any touch inside makes it the active pane (highlighted border when split).
struct ReaderPane: View {
    let state: AppState
    @Bindable var pane: PaneState
    let index: Int

    var body: some View {
        let repo = state.repo
        let books = repo.books(pane.editionId)
        let book = books.first { $0.conical == pane.conical }
        let chapterCount = repo.chapterCount(pane.editionId, pane.conical)
        let verses = repo.verses(pane.editionId, pane.conical, pane.chapter)
        let _ = state.bookmarkVersion  // re-query bookmark marks when they change
        let marked = repo.bookmarkedVerses(pane.editionId, pane.conical, pane.chapter)
        let isActive = state.activePane == index
        let highlight = state.split && isActive
        // Unique per edition: multiple English packages must not all read "EN".
        let edition = state.editions.first { $0.id == pane.editionId }
        let langLabel = edition.map { "\($0.language.uppercased()) · \($0.id)" } ?? "?"
        let chapterKey = "\(pane.editionId)|\(pane.conical)|\(pane.chapter)"

        VStack(spacing: 4) {
            HStack {
                Menu {
                    ForEach(state.editions) { e in
                        Button { state.activePane = index; state.setEdition(e.id) } label: {
                            Text("\(e.language.uppercased()) - \(e.id)")
                            Text(e.displayName)
                        }
                    }
                } label: { Chip(label: langLabel) }
                Spacer(minLength: 4)
                ArrowStepper(onPrev: { activate(); state.stepBook(-1) }, onNext: { activate(); state.stepBook(1) }) {
                    Menu {
                        ForEach(books) { b in
                            Button(b.longName) { activate(); state.setBook(b.conical) }
                        }
                    } label: { Chip(label: book?.longName ?? "—") }
                }
                Spacer(minLength: 4)
                ArrowStepper(onPrev: { activate(); state.prevChapter() }, onNext: { activate(); state.nextChapter() }) {
                    Menu {
                        ForEach(Array(1...max(chapterCount, 1)), id: \.self) { ch in
                            Button("Chapter \(ch)") { activate(); state.seekChapter(ch) }
                        }
                    } label: { Chip(label: "Ch \(pane.chapter)") }
                }
            }
            .menuStyle(.borderlessButton)
            .menuIndicator(.hidden)
            .fixedSize(horizontal: false, vertical: true)

            Group {
                if verses.isEmpty {
                    Text("Not available in this edition")
                        .foregroundStyle(.secondary)
                        .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    ScrollView {
                        LazyVStack(alignment: .leading, spacing: 12) {
                            ForEach(verses) { v in
                                VerseRow(state: state, pane: pane, verse: v, bookmarked: marked.contains(v.num))
                                    .id(v.num)
                            }
                        }
                        .scrollTargetLayout()
                        .padding(.horizontal, 16)
                        .padding(.vertical, 8)
                    }
                    .scrollPosition(id: $pane.topVerse, anchor: .top)
                }
            }
            .background(.background, in: RoundedRectangle(cornerRadius: 16))
            .overlay(
                RoundedRectangle(cornerRadius: 16)
                    .strokeBorder(highlight ? Theme.primary : Color.secondary.opacity(0.3), lineWidth: highlight ? 2 : 1)
            )
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 4)
        .contentShape(Rectangle())
        // Activate on any touch, without stealing the gesture from children.
        .simultaneousGesture(TapGesture().onEnded { activate() })
        // Plain navigation starts the chapter at the top; a jump (pendingVerse) scrolls to its verse.
        .onChange(of: chapterKey, initial: true) { _, _ in
            if let target = pane.pendingVerse {
                pane.topVerse = target
                pane.pendingVerse = nil
            } else if !(state.split && state.syncLocked && !isActive) {
                pane.topVerse = verses.first?.num
            }
        }
        .onChange(of: pane.pendingVerse) { _, target in
            guard let target else { return }
            pane.topVerse = target
            pane.pendingVerse = nil
        }
    }

    private func activate() {
        if state.activePane != index { state.activePane = index }
    }
}

private struct VerseRow: View {
    let state: AppState
    let pane: PaneState
    let verse: Verse
    let bookmarked: Bool

    var body: some View {
        HStack(alignment: .firstTextBaseline, spacing: 8) {
            Menu {
                Button(bookmarked ? "Remove bookmark" : "Add bookmark") {
                    state.toggleBookmark(pane.editionId, pane.conical, pane.chapter, verse.num)
                }
            } label: {
                Text("\(verse.num)")
                    .font(.system(size: CGFloat(state.fontSize) * 0.75, weight: .bold))
                    .foregroundStyle(bookmarked ? Theme.tertiary : Theme.primary)
            }
            .menuStyle(.borderlessButton)
            .menuIndicator(.hidden)
            .fixedSize()
            Text(verse.text)
                .font(readerFont(state.fontKey, size: CGFloat(state.fontSize)))
                .lineSpacing(CGFloat(state.fontSize) * 0.6)
                .textSelection(.enabled)
                .frame(maxWidth: .infinity, alignment: .leading)
        }
    }
}

/// `‹ content ›` control: side arrows step prev/next, the content (a Menu) opens a picker.
private struct ArrowStepper<Content: View>: View {
    let onPrev: () -> Void
    let onNext: () -> Void
    @ViewBuilder let content: Content

    var body: some View {
        HStack(spacing: 2) {
            Button(action: onPrev) { Image(systemName: "chevron.left") }
                .buttonStyle(.borderless).foregroundStyle(.secondary)
            content
            Button(action: onNext) { Image(systemName: "chevron.right") }
                .buttonStyle(.borderless).foregroundStyle(.secondary)
        }
    }
}

private struct Chip: View {
    let label: String

    var body: some View {
        Text(label)
            .font(.subheadline.weight(.semibold))
            .lineLimit(1)
            .padding(.horizontal, 10)
            .padding(.vertical, 6)
            .overlay(RoundedRectangle(cornerRadius: 8).strokeBorder(Color.secondary.opacity(0.3)))
            .foregroundStyle(.primary)
    }
}
