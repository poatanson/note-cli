"""File storage: one markdown file per day, one `- [HH:MM] text #tag` line per note."""

from __future__ import annotations

import os
import re
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path

ENCODING = "utf-8"
NOTE_LINE = re.compile(r"^- \[(\d{2}:\d{2})\] (.*)$")
TAG = re.compile(r"(?<!\S)#(\w[\w-]*)")
FILE_NAME = re.compile(r"^\d{4}-\d{2}-\d{2}\.md$")


class NoteError(Exception):
    """User-facing error (bad date, missing note, ...)."""


@dataclass(frozen=True)
class Note:
    day: date
    index: int  # 1-based position among the note lines of that day
    time: str
    text: str
    tags: list[str] = field(default_factory=list)


def note_dir() -> Path:
    """Storage folder: $NOTE_DIR, or ~/.notes by default."""
    custom = os.environ.get("NOTE_DIR")
    return Path(custom) if custom else Path.home() / ".notes"


def day_file(day: date) -> Path:
    return note_dir() / f"{day.isoformat()}.md"


def parse_date(value: str | None) -> date:
    """Parse YYYY-MM-DD; None means today."""
    if value is None:
        return date.today()
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise NoteError(f"날짜 형식이 올바르지 않습니다: '{value}' (예: 2026-10-16)") from None


def extract_tags(text: str) -> list[str]:
    return TAG.findall(text)


def parse_line(line: str, day: date, index: int) -> Note | None:
    match = NOTE_LINE.match(line.rstrip("\r\n"))
    if not match:
        return None
    time, text = match.groups()
    return Note(day=day, index=index, time=time, text=text, tags=extract_tags(text))


def _read_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return path.read_text(encoding=ENCODING).splitlines()


def read_notes(day: date) -> list[Note]:
    """All notes of a day; lines that are not notes (headings, blank lines) are ignored."""
    notes: list[Note] = []
    for line in _read_lines(day_file(day)):
        note = parse_line(line, day, len(notes) + 1)
        if note:
            notes.append(note)
    return notes


def format_line(time: str, text: str) -> str:
    return f"- [{time}] {text}"


def add_note(text: str, now: datetime | None = None) -> Note:
    """Append a note to today's file. Newlines are flattened to keep one note per line."""
    clean = " ".join(text.split())
    if not clean:
        raise NoteError("메모 내용이 비어 있습니다.")
    now = now or datetime.now()
    path = day_file(now.date())
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding=ENCODING) if path.exists() else ""
    prefix = "" if not existing or existing.endswith("\n") else "\n"
    time = now.strftime("%H:%M")
    with path.open("a", encoding=ENCODING, newline="\n") as f:
        f.write(f"{prefix}{format_line(time, clean)}\n")
    return Note(day=now.date(), index=len(read_notes(now.date())), time=time, text=clean,
                tags=extract_tags(clean))


def iter_days() -> Iterator[date]:
    """All days that have a note file, oldest first."""
    folder = note_dir()
    if not folder.is_dir():
        return
    for path in sorted(folder.iterdir()):
        if FILE_NAME.match(path.name):
            try:
                yield date.fromisoformat(path.stem)
            except ValueError:
                continue


def recent_notes(days: int, tag: str | None = None, today: date | None = None) -> dict[date, list[Note]]:
    """Notes from the last `days` days (including today), newest day first."""
    today = today or date.today()
    start = today - timedelta(days=max(days, 1) - 1)
    result: dict[date, list[Note]] = {}
    for day in sorted(iter_days(), reverse=True):
        if not start <= day <= today:
            continue
        notes = filter_by_tag(read_notes(day), tag)
        if notes:
            result[day] = notes
    return result


def filter_by_tag(notes: list[Note], tag: str | None) -> list[Note]:
    if not tag:
        return notes
    wanted = tag.lstrip("#").lower()
    return [n for n in notes if wanted in (t.lower() for t in n.tags)]


def search_notes(keyword: str) -> list[Note]:
    """Case-insensitive substring search across all notes, newest day first."""
    needle = keyword.lower()
    return [
        note
        for day in sorted(iter_days(), reverse=True)
        for note in read_notes(day)
        if needle in note.text.lower()
    ]


def remove_note(day: date, index: int) -> Note:
    """Delete the index-th note of a day, keeping every other line as-is."""
    path = day_file(day)
    lines = _read_lines(path)
    count = 0
    for pos, line in enumerate(lines):
        note = parse_line(line, day, count + 1)
        if note is None:
            continue
        count += 1
        if count == index:
            del lines[pos]
            path.write_text("".join(f"{l}\n" for l in lines), encoding=ENCODING, newline="\n")
            return note
    if not path.exists():
        raise NoteError(f"{day.isoformat()} 메모가 없습니다.")
    raise NoteError(f"{day.isoformat()}에 {index}번 메모가 없습니다. (총 {count}개)")


def get_note(day: date, index: int) -> Note:
    notes = read_notes(day)
    if not notes:
        raise NoteError(f"{day.isoformat()} 메모가 없습니다.")
    if not 1 <= index <= len(notes):
        raise NoteError(f"{day.isoformat()}에 {index}번 메모가 없습니다. (총 {len(notes)}개)")
    return notes[index - 1]


def tag_counts() -> Counter[str]:
    counter: Counter[str] = Counter()
    for day in iter_days():
        for note in read_notes(day):
            counter.update(note.tags)
    return counter
