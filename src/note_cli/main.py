"""Typer app: command definitions only. Logic lives in storage.py, output in display.py."""

from __future__ import annotations

import os
import shlex
import subprocess
from collections.abc import Callable
from functools import wraps
from typing import Annotated, ParamSpec, TypeVar

import typer

from note_cli import display, storage
from note_cli.storage import NoteError

app = typer.Typer(help="터미널용 빠른 메모 도구. 메모는 ~/.notes/YYYY-MM-DD.md 에 저장됩니다.",
                  no_args_is_help=True, add_completion=False)

P = ParamSpec("P")
R = TypeVar("R")


def friendly_errors(func: Callable[P, R]) -> Callable[P, R]:
    """Show NoteError as a readable message instead of a traceback."""

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return func(*args, **kwargs)
        except NoteError as exc:
            display.error(str(exc))
            raise typer.Exit(code=1) from None

    return wrapper


DateArg = Annotated[str | None, typer.Argument(help="날짜 YYYY-MM-DD (기본: 오늘)", show_default=False)]


@app.command()
@friendly_errors
def add(text: Annotated[str, typer.Argument(help="메모 내용. #태그 자동 인식")]) -> None:
    """메모 추가."""
    display.print_added(storage.add_note(text))


@app.command("ls")
@friendly_errors
def list_notes(
    days: Annotated[int, typer.Option("--days", "-d", min=1, help="최근 며칠")] = 7,
    tag: Annotated[str | None, typer.Option("--tag", "-t", help="태그로 필터")] = None,
) -> None:
    """최근 메모를 날짜별로 보기."""
    notes_by_day = storage.recent_notes(days, tag)
    if not notes_by_day:
        display.info(f"최근 {days}일 동안 메모가 없습니다.")
        return
    display.print_days(notes_by_day)


@app.command()
@friendly_errors
def search(keyword: Annotated[str, typer.Argument(help="검색어 (대소문자 무시)")]) -> None:
    """전체 메모 검색."""
    notes = storage.search_notes(keyword)
    if not notes:
        display.info(f"'{keyword}'와 일치하는 메모가 없습니다.")
        return
    display.print_search(keyword, notes)


@app.command()
@friendly_errors
def show(day: DateArg = None) -> None:
    """특정 날짜 메모 보기."""
    target = storage.parse_date(day)
    notes = storage.read_notes(target)
    if not notes:
        raise NoteError(f"{target.isoformat()} 메모가 없습니다.")
    display.print_day(target, notes)


def editor_command() -> list[str]:
    editor = os.environ.get("EDITOR") or ("notepad" if os.name == "nt" else "vi")
    return shlex.split(editor, posix=os.name != "nt")


@app.command()
@friendly_errors
def edit(day: DateArg = None) -> None:
    """해당 날짜 파일을 $EDITOR로 열기."""
    path = storage.day_file(storage.parse_date(day))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)
    try:
        subprocess.run([*editor_command(), str(path)], check=False)
    except FileNotFoundError:
        raise NoteError("에디터를 찾을 수 없습니다. EDITOR 환경변수를 확인하세요.") from None


@app.command()
@friendly_errors
def rm(
    day: Annotated[str, typer.Argument(help="날짜 YYYY-MM-DD")],
    number: Annotated[int, typer.Argument(help="메모 번호 (show/ls의 # 열)")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="확인 없이 삭제")] = False,
) -> None:
    """메모 삭제."""
    target = storage.parse_date(day)
    note = storage.get_note(target, number)
    if not yes and not typer.confirm(f"삭제할까요? [{note.time}] {note.text}"):
        display.info("취소했습니다.")
        raise typer.Exit()
    storage.remove_note(target, number)
    display.success(f"삭제됨: {target.isoformat()} #{number}")


@app.command()
@friendly_errors
def tags() -> None:
    """태그별 사용 횟수."""
    counts = storage.tag_counts()
    if not counts:
        display.info("태그가 없습니다.")
        return
    display.print_tags(counts)


if __name__ == "__main__":
    app()
