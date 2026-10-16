from datetime import date, datetime
from pathlib import Path

import pytest

from note_cli import storage
from note_cli.storage import NoteError

DAY = date(2026, 10, 16)


def at(hour: int, minute: int, day: date = DAY) -> datetime:
    return datetime(day.year, day.month, day.day, hour, minute)


def test_add_writes_markdown_line(note_dir: Path) -> None:
    note = storage.add_note("회의 준비 #work #급함", now=at(9, 5))
    content = (note_dir / "2026-10-16.md").read_text(encoding="utf-8")
    assert content == "- [09:05] 회의 준비 #work #급함\n"
    assert note.tags == ["work", "급함"]
    assert note.index == 1


def test_add_flattens_newlines_and_rejects_empty() -> None:
    note = storage.add_note("a\nb", now=at(10, 0))
    assert note.text == "a b"
    with pytest.raises(NoteError):
        storage.add_note("   ")


def test_tags_ignore_mid_word_hash() -> None:
    assert storage.extract_tags("url.com/a#b #ok #한글-태그") == ["ok", "한글-태그"]


def test_read_ignores_non_note_lines(note_dir: Path) -> None:
    note_dir.mkdir()
    (note_dir / "2026-10-16.md").write_text(
        "# 제목\n\n- [08:00] first\nrandom text\n- [09:00] second #x\n", encoding="utf-8"
    )
    notes = storage.read_notes(DAY)
    assert [(n.index, n.time, n.text) for n in notes] == [(1, "08:00", "first"), (2, "09:00", "second #x")]


def test_add_after_manual_edit_without_trailing_newline(note_dir: Path) -> None:
    note_dir.mkdir()
    (note_dir / "2026-10-16.md").write_text("- [08:00] first", encoding="utf-8")
    storage.add_note("second", now=at(9, 0))
    assert [n.text for n in storage.read_notes(DAY)] == ["first", "second"]


def test_recent_notes_window_and_tag_filter() -> None:
    storage.add_note("old #a", now=at(9, 0, date(2026, 10, 1)))
    storage.add_note("new #a", now=at(9, 0, date(2026, 10, 15)))
    storage.add_note("today #b", now=at(9, 0))
    result = storage.recent_notes(7, today=DAY)
    assert list(result) == [DAY, date(2026, 10, 15)]
    tagged = storage.recent_notes(30, tag="#A", today=DAY)
    assert list(tagged) == [date(2026, 10, 15), date(2026, 10, 1)]


def test_search_is_case_insensitive() -> None:
    storage.add_note("Hello World", now=at(9, 0))
    storage.add_note("다른 메모", now=at(10, 0))
    assert [n.text for n in storage.search_notes("hello")] == ["Hello World"]
    assert storage.search_notes("없음") == []


def test_remove_keeps_other_lines(note_dir: Path) -> None:
    note_dir.mkdir()
    (note_dir / "2026-10-16.md").write_text("# 제목\n- [08:00] a\n- [09:00] b\n", encoding="utf-8")
    removed = storage.remove_note(DAY, 1)
    assert removed.text == "a"
    assert (note_dir / "2026-10-16.md").read_text(encoding="utf-8") == "# 제목\n- [09:00] b\n"


def test_remove_errors() -> None:
    with pytest.raises(NoteError, match="메모가 없습니다"):
        storage.remove_note(DAY, 1)
    storage.add_note("a", now=at(9, 0))
    with pytest.raises(NoteError, match="3번"):
        storage.remove_note(DAY, 3)


def test_tag_counts() -> None:
    storage.add_note("#a #b", now=at(9, 0))
    storage.add_note("#a", now=at(9, 0, date(2026, 10, 15)))
    assert storage.tag_counts() == {"a": 2, "b": 1}


def test_parse_date() -> None:
    assert storage.parse_date("2026-10-16") == DAY
    assert storage.parse_date(None) == date.today()
    with pytest.raises(NoteError):
        storage.parse_date("16/10/2026")


def test_note_dir_env(note_dir: Path) -> None:
    assert storage.note_dir() == note_dir
