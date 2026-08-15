package com.example.goibible.data

import android.content.Context
import android.database.sqlite.SQLiteDatabase
import java.io.File

data class Edition(val id: String, val displayName: String, val language: String)
data class Book(val conical: Int, val osis: String, val longName: String, val testament: String)
data class Verse(val num: Int, val text: String)
data class Bookmark(
    val id: Long,
    val editionId: String,
    val editionName: String,
    val conical: Int,
    val bookName: String,
    val chapter: Int,
    val verse: Int,
    val text: String,
    val createdAt: Long,
)
data class SearchHit(
    val conical: Int,
    val bookName: String,
    val chapter: Int,
    val verse: Int,
    val text: String,
)
data class RandomVerse(
    val editionId: String,
    val editionName: String,
    val conical: Int,
    val bookName: String,
    val chapter: Int,
    val verse: Int,
    val text: String,
)

/**
 * Owns the app's working database (filesDir/bible.db).
 * Ships with GOI_En bundled; other editions are merged in via ATTACH.
 */
class BibleRepo(private val context: Context) {

    private val dbFile = File(context.filesDir, "bible.db")
    private val db: SQLiteDatabase

    init {
        val firstRun = !dbFile.exists()
        if (firstRun) {
            context.assets.open(BUNDLED.first()).use { input ->
                dbFile.outputStream().use { input.copyTo(it) }
            }
        }
        db = SQLiteDatabase.openDatabase(dbFile.path, null, SQLiteDatabase.OPEN_READWRITE)
        // Databases created before localized names existed lack this table.
        db.execSQL(
            "CREATE TABLE IF NOT EXISTS book_names (" +
                "edition_id TEXT NOT NULL, conical INTEGER NOT NULL, name TEXT NOT NULL, " +
                "PRIMARY KEY (edition_id, conical))"
        )
        db.execSQL(
            "CREATE TABLE IF NOT EXISTS bookmarks (" +
                "id INTEGER PRIMARY KEY AUTOINCREMENT, " +
                "edition_id TEXT NOT NULL, " +
                "conical INTEGER NOT NULL, " +
                "chapter INTEGER NOT NULL, " +
                "verse INTEGER NOT NULL, " +
                "created_at INTEGER NOT NULL, " +
                "UNIQUE (edition_id, conical, chapter, verse))"
        )
        val assetsToMerge = if (firstRun) BUNDLED.drop(1) else BUNDLED
        assetsToMerge.forEach { asset ->
            mergeBundled(asset)
        }
    }

    companion object {
        /** Editions shipped in the APK; the first is the base database, the rest are merged in. */
        private val BUNDLED = listOf("GOI_En.db", "GOI_Zh_Hant.db", "GOI_Zh_Hans.db", "GOI_vi.db")
    }

    private fun mergeBundled(asset: String) {
        val tmp = File(context.cacheDir, asset)
        context.assets.open(asset).use { input ->
            tmp.outputStream().use { input.copyTo(it) }
        }
        mergeFrom(tmp)
        tmp.delete()
    }

    fun editions(): List<Edition> {
        val out = mutableListOf<Edition>()
        db.rawQuery(
            "SELECT edition_id, COALESCE(display_name, edition_id), language_subtag " +
                "FROM editions ORDER BY edition_id", null
        ).use { c ->
            while (c.moveToNext()) out.add(Edition(c.getString(0), c.getString(1), c.getString(2)))
        }
        return out
    }

    /**
     * Books that actually have verses in this edition (WLC is OT-only, TR1550 NT-only),
     * titled in the edition's own language when book_names has an entry (e.g. 創世記).
     */
    fun books(editionId: String): List<Book> {
        val out = mutableListOf<Book>()
        db.rawQuery(
            "SELECT b.conical, b.osis, COALESCE(bn.name, b.long_name), b.testament FROM books b " +
                "LEFT JOIN book_names bn ON bn.conical = b.conical AND bn.edition_id = ? " +
                "WHERE EXISTS (SELECT 1 FROM verses v WHERE v.edition_id = ? AND v.conical = b.conical) " +
                "ORDER BY b.conical",
            arrayOf(editionId, editionId)
        ).use { c ->
            while (c.moveToNext()) out.add(Book(c.getInt(0), c.getString(1), c.getString(2), c.getString(3)))
        }
        return out
    }

    fun chapterCount(editionId: String, conical: Int): Int {
        db.rawQuery(
            "SELECT MAX(chapter) FROM verses WHERE edition_id = ? AND conical = ?",
            arrayOf(editionId, conical.toString())
        ).use { c ->
            return if (c.moveToFirst() && !c.isNull(0)) c.getInt(0) else 0
        }
    }

    fun verses(editionId: String, conical: Int, chapter: Int): List<Verse> {
        val out = mutableListOf<Verse>()
        db.rawQuery(
            "SELECT verse, verse_text FROM verses " +
                "WHERE edition_id = ? AND conical = ? AND chapter = ? ORDER BY verse",
            arrayOf(editionId, conical.toString(), chapter.toString())
        ).use { c ->
            while (c.moveToNext()) out.add(Verse(c.getInt(0), c.getString(1) ?: ""))
        }
        return out
    }

    fun search(editionId: String, query: String, limit: Int = 100): List<SearchHit> {
        if (query.isBlank()) return emptyList()
        val out = mutableListOf<SearchHit>()
        db.rawQuery(
            "SELECT v.conical, COALESCE(bn.name, b.long_name), v.chapter, v.verse, v.verse_text " +
                "FROM verses v JOIN books b ON b.conical = v.conical " +
                "LEFT JOIN book_names bn ON bn.conical = v.conical AND bn.edition_id = v.edition_id " +
                "WHERE v.edition_id = ? AND v.verse_text LIKE ? ESCAPE '\\' " +
                "ORDER BY v.conical, v.chapter, v.verse LIMIT $limit",
            arrayOf(editionId, "%" + query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%")
        ).use { c ->
            while (c.moveToNext()) {
                out.add(SearchHit(c.getInt(0), c.getString(1), c.getInt(2), c.getInt(3), c.getString(4) ?: ""))
            }
        }
        return out
    }

    fun randomVerse(editionId: String): RandomVerse? {
        db.rawQuery(
            "SELECT v.edition_id, COALESCE(e.display_name, v.edition_id), v.conical, " +
                "COALESCE(bn.name, b.long_name), v.chapter, v.verse, v.verse_text " +
                "FROM verses v " +
                "JOIN editions e ON e.edition_id = v.edition_id " +
                "JOIN books b ON b.conical = v.conical " +
                "LEFT JOIN book_names bn ON bn.conical = v.conical AND bn.edition_id = v.edition_id " +
                "WHERE v.edition_id = ? ORDER BY RANDOM() LIMIT 1",
            arrayOf(editionId)
        ).use { c ->
            if (!c.moveToFirst()) return null
            return RandomVerse(
                editionId = c.getString(0),
                editionName = c.getString(1),
                conical = c.getInt(2),
                bookName = c.getString(3),
                chapter = c.getInt(4),
                verse = c.getInt(5),
                text = c.getString(6) ?: "",
            )
        }
    }

    fun bookmarkedVerses(editionId: String, conical: Int, chapter: Int): Set<Int> {
        val out = mutableSetOf<Int>()
        db.rawQuery(
            "SELECT verse FROM bookmarks WHERE edition_id = ? AND conical = ? AND chapter = ?",
            arrayOf(editionId, conical.toString(), chapter.toString())
        ).use { c ->
            while (c.moveToNext()) out.add(c.getInt(0))
        }
        return out
    }

    fun isBookmarked(editionId: String, conical: Int, chapter: Int, verse: Int): Boolean {
        db.rawQuery(
            "SELECT 1 FROM bookmarks WHERE edition_id = ? AND conical = ? AND chapter = ? AND verse = ?",
            arrayOf(editionId, conical.toString(), chapter.toString(), verse.toString())
        ).use { c -> return c.moveToFirst() }
    }

    fun addBookmark(editionId: String, conical: Int, chapter: Int, verse: Int) {
        db.execSQL(
            "INSERT OR IGNORE INTO bookmarks (edition_id, conical, chapter, verse, created_at) " +
                "VALUES (?, ?, ?, ?, ?)",
            arrayOf<Any>(editionId, conical, chapter, verse, System.currentTimeMillis())
        )
    }

    fun removeBookmark(editionId: String, conical: Int, chapter: Int, verse: Int) {
        db.execSQL(
            "DELETE FROM bookmarks WHERE edition_id = ? AND conical = ? AND chapter = ? AND verse = ?",
            arrayOf<Any>(editionId, conical, chapter, verse)
        )
    }

    fun removeBookmark(id: Long) {
        db.execSQL("DELETE FROM bookmarks WHERE id = ?", arrayOf(id))
    }

    fun bookmarksNear(editionId: String, conical: Int, chapter: Int): List<Bookmark> {
        val out = mutableListOf<Bookmark>()
        db.rawQuery(
            "SELECT bm.id, bm.edition_id, COALESCE(e.display_name, bm.edition_id), bm.conical, " +
                "COALESCE(bn.name, b.long_name), bm.chapter, bm.verse, COALESCE(v.verse_text, ''), bm.created_at " +
                "FROM bookmarks bm " +
                "JOIN editions e ON e.edition_id = bm.edition_id " +
                "JOIN books b ON b.conical = bm.conical " +
                "LEFT JOIN book_names bn ON bn.edition_id = bm.edition_id AND bn.conical = bm.conical " +
                "LEFT JOIN verses v ON v.edition_id = bm.edition_id AND v.conical = bm.conical " +
                "AND v.chapter = bm.chapter AND v.verse = bm.verse",
            null
        ).use { c ->
            while (c.moveToNext()) {
                out.add(
                    Bookmark(
                        id = c.getLong(0),
                        editionId = c.getString(1),
                        editionName = c.getString(2),
                        conical = c.getInt(3),
                        bookName = c.getString(4),
                        chapter = c.getInt(5),
                        verse = c.getInt(6),
                        text = c.getString(7),
                        createdAt = c.getLong(8),
                    )
                )
            }
        }
        return out.sortedWith(
            compareBy<Bookmark> { if (it.editionId == editionId) 0 else 1 }
                .thenBy { if (it.conical == conical) 0 else 1 }
                .thenBy { if (it.chapter == chapter) 0 else 1 }
                .thenBy { kotlin.math.abs(it.conical - conical) }
                .thenBy { kotlin.math.abs(it.chapter - chapter) }
                .thenBy { kotlin.math.abs(it.verse - 1) }
                .thenByDescending { it.createdAt }
        )
    }

    /** Merge a single-edition .db (same schema) into the working database. */
    fun mergeFrom(file: File): Result<String> {
        return try {
            db.execSQL("ATTACH DATABASE '${file.path.replace("'", "''")}' AS src")
            try {
                db.rawQuery(
                    "SELECT count(*) FROM src.sqlite_master WHERE type='table' AND name IN ('editions','verses')",
                    null
                ).use { c ->
                    c.moveToFirst()
                    if (c.getInt(0) != 2) return Result.failure(Exception("Not an edition db (missing editions/verses tables)"))
                }
                val names = mutableListOf<String>()
                db.rawQuery("SELECT COALESCE(display_name, edition_id) FROM src.editions", null).use { c ->
                    while (c.moveToNext()) names.add(c.getString(0))
                }
                val hasBookNames = db.rawQuery(
                    "SELECT count(*) FROM src.sqlite_master WHERE type='table' AND name='book_names'", null
                ).use { c -> c.moveToFirst() && c.getInt(0) == 1 }
                db.beginTransaction()
                try {
                    db.execSQL("INSERT OR IGNORE INTO books SELECT * FROM src.books")
                    db.execSQL("INSERT OR REPLACE INTO editions SELECT * FROM src.editions")
                    if (hasBookNames) {
                        db.execSQL("INSERT OR REPLACE INTO book_names SELECT * FROM src.book_names")
                    }
                    db.execSQL("INSERT OR REPLACE INTO verses SELECT * FROM src.verses")
                    db.setTransactionSuccessful()
                } finally {
                    db.endTransaction()
                }
                Result.success(names.joinToString(", "))
            } finally {
                db.execSQL("DETACH DATABASE src")
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    fun removeEdition(id: String) {
        db.beginTransaction()
        try {
            db.execSQL("DELETE FROM bookmarks WHERE edition_id = ?", arrayOf(id))
            db.execSQL("DELETE FROM verses WHERE edition_id = ?", arrayOf(id))
            db.execSQL("DELETE FROM book_names WHERE edition_id = ?", arrayOf(id))
            db.execSQL("DELETE FROM editions WHERE edition_id = ?", arrayOf(id))
            db.setTransactionSuccessful()
        } finally {
            db.endTransaction()
        }
    }
}
