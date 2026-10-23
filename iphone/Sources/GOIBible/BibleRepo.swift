import Foundation
import SQLite3

struct Edition: Identifiable, Hashable { let id: String; let displayName: String; let language: String }
struct Book: Identifiable, Hashable { let conical: Int; let osis: String; let longName: String; let testament: String; var id: Int { conical } }
struct Verse: Identifiable, Hashable { let num: Int; let text: String; var id: Int { num } }
struct Bookmark: Identifiable, Hashable {
    let id: Int64
    let editionId: String
    let editionName: String
    let conical: Int
    let bookName: String
    let chapter: Int
    let verse: Int
    let text: String
    let createdAt: Int64
}
struct SearchHit: Identifiable, Hashable {
    let conical: Int
    let bookName: String
    let chapter: Int
    let verse: Int
    let text: String
    var id: String { "\(conical):\(chapter):\(verse)" }
}
struct RandomVerse: Hashable {
    let editionId: String
    let editionName: String
    let conical: Int
    let bookName: String
    let chapter: Int
    let verse: Int
    let text: String
}

struct DBError: LocalizedError { let message: String; var errorDescription: String? { message } }

/// Bundled files live in a "Resources" folder: Bundle.module under SwiftPM/xtool, Bundle.main under Xcode.
func resourceURL(_ name: String) -> URL? {
    #if SWIFT_PACKAGE
    let bundle = Bundle.module
    #else
    let bundle = Bundle.main
    #endif
    return bundle.url(forResource: name, withExtension: nil, subdirectory: "Resources")
}

/// Thin wrapper over the system sqlite3 C API. Serialized mode, so background merges are safe.
final class DB: @unchecked Sendable {
    private var handle: OpaquePointer?
    private static let transient = unsafeBitCast(-1, to: sqlite3_destructor_type.self)

    init(path: String) throws {
        let flags = SQLITE_OPEN_READWRITE | SQLITE_OPEN_CREATE | SQLITE_OPEN_FULLMUTEX
        guard sqlite3_open_v2(path, &handle, flags, nil) == SQLITE_OK else {
            throw DBError(message: "Cannot open \(path)")
        }
    }

    deinit { sqlite3_close(handle) }

    private func prepare(_ sql: String, _ args: [Any]) throws -> OpaquePointer? {
        var stmt: OpaquePointer?
        guard sqlite3_prepare_v2(handle, sql, -1, &stmt, nil) == SQLITE_OK else {
            throw DBError(message: String(cString: sqlite3_errmsg(handle)))
        }
        for (i, arg) in args.enumerated() {
            let idx = Int32(i + 1)
            switch arg {
            case let v as Int: sqlite3_bind_int64(stmt, idx, Int64(v))
            case let v as Int64: sqlite3_bind_int64(stmt, idx, v)
            case let v as String: sqlite3_bind_text(stmt, idx, v, -1, DB.transient)
            default: sqlite3_bind_null(stmt, idx)
            }
        }
        return stmt
    }

    func exec(_ sql: String, _ args: [Any] = []) throws {
        let stmt = try prepare(sql, args)
        defer { sqlite3_finalize(stmt) }
        let rc = sqlite3_step(stmt)
        guard rc == SQLITE_DONE || rc == SQLITE_ROW else {
            throw DBError(message: String(cString: sqlite3_errmsg(handle)))
        }
    }

    func query<T>(_ sql: String, _ args: [Any] = [], _ row: (Row) -> T) -> [T] {
        guard let stmt = try? prepare(sql, args) else { return [] }
        defer { sqlite3_finalize(stmt) }
        var out: [T] = []
        while sqlite3_step(stmt) == SQLITE_ROW { out.append(row(Row(stmt: stmt))) }
        return out
    }

    func transaction(_ body: () throws -> Void) throws {
        try exec("BEGIN")
        do { try body(); try exec("COMMIT") } catch { try? exec("ROLLBACK"); throw error }
    }

    struct Row {
        let stmt: OpaquePointer?
        func int(_ i: Int32) -> Int { Int(sqlite3_column_int64(stmt, i)) }
        func int64(_ i: Int32) -> Int64 { sqlite3_column_int64(stmt, i) }
        func isNull(_ i: Int32) -> Bool { sqlite3_column_type(stmt, i) == SQLITE_NULL }
        func text(_ i: Int32) -> String {
            guard let c = sqlite3_column_text(stmt, i) else { return "" }
            return String(cString: c)
        }
    }
}

/// Owns the app's working database (Application Support/bible.db).
/// Ships with GOI_En bundled; other editions are merged in via ATTACH.
final class BibleRepo: @unchecked Sendable {
    /// Editions shipped in the app; the first is the base database, the rest are merged in.
    private static let bundled = ["GOI_En.db", "GOI_Zh_Hant.db", "GOI_Zh_Hans.db", "GOI_vi.db"]
    private static let removedKey = "removed_bundled"

    private let db: DB
    private let defaults = UserDefaults.standard
    private var booksCache: [String: [Book]] = [:]
    private var chapterCache: [String: Int] = [:]
    private let cacheLock = NSLock()

    init() throws {
        let dir = try FileManager.default.url(
            for: .applicationSupportDirectory, in: .userDomainMask, appropriateFor: nil, create: true)
        let dbFile = dir.appendingPathComponent("bible.db")
        let firstRun = !FileManager.default.fileExists(atPath: dbFile.path)
        if firstRun, let base = resourceURL(Self.bundled[0]) {
            try FileManager.default.copyItem(at: base, to: dbFile)
        }
        db = try DB(path: dbFile.path)
        // Databases created before localized names existed lack this table.
        try db.exec(
            "CREATE TABLE IF NOT EXISTS book_names (" +
                "edition_id TEXT NOT NULL, conical INTEGER NOT NULL, name TEXT NOT NULL, " +
                "PRIMARY KEY (edition_id, conical))")
        try db.exec(
            "CREATE TABLE IF NOT EXISTS bookmarks (" +
                "id INTEGER PRIMARY KEY AUTOINCREMENT, " +
                "edition_id TEXT NOT NULL, conical INTEGER NOT NULL, chapter INTEGER NOT NULL, " +
                "verse INTEGER NOT NULL, created_at INTEGER NOT NULL, " +
                "UNIQUE (edition_id, conical, chapter, verse))")
        let toMerge = firstRun ? Array(Self.bundled.dropFirst()) : Self.bundled
        let installed = Set(editions().map { $0.id + ".db" })
        for asset in toMerge where !removedBundled().contains(asset) && !installed.contains(asset) {
            // Copy out of the read-only app bundle first, as Android does with assets.
            guard let url = resourceURL(asset) else { continue }
            let tmp = FileManager.default.temporaryDirectory.appendingPathComponent(asset)
            try? FileManager.default.removeItem(at: tmp)
            try FileManager.default.copyItem(at: url, to: tmp)
            _ = mergeFrom(tmp)
            try? FileManager.default.removeItem(at: tmp)
        }
    }

    private func removedBundled() -> Set<String> {
        Set(defaults.stringArray(forKey: Self.removedKey) ?? [])
    }

    private func setRemovedBundled(_ s: Set<String>) {
        defaults.set(Array(s), forKey: Self.removedKey)
    }

    private func clearCaches() {
        cacheLock.lock(); booksCache = [:]; chapterCache = [:]; cacheLock.unlock()
    }

    func editions() -> [Edition] {
        db.query(
            "SELECT edition_id, COALESCE(display_name, edition_id), language_subtag " +
                "FROM editions ORDER BY edition_id"
        ) { Edition(id: $0.text(0), displayName: $0.text(1), language: $0.text(2)) }
    }

    /// Books that actually have verses in this edition, titled in the edition's own language when available.
    func books(_ editionId: String) -> [Book] {
        cacheLock.lock(); defer { cacheLock.unlock() }
        if let hit = booksCache[editionId] { return hit }
        let out = db.query(
            "SELECT b.conical, b.osis, COALESCE(bn.name, b.long_name), b.testament FROM books b " +
                "LEFT JOIN book_names bn ON bn.conical = b.conical AND bn.edition_id = ? " +
                "WHERE EXISTS (SELECT 1 FROM verses v WHERE v.edition_id = ? AND v.conical = b.conical) " +
                "ORDER BY b.conical", [editionId, editionId]
        ) { Book(conical: $0.int(0), osis: $0.text(1), longName: $0.text(2), testament: $0.text(3)) }
        booksCache[editionId] = out
        return out
    }

    func chapterCount(_ editionId: String, _ conical: Int) -> Int {
        let key = "\(editionId)|\(conical)"
        cacheLock.lock(); defer { cacheLock.unlock() }
        if let hit = chapterCache[key] { return hit }
        let n = db.query(
            "SELECT MAX(chapter) FROM verses WHERE edition_id = ? AND conical = ?", [editionId, conical]
        ) { $0.isNull(0) ? 0 : $0.int(0) }.first ?? 0
        chapterCache[key] = n
        return n
    }

    func verses(_ editionId: String, _ conical: Int, _ chapter: Int) -> [Verse] {
        db.query(
            "SELECT verse, verse_text FROM verses " +
                "WHERE edition_id = ? AND conical = ? AND chapter = ? ORDER BY verse",
            [editionId, conical, chapter]
        ) { Verse(num: $0.int(0), text: $0.text(1)) }
    }

    func search(_ editionId: String, _ query: String, limit: Int = 100) -> [SearchHit] {
        if query.trimmingCharacters(in: .whitespaces).isEmpty { return [] }
        let escaped = query.replacingOccurrences(of: "\\", with: "\\\\")
            .replacingOccurrences(of: "%", with: "\\%")
            .replacingOccurrences(of: "_", with: "\\_")
        return db.query(
            "SELECT v.conical, COALESCE(bn.name, b.long_name), v.chapter, v.verse, v.verse_text " +
                "FROM verses v JOIN books b ON b.conical = v.conical " +
                "LEFT JOIN book_names bn ON bn.conical = v.conical AND bn.edition_id = v.edition_id " +
                "WHERE v.edition_id = ? AND v.verse_text LIKE ? ESCAPE '\\' " +
                "ORDER BY v.conical, v.chapter, v.verse LIMIT \(limit)",
            [editionId, "%" + escaped + "%"]
        ) { SearchHit(conical: $0.int(0), bookName: $0.text(1), chapter: $0.int(2), verse: $0.int(3), text: $0.text(4)) }
    }

    func randomVerse(_ editionId: String) -> RandomVerse? {
        db.query(
            "SELECT v.edition_id, COALESCE(e.display_name, v.edition_id), v.conical, " +
                "COALESCE(bn.name, b.long_name), v.chapter, v.verse, v.verse_text " +
                "FROM verses v " +
                "JOIN editions e ON e.edition_id = v.edition_id " +
                "JOIN books b ON b.conical = v.conical " +
                "LEFT JOIN book_names bn ON bn.conical = v.conical AND bn.edition_id = v.edition_id " +
                "WHERE v.edition_id = ? ORDER BY RANDOM() LIMIT 1", [editionId]
        ) {
            RandomVerse(editionId: $0.text(0), editionName: $0.text(1), conical: $0.int(2),
                        bookName: $0.text(3), chapter: $0.int(4), verse: $0.int(5), text: $0.text(6))
        }.first
    }

    func bookmarkedVerses(_ editionId: String, _ conical: Int, _ chapter: Int) -> Set<Int> {
        Set(db.query(
            "SELECT verse FROM bookmarks WHERE edition_id = ? AND conical = ? AND chapter = ?",
            [editionId, conical, chapter]
        ) { $0.int(0) })
    }

    func isBookmarked(_ editionId: String, _ conical: Int, _ chapter: Int, _ verse: Int) -> Bool {
        !db.query(
            "SELECT 1 FROM bookmarks WHERE edition_id = ? AND conical = ? AND chapter = ? AND verse = ?",
            [editionId, conical, chapter, verse]
        ) { _ in true }.isEmpty
    }

    func addBookmark(_ editionId: String, _ conical: Int, _ chapter: Int, _ verse: Int) {
        try? db.exec(
            "INSERT OR IGNORE INTO bookmarks (edition_id, conical, chapter, verse, created_at) " +
                "VALUES (?, ?, ?, ?, ?)",
            [editionId, conical, chapter, verse, Int64(Date().timeIntervalSince1970 * 1000)])
    }

    func removeBookmark(_ editionId: String, _ conical: Int, _ chapter: Int, _ verse: Int) {
        try? db.exec(
            "DELETE FROM bookmarks WHERE edition_id = ? AND conical = ? AND chapter = ? AND verse = ?",
            [editionId, conical, chapter, verse])
    }

    func removeBookmark(id: Int64) {
        try? db.exec("DELETE FROM bookmarks WHERE id = ?", [id])
    }

    func bookmarksNear(_ editionId: String, _ conical: Int, _ chapter: Int) -> [Bookmark] {
        let all = db.query(
            "SELECT bm.id, bm.edition_id, COALESCE(e.display_name, bm.edition_id), bm.conical, " +
                "COALESCE(bn.name, b.long_name), bm.chapter, bm.verse, COALESCE(v.verse_text, ''), bm.created_at " +
                "FROM bookmarks bm " +
                "JOIN editions e ON e.edition_id = bm.edition_id " +
                "JOIN books b ON b.conical = bm.conical " +
                "LEFT JOIN book_names bn ON bn.edition_id = bm.edition_id AND bn.conical = bm.conical " +
                "LEFT JOIN verses v ON v.edition_id = bm.edition_id AND v.conical = bm.conical " +
                "AND v.chapter = bm.chapter AND v.verse = bm.verse"
        ) {
            Bookmark(id: $0.int64(0), editionId: $0.text(1), editionName: $0.text(2), conical: $0.int(3),
                     bookName: $0.text(4), chapter: $0.int(5), verse: $0.int(6), text: $0.text(7),
                     createdAt: $0.int64(8))
        }
        // Same ordering as Android: this edition, this book, this chapter, then by distance, newest first.
        func key(_ b: Bookmark) -> [Int64] {
            [b.editionId == editionId ? 0 : 1, b.conical == conical ? 0 : 1, b.chapter == chapter ? 0 : 1,
             Int64(abs(b.conical - conical)), Int64(abs(b.chapter - chapter)), Int64(abs(b.verse - 1)),
             -b.createdAt]
        }
        return all.sorted { key($0).lexicographicallyPrecedes(key($1)) }
    }

    /// Merge a single-edition .db (same schema) into the working database. Returns the edition names.
    func mergeFrom(_ file: URL) -> Result<String, Error> {
        do {
            try db.exec("ATTACH DATABASE ? AS src", [file.path])
            defer { try? db.exec("DETACH DATABASE src") }
            let tables = db.query(
                "SELECT count(*) FROM src.sqlite_master WHERE type='table' AND name IN ('editions','verses')"
            ) { $0.int(0) }.first ?? 0
            guard tables == 2 else { throw DBError(message: "Not an edition db (missing editions/verses tables)") }
            let names = db.query("SELECT COALESCE(display_name, edition_id) FROM src.editions") { $0.text(0) }
            let hasBookNames = (db.query(
                "SELECT count(*) FROM src.sqlite_master WHERE type='table' AND name='book_names'"
            ) { $0.int(0) }.first ?? 0) == 1
            try db.transaction {
                try db.exec("INSERT OR IGNORE INTO books SELECT * FROM src.books")
                try db.exec("INSERT OR REPLACE INTO editions SELECT * FROM src.editions")
                if hasBookNames { try db.exec("INSERT OR REPLACE INTO book_names SELECT * FROM src.book_names") }
                try db.exec("INSERT OR REPLACE INTO verses SELECT * FROM src.verses")
            }
            let installedAssets = Set(db.query("SELECT edition_id FROM src.editions") { $0.text(0) + ".db" })
            setRemovedBundled(removedBundled().subtracting(installedAssets))
            clearCaches()
            return .success(names.joined(separator: ", "))
        } catch {
            return .failure(error)
        }
    }

    func removeEdition(_ id: String) throws {
        guard editions().count > 1 else { throw DBError(message: "Keep at least one Bible translation installed") }
        try db.transaction {
            try db.exec("DELETE FROM bookmarks WHERE edition_id = ?", [id])
            try db.exec("DELETE FROM verses WHERE edition_id = ?", [id])
            try db.exec("DELETE FROM book_names WHERE edition_id = ?", [id])
            try db.exec("DELETE FROM editions WHERE edition_id = ?", [id])
        }
        setRemovedBundled(removedBundled().union([id + ".db"]))
        clearCaches()
    }
}
