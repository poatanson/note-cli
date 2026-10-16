"""Rich rendering for notes."""

from __future__ import annotations

from collections import Counter
from datetime import date

from rich.console import Console
from rich.table import Table
from rich.text import Text

from note_cli.storage import TAG, Note

console = Console()
err_console = Console(stderr=True)

TAG_STYLE = "cyan"
MATCH_STYLE = "bold black on yellow"


def note_text(note: Note, keyword: str | None = None) -> Text:
    """Note body as Text (never parsed as markup), tags colored, keyword highlighted."""
    text = Text(note.text)
    text.highlight_regex(TAG.pattern, TAG_STYLE)
    if keyword:
        text.highlight_words([keyword], MATCH_STYLE, case_sensitive=False)
    return text


def notes_table(title: str, notes: list[Note], keyword: str | None = None, with_date: bool = False) -> Table:
    table = Table(title=title, title_justify="left", title_style="bold", expand=False)
    table.add_column("#", justify="right", style="dim", no_wrap=True)
    if with_date:
        table.add_column("날짜", style="green", no_wrap=True)
    table.add_column("시간", style="magenta", no_wrap=True)
    table.add_column("내용")
    for note in notes:
        cells = [str(note.index)]
        if with_date:
            cells.append(note.day.isoformat())
        table.add_row(*cells, note.time, note_text(note, keyword))
    return table


def print_days(notes_by_day: dict[date, list[Note]]) -> None:
    for day, notes in notes_by_day.items():
        console.print(notes_table(day.isoformat(), notes))


def print_day(day: date, notes: list[Note]) -> None:
    console.print(notes_table(day.isoformat(), notes))


def print_search(keyword: str, notes: list[Note]) -> None:
    console.print(notes_table(f"검색: {keyword} ({len(notes)}건)", notes, keyword=keyword, with_date=True))


def print_tags(counts: Counter[str]) -> None:
    table = Table(title="태그", title_justify="left", title_style="bold")
    table.add_column("태그", style=TAG_STYLE)
    table.add_column("횟수", justify="right")
    for tag, count in counts.most_common():
        table.add_row(f"#{tag}", str(count))
    console.print(table)


def print_added(note: Note) -> None:
    message = Text("✓ 저장됨 ", style="green")
    message.append(f"{note.day.isoformat()} #{note.index} [{note.time}] ", style="dim")
    message.append_text(note_text(note))
    console.print(message)


def info(message: str) -> None:
    console.print(Text(message, style="yellow"))


def success(message: str) -> None:
    console.print(Text(message, style="green"))


def error(message: str) -> None:
    err_console.print(Text(f"오류: {message}", style="bold red"))
