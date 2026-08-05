from __future__ import annotations

import html
import json
import sys
import tempfile
import urllib.request
from pathlib import Path

from PySide6.QtCore import QEvent, Qt, QTimer, Slot, QUrl
from PySide6.QtGui import QAction, QFontDatabase, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QSplitter,
    QSizePolicy,
    QSpinBox,
    QTextBrowser,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .paths import font_file, icon_file, settings_file, working_db
from .repo import BibleRepo, Bookmark, RandomVerse, SearchHit
from .state import AppState, PaneState


DOWNLOAD_MANIFEST_URL = "https://raw.githubusercontent.com/goibible/goibible/main/goi_db_download/manifest.json"
DOWNLOAD_BASE_URL = "https://raw.githubusercontent.com/goibible/goibible/main/goi_db_download/"


def tool_button(text: str) -> QToolButton:
    button = QToolButton()
    button.setText(text)
    return button


def edition_label(edition) -> str:
    return f"{edition.language.upper()} - {edition.id}"


def edition_signature_label(edition) -> str:
    return f"{edition.id} - {edition.display_name}"


LIGHT_STYLE = """
QMainWindow, QWidget { background: #f4f1ed; color: #262a2f; }
QDialog { background: #f4f1ed; }
QFrame#paneHeader { background: #ebe8e2; border: 1px solid #d6d1c8; border-radius: 8px; }
QFrame#paneHeader[active="true"] { background: #e3ece7; border-color: #789788; }
QFrame#readerCard { background: #fffdf9; border: 1px solid #d8d2c8; border-radius: 8px; }
QFrame#readerCard[active="true"] { border: 2px solid #789788; }
QTextBrowser { background: transparent; border: none; padding: 12px; selection-background-color: #cfe0d8; selection-color: #17201d; }
QComboBox, QLineEdit, QSpinBox {
  background: #fffdf9; color: #262a2f; border: 1px solid #c8c2ba; border-radius: 6px; padding: 5px 8px;
}
QComboBox:hover, QLineEdit:hover, QSpinBox:hover { border-color: #9ea89f; }
QComboBox:focus, QLineEdit:focus, QSpinBox:focus { border: 1px solid #789788; background: #ffffff; }
QPushButton, QToolButton {
  background: #ece9e3; color: #2c3035; border: 1px solid #c9c3ba; border-radius: 6px; padding: 6px 10px;
}
QPushButton:hover, QToolButton:hover { background: #e3e7e2; border-color: #9cac9f; }
QPushButton:pressed, QToolButton:pressed { background: #d8ded6; }
QPushButton:checked, QToolButton:checked { background: #dbe8e1; border-color: #789788; color: #244239; }
QToolButton#lockButton:checked { background: #dee8f2; border-color: #7b93ad; color: #243f5d; }
QToolButton#searchButton { background: #f1e7e6; border-color: #caa7a3; color: #633a38; }
QToolButton#searchButton:hover { background: #ead8d6; border-color: #b8847f; }
QToolButton#randomButton { background: #e6ecef; border-color: #9eb6c1; color: #294653; }
QToolButton#randomButton:hover { background: #d9e5e9; border-color: #7ea1ae; }
QToolButton#settingsButton { background: #e8e4ed; border-color: #b7aac4; color: #473956; }
QToolButton#settingsButton:hover { background: #ded8e7; border-color: #9e8eb0; }
QSplitter::handle { background: #d6d1c8; }
QSplitter::handle:horizontal { width: 9px; margin: 4px 0; border-radius: 4px; }
QSplitter::handle:hover { background: #789788; }
QSlider::groove:horizontal { height: 5px; background: #d7d2ca; border-radius: 2px; }
QSlider::handle:horizontal { width: 16px; margin: -6px 0; background: #789788; border: 1px solid #5f7f70; border-radius: 8px; }
QListWidget { background: #fffdf9; border: 1px solid #d8d2c8; border-radius: 7px; padding: 4px; }
QListWidget::item { padding: 7px; border-radius: 5px; }
QListWidget::item:selected { background: #dbe8e1; color: #1f332d; }
"""

DARK_STYLE = """
QMainWindow, QWidget { background: #18191b; color: #eee9e1; }
QDialog { background: #18191b; }
QFrame#paneHeader { background: #232528; border: 1px solid #3a3e42; border-radius: 8px; }
QFrame#paneHeader[active="true"] { background: #24302d; border-color: #90b6a3; }
QFrame#readerCard { background: #202225; border: 1px solid #3a3e42; border-radius: 8px; }
QFrame#readerCard[active="true"] { border: 2px solid #90b6a3; }
QTextBrowser { background: transparent; border: none; padding: 12px; color: #eee9e1; selection-background-color: #426456; selection-color: #f8f5ef; }
QComboBox, QLineEdit, QSpinBox {
  background: #24272a; color: #eee9e1; border: 1px solid #4b5055; border-radius: 6px; padding: 5px 8px;
}
QComboBox:hover, QLineEdit:hover, QSpinBox:hover { border-color: #687077; }
QComboBox:focus, QLineEdit:focus, QSpinBox:focus { border: 1px solid #90b6a3; background: #272b2e; }
QPushButton, QToolButton {
  background: #292c30; color: #eee9e1; border: 1px solid #4b5055; border-radius: 6px; padding: 6px 10px;
}
QPushButton:hover, QToolButton:hover { background: #32363a; border-color: #687077; }
QPushButton:pressed, QToolButton:pressed { background: #3a403d; }
QPushButton:checked, QToolButton:checked { background: #2f453d; border-color: #90b6a3; color: #dff1e9; }
QToolButton#lockButton:checked { background: #2b3d54; border-color: #8ba8c6; color: #e2efff; }
QToolButton#searchButton { background: #3a2d31; border-color: #9b7478; color: #f1d8da; }
QToolButton#searchButton:hover { background: #463438; border-color: #bc8f94; }
QToolButton#randomButton { background: #29363b; border-color: #7194a0; color: #dceff5; }
QToolButton#randomButton:hover { background: #314249; border-color: #8db2bf; }
QToolButton#settingsButton { background: #332d3b; border-color: #837293; color: #eadff4; }
QToolButton#settingsButton:hover { background: #3f3748; border-color: #9b88ad; }
QSplitter::handle { background: #3a3e42; }
QSplitter::handle:horizontal { width: 9px; margin: 4px 0; border-radius: 4px; }
QSplitter::handle:hover { background: #90b6a3; }
QSlider::groove:horizontal { height: 5px; background: #3e4347; border-radius: 2px; }
QSlider::handle:horizontal { width: 16px; margin: -6px 0; background: #90b6a3; border: 1px solid #b7d5c7; border-radius: 8px; }
QListWidget { background: #202225; border: 1px solid #3a3e42; border-radius: 7px; padding: 4px; }
QListWidget::item { padding: 7px; border-radius: 5px; }
QListWidget::item:selected { background: #2f453d; color: #e8f5ef; }
"""


class ReaderPane(QWidget):
    def __init__(self, index: int, window: "MainWindow") -> None:
        super().__init__()
        self.index = index
        self.window = window
        self._loading = False

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 4, 10, 4)
        root.setSpacing(6)

        self.header = QFrame()
        self.header.setObjectName("paneHeader")
        header = QHBoxLayout(self.header)
        header.setContentsMargins(6, 4, 6, 4)
        header.setSpacing(6)
        self.edition_combo = QComboBox()
        self.book_combo = QComboBox()
        self.chapter_combo = QComboBox()
        self.edition_combo.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.edition_combo.setMinimumWidth(128)
        self.book_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.chapter_combo.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)

        self.prev_book = tool_button("‹")
        self.next_book = tool_button("›")
        self.prev_chapter = tool_button("‹")
        self.next_chapter = tool_button("›")

        header.addWidget(self.edition_combo)
        header.addWidget(self.prev_book)
        header.addWidget(self.book_combo, 1)
        header.addWidget(self.next_book)
        header.addWidget(self.prev_chapter)
        header.addWidget(self.chapter_combo)
        header.addWidget(self.next_chapter)
        root.addWidget(self.header)

        self.card = QFrame()
        self.card.setObjectName("readerCard")
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(False)
        self.browser.setLineWrapMode(QTextBrowser.LineWrapMode.WidgetWidth)
        self.browser.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.browser.anchorClicked.connect(self.open_verse_action)
        card_layout.addWidget(self.browser)
        root.addWidget(self.card, 1)

        for widget in (
            self,
            self.card,
            self.browser,
            self.browser.viewport(),
            self.edition_combo,
            self.book_combo,
            self.chapter_combo,
            self.prev_book,
            self.next_book,
            self.prev_chapter,
            self.next_chapter,
        ):
            widget.installEventFilter(self)

        self.edition_combo.currentIndexChanged.connect(self._edition_changed)
        self.book_combo.currentIndexChanged.connect(self._book_changed)
        self.chapter_combo.currentIndexChanged.connect(self._chapter_changed)
        self.prev_book.clicked.connect(lambda: self.window.navigate(lambda s: s.step_book(-1)))
        self.next_book.clicked.connect(lambda: self.window.navigate(lambda s: s.step_book(1)))
        self.prev_chapter.clicked.connect(lambda: self.window.navigate(lambda s: s.previous_chapter()))
        self.next_chapter.clicked.connect(lambda: self.window.navigate(lambda s: s.next_chapter()))

    def mousePressEvent(self, event) -> None:
        self.window.set_active_pane(self.index)
        super().mousePressEvent(event)

    def eventFilter(self, watched, event) -> bool:
        if event.type() in (QEvent.Type.MouseButtonPress, QEvent.Type.FocusIn):
            self.window.set_active_pane(self.index)
        return super().eventFilter(watched, event)

    def refresh(self) -> None:
        self._loading = True
        state = self.window.state
        pane = state.panes[self.index]
        self.card.setProperty("active", state.split and state.active_pane == self.index)
        self.header.setProperty("active", state.split and state.active_pane == self.index)
        self.card.style().unpolish(self.card)
        self.card.style().polish(self.card)
        self.header.style().unpolish(self.header)
        self.header.style().polish(self.header)

        self.edition_combo.clear()
        for edition in state.editions:
            self.edition_combo.addItem(edition_label(edition), edition.id)
            self.edition_combo.setItemData(
                self.edition_combo.count() - 1,
                edition_signature_label(edition),
                Qt.ItemDataRole.ToolTipRole,
            )
        self.edition_combo.setCurrentIndex(max(0, self.edition_combo.findData(pane.edition_id)))

        books = state.repo.books(pane.edition_id)
        self.book_combo.clear()
        for book in books:
            self.book_combo.addItem(book.long_name, book.conical)
        self.book_combo.setCurrentIndex(max(0, self.book_combo.findData(pane.conical)))

        chapter_count = max(1, state.repo.chapter_count(pane.edition_id, pane.conical))
        self.chapter_combo.clear()
        for chapter in range(1, chapter_count + 1):
            self.chapter_combo.addItem(f"Ch {chapter}", chapter)
        self.chapter_combo.setCurrentIndex(max(0, self.chapter_combo.findData(pane.chapter)))

        self._loading = False
        self._render_verses(pane)

    def _render_verses(self, pane: PaneState) -> None:
        verses = self.window.state.repo.verses(pane.edition_id, pane.conical, pane.chapter)
        family = "Literata" if self.window.state.font_key == "literata" else "Georgia"
        text_color = "#eee9e1" if self.window.state.dark_mode else "#262a2f"
        num_color = "#90b6a3" if self.window.state.dark_mode else "#789788"
        bookmarked_color = "#d2ad62" if self.window.state.dark_mode else "#9b6b1f"
        empty_color = "#9fa8a2" if self.window.state.dark_mode else "#767d78"
        size = self.window.state.font_size
        bookmarked = self.window.state.repo.bookmarked_verses(pane.edition_id, pane.conical, pane.chapter)

        if not verses:
            body = "<p class='empty'>Not available in this edition</p>"
        else:
            rows = []
            for verse in verses:
                num_class = "num bookmarked" if verse.num in bookmarked else "num"
                rows.append(
                    f"<p id='v{verse.num}'><a name='v{verse.num}'></a>"
                    f"<a class='{num_class}' href='bookmark:{verse.num}'>{verse.num}</a> {html.escape(verse.text)}</p>"
                )
            body = "\n".join(rows)

        self.browser.setHtml(
            f"""
            <html><head><style>
            body {{ color: {text_color}; font-family: '{family}', Georgia, serif; font-size: {size}px; line-height: 1.6; }}
            p {{ margin: 0 0 12px 0; }}
            a.num {{ color: {num_color}; font-weight: 700; font-size: {max(10, int(size * 0.75))}px; text-decoration: none; }}
            a.bookmarked {{ color: {bookmarked_color}; }}
            .empty {{ color: {empty_color}; text-align: center; margin-top: 40px; }}
            </style></head><body>{body}</body></html>
            """
        )
        if pane.pending_verse is not None:
            target = pane.pending_verse
            pane.pending_verse = None
            QTimer.singleShot(0, lambda: self.browser.scrollToAnchor(f"v{target}"))
        else:
            self.browser.verticalScrollBar().setValue(0)

    @Slot(QUrl)
    def open_verse_action(self, url: QUrl) -> None:
        if url.scheme() != "bookmark":
            return
        try:
            verse = int(url.path() or url.toString().split(":", 1)[1])
        except (IndexError, ValueError):
            return
        self.window.set_active_pane(self.index)
        pane = self.window.state.panes[self.index]
        bookmarked = self.window.state.repo.is_bookmarked(pane.edition_id, pane.conical, pane.chapter, verse)
        action = "Remove bookmark" if bookmarked else "Add bookmark"
        choice = QMessageBox.question(
            self,
            "Bookmark",
            f"{action} for verse {verse}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if choice != QMessageBox.StandardButton.Yes:
            return
        if bookmarked:
            self.window.state.repo.remove_bookmark(pane.edition_id, pane.conical, pane.chapter, verse)
        else:
            self.window.state.repo.add_bookmark(pane.edition_id, pane.conical, pane.chapter, verse)
        self.window.refresh_all()

    @Slot()
    def _edition_changed(self) -> None:
        if self._loading:
            return
        self.window.set_active_pane(self.index)
        edition_id = self.edition_combo.currentData()
        if edition_id:
            self.window.navigate(lambda s: s.set_edition(edition_id))

    @Slot()
    def _book_changed(self) -> None:
        if self._loading:
            return
        self.window.set_active_pane(self.index)
        conical = self.book_combo.currentData()
        if conical:
            self.window.navigate(lambda s: s.set_book(int(conical)))

    @Slot()
    def _chapter_changed(self) -> None:
        if self._loading:
            return
        self.window.set_active_pane(self.index)
        chapter = self.chapter_combo.currentData()
        if chapter:
            self.window.navigate(lambda s: s.set_chapter(int(chapter)))


class SearchDialog(QDialog):
    def __init__(self, window: "MainWindow") -> None:
        super().__init__(window)
        self.window = window
        self.setWindowTitle("Search")
        self.resize(720, 520)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.run_search)

        layout = QVBoxLayout(self)
        title_row = QHBoxLayout()
        self.title = QLabel()
        close = QPushButton("Close")
        close.clicked.connect(self.reject)
        title_row.addWidget(self.title, 1)
        title_row.addWidget(close)
        layout.addLayout(title_row)

        self.query = QLineEdit()
        self.query.setPlaceholderText("Search verses")
        self.query.textChanged.connect(lambda: self.timer.start(250))
        layout.addWidget(self.query)

        self.count = QLabel("")
        layout.addWidget(self.count)
        self.results = QListWidget()
        self.results.itemActivated.connect(self.open_hit)
        layout.addWidget(self.results, 1)
        self.refresh_title()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.query.setFocus()
        self.query.selectAll()

    def refresh_title(self) -> None:
        pane = self.window.state.panes[self.window.state.active_pane]
        edition = next((e for e in self.window.state.editions if e.id == pane.edition_id), None)
        self.title.setText(f"Search {edition_signature_label(edition) if edition else pane.edition_id}")

    @Slot()
    def run_search(self) -> None:
        query = self.query.text()
        self.results.clear()
        if len(query) < 2:
            self.count.setText("")
            return
        pane = self.window.state.panes[self.window.state.active_pane]
        hits = self.window.state.repo.search(pane.edition_id, query)
        self.count.setText("First 100 matches" if len(hits) >= 100 else f"{len(hits)} matches")
        for hit in hits:
            item = QListWidgetItem(f"{hit.book_name} {hit.chapter}:{hit.verse}\n{hit.text}")
            item.setData(Qt.ItemDataRole.UserRole, hit)
            self.results.addItem(item)

    @Slot(QListWidgetItem)
    def open_hit(self, item: QListWidgetItem) -> None:
        hit: SearchHit = item.data(Qt.ItemDataRole.UserRole)
        self.window.navigate(lambda s: s.go_to_verse(hit.conical, hit.chapter, hit.verse))
        self.accept()


class BookmarksDialog(QDialog):
    def __init__(self, window: "MainWindow") -> None:
        super().__init__(window)
        self.window = window
        self.setWindowTitle("Bookmarks")
        self.resize(720, 520)

        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        top.addWidget(QLabel("<h2>Bookmarks</h2>"), 1)
        close = QPushButton("Close")
        close.clicked.connect(self.accept)
        top.addWidget(close)
        layout.addLayout(top)

        self.list = QListWidget()
        self.list.itemActivated.connect(self.open_bookmark)
        layout.addWidget(self.list, 1)

        remove = QPushButton("Remove Selected Bookmark")
        remove.clicked.connect(self.remove_selected)
        layout.addWidget(remove)
        self.refresh()

    def refresh(self) -> None:
        self.list.clear()
        pane = self.window.state.panes[self.window.state.active_pane]
        bookmarks = self.window.state.repo.bookmarks_near(pane.edition_id, pane.conical, pane.chapter)
        if not bookmarks:
            self.list.addItem("No bookmarks yet.")
            self.list.item(0).setFlags(Qt.ItemFlag.NoItemFlags)
            return
        for bookmark in bookmarks:
            item = QListWidgetItem(
                f"{bookmark.book_name} {bookmark.chapter}:{bookmark.verse}\n"
                f"{bookmark.edition_name}\n"
                f"{bookmark.text}"
            )
            item.setData(Qt.ItemDataRole.UserRole, bookmark)
            self.list.addItem(item)

    @Slot(QListWidgetItem)
    def open_bookmark(self, item: QListWidgetItem) -> None:
        bookmark = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(bookmark, Bookmark):
            return
        self.window.navigate(
            lambda s: s.go_to_bookmark(bookmark.edition_id, bookmark.conical, bookmark.chapter, bookmark.verse)
        )
        self.accept()

    @Slot()
    def remove_selected(self) -> None:
        item = self.list.currentItem()
        if item is None:
            return
        bookmark = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(bookmark, Bookmark):
            return
        self.window.state.repo.remove_bookmark_id(bookmark.id)
        self.window.refresh_all()
        self.refresh()


class RandomizerDialog(QDialog):
    def __init__(self, window: "MainWindow") -> None:
        super().__init__(window)
        self.window = window
        self.current_verse: RandomVerse | None = None
        self.setWindowTitle("Random Verse")
        self.resize(620, 420)

        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        top.addWidget(QLabel("<h2>Random Verse</h2>"), 1)
        close = QPushButton("Close")
        close.clicked.connect(self.reject)
        top.addWidget(close)
        layout.addLayout(top)

        edition_row = QHBoxLayout()
        edition_row.addWidget(QLabel("Edition"))
        self.edition_combo = QComboBox()
        pane = self.window.state.panes[self.window.state.active_pane]
        for edition in self.window.state.editions:
            self.edition_combo.addItem(edition_signature_label(edition), edition.id)
        self.edition_combo.setCurrentIndex(max(0, self.edition_combo.findData(pane.edition_id)))
        self.edition_combo.currentIndexChanged.connect(self.pick_random_verse)
        edition_row.addWidget(self.edition_combo, 1)
        layout.addLayout(edition_row)

        self.reference = QLabel("Reference")
        self.reference.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.reference.setStyleSheet("font-weight: 700;")
        layout.addWidget(self.reference)

        self.verse = QTextBrowser()
        self.verse.setOpenExternalLinks(False)
        self.verse.setMinimumHeight(180)
        layout.addWidget(self.verse, 1)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        go = QPushButton("Go")
        go.clicked.connect(self.go_to_current)
        self.new_verse = QPushButton("New Verse")
        self.new_verse.clicked.connect(self.pick_random_verse)
        buttons.addWidget(go)
        buttons.addWidget(self.new_verse)
        layout.addLayout(buttons)

        self.pick_random_verse()

    @Slot()
    def pick_random_verse(self, *_args) -> None:
        edition_id = self.edition_combo.currentData()
        if not edition_id:
            self.current_verse = None
            self.reference.setText("No editions installed")
            self.verse.setHtml("<p>No verse available.</p>")
            return
        self.current_verse = self.window.state.repo.random_verse(edition_id)
        if self.current_verse is None:
            self.reference.setText("No verse available")
            self.verse.setHtml("<p>No verse available in this edition.</p>")
            return
        item = self.current_verse
        self.reference.setText(f"{item.book_name} {item.chapter}:{item.verse}")
        self.verse.setHtml(
            f"""
            <html><body>
            <p style="font-size: {self.window.state.font_size}px; line-height: 1.55;">
            {html.escape(item.text)}
            </p>
            <p style="color: #888;">{html.escape(item.edition_name)}</p>
            </body></html>
            """
        )

    @Slot()
    def go_to_current(self, *_args) -> None:
        if self.current_verse is None:
            return
        item = self.current_verse
        self.window.navigate(
            lambda s: s.go_to_random_verse(item.edition_id, item.conical, item.chapter, item.verse)
        )
        self.accept()


class SettingsDialog(QDialog):
    def __init__(self, window: "MainWindow") -> None:
        super().__init__(window)
        self.window = window
        self.setWindowTitle("Settings")
        self.resize(620, 560)

        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        top.addWidget(QLabel("<h2>Settings</h2>"), 1)
        done = QPushButton("Done")
        done.clicked.connect(self.accept)
        top.addWidget(done)
        layout.addLayout(top)

        self.dark = QCheckBox("Dark mode")
        self.dark.setChecked(window.state.dark_mode)
        self.dark.toggled.connect(self.set_dark)
        layout.addWidget(self.dark)

        font_row = QHBoxLayout()
        font_row.addWidget(QLabel("Font"))
        self.font_choice = QComboBox()
        self.font_choice.addItem("Literata", "literata")
        self.font_choice.addItem("Serif", "serif")
        self.font_choice.setCurrentIndex(max(0, self.font_choice.findData(window.state.font_key)))
        self.font_choice.currentIndexChanged.connect(self.set_font)
        font_row.addWidget(self.font_choice, 1)
        layout.addLayout(font_row)

        size_row = QHBoxLayout()
        self.size_label = QLabel()
        self.size = QSlider(Qt.Orientation.Horizontal)
        self.size.setRange(10, 28)
        self.size.setValue(window.state.font_size)
        self.size.valueChanged.connect(self.set_size)
        size_row.addWidget(self.size_label)
        size_row.addWidget(self.size, 1)
        layout.addLayout(size_row)
        self.preview = QLabel("In the beginning God created the heavens and the earth.")
        layout.addWidget(self.preview)

        layout.addWidget(QLabel("<h3>Editions</h3>"))
        self.editions = QListWidget()
        layout.addWidget(self.editions, 1)

        remove = QPushButton("Remove Selected Edition")
        remove.clicked.connect(self.remove_selected)
        layout.addWidget(remove)

        layout.addWidget(QLabel("<h3>Add Edition</h3>"))
        pick = QPushButton("Pick .db File")
        pick.clicked.connect(self.pick_file)
        layout.addWidget(pick)

        download_db = QPushButton("Download .db")
        download_db.clicked.connect(self.download_from_github)
        layout.addWidget(download_db)

        url_row = QHBoxLayout()
        self.url = QLineEdit()
        self.url.setPlaceholderText("Download URL (.db)")
        get = QPushButton("Get")
        get.clicked.connect(self.download)
        url_row.addWidget(self.url, 1)
        url_row.addWidget(get)
        layout.addLayout(url_row)

        self.status = QLabel("")
        layout.addWidget(self.status)
        self.refresh()

    def refresh(self) -> None:
        self.editions.clear()
        for edition in self.window.state.editions:
            item = QListWidgetItem(f"{edition_signature_label(edition)}\nLanguage: {edition.language}")
            item.setData(Qt.ItemDataRole.UserRole, edition.id)
            self.editions.addItem(item)
        self.size_label.setText(f"Size {self.window.state.font_size}")
        self.preview.setStyleSheet(f"font-size: {self.window.state.font_size}px;")

    @Slot(bool)
    def set_dark(self, enabled: bool) -> None:
        self.window.state.dark_mode = enabled
        self.window.state.save()
        self.window.apply_style()
        self.window.refresh_all()

    @Slot()
    def set_font(self) -> None:
        self.window.state.font_key = self.font_choice.currentData()
        self.window.state.save()
        self.window.refresh_all()

    @Slot(int)
    def set_size(self, size: int) -> None:
        self.window.state.font_size = size
        self.window.state.save()
        self.refresh()
        self.window.refresh_all()

    @Slot()
    def remove_selected(self) -> None:
        item = self.editions.currentItem()
        if item is None:
            return
        if len(self.window.state.editions) <= 1:
            QMessageBox.warning(self, "Remove Edition", "At least one edition must remain installed.")
            return
        edition_id = item.data(Qt.ItemDataRole.UserRole)
        self.window.state.repo.remove_edition(edition_id)
        self.window.state.refresh_editions()
        self.status.setText("Edition removed.")
        self.window.refresh_all()
        self.refresh()

    @Slot()
    def pick_file(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(self, "Pick edition database", "", "SQLite databases (*.db);;All files (*)")
        if not filename:
            return
        self._merge(Path(filename))

    @Slot()
    def download_from_github(self) -> None:
        self.status.setText("Loading downloads...")
        QApplication.processEvents()
        try:
            with urllib.request.urlopen(DOWNLOAD_MANIFEST_URL, timeout=20) as response:
                manifest = json.loads(response.read().decode("utf-8"))
            editions = manifest.get("editions", [])
            if not editions:
                self.status.setText("No downloads found.")
                return
        except Exception as exc:
            self.status.setText(f"Could not load downloads: {exc}")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Download .db")
        dialog_layout = QVBoxLayout(dialog)
        dialog_layout.addWidget(QLabel("Choose an edition to download."))

        choices = QListWidget()
        for edition in editions:
            edition_id = edition.get("edition_id", "")
            display_name = edition.get("display_name") or edition_id
            bcp47_tag = edition.get("bcp47_tag") or edition.get("language_subtag") or ""
            verse_count = edition.get("verse_count", 0)
            item = QListWidgetItem(f"{display_name}\n{edition_id} - {bcp47_tag} - {verse_count} verses")
            item.setData(Qt.ItemDataRole.UserRole, edition)
            choices.addItem(item)
        if choices.count() > 0:
            choices.setCurrentRow(0)
        dialog_layout.addWidget(choices)

        button_row = QHBoxLayout()
        cancel = QPushButton("Cancel")
        download = QPushButton("Download")
        cancel.clicked.connect(dialog.reject)
        download.clicked.connect(dialog.accept)
        button_row.addWidget(cancel)
        button_row.addWidget(download)
        dialog_layout.addLayout(button_row)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            self.status.setText("")
            return
        item = choices.currentItem()
        if item is None:
            return
        edition = item.data(Qt.ItemDataRole.UserRole)
        filename = edition.get("file")
        if not filename:
            self.status.setText("Download entry has no file.")
            return
        self._download_url(DOWNLOAD_BASE_URL + filename, edition.get("display_name") or filename)

    @Slot()
    def download(self) -> None:
        url = self.url.text().strip()
        if not url:
            return
        self._download_url(url, "database")

    def _download_url(self, url: str, label: str) -> None:
        self.status.setText(f"Downloading {label}...")
        QApplication.processEvents()
        try:
            with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
                tmp_path = Path(tmp.name)
            urllib.request.urlretrieve(url, tmp_path)
            self._merge(tmp_path, cleanup=True)
        except Exception as exc:
            self.status.setText(f"Download failed: {exc}")

    def _merge(self, path: Path, cleanup: bool = False) -> None:
        try:
            names = self.window.state.repo.merge_from(path)
            self.window.state.refresh_editions()
            self.window.refresh_all()
            self.refresh()
            self.status.setText(f"Added: {names}")
        except Exception as exc:
            self.status.setText(f"Failed: {exc}")
        finally:
            if cleanup:
                path.unlink(missing_ok=True)


class MainWindow(QMainWindow):
    def __init__(self, state: AppState) -> None:
        super().__init__()
        self.state = state
        self.setWindowTitle("GOI Bible")
        self.setWindowIcon(QIcon(str(icon_file())))
        self.resize(1100, 760)
        self.search_dialog: SearchDialog | None = None

        QFontDatabase.addApplicationFont(str(font_file()))

        central = QWidget()
        outer = QVBoxLayout(central)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(8)

        self.panes = [ReaderPane(0, self), ReaderPane(1, self)]
        self._syncing_scroll = False
        self.panes[0].browser.verticalScrollBar().valueChanged.connect(lambda value: self.sync_scroll(0, value))
        self.panes[1].browser.verticalScrollBar().valueChanged.connect(lambda value: self.sync_scroll(1, value))
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self.panes[0])
        self.splitter.addWidget(self.panes[1])
        self.splitter.setSizes([1, 1])
        outer.addWidget(self.splitter, 1)

        controls = QHBoxLayout()
        self.first = tool_button("|‹")
        self.previous = tool_button("‹‹")
        self.next = tool_button("››")
        self.last = tool_button("›|")
        self.chapter_label = QLabel()
        self.chapter_slider = QSlider(Qt.Orientation.Horizontal)
        self.chapter_slider.valueChanged.connect(lambda value: self.navigate(lambda s: s.set_chapter(value)))
        self.chapter_count_label = QLabel()
        self.split_button = tool_button("Split")
        self.split_button.setCheckable(True)
        self.lock_button = tool_button("Lock")
        self.lock_button.setObjectName("lockButton")
        self.lock_button.setCheckable(True)
        search = tool_button("Search")
        search.setObjectName("searchButton")
        bookmarks = tool_button("Bookmarks")
        randomizer = tool_button("Random")
        randomizer.setObjectName("randomButton")
        settings = tool_button("Settings")
        settings.setObjectName("settingsButton")

        self.first.clicked.connect(lambda: self.navigate(lambda s: s.step_book(-1)))
        self.previous.clicked.connect(lambda: self.navigate(lambda s: s.previous_chapter()))
        self.next.clicked.connect(lambda: self.navigate(lambda s: s.next_chapter()))
        self.last.clicked.connect(lambda: self.navigate(lambda s: s.step_book(1)))
        self.split_button.clicked.connect(lambda checked: self.navigate(lambda s: s.set_split(checked)))
        self.lock_button.clicked.connect(lambda checked: self.navigate(lambda s: s.set_sync_locked(checked)))
        search.clicked.connect(self.open_search)
        bookmarks.clicked.connect(self.open_bookmarks)
        randomizer.clicked.connect(self.open_randomizer)
        settings.clicked.connect(self.open_settings)

        for widget in [self.first, self.previous, self.chapter_label, self.chapter_slider, self.chapter_count_label, self.next, self.last, self.split_button, self.lock_button, search, bookmarks, randomizer, settings]:
            controls.addWidget(widget)
        self.chapter_slider.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        outer.addLayout(controls)
        self.setCentralWidget(central)

        self._install_shortcuts()
        self.apply_style()
        self.refresh_all()

    def _install_shortcuts(self) -> None:
        actions = [
            (QKeySequence.StandardKey.Find, self.open_search),
            (QKeySequence(Qt.Key.Key_Left), lambda: self.navigate(lambda s: s.previous_chapter())),
            (QKeySequence(Qt.Key.Key_Right), lambda: self.navigate(lambda s: s.next_chapter())),
        ]
        for sequence, callback in actions:
            action = QAction(self)
            action.setShortcut(sequence)
            action.triggered.connect(callback)
            self.addAction(action)

    def apply_style(self) -> None:
        QApplication.instance().setStyleSheet(DARK_STYLE if self.state.dark_mode else LIGHT_STYLE)

    def set_active_pane(self, index: int) -> None:
        if self.state.active_pane != index:
            self.state.set_active(index)
            self.refresh_all()

    def navigate(self, action) -> None:
        action(self.state)
        self.refresh_all()

    def sync_scroll(self, source_index: int, value: int) -> None:
        if self._syncing_scroll or not (self.state.split and self.state.sync_locked):
            return
        if source_index != self.state.active_pane:
            return
        self._syncing_scroll = True
        try:
            self.panes[1 - source_index].browser.verticalScrollBar().setValue(value)
        finally:
            self._syncing_scroll = False

    def refresh_all(self) -> None:
        self.panes[1].setVisible(self.state.split)
        self.split_button.setChecked(self.state.split)
        self.lock_button.setVisible(self.state.split)
        self.lock_button.setChecked(self.state.sync_locked)

        for index in self.state.visible_panes():
            self.panes[index].refresh()

        active = self.state.panes[self.state.active_pane]
        chapter_count = max(1, self.state.repo.chapter_count(active.edition_id, active.conical))
        self.chapter_slider.blockSignals(True)
        self.chapter_slider.setRange(1, max(2, chapter_count))
        self.chapter_slider.setEnabled(chapter_count > 1)
        self.chapter_slider.setValue(active.chapter)
        self.chapter_slider.blockSignals(False)
        self.chapter_label.setText(str(active.chapter))
        self.chapter_count_label.setText(str(chapter_count))

        if self.state.split and self.state.sync_locked:
            source = self.panes[self.state.active_pane].browser.verticalScrollBar()
            target = self.panes[1 - self.state.active_pane].browser.verticalScrollBar()
            target.setValue(source.value())

    @Slot()
    def open_search(self) -> None:
        self.search_dialog = SearchDialog(self)
        self.search_dialog.exec()

    @Slot()
    def open_bookmarks(self) -> None:
        BookmarksDialog(self).exec()

    @Slot()
    def open_randomizer(self) -> None:
        RandomizerDialog(self).exec()

    @Slot()
    def open_settings(self) -> None:
        SettingsDialog(self).exec()

    def closeEvent(self, event) -> None:
        self.state.save()
        self.state.repo.close()
        super().closeEvent(event)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("GOI Bible")
    app.setWindowIcon(QIcon(str(icon_file())))
    repo = BibleRepo(working_db())
    state = AppState(repo, settings_file())
    window = MainWindow(state)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
