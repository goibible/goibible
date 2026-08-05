from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .repo import BibleRepo, Edition


@dataclass
class PaneState:
    edition_id: str
    conical: int = 1
    chapter: int = 1
    pending_verse: int | None = None


class AppState:
    def __init__(self, repo: BibleRepo, settings_path: Path) -> None:
        self.repo = repo
        self.settings_path = settings_path
        self.editions: list[Edition] = repo.editions()
        if not self.editions:
            raise RuntimeError("The Bible database has no editions.")
        data = self._load()
        default_edition = next((e.id for e in self.editions if e.id == "GOI_En"), self.editions[0].id)
        self.split = bool(data.get("split", False))
        self.sync_locked = bool(data.get("sync_locked", False))
        self.active_pane = int(data.get("active_pane", 0))
        self.dark_mode = bool(data.get("dark_mode", True))
        self.font_key = str(data.get("font_key", "literata"))
        self.font_size = int(data.get("font_size", 16))
        panes = data.get("panes", [])
        self.panes = [
            self._pane_from_dict(panes[i] if i < len(panes) else {}, default_edition)
            for i in range(2)
        ]
        self.refresh_editions(save=False)

    def _load(self) -> dict:
        if not self.settings_path.exists():
            return {}
        try:
            return json.loads(self.settings_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

    def _pane_from_dict(self, data: dict, default_edition: str) -> PaneState:
        return PaneState(
            edition_id=str(data.get("edition_id", default_edition)),
            conical=int(data.get("conical", 1)),
            chapter=int(data.get("chapter", 1)),
        )

    def save(self) -> None:
        payload = {
            "split": self.split,
            "sync_locked": self.sync_locked,
            "active_pane": self.active_pane,
            "dark_mode": self.dark_mode,
            "font_key": self.font_key,
            "font_size": self.font_size,
            "panes": [asdict(p) | {"pending_verse": None} for p in self.panes],
        }
        self.settings_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def refresh_editions(self, save: bool = True) -> None:
        self.editions = self.repo.editions()
        valid = {edition.id for edition in self.editions}
        fallback = self.editions[0].id
        for pane in self.panes:
            if pane.edition_id not in valid:
                pane.edition_id = fallback
                pane.conical = 1
                pane.chapter = 1
            self._clamp_pane(pane)
        if save:
            self.save()

    def visible_panes(self) -> list[int]:
        return [0, 1] if self.split else [0]

    def targets(self) -> list[PaneState]:
        return self.panes if self.split and self.sync_locked else [self.panes[self.active_pane]]

    def set_active(self, index: int) -> None:
        self.active_pane = 0 if index < 1 else 1
        self.save()

    def set_split(self, enabled: bool) -> None:
        self.split = enabled
        if not enabled:
            self.active_pane = 0
        self.save()

    def set_sync_locked(self, enabled: bool) -> None:
        self.sync_locked = enabled
        if enabled:
            src = self.panes[self.active_pane]
            dst = self.panes[1 - self.active_pane]
            dst.conical = src.conical
            dst.chapter = src.chapter
        self.save()

    def set_edition(self, edition_id: str) -> None:
        pane = self.panes[self.active_pane]
        pane.edition_id = edition_id
        self._clamp_pane(pane)
        self.save()

    def set_book(self, conical: int) -> None:
        for pane in self.targets():
            pane.conical = conical
            pane.chapter = 1
            self._clamp_pane(pane)
        self.save()

    def set_chapter(self, chapter: int) -> None:
        for pane in self.targets():
            max_chapter = max(1, self.repo.chapter_count(pane.edition_id, pane.conical))
            pane.chapter = max(1, min(chapter, max_chapter))
        self.save()

    def step_book(self, delta: int) -> None:
        for pane in self.targets():
            books = self.repo.books(pane.edition_id)
            index = next((i for i, book in enumerate(books) if book.conical == pane.conical), -1)
            target = index + delta
            if 0 <= target < len(books):
                pane.conical = books[target].conical
                pane.chapter = 1
        self.save()

    def next_chapter(self) -> None:
        for pane in self.targets():
            max_chapter = self.repo.chapter_count(pane.edition_id, pane.conical)
            if pane.chapter < max_chapter:
                pane.chapter += 1
            else:
                books = self.repo.books(pane.edition_id)
                index = next((i for i, book in enumerate(books) if book.conical == pane.conical), -1)
                if 0 <= index < len(books) - 1:
                    pane.conical = books[index + 1].conical
                    pane.chapter = 1
        self.save()

    def previous_chapter(self) -> None:
        for pane in self.targets():
            if pane.chapter > 1:
                pane.chapter -= 1
            else:
                books = self.repo.books(pane.edition_id)
                index = next((i for i, book in enumerate(books) if book.conical == pane.conical), -1)
                if index > 0:
                    pane.conical = books[index - 1].conical
                    pane.chapter = max(1, self.repo.chapter_count(pane.edition_id, pane.conical))
        self.save()

    def go_to_verse(self, conical: int, chapter: int, verse: int) -> None:
        for pane in self.targets():
            pane.conical = conical
            pane.chapter = chapter
            pane.pending_verse = verse
            self._clamp_pane(pane)
        self.save()

    def go_to_bookmark(self, edition_id: str, conical: int, chapter: int, verse: int) -> None:
        pane = self.panes[self.active_pane]
        pane.edition_id = edition_id
        pane.conical = conical
        pane.chapter = chapter
        pane.pending_verse = verse
        self._clamp_pane(pane)
        self.save()

    def go_to_random_verse(self, edition_id: str, conical: int, chapter: int, verse: int) -> None:
        pane = self.panes[self.active_pane]
        pane.edition_id = edition_id
        pane.conical = conical
        pane.chapter = chapter
        pane.pending_verse = verse
        self._clamp_pane(pane)
        self.save()

    def _clamp_pane(self, pane: PaneState) -> None:
        books = self.repo.books(pane.edition_id)
        if not books:
            return
        if pane.conical not in {book.conical for book in books}:
            pane.conical = books[0].conical
            pane.chapter = 1
        max_chapter = max(1, self.repo.chapter_count(pane.edition_id, pane.conical))
        pane.chapter = max(1, min(pane.chapter, max_chapter))
